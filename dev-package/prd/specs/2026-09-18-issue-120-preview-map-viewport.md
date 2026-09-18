# Spec: 미리보기를 지도식 뷰포트로 — 도구 층 고정·그림 중앙 정렬·커서 고정점 확대 (#120)
출처 intent: `dev-package/intent/2026-09-18-issue-120-preview-map-viewport.md` (승인 2026-09-18 · `## 확인` 절이 구속력이다)

## 문제 진술
- 상세 미리보기 `PreviewMap`(`frontend/src/components/preview/PreviewPanels.tsx`)에서 확대 줄·스크린샷·값 조회·커서 HUD 가 `.pv-viewport` 의 **뒤 형제**로 `.pv-mapcol` 에 쌓이고, 범례 `dl.pv-legend` 는 `.pv-map` 의 오른쪽 열이다. 이 전부가 4:3 틀 안쪽 `.pv-frame-in { overflow: auto }`(`preview.css`) 에 실려 그림과 함께 스크롤된다. 뷰포트에 `position: relative` 가 없다.
- 한가운데 놓기 `centeredPanFor`(`useZoomPan.ts`) 와 이동 범위 `clampView` 가 **층 묶음 크기 = 뷰포트 크기**를 전제한다. 층 묶음 높이는 그림의 가로세로비를 따르므로(`.pv-layers .pv-tile { width: 100% }` · 높이 auto) 비율이 다르면 세로 중심이 어긋나고, 배율 1 이상에서 세로가 긴 그림의 아래를 볼 수 없다.
- 역변환(`fractionOf` · `pvLonOf`·`pvLatOf`·`pointFromViewport`)과 스크린샷 장면(`visibleFraction`)도 같은 전제로 뷰포트 상자를 쓴다. 배경 층 `.pv-basemap` 은 `inset: 0`·`preserveAspectRatio="none"` 으로 **층 묶음 상자**에 붙는다. 두 상자가 다를 때 값 조회 세로 좌표가 어긋난다(종전부터).
- 휠 확대는 `onWheel` 이 `zoomIn()/zoomOut()` 만 부르고 `zoomTo(target, anchorX, anchorY)` 의 고정점 인자를 넘기지 않아 뷰포트 중심 기준이다.
- 업로드 인라인(`frontend/src/components/upload/PreviewPanel.tsx` · `up-preview-viewport`)과 확장보기(`pv-expand-viewport`)도 `PreviewZoomControls` 를 뷰포트 뒤 형제로 둔다.

## 해법 개요
- 뷰포트 안에 **도구 층**(`.pv-overlay`)을 층 묶음의 형제로 세우고, 도구 전부를 그 안 네 모서리 자리로 옮긴다. 뷰포트 밖에는 아무 것도 남지 않아 틀 안 스크롤이 사라진다.
- 훅이 **내용 상자**(층 묶음의 실제 배치 크기)를 재어, 중앙 정렬·이동 범위·역변환·스크린샷 장면이 모두 그 상자를 쓴다. 뷰포트 상자 하나로 두 축을 계산하던 전제를 버린다.
- 휠은 커서 좌표를 고정점으로 넘긴다. 버튼은 종전대로 뷰포트 중심.
- 세 화면이 같은 도구 층 부품을 쓴다. 배치 규칙은 부품 한 곳에만 산다.

## 사용자 스토리
1. 데이터셋 상세 사용자로서 그림을 끌고 키워도 확대·축소·스크린샷·값 조회·범례가 늘 같은 자리에 있기를 원한다, 도구를 찾아 스크롤하지 않기 위해.
2. 데이터셋 상세 사용자로서 미리보기가 처음 열릴 때와 「기본 배율로」를 눌렀을 때 그림이 틀 한가운데에 있기를 원한다, 지도처럼 읽기 위해.
3. 데이터셋 상세 사용자로서 휠을 굴리면 커서 아래 지점이 그 자리에 머문 채 확대되기를 원한다, 보려던 곳을 놓치지 않기 위해.
4. 업로드 사용자로서 인라인 미리보기와 확장보기가 상세와 같은 조작을 갖기를 원한다, 화면마다 다른 조작을 배우지 않기 위해.
5. 값 조회 사용자로서 누른 자리의 값이 실제로 그 자리의 값이기를 원한다, 세로가 긴 그림에서도.

## 구현 결정
- 모듈 · 인터페이스 — **도구 층 부품 신설** `frontend/src/components/preview/PreviewOverlay.tsx`: `PreviewOverlay({ topRight?, bottomRight?, bottomLeft?, testId? })` 가 `div.pv-overlay[data-testid]` 하나를 내고 자리별 `div.pv-overlay-tr / -br / -bl` 을 자식으로 둔다. **뷰포트의 직계 자식이자 `.pv-layers` 의 뒤 형제**로만 놓는다. 문면·버튼·패널 컴포넌트는 손대지 않고 자리만 옮긴다.
  - 상세 `PreviewMap`: 우상단 = `dl.pv-legend`(변수 행 포함) · 우하단 = `PreviewZoomControls` + `props.actions`(스크린샷) · 좌하단 = `p.pv-hud` + `props.valuePanel`. `.pv-mapcol` 에는 뷰포트만 남고 `.pv-map` 의 오른쪽 열이 없어진다.
  - 업로드 인라인: 우하단 = `PreviewZoomControls`(testId `up-preview-zoom` 유지). 확장보기: 우하단 = `PreviewZoomControls`(`pv-expand-zoom` 유지). 두 화면의 배지 `.pv-badges` 는 뷰포트 밖 현 자리 유지(범위 밖).
- 이벤트 경계 — 도구 층이 뷰포트 안으로 들어가므로 버튼 클릭이 뷰포트의 `onClick`(값 조회)·`onMouseDown`(드래그 시작)·`onDoubleClick`(데이터 맞춤)으로 **버블링된다.** `PreviewOverlay` 루트가 `onClick`·`onMouseDown`·`onDoubleClick` 에서 `stopPropagation()` 한다. 휠은 훅이 뷰포트 노드에 **네이티브** 리스너로 걸어 React 의 `stopPropagation` 이 닿지 않으므로, 훅의 휠 핸들러가 `event.target` 이 `.pv-overlay` 안이면 무시한다(그 위에서는 페이지 스크롤이 자연스럽다). `pointer-events`: `.pv-overlay`·모서리 컨테이너 = `none`, 그 안 도구 요소 = `auto`.
- 훅 `useZoomPan` — **내용 상자** `contentBox()` 신설: `layersRef` 로 받은 `.pv-layers` 의 `offsetWidth/offsetHeight`(transform 미적용 배치 크기). **두 치수 중 하나라도 0 이면**(jsdom·미측정·타일 갈래 — 타일은 `offsetWidth` 가 뷰포트, `offsetHeight` 가 0 이다) **뷰포트 상자로 대체** — 타일 갈래는 설계상 내용 = 뷰포트 상자(`baseLevel` 이 그렇게 세운다)이고, 이미지 갈래에서 jsdom 은 0 이라 기존 시험이 종전과 같은 수를 본다. `ZoomPan` 에 `layersRef`·`contentSize()` 를 더한다. 세 화면의 `.pv-layers` 에 `ref={zoom.layersRef}` 를 단다.
- 중앙 정렬·이동 범위 — **시작 자리와 이동 범위를 가른다.** ⓐ 첫 표시·「기본 배율로」·더블클릭 맞춤의 이동값은 **두 축 모두** `(viewport − content × scale) / 2` 다. 내용이 뷰포트보다 커도 그렇다 — 축척 사다리는 폭 기준이라 세로가 긴 그림은 기본 배율에서 세로가 넘치고, 종전 `reset → (0,0)` 은 그 그림을 **위 정렬**로 둔다(이슈 첨부 1 의 바로 그 경우). ⓑ 드래그·확대의 결과만 가둔다: `content × scale ≤ viewport` 인 축은 중앙에 고정(옮길 곳이 없다), 큰 축은 `[viewport − content × scale, 0]`. 중앙값은 그 범위 안에 있으므로 ⓐ 와 ⓑ 가 충돌하지 않는다. 구현은 이동값을 **중앙 기준 편차**로 저장해 크기를 못 잰 순간에도 0 = 중앙이 되게 한다(종전 「출력 시 중앙」 패턴의 일반화). `centeredPanFor(view, viewportSize, contentSize)` 로 서명을 넓힌 **순수 export** 를 유지하고 `clampView` 가 같은 함수를 쓴다.
- 역변환·스크린샷 — `fractionOf` 의 `size` 인자에 뷰포트가 아니라 **내용 상자** 치수를 넘긴다. `PreviewMap` 의 `onClick`·`onMouseMove` 는 **종전대로 `getBoundingClientRect()` 로 뷰포트 상자를 재고 핸들러 안에서 `centeredPanFor` 를 부른다** — 지우지 않는다. 기존 시험(`dataset-value-lookup.test.tsx` `sizeViewport` · `prd39-rev2-build-20260906.test.tsx`)이 `getBoundingClientRect` 만 스텁하고 훅의 `box()`(`clientWidth`) 는 jsdom 에서 0 이라, 훅 값에 기대면 그 시험이 깨진다. 내용 상자는 `zoom.contentSize()` 가 주되 없으면(두 치수 중 하나라도 0) rect 로 대체한다. 훅 안 `zoomTo`·`clampView` 는 `box()` 를 쓰고 rect 는 휠의 좌표 원점(left/top)에만 쓴다. `visibleFraction` 도 내용 상자로 센다. 타일 갈래는 내용 = 뷰포트라 수가 같다.
- 커서 고정점 — `onWheel(e: { deltaY, clientX?, clientY?, preventDefault? })`: 뷰포트 `getBoundingClientRect()` 로 뷰포트 좌표를 만들어 `zoomTo(target, ax, ay)` 에 넘긴다. 좌표가 없으면(시험의 합성 이벤트) 종전대로 중심. `zoomIn/zoomOut` 버튼은 인자 없이 중심 유지. 한계·`blocked` 판정은 `zoomIn/zoomOut` 안의 것을 그대로 거친다 — 휠 확대도 `atLimit` 를 지어내지 않는다.
- 스타일(`preview.css`) — `.pv-viewport { position: relative }` 추가. `.pv-overlay { position: absolute; inset: 0; pointer-events: none }`, 모서리 컨테이너 `position: absolute` + `top/bottom/right/left: 12px` + `display: flex; flex-direction: column; gap: 8px; pointer-events: none`. 도구 요소(`.pv-overlay .pv-zoom`·`.pv-shot`·`.pv-value`·`.pv-legend`·`.pv-hud`) = `pointer-events: auto; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-sm); padding: 6px 8px`. 그림자 0. `.pv-hud` 의 `margin: 6px 0 0` 은 컨테이너 gap 이 대신하므로 도구 층 안에서는 0. 범례는 `max-height: calc(100% - 24px); overflow: auto`(길면 범례 패널 안에서만 스크롤). `.pv-zoom` 의 `white-space: nowrap; flex: none` 유지. `.pv-map { flex-wrap: wrap }`(`preview.css` `.pv-map {`) 은 **정리가 아니라 결함의 절반이다** — 여러 줄 flex 는 줄 높이를 `.pv-mapcol` 의 내용(= 그림 높이)으로 재서 세로 긴 그림이 도구를 옮긴 뒤에도 `.pv-frame-in` 을 넘친다. `flex-wrap: nowrap` 으로 바꾸고 `gap: 20px` 을 지운다. `.pv-map {` 원문에 `flex-wrap: nowrap` 이 있음을 CSS 원문 시험으로 잠근다(시험이 원문을 읽는 규칙은 `.pv-frame .pv-viewport`·`.pv-zoom`·`.pv-layers .pv-tile`·`.pv-frame .mapcanvas`·`.pv-frame .pv-map`·`.pv-frame .pv-mapcol` 이며 이들의 단언 문자열은 그대로 남긴다).
- 확장보기 뷰포트 상자(`frontend/src/components/upload/upload.css`) — `.pvx-b { overflow: auto; align-items: center }` 안에서 `.pv-viewport` 에 높이 규칙이 없고 `.pvx-img { max-height: 100% }` 는 auto 높이 `.pv-layers` 아래서 무효라 세로 긴 그림이 `.pvx-b` 를 스크롤시킨다. `.pvx-b .pv-viewport { align-self: stretch; flex: 1 1 auto; min-height: 0; width: 100% }` 를 추가하고 CSS 원문 시험으로 잠근다.
- 네 번째 소비처 — `frontend/src/routes/UnregisteredPreviewPage.tsx` 의 `<PreviewMap result={…} />`(등록 전 미리보기 S-08 · `zoom` 없음)도 같은 `PreviewMap` 이라 범례·HUD 가 도구 층으로 옮겨 간다. **범위 안으로 선언한다** — 확대 줄은 없고(zoom 없음) 범례·HUD 만 도구 층에 선다. 시험 ⑴ 네 번째 케이스와 `COLAB_VISUAL_URLS` 에 이 페이지를 넣는다.
- 종전 판정 개정 — `preview.css` `.pv-zoom` 주석의 「배치 소유는 옮기지 않는다 — 고정·절대 배치를 신설하지 않는다(판정 ⑦ ⓐ)」와 `PreviewSlot.tsx` 머리말의 존치 규칙 문구에 **⟨개정 2026-09-18 · #120 intent⟩** 표시를 붙여 도구 층이 뷰포트 안 절대 배치로 옮겨 갔음을 적는다. 원문은 지우지 않는다.
- 스키마 · 마이그레이션: 없음.
- API 계약: 비파괴. 스크린샷 요청 `viewport.width/height` 는 종전대로 뷰포트 크기, `bounds` 는 `visibleFraction` 이 내용 상자로 센 값.
- 커밋·PR 단위: 이슈 1건 = 커밋 1개 = PR 1건. 브랜치 `claude/issue-120-preview-map-viewport`, base `develop`.

## 시험 결정
- 외부 행위 기준 검증 항목: ⑴ 상세·업로드 인라인·확장보기·등록 전 미리보기 네 화면에서 `pv-overlay` 가 뷰포트의 직계 자식이고 `preview-layers` 의 형제이며, 확대 줄·스크린샷·값 조회·범례·HUD 가 그 자손이고 `preview-layers` 자손이 아님 ⑵ `.pv-mapcol` 의 자식이 뷰포트 하나뿐이고 `.pv-map` 안에 도구 층 밖 `.pv-legend` 가 없음 ⑶ 내용 상자가 뷰포트보다 작은 축은 중앙, 큰 축은 **시작·리셋 시 중앙**이고 드래그로 가장자리까지 도달(순수 함수 · `content × scale > viewport` 케이스 필수) ⑷ 휠 고정점: 확대 전후 `(anchor − pan) / scale` 이 같음(순수 함수 + 훅) ⑸ 역변환이 내용 상자를 씀: 세로 800·가로 1000 뷰포트에 내용 500×800 을 두고 중앙 클릭 → 위도 중앙 ⑹ 도구 층 위 클릭이 값 조회를 일으키지 않음(`onPickPoint` 호출 0) · 도구 층 위 mousedown 이 드래그를 시작하지 않음 ⑺ CSS 원문: `.pv-viewport {` 에 `position: relative`, `.pv-overlay {` 에 `position: absolute`·`pointer-events: none`, 도구 요소 규칙에 `pointer-events: auto`, `.pv-map {` 에 `flex-wrap: nowrap`, `.pvx-b .pv-viewport {` 에 `flex: 1 1 auto`·`min-height: 0` ⑻ 기존 단언 유지 — 범례 ∉ layers · transform 은 layers 에만 · 100 ms 반응 · 스크린샷 요청 형태 · 값 조회 · 타일 갈래.
- 재사용 seam: 상세 화면 seam `frontend/test/datasetPreviewTest.tsx`(`renderDetail`·`drawnMap`) 위의 `dataset-preview-zoom.test.tsx`·`dataset-value-lookup.test.tsx`·`dataset-preview-screenshot.test.tsx`·`dataset-preview-tiles.test.tsx`, 업로드 모달 seam 위의 `preview-layout-20260912.test.tsx`(CSS 원문 계측 도우미 `block()` 포함), 훅 순수 함수 seam(`centeredPanFor` 직접 호출 · `scale-ladder.test.tsx` 와 같은 형태).
- 신설 seam: **없음.** 새 렌더 진입점·새 목 계층을 만들지 않는다. ⑶⑷⑸ 는 export 된 순수 함수 호출이고, jsdom 에서 내용 상자를 만들려면 `.pv-layers` 의 `offsetWidth/offsetHeight` 를 `Object.defineProperty` 로 주는 기존 관행(뷰포트 `clientWidth` 를 주던 것과 같은 방식)을 쓴다.
- 해당 서비스 단독 게이트 이름: `frontend-typecheck` · `frontend-test` · `frontend-visual` · `frontend-fixture-reach`. 프런트 단독. `frontend-visual` 은 `COLAB_VISUAL_URLS` 에 상세 미리보기·업로드 미리보기·등록 전 미리보기 페이지 URL 을 **실선언**한다(CSS 를 만지므로 `COLAB_VISUAL_EXEMPT=1` 금지).
- red → green 순서: ⑴⑵⑹⑺ 을 요구하는 시험을 먼저 추가해 red 를 관측한 뒤 도구 층을 세운다. ⑶⑤ 는 내용 ≠ 뷰포트 픽스처로 red 를 먼저 관측한 뒤 내용 상자를 넣는다. ⑷ 는 `clientX/Y` 를 실은 휠 이벤트로 red 를 먼저 관측한다. 각 red 의 관측 기록(시험 이름·실패 문구)을 남긴다.
- green-by-skip 방지: ⑴ 은 네 화면 **각각** 별도 케이스로 돌리고 도구 요소가 화면에 **존재**함을 먼저 단언한 뒤 부모를 본다(조회 실패 0건 통과 금지). ⑶⑤ 는 내용 = 뷰포트인 대조군과 내용 ≠ 뷰포트인 실험군을 **쌍**으로 두어 새 인자가 실제로 결과를 바꿈을 보인다. ⑹ 은 도구 층 밖 클릭이 값 조회를 **일으킴**(양성)과 도구 층 위 클릭이 일으키지 않음(음성)을 같은 시험에 둔다. 수집 0건 red 는 게이트가 잰다.
- 실제 브라우저(`agent-browser` · 판정은 사람): 상세 미리보기에서 ⓐ 첫 표시 시 그림(`preview-single-image`)과 뷰포트(`preview-viewport`)의 `get box` 중심이 두 축 모두 1px 이내 ⓑ 확대 2회 + 드래그 200px 뒤 확대 줄·범례·값 조회의 `get box` 가 변하지 않음 ⓒ 뷰포트 `get box` 높이 = `.pv-frame-in` 높이(뷰포트가 틀을 채움)이고 도구 요소 상자가 뷰포트 상자 안에 있음 ⓓ 휠 확대 뒤 커서 아래 픽셀이 같은 자리(스크린샷 전후) ⓔ 도구 층 위 클릭 뒤 값 조회 패널이 바뀌지 않음. 업로드 인라인·확장보기는 ⓑⓒ(확장보기 ⓒ 는 `.pvx-b` 가 스크롤되지 않음 — 뷰포트 높이 = `.pvx-b` 내용 높이). 등록 전 미리보기는 ⓒ. ⓕ **모서리 충돌**: 업로드 모달 뷰포트(가장 좁은 화면)에서 도구 요소 쌍마다 `get box` 교집합 = 0(우하단 확대 줄 + 한계 안내 + 스크린샷 버튼 `min-height: 44px` 대 좌하단 HUD + 값 조회). 좌표는 JSON 으로 남긴다(워크트리 가드가 `eval` 을 막으므로 `get box` 만 쓴다). 라이트·다크 스크린샷을 `frontend-visual` 이 남긴다.
- 준비 실패·미실행을 green 으로 세지 않는다. 3계수·종료코드를 그대로 회수한다.

## 정책 대조 (작성 시점 제약)
대조 원본은 `.agents/rules/product.md` §3(불변 규칙 8항)·§5(절대 하지 않는 것)이며 두 절을 읽고 항목별로 대조했다.
- §3-1 도메인 테이블 참조 · §3-2 AI→계보 쓰기 · §3-3 마이그레이션 체인 · §3-4 core-api geo import · §3-5 연구실 경계 · §3-6 정규 ID 타입: **저촉 없음.** 프런트 화면 코드만 바꾸고 조회·DB·백엔드를 건드리지 않는다.
- §3-7 생성물 손수정: **저촉 없음.** `src/generated/` 를 만지지 않는다. §3-8 절대경로: **준수.**
- §5 PoC·v1 복사: **저촉 없음.** §5 게이트 우회: **저촉 없음** — 네 게이트 실선언. §5 생성물 손수정·절대경로: **저촉 없음.**
- §5 「나중에」로 남기기: **부분 해당 — 드러내 둔다.** 터치·핀치는 승인 intent 가 명시 후속 분리한 항목이다(Ted 「좋아 후속 분리 할게」). 완료로 세지 않고 「범위 밖」에 남긴다.
- §5 범위 늘리기: **저촉 없음.** 값 조회 역변환의 내용 상자 전환은 intent 「값 조회 클릭과 커서 위경도 표시는 종전대로 동작한다」와 「스크린샷의 지금 장면이 실제 그려진 자리와 일치」를 지키기 위한 동반 필수다 — 중앙 정렬만 옮기고 역변환을 두면 두 결과가 서로 다른 상자를 봐 값 조회가 더 어긋난다. 우려 항목 1 로 올린다.
- §5 대화형 UI 도입: **저촉 없음.** 계약 동결 해제 필요: **아니오.**
- 정본 §8 확대 조건(`Policy_데이터셋_상세` v2.6): ⑵ 값·팔레트·범례 불변 ⑶ 재렌더 없음 ⑷ 한계 = 데이터 해상도 ⑸ 모든 층에 함께 ⑹ 저장 없음 ⑺ 100 ms — **전부 유지.** 기본 배율 값(축척 사다리 〈232〉·〈238〉)은 손대지 않는다.
- 결정 로그: 종전 판정 ⑦ ⓐ(`dev-package/prd/specs/2026-09-12-issue-preview-controls-v2.md`)를 intent 가 명시 해제. 신규 legacy 결정번호 없음.
- 용어: 뷰포트 · 층 묶음 · 도구 층 · 내용 상자 · 기본 배율 · 축척 사다리. `DOMAINS.md` 정본 표기(연구실·계보·Lv)는 건드리지 않는다.

### 디자인 제약 확인
정본 = `frontend/src/shell/tokens.css`. 판정 기준 = `.agents/skills/design-review/SKILL.md §0`(대비 4.5:1 · 글자 13px 이상 · 미정의 토큰 0 · 음수 여백 0 · 카드 그림자 0(팝오버 허용) · 여백은 컨테이너 소유). 인터랙션 = `.agents/skills/apple-design/SKILL.md`.

**① 데이터셋 상세 — 미리보기 뷰포트 + 도구 층**
- 토큰: `--color-surface`·`--color-border`·`--radius-sm` 만 쓴다. 파일별 `:root` 신설 없음. 새 색 없음.
- 글자: 도구 문면은 종전 13px(`.pv-zoom`·`.pv-legend`·`.pv-hud` 모두 13px 명시). 상속에 기대지 않는다.
- 대비: 도구 패널이 그림 위에 얹히므로 **불투명 표면 배경**을 갖는다 — `frontend-visual` 이 상속 배경 기준으로 재는 값이 그림에 좌우되지 않는다. 다크에서도 `--color-surface`(#1a222c) 위 `--color-text-muted` 가 4.5:1 인지 실화면에서 잰다(우려 3).
- 그림자: 0. 도구 패널은 팝오버가 아니라 고정 층이므로 보더만.
- 여백: 모서리 컨테이너가 `inset 12px` 과 `gap` 을 소유한다. 도구 요소는 margin 을 지지 않는다(`.pv-hud` 의 상단 margin 은 도구 층 안에서 0).
- 인터랙션: 버튼의 pointer-down 피드백은 종전 `.pv-zoom button` 규칙 그대로. 새 전환·애니메이션 없음 → `prefers-reduced-motion` 분기 신설 없음. 휠·드래그는 `transform` 값 갱신뿐이며 중단 가능.
- 판정: **조건부 통과.** 다크 대비와 범례 최대 높이는 실화면 계측으로 확정한다(우려 3·4).

**② 업로드 인라인 미리보기 — 도구 층(확대 줄만)**
- 토큰·글자·그림자·여백: ①과 같은 규칙. 배지 `.pv-badges` 는 현 자리(뷰포트 밖) 유지.
- 판정: **통과.** 새 시각 결정 없음(①의 규칙 재사용).

**③ 업로드 확장보기 — 도구 층(확대 줄만)**
- ②와 같다. 확장보기 본문 `.modal-b.pvx-b` 의 세로 방향(`#27` 시험 20)은 유지.
- 판정: **통과.**

## advisor ① 검토 결과 (2026-09-18)
판정 go-with-fixes. 반영한 수정 — ⑴ 넘치는 축의 시작·리셋 중앙 ⑵ `.pv-map` `flex-wrap` 이 넘침 원인 ⑶ 핸들러의 `centeredPanFor` 존치(기존 시험 스텁 호환) ⑷ 네 번째 소비처 등록 전 미리보기 ⑸ 확장보기 뷰포트 상자 규칙 ⑹ 모서리 충돌 실측 ⑺ 두 치수 중 하나라도 0 이면 대체. 원문 `advisor-1-issue-120.md`(task runtime). 내 단언 (b)「스크롤은 `overflow: auto` 에서 난다」는 절반만 맞았다 — 자리는 맞고 원인은 형제 쌓임 + `flex-wrap` 줄 높이 둘이다.

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 중앙 정렬을 그림 실제 상자 기준으로 바꾸면, 뷰포트 상자를 전제한 값 조회·HUD 역변환과 스크린샷 장면이 **다른 상자를 보게 된다.** 지금도 세로가 긴 그림에서 값 조회 세로가 어긋나 있지만, 한쪽만 고치면 더 벌어진다. | 같은 커밋에서 역변환·스크린샷도 내용 상자를 쓰게 한다(내용 = 뷰포트인 타일 갈래는 수가 같다) | 중앙 정렬만 바꾸고 역변환은 그대로 둔다 | ⓐ — intent 가 「값 조회 종전대로」·「장면 일치」를 요구했다. ⓑ 는 중간 상태에서 값 조회가 더 틀린다 |
| 2 | 도구가 뷰포트 안으로 들어가면 **버튼 클릭이 뷰포트의 값 조회 클릭·드래그 시작·더블클릭으로 버블링**된다. 확대 버튼을 누르면 그 자리의 값을 조회하는 결함이 새로 생긴다. | 도구 층 루트가 click·mousedown·dblclick 을 멈추고, 훅의 네이티브 휠 핸들러가 도구 층 안 target 을 무시한다 | 뷰포트 핸들러마다 target 검사를 넣는다 | ⓐ — 규칙이 부품 한 곳에 산다. ⓑ 는 핸들러 넷에 같은 검사가 흩어진다 |
| 3 | 도구 패널이 그림 위에 얹힌다. 배경을 투명하게 두면 **대비가 그림 색에 좌우**돼 4.5:1 을 보장할 수 없다. | 불투명 `--color-surface` 배경 + 토큰 보더 | 반투명 배경 | ⓐ — `frontend-visual` 이 상속 배경으로 재므로 반투명은 판정 자체가 서지 않는다 |
| 4 | 범례가 구간 수에 따라 길어져 **뷰포트 높이를 넘을 수 있다.** 넘치면 잘리거나 다른 모서리와 겹친다. | 범례 패널에 `max-height: calc(100% - 24px); overflow: auto` — 범례 안에서만 스크롤 | 범례를 뷰포트 밖에 남긴다 | ⓐ — ⓑ 는 「같이 움직인다」 결함을 범례에 남긴다. 실제 구간 수 상한은 실화면에서 확인 |
| 5 | jsdom 은 `offsetWidth/offsetHeight` 를 0 으로 주므로 내용 상자를 **뷰포트로 대체**하는 분기가 기존 시험을 전부 통과시킨다. 새 분기가 실제로 도는지 시험이 보지 않으면 green-by-skip 이다. | 내용 ≠ 뷰포트 픽스처(`defineProperty`)로 실험군을 두고 대조군과 쌍으로 단언 | 순수 함수 단위 시험만 둔다 | ⓐ — 훅이 실제로 내용 상자를 읽어 넘기는지까지 잰다 |
| 6 | 타일 갈래에서 `.pv-layers` 의 배치 높이가 무엇인지 **코드로 확인하지 못했다**(`.pv-mosaic { height: 100% }` 의 부모 높이가 auto). 0 이면 뷰포트 대체 분기로 종전과 같고, 0 이 아닌 다른 값이면 타일 좌표가 어긋난다. | 레인이 `dataset-preview-tiles.test.tsx` 와 실물 DOM 으로 먼저 확인하고, 타일 갈래는 **명시적으로 뷰포트 상자를 쓰게** 고정한다(`tiled` 이면 `contentBox = box`) | 측정값을 그대로 믿는다 | ⓐ — 타일 갈래는 설계상 내용 = 뷰포트다. 지어내지 않고 고정한다 |
| 7 | `.pv-frame-in { overflow: auto }` 를 남기면 도구 층 밖에 남는 형제(부분 실패 안내 등)가 있을 때 **스크롤바가 다시 설 수 있다.** `hidden` 으로 바꾸면 그 안내가 잘린다. | `auto` 유지 — 뷰포트가 틀을 채우고 도구가 안으로 들어가 완료 상태에서 넘칠 것이 없음을 실화면 ⓒ 로 잰다 | `hidden` 으로 바꾼다 | ⓐ — ⓑ 는 넘침을 감추는 것이지 없애는 것이 아니다 |
| 8 | 세로가 긴 그림은 기본 배율에서 **세로가 뷰포트를 넘친다**(사다리가 폭 기준). 종전 리셋 `(0,0)` 은 그 그림을 위 정렬로 둬 intent 결과 3(중앙)에 미달한다. | 시작·리셋 이동값을 두 축 모두 중앙으로 하고 드래그만 가둔다(중앙 기준 편차 저장) | 종전대로 넘치는 축은 `(0,0)` | ⓐ — ⓑ 는 이슈 첨부 1 의 경우가 그대로 남는다 |
| 9 | `.pv-map { flex-wrap: wrap }` 이 세로 긴 그림의 **넘침 원인 절반**이다. 도구만 옮기면 jsdom 은 green 인데 실화면에는 스크롤바가 남는다. | `nowrap` 으로 바꾸고 CSS 원문 시험 + 실화면 ⓒ 로 잠근다 | 도구 이동만 한다 | ⓐ |
| 10 | 도구 층 모서리 묶음이 좁은 뷰포트(업로드 모달)에서 **서로 겹칠 수 있다.** 재지 않으면 모른다. | 실화면에서 쌍별 `get box` 교집합 0 을 잰다. 겹치면 좌하단 값 조회 패널의 폭 상한을 토큰 여백 안에서 조정 | 재지 않는다 | ⓐ |

## 범위 밖
- 터치·핀치 조작(Ted 결정 「좋아 후속 분리 할게」 · 후속 이슈). 기본 배율 값·축척 사다리·한계 배율 정책. canvas/WebGL 재렌더. 라이브러리 도입.
- 업로드 화면 배지 `.pv-badges` 의 자리. 서버 스크린샷 계약·렌더 요청·범례 값 형식. 다른 이슈. 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 산출 계획
- 라운드 파일: 미작성(선례 #97 묶음과 같이 spec + 보고서로 간다).
- 예상 레인 수: **1 (직렬).** 세 화면이 같은 훅·같은 CSS 파일을 만진다. 쓰기 주체 하나.
- 커밋 1개, PR 1건(`Closes #120`). 보고서 `dev-package/reports/issue-120/README.md` + `images/` + 게이트 요약 사본. PR 본문은 task runtime 에 두고 저장소에 커밋하지 않는다.

## 미확인 (이 spec 작성 중 확인하지 못한 것)
- ~~타일 갈래 `.pv-layers` 의 실제 배치 높이(우려 6)~~ — advisor ① 확인(2026-09-18): `offsetWidth` = 뷰포트 · `offsetHeight` = 0 → 뷰포트 대체 분기. 타일 시험 의미 불변.
- 다크 모드에서 `--color-surface` 위 `--color-text-muted` 의 실제 대비값. 실화면에서 잰다.
- `.agents/skills/apple-design/SKILL.md` 본문을 열어 읽지 않았다. 인터랙션 하한은 `to-spec` 템플릿과 `design-review` §0 표 항목에 근거한다.
- `dev-package/PLAN-SoT.md §9` 는 통독하지 않았다. 〈232〉·〈238〉 은 코드 주석의 인용을 옮긴 것이다.
