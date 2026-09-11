> spec: dev-package/prd/specs/stage1-stage2-closeout.md

> 2026-09-11 보류 해소: 실패 업로드3건 실제 삭제·정상 파일6개 보존. BF-10·PA-G는 단계 미정 backlog/open으로 이동(미구현, 자동 착수 없음). Stage1 완료62/미완료0/보류0, Stage2 완료94/미완료1(I4)/보류0, 백로그2건. 근거 `sessions/20260911-deferred-closeout.md`, `reports/deferred-closeout/results.json`. 아래 기존 날짜의 수치는 당시 이력이다.

# stage 1·2 종료 Implementation Plan

> **For agentic workers:** 위임 원칙(글로벌 `CLAUDE.md`) ＋ `lane-worker` 에이전트로 태스크당 레인 1개(권고), 또는 `executing-plans`(로컬 vendored)로 이 세션에서 직접. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 대장과 실물을 먼저 일치시킨 뒤 stage 1·2의 실제 잔여 개발을 독립 라운드로 끝낸다. Google 로그인과 격자선·눈금은 승인된 후속 이슈로 유예한다.

**Architecture:** 첫 라운드는 기록 재검증만 수행해 실제 개발 범위를 줄인다. 이후 저장소, 시험 효율, 운영, 미리보기 회수, 코드리뷰 후속, 편의 기능을 파일 면과 완료 기준이 겹치지 않는 라운드로 순차 집행한다.

**Tech Stack:** Git, GitHub Actions, CoLAB gates, Python 3.12, React, PostgreSQL, S3, Terraform, agent-browser

**Spec:** `dev-package/prd/specs/stage1-stage2-closeout.md`

## 2026-09-11 최신 실행 상태

전체 실행 승인 후 U-2 실제 회수·IS4 복구·I3 실제 cron RED→동일 후보 GREEN·TL-2 실제 정기 분류를 완료 수용했다. Stage 1 완료62/미완료0/보류1, Stage 2 완료93/미완료1/보류2. TL-2는 실제 예약 발행·staging 정기분류 수용, I4는 현재 글로벌 계정 권한 부족·알람 수신 설정 미확인이다. 나머지 실행·입력 상태는 `sessions/20260911-stage12-execution.md`에서 추적한다. 아래 준비·배포 수치는 당시 이력이다.

미완료5건의 실행 준비와 입력·승인 경계는 `sessions/20260911-stage12-execution-preparation.md`에서 추적한다. 대장 상태는 유지하며 현재 준비 후보는 c329, 시험 시작은 d564다.

후속 제품 d56428d: 전체61/0/0·main CI success·dev배포·운영자doctor15/0/0. TL-2 전수장부450/596개 발행과 실제 자동174벌 분류(삭제0)를 확인했다. TL-2는 매시간 publisher 설치와 staging 정기주기 미실측으로 partial 유지. 전체 잔여5·유예3은 불변. 최신 근거 `reports/stage12-tl2-deploy/release.md`. 아래30f5는 직전 수용 이력이다.

main/dev30f5adf 배포 및 운영자 doctor 단일15/0/0, 같은 트리 전체검사 before/after 각각61/0/0을 확인했다. G10·U-1·F-3·J-1·CR-2를 수용했다. 전체 종료는 미완료: U-2 실제 회수, IS4 exact plan apply, I3 cron red/green, I4 IMDS 읽기 권한·cron·외부 알람, TL-2 자동 연결·staging 실제 주기가 남는다. TL-2 실제 자료 분류는 완료했으나 자동 연결 누락을 수정 중이므로 Task6 완료로 표시하지 않는다. 실행 패킷과 제한은 `reports/stage12-release-acceptance/acceptance.md`.

## Global Constraints

- 실행은 깨끗한 최신 `origin/main` 작업 사본에서 시작한다.
- 완료 138건을 근거 없이 재개봉하지 않는다.
- 대장 상태는 오케스트레이터 한 명만 수정한다.
- 제품 데이터·S3 객체·미리보기 캐시는 사용자 별도 승인 없이 삭제하지 않는다.
- 관련 단독 게이트의 준비 실패를 성공으로 세지 않는다.
- 각 구현 라운드는 실패 시험, 최소 구현, 단독 게이트, 수용 검토 순서를 지킨다.
- prod와 `after_stage2` 구현은 이 계획의 범위 밖이다. Stage 3 최우선은 `BO-1` 운영자 계정 추가 백오피스이며 상세 발급 설계는 별도 확정한다.
- 2026-09-10 사용자 결정 원문: `dev-package/sessions/20260910-stage12-decisions.md`. main push·staging/dev 배포·실제 삭제는 각각 실행 직전 승인; 로컬 구현·시험·문서는 연속 진행한다.
- 이 파일은 전체 순서 계획이다. 각 구현 라운드의 구체적인 파일 경계·실패 시험·완료 증거는 자식 사양·계획에서 확정한다.

---

### Task 1: `R-S12-VERIFY` — 9건 재검증

2026-09-10 조사 완료: `dev-package/sessions/s12-verify.md`. X-7 완료 수용, 다른 10건(승인 대조 2건 포함)은 명시된 dev 검증·결손 조건 유지. 최초 6게이트 5/1/0과 h5py 환경 보완 뒤 viz 단독 성공을 별도 기록했다. 개별 배포 검증 대기는 독립 로컬 구현의 착수를 막지 않는다.

**Files:**
- Create: `dev-package/prd/specs/s12-verify.md`
- Create: `dev-package/prd/rounds/R-S12-VERIFY.md`
- Create: `dev-package/sessions/s12-verify.md`
- Modify: `dev-package/work-items.yaml`
- Modify: `dev-package/03-HANDOFF.md`

**Interfaces:**
- Consumes: 최신 `origin/main`, dev 실행 SHA, 기존 CI·배포 근거
- Produces: 재검증 9건의 done 또는 정확한 미충족 조건

- [x] **Step 1: 기준 SHA와 승인된 변경을 고정한다**

Run: `git fetch origin main && git status --short --branch && git rev-list --left-right --count origin/main...HEAD`

Expected: HEAD와 `origin/main` 동일, 앞뒤 수 `0 0`. 승인된 미커밋 문서는 폐기하지 않고 별도 diff/hash baseline으로 보존한다. dirty를 clean으로 보고하지 않는다.

- [x] **Step 2: 재검증 행렬을 작성한다**

Rows: `BF-7`, `BF-8`, `BF-9`, `BF-11`, `BF-13`, `I3`, `BF-12`, `X-7`, `WU-PREVIEW`.

Columns: 완료 정의, main 포함 SHA, 관련 게이트, dev 확인, 미충족 조건, 판정.

- [x] **Step 3: 항목별 관련 게이트와 dev 실물을 확인한다**

Expected: 실제 실행한 게이트만 green으로 기록하고 CI skip은 미실행으로 기록한다. dev 확인은 같은 배포 SHA를 가리켜야 한다.

- [x] **Step 4: `U-1`과 `F-3` 승인 이력을 함께 대조한다**

Expected: 2026-09-10 현행 계약 승인으로 제품 판정 대기를 해소한다. 최신 시험·dev 배포를 재검증한 뒤에만 마감 후보에 넣는다.

- [x] **Step 5: 대장을 먼저 갱신하고 반영본을 맞춘다**

Expected: 확인된 항목만 `done`; 나머지는 상태 유지와 해제 조건 기재. `work-item-consistency` green.

### Task 2: `R-S1-STORAGE` — S3 고아 바이트 정리

**Files:**
- Create: `dev-package/prd/specs/s1-storage.md`
- Create: `dev-package/prd/rounds/R-S1-STORAGE.md`
- Create: `services/core-api/src/colab_core/app/storage_maintenance.py`
- Modify: `services/core-api/src/colab_core/domains/d3_catalog.py`
- Modify: `services/core-api/src/colab_core/domains/d5_ingestion.py`
- Modify: `services/core-api/src/colab_core/app/routes/upload_transfers.py`
- Modify: `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py`
- Test: `services/core-api/tests/test_storage_maintenance.py`
- Test: `services/pipeline-worker/tests/test_storage_reaper_dbint.py`

**Interfaces:**
- Consumes: `I-D`와 `U-1`의 저장소 계약
- Produces: 원장이 아는 키만 대상으로 하는 실패 안전 회수 경로

- [x] **Step 1: 저장 Port와 만료 스윕의 현재 호출 경계를 조사해 사양에 고정한다**

Expected: 버킷 전체 스캔 0, 등록된 업로드 삭제 0, 완료 전송 메타 원장은 completed_at 기준 7일 보관한다. 원본 파일 TTL과 구분하고 등록 업로드를 보존한다.

- [x] **Step 2: 실패 시험을 작성한다**

Cases: S3 삭제 실패 시 원장 행 유지, 등록 업로드 보존, 열린 전송 보존, 완료 전송 보존 기간, 대상 0건 판정.

- [x] **Step 3: 실패 시험의 RED를 확인하고 최소 구현을 수행한다**

Expected: 객체 삭제 성공 뒤에만 원장 행을 제거하며 재시도 가능성을 유지한다.

- [x] **Step 4: 단독 서비스 게이트와 S3 경계 시험을 실행한다**

Expected: 판정 실패 0, 준비 실패 0. 실제 객체 삭제는 수행하지 않는다.

### Task 3: `R-S1-GATE-PERF` — G10 게이트 내부 병렬화

**Files:**
- Create: `dev-package/prd/specs/s1-gate-perf.md`
- Create: `dev-package/prd/rounds/R-S1-GATE-PERF.md`
- Modify: `gates/tools/service-tests.sh`
- Modify: `gates/tools/service-tests-selftest.sh`
- Modify if measured bottleneck requires: `gates/tools/frontend-test.sh`

**Interfaces:**
- Consumes: 기존 게이트 수집·실행 계수
- Produces: 동일 판정 의미를 보존하는 더 빠른 게이트

- [x] **Step 1: 병렬화 전 기준 계수를 같은 트리에서 측정한다**

Expected: 수집·실행·skip·deselect·실패 수와 전체 시간을 기록한다.

- [x] **Step 2: 게이트 내부 시험만 병렬화하고 실패 픽스처를 재실행한다**

Expected: `gates/config/parallelism.toml`의 게이트 간 `serial` 의미는 유지하고, 판정 계수와 준비 실패 의미도 동일하다.

- [x] **Step 3: 같은 트리에서 전후 시간과 판정 계수를 비교한다**

Expected: 실패·skip·deselect 수 불변, 준비 실패 0, 측정 가능한 시간 단축.

### Task 4: 격자선·눈금 범위 제외 확인

- [x] **2026-09-10 사용자 결정 반영**: 기존 배경과 커서 좌표 수용. `BF-10`은 미구현 단계 미정 `backlog/open`으로 stage 1·2 필수 범위에서 제외한다.
- [x] **후속 이슈 연결**: 화면과 저장 PNG 양쪽의 동일 격자선·눈금은 https://github.com/CognileapAI/colab-v2/issues/10 에서 추적한다. 별도 착수 승인 전 구현하지 않는다.
- [x] **stage 1 종료 계수 검증**: 완료62·미완료0·보류1. 격자선·눈금은 기존 사용자 결정에 따른 보류 그대로이며 구현하지 않았다. 근거 `sessions/20260911-stage12-execution.md`.

### Task 5: `R-S2-OPS` — 복구·배포·운영 관측

**Files:**
- Create: `dev-package/prd/specs/s2-ops.md`
- Create: `dev-package/prd/rounds/R-S2-OPS.md`
- Modify: `infra/dev/compose.yml`
- Modify if staging evidence requires: `infra/staging/compose.i2.yml`
- Modify: `infra/README.md`
- Discover in child spec: 추적·로그·알람을 연결할 서비스 경계
- Test: 운영 설정 selftest와 복구 리허설

**Interfaces:**
- Consumes: `IS4`, `I3`, 기존 `R-1` 복원 결과
- Produces: 맨몸 state 복구, 배포 자동화 완주, 추적·로그·알람·레지던시 근거

- [x] **Step 1: IS4 맨몸 state 복구를 격리 환경에서 재현한다**

Expected: 문서만 사용해 복구하고 `terraform plan`이 `No changes`를 출력한다. 준비 당시에는 실제 apply를 수행하지 않는다.

후속 전체 실행 승인으로 고정 hash 계획을 1회 적용하고 후속 No changes·health200을 확인했다. 근거 `sessions/20260911-stage12-execution.md`.

- [x] **Step 2: I3의 15개 완료 조건을 최신 배포 이력으로 다시 센다**

Expected: 이미 충족된 조건은 근거로 닫고 실제 미충족 조건만 구현 범위로 남긴다.

기존 유효한 조건 증거와 실제5분 cron RED→같은 후보 GREEN을 대조해 I3를 완료 수용했다. staging 배포 검증15/0/0은 dev 자동 doctor 판정과 별개다. 근거 `sessions/20260911-stage12-execution.md`.

I3의 cron 5분·실제 red/green 리허설 기준은 `dev-package/sessions/I3.md`의 기존 확정값을 사용한다. 재질문하지 않으며 실행 직전 Q7 승인 경계는 유지한다.

- [ ] **Step 3: I4 관측 범위를 독립 실패 시험과 함께 구현한다**

Required: 분산 추적, 구조화 로그, 알람, 데이터 레지던시 기록, 기존 복원 결과를 소비하는 운영 리허설.

기존 복원 증거를 재사용한다. 새 결함·근거 없이 복원을 반복하거나 WAL 범위를 확대하지 않는다.

- [ ] **Step 4: staging 리허설과 dev 완료 판정을 분리한다**

Expected: dev `deploy_doctor` 한 번의 실행 15/15, skip 0.

### Task 6: `R-S2-PREVIEW-RETENTION` — 미리보기 회수

**Files:**
- Create: `dev-package/prd/specs/s2-preview-retention.md`
- Create: `dev-package/prd/rounds/R-S2-PREVIEW-RETENTION.md`
- Modify after BF-12 close: `services/viz-render/src/colab_viz/kernel/logging_setup.py`
- Modify after BF-12 close: `services/viz-render/src/colab_viz/domains/d7_visualization/tile_reclaim.py`
- Modify after BF-12 close: `services/viz-render/src/colab_viz/domains/d7_visualization/ownership.py`
- Test: `services/viz-render/tests/test_app_logging.py`
- Test: `services/viz-render/tests/test_tile_reclaim.py`
- Test: `services/viz-render/tests/test_artifact_ownership.py`

**Interfaces:**
- Consumes: dev의 BF-12 첫 회수 주기 로그
- Produces: 구판 미리보기의 관측 전용 분류와 소유 판정

- [x] **Step 1: BF-12 dev 로그를 한 주기 이상 관측한다**

Expected: 첫 바퀴 요약 1줄, 계수, 삭제 0, 비밀값 출력 0.

2026-09-11 수용: dev f8, startup 06:30 UTC와 기본 주기 뒤 07:30 UTC 실제 요약 구분. 주체 612·map.tif 0·삭제 0, 재시작·수동 실행·주기 변경 0. 독립 검토 승인. `reports/stage12-final-verification/s3-first-cycle.log` 및 `sessions/20260911-stage12-final-verification.md`.

- [x] **Step 2: BF-12가 닫힌 경우에만 TL-2 실패 시험을 작성한다**

Expected: 원천 원장 부재와 사이드카 부재가 별도 등급으로 관측되고 자동 삭제되지 않는다.

- [x] **Step 3: 관측 전용 분류를 구현하고 기존 19벌 기준 집합과 대조한다**

Expected: 재굽기로 닿지 않는 16벌이 설명 가능한 하위 집합으로 나타난다. 실제 삭제 0.

- [x] **Step 4: publisher 정기 실행과 staging 실제 한 주기를 확인한다**

기존 TL-2 완료 정의의 자동 순회·staging 확인 조건을 추적한다. d564 dev 최초 발행·기동 자동순회 성공을 매시간 갱신이나 staging 한 주기 성공으로 대신하지 않는다. 실제 cron 설치는 승인 경계를 따른다.

### Task 7: `R-S2-REVIEW` — CR-2 후속 마감

**Files:**
- Create: `dev-package/prd/specs/s2-review.md`
- Create: `dev-package/prd/rounds/R-S2-REVIEW.md`

**Interfaces:**
- Consumes: 2026-09-10 CR-2 계약·현행 dev 제한 수용 결정
- Produces: 계약·제한·배포 실측·CI 후속 마감

- [x] **Step 1: CR-2 계약·로그인 제한 결정 반영**

Decisions: core-viz 경계 헤더 필수·부재 400·스크린샷 레이어 최대 8 가산 승인. 현행 dev 제한(자격/클라이언트 각각 5회/15분·성공 시 초기화·프로세스 메모리) 수용. 공유 limiter는 https://github.com/CognileapAI/colab-v2/issues/11 후속. 배포 후 실제 전달 IP·여섯 번째 실패 429 확인과 나머지 배포·CI 조건 검증은 남는다.

- [x] **Step 2: CR-2를 계약·배포 실측·CI 결과로 나눠 각각 검증한다**

Expected: 한 부분의 완료로 전체를 닫지 않는다.

### Task 8: `R-S2-CONVENIENCE` — J-1 편의 기능 9건

**Files:**
- Create: `dev-package/prd/specs/s2-convenience.md`
- Create: `dev-package/prd/rounds/R-S2-CONVENIENCE.md`
- Discover in child spec: 9개 사용자 여정별 화면·API·저장 경계

**Interfaces:**
- Consumes: J-1의 확정 완료 정의 9건
- Produces: 편의 기능 9건과 사용자 여정 검증

- [x] **Step 1: 9개 기능을 사용자 여정 단위로 쪼갠 실행 계획을 작성한다**

Expected: 각 기능에 화면 동작, 저장 결과, 권한, 실패 상태, 관련 게이트가 있다.

수용표 9건은 유지한다. 신규·잔여 편의 구현 8건과 F-3의 폴더 구조 보존 증거 재사용 1건으로 나누어 중복 구현을 피한다(`PLAN-SoT` 〈78〉·〈339〉, `dev-package/sessions/20260908-j1-scope-map.md`).

- [x] **Step 2: 운영 안전성 P0 종료 뒤 실패 시험부터 구현한다**

Expected: 기능별 단독 게이트와 사용자 여정 E2E가 green이다.

- [x] **Step 3: J-1을 배포 검증한다**

Expected: 9개 완료 정의 전건 충족.

### Task 9: 인증 전환 없는 stage 1·2 전체 종료

**Files:** `dev-package/work-items.yaml`, `dev-package/03-HANDOFF.md`, 각 라운드 검증 기록

**Interfaces:**
- Consumes: Task 1~8 결과, 관련 단독 게이트와 전체 통합 증거
- Produces: 비연기 미완 0의 stage 1·2 종료 판정 또는 정확한 잔여 조건

- [x] **Step 1: Google 로그인 구현 제외**

`PA-G`는 단계 미정 `backlog/open`; https://github.com/CognileapAI/colab-v2/issues/12 에서 추적한다. 종전 자동 전환 기한은 해제. 기존 로그인·비밀번호 발급 경로 제거는 승인되지 않았다.

- [x] **Step 2: 통합 검증과 구체적인 배포 검토 자료 준비**

Expected: 각 라운드 수용 검토·관련 게이트·최종 전수 결과, 정확한 SHA와 변경 목록을 갖춘 뒤 main push·staging/dev 배포 실행 직전 승인을 받는다.

- [x] **Step 3: 승인된 dev 배포와 기존 로그인 회귀 검증**

Expected: 동일 main SHA에서 기존 로그인·세션 유지·로그아웃과 사용자 여정 성공, `deploy_doctor` 한 번의 실행 15/15, skip 0. 신규 Google 로그인 구현 없음. d564 실제 인증 회귀는 `dev-package/sessions/20260911-stage12-auth-regression-d564.md` 참조.

- [ ] **Step 4: 최종 대장 확인**

Run: `bash gates/run.sh work-item-consistency`

Expected: stage 1·2 각각 비연기 미완 0, 연기 항목의 건수·사유 공개, 대장 불일치 0, 준비 실패 0. stage 3 `BO-1` 설계 미확정은 이 종료를 차단하지 않는다.

## Self-Review

- 재검증 9건은 Task 1에서 구현 작업보다 먼저 판정한다.
- stage 1의 나머지 `U-1`, `F-3`, `U-2`, `G10`, `BF-10`은 Task 1~4에 모두 배치했다.
- stage 2의 `IS4`, `I3`, `I4`, `BF-12`, `TL-2`, `CR-2`, `J-1`, `X-7`, `WU-PREVIEW`, `PA-G`은 Task 1과 Task 5~9에 모두 배치했다.
- 독립 하위 시스템의 자식 사양·라운드 작성은 각 Task의 착수 단계에 배치했다. 모든 자식 계획의 완성·구현을 이번 문서 갱신으로 주장하지 않는다.
- prod, after_stage2, 실제 데이터·캐시 삭제는 포함하지 않았다.
