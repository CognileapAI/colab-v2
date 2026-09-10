> spec: dev-package/prd/specs/main-closeout.md

# `main` 잔여 작업 정리 Implementation Plan

> **For agentic workers:** 위임 원칙(글로벌 `CLAUDE.md`) ＋ `lane-worker` 에이전트로 태스크당 레인 1개(권고), 또는 `executing-plans`(로컬 vendored)로 이 세션에서 직접. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 깨끗한 원격 `main`에서 stage 1·2 완료·미완 지도를 고정하고, 낡은 대장 상태와 최신 배포 여부 및 다음 운영 라운드의 의존 순서를 확정한다.

**Architecture:** 이 라운드는 제품 기능을 추가하지 않는 종료·판정 라운드다. 기준선 고정, 두 항목 재측정, 조건부 배포, 대장 동기화를 순서대로 수행하며 배포는 별도 승인 지점에서 멈춘다.

**Tech Stack:** Git, GitHub Actions CLI, CoLAB gates, agent-browser, dev·staging 배포 도구

**Spec:** `dev-package/prd/specs/main-closeout.md`

## Global Constraints

- 현재 더러운 로컬 `main`은 실행·병합·배포 기준으로 사용하지 않는다.
- 손으로 형제 worktree를 만들지 않는다. 실행은 Codex의 새 작업 사본에서 시작한다.
- prod와 제품 데이터·캐시·브랜치·태그 삭제는 범위 밖이다.
- 배포는 사용자 GO 전에는 실행하지 않는다.
- staging은 리허설이고 완료 판정은 dev `deploy_doctor` 15/15 한 번의 실행이다.
- 최신 CI가 성공해도 관련 job이 skip이면 해당 단독 게이트를 실행한다.

---

### Task 1: 깨끗한 `main` 기준선 고정

**Files:**
- Create: `dev-package/sessions/20260910-main-closeout.md`
- Create: `dev-package/sessions/20260910-stage1-stage2-map.md`
- Read: `dev-package/work-items.yaml`
- Read: `docs/BRANCHING.md`

**Interfaces:**
- Consumes: 원격 `main`, 사양의 기준 SHA 규칙
- Produces: 기준 SHA, dirty 0, 원격과의 앞뒤 커밋 수 0인 실행 사본

- [ ] **Step 1: 새 Codex 작업 사본에서 저장소 루트를 확인한다**

Run: `git rev-parse --show-toplevel`

Expected: 출력 끝이 `30 CoLAB-v2`이고 현재 더러운 체크아웃 경로와 다르다.

- [ ] **Step 2: 원격 참조를 갱신한다**

Run: `git fetch origin main`

Expected: 종료코드 0. 병합·reset·checkout은 수행하지 않는다.

- [ ] **Step 3: 기준선 일치를 확인한다**

Run: `git status --short --branch && git rev-list --left-right --count origin/main...HEAD && git rev-parse HEAD origin/main`

Expected: 변경 0, 앞뒤 수 `0 0`, 두 SHA 동일.

- [ ] **Step 4: 작업 증거를 시작하고 ID를 현재 셸에 보존한다**

Run:

```bash
COLAB_MAIN_CLOSEOUT_TASK_ID=$(python3 scripts/agent-bridge.py lifecycle begin \
  --role lane-worker \
  --gate service-tests-core-api \
  --gate work-item-consistency \
  --report dev-package/reports/main-closeout/reconcile/gate-summary.json \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["task_id"])')
test ${#COLAB_MAIN_CLOSEOUT_TASK_ID} -eq 32
```

Expected: 길이 32의 새 작업 ID가 현재 셸 변수에 들어간다.

- [ ] **Step 5: 기준선 세션 기록을 작성한다**

Record: 기준 SHA, 원격 조회 시각, dirty 파일 수 0, 현재 대장 상태 수치와 명령 결과. 비밀값과 환경 파일 내용은 적지 않는다.

- [ ] **Step 6: stage 1·2 완료 지도를 대장에서 생성한다**

Record: 단계별 전체·완료·열림·부분 완료·연기 수, 완료 항목의 기능 묶음과 정확한 ID 집합. 완료 표시는 대장의 `status: done`만 사용하고 시험 재실행 여부와 구분한다.

Expected: stage 1은 63건, stage 2는 96건을 기준으로 시작하되, 실행 시점 대장 수가 다르면 최신 수치로 고치고 차이 원인을 기록한다.

- [ ] **Step 7: 미완 항목을 실행 성격으로 분류한다**

Classify: 재검증·마감 후보, 승인·상태 재확인, 실제 개발, 제품 판단 뒤 개발, 선행 항목에 차단됨. 한 항목은 한 분류에만 두고 직접 의존 상태를 함께 적는다.

Expected: 모든 stage 1·2 비연기 미완 항목이 중복·누락 없이 포함되고, 재검증 후보를 확인 없이 완료로 바꾸지 않는다.

### Task 2: `X-7`과 7종 미리보기 상태 재판정

**Files:**
- Modify: `dev-package/work-items.yaml`
- Modify: `dev-package/03-HANDOFF.md`
- Modify: `dev-package/sessions/20260910-main-closeout.md`
- Verify: `dev-package/sessions/20260910-preview-all-formats.md`
- Candidate evidence: `dev-package/sessions/20260910-preview-dev-stage-deployment.md`

**Interfaces:**
- Consumes: Task 1의 기준 SHA와 `COLAB_MAIN_CLOSEOUT_TASK_ID`
- Produces: 두 작업 항목의 최신 상태와 검증 가능한 근거

- [ ] **Step 1: 최신 `main`에서 core-api 단독 게이트를 실행한다**

Run: `bash gates/run.sh service-tests-core-api`

Expected: 종료코드 0, green 1, 판정 실패 0, 준비 실패 0. 준비 실패면 `X-7`은 `partial`을 유지한다.

- [ ] **Step 2: 과거 CI 근거가 실제 실행인지 확인한다**

Run: `gh run view 34329090220 --json headSha,conclusion,jobs,url`

Expected: `service-tests (core-api)`가 `success`; 최신 커밋 CI의 skip과 구분해 세션 기록에 적는다.

- [ ] **Step 3: dev·staging 배포 주장을 독립 확인한다**

Check: 릴리스 태그 `dev-20260910-2`, 배포 원장 SHA, dev `MAIN_SHA`, 실행 컨테이너 이미지 SHA, staging 원장 SHA, 기존 보고서 해시. 모든 값은 읽기 전용으로 확인한다.

Expected: 확인된 값만 기록한다. 미추적 세션 파일은 실제 파일 hash와 원격 상태가 맞을 때만 근거로 채택한다.

- [ ] **Step 4: 각 항목을 별도로 판정한다**

Rule:
- `X-7`: 최신 단독 게이트 green이면 `done`; 아니면 `partial`과 실제 실패/준비 사유.
- `WU-PREVIEW`: 완료 정의의 로컬 시험, arm64, 배포, 배포 후 실제 GRIB/HDF5 여정이 같은 배포 SHA로 확인되면 `done`; 하나라도 확인되지 않으면 `partial`.

- [ ] **Step 5: 대장을 먼저 수정하고 인계 문서를 5줄 이내로 맞춘다**

Update: `dev-package/work-items.yaml`의 두 항목 상태·근거·미실측값을 먼저 고친 뒤, `dev-package/03-HANDOFF.md` 상단 반영본만 동기화한다. 과거 문면은 삭제하지 않고 개정 표시를 붙인다.

- [ ] **Step 6: 선언한 두 게이트를 한 작업 실행으로 검증한다**

Run: `COLAB_TASK_ID="$COLAB_MAIN_CLOSEOUT_TASK_ID" bash gates/run.sh task`

Run: `python3 scripts/agent-bridge.py verify-report --task "$COLAB_MAIN_CLOSEOUT_TASK_ID" --report dev-package/reports/main-closeout/reconcile/gate-summary.json --gate service-tests-core-api`

Run: `python3 scripts/agent-bridge.py verify-report --task "$COLAB_MAIN_CLOSEOUT_TASK_ID" --report dev-package/reports/main-closeout/reconcile/gate-summary.json --gate work-item-consistency`

Expected: 한 run ID 아래 두 게이트 모두 종료코드 0, 판정 실패 0, 준비 실패 0, 대장 불일치 0.

### Task 3: 최신 `main` 배포 go/no-go 패키지

**Files:**
- Modify: `dev-package/sessions/20260910-main-closeout.md`
- Create on GO: `dev-package/reports/main-closeout/deploy/`
- Read: `infra/staging/README.md`
- Read: `infra/dev/README.md`

**Interfaces:**
- Consumes: Task 2의 대장 판정, 현재 dev SHA, 최신 `origin/main` SHA
- Produces: NO-GO 기록 또는 승인 가능한 단일 배포 후보 SHA

- [ ] **Step 1: 배포 차이를 파일 단위로 고정한다**

Run:

```bash
COLAB_DEPLOYED_SHA=$(git rev-parse 'dev-20260910-2^{commit}')
git log --oneline "$COLAB_DEPLOYED_SHA"..origin/main
git diff --stat "$COLAB_DEPLOYED_SHA"..origin/main
```

Expected: 업로드 진행 표시 관련 차이와 문서 차이를 분리하고, 배포 후보를 최신 `origin/main` 한 SHA로 고정한다.

- [ ] **Step 2: 변경 경로에 맞는 게이트 작업을 선언하고 실행한다**

Run:

```bash
COLAB_DEPLOY_TASK_ID=$(python3 scripts/agent-bridge.py lifecycle begin \
  --role lane-worker \
  --gate frontend-test \
  --gate frontend-typecheck \
  --gate service-tests-core-api \
  --report dev-package/reports/main-closeout/deploy-gates/gate-summary.json \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["task_id"])')
test ${#COLAB_DEPLOY_TASK_ID} -eq 32
COLAB_TASK_ID="$COLAB_DEPLOY_TASK_ID" bash gates/run.sh task
```

Expected: 한 run ID 아래 세 게이트 모두 종료코드 0, 판정 실패 0, 준비 실패 0. 하나라도 아니면 NO-GO.

- [ ] **Step 3: 배포 전 패키지를 사용자에게 한 번에 제시한다**

Include: 후보 SHA, 현재 dev SHA, 사용자에게 달라지는 동작, 세 게이트 결과, 데이터 삭제 0, rollback 기준, staging→dev 순서.

Expected: 명시적 GO가 없으면 여기서 멈추고 NO-GO가 아니라 승인 대기로 기록한다.

- [ ] **Step 4: GO일 때만 staging 리허설을 수행한다**

Follow: `infra/staging/README.md`의 현재 명령과 백업·복구 사전 검사를 그대로 사용한다.

Expected: 서비스 healthy, 신규 미선언 고아 0, 실제 GRIB/HDF5 업로드·두 번째 변수 선택·PNG·재조회 성공. staging 결과를 완료 판정으로 쓰지 않는다.

- [ ] **Step 5: staging green 뒤 dev에 같은 SHA를 배포한다**

Follow: `infra/dev/README.md`의 `ship.sh` 절차. 비조상 우회 변수는 사용하지 않는다.

Expected: 실행 SHA가 후보 SHA와 같고 `origin/main`의 조상이다.

- [ ] **Step 6: dev 완료 조건을 한 번의 실행으로 확인한다**

Run: `services/core-api/.venv/bin/python services/core-api/ops/deploy_doctor.py`에 `infra/dev/README.md`의 현재 dev 인자를 사용한다.

Expected: 15/15, 실패 0, skip 0이 한 번의 실행에서 나온다. 실제 GRIB/HDF5 업로드·선택·PNG·재조회도 같은 SHA에서 통과한다.

- [ ] **Step 7: 릴리스 기록을 남긴다**

Follow: `infra/dev/tag-release.sh`로 다음 `dev-YYYYMMDD-N` 후보를 계산하고, 태그 push는 사용자 승인 범위 안에서만 수행한다. 세션 기록에는 배포 SHA, 태그, doctor, E2E, 실패·재시도 이력을 구분해 적는다.

### Task 4: 다음 독립 라운드의 순서 확정

**Files:**
- Modify: `dev-package/sessions/20260910-main-closeout.md`
- Create after approval: `dev-package/prd/specs/ops-deploy-closeout.md`
- Create after approval: `dev-package/prd/rounds/R-OPS-DEPLOY-CLOSEOUT.md`
- Create after approval: `dev-package/prd/specs/preview-retention-closeout.md`
- Create after approval: `dev-package/prd/rounds/R-PREVIEW-RETENTION-CLOSEOUT.md`

**Interfaces:**
- Consumes: Task 2·3 이후 최신 대장
- Produces: 서로 파일 면이 겹치지 않는 다음 두 라운드의 진입조건

- [ ] **Step 1: 현재 단계 미완을 다시 계산한다**

Count: `stage1`·`stage2`, status가 `done`이 아니며 `deferred`가 아닌 항목. `PA-G` 자신은 Google 로그인 개시조건 계수에서 제외한다.

Expected: 항목 ID, 상태, 직접 의존 항목 상태를 세션 기록에 표로 남긴다. 과거 계수를 재사용하지 않는다.

- [ ] **Step 2: 배포·운영 준비 라운드의 경계를 고정한다**

Order: `IS4`의 실제 원격 상태 보관 판정 → `I3` 배포 자동화의 남은 완료 정의 → `I4` 추적·알람·복구 리허설. 제품 UI와 미리보기 회수 코드는 포함하지 않는다.

Expected: 세 항목별 현재 실물, 미충족 완료 조건, 필요한 사용자 승인과 파괴적 행동 0을 사양에 기록한다.

- [ ] **Step 3: 미리보기 회수 라운드의 경계를 고정한다**

Order: `BF-12`에서 회수 주기 로그가 실제로 보이고 삭제 0인지 확인 → 그 뒤에만 `TL-2`의 구판 산출물 소유 판정을 시작한다.

Expected: `BF-12`가 닫히지 않으면 `TL-2`는 착수하지 않는다. 캐시 삭제는 별도 사용자 승인 없이는 계획에도 실행 단계로 넣지 않는다.

- [ ] **Step 4: 제품 백로그는 별도 선택 목록으로 남긴다**

Group: UI 하드닝(`BF-7`~`BF-13`), 업로드·파일 관리(`U-1`, `U-2`, `F-3`), 편의 기능(`J-1`), 시험 시간(`G10`), 코드리뷰 후속(`CR-2`).

Expected: 의존이 이미 충족된 항목과 제품 판단이 필요한 항목을 나누되, 이 라운드에서 구현하거나 상태를 닫지 않는다.

- [ ] **Step 5: 종료 검증과 인계를 수행한다**

Run: `bash gates/run.sh work-item-consistency`

Run: `python3 scripts/agent-bridge.py lifecycle handoff --task "$COLAB_MAIN_CLOSEOUT_TASK_ID" --mode complete --summary 'main 기준선, 대장 재판정, 배포 판정, 다음 두 라운드 순서 확정'`

Expected: 대장 불일치 0, stage 1·2 완료·미완 현황, 다음 진입조건과 승인 대기 사항이 세션 기록에 남고 `COLAB_HANDOFF` 한 줄이 출력된다.

## Self-Review

- 사양의 원하는 결과 1~6은 Task 1~4에 각각 대응한다.
- prod·삭제·더러운 체크아웃 정리는 모든 작업에서 제외했다.
- 특정 CI job의 skip을 전체 CI 성공으로 대체하지 않는다.
- 배포 후보 SHA는 Task 3에서 하나로 고정하고 staging과 dev가 같은 값을 소비한다.
- 다음 두 하위 라운드는 독립 사양으로 분리하며 이 라운드에서 제품 구현을 섞지 않는다.
- stage 1·2 완료 138건과 미완 20건은 사양의 현황 지도와 Task 1에서 다루며, 최신 대장과 수치가 갈리면 실행 시점 값을 우선한다.
