> spec: dev-package/prd/specs/s12-verify.md

# Stage 1·2 재검증 Implementation Plan

> **For agentic workers:** 단일 쓰기 lane-worker가 수행하고 대장 갱신은 부모가 담당한다. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 9건과 승인계약 2건의 현재 근거와 잔여조건 확정.

**Architecture:** baseline 내용 hash → 로컬 게이트와 원격 읽기전용 증거 → 항목별 판정 → 부모 대장 반영.

**Tech Stack:** Git, GitHub Actions, CoLAB gates, SSH read-only.

**Spec:** `dev-package/prd/specs/s12-verify.md`

## Global Constraints

- 승인결정 dirty baseline을 보존하고 재승인을 요구하지 않는다.
- 제품 코드 변경 0, 운영 쓰기·배포·push·삭제 0.
- 개별 done은 완료 정의 전부 충족할 때만. 조사완료로 dev 완료를 갈음하지 않는다.

### Task 1: 기준과 증거 행렬

**Files:** Create `dev-package/prd/specs/s12-verify.md`, this round, `dev-package/sessions/s12-verify.md`.
**Interfaces:** Consumes 승인결정과 대장; Produces 부모용 갱신문안.

- [x] `git fetch origin main` 후 HEAD/origin/main와 기존 dirty baseline 구분.
- [x] 대장 11행 완료 정의 및 I3 15조건 읽기.
- [x] 원격 CI의 실제 core-api 시험 step와 dev CURRENT_SHA/MAIN_SHA/healthy 읽기.
- [x] dev 회수 로그와 코드 배선을 대조해 미충족을 명시.
- [x] 아래 단일 task를 선언하고 최종 문서를 고정. 결과는 지정 보고서에서 읽는다.

### Task 2: 새 로컬 증거와 인계

**Files:** Generated `dev-package/reports/s12-verify/local/gate-summary.json`.
**Interfaces:** Consumes 고정된 작업파일; Produces 종료코드·3계수와 lifecycle 인계.

- [x] `COLAB_TASK_ID=f2f85210f14f43beb3956d96425d95b8 COLAB_GATE_REPORT_DIR=dev-package/reports/s12-verify/local bash gates/run.sh task` 실행: exit1, green5/red(판정)1/red(준비)0. viz h5py 의존 누락, 나머지 통과. 단일6종green 주장이 아니다.
- [x] 최초 task의 `verify-report` 실행: exit1 `gate failures remain`. 실패를 보존한다.
- [x] 부모 지시에 따라 로컬 viz venv에 정본 `h5py==3.16.0`만 보충. 복구 task `7437468635f84d1fbf7c1580a1de886d`, `reports/s12-verify/viz-recovery/gate-summary.json`: 단독 viz 387통과, 1/0/0, verify-report 및 handoff 성공. 나머지 제품게이트 재실행0.
- [ ] 부모가 X-7 완료 후보를 수용하고 기타 상태 유지/잔여조건을 대장에 반영한다. 부모 문서 반영 후 부모 관련 게이트로 검증한다.

부모 지시로 이 결과 문서만 수정했다. 두 제품 보고서는 각 실행 당시의 입력 hash 증거이며 최종 문서까지 같은 snapshot이라고 주장하지 않는다. 최종 문서 task `d62240844b9f422ba82fb0c60ed6437a`, `reports/s12-verify/docs-final/gate-summary.json`에서 work-item-consistency/contract-lint를 별도로 검증한다. 최초6종실패와 viz복구를 사후 합산하여 한 run의 green으로 만들지 않는다.
