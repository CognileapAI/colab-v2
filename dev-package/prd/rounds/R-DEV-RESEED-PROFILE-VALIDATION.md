> spec: dev-package/prd/specs/2026-09-16-dev-reseed-profile-validation.md

# 개발 초기화 계정 프로필 검증 Implementation Plan

> **For agentic workers:** 위임 원칙(글로벌 `CLAUDE.md`) ＋ `lane-worker` 에이전트로 태스크당 레인 1개(권고), 또는 `executing-plans`(로컬 vendored)로 이 세션에서 직접. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 실행 계정 후보를 외부 승인 기준과 대조하고, 개인 설정 없이 같은 fail-closed 조건을 검사한다.

**Architecture:** `accounts.py`가 승인 기준과 후보를 분리해 검증하고 `reseed.sh`가 검증된 후보에서만 교수 신원을 적용한다. 기존 shell fixture가 독립 임시 파일로 성공·실패·결과 JSON을 검사한다.

**Tech Stack:** Python 3.12 표준 라이브러리, Bash, 기존 gate runner

**Spec:** `dev-package/prd/specs/2026-09-16-dev-reseed-profile-validation.md`

## Global Constraints

- 실제 개인 승인 파일·비밀·dev·운영·네트워크 접촉 0건.
- 공개 예제는 임시 시험 입력으로만 사용하고 승인 기준 자체의 trust 정책은 유지.
- 새 의존성·DB/API/화면 변경 0건.

---

### Task 1: 기존 승인 기준과 실행 후보 분리 계약 확인

**Files:**
- Modify: `dev-package/tools/dev-reseed/tests/test_accounts.py`
- Modify: `dev-package/tools/dev-reseed/accounts.py`

**Interfaces:**
- Consumes: `COLAB_RESEED_ACCOUNTS_PROFILE` 승인 기준, `--profile` 실행 후보.
- Produces: 후보를 기준과 대조한 `professor` 출력 또는 비영 종료.

- [x] **Step 1: 기존 계약 회귀 확인** — 승인·후보를 별도 0600 파일로 만든 기존 `accounts.py --profile` 검증이 정상 후보를 통과시키고 누락·0644·symlink·변조·빈 이메일을 거절하는지 확인.
- [x] **Step 2: 통합 RED 작성** — `preflight-secrets.sh`에서 `reseed.sh --accounts-file <후보>`가 같은 후보의 교수 신원을 사용하는 시험 추가.
- [x] **Step 3: RED 확인** — 후보와 기본 승인 파일의 교수 값을 구분한 뒤 `preflight-secrets.sh`가 후보 오류와 override 오류를 구별하지 못해 exit 1인 것을 확인.
- [x] **Step 4: 최소 구현** — `accounts.py`는 변경하지 않고 기존 분리 검증을 호출하는 `reseed.sh`만 수정.

### Task 2: preflight 신원 적용과 판정 정확성

**Files:**
- Modify: `dev-package/tools/dev-reseed/tests/preflight-secrets.sh`
- Modify: `dev-package/tools/dev-reseed/tests/preflight-red.sh`
- Modify: `dev-package/tools/dev-reseed/reseed.sh`
- Modify: `dev-package/tools/dev-reseed/preflight.sh`

**Interfaces:**
- Consumes: `--accounts-file`, 승인 기준 환경값, 선택적 `RESEED_ACCOUNT_*` override.
- Produces: 검증된 후보 신원 또는 구분된 `seed-inputs` 실패와 정상종결 JSON.

- [x] **Step 1: 실패 시험 작성** — fixture가 별도 승인·후보를 만들고 정상 통과, 조회 실패·빈 출력·override 불일치·후보 오류를 검사. 의도적 실패의 preflight/result JSON 구조와 판정 중복을 검증.
- [x] **Step 2: RED 확인** — `preflight-secrets.sh`가 후보 오류 7건과 override 불일치 1건을 구별하지 못해 exit 1인 것을 확인.
- [x] **Step 3: 최소 구현** — 후보를 명시해 교수 신원을 조회하고 성공·필드 비어 있지 않을 때만 적용. 후보 오류와 override 오류를 구분해 preflight에 전달.
- [x] **Step 4: 형제 회귀 GREEN 확인** — `preflight-secrets.sh`, `preflight-red.sh`, 기존 계정 pytest 16건을 순차 실행.

### Task 3: 선언 게이트 검증

**Files:**
- Verify: `gates/tools/dev-reseed-selftest.sh`
- Verify: task runtime `gate-summary.json`

**Interfaces:**
- Consumes: 변경된 실제 파일 hash와 선언 게이트 2개.
- Produces: `dev-reseed-selftest`, `selftest`의 판정·준비 실패 0 증거.

- [x] **Step 1: 작업 게이트 실행** — `COLAB_TASK_ID=<task-id> bash gates/run.sh task` 한 번으로 선언 게이트를 실행.
- [x] **Step 2: 보고서 검증** — `verify-report --task <task-id> --report <현재 report> --gate dev-reseed-selftest --gate selftest` 실행.
- [x] **Step 3: intent 대조** — proposed outcome 미달·초과를 열거하고 실제 dev/reseed 미실행 범위를 명시.

## Self-Review

- Spec coverage: 개인 설정 독립, 기존 승인/후보 분리 재사용, 거절 조건, false green, 결과 JSON, 두 게이트를 Task 1~3에 연결.
- Placeholder scan: 실행 시 치환되는 lifecycle `<task-id>` 외 구현 미정 항목 없음.
- Type consistency: 승인 기준은 환경값, 실행 후보는 `--profile`/`--accounts-file`, 교수 출력은 tab 5필드로 일관.
