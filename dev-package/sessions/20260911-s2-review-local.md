# Stage 2 코드리뷰 후속 — 로컬 계약 대조

HEAD `712a33711f6a222ff7c1d431c4ecef0946508cca` 위 미커밋 작업 트리.
사양 `prd/specs/s2-review.md`, 실행 `prd/rounds/R-S2-REVIEW.md`.

## 구현과 증거

- core-viz의 실제 tenant_scope 호출 5개 op에 LabScope 헤더 필수 선언.
- getRender 400 응답 및 ScreenshotRequest.layers 1~8건 선언. 런타임 상한 변경 0.
- `node --test contracts/tests/s2-review.test.cjs`: 실제 YAML을 고정 PyYAML/AJV 2020으로 읽어 요청을 검증, 6 failed RED → 6 passed/skip 0 GREEN.
- contract-lint: seam 3건 룰 위반 0. Node punycode 폐기 경고 1건은 별도이며 룰 실패는 아니다.
- seam-consistency: G-e 472, G-b 10, 신설 38, 단계 18, 끊긴 자리 0. lint 종료 확인을 놓쳐 두 읽기 전용 게이트 실행이 잠시 겹쳤다. 순차 실행했다고 보고하지 않는다.
- CI schema 준비 selftest 2건, planning 합성 fixture selftest 5건 통과. 원격 CI 재실행이나 실제 기획 정본 대조 성공으로 확대하지 않는다.
- Viz 서비스 전체: 398 passed, skipped 0, deselected 42, 14.73초, exit 0. 연구실 경계와 스크린샷 상한 시험 포함.
- 새 계약 소비 시험은 명시적 위 node 명령으로 실행한다. 기존 all 게이트 자동 포함을 주장하지 않는다.

## 확인 경계

### 2026-09-11 후속 승인·집행

질문: “승인안대로 계정 정보가 없는 내부 요청도 HTTP 400으로 거절하도록 서버 동작까지 맞출까요?”
사용자: “맞아”. 계약 필수 선언뿐 아니라 서버의 계정 누락 400을 승인한 것이다.
`tenant_scope`와 5개 op의 AccountScope를 맞췄다. 누락·빈값·공백은 같은 오류이며,
오류 details.header는 X-CoLAB-Account다. 타 연구실 404, 서명 타일과 팔레트 경계는 유지한다.
경계 시험 신규 15건 RED(기존 12 passed) → 전체 27 passed, 계약 5 failed/1 passed → 6 passed.
변경 후 서비스 전체: viz 413 passed/skip 0/deselect 42/15.44초(기존 rasterio 경고 1건),
core 1,060 passed/skip 0/deselect 6/59.73초. contract-lint 3 seam 위반 0,
seam-consistency G-e 473/G-b 10/신설 39/단계 18 green, work-item-consistency 불일치 0.
보고 경로 `dev-package/reports/stage12-account-required/<gate>/gate-summary.json`.

generated-up-to-date 최초 판정은 RED였다: core-viz를 참조하는 fe-core 생성 타입의
ScreenshotRequest.layers 설명 1줄이 낡았다. manifest 정본 openapi-typescript로 재생성했고
재검증은 `recheck-generated-up-to-date`, `recheck-frontend-typecheck` 보고 경로에서 확인한다.
재검증 결과: 생성물 13건 전부 일치, 등기부 밖 0건; frontend src/test 타입 오류 0건, 둘 다 exit 0.

contract-breaking은 HEAD 대비 ERR 10/ WARN 0/ INFO 0, exit 1이다.
전부 5개 op × 연구실/계정 필수 헤더 2개이며 승인된 변경에 대응한다.
통과로 바꾸지 않는다. 비교 기준은 스크립트가 정한 HEAD이며,
승인 없는 커밋·기준선 변경으로 이 판정을 없애지 않았다.
다음 경계는 이번 계약·서버·시험의 로컬 재동결 커밋이다. push·배포 승인과 별개다.
⟨2026-09-11 승인⟩ 사용자 “좋아”: 위 계약·서버·시험 변경을 현재 작업 브랜치에 로컬 커밋해
새 기준으로 고정하는 데 동의했다. 원격 push와 배포는 명시적으로 제외한다.
커밋에는 관련 사양·계획·승인 증거와 생성 타입의 해당 설명 한 줄만 포함하고,
다른 Stage 1·2 진행 중 변경은 작업 트리에 보존한다.

⟨로컬 재동결 결과⟩ `eac2f0b`, 관련 9파일(계약·서버·시험·승인/설계 기록·생성 설명 1줄).
커밋 직전 경계 27 passed와 계약 소비 6 passed를 다시 확인했다.
새 HEAD 기준 contract-breaking exit 0, 판정 실패 0/준비 실패 0.
보고: `dev-package/reports/stage12-account-required/refrozen-contract/gate-summary.json`.
이전 ERR 10 근거는 위에 보존한다. 나머지 작업 트리 변경과 후속 검증 기록은 미커밋이며
원격 push·배포·main 병합은 수행하지 않았다. Stage 1·2 전체 완료를 의미하지 않는다.

### 확인 전 이력

승인 기록 `sessions/20260910-stage12-decisions.md Q4`와 원 초안
`sessions/CODE-REVIEW-20260903-C.md`는 연구실·계정 헤더를 모두 필수로 적었다.
실제 `services/viz-render/src/colab_viz/app/deps.py::tenant_scope`는
연구실 누락만 400이고, 계정은 출처 표시로 받아 누락을 허용한다.
따라서 당시 '이미 그렇게 동작한다'는 전제는 계정에 대해 틀렸다.

필요한 사용자 확인: 승인 문면에 맞춰 계정 없는 요청도 400으로 바꿀지,
현재 동작을 유지하고 계정 헤더를 선택으로 정정할지.
확인 전에는 계정 헤더의 필수 선언/런타임 변경을 하지 않았다. 후속 승인·집행은 위 절 참조.

## 남은 검증

- 위 결정 반영 뒤 계약·런타임 일치 시험 및 계약 변경 비교, 최종 트리 전수.
- 실제 전달 IP/여섯 번째 실패 429, 같은 배포 SHA의 healthy/재굽기·소유 관측.
- 배포·main push·실제 삭제·원격 apply는 실행하지 않았다. CR-2 partial을 유지한다.

읽기 전용 조사자는 같은 모순을 독립 확인했다. 공유 dirty checkout의 lifecycle unchanged 검사로
COLAB_HANDOFF 발급은 차단됐다. 정상 인계 게이트 통과로 세지 않으며 부모가 실제 deps/계약과 시험을 직접 대조했다.
