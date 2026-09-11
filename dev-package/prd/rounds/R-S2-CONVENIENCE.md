> spec: dev-package/prd/specs/s2-convenience.md

# R-S2-CONVENIENCE Implementation Plan

진행 기록 2026-09-11: `sessions/20260911-s2-convenience-local.md`에서 실제 결과와 실패 이력을 추적한다.
Core/Pipeline 서비스, 격자 프로필·실제 렌더 경계, 타일 재사용, frontend 집중·타입 검증을 수행했다.
Frontend 전체 1,204건과 격리 브라우저 직접 격자→재사용→등록·새로고침·DB·필터 여정을 검증했다.
실제 CSS 가시성 후속 보완은 집중 16건과 타입 검증을 통과했으며 최종 트리 전수에 포함한다.
스테이징 배포와 실제 운영 변경은 기존 실행 직전 승인 경계를 유지한다.

## Task 1: 계약과 DB 원장

- [ ] J-1/J-2/J-3/J-4/J-5/J-9의 seam을 실패 계약 시험으로 고정하고 RED를 확인한다.
- [x] `0024_s2_grid_convenience` migration, assertions, head/previous/downgrade drift를 작성한다.
- [x] 선언 schema와 migration 적용 shape를 맞추고 RLS·교수 전용 판정·기존행 `아직 모름`을 증명한다.
- [x] fe-core 생성물을 갱신하고 generated/up-to-date 및 contract tests를 green으로 만든다.

## Task 2: 파이프라인 격자 프로필

- [ ] 본체/격자 형상, 격자 SHA-256·형식 서명, 실제 COG 경계, 지도 3상태를 저장하는 실패 시험을 먼저 작성한다.
- [x] pipeline-worker의 D5 Port와 SQL/메모리 대역에 프로필 upsert를 구현한다.
- [ ] 직접 업로드·격자 없음·읽기 실패·격자 전용 후주입 네 갈래를 green으로 만든다.
- [x] pipeline 서비스와 DB boundary를 green으로 만든다.

## Task 3: 격자 후보·가져오기·기본값

- [x] 같은 연구실/같은 형상 후보, 기본 제시만, 타 연구실 404, 연구원 기본 지정 403을 실패 시험으로 고정한다.
- [x] local/S3 exact-key 복제 Port와 rollback을 구현하고 동일 바이트 digest를 증명한다.
- [x] grid options/reuse/default API와 등록 전환 프로필 승계·D8 활동 1행을 구현한다.
- [x] 직접 업로드 대비 동일 grid digest → 동일 지도형 내용 키, 계보 무변경을 green으로 만든다.

## Task 4: 불일치·예상 영역·카탈로그 지도 상태

- [ ] 형식/해시 불일치의 비차단 경고, 쌍별 거리/[미상], 예상 경계 4값/[미상]을 실패 시험으로 고정한다.
- [ ] catalog `mapState` 응답·필터가 상세와 같은 프로필 값을 쓰고 RLS 안에서만 세는 시험을 작성한다.
- [x] 업로드 격자 블록과 카탈로그에 경고·예상 영역·배지·필터를 구현한다.
- [x] 적용 전 예상 경계와 렌더 완료 경계의 동일성을 green으로 만든다.

## Task 5: 팔레트·구간 수와 남은 시간

- [x] 데이터셋 상세 편집 권한자에게만 팔레트/3~9 구간 컨트롤이 보이는 실패 시험을 작성한다.
- [x] 서버 목록 3종만 사용하고 고른 `palette/classCount`로 재렌더하도록 구현한다.
- [ ] 단계별 표본 중앙값, 표본 0이면 ETA DOM 0, 전송 진행률 기반 예측을 실패 시험→구현 순으로 세운다.
- [x] frontend 단독 시험·타입 검사를 green으로 만든다.

## Task 6: 첫 파일 임시 미리보기

- [ ] 첫 본체 완료 전에는 임시 업로드가 없고, 완료 직후 한 번만 생기며, 최종 전송은 독립적으로 완결되는 실패 시험을 작성한다.
- [ ] transfer 원장 멱등 키, exact-copy 임시 D5 접수, 실패 rollback을 구현한다.
- [x] frontend transfer callback과 임시 고지, 최종 uploadId 수렴, 알림 정확히 1회를 구현한다.
- [x] 첫 미리보기 도달이 전량 완료보다 앞서며 등록은 최종 접수 전 불가함을 green으로 만든다.

## Task 7: 폴더 드롭 재사용 증거와 전체 검증

- [ ] F-3 기존 폴더 드롭이 직접 2파일 선택과 같은 결과, 서버 축 판별, 3개 이상 거절을 만족하는 대응 시험을 보강한다.
- [ ] core/pipeline/viz/frontend 서비스 게이트, generated/import/db/contract/planning 경계를 실행한다.
- [x] 가능한 로컬 브라우저 여정을 agent-browser로 검증하고 준비 실패는 미실행으로 기록한다.
- [ ] 세션 증거와 work-items를 갱신하고 consistency를 green으로 만든다.

## Task 8: 승인 경계와 닫기

- [x] Stage 1·2 전체 구현의 push·dev 배포·후속 통합검증 사용자 승인: `sessions/20260911-stage12-deploy.md`. 실행 전 SHA·이미지·영향·롤백과 go/no-go를 확인한다.
- [ ] 승인 후 같은 main SHA의 dev 배포·healthy·핵심 여정을 확인한다. staging은 리허설이며 완료 판정이 아니다.
- [ ] dev 배포와 단일 deploy_doctor 전건 통과, 기능별 완료 조건을 충족한 경우에만 `J-1`을 done으로 닫는다(전체 계획·CLAUDE.md §0 적용).
