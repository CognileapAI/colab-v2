> spec: dev-package/prd/specs/2026-09-16-issue-80-76-preserve-values.md
# 계보 단계·기간 입력 보존 실행 계획

**Goal:** 승인된 #80·#76 intent의 사용자 입력 보존을 구현하고 로컬 실제 저장·조회까지 검증한다.
**Architecture:** 기존 업로드 상태와 상세 수정 draft를 바로잡고, 기간 입력은 등록 컴포넌트를 재사용한다.
**Tech Stack:** React 19, TypeScript, Vitest, agent-browser, 기존 core-api·일회용 Postgres.
**Spec:** 첫 줄 링크. 두 intent는 2026-09-16 사용자 “좋아 그다음 단계”로 승인.

## Global Constraints
- 새 의존성·계약·DB 변경 없음. 정밀도 축소와 미변경 데이터 보존을 구분한다.
- 개발 브랜치 `codex/issue-80-76-preserve-values`, 기준 `8c063cf2`.
- 한 사본 쓰기 주체 1명. 구현은 직렬, 읽기 전용 조사·검토만 병행.
- 커밋·push·PR 게시·배포를 하지 않는다. 운영 DB·컨테이너를 접촉하지 않는다.
- 테스트 실패를 구현 전에 확인. 최종 변경 후 필수 게이트 재실행 및 runtime 검증.

## 상태·의존
- [x] develop 최신화·도구 확인·이슈 조사.
- [x] #80·#76 intent 설명·사용자 승인 기록.
- [x] 구현 spec와 실행 계획 작성.
- [x] advisor 계획 검토: 무수정 팝오버 적용과 실제 계보 조작 네 경로 보강.
- [x] #80 RED → 구현 → 관련 시험 GREEN.
- [x] #76 RED → 구현 → 관련 시험 GREEN.
- [x] 실제 브라우저 등록·편집·저장·새로고침 검증: after-2 단일 실행 6개 시나리오 묶음 통과.
- [ ] 최종 frontend-typecheck·frontend-test 및 필요 시 디자인 검사.
- [ ] 독립 수용 검토·intent 대조·로컬 PR 요약·인계.
- 이후 이슈: #73·#82 → 업로드/프로젝트 개선. #79 미리보기 전용 선택 제거 방향은 확정됐으며 별도 intent로 진행한다. 이번 구현의 승인 범위는 위 두 intent다.

## Task 1: 계보 연결에서 선택한 가공 단계 유지
**Files:**
- Modify: `frontend/src/components/upload/UploadModal.tsx`, `frontend/src/components/lineage/LineageStep.tsx` 및 해당 context 정의(검색으로 실제 소비자 전수 확인).
- Test: `frontend/test/processing-level-default-20260913.test.tsx`, 영향받는 lineage/upload 시험.
- Docs: 기존 `dev-package/intent/2026-09-13-lth-processing-level-mismatch.md` 자동 추종 결정 개정 링크.
**Interfaces:** 기존 processingLevelUserSet 및 부모 목록 계약 유지. 단계는 부모 계산값에 의해 덮이지 않음.

- [ ] 기존 시험의 미접촉 기본값 흐름에서 다음 행동 기준으로 기대를 개정하고 실패를 확인한다.
```tsx
await openLineageUntouched(sources);
await click(screen.getByTestId('lin-add'));
await screen.findByTestId('lin-picker');
expect(screen.getByTestId(`lin-pick-${LV1}`)).toBeDisabled();
expect(screen.getByTestId(`lin-pick-${LV2}`)).toBeDisabled();
```
- [ ] `npm test -- --maxWorkers=2 test/processing-level-default-20260913.test.tsx`의 기대 실패를 runtime에 보존한다.
- [ ] 자동 추종 상태/효과와 부모 상한 해제 경로만 제거한다. 실제 호출자를 검색해 미사용 필드가 남지 않게 한다.
- [ ] 기존 단계 변경 입력은 값만 갱신하고, 계보 계산값은 안내에만 남긴다.
- [ ] 같은 단계 연결·해제/왕복 후 선택값 유지, 높은 후보 제한, 기존 연결 후 단계 하향 충돌을 시험한다. 등록 요청의 선택값을 단언한다.
- [ ] 관련 시험군 GREEN 후 다음 태스크로 이동한다.

## Task 2: 상세 기간 정밀도 보존
**Files:**
- Modify: `frontend/src/components/detail/editFields.ts`, `frontend/src/components/detail/DatasetEditForm.tsx`.
- Reuse: `frontend/src/components/upload/periodParts.ts`, `PeriodCalendarPopover.tsx`.
- Test: `frontend/test/detail-edit.test.tsx`, `frontend/test/interval-period-20260906.test.tsx` 및 필요 시 기간 전용 회귀시험.
**Interfaces:** DatasetEditDraft는 전체 기간을 보존하며 onField 문자열 인터페이스를 가능한 유지. period patch 계약은 불변.

- [ ] 다음 보존 기준을 기존 실제 fixture에 적용한 시험부터 작성한다.
```tsx
const original = {...detail, basicInfo: {...detail.basicInfo!, period: {
  start: '2026-09-18T23:30:00Z', end: null, granularity: '분'
}}};
const draft = toDraft(original);
expect(toPatch(original, draft)).not.toHaveProperty('period');
expect(applyDraft(original, {...draft, name: '새 이름'}).basicInfo?.period)
  .toEqual({start: '2026-09-18T23:30:00Z', end: null, granularity: '분'});
```
- [ ] 편집 진입에서 실제 시·분 표시와 편집을 시험하고, 현재 날짜-only 실패를 확인한다.
- [ ] `npm test -- --maxWorkers=2 test/detail-edit.test.tsx test/interval-period-20260906.test.tsx`로 RED 증거를 보존한다.
- [ ] draft 시각 절단을 제거하고, 기존 기간 팝오버의 적용 시점에만 문자열 조립을 수행한다. 무변경 원본은 재조립하지 않는다.
- [ ] toPatch 및 applyDraft에서 단위 미지정·끝 null·기간 null·미변경을 보존한다.
- [ ] 팝오버를 열어 아무것도 바꾸지 않고 적용해도 null 단위나 표시 단위 아래의 원본 시각을 보존한다. 단위 명시 변경과 무수정 적용을 시험으로 구분한다.
- [ ] 분/초 편집, 년~초 입력, 단위 축소, 삭제, 팝오버 취소/Esc, 이름만 수정하는 시험을 실행한다.
- [ ] 새 스타일이 필요하면 토큰·기존 클래스 우선. CSS 변경 시 디자인 정적/시각 검사 추가를 선언한다.

## Task 3: 실제 브라우저 및 최종 검증
**Files:** 이번 시나리오 `scripts/issue-80-76-journey.py`; 실행 결과는 Git runtime의 전용 근거 폴더.
**Interfaces:** `scripts/e2e-login.py --journey`의 `run(command,args,session)` 재사용. 실제 API와 일회용 DB, 일반 연구원 역할. 비밀번호·접속 문자열 출력 금지.

- [ ] 기존 `scripts/e2e-login.sh`를 사용해 tmpfs·포트 비공개 일회용 DB를 준비한다. 자식 앱과 브라우저는 기존 정리 절차로 종료한다.
- [ ] 실제 화면에서 Lv.0 기본값의 초과 부모 차단·같은 단계 연결·선택값 보존을 확인하고 등록/조회값을 대조한다.
- [ ] 직접 단계 선택·연결 해제·단계 왕복·연결 후 하향 충돌을 실제 조작한다. 하향 시 카드 유지와 등록 차단, 충돌 해소 후 저장·재조회를 확인한다.
- [ ] 실제 데이터셋 편집에서 분 시각 표시·변경·저장·새로고침, 다른 필드만 저장해 기간 유지, 단위 축소를 확인한다.
- [ ] 스크린샷·행동 결과·사용한 fixture/환경을 남긴다. 막히면 해당 조건을 미실행으로 명시한다.
- [ ] 마지막 제품·시험 변경 뒤 `frontend-typecheck`, `frontend-test`를 하나의 task run으로 실행한다. CSS 변경 시 추가 검사 결과도 회수한다.
- [ ] advisor 수용 검토 후 지적을 수정하면 영향 시험과 최종 증거를 다시 갱신한다.
- [ ] 각 intent의 원한 결과별 미달·초과를 기록한다. 배포되지 않은 로컬 검증 결과임을 명시한다.
- [ ] 로컬 PR 요약과 다음 이슈 진입조건을 남기고 runtime 인계한다.

## 검증 기록
- 승인·계획 단계: 제품 코드 변경 및 기능 시험 없음.
- 수정 전 실제 브라우저: 로컬 일회용 API/DB·일반 연구원. 분 단위 fixture에서도 날짜-only 수정 입력임을 캡처했다. `edit-period-open` 부재로 예상 실패(exit 1); 통과가 아니다.
- 수정 전 근거: `.git/colab-evidence/issue-80-76/before/01-period-edit.png`, `journey.json`.
- 구현 작업 사본: `/tmp/colab-issue-80-76-implementation`, 승인 입력 4개 복사 후 hash 일치 확인. 코드·시험 쓰기 주체는 한 명이다.
- 구현 사본 검증: task `835a6ad03559418fb2989f3557994ed4`, run `98fc21bd3e134171ac27e4a01faafc17`. frontend-typecheck 오류 0; frontend-test 124파일/1496시험/실패0. 부모가 verify-report로 현재 파일과 직접 대조했다.
- 구현 사본 최초 targeted RED는 터미널 출력으로 확인(#80 3건, #76 2건); 별도 로그 파일 없음. 전체 시험 중간 실패는 run `3c20d48f62ab435a8b74f68194b20c6e`에 보존. 원천 정보 조건을 바꾸는 범위 초과는 원복했고, 시험의 가공 단계 전제를 명시하여 회귀를 해소했다.
- 실제 브라우저 after-2: exit 0, `journey.json` status=passed. 무수정 적용·다른 필드 저장·분 변경·단위 축소·null단위/끝없음, 가공 단계 상한·왕복·해제·하향 충돌·실제 등록 후 DB/새로고침 대조를 통과했다.
- 브라우저에서 발견한 기간 버튼 넘침/상세 입력 스타일 상속은 기존 클래스/컨테이너 재사용으로 수정했다(CSS파일 변경 없음). 최종 화면·좁은 너비 검증은 `.git/colab-evidence/issue-80-76/after-final/`에 별도 보존한다.
- 최종 통합 검증: frontend-typecheck, frontend-test, work-item-consistency를 한 task run으로 실행한다. 이 계획 파일의 마지막 수정 후 실행하며, 결과·최종 체크 상태·PR 요약은 Git runtime 인계가 정본이다.
- 구현 사본 종료 훅은 신규 runtime 대신 legacy 경로를 찾는 호환 오류를 보고했다. 기존 보고서의 직접 verify-report는 통과했으며, 훅 오류를 숨기거나 legacy 증거를 만들어 우회하지 않았다.
