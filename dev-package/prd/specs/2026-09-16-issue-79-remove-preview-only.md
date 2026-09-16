# #79 업로드 미리보기 전용 선택 제거

Intent: `dev-package/intent/2026-09-16-issue-79-remove-preview-only-choice.md`

## 수용 기준
- 업로드 결정 영역에 `보기만 할게요`가 없고 `다음 →`가 남는다.
- 다음을 누르면 같은 모달의 분류 입력으로 들어간다. 그 자체로 데이터셋이 생성되거나 주소가 바뀌지 않는다.
- 등록 중 PreviewPanel과 그리던 미리보기가 유지된다.
- 닫기 후 접수 완료 업로드를 다시 열어 등록을 이어갈 수 있다. 전송 재개·숨기기·만료 계약은 유지한다.

## 구현 경계
- UploadModal의 `viewOnly`, `reg-viewonly`, 전용 `previewNavigation` import 제거. 관련 주석을 현재 정책으로 고친다.
- 전용 이동만 소비하던 rendered·bodyByteSize와 PreviewPanel의 호출자 없는 onRender 콜백을 함께 제거한다. 실제 렌더·onResult 경로는 유지한다.
- upload.test의 해당 전이 시험을 현재 정책의 사용자 동작 시험으로 개정한다.
- 미등록 미리보기 직접 URL과 페이지, 서버/API/DB, 자동 분석 시점, 기존 CSS는 변경하지 않는다.
- 서버 부하 감소량을 이번 UI 변경으로 보장하지 않는다.

## 검증
- 먼저 선택지 부재와 등록 진입 시험의 실패를 확인하고 최소 구현 후 통과 확인.
- 프런트 타입·전체 시험 및 실제 브라우저의 선택지 부재→등록 진입→닫기→등록 복원·새로고침 검증.
- frontend-visual 실제 업로드 화면 1개 이상 검사. 이 검사는 동작 검증과 별개다.
- intent 미달/초과 대조 및 결과는 task runtime에 기록한다.
