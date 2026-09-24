---
name: dev-reseed
description: 명시적으로 요청한 dev 전체 초기화와 정본 재적재를 수행한다. product(pr)의 운영 시작 전 최초 초기화 요청은 별도 운영용 실행 경로로 연결한다. 배포만 하거나 상태 조회만 하는 요청에는 적용하지 않는다.
---

# dev 재생성

## 대상부터 구분한다

- dev 초기화는 아래 dev 실행기를 사용한다.
- product(pr) 운영 시작 전 청소·최초 재적재는 [product 최초 초기화](references/product-first-reset.md)를 읽고 운영용 실행기를 사용한다. `pr`을 pull request로 단정하지 않고 현재 대화의 환경 의미를 따른다.
- 서비스 운영 중 product 또는 staging 초기화는 해당 환경의 승인된 계획을 따른다. 운영 전이라는 가정을 자동 적용하지 않는다.
- 현재 대화의 삭제·계정 구성 승인은 유지한다. 대상이 product라고 해서 추가 dev 초기화나 새 PR을 자동 요구하지 않는다.
- 기존 자료 수정·reseed 도구 개선 요청만으로 전체 초기화를 실행하지 않는다. 실제 변경 범위를 먼저 고정한다.

## 본체와 보조격자

- 정본의 `files`는 관측 본체, `grid_files`는 그 본체에 붙이는 LAT/LON 보조격자다.
  초기화 전 계획 생성에서 전체 정본의 보조격자 경로가 어느 자료의 본체 목록에도 포함되지 않는지 검사한다.
  혼입은 자동 제외하지 않고 입력 오류로 중단한다.
- `lon2d` 같은 이름만으로 파일 역할을 단정하지 않는다. 원본 배열·정본 경로·연결을 확인한다.
  EPSG 좌표계 입력은 LAT/LON 파일 첨부를 대신하지 않으며, 다른 관측 자료의 격자를 붙이지 않는다.
- 재적재 후에는 자료 수뿐 아니라 본체/격자 역할과 대상 자료 연결도 확인한다.
  보조격자가 독립 본체로 등록되면 성공으로 보고하지 않는다.
- 기간은 원본 헤더·파일명·설명 문서의 근거를 사용한다. 등록일이나 파일 수정일을 관측일로 대체하지 않는다.
  근거가 없고 현재 등록 화면이 날짜를 요구하면 초기화 전에 미확정 입력으로 보고한다.

## 식생 모델 입력 DEM·Aspect

- 사용자 결정(2026-09-16): `01.level-data/02.vegetation/02.vegetation/Lv.1_(Model_Input_Data)/`
  아래 `DEM.tif`와 `Aspect.tif`의 등록 기준 시점은 **2023년 5월, 월 단위**다.
  이는 사용자가 알려준 자료 맥락에 따른 등록값이며, 파일에서 확인한 관측일이나 제작일이 아니다.
  설명에 “기준 시점은 사용자 제공 맥락에 따른 2023년 5월이며, 파일 내부 날짜 정보는 없음”을 남긴다.
  월의 내부 저장값에 일자가 필요해도 5월 1일을 실제 관측일로 표현하거나 정밀도를 일 단위로 바꾸지 않는다.
- 두 파일은 각각 독립 데이터셋의 본체로 등록한다. LAT/LON 기준 격자나 일반 첨부로 넣지 않는다.
  동봉 `#readme/#processing_description_NDVI.docx`의 모델 학습 설명에 따라 해당 NDVI Lv.2
  산출물에 부모 자료로 연결하며, 역할은 `보조입력`이다. 다른 NDVI 단계에 일괄 연결하지 않는다.
- 실제 화면 개발은 추후 작업이다. 현재 화면의 `주입력` 고정값을 그대로 수용하지 말고,
  재적재에서는 기존 공식 계보 API의 `parentRole: "보조입력"`을 사용해 연결한다.
  기존 연결이 같은 역할이면 중복 생성 없이 재사용한다. 같은 부모가 `주입력`으로 이미 연결돼 있으면
  공식 PATCH가 역할 변경을 받지 않으므로 자동 삭제·재생성하지 않고 중단해 수동 정정을 요구한다.
  DB 직접 수정은 하지 않는다.
- 초기화 전 실행 경로가 월 단위 기간 입력과 보조입력 연결을 지원하는지 확인한다.
  스킬에 적었다는 이유로 러너 구현이 완료됐다고 간주하지 않는다. 미지원이면 삭제 전에 중단한다.
  적재 후 두 자료의 기간·정밀도·설명·본체와 NDVI 대상/역할을 조회해 확인한다.
  기존 간선 수와 달라지면 승인된 계획의 대상별 연결 목록에 맞춰 기대값을 갱신하고 검증한다.

## dev에서 무엇을 실행하는가

```bash
bash dev-package/tools/dev-reseed/reseed.sh --dry-run          # 명령만 찍고 아무것도 건드리지 않는다
bash dev-package/tools/dev-reseed/reseed.sh --preflight-only    # 검사만 — dev 를 읽기만 한다
bash dev-package/tools/dev-reseed/reseed.sh --rehearse           # 원격 원시동작 10 을 실모드로 한 번씩 — 바꾸지 않는다
bash dev-package/tools/dev-reseed/reseed.sh                     # 10단계 무인 실행
bash dev-package/tools/dev-reseed/reseed.sh --from s3 --run-dir <reset 을 돈 실행 자리>   # 그 단계부터 재개
```

### 기본 계정 5개

- 계정 목록의 원본은 비공개 `~/.config/colab-platform/dev-reseed-accounts-approved.json`(0600)이다.
  `COLAB_RESEED_ACCOUNTS_PROFILE`로 승인된 보호 파일 위치를 지정할 수 있다. 저장소에는 실제 계정을 넣지 않고
  `accounts-profile.example.json`의 가상 예시만 둔다. 예시를 실제 실행의 기본값으로 사용하지 않는다.
  `--accounts-file`로 다른 파일을 지정해도 이번 승인된 5명·역할·소속과 일치해야 한다.
  파일 누락·중복·구성 불일치는 초기화 전에 실패하며, 일반 seed 러너의 선택 계정 모드와 구분한다.
- 최종 구성은 연구실 미소속 서비스 운영자 4명과 정본 연구실 교수 1명이다.
  서비스 운영자 권한을 모든 연구실의 자료 접근 권한으로 해석하지 않는다.
- 초기 비밀번호는 각 계정의 이메일이며 첫 로그인에서 변경해야 한다.
  개별 보호 파일을 실행 자리에서 만들고, 비밀번호를 명령 인자나 보고서에 남기지 않는다.
- 교수는 자료 적재·검증 동안만 임시 운영자로 사용한다. 자료 검증 후 초기 비밀번호로 돌리고
  임시 운영자 권한을 해제한다. 최종화 재개 때 완료한 비밀번호 초기화를 반복하거나 권한을 다시 부여하지 않는다.
- 기존 파일 기반 인증 계정은 앱 기동 전에 보호 백업 후 비우고, 새 DB 계정 외의 로그인이 남지 않게 확인한다.
- 5명 모두 실제 초기 로그인·신원·역할·소속·비밀번호 변경 요구를 검사하고 로그아웃한다.
  검증 중 비밀번호를 변경하지 않는다. 계정 생성 수만으로 완료를 판정하지 않는다.

### 실행 구성

- 10단계 = `preflight → deploy → reset → bootstrap → up → s3 → prelude → seed → verify → report`.
- ⭑ **`preflight` 는 `--from` 과 무관하게 언제나 먼저 돈다.** 읽기 전용이고, **배포 대상 sha 를 해석하는
  자리가 거기 하나뿐**이다 — 건너뛰면 이미지 태그가 `…:dev-` 로, 승인 기록의 `targetSha` 가 빈 값으로 선다.
  `--from` 이 고르는 것은 **바꾸는 단계 여덟**(`deploy`~`verify`) 중 시작 지점 하나다.
- `--preflight-only` = preflight 만 돌고 바꾸는 단계는 **0건**. dev 를 읽기만 한다
  (ssh 조회 · `aws sts` · `docker ps` · 파일 · `agent-browser doctor` · 계획 생성 dry-run).
- ⭑ **`--rehearse` = 부수기 전에 원격 원시동작을 전부 한 번씩 실모드로 내 본다.** 바꾸는 단계는 **0건**이다.
  왜 = 실모드 정지가 세 회차 내리 **한 번도 실행된 적 없는 원격 줄**에서 났다(deploy ⑤ → preflight secrets →
  reset ①″). `--dry-run` 은 명령을 찍기만 하므로 그 줄을 원격 셸이 어떻게 읽는지는 파괴 단계를 밟고 나서야
  드러났다. 리허설이 그 순서를 끊는다. 원시동작 열 — (⑷ 는 체인 둘이라 두 벌이다)
  ⑴ `psql:master`(작은따옴표가 든 SQL) ⑵ `ssh_script`(따옴표·`$`·백틱 되받기) ⑶ compose `ps`(정지·기동과 같은
  compose·env 한 벌) ⑷ 마이그레이터 이미지 `alembic current` 두 체인 ⑸ 초기화 도구 BYPASSRLS `--phase count` ＋
  그 계수에 묶인 `--phase s3-plan --dry-run`(임시 폴더 · 적용 불가 표지 계획 · **적용 없음**) ＋ 계획 검토 ⑹ `postgres:16-alpine` 로 소유자 URL `select 1` ⑺ `deploy_doctor` 1회를
  `doctor_summary_line` 으로 읽기 ⑻ 러너 `--phase report` ⑼ `agent-browser` 제목 읽기.
  원시동작마다 한 줄을 찍고 **기대와 대조**한다 — 어긋나면 그 **이름을 대고** 비영 종료한다(fail-closed).
  `--dry-run` 과 함께 주면 원격에 한 바이트도 내지 않는다.
- dev 접속 값(`COLAB_DEV_SSH`·`COLAB_DEV_KEY_FILE`)이 없으면 **셸이 죽지 않는다** —
  `dev-sha`·`secrets`·`leftovers` 가 그 변수 이름을 대고 미달로 떨어지고, 접속이 필요 없는 항목은 그대로 잰다.
- 절차의 원본 = `dev-package/sessions/DR-2-runbook.md`(사람이 실제로 밟은 순서). 이 스크립트가 그 실행형이다.
- 접속·참조 경로는 환경변수로 준다 — `COLAB_DEV_SSH` · `COLAB_DEV_KEY_FILE` ·
  `COLAB_RESEED_EC2_SECRETS_DIR` · `COLAB_REF_ROOT` · `COLAB_DEV_URL`.
  계정 신원은 기본 프로필을 따르며 다른 `RESEED_ACCOUNT_ID`/`_EMAIL`/`_NAME` 지정은 거부한다.
  `--operator-password-file`을 별도 지정하면 0600 파일과 승인된 이메일 초기값의 일치를 검사한다.
  계정별 초기 비밀번호 값은 argv·로그·결과 JSON에 쓰지 않는다.
- ⛔ **`COLAB_DEV_SECRETS_DIR` 를 이 도구에 주지 않는다 — 읽지도 않는다.** 한 이름이 두 뜻이다:
  운영자 기계의 `~/.config/colab-platform/dev-operator.env` 에서는 **개발 기계의 로컬 폴더**,
  `infra/dev/README.md` 의 `dev.env` 안에서는 **EC2 경로**(`/etc/colab`). 그 값이 실린 채 `reset`·`prelude`
  가 돌면 EC2 에 없는 호스트 경로를 `docker -v` 로 마운트한다(DR-4 회차 §5 ⑴ 실측).
  원격 경로의 출처는 **`COLAB_RESEED_EC2_SECRETS_DIR`(기본 `/etc/colab`) 하나**다.
  `--preflight-only` 가 **마운트할 그 경로를 한 줄로 찍는다**(경로만 · 파일 값은 읽지 않는다).
- 교수 bootstrap은 `infra/staging/provision-lab.sql`의 정본 계정·연구실 ID를 유지하고,
  이메일은 계정 프로필과 일치시킨다. 실제 원격 실행 SQL과 로그인 신원을 함께 검사한다.
  환경변수의 이메일만 바꾸거나 새 ID의 교수 계정을 덧붙이지 않는다.

## 승인

- 정본 = `.agents/rules/deploy.md` 11번 증보 문단(2026-09-25 개정). **빈 dev 만** dev 한정 상시 승인이다.
  ⛔ **비어 있지 않은 dev 는 상시 승인 밖이다** — 매 회차 Ted 가 현재 대화에서 표별 계수를 보고 준 명시 GO 로만 지운다.
- 조건 = 게이트 다섯 충족(`--target dev`＋`--yes-reset-dev` · 버킷 정확 일치 · 두 DB URL 호스트에 `-dev` ·
  계획 키가 `uploads/`·`previews/` 안 · BYPASSRLS 계수가 비었거나 그 계수에 대한 사용자 GO). 하나라도 어긋나면
  아무것도 지우지 않고 비영 종료한다.
- `reset` 단계 직전에 `approval-record.json`(누가·언제·어느 sha·어느 게이트)이 실행 자리에 먼저 선다.
- ⛔ **reset 정지 게이트** — `reset` ① 은 먼저 원격의 옛 계수·계획 파일을 지우고, BYPASSRLS 읽기 롤 두 체인
  (`$COLAB_RESEED_EC2_SECRETS_DIR/backup-platform-db.url`·`backup-ai-db.url` · `colab_backup`)과 `row_security=off` 로 센다.
  계수 파일(= 토큰의 재료)이 덮는 것 — 두 체인 **모든** 기본 표의 행수와 행 내용 지문 · DB 가 가리키는 저장 키 ·
  `uploads/`·`previews/` 키·크기 목록 sha256 · 멀티파트 목록 sha256. 행 추가·삭제·내용 편집·키 교체는 토큰을 바꾼다.
  **같은 키·같은 크기의 객체 덮어쓰기는 보지 못한다**(목록 조회가 ETag 를 모은다면 덮는다 · 업로드 키는 ULID 라 제품 경로에서 재사용하지 않는다).
  「비어 있다」 = 사람 자료 표 일곱 행 0 · 참조 키 0 · `uploads/` 객체 0 · 멀티파트 0 — 고아 객체도 비어 있지 않다.
  비어 있지 않으면 **앱 정지·DROP·S3 전에** 비영 종료하고 첫 줄에 시드 기준선 대비 초과분(표별 +N), 이어서 표별 계수 ·
  고아 객체 건수 · 1회용 토큰을 찍는다. 토큰 = sha256(계수 바이트 ‖ 그 회차가 원격에 남긴 nonce) · 만료 30분 · 한 번 쓰면 소진.
  붙여 넣을 완성 명령은 찍지 않는다. **토큰은 stdout 이 터미널일 때만(`[ -t 1 ]`) 그 터미널에 찍고** 단계 로그·실행 기록에는
  남기지 않는다. stdout 이 터미널이 아니면(에이전트 · 파이프) 토큰 없이 「자기 터미널에서 다시 열어야 보인다」만 남긴다.
- 넘기는 것은 **사용자**다 — Ted 가 계수를 보고 GO 를 준 뒤 사용자 터미널에서 `COLAB_RESEED_ACK_NONEMPTY`(그 토큰)와
  `COLAB_RESEED_ACK_BASIS`(GO 근거 — 누가 · 어디서 · 언제)를 두고 `--from reset` 으로 다시 연다. 판정·근거는 `reset-ack.json` 에 남는다.
  ⛔ 에이전트는 두 값을 채우지 않는다 — 공용 Bash 훅(`scripts/harness/hooks/git-guard.sh` ⑹)이 Claude·Codex 모두에서 막는다.
- 도구도 스스로 막는다 — `--phase schema` 는 DROP 직전 같은 프로세스에서 다시 세어 비어 있지 않은데 재계수 sha256 과 같은
  ack 가 없으면 지우지 않는다. `--phase s3-plan` 은 이번 reset 의 DROP 직전 계수(`count-at-drop.json`)와 그 sha256 을 필수로
  받고, **지금** DB 가 가리키는 키가 1건이라도 있으면 계획을 쓰지 않는다. 런북대로 손으로 불러도 같다.
  preflight `backup-size` 는 최근 백업 크기를 빈 스키마 기준(gz ~15~21 KB)과 대조해 **알림만** 낸다.
- ⛔ **에이전트가 몰아서 실행할 때는 `reset` 앞에 advisor 게이트 ③(go/no-go)을 붙인다.**
  상시 승인(빈 dev)은 advisor 판정을 대체하지 않는다(`R-DATA-CANON §7`). advisor 판정도 사용자 GO 를 대체하지 않는다.
- dev 실행기는 dev 식별자 밖에서 어느 조건으로도 돌지 않는다. product 최초 초기화는 위의 별도 경로와 현재 대화의 명시 승인을 따른다. staging에는 dev 상시 승인을 적용하지 않는다.

## 결과를 읽는 법

- `<실행 자리>/result.json` — 스키마 `colab-reseed-result/1`(`dev-package/tools/dev-reseed/result-schema.json`).
  - `stages[]` — 단계별 `status`(ok/failed/skipped) · `exitCode` · `durationSec` · `log`.
  - `preflight` — 통과·미달 항목 **이름**.
  - `counts` — 데이터셋 28 · 프로젝트 4 · 간선 18 · 가공 단계 불일치 · 「미지정」 · 프로젝트 미연결.
  - `previewJudgment[]` — 데이터셋 1건당 **성립 / 미성립 / 판정불가**와 소요 ms.
    ⭑ **「판정불가」는 값을 못 받은 것**(브라우저 무응답·선택자 변경)이고 통과로 세지 않는다 — `verify` 가 비영 종료한다.
  - `doctorSummary` — `deploy_doctor` 요약줄 축자(**한 번의 실행** 결과다. 부분 실행을 합치지 않는다).
  - `blocked[]` — 차단 항목의 이름과 사유.
  - `outcome` — `ok` · `failed` · `dry-run`. 실패면 `failedStage` 가 멈춘 자리다.
- 실행 자리 = `$COLAB_JOB_DIR/tmp/dev-reseed/<시각>` 또는 `dev-package/reports/dev-reseed-runs/<시각>`(추적 제외).
- 회차 기록 뼈대는 `dev-package/sessions/DR-4-run-<날짜＋시각>.md` 로 나온다(같은 날 두 번째 실행이 첫 기록을
  덮어쓰지 않게 시각까지 쓴다). **레포에 남는 조건 = 바꾸는 단계가 실제로 돌았다** — `--dry-run`·
  `--preflight-only`·preflight 에서 멈춘 회차는 실행 자리에만 남는다. 원장·대장·HANDOFF 갱신은 오케스트레이터가 한다.
- 검사기 = `bash gates/run.sh dev-reseed-selftest`(요약줄 파서 · preflight fail-closed · 계획 요약줄 ·
  `result.json` · `--from` · `--preflight-only` · `die` 복귀 · 미리보기 판정불가 · **원격 전송로** ·
  **정지 뒤 자동 재기동** · **리허설 fail-closed** · **reset 정지 게이트** `tests/reset-gate.sh`). dev 무접촉이다.

## 멈췄을 때

- 단계 하나가 비영 종료하면 그 자리에서 멈춘다. **자동 재시도는 없다** — 등록 확정과 삭제는 되돌릴 수 없다.
- ⭑ **`reset` 이 앱을 정지(①′)한 뒤 실패하면 도구가 앱을 스스로 되살린다**(같은 compose·env 로 `start`).
  그 사실은 `result.json` 의 `recovery` 와 회차 기록 §4-1 에 남는다. 사람이 dev 를 올리러 들어갈 일이 없다.
  정지는 **되돌릴 수 없는 걸음(② 스키마 DROP) 직전**에만 내린다 — 읽기 전용 계수는 그보다 먼저 끝난다.
- `reset` ①ᵇ 정지 게이트에서 멈췄으면 dev 는 **아무것도 바뀌지 않았다**(앱도 돌고 있다). 표별 계수와 기준선 초과분을
  사용자에게 그대로 보이고 멈춘다. 지울지는 사용자가 정하고 넘기는 것도 사용자다(위 「승인」).
- 출력 마지막 줄이 멈춘 단계 이름과 로그 경로를 낸다. 원인을 본 뒤 `--from <그 단계>` 로 잇는다.
  ⚠ `reset` 뒤 단계(`bootstrap`·`up`·`s3`)에서 이을 때는 **그 reset 을 돈 `--run-dir`** 을 그대로 준다 —
  `s3` 는 그 실행 자리의 `reset-ack.json`·`count-at-drop.json` 없이 계획을 세우지 않는다.
- `preflight` 미달은 이름으로 나온다. 이름을 고치기 전에 다음 단계로 넘어가지 않는다.
