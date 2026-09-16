> spec: dev-package/prd/specs/R-SELECTED-PREVIEW-TIMING.md
# 선택 미리보기와 개별 시간 측정 실행 계획
> 후속 승인: 사용자가 "pr니가 민들어"라고 요청하여 이 변경의 커밋·기능 브랜치 push·develop 대상 PR 게시를 에이전트가 수행한다. 병합·배포·reseed 실행은 포함하지 않는다. 아래 로컬 인계 기록은 게시 전 검증 시점의 기록이다.
**Goal:** 선택된 파일·시점만 명시 실행하고 요청별 시간을 올바르게 측정한다.
**Architecture:** 기존 UI/API/worker/관측 로그 재사용. 독립 UI·서버 작업을 분리 사본에서 구현 후 통합한다.
**Tech Stack:** React/TypeScript, Python, Vitest/pytest/agent-browser.
**Spec:** 위 출처 spec. 사용자 ‘좋아’로 권고안 수락.
## Global Constraints
- 기존 미커밋 보존. 원격push/PR게시/배포/reseed 반복 없음.
- API/DB 변경 없음. 비밀 로그 금지. 실패를 면제나 빈 표본 성공으로 바꾸지 않는다.
## 상태
- [x] 실물 조사·intent·spec·계획 작성.
- [x] advisor 계획 검토: 조건부 승인. 조회/생성 응답 유실의 중복방지, 타일표시 완료·미측정 규정 반영.
- [x] UI/검증 도구 구현·시험.
- [x] 서버 timing 구현·시험. 수용 검토 승인 후 통합 사본에서 541개 통과(건너뜀 0, 기존 선택자 제외 42).
- [x] 수용 검토·통합 게이트·로컬 브라우저 검증.
- [x] 최종 인계·PR 요약. 원격 게시는 미수행.
## Task 1 — 선택 실행·사용자 체감 시간
소유: UI 사본은 `frontend/src/components/datasetpreview/**`, 최소 공유 `frontend/src/components/preview/**`, 관련 frontend tests. 도구 사본은 `dev-package/tools/dev-seed/**`, `dev-package/tools/dev-reseed/**`를 별도 소유한다.
Interfaces: describe에선택file전달(기존fileIds API), create 단일fileIds; 서버 새 응답필드에 의존하지 않음.
1. 먼저 mount/선택변경 POST0, 보기1회→선택payload1회, 진행중중복0 시험을 작성·RED 확인.
   예: `render(<DatasetPreviewSection ... source={source}/>); expect(source.create).not.toHaveBeenCalled();` 선택·보기 click 후 `fileIds === [chosenId]` 검증.
2. idle/draft→submitting→drawing→done/failed 최소 구현, 후보없음 unsupported. 상세만 다른file폴백 제거.
3. 이미지decode/최초화면타일decode전 총소요시간확정0, 재선택/경합/실패재시도 시험. renderId확보후 조회실패는동일job조회만; 생성응답유실은 결과불명·재생성금지 회귀시험.
4. runner/stages 명시선택·보기·순차대기 시험 RED 후 수정. 검증대상 유지.
5. frontend-test/frontend-typecheck/product-reseed-selftest, patch/hash/로그 인계.
## Task 2 — 큐·실행 시간
소유: `services/viz-render/src/colab_viz/domains/d7_visualization/jobs.py` 및 viz tests. 관측 kernel/계약 수정 제외.
Interfaces: 기존 emit함수·`render.timing` event. render_id로 진단 기록 연결.
1. 기존 JobStore 시험에 fake clock 적용, 예 `queue_ms=20`, `processing_ms=30`의 독립기록 RED.
2. 실패도측정/타job누적금지/복원pending대기unknown 시험 RED.
3. enqueue/start/finish monotonic 값을 작업별 기록하고 worker finally에서emit. inline/manual/thread·큐거부 경로 대조.
4. service-tests-viz-render, 실측 근거·hash 인계. migration없음.
## Task 3 — 통합·수용
1. advisor가 intent미달·초과, 선택전POST0, 이미지/타일표시측정, DB변경없음 검토.
2. 부모가patch통합 후 필수게이트 각각실행, 종료코드·3계수 확인.
3. 로컬 fixture2자료에서 클릭/요청/중복방지/시간/실패를 확인. dev/prod 쓰기 없음.
4. 계획 갱신·로컬PR요약. 미배포와 미실행 검증을 분명히 기록.

## 중간 검토 기록
- 로컬 브라우저 기존 동작: 클릭 전 전체 데이터셋 create 1건, 범위 없는 describe 1건 재현.
- 서버 수용: 실제 terminal 상태별 판정과 journal 복원 시 대기시간 미측정 시험 보완 후 승인.
- UI 첫 수용은 보류였음: 생성 응답 유실 후 재클릭, 조회 오류 후 동일 작업 재조회, 이전 decode와 새 요청의 시간 혼합, 상대 URL 타일 완료 판정을 보완했고 최종 조건을 충족했다.
- 기존 미반영 reseed 도구 수정 7파일은 명시 실행 검증의 선행 수정으로 도구 사본에서 검토·통합한다. 이전 자동 렌더를 기다리는 직렬화 패치는 그대로 적용하지 않는다.

## 최종 인계 — 2026-09-16
- 구현 사본: `/tmp/colab-preview-selected`, 브랜치 `feat/selected-preview-timing`, 기준 `d81e43871f08a221478c84ab9f3990103a6f4384`. 변경은 미커밋 상태다. 원래 작업 사본의 기존 변경은 보존했다.
- 부모 통합 검증: frontend-test 1,522건, frontend-typecheck 오류 0, viz-render 541건(선택자 제외 42, skip 0), product-reseed-selftest 104건(필수 28/28), 추가 dev-seed 관련 pytest 58건 통과. 각 게이트 성공 1 / 판정 실패 0 / 준비 실패 0.
- CSS 정적 검사: 변경한 preview.css에 글자 크기·음수 여백·미정의 토큰·대비 위반 0. 기존 다른 파일의 정적 지적은 보고서에 보존했다. frontend-visual은 선언한 로컬 페이지 1건, 작은 글자 0·낮은 대비 0, 라이트/다크 2장.
- 브라우저 실측: 선택 전 create 0, file-b/temperature/선택 시각 payload 1, 작업 중 disabled, 이미지 decode 후 시간 1, 타일 6개 전부 로드/decode 후 시간 1, 생성 응답 유실 시 create 1·시간 0·보기 잠금, 서버 실패 시 시간 0, 조회 오류 뒤 같은 ID 조회만 재개. 모바일 폭 390에서 프레임 390×292.5(4:3), 지도 높이 양수.
- 타일 높이 0을 실제 브라우저에서 발견해 기존 4:3 높이가 내부 지도까지 전달되게 최소 CSS 수정했다. advisor가 필수 의존 수정으로 승인했다. 검증 fixture의 sidecar 누락·인라인 SVG URL 구성 오류도 별도로 바로잡았다.
- 수용 검토: 서버 승인, UI 마지막 일반 예외 잠금 조건 보완, 도구 timeout 중단·실제 enabled 판정·비동기 미지원 대기 보완 후 승인. DB 마이그레이션 없음.
- 공용 상태의 기존 소비자인 미등록 미리보기 화면에도 결과 불명 안내·동일 ID 조회 재개를 연결했다. 새 생성 0건 회귀시험과 수용 검토를 통과했다. 파일 목록 조회로 미지원이 확정된 화면은 실제 브라우저에서 요청 0·보기 잠금으로 확인했다.
- intent 대조: 선택 실행·중복 방지·요청별 측정·순차 검증 4항 충족. 미달 0, 승인되지 않은 초과 0. 기존 타일 높이 수정과 이전 도구 선행 수정은 목적 달성을 위한 의존 수정이다.
- 근거 디렉터리: `/home/ttlhi10/.local/state/colab/selected-preview-20260916/`. 브라우저 시간은 로컬 모의 응답과 수동 완료 대기를 포함하며 실제 원본 파일의 성능 측정값이 아니다.
- 미실행: dev/prod 실제 렌더·전체 reseed·배포·원격 CI. ERA5 좌표 오류는 그대로 별도 해결 대상이다. 업로드 확장 화면의 새 사용자 여정은 이번 범위 밖이며 기존 회귀시험만 수행했다.
- 브라우저 환경 제약: 의존성 symlink 때문에 Vite가 Pretendard 원본 폰트 요청을 차단했다. 크기·대비와 동작은 대체 폰트 상태에서 관측했으며 배포 환경의 정확한 글꼴 재현은 미검증이다.
- PR 초안: `R-SELECTED-PREVIEW-TIMING-PR.md`. 커밋 후 Head-SHA, 원격 게시 후 CI-Ref를 실제 값으로 갱신한다.
