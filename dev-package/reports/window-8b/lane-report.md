# 창 8-b 레인 보고 — dev(AWS) 배포 집행

집행 2026-09-06 · 워크트리 `.claude/worktrees/agent-a3276ccbbe5aba5e6` · 브랜치 `integration/w8b-dev-deploy`
작업지시 = `dev-package/03-HANDOFF.md` 「창 8-b — dev 배포(AWS 필요)」 블록 · 런북 = `infra/dev/README.md` · `docs/DEPLOY.md §6-1`

**한 줄** — **배포는 섰다**(4 단위 healthy · `deploy_doctor` **14/14 를 한 번의 실행으로**).
**판정은 대부분 안 섰다** — dev 데이터가 0 이라 배포 뒤 확인 7개 중 **잴 수 있는 것이 2개뿐**이었고,
**재적재는 집행 0** — 이 레인이 보류로 올린 물음에 Ted 가 답했고, 그 답이 **적재 범위 변경으로 다시 번복**됐다(`§5-b`). 새 매니페스트 확정 대기(HOLD).

---

## 0. 진입조건 넷 — 실측

| | 조건 | 실측 | 판정 |
|---|---|---|---|
| ㉠ | 창 8-a done(`main` ff ＋ 게이트 전수) | `main` = `87d5b87` · PR #1 MERGED · 전수 green 50 한 실행 | **선다** (`§9 〈343〉`) |
| ㉡ | AWS 접근 인수 | `aws sts get-caller-identity` 성공(`user/colab-platform-s3-uploader-dev`) ＋ 그 키로 ssh 성공 | **선다** |
| ㉢ | 유료 전환 | `aws support describe-*` **AccessDenied**(이 IAM 은 S3 최소권한) | **미확인** (`〈345〉`) |
| ㉣ | `t4g.medium` 승격 | IMDS 실조회 = **`t4g.small`**(vCPU 2 · 1,841 MB) | **완화 판정으로 열었다** (`〈344〉`) |

⚠ ㉢ 는 「안 섰다」가 아니라 **못 쟀다**이다 — 콘솔 실측은 Ted 자리다. dev 배포를 막지 않는다.
⚠ ㉣ 는 Ted 완화 판정으로 열었고 **위험은 남았다** — 아래 `§6` 의 OOM 감시 결과 참조.

---

## 1. 유일한 코드 변경 — 「보기」 둘 가르기 (`§9 〈346〉`)

`frontend/src/components/detail/FileList.tsx` 의 토글 낱말 `보기` → **`파일 관리`**. `.ig-more` 의 「보기」는 그대로.
시험 = `frontend/test/detail-files.test.tsx` 에 낱말을 못 박는 단언 1건(종전 시험은 testid 로만 집어 낱말이 바뀌어도 green 이었다).

**판정 기준 / 실측** — `frontend-typecheck` **green**(오류 0) · `frontend-test` **green**(45파일 · **678건** 통과 · 실패 0).
**배포 실물 대조** — CloudFront 가 서빙 중인 번들 `assets/index-B8kHJtXb.js` 안에 `파일 관리` 문자열 **있음**.

커밋 = `c260ab4`(코드·시험) · `15e3b85`(원장).

---

## 2. ⑶ 배포 — 판정 기준 · 실측값 · 로그

**배포 sha = `0045f2233a04`** (이 레인 HEAD `df6899d` 이전 커밋 `0045f22`).
⭑ **롤백 태그 = `COLAB_IMAGE_TAG=dev-30b3f08f4e81`** — 배포 직전 `CURRENT_SHA` 다. 5 이미지 전부 EC2 에 남아 있다.

| 단계 | 판정 기준 | 실측 | 로그 |
|---|---|---|---|
| `build.sh` | 병합 sha 이미지가 서고 종료 0 | **exit 0** · 5 이미지 전부 `Architecture=arm64` 실측 통과 · tar **273M** | `build.txt` |
| `ship.sh` | tar 전송 ＋ `docker load` ok ＋ 종료 0 | **exit 0** · `Loaded image` 5줄 · `:dev` 재태그 · `CURRENT_SHA` 갱신 | `ship.txt` |
| EC2 `up.sh` | 4 단위 healthy ＋ `CURRENT_SHA` 갱신 ＋ 종료 0 | **exit 0** · **4/4 healthy** · sha `0045f2233a04` | `up.txt` |
| `deploy_web.py` | 종료 0 ＋ CloudFront 가 새 번들을 준다 | **exit 0** · 96파일 · 5,576,955 B | `deploy-web.txt` · `cloudfront-check.txt` |

**헬스 본문(조용한 `local` 을 잡는 자리)** — `pipeline-worker storageMode=s3` · `viz-render sourceMode=s3` ·
`previewSink=s3` · `tileBranch=꺼짐`.

**CloudFront 실측** — 서빙 중인 `index.html` 이 로컬 `frontend/dist` 와 **같은 해시 자산**
`assets/index-B8kHJtXb.js` · `assets/index-CW1Ughrj.css` 를 가리키고, 그 js 가 **HTTP 200 · 430,205 B ·
`cache-control: public, max-age=31536000, immutable`**.

⚠ **WSL2 크로스빌드 실측** — `tonistiigi/binfmt --install arm64` 로 QEMU 를 등록한 뒤에야 `build.sh` 가 선다.
`infra/dev/README.md` 진단표의 그 행이 실물과 맞다. 빌드 소요 = 약 50분(geo 스택 `pipeline-worker`·`viz-render` 가 대부분).

---

## 3. ⑷ `deploy_doctor` — 14/14 를 한 번의 실행으로

**판정 기준** = 축자 「14/14 를 **한 번의 실행으로**」 · **재시도해 모은 14 는 14 가 아니다**.
**실측** = `항목 14 — ✓ 14 · ✗ 0 · ─ 0` · 축자 **「전 항목 통과 (─ 0 — 14 항목이 실제로 돌았다)」** · exit 0.
로그 = `deploy-doctor.txt`(전문).

집행 방식 = `docs/DEPLOY.md §6-1` 그대로 **EC2 위 컨테이너 격리 실행**(맥 터널 방식은 ⑫ 가 red 로 뜬다).
운영자 키는 `--env-file /tmp/op.env`(umask 077)로 넘기고 **실행 직후 `shred -u`**.

⚠ **EC2 `/opt/colab-repo` 에 `git` 이 없다** — `deploy_doctor` 가 `REPO_ROOT/db`(alembic head) 와
`REPO_ROOT/gates/tools` 를 읽으므로 `db`·`gates`·`services/core-api/ops`·`infra` 를 **tar 로 동기화**했다.
동일성 실측 = `deploy_doctor.py` md5 로컬 = 원격(`49ad1774…`) · 마이그레이션 파일 15개 동수.
⟹ **런북에 없는 단계다.** `infra/dev/README.md` 에 「`deploy_doctor` 전에 `/opt/colab-repo` 를 배포 sha 로 맞춘다」를 적어야 한다(아래 `§8` 후속).

주요 항목 실측 — ⑪ 앱 자격증명 출처 **`imds`**(EC2 에 액세스 키 0 · 만료 330분) · ⑫ 환경 짝 dev(RDS 호스트 실주소) ·
⑬ `/api/v1/me` **401 JSON** · `/previews/*` **403 비-HTML** · ⑭ 백업 **21.3시간 전 · 객체 15건**.

---

## 4. ⑸ 배포 뒤 확인 — 항목별 판정

⛔ **전제 실측 하나가 이 절 전체를 지배한다 — dev 는 비어 있다.**
`d3_dataset` **0** · `d3_file` **0** · `d4_lineage_edge` **0** · `d1_account` **0**(연구실 2건뿐).
계수는 core-api 컨테이너 안에서 read-only `SELECT count(*)` 로 쟀다(쓰기 0 · `pre-deploy-snapshot.txt`).

| | 항목 | 완료 조건 | 판정 | 근거 · 남은 것 |
|---|---|---|---|---|
| ⓐ | `BF-12` ⑶ viz 회수 요약 1줄 | healthy 뒤 ≥60분 · 첫 바퀴 계수 ＋ **삭제 0** | **red** | ⛔ **요약 0줄 · 트리거 집행 0줄** (INFO 는 416줄 난다 — 로깅은 살아 있다). 원인 = `infra/dev/compose.yml` 에 **`COLAB_VIZ_TRIGGER_SPOOL` 이 없다** ⟹ `main.py:105` 에서 `triggers=None` ⟹ **트리거 루프도 회수 루프도 안 뜬다.** `infra/staging/compose.i2.yml:335` 에는 있다. **재시도로 덮을 수 없다** · `post-deploy-a.txt` |
| ⓑ | `BF-11` ⑵⑷ 색 5종 계산 스타일 | **눈 확인** · 화면 회귀 0 | **Ted-확인** | 정적 대조는 이미 시험이 한다. 실화면은 로그인 뒤라 이 레인이 자격을 전사하지 않고 남긴다 |
| ⓒ | `BF-8` ⑴⑶ S-01 여백·폭 | 뿌리 `padding` > 0 · 최대폭 1200px · 히어로 680px 불변. **눈 확인** | **Ted-확인** | 같은 이유(로그인 필요) |
| ⓓ | `BF-7` ⑶ 스크린샷 내려받기 | **실브라우저(headless 아님) 크롬** 완주 | **Ted-확인** | 정의상 사람 자리다. 게다가 데이터셋이 0 이라 지금은 열 화면이 없다 |
| ⓔ | `BF-9` ⑴⑵ 계보 원천 edge | **실데이터셋**의 계보에 원천 → 루트 edge(`method` = null) | **red(준비)** | ⛔ 실데이터셋 0 ⟹ 잴 대상이 없다. **재적재 뒤에만 선다** |
| ⓕ | 미리보기 1건 실호출 | 실데이터셋 1건의 `previews` ≥ 1 ⟹ `I-D` partial 해소 | **red(준비)** | 같은 이유 |
| ⓖ | 맥 한글 파일명(NFD) 왕복 | 업로드·조회·내려받기까지 이름 무손상 | **red(준비)** | 업로드가 곧 실데이터 생성이다 — 매니페스트 밖 쓰레기 데이터를 dev 에 만들지 않았다(`deleteDataset` 이 없다) |

**계 — green 0 · red 1(ⓐ) · red(준비) 3 · Ted-확인 3.** ⚠ **red(준비)는 판정 red 가 아니다** — 잴 준비가 안 섰다는 뜻이고,
준비를 세우는 것이 곧 `§5` 재적재다.

### Ted 가 눈으로 볼 자리 — 정확한 주소

- 로그인 — `https://d31zgpff2091oh.cloudfront.net/` (계정·비밀번호 = `~/.config/colab-platform/dev-secrets/dev-logins.txt`)
- ⓑ·ⓒ — 로그인 뒤 **S-01 연구실 화면**(진입 `/`). 볼 것 = 뿌리 여백이 0 이 아니고 본문이 1200px 에서 멈추는가 ·
  히어로 내용 폭이 680px 그대로인가 · 정본 토큰으로 바뀐 색 5종이 종전과 같은 그림인가.
- ⓓ — 데이터셋 상세의 **스크린샷 버튼**. 실브라우저 크롬에서 내려받기가 **완주**하는가 · 잔존 앵커 0 · 취소 증상 미재현.
  ⛔ **지금은 열 데이터셋이 없다** — `§5` 재적재 뒤에 본다.

---

## 5. ⑹ 재적재 — **이 회차는 집행 0** (Ted 판정으로 범위가 바뀌었다)

**결론 = 돌리지 않았다.** dev 접촉은 `up.sh` 경로뿐이고 `load-seed.py` 는 **한 번도 부르지 않았다**.

### 5-a. 이 레인이 처음 세운 판정 — 그리고 Ted 가 답한 것

이 레인은 `03-HANDOFF §4.5` 창 8 ⑹ 축자(「⛔ **매니페스트 확정 전에는 실행하지 않는다 — dev 에
`deleteDataset` 이 없어 잘못 적재하면 지울 수단이 0 이다**」)를 근거로 **보류**하고 물음 셋을 올렸다.

**Ted 판정 (2026-09-06 ~02:15)** — ⑴ `manifest-s2.json` 이 확정 매니페스트다(`#28` 닫는다) ·
⑵ 적재 주체·연구실은 staging 과 동일(`〈334〉`-㉳-⑯ 초안 그대로) · ⑶ 계정 부트스트랩이 이 회차에 든다.

### 5-b. ⭑ 그 판정이 **다시 번복**됐다 — 적재 범위 변경 (2026-09-06)

**Ted 재판정** — 원천은 `COLAB_REFERENCE_DATA`(＝ `03 Reference-Data` · 창 8-a 초안이 쓴 같은 뿌리)이고
**`03_KWRA_conference-20260517T141236Z-3-001` 폴더는 제외**한다.

⟹ **`manifest-s2.json` 은 지금 적재할 매니페스트가 아니다** — 그 매니페스트가 덮는 것이 정확히 그 KWRA 폴더다.
새로 필요한 것 = **`01.level-data/`**(126파일 · 498MB · `01.precipitation` · `02.vegetation` · `03.drought`) ＋
**`02.File-format/`**(358파일 · 3.1GB · grib · nc · bin · tif · HDF5) 를 덮는 매니페스트이고,
**그 레벨·포맷 갈래가 곧 데이터셋 묶음 단위**여야 한다.

⛔ **이 레인은 여기서 멈춘다(HOLD).** 매니페스트 묶음이 Ted 확정으로 내려오기 전에는 `load-seed.py` 를 부르지 않는다.
**되돌릴 수단이 0 인 행위**(dev 에 `deleteDataset` 없음)에서 짐작으로 가지 않는다.

⭑ 남은 것 = `level-format-check.md`(레벨·포맷 갈래가 매니페스트로 재현되는지 실측) ＋ 매니페스트 확정 대기.
⭑ 재적재가 서면 **ⓔ·ⓕ·ⓖ 셋이 한꺼번에 잴 수 있게 되고**, `I-D` 의 partial 도 ⓕ 로 풀린다.

---

## 6. `t4g.small` 위험 감시 — 〈344〉-㉱ 규칙

**규칙** = ⑸ 중 어떤 단위든 OOM-kill 되면 그 자리에서 멈추고 보고(고침은 `t4g.medium` 승격이지 재시도가 아니다).
**실측** — 배포 뒤 **신규 OOM 0건**(`dmesg` 최신 항목은 여전히 2026-09-02 13:29:02 · 배포 이전 것).
자원 실사용(배포 70분 뒤) = viz 84.3MiB/640MiB · worker 71.8/512 · ai 59.3/256 · core 85.9/384 — **합 ≈ 301MiB / 상한 합 1,792MiB** · 스왑 사용 **0**.
⟹ 완화 판정(`〈344〉`)은 이 회차 동안 유지됐다. ⚠ 다만 **부하가 없었다** — 데이터 0 이라 렌더도 업로드도 안 돌았다. 실부하 판정은 재적재 회차 자리다.

---

## 7. ⑺ 판정 — 대장 갱신

| 항목 | 종전 | 이번 | 막는 것 |
|---|---|---|---|
| `BF-12` | `open` | `open` 무변 | ⭑ **ⓐ 가 red** — 그런데 `BF-12` 가 고친 결손(로거 부재)이 되살아난 것이 **아니다**. dev 에서는 **회수 루프 자체가 안 뜬다**(compose 결손). `post-deploy-a.txt` §원인 |
| `BF-11` | `open` | `open` 무변 | ⓑ 눈 확인(Ted) |
| `BF-8` | `open` | `open` 무변 | ⓒ 눈 확인(Ted) |
| `BF-7` | `open` | `open` 무변 | ⓓ 실브라우저 크롬(Ted) ＋ 열 데이터셋 |
| `BF-9` | `open` | `open` 무변 | ⓔ 실데이터셋 계보 — 재적재 선행 |
| `U-1` | `partial` | `partial` 무변 | **배포와 무관** — 8차 동결 해제 Ted 판정 ㉯ |
| `F-3` | `partial` | `partial` 무변 | **배포와 무관** — 9차 동결 해제 Ted 판정 ㉯ |
| `I-D` | `partial` | `partial` 무변 | 완료 정의의 **「미리보기 1건 실호출」** — ⓕ · 재적재 선행 |
| `V-4` | `done` | `done` 무변 | 없음 |

⛔ **「배포했으니 닫는다」로 세지 않았다** — 창 7 블록의 그 문장을 그대로 따랐다.

**문서 게이트 실측** — `work-item-consistency` **green**(대장↔산문 불일치 0) · `planning-freshness` **green**(임베드 15/15) ·
`work-item-selftest` **green**(17 케이스 · 대조군 1 · red 증명 16).

---

## 8. 후속으로 남기는 것

1. **런북 결손** — `deploy_doctor` 앞에 「EC2 `/opt/colab-repo` 를 배포 sha 로 맞춘다」 단계가 `infra/dev/README.md` 에 없다.
   EC2 에 `git` 이 없어 tar 동기화가 실질 절차다. **다음 회차가 README 에 적는다.**
2. **`dev.env` 자원 상한이 문서와 다르다** — 문서(`infra/dev/README.md`)는 기본값 `512/768/768/384`(합 2.3 GB)를 적고,
   EC2 실물은 **`384/512/640/256`(합 1.79 GB)** 이다. 어느 쪽이 정본인지 적히지 않았다 `[미확인]`.
3. **㉢ 유료 전환 실측** — 이 레인의 IAM 으로는 영영 못 잰다. 콘솔 확인 결과를 `§9` 에 한 줄로 남길 자리가 필요하다.
4. **`t4g.medium` 승격 판단** — `§6` 의 감시 결과를 근거로 Ted 가 정한다.

---

## 9. 산출물 · 로그 경로

전부 `dev-package/reports/window-8b/` 아래다(`.txt` — `*.log` 는 gitignore).

| 파일 | 무엇 |
|---|---|
| `pre-deploy-snapshot.txt` | 배포 직전 원격 실측(컨테이너·메모리·디스크·OOM·이미지·데이터 계수·롤백 태그) |
| `build.txt` | `build.sh` 전문 · 5 이미지 arch 실측 · `EXIT=0` |
| `ship.txt` | `ship.sh` 전문 · `docker load` 5건 · `EXIT=0` |
| `up.txt` | EC2 `up.sh` 전문 · 마이그레이션 2체인 · 4/4 healthy · 헬스 본문 |
| `deploy-web.txt` | S3 웹 업로드 96파일 계획·결과 |
| `cloudfront-check.txt` | 로컬 dist ↔ CloudFront 해시 자산 대조 |
| `deploy-doctor.txt` | `deploy_doctor` 전문 · `✓ 14 · ✗ 0 · ─ 0` |
| `post-deploy-a.txt` | ⓐ viz 회수 요약 실측 ＋ OOM 재확인 |
| `lane-report.md` | 이 문서 |

⛔ **어느 파일에도 비밀값이 없다** — DB URL·토큰·비밀번호·액세스 키는 파일 경로로만 부르고 값은 한 번도 출력하지 않았다.
