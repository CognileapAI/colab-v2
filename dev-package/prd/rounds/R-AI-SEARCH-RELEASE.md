# AI 검색 릴리스 실행 계획

> 상태: 최신 main 통합과 로컬 전수 검증 완료. `local-stage`/ST, `main`, DEV 배포는 아직 실행하지 않았다.
> 기준 작업: `codex/ai-search-next` `86aaf22b` 와 `origin/main` `c7504875` 비-rebase merge.
> 최신 인계: `dev-package/sessions/20260914-ai-search-client.md`.

## 목표와 비목표

이 회차는 이미 로컬에서 검증한 AI 검색 변경을 최신 main 기반에서 다시 검증하고, ST 리허설 후 main과 DEV로 순차 승격할 수 있는 단일 릴리스 후보를 만든다.

- `K4` 상태는 `open`을 유지한다.
- 실제 Sonnet 호출·A층 품질 평가는 기존 보류를 유지한다.
- 일일 갱신 worker와 Sonnet 개념 제안 경로는 런타임 배선과 운영 승인 전까지 가동하지 않는다.
- 현재 온톨로지 DB 데이터를 삭제·교체하지 않고, dev-reseed는 main 코드만 통합하며 데이터 재생성은 실행하지 않는다.

## 릴리스 실범위

- 접근 정책: platform migration `0032_private_owner_access`.
- 검색 스키마: platform migration `0033_search_changes` → `0034_search_fact_snapshots` → `0035_search_ontology` → `0036_search_refresh_runtime`.
- ST 보호: `ONTO-PROTECT` 에 기록된 일반 앱/배포 자격의 온톨로지 삭제 거절과 데이터 보존 재확인.
- 제품: 자료 근거·변경 원장·온톨로지·제한된 자연어/유형 조건 검색을 위한 core-api·ai-service 코드.
- 계약/생성물: 검색 API·seam·의미 규칙과 정본 명령으로 다시 만든 클라이언트/타입.
- 화면: 검색 범위·해석 조건·출처·비교 속성·연구 입력/기준 선택과 상세 이동.

## 사용자 승인과 승격 순서

1. 최신 `origin/main`을 기능 브랜치에 비-rebase merge하고 충돌·자동 병합 의미를 검토한다.
2. 계약 생성물을 재생성한 뒤 최신 통합 트리에서 로컬 관련 게이트와 전수 회귀를 통과한다.
3. 2026-09-14 사용자 지시(“작업 순서대로 진행”) 범위에서 `local-stage`로 승격·배포하고, 온톨로지 보호·마이그레이션·검색 여정을 ST에서 재검증한다.
4. ST 근거와 변경 목록을 대조한 뒤 같은 사용자 승인 범위에서 main에 승격한다.
5. main 포함 SHA와 배포 산출물을 고정하고 같은 사용자 승인 범위에서 DEV에 배포한다. 마지막 판정은 동일 실행의 `deploy_doctor` 15/15이다.

## advisor `approve-with-changes` 수용 조건

다음 조건을 모두 닫기 전에는 승격 후보를 완료로 판정하지 않는다.

- main의 BO-3·후속 대장 항목·dev-reseed를 누락 없이 보존하고, AI 브랜치의 최신 K4 evidence·`ONTO-PROTECT`를 함께 보존한다.
- 자동 병합된 계약·API·frontend 소비자를 다시 검토하고, 생성물 diff와 전수 회귀를 최신 통합 트리에서 새로 만든다.
- ST에서 migration 적용·데이터 보존·삭제 거절·실제 검색 여정을 재검증하고, 이 결과를 로컬 green으로 대체하지 않는다.
- Sonnet 평가·일일 worker·운영 지속 확인을 보류 상태로 명시하고, 가동·K4 완료로 확대 보고하지 않는다.
- main·DEV는 2026-09-14 사용자가 승인한 순서를 따르되, 각 단계 직전 최신 원격 tip·직전 환경 근거·go/no-go를 다시 대조한다. DEV 완료는 main SHA 대조를 포함한 `deploy_doctor` 15/15 단일 실행으로만 판정한다.

## 단계 체크리스트

- [x] 통합: `origin/main` 비-rebase merge, 충돌 의미 해소, 릴리스 계획 작성.
- [x] 로컬 검증: 계약 재생성, 좁은 통합 게이트, 서비스·frontend 전수, 마이그레이션 drift/schema, 브라우저 여정.
- [ ] `local-stage`/ST: 승인된 순서에 따라 승격·배포, 온톨로지 보호·데이터 보존·검색 여정 재검증.
- [ ] main: ST 근거와 최신 원격 tip을 대조한 뒤 승격.
- [ ] DEV: main 포함 SHA 고정, 배포, `deploy_doctor` 15/15 단일 실행.

## 현재 인계

로컬 최종 `all`은 67/67 green이다. 실제 참조자료 실물 대조를 수행했고, 실제 Sonnet 평가는 `COLAB_HARNESS_EVAL_EXEMPT=1`로 보류를 드러냈다. 종합 실행의 시각 항목은 앱 프로세스와 core 전수 테스트의 간섭을 피하려고 명시 면제했으며, 직전 일회용 인증 스택의 별도 `frontend-visual`에서 검색·상세 2페이지, 13px 미만 0건, 대비 미달 0건, 스크린샷 4장을 확인했다. core 전수는 앱 정리 후 1,383/1,383 green으로 재확인했다. 근거는 `dev-package/reports/ai-search-release/`에 있다.

다음 단계는 `local-stage` 원격 tip·ST 배포 잠금·백업/복구 근거를 다시 확인하고, go/no-go 검토가 승인되면 ST 승격을 집행하는 것이다. ST·main·DEV는 아직 실행하지 않았다.
