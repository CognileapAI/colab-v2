> spec: dev-package/prd/specs/2026-09-16-issue-79-remove-preview-only.md
# 업로드 미리보기 전용 선택 제거 실행 계획

**Goal:** 등록 결정 영역에서 보기만 하기 선택을 없앤다.
**Architecture:** 기존 UploadModal의 전용 분기만 제거하고 등록·복원 상태 경로를 재사용한다.
**Tech Stack:** React, TypeScript, Vitest, agent-browser.
**Spec:** `dev-package/prd/specs/2026-09-16-issue-79-remove-preview-only.md`

## Global Constraints
- 새 의존성·CSS·API·DB 변경 없음. 등록 중 미리보기 및 중단 후 복원 유지.
- 작은 단일 UI 분기 수정이므로 부모가 직접 수행한다. 병렬 쓰기 없음.
- 기준: PR #86이 머지된 develop `e77374ec`에서 새 브랜치.
- 이번 지시는 후속 구현 진행이며 원격 게시·머지는 별도 실행하지 않는다.

## 실행 및 검증 상태
- [x] 이슈 댓글·영향 경로 조사 및 기존 초안 제시.
- [x] PR #86 머지 확인, 최신 develop에서 분기.
- [x] `frontend/test/upload.test.tsx`의 선택지 부재와 다음→등록 진입 시험으로 RED 확인: 2실패/132통과.
  - `expect(screen.queryByTestId('reg-viewonly')).toBeNull()`
  - `reg-open` 클릭 후 `reg-s1`, `up-preview` 존재, register 호출 0회, 주소 유지.
- [x] `frontend/src/components/upload/UploadModal.tsx`의 버튼·전용 함수·import와 고아 상태 제거. PreviewPanel의 고아 onRender 콜백도 제거.
- [ ] 관련 시험 GREEN 및 전체 프런트 타입·시험 게이트.
- [ ] 실제 브라우저에서 업로드→선택지 부재→등록→닫기→복원→새로고침 확인 및 화면 저장.
- [ ] 실제 업로드 화면 시각 게이트, intent 미달/초과 확인, 검증 보고서와 현재 파일 대조.

## 증거 위치
task runtime의 최종 인계에 단계 결과·실행 수·제약과 다음 진입조건을 한 번 기록한다. 계획 체크 표시는 실행 전에 적은 상태이며 최종 판정은 그 인계를 따른다.

## 중간 검증 이력
- 최초 시험 명령은 작업 디렉터리가 맞지 않아 대상 0건으로 종료했다. RED 근거로 쓰지 않는다.
- 올바른 디렉터리에서 2실패/132통과를 확인한 뒤 구현했다. 관련 3파일 176시험 통과.
- 첫 실제 브라우저 3단계는 통과했으나 전체 타입 검사에서 제거한 이동 함수의 고아 상태 2건을 검출했다. 정리 후 최종 게이트와 브라우저를 다시 실행한다.
