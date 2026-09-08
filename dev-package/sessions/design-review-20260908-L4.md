# design-review 20260908 · L4 인터랙션·모션 (apple-design 축 전용)

- 대상 = `frontend/src/` 의 `auth/login.css` · `components/catalog/catalog.css` · `components/members/members.css` · `components/search/search.css` · `components/upload/upload.css` · `components/upload/FileDropCard.tsx` · `components/upload/UploadModal.tsx` · `shell/shell.css` ＋ 그 스타일이 겨냥하는 오버레이·팝오버·토스트 구현 `.tsx`(`components/upload/PreviewExpandOverlay.tsx` · `components/upload/PeriodCalendarPopover.tsx` · `components/upload/escLayer.ts` · `components/common/Toast.tsx` · `components/preview/useZoomPan.ts`).
- 정본 = `.claude/skills/apple-design/SKILL.md`. 정적 축(대비·글자 크기·토큰·여백)은 이 레인에서 판정하지 않는다.
- 「판정」은 각 행 **항목 문구의 존재 여부**다 — 항목이 결함 서술이면 「있음」이 결함 존재, 항목이 장치 서술이면 「있음」이 장치 존재.
- `--ease` 실측값 = `shell/tokens.css:42` `--ease: 0.14s cubic-bezier(0.4, 0, 0.2, 1)`. 이 레인의 모든 `transition: … var(--ease)` 가 이 한 값을 쓴다.

## 판정표

| # | 축 | 항목 | 판정 | 근거 path:line · 실측값 | 처리 |
|---|---|---|---|---|---|
| 1 | 응답 | `:active` 규칙(누름 순간 피드백)이 없음 | 있음 | `frontend/src` 전체 `.css`·`.tsx` 에 `:active` 선택자 0건(전수 grep) · apple-design §1 「Respond on pointer-down, not on release」 | Ted 판정 |
| 2 | 응답 | 버튼·행·칩 피드백이 hover 전용 | 있음 | `catalog.css:56` `.tbl tr.clk td { transition: background var(--ease), box-shadow var(--ease); }` · `upload.css:418` `.dr-cal-d:hover{background:var(--color-primary-100);}` · `upload.css:406`·`434` 동형 · `shell.css:65`·`143`·`172`·`210`·`233`·`251`·`276` 전부 hover·포커스 색 전환 · apple-design §1 | Ted 판정 |
| 3 | 응답 | 입력 경로의 인위적 지연(debounce·피드백 전 `setTimeout`) | 없음 | `components/search/SearchHero.tsx:32` `onChange={(e) => setQuery(e.target.value)}` 직결 · `:25` `onSubmit={submit}` · `frontend/src` 의 `setTimeout` 은 전부 폴링(`UploadModal.tsx:373` · `PreviewPanel.tsx:218` · `usePreviewRender.ts:61`·`70`)·재시도(`backoff.ts:14`)·정지 감시(`xhrPut.ts:36`)·토스트 수명(`Toast.tsx:50`)·포커스 이동(`UploadModal.tsx:773`·`781`·`791`·`805`, 지연 인자 `0`) — 피드백 앞 지연 0건 · apple-design §1 | — |
| 4 | 응답 | 배경 클릭 닫기를 `onMouseDown` ＋ `onClick` 두 단으로 확인 | 있음 | `UploadModal.tsx:869` `onMouseDown` 에서 `downOnBackdrop.current = e.target === e.currentTarget` · `:873` `onClick` 에서 두 조건 동시 확인 · `PreviewExpandOverlay.tsx:32`·`:36` 동형 | — |
| 5 | 중단 가능성 | 사용자 구동 상태 전환이 `transition`(중단 가능) | 있음 | `login.css:61`·`79` · `catalog.css:56`·`150` · `members.css:41` · `search.css:109`·`113` · `upload.css:405`·`417`·`432` · `shell.css:65`·`143`·`172`·`210`·`233`·`251`·`276` — 전부 `transition` · apple-design §3 | — |
| 6 | 중단 가능성 | 모달 열기가 고정 길이 `animation`/`@keyframes` | 있음 | `upload.css:31` `animation: up-rise 0.46s ease;` ＋ `:33` `@keyframes up-rise { from { transform: translateY(3%); opacity: 0.4; } to { transform: none; opacity: 1; } }` · apple-design §3 「Avoid CSS transitions and `@keyframes` for anything gesture-driven」 | Ted 판정 |
| 7 | 중단 가능성 | 고정 시작값에서 출발(현재값 아님) | 있음 | `upload.css:34` `from { transform: translateY(3%); opacity: 0.4; }` — 화면의 현재값이 아니라 고정 `3%`·`0.4` 에서 시작 · apple-design §3 「Always animate from the presentation (current) value」 | Ted 판정 |
| 8 | 중단 가능성 | 무한 반복 `animation`(제스처 대상 아님) | 있음 | `upload.css:165` `animation: up-spin 0.8s linear infinite;` ＋ `:167` `@keyframes up-spin { to { transform: rotate(360deg); } }` — 로딩 표시 | — |
| 9 | reduced-motion | `upload.css` 분기 | 있음 | `upload.css:37` `@media (prefers-reduced-motion: reduce) { .modal.modal-takeover { animation: none; } }` · `:168` `@media (prefers-reduced-motion: reduce) { .vizload .spin { animation: none; } }` — 움직이는 속성 = `transform`(translateY · rotate) ＋ `opacity` · apple-design §14 | — |
| 10 | reduced-motion | `login.css` 분기 | 없음 | 모션 선언 2건 = `:61` `transition: border-color var(--ease);` · `:79` `transition: background var(--ease);` — 색 전용, `transform` 0건. apple-design §14 「Keep opacity/color changes that aid comprehension」 → 분기 불요 | — |
| 11 | reduced-motion | `catalog.css` 분기 | 없음 | 모션 선언 2건 = `:56` `transition: background var(--ease), box-shadow var(--ease);` · `:150` `.tbl td.rowact .ra { … opacity: 0; transition: opacity var(--ease); }` — 색·그림자·불투명도 전용, `transform` 0건 → apple-design §14 기준 분기 불요 | — |
| 12 | reduced-motion | `members.css` 분기 | 없음 | 모션 선언 1건 = `:41` `transition: background var(--ease), border-color var(--ease);` — 색 전용 → 분기 불요 | — |
| 13 | reduced-motion | `search.css` 분기 | 없음 | 모션 선언 2건 = `:109` `transition: background var(--ease);`(색) · `:113` `border-radius: 50%; background: #fff; transition: left var(--ease);` — **`left` 는 위치 이동**이라 색 전용이 아니다(토글 손잡이). apple-design §14 | Ted 판정 |
| 14 | reduced-motion | `shell.css` 분기 | 없음 | 모션 선언 7건 = `:65`·`:143`·`:172`·`:210`·`:233`·`:251`·`:276`, 전부 `background`·`border-color`·`color` 전환. `transform` 0건 → 색 전용, 분기 불요 | — |
| 15 | reduced-motion | `prefers-reduced-transparency` · `prefers-contrast` 분기 | 없음 | `frontend/src` 전체 `prefers-` 히트 2건이 모두 `upload.css` 의 reduced-motion(`:37`·`:168`) · apple-design §14. 단 `backdrop-filter` 가 0건이라(#19) 반투명 대상 자체가 없다 | — |
| 16 | 타이포 | 크기와 무관한 고정 `letter-spacing` | 있음 | `login.css:27` `letter-spacing: 0.01em;` · `catalog.css:46` `font-size: 10px … letter-spacing: 0.05em` · `catalog.css:59` `font-size: 13px … letter-spacing: -0.01em` · `catalog.css:89` `font-size: 10px … letter-spacing: 0.04em` · `shell.css:92` `letter-spacing: var(--tracking-body)` = `tokens.css:34` `--tracking-body: 0.0096em`(크기 무관 단일 값) · apple-design §15 「Tracking is size-specific — never one value for all sizes」 | Ted 판정 |
| 17 | 타이포 | 제목 tracking 이 음수(큰 글자를 조임) | 있음 | `catalog.css:30` `font-size: var(--text-h2, 24px) … letter-spacing: -0.023em` · `search.css:6` 동일 값 · `shell.css:116` `font-size: 17px; letter-spacing: -0.02em` · apple-design §15 「tighten large text (`-0.02em`)」 부합 | — |
| 18 | 타이포 | 본문 `line-height` 지정 | 있음 | `shell.css:91` `line-height: var(--leading-body)` = `tokens.css:33` `--leading-body: 1.467` · `login.css:39`·`:94` `1.5` · `search.css:19` `1.6` · `:34` `1.7` · `:74`·`:77` `1.6` · `members.css:118` `1.7` · `upload.css:226` `1.5` · apple-design §15 | — |
| 19 | 재질·깊이 | `backdrop-filter` 사용처 열거 | 없음 | `frontend/src` 전체 `.css`·`.tsx` 에 `backdrop-filter` 0건. 반투명 크롬은 스크림 2건뿐 = `upload.css:20` `background: rgba(18, 22, 25, 0.5);`(전체화면 모달 배경) · `upload.css:450` `.modal-back.pvx-back{ … background:rgba(18,22,25,0.5);}`(확장보기 배경). apple-design §12 는 정적 합격선이 없어 열거만 한다 | — |
| 20 | 공간 연속성 | 오버레이·팝오버가 호출한 자리에서 열림(`transform-origin` 앵커 ＋ 여는 전환) | 없음 | `upload.css:397` `.dr-pop{position:absolute;top:calc(100% + 6px);left:0;z-index:60; …}` — 위치는 트리거 아래에 붙으나 전환 0건 · `frontend/src` 전체 `transform-origin` 선언 0건(히트 2건은 `PreviewPanels.tsx:156`·`161` 의 좌표계 설명 주석) · `upload.css:450`·`452` `.pvx-back`/`.pvx` 도 전환 0건 = 즉시 표시 · apple-design §7 「Anchor interactions to their source」 | Ted 판정 |
| 21 | 공간 연속성 | 열기·닫기 경로 대칭 | 없음 | `upload.css:31` 열기만 `up-rise`(위로 3% 상승) 정의 · 닫기 애니메이션 정의 0건 — 조건부 렌더 해제로 즉시 사라짐(`PreviewExpandOverlay.tsx:27` 이하 반환 트리) · apple-design §7 「Enter and exit along the same path」 | Ted 판정 |
| 22 | 오버레이 해제 | Escape 처리(`data-esc-layer` 표식 ＋ 층별 자기 닫기) | 있음 | `escLayer.ts:12` `export const ESC_LAYER_ATTR = 'data-esc-layer';` · `:15`–`:26` `useEscLayer` 가 `document` keydown 에서 `e.key === 'Escape'` 만 받아 자기 닫기 호출 · `PreviewExpandOverlay.tsx:26` `useEscLayer(useCallback(() => requestClose(), [requestClose]))` ＋ `:31` `{...{ [ESC_LAYER_ATTR]: '확장보기' }}` · `PeriodCalendarPopover.tsx:14` 동일 import · `UploadModal.tsx:643`–`:649` 표식이 하나라도 떠 있으면 Esc 를 먹지 않음 | — |
| 23 | 오버레이 해제 | 배경 클릭 닫기 | 있음 | `UploadModal.tsx:869`–`:874` · `PreviewExpandOverlay.tsx:32`–`:38` — 둘 다 `e.target === e.currentTarget` ＋ 누른 자리 확인 | — |
| 24 | 직접 조작 | 드래그가 Pointer Events ＋ `setPointerCapture` 를 쓰지 않음 | 있음 | `useZoomPan.ts:228` `onMouseDown` · `:236`–`:250` `window` 의 `mousemove`/`mouseup` 로 추적 · `frontend/src` 전체 `onPointerDown`·`setPointerCapture` 0건 · apple-design §2 | Ted 판정 |
| 25 | 직접 조작 | 드래그 히스테리시스(약 10px 임계) 없음 | 있음 | `useZoomPan.ts:229`–`:231` `if (e.button !== undefined && e.button !== 0) return; drag.current = { x: e.clientX, y: e.clientY };` — 첫 이동부터 즉시 추적, 임계 0 · apple-design §10 | Ted 판정 |
| 26 | 직접 조작 | 파일 드롭 영역에 드래그 중 시각 피드백 없음 | 있음 | `FileDropCard.tsx:168`–`:171` `onDragOver` 가 `preventDefault`·`stopPropagation` 만 수행(상태 갱신 0) · `onDragEnter`/`onDragLeave` 0건 · `upload.css` 에 `.dropzone` 드래그 상태 규칙 0건 · apple-design §1 「Feedback must be continuous during the interaction」 | Ted 판정 |
| 27 | 모션 | 스프링·속도 계승·모멘텀 투사 사용 | 없음 | 스프링 라이브러리 import 0건 · 모든 전환이 `--ease`(`tokens.css:42` 고정 0.14s cubic-bezier) · `useZoomPan.ts:239`–`:241` 는 매 `mousemove` 의 델타를 더할 뿐 속도 기록 0 · apple-design §4·§5·§6 | Ted 판정 |
| 28 | 모션 | 1:1 드래그 추적 품질(오프셋 유지·프레임 지연) | [미상 · 실화면 계측 필요] | `useZoomPan.ts:236`–`:243` 는 델타 누적식이라 코드상 1:1 이나 실제 추적 지연은 정적으로 못 잰다 | 실화면 계측 |
| 29 | 모션 | 스프링 감쇠·응답 체감 | [미상 · 실화면 계측 필요] | 스프링 미사용(#27)이라 측정 대상 자체가 없다 — 도입 후에만 계측 가능 | 실화면 계측 |
| 30 | 모션 | 경계 러버밴딩 | [미상 · 실화면 계측 필요] | `useZoomPan.ts:241` `clampView` 로 경계에서 값을 자름(점진 저항 코드 0) · 하드 스톱 체감은 실화면 필요 · apple-design §9 | 실화면 계측 |
| 31 | 모션 | 프레임 평활도(스트로빙·드롭 프레임) | [미상 · 실화면 계측 필요] | 이 레인 대상 파일에 `will-change` 0건(전체 1건 = `preview/preview.css:195`, 대상 밖) · 실측은 화면에서만 | 실화면 계측 |

### 실화면 계측 방법(#28~#31)

- #28 = 확대된 미리보기를 일정 속도로 끌며 포인터 좌표와 이미지 변위를 프레임별로 기록해 차이를 잰다(개발도구 Performance 의 입력 이벤트 ↔ 페인트 타임라인).
- #29 = 스프링 도입 후 열기·닫기 변위 곡선을 녹화해 오버슈트 비율과 정착 시간을 잰다.
- #30 = 경계 밖으로 끌었을 때 변위 ÷ 포인터 이동 비율이 거리에 따라 줄어드는지 기록한다.
- #31 = 모션 구간을 60fps 로 녹화해 프레임당 위치 변화량과 드롭 프레임 수를 센다.

## 소계

- 있음 15 · 없음 12 · [미상] 4 · 합 31
- 처리 = 즉시 수정 후보 0 · Ted 판정 12 · 실화면 계측 4 · — 15

## Ted 판정 후보

1. **누름 순간 피드백(`:active`) 도입 여부**(#1·#2 · 현재 전수 0건)
   - ⓐ 단추·행·칩에 누름 상태 규칙을 새로 세운다.
   - ⓑ 현행 hover 전용 피드백을 유지한다.
   - 권고 = ⓐ. apple-design §1 은 피드백을 누름 순간에 두라고 정한다. 다만 적용할 선택자 묶음과 값(배경 한 단계 어둡게 대 축소 변형)은 정본이 없어 판정이 필요하다.
2. **전역 reduced-motion 규칙을 `shell/tokens.css` 또는 `shell/shell.css` 에 둘지**(#13·#15)
   - ⓐ 셸에 전역 규칙 한 벌을 세워 이동·변형 전환을 일괄로 끈다.
   - ⓑ 이동을 쓰는 파일마다 분기를 따로 단다(현행 연장).
   - 권고 = ⓑ. 대상이 `search.css:113` 의 `transition: left` 한 건이고, 나머지 파일의 모션은 전부 색·불투명도 전환이라 apple-design §14 가 유지하라고 한 종류다. 전역 규칙은 그 색 전환까지 함께 끄게 되어 범위가 과하다. 이동·변형 전환이 늘어난 뒤 재검토한다.
3. **모달 열기 애니메이션을 중단 가능한 형태로 바꿀지**(#6·#7·#21)
   - ⓐ `upload.css:31` 의 `up-rise` 를 전환 기반으로 바꾸고 닫기 경로를 대칭으로 세운다.
   - ⓑ 현행 0.46s 고정 애니메이션을 유지한다.
   - 권고 = ⓑ. apple-design §3 이 금지하는 대상은 제스처로 잡히는 것이고 이 모달은 드래그로 잡히지 않는다. 단 §7 의 대칭 경로는 어긋나 있으므로 닫기 경로 추가는 별도로 판정한다.
4. **팝오버·오버레이를 호출한 자리에서 열지**(#20)
   - ⓐ `.dr-pop`·`.pvx` 에 `transform-origin` 앵커와 여는 전환을 세운다.
   - ⓑ 현행 즉시 표시를 유지한다.
   - 권고 = ⓐ 중 `.dr-pop` 만. apple-design §7 은 팝오버가 트리거에서 나오라고 정하고 `.dr-pop` 은 이미 트리거 바로 아래에 붙어 앵커 값이 자명하다. 전체화면 오버레이 `.pvx` 는 나오는 자리가 정본에 없다.
5. **드래그를 Pointer Events 로 옮기고 히스테리시스를 둘지**(#24·#25)
   - ⓐ `useZoomPan.ts` 를 `onPointerDown` ＋ `setPointerCapture` 로 옮기고 약 10px 임계를 둔다.
   - ⓑ 현행 mouse 이벤트 ＋ `window` 리스너를 유지한다.
   - 권고 = ⓐ. apple-design §2 는 포인터가 요소 밖으로 나가도 추적이 이어지도록 캡처를 쓰라고 정한다. 현행 `window` 리스너가 같은 효과를 내지만 터치·펜 입력을 받지 않는다. 임계값은 정본에 「약 10px」로만 있어 확정값 판정이 필요하다.
6. **파일 드롭 영역의 드래그 중 시각 피드백을 세울지**(#26)
   - ⓐ `onDragEnter`/`onDragLeave` 상태와 대응 CSS 규칙을 세운다.
   - ⓑ 현행(피드백 없음)을 유지한다.
   - 권고 = ⓐ. apple-design §1 은 상호작용 도중 피드백이 이어져야 한다고 정한다. 상태 색은 정본에 없어 값 선택이 필요하다.
7. **고정 `letter-spacing` 값을 크기별로 가를지**(#16)
   - ⓐ 크기 구간별 tracking 값을 세워 `tokens.css` 에 올린다.
   - ⓑ 현행 파일별 고정 값을 유지한다.
   - 권고 = ⓐ. apple-design §15 는 tracking 이 크기별이어야 한다고 정한다. 구간 경계와 각 값은 정본이 없다.
8. **스프링·속도 계승을 도입할지**(#27)
   - ⓐ 스프링 라이브러리를 들여 제스처 종료 시 속도를 넘긴다.
   - ⓑ 현행 고정 이징(`--ease` 0.14s)을 유지한다.
   - 권고 = ⓑ. 이 레인의 모션은 색 전환이 대부분이고 제스처 종료가 있는 자리는 확대·이동 하나다. 의존성 추가 대비 적용 면이 좁다. #24 처리 뒤 재검토한다.

## 이번에 세지 않은 축

- 정적 축 전부 — 대비 비율 · 13px 미만 글자 · 미정의 토큰 · 파일 내 토큰 정의 · 음수 여백 · `box-shadow` 개수. L1~L3 레인 담당.
- 재질·깊이의 품질 — apple-design §12 에 대응하는 정적 합격선이 없어 열거만 했다(#19).
- 다중 감각 피드백(소리·햅틱, apple-design §13) — 구현 0건이고 정본에 요구가 없다.
- 대상 파일 밖의 모션 — `components/preview/preview.css:195` `will-change: transform` 등.

## css_audit 오탐

- 0건. `motion decl` 열의 6개 파일 값(login 2 · catalog 2 · members 1 · search 2 · upload 7 · shell 7)과 `reduced-motion` 열(`upload.css` 만 yes)을 실물 규칙으로 전수 대조해 일치를 확인했다.
