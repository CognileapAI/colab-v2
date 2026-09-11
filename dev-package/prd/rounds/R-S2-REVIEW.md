> spec: dev-package/prd/specs/s2-review.md

# Stage 2 코드리뷰 후속 Implementation Plan

> **For agentic workers:** `executing-plans`로 직접 실행한다. 같은 작업 사본의 파일 수정자는 한 명이다.

**Goal:** 승인된 계약 가산과 실제 동작의 차이를 시험으로 고정하고 배포 검증과 구분한다.
**Architecture:** 제품 런타임을 계약에 맞춰 임의로 바꾸지 않는다. 실제 OpenAPI를 AJV에 제공하는 요청 시험과 기존 서비스 시험을 대조한다.
**Tech Stack:** OpenAPI 3.1, 기존 gates의 PyYAML/AJV 2020, Python pytest.
**Spec:** `dev-package/prd/specs/s2-review.md`.

## Global Constraints

- 과거 오류 코드 일괄 추가, 로그인 제한 재설계, Google 로그인은 제외한다.
- 계정 헤더 누락의 신규 400 동작은 2026-09-11 사용자 “맞아”로 승인됐다. 누락·빈값·공백을 같은 400으로 처리하며 기존 연구실 소유 판정은 유지한다.
- main push·배포·실제 삭제는 실행 직전 승인한다.

## Task 1: 독립적인 계약 가산

Files: `contracts/tests/s2-review.test.cjs`, `contracts/seams/core-viz.yaml`.
Consumes: 실제 ScreenshotRequest 및 5개 operation parameters.
Produces: 실제 요청 샘플 수용/거절 결과. 기존 gate 도구의 고정 의존만 사용한다.

- [x] 실패 시험을 추가한다: `assert.equal(validate(requestWith9Layers), false)`, 연구실 없는 헤더도 false.
- [x] `node --test contracts/tests/s2-review.test.cjs`로 상한/필수 누락의 RED를 확인한다.
- [x] `layers.maxItems: 8`, 5개 op의 `LabScope` 참조, getRender의 `400`을 추가한다.
- [x] 같은 시험 GREEN과 `bash gates/run.sh contract-lint`, `bash gates/run.sh seam-consistency`를 각각 확인한다.

## Task 2: 런타임·CI 대조

Files: 기존 `services/viz-render/tests/test_tenant_boundary.py`, `test_job_retention.py`, `scripts/tests/test_ci_schema_setup.py`, `test_planning_gate.py`.

- [x] `bash gates/run.sh service-tests-viz-render`로 실제 연구실 누락/상한 응답을 포함한 서비스 전체를 검증한다.
- [x] `python3 -m unittest discover -s scripts/tests -p test_ci_schema_setup.py` 및 `test_planning_gate.py`를 각각 실행한다.
- [x] 세션 증거에 실제 CI 실행과 로컬 selftest를 구별해 적는다.

## Task 3: 확인 경계와 인계

- [x] 사용자에게 계정 누락 400까지 적용할지 현재 선택 헤더 동작을 유지할지 확인한다. 2026-09-11 서버 동작까지 필수로 맞추는 안 승인.
- [x] 확정 결과를 계약/런타임 실패 시험으로 일치시킨다. 신규 계정 누락·빈값·공백 15 RED → 경계 27 GREEN, 계약 5 RED → 6 GREEN. 기존 승인 문면을 소급 삭제하지 않는다.
- [ ] 승인된 필수 헤더 10건의 contract-breaking 결과를 보존하고 계약·서버·시험의 로컬 재동결 커밋 경계를 확인한다. 검사만 통과시키려고 HEAD 비교를 우회하지 않는다.
- [ ] 배포 IP·429·동일 SHA dev 확인 및 수용 검토 후에만 대장을 닫는다. 그 전에는 partial을 유지한다.
