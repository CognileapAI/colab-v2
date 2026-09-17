# Intent: 지도용 선택지를 미리보기를 그릴 수 있는 형식에서만 보인다
메타 — 발의자: samtae0610 · 방향 결정: Ted · 작성 2026-09-17 · 승인 2026-09-17(초안 4건 제시 후 Ted 명시 승인)

## 문제
- 전제 정정: 이슈가 보고한 `보기만 할게요` 버튼은 develop에 이미 없다. #79 작업에서 제거됐고 그 부재를 `frontend/test/upload.test.tsx:2239`가 잠근다(근거 spec `dev-package/prd/specs/2026-09-16-issue-79-remove-preview-only.md`). QA 재현 빌드가 #79 이전 판이었다. 이슈 전반부는 무효다.
- 남는 요구는 이것이다. 문서 파일처럼 미리보기를 그릴 수 없는 형식에서도 지도용 선택지(팔레트·구간 수·격자 업로드)가 그대로 보여, 사용자가 그릴 수 없는 조작을 시도하게 된다.

## 원한 결과 (proposed outcome)
- 서버가 미리보기를 그릴 수 없다고 판정한 파일에서는 지도용 선택지가 보이지 않는다.
- 아직 판정 전(분석 중)인 파일에서는 지도용 선택지가 그대로 보인다. 숨겼다가 다시 나타나는 화면 흔들림을 만들지 않는다.
- 그릴 수 있다고 판정된 파일의 화면은 지금과 같다.

## 영향 범위
- 사용자 / 화면: 업로드 중 미리보기 패널의 지도용 선택지 노출과 `:672`의 안내 문구.
- 서비스 · 스키마 · 계약: `frontend/src/components/upload/PreviewPanel.tsx`만 바꾼다. 기존 계약 필드를 읽기만 한다. API·DB 변경 없음.
- 계약 파괴 여부: 아니오.

## 제약
- 판정 필드는 서버가 준다. `contracts/seams/fe-core.yaml:4630-4631`의 `renderable`이며 축자 설명은 "미리보기를 그릴 수 있는가 (upload.ready.renderable). 아직 모르면 null. false 여도 등록은 막지 않는다."다. 3상태이고 주입 지점은 `UploadModal.tsx:1491`이다.
- 결함 위치는 `PreviewPanel.tsx`의 세 블록이다. `:450-501`(`<details up-preview-options>`), `:504-519`(`up-nogrid`), `:685-703`(`GridUploadBlock`)이 `props.renderable`을 보지 않는다.
- `const mapCapable = props.renderable !== false;`로 세 블록을 감싸고 `:672` 문구를 고친다. 즉 `null`(분석 중)이면 노출한다. `renderable`이 3상태이고 분석 완료 시점에 값이 바뀌므로, `null`에서 숨기면 판정이 도착할 때 화면이 흔들린다. `false`로 확정된 경우에만 숨긴다.
- 구현 순서는 #97 → #93 → #84+#54 → #92다. `PreviewPanel.tsx`의 `<details>`(450-501)를 #93과 #92가 함께 만지는 것이 이번 4건의 유일한 실질 충돌이므로, 배치를 옮기는 #93을 먼저 넣고 노출 조건을 씌우는 #92를 마지막에 얹는다.
- `renderable === false`여도 등록은 막지 않는다. 계약의 축자 규정이며 이번 변경은 노출만 다룬다.
- 이번 4건은 PR 1건으로 묶고 이슈당 커밋 1개로 간다.

## 설계트리 (grill-me 결과)
- Q1 이슈가 보고한 `보기만 할게요`부터 고치는가 → A 아니다. develop에 이미 없다. 이슈 전반부는 무효이고 후반부 요구만 살린다.
- Q2 형식 판정을 프런트에서 확장자로 할 것인가 → A 아니다. 서버가 `renderable`을 준다. 프런트는 읽기만 한다. (권장안 수용)
- Q3 `null`을 어떻게 다루는가 → A 노출한다. `!== false`로 판정한다. 숨겼다가 다시 나타나면 화면이 흔들린다.
- Q4 이슈 To-be의 'DOCX 다운로드 제공'까지 하는가 → A 아니다. To-be가 "숨기거나 … 제공"의 택일이라 숨김으로 충족된다. 등록 전 다운로드 seam은 미조사여서 계약 변경이 딸려올 수 있다.
- Q5 같은 문구가 남은 S-08 화면은 → A 이번 범위 밖. 별도 이슈로 분리한다.

## 미해결 질문
- 없음.

## 범위 밖 (명시 제외)
- DOCX 다운로드 제공. 이슈 To-be가 "숨기거나 … 제공"의 택일이라 숨김으로 충족되며, 등록 전 다운로드 seam이 미조사여서 계약 변경이 딸려올 수 있다.
- 진입점 0건인 S-08 화면 철거. `frontend/src/routes/UnregisteredPreviewPage.tsx:107-111`에 문제 문구가 잔존하나 이번 범위 밖이며 별도 이슈로 분리한다. 이 intent 작성 시점에 해당 이슈는 아직 만들지 않았다.
- 등록 차단 정책 변경, 계약·API·DB 변경.
- 다른 이슈 구현, 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 확인
- 프론티어 공집합 확인: 2026-09-17.
- Ted 확인 문장(원문 그대로): "권고대로 한다"
- 수용한 권고: 서버 `renderable`을 `!== false`로 읽어 세 블록을 감싸고, DOCX 다운로드 제공과 S-08 철거는 범위 밖으로 둔다.
- Ted 확인 문장(원문 그대로, PR·커밋 단위): "59는 현 순서 유지하고,

A4건을 Pr1건으로 묵을게,"
- Ted 승인 문장(원문 그대로, 이 초안에 대한 승인): "좋아 이렇게 하자"
- 재개봉 금지: 예. 확정된 `null` 노출 판정을 다시 질문하지 않는다.

## 참조
- 이슈: https://github.com/CognileapAI/colab-v2/issues/92
- 계약: `contracts/seams/fe-core.yaml:4630-4631` (`renderable`)
- 코드: `frontend/src/components/upload/PreviewPanel.tsx:450-501`·`:504-519`·`:672`·`:685-703`, `frontend/src/components/upload/UploadModal.tsx:1491`, `frontend/src/routes/UnregisteredPreviewPage.tsx:107-111`
- 시험: `frontend/test/upload.test.tsx:2239`
- 선행 근거 spec: `dev-package/prd/specs/2026-09-16-issue-79-remove-preview-only.md`
- 조사 인계: task `55bdccba41e94627a4d852e048d5642b`, run `51c1a92fdd634b49903d2c7c7f5e9ab1`, 산출물 `qa-a-map.md`
- spec: 미작성. Ted 승인 뒤 합성한다.
- 결정: 신규 legacy 결정번호 발급 없음.
