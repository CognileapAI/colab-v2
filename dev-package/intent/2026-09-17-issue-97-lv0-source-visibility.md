# Intent: Lv.0에 상위 데이터를 연결하면 원천·연구실 밖 출처 블록을 숨긴다
메타 — 발의자: joddanddan-commits · 방향 결정: Ted · 작성 2026-09-17 · 승인 2026-09-17(초안 4건 제시 후 Ted 명시 승인)

## 문제
- Lv.0 데이터에 상위 데이터를 연결해도 등록 화면의 `원천·연구실 밖 출처` 입력 블록이 계속 보인다. 상위가 이미 있으면 출처는 상위에서 따라오므로, 사용자는 불필요한 출처 URL·내려받은 날짜를 다시 적어야 하는 것으로 읽는다.
- 원인은 `frontend/src/components/upload/RegisterArea.tsx:986`의 `const sourceVisible = lv0 || props.ctx.parents.length === 0;`다. `lv0`가 앞항이므로 Lv.0이면 부모 유무와 무관하게 항상 참이 되고, 뒤의 부모 0건 조건이 판정에 이르지 못한다.

## 원한 결과 (proposed outcome)
- Lv.0 데이터에 상위 데이터를 1건 이상 연결하면 원천·연구실 밖 출처 블록이 화면에서 사라진다.
- 상위 데이터가 0건인 Lv.0에서는 기존대로 원천 블록이 보이고 출처 URL·내려받은 날짜를 요구한다.
- 블록이 숨은 상태에서도 등록이 정상적으로 완료된다. 보이지 않는 입력칸 때문에 등록이 막히지 않는다.

## 영향 범위
- 사용자 / 화면: 업로드 등록 화면의 원천·연구실 밖 출처 블록 노출 조건과 그 블록에 걸린 등록 전 형상 검증.
- 서비스 · 스키마 · 계약: 프런트 `RegisterArea.tsx`·`UploadModal.tsx`의 노출 조건과 검증 분기만 바꾼다. API·DB·백엔드 변경 없음.
- 계약 파괴 여부: 아니오.

## 제약
- 노출 조건은 부모 0건 단일 조건으로 통일한다. `RegisterArea.tsx:986`은 `props.ctx.parents.length === 0`, `UploadModal.tsx:783`은 `lineageCards.length === 0`으로 맞춘다. Lv0의 허용 부모는 Lv0뿐이므로(`LineageStep.tsx:71`) 이 단일 조건은 이슈가 말한 'Lv.0에 Lv.0 상위 연결' 조건과 동치다.
- 동반 필수: `UploadModal.tsx:1153`의 `if (level === LV0 && (!sourceUrl.trim() || !sourceDownloadedOn.trim()))`와 1161행 형상 검증을 `sourceVisible &&`로 좁힌다. 이 수정을 빼면 블록이 숨은 뒤에도 검증이 걸리고, 초점 대상 `#reg-source-url`이 화면에 없어 등록이 영구히 막힌다.
- 이미 업로드된 파일이나 입력된 사용자 데이터를 삭제하지 않는다.
- 이번 4건은 PR 1건으로 묶고 이슈당 커밋 1개로 간다. 구현 순서는 #97 → #93 → #84+#54 → #92이며 이 항목이 첫 커밋이다.

## 설계트리 (grill-me 결과)
- Q1 조건을 `lv0 && parents.length === 0`으로 고칠 것인가, 부모 0건 단일 조건으로 바꿀 것인가 → A 단일 조건. Lv0의 허용 부모가 Lv0뿐이라 두 식이 동치이고, 조건이 하나면 `UploadModal` 쪽과 형태가 같아진다. (권장안 수용)
- Q2 `RegisterArea`만 고치면 되는가 → A 아니다. `UploadModal.tsx:783`이 같은 판정을 따로 들고 있어 두 곳을 함께 맞춘다.
- Q3 숨김만으로 끝나는가 → A 아니다. 1153·1161행 검증이 `sourceVisible`을 보지 않으면 등록이 막힌다. 숨김과 검증 축소는 한 커밋에 함께 간다.
- Q4 계약·백엔드가 딸려오는가 → A 아니다. 서버로 보내는 필드 구성은 이미 조건부이고 노출 판정은 프런트 지역 상태다.

## 미해결 질문
- 없음.

## 범위 밖 (명시 제외)
- Lv.1 이상 계층의 출처 정책 변경, 부모에서 출처를 자동 복사하는 기능, 계약·API·DB 변경.
- 다른 이슈 구현, 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 확인
- 프론티어 공집합 확인: 2026-09-17.
- Ted 확인 문장(원문 그대로): "권고대로 한다"
- 수용한 권고: 부모 0건 단일 조건으로 통일하고, 1153·1161행 형상 검증을 `sourceVisible &&`로 함께 좁힌다.
- Ted 확인 문장(원문 그대로, PR·커밋 단위): "59는 현 순서 유지하고,

A4건을 Pr1건으로 묵을게,"
- Ted 승인 문장(원문 그대로, 이 초안에 대한 승인): "좋아 이렇게 하자"
- 재개봉 금지: 예. 확정된 숨김 조건을 다시 질문하지 않는다.

## 참조
- 이슈: https://github.com/CognileapAI/colab-v2/issues/97
- 코드: `frontend/src/components/upload/RegisterArea.tsx:986`, `frontend/src/components/upload/UploadModal.tsx:783`, `frontend/src/components/upload/UploadModal.tsx:1153`·`:1161`, `frontend/src/components/upload/LineageStep.tsx:71`
- 시험: `frontend/test/lv0-source-20260907.test.tsx`, `frontend/test/upload-form-rev2-20260914.test.tsx:356`·`:372-390`
- 조사 인계: task `55bdccba41e94627a4d852e048d5642b`, run `51c1a92fdd634b49903d2c7c7f5e9ab1`, 산출물 `qa-a-map.md`
- spec: 미작성. Ted 승인 뒤 합성한다.
- 결정: 신규 legacy 결정번호 발급 없음.
