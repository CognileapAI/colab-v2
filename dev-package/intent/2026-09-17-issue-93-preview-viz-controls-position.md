# Intent: 업로드 중 미리보기에서 팔레트·구간 수를 접힌 메뉴 밖으로 옮긴다
메타 — 발의자: joddanddan-commits · 방향 결정: Ted · 작성 2026-09-17 · 승인 2026-09-17(초안 4건 제시 후 Ted 명시 승인)

## 문제
- 업로드 중 미리보기 화면에서 팔레트와 구간 수가 접힌 메뉴 안에 들어 있어, 사용자가 메뉴를 펼치기 전에는 지도 표현을 바꾸는 수단이 있는지조차 알 수 없다.
- 원인은 조건부 렌더가 아니라 정적 배치다. `frontend/src/components/upload/PreviewPanel.tsx:450-501`의 `<details>`가 기본 닫힘이고, 팔레트·구간 수·그리기가 그 안(`:456-499`의 `<div className="vizsetup">`)에 있다.

## 원한 결과 (proposed outcome)
- 미리보기 화면을 열면 팔레트와 구간 수가 접기 조작 없이 바로 보인다.
- 두 조작은 파일·변수 선택 줄 바로 아래에 놓여 '무엇을 그릴지 → 어떻게 그릴지' 순서로 읽힌다.
- 이동 뒤에도 팔레트·구간 수·그리기의 동작과 미리보기 갱신이 그대로다.

## 영향 범위
- 사용자 / 화면: 업로드 중 미리보기 패널의 조작부 배치.
- 서비스 · 스키마 · 계약: `PreviewPanel.tsx` 한 파일의 JSX 배치와 관련 스타일. 상태 정의·API·DB 변경 없음.
- 계약 파괴 여부: 아니오.

## 제약
- `PreviewPanel.tsx:456-499`의 `<div className="vizsetup">`(팔레트 458 / 구간 수 473 / 그리기 487)를 `<details>`(450-501) 밖으로 꺼내, `:530-542` `PreviewSlot`의 `controls` 안 `<PreviewPickRow idPrefix="up">`('파일'/'변수') 아래에 놓는다.
- 상태가 전부 PreviewPanel 지역 상태이므로 배선 변경 없이 이동만으로 동작이 유지된다. 이동을 계기로 상태를 상위로 끌어올리지 않는다.
- 구현 순서는 #97 → #93 → #84+#54 → #92다. `PreviewPanel.tsx`의 `<details>`(450-501)를 #93과 #92가 함께 만지는 것이 이번 4건의 유일한 실질 충돌이므로, 배치를 바꾸는 #93을 먼저 넣고 노출 조건을 씌우는 #92를 뒤에 얹는다.
- 이번 4건은 PR 1건으로 묶고 이슈당 커밋 1개로 간다.

## 설계트리 (grill-me 결과)
- Q1 안 보이는 원인이 조건부 렌더인가 → A 아니다. 조건은 걸려 있지 않고 `<details>`가 기본 닫힘이라는 정적 배치가 원인이다.
- Q2 `<details>`를 기본 열림으로 바꾸면 되는가 → A 아니다. 그러면 나머지 옵션까지 함께 펼쳐진다. 두 조작만 밖으로 옮긴다. (권장안 수용)
- Q3 옮길 자리 → A `PreviewSlot`의 `controls` 안, 파일·변수 선택 줄 바로 아래.
- Q4 상태 배선을 바꿔야 하는가 → A 아니다. 모두 PreviewPanel 지역 상태다.

## 미해결 질문
- 없음.

## 범위 밖 (명시 제외)
- `<details>` 안 나머지 옵션의 재배치, 미리보기 렌더 로직·색상 알고리즘 변경, 등록 화면 밖 미리보기 화면의 배치 변경.
- 다른 이슈 구현, 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 확인
- 프론티어 공집합 확인: 2026-09-17.
- Ted 확인 문장(원문 그대로): "권고대로 한다"
- 수용한 권고: `<details>`를 기본 열림으로 바꾸지 않고, 팔레트·구간 수·그리기만 `PreviewSlot`의 `controls` 안 파일·변수 선택 줄 아래로 옮긴다.
- Ted 확인 문장(원문 그대로, PR·커밋 단위): "59는 현 순서 유지하고,

A4건을 Pr1건으로 묵을게,"
- Ted 승인 문장(원문 그대로, 이 초안에 대한 승인): "좋아 이렇게 하자"
- 재개봉 금지: 예. 확정된 이동 위치를 다시 질문하지 않는다.

## 참조
- 이슈: https://github.com/CognileapAI/colab-v2/issues/93
- 코드: `frontend/src/components/upload/PreviewPanel.tsx:450-501`(`<details>`), `:456-499`(`vizsetup`, 팔레트 458 / 구간 수 473 / 그리기 487), `:530-542`(`PreviewSlot` `controls`, `PreviewPickRow idPrefix="up"`)
- 시험: `frontend/test/preview-layout-20260912.test.tsx`, `frontend/test/s2-preview-style.test.tsx`
- 조사 인계: task `55bdccba41e94627a4d852e048d5642b`, run `51c1a92fdd634b49903d2c7c7f5e9ab1`, 산출물 `qa-a-map.md`
- spec: 미작성. Ted 승인 뒤 합성한다.
- 결정: 신규 legacy 결정번호 발급 없음.
