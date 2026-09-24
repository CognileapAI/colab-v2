# dev 재시드 문제 기록 — 2026-09-24 (1~4회차 · 로컬 검증 2건)

메타 — 기준 `b210ce5c`(corpus-upload-classify) · 가지 `corpus-reseed-issues` · task `199ecf26fcde4293808329dd19531aa8` ·
**dev 무접촉**(실행 자리 로그·`state.json`·덤프만 읽었다). file:line 은 `b210ce5c` 기준이고, 인용한 제품 파일은
dev 가 도는 `ea21d8c2aa54` 와 줄이 같다(`routes/ingestion.py` 만 달라 sha 를 붙였다).

- **목적** — `dev-package/tools/dev-reseed`(+ `dev-package/tools/dev-seed/runner.py`) 개선 intent 의 입력.
  dev-reseed 는 **검증용 데이터를 세우는 도구**다. 이 문서는 무엇이 시간을 먹었고 무엇을 바꿀 후보인지만 적는다.
  intent·결정·코드 변경은 하지 않는다.
- **범위** — dev 1차(08:33Z) · 2차(09:12Z·09:13Z 두 시도) · 3차(12:44Z) · 4차(13:37Z) ＋ 로컬 검증 2건
  (L1 12:20Z 재로그인·재개 · L2 12:58Z 업로드 필수 칸). 회차 상세의 정본은 `wu2-reseed-2026-09-24.md` §1–32.
- **시간** — 1차 시작 08:33Z → 4차 멈춤 14:18:59Z ≈ **5시간 46분**. dev 가 실제로 돈 시간은 ≈ 47분
  (1차 162s · 2차 3s+22s · 3차 ≈155s · 4차 2,488s). 나머지는 멈춘 자리 분석·수선·로컬 재현·서명 대기다.
  4차 seed 2,484s 중 **고정 대기 초과가 ≈ 1,566s**(격자 칸 180s × 4 · seq 18 격자 판정 846s).
  4차 멈춤 시점 dev 의 데이터셋 = **17/28**(`state.json` · done 15 · registered_no_preview 2).
- **전반** — preflight 11/11 · doctor 15/15 · `--rehearse` 10/10 이 **전부 green 인 채** 본 실행이 네 번 멈췄다.
  세 검사 중 **대상 sha 의 화면 걷기(seed)** 를 밟는 것이 없고, 러너↔제품 권한 모델·업로드 계약 정합을 보는 게이트도 없다
  (인계서 `HANDOFF-20260924-k3-k4-corpus.md` §5-6).

| # | 증상 | 원인 한 줄 | 임시 조치(commit) | 막았어야 할 검사 | 개선 후보 |
|---|---|---|---|---|---|
| 1 | 1차 projects 「대상 연구실을 선택해 주세요.」 | 권한 개정이 운영자 주체의 생성 4종에 대상 연구실 헤더 요구 · 러너는 교수를 임시 운영자로 둔 채 걷는다 | 운영자 창을 accounts 로 좁힘 `0d6a27b6` | 러너↔권한 모델 계약 | 계약 게이트 · 국면별 주체 선언 |
| 2 | 2차 projects 「지목점 project-new-button 해소 실패」 · 화면은 로그인 | 운영자 해제가 열린 세션을 무효화 → 401 → 로그인 화면 | 해제 뒤 재로그인 `c4cdd5ea` | 대상 sha 로컬 리허설 | 해제·재로그인을 리허설 원시동작으로 |
| 3 | (L1) `--from seed` 재개가 accounts 에서 「계정 관리 화면(account-create)이 열리지 않았다」 | 앞 회차가 이미 해제 → 재개 회차의 교수는 비운영자 | seed 첫 login 앞 운영자 올림 `71a1d95c` | 재개 경로 리허설 | 재개 전제(자격·상태)를 preflight 로 |
| 4 | 3차 datasets seq 1 「단계 이동 실패: ② 메타데이터 입력」 | 업로드 필수 칸(분류·유형·관측 간격·Lv0 출처)이 러너·계획·정본 어디에도 없음 | 배관 `d03b744e`·`02f5ab1f` · 값 서명 `b210ce5c` | 계약(required) ↔ 계획 대조 | 계약 게이트 · 값 출처를 정본에 |
| 5 | (L2) 「기간 고르기가 열리지 않았다」 · 3차 disabled 단추 click 성공 기록 | 가려진·비활성 요소 click 이 rc 0 | 기간 단추만 초점＋Enter `02f5ab1f` | 없음 | click 뒤 사후조건 · 비활성 사유 판독 |
| 6 | (L1) 엉뚱한 요소 누름을 선택자로 캐시 · 로그인 화면을 빈 프로젝트 목록으로 읽음 | `spot()` rc 0 캐시 · `project_index()` fail-open | 없음 | 없음 | 캐시 전 사후조건 · 로그인 화면 판별 |
| 7 | 4차 격자 칸 180s 초과 4회 · grid-skip 지목점 실패 6회 | 부재를 고정 상한으로 기다린다 · 건너뛰기 문구 사라짐 | 없음 | 없음 | 상태 판독형 대기 · 선택 단계 정리 |
| 8 | 재개 상태·실행 자리가 앞 회차 체크아웃에 묶임 · `result.json` 이 회차를 섞음 | `SEED_WORK_DIR` 기본값이 `$REPO_ROOT` · run-dir 누적 | `COLAB_SEED_WORK_DIR` 손 지정 | 없음 | 체크아웃 밖 상태 자리 · 회차별 결과 |
| 9 | 회차 기록 뼈대가 실행 체크아웃을 dirty 로 만든다 | `stage_report` 가 `$REPO_ROOT/dev-package/sessions/` 에 미추적 파일 | 손으로 정리 | 없음(preflight:git 은 **다음** 실행에서 증상만) | 기록은 run-dir 에만 |
| 10 | 앞 회차 seed.log 소실 · 진행 로그가 줄 중간에서 끊겨 지연 | 단계 시작마다 로그 비움 · `redact` 의 `sed` 블록 버퍼 | 러너 자체 로그로 대조 | 없음 | 추가 쓰기 · 줄 버퍼 |
| 11 | 접속 env 감싸개가 둘 · 내용이 다름 | `with-dev-env.sh` 는 `COLAB_DEV_SECRETS_DIR` 미해제 · 대상 ref 없음 | 추적 제외 `wu2-env.sh` | 없음 | 도구가 env 를 스스로 검증 |
| 12 | 파일럿은 사람이 SQL 을 낸다 · 중단 수단이 없다 · 판정 기준이 포맷을 모른다 | 러너 기능 아님 · `reseed.sh` 에 trap 없음 · 첫 절차의 SQL 이 소유자 롤 | 인계서에서 BYPASSRLS 롤로 정정 | 없음 | 파일럿을 러너 국면으로 |
| 13 | L1 이 datasets 를 「참조자료가 없어」 면제 → 업로드 칸 결함이 dev 3차에서 처음 드러남 | 레인에 참조자료 경로(`03 Reference-Data`)가 주어지지 않음 | L2 에서 실물로 재측 | 없음 | 로컬 리허설의 입력 선언 |
| 14 | 재시드 창 동안 사람이 dev 계정을 못 쓴다 | 최종화가 운영자 4명의 초기 비밀번호·`must_change_password` 유지를 검사 | Ted 비밀번호 초기화 연기 | 없음 | 사람 계정과 시드 계정 분리 |
| 15 | 4차 seq 18 「기준 격자 판정 표시가 나타나지 않았다」(846s) | **미확인** — §4 | — | — | §4 뒤에 붙인다 |

---

## 1. 멈춘 자리 (본 실행을 세운 것)

### #1 대상 연구실 헤더 — 1차 `projects`
- **증상** 「x 실패: 프로젝트 생성 실패(precipitation): 대상 연구실을 선택해 주세요.」(08:36:04Z). 덤프
  `.work/fail/project-precipitation-submit.txt` 에 빈 「대상 연구실」 combobox.
- **근거** `services/core-api/src/colab_core/app/target_scope.py:8`(`_CREATIONS` 4종) · `:31-34`(비운영자는 통과) · `:42-43`(거절) ·
  `frontend/src/components/project/ProjectFormModal.tsx:86` · prelude ④ 올림 `dev-package/tools/dev-reseed/stages.sh:486`.
- **원인** `bafae4a7`(2026-09-17 KST)이 운영자 주체에만 헤더를 요구한다. DR-4(`d5cd6ca9`, 09-14)에는 없던 규칙이고,
  러너는 교수를 임시 운영자로 둔 채 화면을 걸었다. `_CONTEXT` 8종(`getPreviewRender` 등, `:9-10`)도 같은 요구다.
- **임시 조치** ㈏ 운영자 창을 `accounts` 로 좁힘 — `0d6a27b6`(해제 `stages.sh:662`).
- **왜 못 잡았나** preflight 11 은 환경(git·aws·qemu·자원·계획 생성), doctor 15 는 배포 건강만 본다. 리허설 ⑻ 은 러너 `--phase report`
  (읽기 전용), ⑼ 는 첫 화면 제목만 읽는다. `dev-reseed-selftest` 는 dev 무접촉이라 러너 화면 경로가 없다.
- **개선 후보** ⓐ 제품 권한 규칙(`_CREATIONS`·`_CONTEXT`)과 러너 국면의 주체를 대조하는 게이트 ⓑ 국면별 주체(운영자/교수)를 계획에 선언.

### #2 운영자 해제 = 세션 무효화 — 2차 `projects`
- **증상** 「x 실패: 지목점 project-new-button 해소 실패. 마지막 사유 = ('text', '새 프로젝트') -> Element not found.」(09:14Z).
  URL 은 `/projects`, 화면은 「로그인」(`.work/fail/projects-fail.txt`).
- **근거** 발급 주장 `kernel/session_token.py:60-62` · 매 요청 재조회 `kernel/login_sessions.py:193-194` · 불일치 거절 `:226-228` ·
  API 해제 경로의 세션 폐기 `kernel/db_credentials.py:260-265` → `/me-v2` 401 → `frontend/src/api/client.ts:64-66` `clearIfCurrent` →
  `frontend/src/auth/store.ts:108-116`(suspended) · `:78-81`(`getToken()` null) → `frontend/src/auth/AuthGate.tsx:128-130` 로그인 화면.
- **원인** 자격을 어떤 길로 내리든 열린 세션은 닫힌다(제품 설계). ㈏ 옵션표가 이 결합을 몰랐다(보고 §12-1).
- **임시 조치** 해제 뒤 `--phase login` — `c4cdd5ea`(`stages.sh:672`). 당시 「재개 1회」 규칙으로 실물 미검증 → L1 A-2 에서 `POST /projects` 201×4 확인.
- **왜 못 잡았나** #1 과 같다. 로컬에서 대상 sha 로 seed 국면을 한 번도 돌리지 않았다.
- **개선 후보** ⓐ 운영자 올림/해제·재로그인을 리허설 원시동작으로(일회용 스택) ⓑ 해제 뒤 세션 유효성을 러너가 먼저 확인.

### #3 재개 회차의 운영자 창 부재 — L1 에서 발견(막지 않았으면 3차 멈춤)
- **증상** B-1 red 「x 실패: 계정 관리 화면(account-create)이 열리지 않았다 — 관리자 권한 계정으로 로그인했는지 확인한다.」
  (`local-verify-2026-09-24.txt` §B-1).
- **근거** `runner.py:1811-1814` 가 항목별 「이미 생성됨」 판정(`:1819-1822`)보다 **먼저** 계정 관리 화면을 기다린다.
- **원인** 앞 회차 ③ 이 이미 해제했으므로 `--from seed` 재개의 교수는 평범한 교수다.
- **임시 조치** `stage_seed` 첫 login 앞 `operator_grant` — `71a1d95c`(`stages.sh:651`). 보고 `8f90f7d7`.
- **왜 못 잡았나** preflight 는 재개 전제(누가 어떤 자격인가·state 의 어느 국면까지 왔나)를 보지 않는다.
- **개선 후보** ⓐ 재개 시 dev 의 자격 상태와 `state.json` 을 대조하는 preflight 항목 ⓑ 이미 끝난 국면은 화면을 열기 전에 건너뛰기.

### #4 업로드 필수 칸 — 3차 `datasets` seq 1
- **증상** 「x seq 1 실패: 단계 이동 실패: ② 메타데이터 입력 (기대 [data-testid="reg-name"])」(12:47:28Z). 덤프
  `…/agent-a9c33a67acf039b61/dev-package/tools/dev-seed/.work/fail/step-reg-step-2.txt` — 「분류 필수」「유형 필수」 `직접 선택해 주세요`,
  「② 메타데이터 입력」 `[disabled]`.
- **근거** `frontend/src/components/upload/RegisterArea.tsx:1164`(`classifyBlocked`) · `:1299` · 제출 검사
  `frontend/src/components/upload/UploadModal.tsx:1145`(#78) · 서버 `routes/ingestion.py:610`@`ea21d8c2aa54`
  (`_validate_create_required_metadata`) · 계약 `contracts/seams/fe-core.yaml:4871`(`required: [… category, dataType, observationInterval]`).
- **원인** `6705675d`(09-17 · 분류·유형 기본값 제거) · `e171c5c2`(09-16 · 관측 간격·Lv0 출처 필수). 값이 러너·`upload-plan.json`·
  정본 md 4건·`canonical-metadata.json`·k4 dev 스냅샷 **어디에도 없었다** → 28행 제안표(`upload-classify-proposal-2026-09-24.md`).
- **임시 조치** 배관 `d03b744e`(서명 전 계획 생성 거절) · `02f5ab1f`(러너 `select_classify`·`fill_interval`·`fill_source`,
  `runner.py:1165`·`:1175`·`:1185`) · 보고 `2d24bf0c` · Ted 서명 `b210ce5c`(값 `dev-package/tools/dev-seed/upload-classify.json`). 소요 12:47Z→13:37Z.
- **왜 못 잡았나** preflight ⑽ 은 정본 md → 28/18 만 봤다. 계약의 `required` 와 계획 행을 대조하는 자리가 없다.
- **개선 후보** ⓐ `fe-core.yaml` 의 `DatasetCreate.required` ↔ 계획 행 대조 게이트(제품 병합 시점에 red) ⓑ 필수 값의 출처를 정본 md 로 올리기
  ⓒ 제품 필수 칸 개정 PR 의 완료 조건에 러너 갱신 포함.

## 2. 러너 판정의 약한 자리 (멈추거나 시간을 버리게 한 것)

### #5 누른 척 click — rc 0 인데 동작 없음
- **증상** L2 R2 「기간 고르기가 열리지 않았다」 — `reg-period-open` 중심의 `elementFromPoint` = `DIV.modal-h`(`upload-classify-local-2026-09-24.txt`).
  3차 러너 로그 `.work/logs/run-20260924-214536.log` — 비활성 「② 메타데이터 입력」 을 누르고 「지목점 reg-step-2 <- role:button」 성공 기록 → 「대기 시간 초과(15s)」 ×4.
- **근거** `runner.py:603-607`(rc 0 이면 성립) · `goto_step` `:1239-1250`(`reg-next` 비활성이면 탭 단추 폴백 후 15s 대기 4회) ·
  `activate` 머리말 `:1198-1205`(2026-09-13 「+ 추가」 같은 계열 선례).
- **원인** agent-browser `click` 은 가려지거나 비활성인 요소에도 0 을 돌려준다. 러너는 사후조건 없이 성공으로 센다.
- **임시 조치** 기간 단추 여닫기만 `activate`(초점＋Enter, `:1113`·`:1118`) — `02f5ab1f`. `spot()` 22 자리의 기본 `click` 은 그대로(보고 §32 ⒃).
- **왜 못 잡았나** 러너 픽스처는 계획 매핑만 보고 화면을 걷지 않는다.
- **개선 후보** ⓐ 모든 click 에 사후조건(다음 표식 출현) ⓑ `reg-next` 비활성이면 막는 칸을 읽어 즉시 실패(60s 대기 제거).

### #6 fail-open 둘 — 선택자 캐시 · 프로젝트 목록
- **증상** L1 — `vite` 개발 서버에서 `spot()` 문구 후보가 `<style>` 안 「새 프로젝트」를 누르고 성립으로 캐시(dev 번들에서는 미재현).
  `project_index()` 는 로그인 화면을 빈 목록으로 읽는다(2차에서는 뒤의 지목점 실패가 막았다).
- **근거** `runner.py:603-607`(캐시 저장) · `runner.py:865-893`(`project-list-error` 없으면 행 0 을 「없음」으로 반환).
- **원인** 성공 판정이 「명령 rc」와 「오류 표식 부재」 뿐이다.
- **임시 조치** 없음(보고 §25 ⑾⑿).
- **개선 후보** ⓐ 캐시 전 사후조건 ⓑ 목록 판독 전 로그인 화면(`login-submit`) 판별 — `stage_verify` 는 이미 이 판별을 한다(`stages.sh:889-900`).

### #7 고정 대기로 버린 시간 — 4차
- **증상** seq 6·7·15·17 「! 대기 시간 초과(180s) 격자 칸」→「격자 칸 미출현 — 화면이 좌표 보유로 판정. 격자 부착 생략」.
  seq 8~11·13·14 「! 지목점 grid-skip 해소 실패(선택 단계라 계속): ('text', '건너뛰기 — 나중에 올릴게요')」.
- **근거** `runner.py:1271-1279`(부재를 180s 상한으로 기다림) · `:1262-1268`(건너뛰기 후보) · 4차 러너 로그
  `.work/logs/run-20260924-223757.log`. seq 17 은 282.7s 중 180s 가 이 대기였다.
- **원인** 「격자 칸이 안 붙는다」가 정상 갈래인데 그 판정을 시간 초과로만 낸다. 건너뛰기 문구는 현 화면에 없다.
- **임시 조치** 없음. 비치명이라 실행은 이어졌다(합계 720s).
- **개선 후보** ⓐ 화면의 격자 판정 상태(`data-grid-state` 등)를 읽어 즉시 분기 ⓑ 계획에 행별 기대(격자 부착/좌표 보유)를 싣기 ⓒ 사라진 선택 단계 정리.

## 3. 운영의 함정 (실행을 느리게 하거나 기록을 흐린 것)

### #8 상태·실행 자리가 앞 회차 체크아웃에 묶인다
- **증상** 재개 상태(`state.json`: 계정 4 created · `password_rotated`)가 1차를 낸 `agent-a9c33a67acf039b61` 의
  `dev-package/tools/dev-seed/.work` 에만 있다. 3·4차는 다른 체크아웃에서 냈다 → `COLAB_SEED_WORK_DIR` 를 손으로 줘야 했다(어드바이저 발견).
- **근거** `dev-package/tools/dev-reseed/reseed.sh:247`(기본값 `$REPO_ROOT/dev-package/tools/dev-seed/.work`). run-dir 도 같은 워크트리
  `…/dev-package/reports/dev-reseed-runs/wu2-20260924T0834Z`. 4차 `result.json` 실측 — `startedAt 08:33:26Z`(1차) · `durationSec 2544`
  (1·4차 단계 합) · `report` 조각 `12:47:28Z`(3차 — `stage_report` 가 자기 조각보다 먼저 결과를 만든다) · `blocked` 에 09:12Z `preflight:git` ·
  `doctorSummary` 는 08:34Z 값.
- **원인** 상태·결과의 자리가 「체크아웃」과 「run-dir 누적」에 매여 있다(보고 §18 ⑺⑻).
- **개선 후보** ⓐ 상태를 체크아웃 밖(대상 dev·회차 식별자 키)에 ⓑ 회차마다 결과를 따로, 누적은 색인으로 ⓒ 재개 시 상태 자리 불일치를 preflight 가 거절.

### #9 회차 기록 뼈대가 실행 체크아웃을 dirty 로 만든다
- **증상** 3차를 낸 `agent-a604d198b8b428287` 에 `?? dev-package/sessions/DR-4-run-20260924T124453Z.md`(21:47 KST 생성 · 이후 정리됨).
  4차를 낸 `agent-ad12aacdc6d835b49` 에도 `DR-4-run-20260924T133731Z.md` 가 생겼다(23:18:59 KST). 그 체크아웃에서 다음 실행은 preflight:git 에 걸린다.
- **근거** `stages.sh:1212-1215`(바꾸는 단계가 돌면 `$REPO_ROOT/dev-package/sessions/` 에 쓴다) · `preflight.sh:43-45`(작업 트리 청결).
- **정정** 2차 시도 1 의 「작업 트리가 깨끗하지 않다 — 4 건」(`blocked.jsonl`)은 보고 §14 가 「커밋 후 재시도」로 적었다 —
  회차 기록 탓이 아니라 수선 파일 미커밋으로 읽힌다(§19 의 네 파일).
- **개선 후보** ⓐ 기록은 run-dir 에만, 레포 반영은 사람이 ⓑ preflight 가 자기 도구의 산출물만 있는 dirty 를 구분해 안내.

### #10 로그가 덮이고 늦게 보인다
- **증상** 실행 자리 `logs/seed.log` 에 4차만 남았다(1~3차 소실 — 3차 datasets 기록은 러너 자체 로그 `.work/logs/run-20260924-214536.log` 에만 있다).
  4차 도중 `seed.log` 가 22:58:17 KST 에 「· 등록 확정(reg-done) — 자동 재시도 」 에서 줄 중간으로 끊긴 채 20분 멈춰 보였다. 같은 시각 러너 로그는 seq 18 까지 진행.
- **근거** `dev-package/tools/dev-reseed/lib.sh:133`(`: > "$STAGE_LOG"`) · `lib.sh:18-22`(`redact` = `sed -E`, `-u` 없음) · `lib.sh:80`
  (`"$@" 2>&1 | redact | tee -a`). 러너는 줄마다 flush 한다(`runner.py:147-153`) — 지연은 `sed` 블록 버퍼다.
- **정정** 오케스트레이터가 본 「등록 확정(reg-done) — 자동 재시도」 1회는 모든 건에 찍히는 「… 자동 재시도 없음」(`runner.py:1606`)이 버퍼 경계에서 잘린 것이다. 재시도는 없었다.
- **개선 후보** ⓐ 단계 로그를 회차별 파일로(덮지 않기) ⓑ 줄 버퍼(`sed -u` 등) ⓒ 진행 판독의 정본을 `state.json` 으로 명시.

### #11 접속 env 감싸개가 흩어져 있다
- **증상·근거** `~/.config/colab-platform/with-dev-env.sh` 는 `dev-operator.env`(`COLAB_DEV_SECRETS_DIR` 를 export)를 싣고 **unset 하지 않으며**
  `COLAB_RESEED_TARGET_REF` 도 안 싣는다. 실제 실행은 추적 제외 `dev-package/reports/dev-reseed-runs/wu2-env.sh`(unset ＋ 대상 ref)로 했다.
  규칙은 `.agents/skills/dev-reseed/SKILL.md:101-106` 에만 있고, 도구는 그 이름을 읽지 않는다고만 적혀 있다(`reseed.sh:26-30`).
- **개선 후보** ⓐ 레포 안 감싸개 하나 ⓑ `reseed.sh` 가 금지 env 를 보면 거절(78) ⓒ 대상 ref 를 인자로 필수화.

### #12 파일럿이 러너 기능이 아니다
- **증상** 「첫 업로드 뒤 자동 메타 non-null 확인」은 사람이 `state.json` 을 보다가 SQL 을 내는 절차다(`wu2-prereq-2026-09-24.md` §7).
  첫 절차 §7-2 는 소유자 URL(`platform-owner-db.url`)로 내라고 적었다 — FORCE RLS 로 **거짓 0**(보고 §6 · 인계서 §4-(b)에서 BYPASSRLS 로 정정).
  중단하려면 `reseed.sh` 에 trap 이 없고 `run()` 이 파이프라(`lib.sh:80`) bash 만 죽이면 러너가 계속 올린다 → 프로세스 그룹 kill →
  `result.json`·회차 기록이 안 남는다(`reseed.sh:337-343` 의 report 가 돌지 못함).
- 판정 기준 「첫 3건 전부 null 이면 중단」(인계서 §4-(b))은 포맷을 모른다(seq 1 bin · seq 2 nc · seq 3 npy). 4차 실측으로 seq 1(Binary)도
  crs·grid·period_start 가 찼다 — 격자 파일 지정 때문으로 보인다. 도구 안에 autometa 를 보는 자리는 없다(`stages.sh`·`runner.py` 에 해당 판독 0).
- **개선 후보** ⓐ `datasets` 국면에 N 건 뒤 읽기 전용 autometa 판독(BYPASSRLS)과 포맷·격자 지정별 기대표 ⓑ 판정 미달이면 러너가 스스로 멈추고 결과를 남김
  ⓒ `reseed.sh` 에 신호 trap(자식 정리 ＋ report).

### #13 로컬 검증 레인에 참조자료가 주어지지 않았다
- **증상** L1 이 `datasets`·`verify`·`report` 를 「참조자료가 없어」 명시 면제(보고 §21 · `local-verify-2026-09-24.txt` 의 `SKIP(local exemption)` 3줄).
  참조자료는 `/home/ttlhi10/workspace/00_Project/00 CoLAB/03 Reference-Data`(4.4 GB)에 있었다. L2 는 그것으로 R1 을 dev 3차와 같은 문면으로 재현했다.
- **원인** 레인 지시에 경로가 없었다. L1 에서 datasets 를 돌렸다면 #4 는 3차 전에 나왔을 것이다.
- **개선 후보** ⓐ 로컬 리허설 명령이 `COLAB_REF_ROOT` 를 필수 입력으로(없으면 78) ⓑ 면제는 건수·사유와 함께 **다음 dev 실행의 go 조건**에서 빼기.

### #14 재시드 창 동안 사람의 dev 계정이 묶인다
- **증상** Ted 가 자기 계정(운영자 4명 중 하나) 비밀번호를 초기화하려다 3차 뒤로 미뤘다.
- **근거** `dev-package/tools/dev-reseed/accounts.py:56`(운영자 초기 자격 변경 거절) · `:68`(최종 정책) · `:84`(`mustChangePassword` 기대) ·
  `stages.sh:741-752`(`account_finalize`). 초기 비밀번호 전략 = `email`(`accounts.py:13`·`:40`).
- **개선 후보** ⓐ 사람 계정과 시드 전용 계정 분리 ⓑ 최종화 검사를 「시드가 만든 직후」로 한정하고 이후 사람 변경은 허용 ⓒ 창의 시작·끝을 사람에게 알림.

---

## 4. 4회차 (진행 중 기록 · 결과 분석은 뒤에 붙인다)

⚠ **중간 기록이다.** 이 문서 작성 중 14:18:59Z 에 seed 가 종료코드 1 로 끝났다. 원인 분석 전이다.

- 실행 — 13:37:31Z(`RUN_ID 20260924T133731Z`) · 체크아웃 `agent-ad12aacdc6d835b49`(`corpus-upload-classify` `b210ce5c`) ·
  run-dir 는 1~3차와 같은 `…/agent-a9c33a67acf039b61/dev-package/reports/dev-reseed-runs/wu2-20260924T0834Z` · `COLAB_SEED_WORK_DIR` 명시(같은 워크트리의 `.work`).
- preflight 11/11(4s) → 올림 `INSERT 0 1` → login → accounts 4건 「이미 생성됨」 → 해제 `DELETE 1` → 재로그인 → projects 4건 「이미 완료」 → datasets 13:37:57Z.
- **파일럿 통과**(오케스트레이터 실측) — seq 1 Binary · seq 2 NetCDF 모두 `d3_dataset_autometa` 행 있음, crs·grid·period_start non-null
  (BYPASSRLS `/etc/colab/backup-platform-db.url` 읽기 전용 SQL). ⇒ 운영자 해제 뒤 **교수 세션으로 업로드·등록이 선다**는 첫 실측.
- 진행 — seq 1~17 등록(done 15 · `registered_no_preview` 2 = seq 13·14 「형식 인식 실패」). seq 2 50.8s. seq 16 「격자 경계 위생 실패 — 지도형 미생성」(비치명).
- **#15 멈춘 자리** — seq 18(GK-2A LST 변환 결과 · 143 파일 · 469,818,560 B) 기준 격자 2건 지정 뒤
  「! 대기 시간 초과(846s) 격자 판정」→「x seq 18 실패: 기준 격자 판정 표시가 나타나지 않았다.」(`runner.py:1286-1311`).
  덤프 `…/agent-a9c33a67acf039b61/dev-package/tools/dev-seed/.work/fail/18-failed.txt` — 화면에 「그리는 데 너무 오래 걸려요.
  조각 하나나 좁은 기간으로 다시 해 보세요.」 · 「올린 파일 145개」. seq 18 은 L2 가 밟지 않은 24행 중 하나다(보고 §32 ⒀).
- 기록 — `result.json` `outcome failed` · `failedStage seed` · seed 2,484s. 회차 기록 뼈대가 `agent-ad12…` 에 미추적으로 생겼다(#9).
- 뒤에 붙일 것 — seq 18 원인 · 재개(`--from-seq 18`) 결과 · 28건 autometa 5축 계수 · verify·최종화 결과.

## 5. 개선 방향 후보 (판단은 intent 에서)

전제 — dev-reseed 의 산출물은 **검증용 데이터**(28건·계보 18·autometa)다. 화면 회귀 시험은 부산물이다.
autometa 는 업로드 분석 사건으로만 들어온다(`routes/ingestion.py:1004`@`b210ce5c` `apply_autometa` · intent Q1).

| 안 | 무엇 | 얻는 것 | 치르는 것 |
|---|---|---|---|
| A 화면 걷기 유지 ＋ 대상 sha 로컬 end-to-end 리허설 | 일회용 스택(대상 sha 이미지·번들·참조자료 실물)에서 seed 전 국면을 먼저 돈다 | #1~#5·#13·#15 계열을 dev 전에 잡는다. 러너 구조는 그대로 | 리허설에 수십 분·4.4 GB. 화면 개정마다 러너 수선은 계속 |
| B 제품 공개 API 로 업로드·등록 | 화면이 부르는 같은 API(`/uploads`→전송→분석→`/datasets`)를 러너가 직접 | DOM·click 판정(#5~#7) 소거. 계약(`fe-core.yaml`)이 변경을 알려준다 | 업로드 전송·대상 연구실 헤더·필수 칸을 러너가 재현. `load-seed.py` 직적재와 달리 분석 사건을 타는지 실측 필요 |
| C 혼합 | 대량은 B, 대표 표본 몇 건만 화면 걷기 | 속도와 화면 확인을 나눠 가진다 | 두 경로 유지 비용 |
| D 러너↔제품 계약 게이트 | `DatasetCreate.required`·`_CREATIONS`/`_CONTEXT`·러너가 쓰는 testid 를 계획·러너와 대조, 제품 PR 에서 red | 개정 시점(#1·#4)에 잡는다. A·B·C 어느 쪽과도 겹쳐 쓸 수 있다 | 대조 규칙 유지. 화면 동작(#2·#5)은 못 본다 |
| E 실행 자리·기록 분리 | 상태·run-dir·회차 기록을 체크아웃 밖·회차별로 | #8~#10 소거, 재개가 체크아웃과 무관 | 기존 `--from seed` 자리 규약 이전 |
| F 러너 판정 강화 | click 사후조건 · 상태 판독형 대기 · 파일럿 국면 · 신호 trap | #5~#7·#12 | 러너 코드량. 화면 구조에 더 묶인다(A 와 같은 비용) |

## 6. 관련 별건

- dev DB 가 2026-09-15 04:17~07:27Z 사이 **행만** 비워진 사건 — 주체 미확인(인계서 §3-3).
- dev 야간 백업 크론이 9-13 이후 죽어 있다 — EC2 `/etc/cron.d/colab-dev` 가 `infra/dev/install-cron.sh:49` 정본보다 옛 판(`wu2-prereq` §2-3).
- 백업 행수 급감 경보 권고(미착수) · 크론 드리프트 검사 없음(인계서 §5-5).
- `variables` 축은 재시드로 안 채워진다(0/28) — 후속 PATCH `d3_catalog.replace_variables`(`services/core-api/src/colab_core/domains/d3_catalog.py:827`).
- `--rehearse` 가 배포 0건인데 `--release-plan`·`HEAD = 후보 sha` 를 요구(`stages.sh:1053-1056` · `wu2-prereq` §3-3).
- `ship.sh` 가 `/opt/colab-repo` 를 갱신하지 않는데 재시드 도구는 거기를 본다(`wu2-prereq` 후속 ⑶).
- 3차가 dev 에 남긴 미등록 업로드(만료 24h · 보고 §32 ⒁). 4차 덤프의 「올리다 만 것이 있어요」 9줄과의 관계는 미확인.
- `stages.sh:667` 주석의 줄 인용(`session_token.py:59-61` · `login_sessions.py:192-206`)이 실제 자리(`:60-62` · `:193-194`·`:226-228`)와 어긋난다.
