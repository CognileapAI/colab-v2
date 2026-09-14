# AI 검색 릴리스 실행 계획

> 상태: `local-stage`/ST 배포와 실제 사용자 여정 완료. main/DEV 승격은 최신 main의 프런트 게이트 42건 RED로 중단했다.
> 기준 작업: `codex/ai-search-next` `a383510d`(AI 검색 `86aaf22b` + `origin/main` `4cb5c397`까지 비-rebase merge + ST 기간 표시 회귀 수정).
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
- [x] `local-stage`/ST: `a383510d7ded` 승격·배포, 온톨로지 보호·데이터 보존·검색 여정 재검증.
- [ ] main: ST 근거와 최신 원격 tip을 대조한 뒤 승격.
- [ ] DEV: main 포함 SHA 고정, 배포, `deploy_doctor` 15/15 단일 실행.

## 현재 인계

최신 제품 코드 HEAD의 종합 실행은 66개 green과 `migration-drift` red 1개를 냈고, 같은 commit/tree에서 그 항목을 즉시 단독 재실행해 오라클 26/26 green으로 확인했다. 최초 red와 재검사 green을 함께 보존하며 이를 단일 67/67 실행으로 확대해 적지 않는다. 이후 main에서 합쳐진 문서·대장 전용 변경은 `planning-freshness`와 `work-item-consistency`를 최신 HEAD에서 다시 통과했다. 실제 참조자료 실물 대조를 수행했고, 실제 Sonnet 평가는 `COLAB_HARNESS_EVAL_EXEMPT=1`로 보류를 드러냈다. 종합 실행의 시각 항목은 앱 프로세스와 core 전수 테스트의 간섭을 피하려고 명시 면제했으며, 직전 일회용 인증 스택의 별도 `frontend-visual`에서 검색·상세 2페이지, 13px 미만 0건, 대비 미달 0건, 스크린샷 4장을 확인했다. core 전수는 앱 정리 후 1,383/1,383 green으로 재확인했다. 근거는 `dev-package/reports/ai-search-release/`에 있다.

ST는 `a383510d7ded`에서 배포 판정 15/15, migration 체인 2/2, 온톨로지 보호 GREEN을 통과했다. D9 행 수는 `49/19/13/4/18`로 배포 전과 같고, 실제 UI에서 검토 근거 저장·새로고침·서울/2025/월평균/강수량/tif 조건 입력·1건 판정·출처 비교·상세 이동·상세 새로고침을 확인했다. 첫 ST 실행 `b8d53a74078f`에서 비교 기간이 응답 키 순서대로 뒤집혀 표시되는 결함을 발견했고, 실패 회귀 테스트를 거쳐 `a383510d`에서 `시작일 ~ 종료일`로 수정·재배포했다. 해당 검색 구간의 core 요청은 200 두 건이며 ai-service의 `/searches` 또는 모델 경로 요청은 0건이다.

main 직전 재fetch에서 `origin/main`이 `6a4ac6c4`로 이동했다. 이를 시험 병합한 트리 `ba12eb074ea7773e09ca117d44eb4fdf6cfc0c73`의 core-api 1,385건과 viz-render 448건, 생성물 17건, 대장 230건, 기획 임베드 15건은 GREEN이었으나 frontend는 123파일 중 8파일, 1,443건 중 42건 RED였다. 이는 새 main 인계 `§4` 블로커 76의 실패 분포(등록 약 31건 + 확인 버튼 11건)와 일치한다. 로컬 판정 JSON은 `dev-package/reports/ai-search-release/main-refresh/frontend/gate-summary.json`이며, 실패 트리를 커밋·배포하지 않고 병합을 중단했다. main/DEV 승격은 이 외부 블로커가 닫힐 때까지 보류한다. 실제 Sonnet 평가는 계속 보류하고 K4·ONTO-PROTECT는 `open`이다.
