# Intent: 미리보기를 지도식 뷰포트로 — 조작 도구는 화면에 고정되고 그림만 움직인다
메타 — 발의자: sungwooHa · 방향 결정: Ted · 작성 2026-09-18 · 승인 2026-09-18(초안 제시 후 판단 셋 중 터치 제외를 질의·확정, Ted 명시 승인)

## 문제
- 데이터셋 상세의 미리보기에서 확대·축소·기본 배율·스크린샷 버튼, 커서 위경도 표시, 값 조회 패널, 범례가 그림과 **같이 움직인다.** 그림을 옮기거나 틀 안을 스크롤하면 도구가 화면 밖으로 밀려나고, 4:3 틀 오른쪽에 스크롤바가 선다(이슈 첨부 1). 범례는 오른쪽 별도 열이라 그림과 떨어져 있다(첨부 2).
- 기본 배율에서 그림이 틀 한가운데에 서지 않는다. 세로가 긴 히트맵이 틀 왼쪽 위 부근에 놓이고 아래는 빈 자리다(첨부 1).
- 원인 둘. ⑴ 도구가 뷰포트(`.pv-viewport`)의 **형제 블록**으로 문서 흐름에 쌓여 있고(`frontend/src/components/preview/PreviewPanels.tsx` `PreviewMap` — `pv-hud`·`PreviewZoomControls`·`actions`·`valuePanel` 이 `.pv-mapcol` 안에서 뷰포트 아래에 순서대로, `dl.pv-legend` 는 `.pv-map` 의 오른쪽 열), 이 전부가 4:3 틀 안쪽 `.pv-frame-in { overflow: auto }`(`preview.css`) 스크롤 영역에 실린다. 뷰포트에 `position: relative` 가 없어 겹쳐 놓을 자리도 없다. ⑵ 한가운데 놓기 `centeredPanFor`(`useZoomPan.ts`)가 **층 묶음 크기 = 뷰포트 크기**를 전제로 `size × (1 − scale) / 2` 를 계산한다. 층 묶음 높이는 그림의 가로세로비를 따르므로 뷰포트와 비율이 다르면 세로 중심이 어긋난다. 같은 전제가 `clampView` 의 이동 범위에도 있어, 배율 1 이상에서 세로가 긴 그림의 아래쪽으로 옮겨 갈 수 없다.
- 이동·배율 자체는 이미 `transform: translate() scale()` 한 층에 걸려 있다(이슈 본문의 「스크롤로 구현했다」는 절반만 맞다). 휠 확대는 커서가 아니라 **뷰포트 중심**을 고정점으로 삼는다 — `zoomTo(target, anchorX, anchorY)` 에 고정점 인자가 있으나 `onWheel` 이 넘기지 않는다.

## 원한 결과 (proposed outcome)
- 미리보기 틀 안에 **스크롤바가 서지 않는다.** 뷰포트가 4:3 틀의 안쪽 전부를 차지하고, 그림 이동은 transform 으로만 한다.
- 확대·축소·기본 배율·스크린샷 버튼, 커서 위경도 표시, 값 조회 패널, 범례는 **뷰포트 위에 겹쳐 고정**된다. 그림을 아무리 옮기고 키워도 이 도구들의 화면 위치와 크기는 변하지 않는다.
- 기본 배율(첫 표시·「기본 배율로」)에서 **그림의 가로·세로 중심이 뷰포트의 가로·세로 중심과 일치**한다. 그림의 가로세로비가 뷰포트와 달라도 그렇다.
- 배율 1 이상에서는 그림의 어느 가장자리든 드래그로 볼 수 있다. 이동 범위는 그림의 실제 크기에서 계산한다.
- 휠 확대·축소는 **커서 아래 지점을 고정점**으로 삼는다. 버튼 확대·축소는 뷰포트 중심 고정점을 유지한다.
- 도구 층의 빈 자리에서도 드래그·휠·클릭이 그림에 그대로 닿는다. 값 조회 클릭과 커서 위경도 표시는 종전대로 동작한다.
- 업로드 인라인 미리보기와 확장보기(`frontend/src/components/upload/PreviewPanel.tsx`)도 같은 구조를 쓴다 — 세 화면이 이미 `PreviewZoomControls` 하나를 공유하므로 배치 규칙도 한 곳에 둔다.
  ⟨advisor ① 추가 2026-09-18⟩ 등록 전 미리보기(`frontend/src/routes/UnregisteredPreviewPage.tsx` · `PreviewMap` 을 zoom 없이 씀)도 같은 컴포넌트라 범례·HUD 가 도구 층으로 옮겨 간다. 네 번째 화면으로 범위에 포함한다(확대 줄은 없음).
- 스크린샷의 「지금 장면」(`visibleFraction`)은 화면에 실제 그려진 자리(중앙 정렬 후 좌표)와 일치한다.

## 영향 범위
- 사용자 / 화면: 데이터셋 상세 미리보기 · 업로드 인라인 미리보기 · 업로드 확장보기. 도구의 자리(뷰포트 위 겹침)와 첫 표시 위치(중앙)가 바뀐다.
- 서비스 · 스키마 · 계약: 프런트만. `PreviewPanels.tsx`·`PreviewPanel.tsx`·`useZoomPan.ts`·`preview.css` 와 시험. 렌더 요청·API·DB·서버 스크린샷 계약 변경 없음.
- 계약 파괴 여부: 아니오.

## 제약
- 3층 구조를 지킨다 — 뷰포트(고정 크기 · `overflow: hidden` · `position: relative`) / 층 묶음(`.pv-layers` · transform 은 여기 하나) / 도구 층(뷰포트의 **직계 자식이자 층 묶음의 형제** · `position: absolute` · 컨테이너 `pointer-events: none`, 버튼·패널만 `auto`). 도구를 층 묶음 안에 넣지 않는다.
- 정본 §8 확대 조건은 그대로다 — 값·팔레트·범례를 건드리지 않고(⑵), 렌더를 다시 걸지 않으며(⑶), 한계 배율은 데이터 해상도에서 온다(⑷). **기본 배율 값은 축척 사다리(`scaleLadder.baseScaleFor`)가 정한 것을 유지한다.** 이번에 바꾸는 것은 그 배율에서의 **자리**(중앙)이지 배율 자체가 아니다.
- 종전 판정 ⑦ ⓐ(R-BUGFIX-260912 · 「고정·절대 배치를 신설하지 않는다」)를 **이 intent 로 명시 해제**한다. `preview.css` `.pv-zoom` 주석과 `PreviewSlot.tsx` 머리말의 해당 문구를 이 intent 를 가리키도록 개정한다(지우지 않고 개정 표시).
- 휠 리스너는 계속 네이티브 `{ passive: false }` 로 건다(검수 #24). React `onWheel` 로 되돌리지 않는다.
- 도구 층의 글자·패널은 그림 위에 얹히므로 **불투명한 표면 배경**을 갖는다. 글자 13px 이상 · 대비 4.5:1 이상은 `frontend-visual` 이 실화면에서 잰다. 토큰은 `tokens.css` 것만 쓴다.
- 문면을 새로 만들지 않는다 — 버튼 이름·HUD·값 조회·범례 문구는 종전 그대로.
- 기존 시험 단언과 양립한다 — 범례는 `preview-layers` 자손이 아니다 · transform 은 `preview-layers` 하나에만 · `.pv-zoom` 은 `white-space: nowrap`·`flex: none` 유지. CSS 원문을 읽는 시험(`frontend/test/preview-layout-20260912.test.tsx`)의 단언 문자열은 그대로 두거나, 바뀐 규칙에 맞춰 함께 고친다(단언 삭제로 통과시키지 않는다).
- 이 이슈 1건 = intent 1건 = 커밋 1개. PR 1건으로 게시하며 게시는 사용자가 한다.

## 설계트리
- Q1 스크롤을 없애는 자리는 어디인가 → A 틀 안쪽 스크롤 영역에 실리는 것을 뷰포트 하나로 줄인다. 도구가 뷰포트 안 겹침 층으로 들어가면 넘칠 내용이 없어 스크롤바가 서지 않는다. `overflow: auto` 를 `hidden` 으로 바꿔 덮지 않는다 — 내용이 넘치면 잘리는 것이지 해결이 아니다.
- Q2 기본 배율을 「뷰포트에 딱 맞는 값」(이슈 본문 제안)으로 바꿀 것인가 → A 아니다. 기본 배율은 축척 사다리 결정(〈232〉·〈238〉)이 정한 값이고, Ted 요청은 「중간 위치를 맞춰 달라」다. 자리만 고친다. 배율 정책 변경은 별건.
- Q3 중앙 정렬은 어디서 계산하나 → A 층 묶음의 실제 크기(뷰포트 폭 × 그림 가로세로비)로 두 축 모두 계산한다. 뷰포트 크기 하나로 두 축을 계산하던 전제를 버린다. 이동 범위(`clampView`)도 같은 크기를 쓴다.
- Q4 커서 고정점 확대는 이번 범위인가 → A 예. 이슈 스펙 항목이고 훅에 인자가 이미 있어 `onWheel` 이 커서 좌표를 넘기면 된다.
- Q5 터치(1지점 드래그·핀치)는 이번 범위인가 → A 아니다. 현재 터치 처리가 전무하고 이슈의 주 대상은 마우스 화면이다. 후속 이슈로 분리한다.
- Q6 도구의 자리 → A 우하단 = 확대·축소·기본 배율·스크린샷, 우상단 = 범례(변수 포함), 좌하단 = 커서 위경도 표시와 값 조회 패널. 이슈 본문의 배치를 따르고 값 조회·HUD 는 남은 모서리에 둔다. 세부는 spec 에서 화면별로 확정.
- Q7 세 화면 중 어디까지 → A 셋 다. 배치 규칙을 공용 부품 한 곳에 두어 호출부 세 곳에 같은 JSX 순서를 복제하지 않는다(`PreviewSlot` 의 존치 규칙과 같은 원칙).

## 미해결 질문
- 없음.

## 범위 밖 (명시 제외)
- 기본 배율 값·축척 사다리·한계 배율 정책 변경. 터치·핀치 조작. canvas/WebGL 재렌더 도입. Leaflet 등 라이브러리 도입.
- 서버 스크린샷 계약·렌더 요청·범례 값 형식 변경. 다른 이슈. 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 확인
- Ted 요청 문장(원문 그대로): "스크롤 없이 지도처럼 보이고, 이미지의 가로 세로 중간위치랑 화면의 중간위치를 맞췄으면 하는데"
- Ted 지시 문장(원문 그대로): "intent 곡"
- Ted 질의(원문 그대로): "터치 핀치 조작은 범위 밖으로 왜뺌? 이건 뭔데" → 설명 후
- Ted 승인 문장(원문 그대로): "좋아 후속 분리 할게"
- 수용한 판단: ⑴ 기본 배율 값 유지·자리만 중앙 ⑵ 터치·핀치 후속 분리 ⑶ 도구 자리 우하단 버튼·우상단 범례·좌하단 HUD·값 조회(세부는 spec)
- 재개봉 금지: 예. 기본 배율 값을 다시 묻지 않는다(Q2).

## 참조
- 이슈: https://github.com/CognileapAI/colab-v2/issues/120
- 코드: `frontend/src/components/preview/PreviewPanels.tsx`(`PreviewMap`), `frontend/src/components/preview/useZoomPan.ts`(`centeredPanFor`·`clampView`·`zoomTo`·`onWheel`·`visibleFraction`), `frontend/src/components/preview/preview.css`(`.pv-viewport`·`.pv-zoom`·`.pv-frame-in`), `frontend/src/components/preview/PreviewSlot.tsx`, `frontend/src/components/preview/PreviewZoomControls.tsx`, `frontend/src/components/upload/PreviewPanel.tsx`(인라인·확장보기 뷰포트 두 자리)
- 시험: `frontend/test/dataset-preview-zoom.test.tsx`, `frontend/test/preview-layout-20260912.test.tsx`, `frontend/test/dataset-preview-zoom-latency.test.tsx`, `frontend/test/dataset-preview-screenshot.test.tsx`, `frontend/test/dataset-value-lookup.test.tsx`
- 종전 판정: `dev-package/prd/specs/2026-09-12-issue-preview-controls-v2.md` 판정 ⑦ ⓐ(이 intent 로 해제)
- spec: 미작성. Ted 승인 뒤 합성한다.
- 결정: 신규 legacy 결정번호 발급 없음.
