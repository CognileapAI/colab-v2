> spec: dev-package/prd/specs/stage1-stage2-closeout.md

# stage 1·2 종료 Implementation Plan

> **For agentic workers:** 위임 원칙(글로벌 `CLAUDE.md`) ＋ `lane-worker` 에이전트로 태스크당 레인 1개(권고), 또는 `executing-plans`(로컬 vendored)로 이 세션에서 직접. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 대장과 실물을 먼저 일치시킨 뒤 stage 1·2의 실제 잔여 개발을 독립 라운드로 끝내고 Google 로그인까지 닫는다.

**Architecture:** 첫 라운드는 기록 재검증만 수행해 실제 개발 범위를 줄인다. 이후 저장소, 시험 효율, 운영, 미리보기 회수, 코드리뷰 후속, 편의 기능, 인증을 파일 면과 완료 기준이 겹치지 않는 라운드로 순차 집행한다.

**Tech Stack:** Git, GitHub Actions, CoLAB gates, Python 3.12, React, PostgreSQL, S3, Terraform, agent-browser

**Spec:** `dev-package/prd/specs/stage1-stage2-closeout.md`

## Global Constraints

- 실행은 깨끗한 최신 `origin/main` 작업 사본에서 시작한다.
- 완료 138건을 근거 없이 재개봉하지 않는다.
- 대장 상태는 오케스트레이터 한 명만 수정한다.
- 제품 데이터·S3 객체·미리보기 캐시는 사용자 별도 승인 없이 삭제하지 않는다.
- 관련 단독 게이트의 준비 실패를 성공으로 세지 않는다.
- 각 구현 라운드는 실패 시험, 최소 구현, 단독 게이트, 수용 검토 순서를 지킨다.
- prod와 `after_stage2`는 이 계획의 범위 밖이다.

---

### Task 1: `R-S12-VERIFY` — 9건 재검증

**Files:**
- Create: `dev-package/prd/specs/s12-verify.md`
- Create: `dev-package/prd/rounds/R-S12-VERIFY.md`
- Create: `dev-package/sessions/s12-verify.md`
- Modify: `dev-package/work-items.yaml`
- Modify: `dev-package/03-HANDOFF.md`

**Interfaces:**
- Consumes: 최신 `origin/main`, dev 실행 SHA, 기존 CI·배포 근거
- Produces: 재검증 9건의 done 또는 정확한 미충족 조건

- [ ] **Step 1: 깨끗한 기준선을 고정한다**

Run: `git fetch origin main && git status --short --branch && git rev-list --left-right --count origin/main...HEAD`

Expected: 변경 0, 앞뒤 수 `0 0`, HEAD와 `origin/main` SHA 동일.

- [ ] **Step 2: 재검증 행렬을 작성한다**

Rows: `BF-7`, `BF-8`, `BF-9`, `BF-11`, `BF-13`, `I3`, `BF-12`, `X-7`, `WU-PREVIEW`.

Columns: 완료 정의, main 포함 SHA, 관련 게이트, dev 확인, 미충족 조건, 판정.

- [ ] **Step 3: 항목별 관련 게이트와 dev 실물을 확인한다**

Expected: 실제 실행한 게이트만 green으로 기록하고 CI skip은 미실행으로 기록한다. dev 확인은 같은 배포 SHA를 가리켜야 한다.

- [ ] **Step 4: `U-1`과 `F-3` 승인 이력을 함께 대조한다**

Expected: 기존 승인으로 완료 정의가 충족되면 마감 후보에 넣고, 새 결정이 필요하면 사용자 결정 묶음에 정확한 선택지만 넣는다.

- [ ] **Step 5: 대장을 먼저 갱신하고 반영본을 맞춘다**

Expected: 확인된 항목만 `done`; 나머지는 상태 유지와 해제 조건 기재. `work-item-consistency` green.

### Task 2: `R-S1-STORAGE` — S3 고아 바이트 정리

**Files:**
- Create: `dev-package/prd/specs/s1-storage.md`
- Create: `dev-package/prd/rounds/R-S1-STORAGE.md`
- Modify: `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py`
- Modify: `services/pipeline-worker/src/colab_pipeline/ports/blobs.py`
- Modify: `services/pipeline-worker/src/colab_pipeline/app/worker.py`
- Modify: `services/pipeline-worker/src/colab_pipeline/kernel/s3.py`
- Test: `services/pipeline-worker/tests/test_reaper_skips_processing.py`
- Test: `services/pipeline-worker/tests/test_worker_lab_scope.py`

**Interfaces:**
- Consumes: `I-D`와 `U-1`의 저장소 계약
- Produces: 원장이 아는 키만 대상으로 하는 실패 안전 회수 경로

- [ ] **Step 1: 저장 Port와 만료 스윕의 현재 호출 경계를 조사해 사양에 고정한다**

Expected: 버킷 전체 스캔 0, 등록된 업로드 삭제 0, 완료 전송 원장 보존 기간을 명시한다.

- [ ] **Step 2: 실패 시험을 작성한다**

Cases: S3 삭제 실패 시 원장 행 유지, 등록 업로드 보존, 열린 전송 보존, 완료 전송 보존 기간, 대상 0건 판정.

- [ ] **Step 3: 실패 시험의 RED를 확인하고 최소 구현을 수행한다**

Expected: 객체 삭제 성공 뒤에만 원장 행을 제거하며 재시도 가능성을 유지한다.

- [ ] **Step 4: 단독 서비스 게이트와 S3 경계 시험을 실행한다**

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

- [ ] **Step 1: 병렬화 전 기준 계수를 같은 트리에서 측정한다**

Expected: 수집·실행·skip·deselect·실패 수와 전체 시간을 기록한다.

- [ ] **Step 2: 게이트 내부 시험만 병렬화하고 실패 픽스처를 재실행한다**

Expected: `gates/config/parallelism.toml`의 게이트 간 `serial` 의미는 유지하고, 판정 계수와 준비 실패 의미도 동일하다.

- [ ] **Step 3: 같은 트리에서 전후 시간과 판정 계수를 비교한다**

Expected: 실패·skip·deselect 수 불변, 준비 실패 0, 측정 가능한 시간 단축.

### Task 4: `R-S1-GRID-OVERLAY` — 조건부 BF-10

**Files:**
- Create: `dev-package/prd/specs/s1-grid-overlay.md`
- Create: `dev-package/prd/rounds/R-S1-GRID-OVERLAY.md`
- Discover in child spec: 화면과 저장 PNG가 공유할 렌더 경계

**Interfaces:**
- Consumes: BF-10 사용자 결정
- Produces: 화면·저장 이미지에 일치하는 격자선·눈금, 또는 승인된 범위 종료

- [ ] **Step 1: BF-10 결정을 사용자에게 한 번에 요청한다**

Choice: 화면과 저장 PNG 모두 구현, 둘 다 미구현으로 범위 조정. 화면만 구현은 표현 불일치 때문에 권고하지 않는다.

- [ ] **Step 2: 구현 선택 시 공통 렌더 경계를 조사해 자식 사양에 고정한다**

Expected: 화면과 저장 PNG가 같은 좌표·눈금 규칙을 소비한다.

- [ ] **Step 3: 승인된 갈래만 실패 시험부터 구현한다**

Expected: 두 출력의 표현이 동일하거나 범위 조정 결정으로 항목이 명확히 닫힌다.

- [ ] **Step 4: stage 1 종료 계수를 확인한다**

Expected: stage 1의 `open`·`partial` 0.

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

- [ ] **Step 1: IS4 맨몸 state 복구를 격리 환경에서 재현한다**

Expected: 문서만 사용해 복구하고 `terraform plan`이 `No changes`를 출력한다. 실제 apply는 수행하지 않는다.

- [ ] **Step 2: I3의 15개 완료 조건을 최신 배포 이력으로 다시 센다**

Expected: 이미 충족된 조건은 근거로 닫고 실제 미충족 조건만 구현 범위로 남긴다.

- [ ] **Step 3: I4 관측 범위를 독립 실패 시험과 함께 구현한다**

Required: 분산 추적, 구조화 로그, 알람, 데이터 레지던시 기록, 기존 복원 결과를 소비하는 운영 리허설.

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

- [ ] **Step 1: BF-12 dev 로그를 한 주기 이상 관측한다**

Expected: 첫 바퀴 요약 1줄, 계수, 삭제 0, 비밀값 출력 0.

- [ ] **Step 2: BF-12가 닫힌 경우에만 TL-2 실패 시험을 작성한다**

Expected: 원천 원장 부재와 사이드카 부재가 별도 등급으로 관측되고 자동 삭제되지 않는다.

- [ ] **Step 3: 관측 전용 분류를 구현하고 기존 19벌 기준 집합과 대조한다**

Expected: 재굽기로 닿지 않는 16벌이 설명 가능한 하위 집합으로 나타난다. 실제 삭제 0.

### Task 7: `R-S2-REVIEW` — CR-2 후속 마감

**Files:**
- Create: `dev-package/prd/specs/s2-review.md`
- Create: `dev-package/prd/rounds/R-S2-REVIEW.md`

**Interfaces:**
- Consumes: CR-2 사용자 결정
- Produces: 계약·제한·배포 실측·CI 후속 마감

- [ ] **Step 1: CR-2의 세 결정을 한 묶음으로 확정한다**

Decisions: 계약 오류 응답 선언, 로그인 제한 클라이언트 기준, 배포 뒤 재굽기·소유 재실측 범위.

- [ ] **Step 2: CR-2를 계약·배포 실측·CI 결과로 나눠 각각 검증한다**

Expected: 한 부분의 완료로 전체를 닫지 않는다.

### Task 8: `R-S2-CONVENIENCE` — J-1 편의 기능 9건

**Files:**
- Create: `dev-package/prd/specs/s2-convenience.md`
- Create: `dev-package/prd/rounds/R-S2-CONVENIENCE.md`
- Discover in child spec: 9개 사용자 여정별 화면·API·저장 경계

**Interfaces:**
- Consumes: J-1의 확정 완료 정의 9건
- Produces: 편의 기능 9건과 사용자 여정 검증

- [ ] **Step 1: 9개 기능을 사용자 여정 단위로 쪼갠 실행 계획을 작성한다**

Expected: 각 기능에 화면 동작, 저장 결과, 권한, 실패 상태, 관련 게이트가 있다.

- [ ] **Step 2: 운영 안전성 P0 종료 뒤 실패 시험부터 구현한다**

Expected: 기능별 단독 게이트와 사용자 여정 E2E가 green이다.

- [ ] **Step 3: J-1을 배포 검증한다**

Expected: 9개 완료 정의 전건 충족.

### Task 9: `R-S2-GOOGLE-AUTH`과 전체 종료

**Files:**
- Create: `dev-package/prd/specs/s2-google-auth.md`
- Create: `dev-package/prd/rounds/R-S2-GOOGLE-AUTH.md`
- Modify: 인증 커널과 비밀번호 발급 경로
- Test: Google 로그인·관리자·기존 세션 음성/양성 시험

**Interfaces:**
- Consumes: 다른 비연기 stage 1·2 미완 0
- Produces: Google IdP 단일 인증 경로와 stage 2 종료

- [ ] **Step 1: PA-G 진입조건을 대장에서 계산한다**

Expected: `PA-G` 자신과 연기 항목을 제외한 미완 0. 하나라도 남으면 착수하지 않는다.

- [ ] **Step 2: 별도 사양에서 인증 전환과 제거 경로를 고정한다**

Required: 어댑터는 인증 커널 한 파일, 비밀번호 발급 경로 제거, 관리자 처리, PA 핵심 회귀.

- [ ] **Step 3: 실패 시험부터 구현하고 인증·경계 게이트를 실행한다**

Expected: Google 로그인 양성, 미허용 계정 음성, 기존 비밀번호 발급 경로 부재.

- [ ] **Step 4: dev 배포와 실제 로그인 여정을 검증한다**

Expected: 같은 main SHA에서 로그인·세션 유지·로그아웃 성공, `deploy_doctor` 15/15.

- [ ] **Step 5: stage 1·2 최종 상태를 닫는다**

Run: `bash gates/run.sh work-item-consistency`

Expected: stage 1 비연기 미완 0, stage 2 비연기 미완 0, 대장 불일치 0, 준비 실패 0.

## Self-Review

- 재검증 9건은 Task 1에서 구현 작업보다 먼저 판정한다.
- stage 1의 나머지 `U-1`, `F-3`, `U-2`, `G10`, `BF-10`은 Task 1~4에 모두 배치했다.
- stage 2의 `IS4`, `I3`, `I4`, `BF-12`, `TL-2`, `CR-2`, `J-1`, `X-7`, `WU-PREVIEW`, `PA-G`은 Task 1과 Task 5~9에 모두 배치했다.
- 독립 하위 시스템은 별도 사양·라운드로 분리했다.
- prod, after_stage2, 실제 데이터·캐시 삭제는 포함하지 않았다.
