# design-review 20260924 — 통합 판정표 (레인 5개 취합)

## 1. 머리

- 범위 — 기준 트리 `dc05531c`(develop `7acd0fce` ＋ 정적 계측 `css_audit` 커밋) · 레인 판정표 5건 커밋 `c0ff9986`. 워크트리 `design-review-apple-20260924`.
- 모드 = `audit`. CSS·TSX 수정 0건. 레인 5개와 이 취합 모두 제품 코드를 고치지 않았다.
- 순서 — 애플 원칙 레인 먼저(L4a 응답·모션·재질 · L4b 타이포), 그다음 정적 레인(L1 셸·공통 · L2 카탈로그·검색·상세·미리보기 · L3 업로드·계보·프로젝트·랩·멤버·승인).
- 계측 보고 = `dev-package/reports/design-review/20260924/css_audit.md`(CSS 21종 · 토큰 85).
- 실화면 미계측 — 로컬 스택이 꺼져 있어 이번 단계는 정적 판정만 했다. 실화면이 필요한 행은 `[미상 · 실화면 계측 필요]`(§9).
- 레인 입력 — `dev-package/sessions/design-review-20260924-L1.md` · `-L2.md` · `-L3.md` · `-L4a.md` · `-L4b.md`.

| 레인 | 범위 | 레인 행 | 취합 행 | 있음 | 없음 | [미상] |
|---|---|---|---|---|---|---|
| L4a | apple-design 응답·모션·재질·접근성 신호(코드 확인분) | 26 | 26 | 15 | 9 | 2 |
| L4b | apple-design §15 타이포 | 7 | 7 | 3 | 4 | 0 |
| L1 | `shell/**`·`components/common/**`·`auth/**`·`components/dashboard/**`·`app/**`·`routes/**` | 28 | 26 | 5 | 17 | 4 |
| L2 | `components/catalog/**`·`search/**`·`detail/**`·`preview/**`·`datasetpreview/**` | 17 | 17 | 3 | 14 | 0 |
| L3 | `components/upload/**`·`lineage/**`·`project/**`·`lab/**`·`members/**`·`approval/**` | 12 | 11 | 1 | 8 | 2 |
| 계 | — | 90 | 87 | 27 | 52 | 8 |

- 취합 행이 레인 행보다 적은 이유 — L1#21 은 L1#19 와 근거가 같아(L1 스스로 「위 #19 와 동일 근거」) 한 행으로 합쳤고, L1#28(모션 선언 사실)은 L4a#16 과 같은 사실이라 그 행에 합쳤다. L3#12(담당 외 · 판정 「—」)는 판정 행이 아니라 표 끝에 미집계로 남겼다.
- 소계는 취합 정정(§4) 반영 값이다. 레인 자체 소계와의 차이는 §3.

## 2. 판정표

- 판정 = 결함 유무(있음 = 결함 있음). 처리 = 즉시 수정 후보 / Ted 판정 / 실화면 계측 / —.
- 「취합 정정」 = 취합이 원 소스를 열어 레인 값과 다르게 확인한 것. 레인 값은 지우지 않고 함께 적는다.
- 대비는 WCAG 상대휘도. 취합 재계산값은 명시했다.

| # | 레인 | 축 | 항목 | 판정 | 근거 path:line · 실측값 | 처리 |
|---|---|---|---|---|---|---|
| 1 | L4a#1 | 애플 §1 응답 | `:active`(누름 순간) 규칙이 거의 없음 | 있음 | `frontend/src` 전체 `:active` 2건 = `shell/primitives.css:32` `.btn-primary:active { background: var(--color-primary-700); }` · `components/search/search.css:155` `.search-hero button:active { background: var(--color-primary-700); }` | 즉시 수정 후보(spec 제약 `S-DESIGN-CONSISTENCY-FULL-20260912.md:53` · 열린 라운드 미이행) |
| 2 | L4a#2 | 애플 §1 응답 | `.btn`(수식자 없음)·`.btn-ghost` 누름 피드백 없음 | 있음 | `primitives.css:28` `.btn:where(:not(.btn-primary, .btn-secondary)):hover` 만 · `:30` `.btn-ghost` · `:active` 0 | 즉시 수정 후보 |
| 3 | L4a#3 | 애플 §1 응답 | `.btn-secondary` 포인터 피드백 0(hover·active 모두 없음) | 있음 | `primitives.css:31` 정의만 · `:28` hover 에서 제외 · `:active` 0 · ⑦-1 | 즉시 수정 후보(누름) · hover 값은 ⑦-1(Ted 묶음 9) |
| 4 | L4a#4 | 애플 §1 응답 | ⑦-1 `.btn-primary:hover` 억눌림이 누름 피드백까지 없앰 | 없음 | hover 는 없지만(`primitives.css:28` 제외) `:32` `:active` 존재 | — |
| 5 | L4a#5 | 애플 §1 응답 | ⑦-5 `.btn-strong` 누름 피드백 없음(대비는 #55) | 있음 | `.btn-strong:hover` gray-50 만(`components/upload/upload.css:311` — 줄 번호는 취합 보충) · 전수 `:active` 2건에 없음 | 즉시 수정 후보 |
| 6 | L4a#6 | 애플 §1 응답 | 셸 대화형 클래스 누름 피드백 없음 | 있음 | `shell/shell.css` `.backlink:hover`(:72) · `.mainnav a:hover`(:177) · `.gnb-settings:hover`(:215) · `.gnb-upload:hover`(:238) · `.gnb-more:hover`(:288) · `.gnb-more-item:hover`(:323) · `.gnb-logout:hover`(:343) 전부 hover 전용 · `.loadfail-retry`(:38)·`.theme-switcher`(:431)·모달 닫기 `.x`(:456) hover·active 0 | 즉시 수정 후보 (값은 spec) |
| 7 | L4a#7 | 애플 §1 응답 | 화면 CSS 대화형 클래스 누름 피드백 없음 | 있음 | `catalog.css:33` `.tbl tr.clk td` transition(hover 전용) · `upload.css:465`·`492`(`.dr-nav button`)·`504`(`.dr-cal-d`)·`519`(`.dr-useg button`) hover 전환(선택자 이름은 취합 보충) · 화면 CSS `:active` = `search.css:155` 1건 | 즉시 수정 후보 (값은 spec) |
| 8 | L4a#8 | 애플 §1·§10 응답 | 입력 경로의 인위적 지연 | 없음 | `debounce` 0. setTimeout 은 폴링(`UploadModal.tsx:588`·`603` · `PreviewPanel.tsx:250` · `usePreviewRender.ts:75`·`122`)·재시도(`backoff.ts:14` · `logoutQueue.ts:56`)·정지 감시(`xhrPut.ts:36`)·토스트 수명(`Toast.tsx:50`)·포커스 이동 지연 0(`UploadModal.tsx:1113`–`1178`)·blob 회수(`ScreenshotButton.tsx:93`)·세션 시계(`AuthGate.tsx:75`) · `auth/workGuard.ts:136`·`:177` 120ms · `:229` 200ms = 탭 간 probe 대기(기능 대기). 대기 중 로그인 단추 진행 표시는 실화면(§9) | — |
| 9 | L4a#9 | 애플 §3 중단 | 사용자 구동 상태 전환이 고정 animation | 없음 | 전부 `transition`: `primitives.css:25` · `shell.css:70`·`175`·`213`·`236`·`286`·`340` · `catalog.css:33`·`155` · `search.css:130`·`134` · `login.css:65`·`79` · `upload.css:355`·`360`·`465`·`492`·`504`·`519` | — |
| 10 | L4a#10 | 애플 §3 중단 | 모달 열기가 고정 길이 `@keyframes`·고정 시작값 | 있음 | `upload.css:24` `animation: up-rise 0.46s ease;` · `:26` `@keyframes up-rise` | Ted 판정(묶음 1 · 판정-16 이월) |
| 11 | L4a#11 | 애플 §3 | 무한 반복 animation(제스처 대상 아님) | 없음 | `upload.css:162`·`172` `up-spin 0.8s linear infinite` · `:644` `up-analyze-pulse 1.4s` — 로딩·분석 표시, reduced-motion 분기 있음(#18) | — |
| 12 | L4a#12 | 애플 §7 공간 | 팝오버가 기준점(`transform-origin`)·여는 전환 없이 즉시 표시 | 있음 | `upload.css:482` 주석 「`display:none` ＋ `.dr-pop.open{display:block}` 로 여닫는다」 · `:484` `.dr-pop{position:absolute;top:calc(100% + 6px);left:0;…}` · 전수 `transform-origin` 1건 = `preview.css:294` `0 0` | Ted 판정(묶음 2 · 판정-17 이월) |
| 13 | L4a#13 | 애플 §7 공간 | 열기·닫기 비대칭(닫기 전환 없음) | 있음 | `UploadModal.tsx`·`PreviewExpandOverlay.tsx` 에 `closing`·`isClosing`·`onAnimationEnd`·`onTransitionEnd` 0건 — 조건부 렌더 해제로 즉시 사라짐 | Ted 판정(묶음 1 · 판정-16 이월) |
| 14 | L4a#14 | 애플 §12 재질 | `backdrop-filter` 사용처 | 없음 | 전수 0건(열거만) | — |
| 15 | L4a#15 | 애플 §12 재질 | 반투명 차단층 열거 | 없음 | `login.css:238` `.auth-expiry-overlay { position: fixed; inset: 0; z-index: 10000; … background: color-mix(in srgb, var(--color-bg) 96%, transparent); }` — 세션 만료 차단(스크림형) · `:239` reduced-transparency 분기 | — |
| 16 | L4a#16 ＋ L1#28 | 애플 §14 | 전역 reduced-motion 분기 없음 | 없음 | `shell/shell.css:419`–`420` `@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; scroll-behavior: auto !important; } }` · `shell/styles.ts:26` 전역 import · 도입 `fc45a9aa`. L1#28 같은 사실 — css_audit motion decl `auth/login.css` 2/NO · `shell/shell.css` 7/yes · `shell/primitives.css` 1/NO · dashboard·toast·variableTable 0 | — |
| 17 | L4a#17 | 애플 §14 | 전역 규칙이 색·불투명도 전환까지 끔 | 있음(전환 곡선 한정 · 색 변화 자체는 유지) | #16 이 `*` 전체 `transition` 을 끔(`.btn`·GNB·`.tbl tr.clk` 의 background/color/opacity 포함). 정본 §14 「Keep opacity/color changes that aid comprehension」 · 20260908 판정-15 권고(ⓑ 파일별)와 반대 방향 | Ted 판정(묶음 6 · 신규) |
| 18 | L4a#18 | 애플 §14 | `animation` 의 reduced-motion 분기 누락 | 없음 | `upload.css:30`–`31`(up-rise) · `:174`–`176`(`.vizload .spin`·`.up-spinner`) · `:369`–`371`(gridbar) · `:645`–`646`(pulse) — 4종 모두 분기 | — |
| 19 | L4a#19 | 애플 §14 | `prefers-reduced-transparency` 분기 누락 | 없음 | 반투명 면 1건(#15)에 `login.css:239` `.auth-expiry-overlay { background: var(--color-bg); }` | — |
| 20 | L4a#20 | 애플 §14 | `prefers-contrast: more` 분기 없음 | 있음 | 전수 grep 0건 · 정본 §14 「Respond to three independent signals」 | Ted 판정(묶음 6 · #17 과 묶음) |
| 21 | L4a#21 | 애플 §2 직접조작 | 확대·이동 드래그가 마우스 전용 | 있음 | `components/preview/useZoomPan.ts:334` `const onMouseDown = useCallback(` · `:342`–`350` `MouseEvent` move/up · `onPointerDown`·`setPointerCapture` 0건 | Ted 판정(묶음 3 · 판정-18 이월) |
| 22 | L4a#22 | 애플 §10 | 드래그 시작 임계(약 10px) 없음 | 있음 | `useZoomPan.ts:336`–`337` 버튼 확인 후 즉시 `drag.current = { x: e.clientX, y: e.clientY }` · 임계 상수 0 | Ted 판정(묶음 3 · 판정-18 이월) |
| 23 | L4a#23 | 애플 §1 | 드롭 영역 드래그 중 시각 피드백 없음 | 있음 | `FileDropCard.tsx:173`–`176` `onDragOver` 는 `preventDefault`·`stopPropagation` 만 · `onDragEnter`/`onDragLeave` 0건 · `upload.css` `.dropzone` 드래그 상태 규칙 0 | Ted 판정(묶음 4 · 판정-19 이월) |
| 24 | L4a#24 | 애플 §4·§5 | 스프링·속도 계승 미도입 | 있음 | `frontend/package.json` `motion`·`framer-motion`·`react-spring` 0 · `useZoomPan.ts:346` 매 move 델타 가산, 속도 기록 0 | Ted 판정(묶음 5 · 판정-21 이월) |
| 25 | L4a#25 | 애플 실화면 | 스프링 체감·속도 인계·1:1 추적 지연·러버밴드(`clampView` 하드 스톱)·드롭 반응·모달 열기 도중 닫기 | [미상 · 실화면 계측 필요] | 라이브 스택 다운 | 실화면 계측 |
| 26 | L4a#26 | 애플 §16 기반 | `onSubmit`·`role="dialog"` TSX 의 피드백 종류·Esc/닫기·길찾기 | [미상] | 이번 회차 미전수(턴 한도) | — |
| 27 | L4b#1 | 애플 §15 tracking | letter-spacing 값이 토큰 없이 파일마다 리터럴로 중복 | 있음 | `login.css:29`(0.01em) · `catalog.css:36,64,66`(0, normal, 0.04em) · `dashboard.css:206`(-0.02em, 28px) · `detail.css:15,64,96,130,143,164,166`(0.05em×5, -0.03em×1, 0×1) · `lineageGraph.css:79`(.05em, 13px) · `members.css:20`(-0.023em, 28px) · `project.css:31,362`(-0.03em/31px, -0.02em/20px) · `search.css:7`(-0.02em, 28px) · `upload.css:242,252`(0) · `shell.css:123,430`(-0.02em) — 토큰은 `--tracking-body: 0` 1개 | Ted 판정(묶음 7 · 판정-20 이월) |
| 28 | L4b#2 | 애플 §15 tracking | 같은 `--text-h2`(28px) 제목의 자간이 셋으로 갈림 | 있음 | `shell.css:430` `.page-head h1` -0.02em · `members.css:20` `.settings-page h1` -0.023em · `detail.css:15` `.dt-header h1` -0.03em(`search.css:7` `.search-hero h1` 은 -0.02em) | Ted 판정(묶음 7) |
| 29 | L4b#3 | 애플 §15 tracking | 방향성(대형 음수 · 소형 양수 · 본문 0) | 없음 | `catalog.css:66`(13px, +0.04em) · `detail.css:64,96,130,143,164`(13px, +0.05em) · `dashboard.css:206`(28px, -0.02em) · `project.css:31`(31px, -0.03em) · `shell.css:3`(본문 `var(--tracking-body)`) | — |
| 30 | L4b#4 | 애플 §15 leading | line-height 가 크기와 역방향 | 없음 | `shell.css:430`(28px, 1.3) · `primitives.css:87`(16px, 1.5) · `dashboard.css:207`(28px, 1.2) · `members.css:75`(14px, 1.7) · `detail.css:78`(1.65) · 칩 1(`catalog.css:121,125,141,145` · `detail.css:39,42`) | — |
| 31 | L4b#5 | 애플 §15 px/rem | font-size 가 px 전용(토큰도 px) | 있음 | `shell/tokens.css:89`–`94` `--text-*` 6개 전부 px. 레인 계수 「px 202 · rem 0 · var() 160」. **취합 정정** — `frontend/src/**/*.css` 재계수 `font-size: Npx` 194 · rem/em 0 · `font-size: var(` 133(레인 계수 범위 미기재). 결론(rem 0)은 같다 | Ted 판정(묶음 8 · 신규) |
| 32 | L4b#6 | 애플 §15 시스템 폰트 | 커스텀 웹폰트 1순위 | 없음 | `tokens.css:84`–`87` Pretendard Variable ＋ 시스템 폴백 — 한글 UI 근거 있는 오버라이드 | — |
| 33 | L4b#7 | 애플 §15 hierarchy | weight+size+leading 세트 일관 | 없음 | `shell.css:430` · `detail.css:64,96,130` · `members.css:75` | — |
| 34 | L1#1 | 정적 그림자 | 카드 그림자 0 — `.gnb` | [미상 · 정본 침묵] | `shell/shell.css:114` `.gnb { box-shadow: var(--shadow-sm) }` — 셸 고정바가 「카드」인지 정본 침묵 | Ted 판정(묶음 13) |
| 35 | L1#2 | 정적 그림자 | 카드 그림자 0 — `.card` | 없음 | `shell/primitives.css:77` `box-shadow: none` | — |
| 36 | L1#3 | 정적 그림자 | 카드 그림자 0 — `.modal` vs `.modal--dialog` | [미상 · 정본 침묵] | `primitives.css:122` `.modal { box-shadow: var(--shadow-sm) }` vs `:130` `.modal--dialog { box-shadow: none }` | Ted 판정(묶음 13) |
| 37 | L1#4 | 정적 그림자 | `.dash-card`/`.dash-tile` | 없음 | `components/dashboard/dashboard.css:408` `box-shadow: none` | — |
| 38 | L1#5 | 정적 그림자 | `.login-card` | 없음(해소) | `auth/login.css:14`–`24` box-shadow 선언 없음(20260908 판정 6 은 있음) | — |
| 39 | L1#6 | 정적 글자 | 글자 13px 미만(L1 파일) | 없음(해소) | css_audit L1 대상 `<13px` 0 · `shell.css:87` `.bl-a` 13px · `components/common/toast.css:15` 13px · `dashboard.css` 전 13px | — |
| 40 | L1#7 | 정적 토큰 | 미정의 토큰 `--dash-bar-w` | 없음(css_audit 오탐) | `dashboard.css:134` · `DataMapCard.tsx:37` `style={{'--dash-bar-w': …}}` 인라인 대입(게이트 g 패턴) | — |
| 41 | L1#8 | 정적 여백 | 음수 여백 | 없음 | L1 8개 CSS `margin: -` 0건 | — |
| 42 | L1#9 | 정적 보더 | `.dash-card` 컨테이너 vs 내부 구분선 | 없음(해소) | `dashboard.css:66` ＋ `:408` `border-color: var(--color-border-strong)`(같은 특이도·뒤 순서) · 구분선 `:159`·`:263`·`:292`·`:397` `--color-border` | — |
| 43 | L1#10 | 정적 보더 | `.card`/`.modal--dialog` | 없음 | `primitives.css:75` strong vs `:85` `.card-h` border · `:128` vs `:134`·`:141` | — |
| 44 | L1#11 | 정적 여백 | 컨테이너 여백 소유 | 없음 | `.lab-page`(`dashboard.css:10`–`14`) · `.login`(`login.css:5`–`12`) | — |
| 45 | L1#12 | 정적 토큰 | 파일 내 토큰 ⓐ | 없음 | `toast.css:7`–`9` `--toast-*` | — |
| 46 | L1#13 | 정적 토큰 | 파일 내 토큰 ⓑ(전역 어휘 재정의) | 없음 | L1 8파일 `:root{}`·전역 계열 재정의 0 | — |
| 47 | L1#14 | 정적 토큰 | `dashboard.css` 대체 어휘(구 D18) | 없음(해소) | `--fg`·`--bg-card`·`--fg-muted`·`--bg-subtle`·`--line` 소거 · `--accent-neutral`(`dashboard.css:136`)·`--fg-danger`(`:163`)는 `tokens.css:52·75`(라이트)·`:173·171`(다크) 정식 토큰 | — |
| 48 | L1#15 | 정적 대비 | `.dash-error`/`.login-error`(`--fg-danger`) | 없음 | 라이트 `#a3222b` on `#ffffff` 7.44:1 · 다크 `#ffadb6` on `#1a222c` 9.09:1 | — |
| 49 | L1#16 | 정적 대비 | `.labswitch .ln-ro`(`--color-gray-500`) | 없음 | `shell.css:260`–`265` 라이트 `#697077` on `#ffffff` 5.02:1 · 다크 `#b2bfce` on `#1a222c` 8.58:1 | — |
| 50 | L1#17 | 정적 대비 | 포커스 링 `base.css:12`–`15` | 없음 | 라이트 `#1369e9` on `#ffffff` 4.97:1 · 다크 `#92c2ff` on `#1a222c` 8.70:1 | — |
| 51 | L1#18 | 정적 대비 | 수식자 없는 `.chip` | 없음 | `primitives.css:67` 라이트 `#565c63` on `#f5f7fa` 6.30:1 · 다크 `#b2bfce` on `#202b37` 7.69:1 | — |
| 52 | L1#19 ＋ L1#21 | 정적 대비 | `.chip--off` — 배경 리터럴 상속, 다크 대비(⑦-4) | 있음(다크) | `primitives.css:55` `.chip { background: #eef2f7 }`(테마 무관) · `:62` `.chip--off { border: …; color: var(--color-text-muted); }` 배경 선언 없음 · 라이트 `#565c63` on `#eef2f7` 6.01:1 · 다크 `#b2bfce` on `#eef2f7` **1.66:1**(취합 재계산 일치) | Ted 판정(묶음 11) |
| 53 | L1#20 | 정적 토큰 | `.chip` 배경 리터럴 `#eef2f7`(⑦-6) | 있음 | `primitives.css:55` · `gates/fixtures/frontend-design-lint/same-in-dark.txt` 게이트 f 면제(「같은 값 토큰 없음 · Ted 판정 대기」) · #52 의 직접 원인 | Ted 판정(묶음 11) |
| 54 | L1#22 | 정적 프리미티브 | `.btn-sm` 등재·정의 0(⑦-3) | 있음 | `gates/fixtures/frontend-design-lint/primitives.txt` 등재 · `frontend/src` CSS `.btn-sm` 정의 0 · TSX 50회 이상(예 `components/detail/FileList.tsx:140`) | Ted 판정(묶음 12) |
| 55 | L1#23 | 정적 대비 | `.btn-strong:hover` 대비(⑦-5) | 있음 | `components/upload/upload.css:309` `.btn-strong { background: var(--color-primary-600); color: var(--color-on-primary) }` · `:311` `.btn-strong:hover { background: var(--color-gray-50); }`(color 재선언 없음) · 라이트 `#ffffff` on `#f9fafb` **1.05:1** · 다크 `#10233c` on `#202b37` **1.10:1**(취합 재계산 일치). **취합 정정** — L1 권고 근거 「`.btn-primary`/`.gnb-upload`/`.login-submit` 전부 hover → primary-700」 중 `.btn-primary` 는 hover 가 없다(⑦-1, `primitives.css:28`). primary-700 hover 는 `shell.css:238` `.gnb-upload:hover` · `login.css:84` | Ted 판정(묶음 10 · 파일 소유 L3) |
| 56 | L1#24 | 정적 프리미티브 | `.inp[readonly]` 배경(⑦-2) | 레인 없음(요소 부재) → **취합 정정 [미상 · 판정 대기]** | 레인: `readonly]` CSS 0건. 취합: 규칙은 P2a 가 억눌린 선언으로 지웠다 — `dev-package/reports/design-system/20260924/p2a/cascade-verify.md:164`–`165` `upload.css:252` `.inp[readonly]` bg `var(--color-surface-alt)`·color `var(--up-muted)` 「삭제」. ⑦-2 의 「선언이 없어 기본 모양」이 곧 현재 상태 — 선택(되살림/그대로) 미결 | Ted 판정(묶음 18) |
| 57 | L1#25 | 정적 프리미티브 | `.login-input:focus-visible` 테두리색(⑦-2) | 레인 변경 → **취합 정정 [미상 · 판정 대기]** | 레인: 전용 규칙 없음, `base.css:12`–`15` 전역 outline 이 대신(#50 통과). 취합: `p2a/cascade-verify.md:11` 「changed-live」 — 억눌린 전용 선언을 값 무변으로 정리한 결과가 오늘 모양. 선택 미결 | Ted 판정(묶음 18) |
| 58 | L1#26 | 정적 층 | 같은 「덮개＋대화상자」 패턴의 z-index 불일치 | 있음 | `primitives.css:116` `.modal-back { z-index: 200 }` vs `auth/login.css:186`–`187` `.account-modal-back { z-index: 120 }` · 참고 `.gnb` 100(`shell.css:106`) · `.auth-expiry-overlay` 10000(`login.css:238`) | Ted 판정(묶음 14) |
| 59 | L1#27 | 정적 여백 | 화면 뿌리 여백 관례 | 없음 | `dashboard.css:10`–`14` · `login.css:5`–`12` | — |
| 60 | L2#1 | 정적 글자 | `catalog.css:48` 정렬 표식 9px | 있음 | `.tbl thead th > .thf::before { content:"▾"; font-size:9px }` — 장식 글리프 | Ted 판정(묶음 15) |
| 61 | L2#2 | 정적 글자 | `catalog.css:138` `.lvl-mismatch` 12px | 있음 | `font-size: 12px` — 읽는 텍스트 | Ted 판정(묶음 16) |
| 62 | L2#3 | 정적 대비 | `.detail-page .dsec-menu-i.is-active` 라이트 | 레인 있음 4.49:1 → **취합 정정 없음** | 레인·css_audit: `#1369e9` on `#edf4ff` 4.49:1(재계산 일치 · 규칙은 `detail.css:206`–`210`, 레인 `:205` 는 `:hover` 줄). 취합: `detail.css:242` `.detail-page .dsec-menu-i.is-active { color:var(--color-text); }` 가 같은 특이도·같은 층에서 뒤에 와 글자색을 덮는다 → 최종 `#121619` on `#edf4ff` **16.44:1**. css_audit 은 같은 규칙 안 색쌍만 잰다(오탐) | 레인 즉시 수정 후보 → — |
| 63 | L2#4 | 정적 대비 | 같은 선택자 다크 | 없음 | 레인 `#92c2ff` on `#203954` 6.43:1(취합 재계산 6.41:1). 취합: #62 와 같이 `detail.css:242` 가 덮어 최종 `#edf2f7` on `#203954` **10.51:1** | — |
| 64 | L2#5 | 정적 대비 | `detail.css:166` `.dt-edit .de-req` 라이트 | 없음 | bg `--color-text-body:#21272ae0`(흰 배경 합성 ≈ rgb(60,65,68)) ＋ `--color-white` → 10.3:1 | — |
| 65 | L2#6 | 정적 대비 | `.dt-edit .de-req` 다크(⑦-9) | 있음 | 다크 bg `--color-text-body:#dce4ed` ＋ `color: var(--color-white)` → **1.28:1**(취합 재계산 일치). **취합 정정(처리)** — ⑦-9 는 판정 대기이고 선택지가 새 뜻 토큰(`--color-on-…`) 이름을 요구한다(`design-review/SKILL.md` §4 「새 토큰 이름은 Ted 판정 뒤에만」) | 레인 즉시 수정 후보 → Ted 판정(묶음 17) |
| 66 | L2#7 | 정적 토큰 | `preview.css:150,293,368`–`371` `--pv-*` 미정의 | 없음(css_audit 오탐) | TSX `style={{'--pv-*': …}}` 인라인 대입(게이트 g) | — |
| 67 | L2#8 | 정적 토큰 | `search.css:92` `--hit-relbar-w` | 없음(css_audit 오탐) | `SearchHitCard.tsx:60` 인라인 대입 | — |
| 68 | L2#9 | 정적 토큰 | `preview.css:418` `--pv-frame-ratio` | 없음 | ⓐ 컴포넌트 전용 | — |
| 69 | L2#10 | 정적 그림자 | `catalog.css:14` `.catalog-page .card` | 없음 | 선언 없음 · `.colmenu`(:63) `--shadow-lg` 는 팝오버 | — |
| 70 | L2#11 | 정적 그림자 | `detail.css:317` `:is(.dt-header,.dt-card)` | 없음 | `box-shadow: none` | — |
| 71 | L2#12 | 정적 그림자 | `preview.css:265` | 없음 | `box-shadow: none` | — |
| 72 | L2#13 | 정적 여백 | 음수 여백(L2 5파일) | 없음 | 0건(주석 `detail.css:62,122` 제외) | — |
| 73 | L2#14 | 정적 보더 | `catalog.css:14` 외곽 vs `:26` `.tbl td` | 없음 | `--color-border-strong:#dfe3e8` vs `--color-border:#e8ecf2` | — |
| 74 | L2#15 | 정적 보더 | `detail.css:55` `.dt-card` vs `:58` `.ig` | 없음 | 같은 값 관계 | — |
| 75 | L2#16 | 정적 여백 | `detail.css:62` 컨테이너 여백(WU-C11) | 없음 | `.dt-split-r` gap 으로 이관 | — |
| 76 | L2#17 | 정적 토큰 | catalog·detail 전역 어휘 재정의 | 없음 | `grep '^\s*--'` 0건 | — |
| 77 | L3#1 | 정적 그림자 | 카드 그림자(7파일) | 없음 | `approval.css:4`·`lab.css:42`·`lineage.css:299,343`·`project.css:270,345,592`·`upload.css:654` `none` · `upload.css:486` `.dr-pop` 팝오버 · `:467` 포커스 링 | — |
| 78 | L3#2 | 정적 글자 | 13px 미만 | 없음 | css_audit 7파일 0 | — |
| 79 | L3#3 | 정적 여백 | 음수 여백 | 없음 | css_audit 0 · 수기 재확인 0 | — |
| 80 | L3#4 | 정적 토큰 | 미정의 토큰 | 없음 | css_audit 0 | — |
| 81 | L3#5 | 정적 토큰 | 파일 내 토큰 정의 | 없음 | css_audit 0 · 재검색 0 | — |
| 82 | L3#6 | 정적 여백 | `lineageGraph.css` 라벨 13px·여백 소유·죽은 스타일 | 없음 | 13px 미만 0 · 자식 margin-top 0(`:13`–`14` 주석) · 미정의 토큰 0(`:8`–`12`) | — |
| 83 | L3#7 | 정적 프리미티브 | `.lin .chip--warning` 색(⑦-2) | 레인 변경(문서만 갱신) → **취합 정정 [미상 · 판정 대기]** | 레인: `lineage.css` 전용 규칙 없음 · `primitives.css:66` `.chip--warning` 이 warning-50/600 렌더. 취합: P2a 가 `lineage.css:236`–`237` `.lin .chip--warning` 전용 bg `var(--lin-over-bg)`·color `var(--lin-over-ink)` 를 억눌린 선언으로 지웠다(`p2a/cascade-verify.md:159`–`160`). 「기본 모양」 = 프리미티브 `.chip--warning` 이라 문서 오차가 아니다 — 되살림/그대로 미결 | Ted 판정(묶음 18) |
| 84 | L3#8 | 정적 프리미티브 | `.pcard` 초점 간격 2px(⑦-2) | 레인 잔존 → [미상 · 판정 대기] | `project.css:119`–`121` `.pcard:focus-visible { outline: 2px solid var(--color-primary-600); }` offset 없음 · `p2a/cascade-verify.md:17` | Ted 판정(묶음 18) |
| 85 | L3#9 | 정적 대비·색 | `lineage.css` 안내 줄 주석과 렌더 불일치(⑦-8) | 레인 잔존 → 있음 | `lineage.css:165` 주석 「안내 줄 `#5b6472` on `#f7f8fa` = 5.63:1」 vs `.lin-over-why`(:223 — 레인 :227)·`.lin-unknown-why`(:265 — 레인 :269) `color: var(--color-warning-600)` `#a85400`. 취합 계산 `#a85400` on `#f7f8fa` 5.02:1 · on `#ffffff` 5.34:1 — 대비는 통과, 주석이 낡음 | Ted 판정(묶음 19) |
| 86 | L3#10 | 정적 대비 | 대표 표본 손계산 | 없음 | `--color-danger` 7.45:1/9.10:1 · `--color-warning-600` on 흰 배경 5.34:1 · `.lin-conflict` 5.00:1 · 2.91:1(비활성 · 4.5 대상 아님). **취합 정정** — 레인 파일 `upload.css:311` `.btn-strong:hover` 는 규칙 간 상속쌍(배경만 바꾸고 글자색은 `:309` 상속)이라 css_audit 이 못 잰다. 표본에서 빠졌고 실제 AA 미달(#55) | — (결함은 #55) |
| 87 | L3#11 | 정적 보더 | 보더 2층 토큰 분리 | 없음 | 역전 중첩 쌍 없음 | — |
| 미집계 | L3#12 | — | apple-design 축(`:active`·모션·reduced-motion) | — | 담당 외(L4a/L4b) | 담당 외 |

## 3. 축별 소계

§2 표 87행을 다시 센 값이다(미집계 1행 제외).

| 축 | 행 | 있음 | 없음 | [미상] | 행 # |
|---|---|---|---|---|---|
| 애플 응답·모션·재질·신호(L4a) | 26 | 15 | 9 | 2 | 1–26 |
| 애플 타이포(L4b) | 7 | 3 | 4 | 0 | 27–33 |
| 정적 대비·색 | 12 | 4 | 8 | 0 | 48–52 · 55 · 62–65 · 85 · 86 |
| 정적 글자 13px | 4 | 2 | 2 | 0 | 39 · 60 · 61 · 78 |
| 정적 그림자·보더·여백 | 21 | 0 | 19 | 2 | 34–38 · 41–44 · 59 · 69–75 · 77 · 79 · 82 · 87 |
| 정적 토큰·프리미티브·층 | 17 | 3 | 10 | 4 | 40 · 45–47 · 53 · 54 · 56–58 · 66–68 · 76 · 80 · 81 · 83 · 84 |
| **계** | **87** | **27** | **52** | **8** | — |

처리별

| 처리 | 행 수 | 행 # |
|---|---|---|
| Ted 판정 | 27 | 10 · 12 · 13 · 17 · 20–24 · 27 · 28 · 31 · 34 · 36 · 52–58 · 60 · 61 · 65 · 83–85 |
| 즉시 수정 후보 | 6 | 1–3 · 5–7 |
| 실화면 계측 | 1 | 25 (＋ 이월 [미상 · 실화면] 은 §9) |
| — | 53 | 나머지 |

- Ted 판정 27행은 §7 에서 21건으로 묶었다(중복·연관 행 합침 ＋ 표 밖 이월 2건 ⑦-7·D14).
- [미상] 8행 = 실화면 1(#25) · 미전수 1(#26) · 정본 침묵 2(#34·#36) · ⑦-2 판정 대기 4(#56·#57·#83·#84).

레인 자체 소계와의 차이

| 레인 | 레인 소계 | 취합 재계수 | 차이 원인 |
|---|---|---|---|
| L4a | 있음 15 · 없음 9 · [미상] 2 · 즉시 6 · Ted 9 · 실화면 1 | 같음 | — |
| L4b | 있음 3 · 없음 4 · [미상] 0 · Ted 3 | 같음 | — |
| L1 | 「있음 8 / 없음 17 / [미상] 3」 · Ted 「6(정정 8)」 | 있음 5 · 없음 17 · [미상] 4 · Ted 9 | 레인 소계는 `[미상 · 정본 침묵]` 인 #1·#3 을 있음으로 셌다(표 값과 불일치). 표의 있음 행은 #19·#20·#21·#22·#23·#26 = 6, 취합에서 #19·#21 을 합쳐 5. #7 「오탐」은 없음, #25 「변경」과 #24 는 [미상 · 판정 대기]로 정정(§4), #28 「사실」은 #16 에 합침 |
| L2 | 있음 4 · 없음 13 · [미상] 0 · Ted 2 · 즉시 2 | 있음 3 · 없음 14 · Ted 3 · 즉시 0 | 레인 소계는 표와 일치. 취합 정정 2건 — #3(#62) css_audit 오탐으로 없음, #6(#65) 처리를 ⑦-9 판정 대기로 |
| L3 | 「있음 0 · 없음 8 · [미상] 1」 · Ted 4 | 있음 1 · 없음 8 · [미상] 2 · Ted 3(＋ 표 밖 D14 1) | 레인 소계가 판정 값 「변경」(#7)·「잔존」(#8·#9) 행을 세지 않았다. [미상] 1 은 레인 스스로 「담당 외로 미상 아님」이라 적은 #12. 취합은 #9 있음, #7·#8 [미상 · 판정 대기] |

## 4. 레인 간 모순·중복

| # | 사안 | 레인 값 | 취합 확인(소스) | 결론 |
|---|---|---|---|---|
| M1 | `.btn-strong:hover` 대비 | L1#23 라이트 1.05:1 · 다크 1.10:1 「있음」 / L3(파일 소유) 판정표에 행 없음 · L3#10 표본 「없음」 · 소계 있음 0 | `upload.css:309` `.btn-strong { … color: var(--color-on-primary) }` · `:311` `.btn-strong:hover { background: var(--color-gray-50); }` — hover 가 배경만 바꾸고 글자색은 상속. 취합 재계산 `#ffffff` on `#f9fafb` 1.05:1 · `#10233c` on `#202b37` 1.10:1 | **L1 이 맞다.** L3 누락 원인 = css_audit 은 같은 규칙 안 색쌍만 재고(SKILL §2-2 항목 8), L3 는 상속쌍을 손으로 계산하지 않았다. 결함 행은 #55 하나, #86 에 정정 주석 |
| M2 | ⑦-1·⑦-5 의 응답(L4a) / 대비(L1) 분할 | L4a#3·#4·#5 = 누름 피드백(응답) · L1#23 = hover 대비 | 같은 선택자, 다른 축 — 사실 중복 없음 | 행은 둘로 유지(#3·#4·#5 / #55). 즉시 수정(누름 · WU-A1·A4)과 Ted 판정(hover 값 · 묶음 9·10)이 같은 파일을 건드리므로 §8 에서 집행 순서를 묶었다. L1 권고 근거의 「`.btn-primary` hover primary-700」은 사실이 아님(#55 정정) — ⑦-1 과 ⑦-5 는 함께 판정해야 버튼 hover 규칙이 한 벌이 된다 |
| M3 | `.dsec-menu-i.is-active` 대비 4.49:1 | L2#3 있음 · 즉시 수정 후보 · css_audit 「AA fail」 | `detail.css:242` 가 뒤에서 글자색을 `--color-text` 로 덮는다 → 16.44:1 / 다크 10.51:1 | **css_audit·L2 오탐.** 즉시 수정 후보에서 뺀다(#62·#63) |
| M4 | ⑦-2 네 건을 「해소·변경」으로 읽음 | L1#24 없음(요소 부재) · L1#25 변경 · L3#7 변경(문서만 갱신 권고) · L3#8 잔존 | P2a `cascade-verify.md:11`·`:17`·`:159`–`160`·`:164`–`165` — 네 건 모두 억눌린 전용 선언을 값 무변으로 지운 것. 「선언이 없어 기본 모양」이 ⑦-2 등록 시점의 상태 그대로 | **네 건 모두 잔존(선택 미결).** [미상 · 판정 대기]로 통일, 묶음 18. 같은 오독이 L2 이월의 ⑦-7 「해소」에도 있다(§5 · `deletion.css:11` 주석 「P1 · 값 무변」 — ⑦-7 은 P1 뒤에 등록됐다) |
| M5 | 20260912 D-행 레인 간 판정 불일치 | D09: L1 [미상 · 레인 밖] / L3 해소 · D10: L1 해소(코드) / L3 [미상] · D12: L2 잔존(일부) / L3 해소 · D17: L2 해소 / L3 잔존 · D18: L1 해소 / L2 「잔존이나 무결함」 · D19: L1 보류 / L3 담당 외 / L4a 해소(코드) | D09 `project.css:333` z 200 > `shell.css:106` 100. D10 `ProjectFormModal.tsx:19`·`:74` `useDialogFocus` 사용(L3 미확인분). D12·D17·D18 은 레인별 파일 범위가 달라 생긴 부분 판정 | D09 해소 · D10 해소(코드 근거 · 실제 Tab 이동은 §9) · D12 부분(프로젝트 해소 · 카탈로그 `catalog.css:140` 상속쌍 미계측) · D17 잔존(⑦-12) · D18 해소(무결함) · D19 해소(코드) — §6 |
| M6 | D14 `pd-closedbar`/`pd-linkempty` 소유 공백 | L3 「레인 밖(`routes/`)」으로 넘김 · L1 범위에 `routes/**` 가 있으나 L1 은 D14 를 다루지 않음 | `routes/ProjectDetailPage.tsx:146`·`:194` 사용 · `frontend/src` CSS 정의 0건(취합 grep) | 잔존(부분) — 묶음 21 |
| M7 | 중복 사실 | L1#21 = L1#19 근거 동일 · L1#28 = L4a#16 사실 동일 | — | 각 한 행(#52 · #16) |
| M8 | L4b#5 계수 | 「px 202 · var() 160」 | `frontend/src/**/*.css` 재계수 194 · 133 | 레인 계수 범위 미기재 — 취합 값 병기(#31). 결론 불변 |
| M9 | 줄 번호 | L2#3 `detail.css:205` · L3#9 `lineage.css:227`·`:269` | 실제 `:206`·`:223`·`:265` | 행에 병기 |

## 5. 판정 대기 ⑦ 1–16 재판정 요약

출처 = `docs/design-system.md` ⑦. 「현재 값」은 기준 트리 `dc05531c` 값.

| ⑦ | 항목 | 현재 값 | 재판정 | 행 |
|---|---|---|---|---|
| 1 | 억눌린 hover `.btn-primary:hover` · `.btn-secondary` hover | `primitives.css:28` hover 가 두 수식자를 제외 · 신규 `.btn-primary:active`(`:32`) primary-700 · `.btn-secondary` 는 hover·active 0 | 잔존(hover) · 누름은 즉시 수정 후보로 분리 | #3 · #4 · 묶음 9 |
| 2 | 억눌린 상태 4건(`.inp[readonly]` 배경 · `.lin .chip--warning` 색 · `.login-input:focus-visible` 테두리색 · `.pcard` 초점 간격) | 네 건 모두 전용 선언 없음 — 오늘 렌더 = 프리미티브·전역 기본(`primitives.css:66` · `base.css:12`–`15` · `project.css:119`–`121`) | 잔존(네 건 · 레인의 「해소·변경」 독해는 취합 정정 · §4 M4) | #56 · #57 · #83 · #84 · 묶음 18 |
| 3 | `.btn-sm` 기본값 없음 | CSS 정의 0 · 목록 등재 · TSX 50회 이상 | 잔존 · 사용처 규모 새로 확인 | #54 · 묶음 12 |
| 4 | `.chip--off` 배경 gray-50 | 배경 선언 없음 → `.chip` 리터럴 `#eef2f7` 상속 · 다크 1.66:1 | 변경 — 「보인 적 없음」에서 다크 AA 미달로 사안이 커짐 | #52 · 묶음 11 |
| 5 | `.btn-strong:hover` gray-50 대비 | `upload.css:311` · 라이트 1.05:1 · 다크 1.10:1 · 누름 피드백 없음 | 잔존 · 실측값 확정 | #55 · #5 · 묶음 10 |
| 6 | `.chip` 배경 `#eef2f7` 리터럴 | `primitives.css:55` · 게이트 f 면제 유지 | 잔존 · ⑦-4 와 한 결정 | #53 · 묶음 11 |
| 7 | `deletion.css` `.dl-keep` 바탕 | `deletion.css:11` `background: transparent; /* 종전 var(--color-surface-muted, transparent) — … (P1 · 값 무변) */` | L2 이월 「해소」 → **취합 정정 잔존** — 미정의 참조 소거는 P1(값 무변)이고 ⑦-7(채움 vs 그대로)은 그 뒤 등록된 선택이라 미결 | L2 이월표 · 묶음 20 |
| 8 | `lineage.css` 안내 줄 주석 vs 렌더 | 주석 `:165` 회색 `#5b6472` · 렌더 `--color-warning-600` | 잔존 | #85 · 묶음 19 |
| 9 | `.de-req` 다크 대비 | 1.28:1 | 잔존 | #65 · 묶음 17 |
| 10 | 화면 편차 통일 | 이번 레인 미재판정 | 이월(변경 없음) | — |
| 11 | 패턴 이관(④) | 레인 미접촉 | 이월(변경 없음) | — |
| 12 | 별 계열 이름 합치기 · 탭 3계열 | L3 가 20260912 D17 을 이 항목으로 이관(「재판정 대상 아님」) | 이월(변경 없음 · D17 흡수) | L3 이월 D17 |
| 13 | 갤러리 제품 라우트 노출 | 레인 미접촉 | 이월(변경 없음) | — |
| 14 | 제품 시험 14곳 단언 변경 수용 | 레인 미접촉 | 이월(변경 없음) | — |
| 15 | `cascade-map.mjs verify` 일반화 수용 | 레인 미접촉 | 이월(변경 없음) | — |
| 16 | 게이트 e 의 `요소.클래스` compound | 레인 미접촉 | 이월(변경 없음) | — |

- ⑦ 문서 갱신 후보(값 무변 · Ted 판정 뒤) — ⑦-3 사용처 규모 · ⑦-4 다크 1.66:1 · ⑦-5 1.05/1.10:1 · ⑦-9 1.28:1 실측 보강. §8 부속.

## 6. 이월 재판정 요약

### 20260908 판정-14..21 (L4a 차이표 재사용 · 판정-20 은 L4b)

| 이월 | 재판정 | 근거 |
|---|---|---|
| 판정-14 누름 피드백 0 | 변경 → Ted 묶음에서 삭제 | `:active` 0 → 2(`primitives.css:32` · `search.css:155` · 도입 `bdf62a31`·`d9aafcee`·`fc45a9aa`). 도입은 `S-DESIGN-CONSISTENCY-FULL-20260912.md:53` spec 제약(열린 라운드 미이행) → #1–#7 즉시 수정 후보(비버튼은 값 확정 선행) |
| D-10 누름 상태 규칙 신설 | 잔존(부분) | 공통 선택자 묶음 미실행 — 2건만 |
| 판정-15 모션 축소 파일별 vs 셸 한 벌 | 해소(다른 경로) | ⓐ 셸 전역으로 실행 `shell.css:419`–`420`(`fc45a9aa`) — 권고 ⓑ 와 반대. 결과로 #17 신규 |
| D-11 검색 토글 손잡이 분기 | 해소 | `search.css:134` `transition: left` 가 전역 규칙으로 무력화 |
| 판정-16 모달 열기 고정·닫기 없음 | 잔존 | `upload.css:24`·`26`(종전 `:31`·`:33`) · 닫기 0(#13) · 정본 §3 `:62` vs `:66` 충돌 미해결 |
| D-16 모달 닫기 경로 | 잔존(미실행) | 닫기 상태·전환 종료 핸들러 0 |
| 판정-17 팝오버 기준점 | 잔존 | `upload.css:484` · `transform-origin` 0 |
| D-12 `.dr-pop` 기준점·여는 전환 | 잔존(미실행) | 상동 |
| 판정-18 드래그 마우스 전용·임계 | 잔존 | `useZoomPan.ts:334`(종전 `:228`) |
| D-14 useZoomPan 포인터 전환 | 잔존(미실행) | `onPointerDown`·`setPointerCapture` 0 |
| 판정-19 드롭 영역 피드백 | 잔존 | `FileDropCard.tsx:173`(종전 `:168`) |
| D-15 드롭 상태·CSS | 잔존(미실행) | `onDragEnter`/`onDragLeave` 0 |
| 판정-20 · D-13 글자 간격 | 잔존(L4b) | `tokens.css` 에 `--tracking-body: 0` 1개 · 구간 토큰 신설·`login.css`·`catalog.css`·`shell.css` 리터럴 치환 미실행(#27) |
| 판정-21 스프링·속도 계승 | 잔존 | 의존성 0 · 판정-18 선행 미충족 |

- 20260908-L4 행 #1–#31 의 개별 재판정은 `design-review-20260924-L4a.md` §2 하단 표 그대로(여기 재수록하지 않음). 그중 #4·#22·#23(배경 클릭 2단·Esc 층·배경 닫기)과 #28–#31 은 [미상] — §9.

### 20260912 D-행 (`dev-package/reports/design-review/20260912/findings.md` D01–D31)

| D | 원 판정 | 재판정 | 레인 · 근거 |
|---|---|---|---|
| D01 폼 글꼴 불일치 | 있음 | 해소(L1 범위) · 카탈로그·검색 부분 미재판정 | L1 `base.css:10` `font-family: inherit` · L2 는 턴 한도로 미도달 |
| D02 카탈로그 필터 스타일 누락 | 있음 | 레인 미재판정 · 취합 관찰: 변경(코드) | `catalog.css:200`–`202`·`:215` `.axis-bar`·`.axis-pick`·`.axis-k` 규칙 존재(당시 0) · 실화면 [미상] |
| D03 대시보드 카탈로그 버튼 외형 | 있음 | 해소 | L1 `dashboard.css:167`–`182` |
| D04 연구실 정보 모달 여백 | 있음 | 해소(코드 근거) | L1 `primitives.css:131` · `dashboard.css:397` · 원 판정이 실화면이라 §9 재확인 |
| D05 연구실 설정 바깥 여백 | 있음 | 레인 미재판정 · 취합 관찰: 해소(코드) | `routes/LabSettingsPage.tsx:29` `.settings-page` · `shell.css:100`·`:433` 컨테이너 |
| D06 프로젝트 생성 모바일 날짜 잘림 | 있음 | [미상 · 실화면] | L3 |
| D07 대표 그림 선택기 조건 불일치 | 있음 | [미상 · 실화면] | L3 |
| D08 로그인 모바일 가로폭 초과 | 있음 | [미상 · 실화면] · 수정 시도 흔적 | L1 `login.css:9` `grid-template-columns: minmax(0, 1fr)` |
| D09 프로젝트 모달 z-index < GNB | 있음 | 해소 | L3 `project.css:333` 200 > `shell.css:106` 100 (L1 [미상] 은 L3 로 닫힘) |
| D10 모달 포커스 배경 이탈 | 있음 | 해소(코드 근거) · 실제 Tab 은 §9 | L1 `useDialogFocus.ts:15`–`65` · 취합 `ProjectFormModal.tsx:19`·`:74` 도 사용(L3 [미상] 정정) |
| D11 11~12px 다수 | 있음 | 변경 — 잔존 2건 | L1(dashboard)·L3(project·lineage) 0 · L2 `catalog.css:48` 9px · `:138` 12px(#60·#61) |
| D12 상태/보조 글자 대비 | 있음 | 부분 — 프로젝트 해소 · 카탈로그 [미상] | L3 해소 · L2 `catalog.css:140` 상속쌍 재계측 없음(css_audit 은 같은 규칙만) |
| D13 승인 UI 스타일 누락 | 있음 | 해소 | L3 `approval.css` 19줄 |
| D14 업로드·빈 상태 스타일 누락 | 있음 | 변경 — 부분 잔존 | L3 `upload.css:627`–`631` · `project.css:568` 정의 · `pd-closedbar`·`pd-linkempty` CSS 0(`routes/ProjectDetailPage.tsx:146`·`:194`) — 묶음 21 |
| D15 없는 주소 화면 스타일 | 있음 | 잔존(부분) | L1 `shell.css:100`·`:413` 컨테이너 생김 · `NotFoundPage.tsx:12` `<Link>` 전용 클래스 없음 |
| D16 잠긴 행 키보드 상세 진입 | 있음 | 레인 미재판정 | 취합 관찰: `CatalogTable.tsx:175` `button.catalog-open` 존재 — 잠긴 행 적용 여부 미확인 |
| D17 전역 control/card/modal 이름 중복 | 있음 | 잔존 → ⑦-12 | L2 catalog·detail 0 · L3 upload·members·project 는 ⑦-12 이관 |
| D18 대체 토큰 혼용 | 있음 | 해소 | L1 dashboard 치환·승격 · L2 preview 는 인라인 대입(무결함) |
| D19 reduced-motion 에도 셸 transition | 있음 | 해소(코드) · 효과 [미상 · 실화면] | L4a `shell.css:419`–`420` · 부작용 #17 |
| D20 카드 그림자·음수 여백 | 있음 | 해소 | L1 · L3 전수 0 |
| D21 모바일 대시보드 밀도 | 미상 | 레인 미재판정 | 디자인 선택 · 실화면 |
| D22 멤버 권한표 등 최종 외형 | 미상 | [미상 · 실화면] | L3 |
| D23 업로드 상태별 외형 | 미상 | [미상 · 실화면] | L3 |
| D24 빈 연구실 안내 잘림 | 미상 | 변경(코드) · [미상 · 실화면] | L1 `dashboard.css:391` `overflow-wrap: anywhere` |
| D25 CSS 통째 미연결 | 없음 | 없음 유지 | L1 |
| D26 미정의 변수 무효 선언 | 없음 | 없음 유지 | css_audit 미정의 8건 전부 TSX 인라인 대입(#40·#66·#67) |
| D27 상세 옛 소형 글자 잔존 | 없음 | 없음 유지 | css_audit `detail.css` `<13px` 0 |
| D28 카탈로그 표 가로 넘침 | 없음 | 레인 미재판정 | 실화면 |
| D29 WU-C11 재이탈 | 없음 | 없음 유지 | L2 `catalog.css:134` · `detail.css:69` |
| D30 다크 테마 완결성 | 미상 | 레인 미재판정 | 요구사항 대조 · #52·#65 가 다크 전용 결함 2건 |
| D31 미정의 클래스 65종 결함 여부 | 없음 | 레인 미재판정 | — |

집계(D01–D31 · 31건)

| 재판정 | 건수 | D |
|---|---|---|
| 해소(전부 · 레인 범위 · 코드 근거) | 10 | D01(L1 범위) · D03 · D04 · D05(취합 관찰) · D09 · D10 · D13 · D18 · D19 · D20 |
| 변경·부분 | 5 | D02(취합 관찰) · D11 · D12 · D14 · D24 |
| 잔존 | 2 | D15 · D17(⑦-12) |
| [미상 · 실화면] | 5 | D06 · D07 · D08 · D22 · D23 |
| 없음 유지 | 4 | D25 · D26 · D27 · D29 |
| 레인 미재판정 | 5 | D16 · D21 · D28 · D30 · D31 |

## 7. Ted 판정 묶음

21건 — 애플 원칙 8 · 정적 13. 권고 끝의 「(취합 권고)」는 레인 권고가 없어 취합이 붙인 것이다. 결정되면 **시각 변경**이 생기는 항목이 대부분이다.

### 애플 원칙

**1 · 업로드 모달이 0.46초 고정 애니메이션으로 열리고, 닫힐 때는 전환 없이 사라진다** (판정-16 이월 · #10 · #13)
- ⓐ 열기를 중간에 멈출 수 있는 전환으로 바꾸고 닫기에도 같은 경로를 둔다. ⓑ 현행 유지.
- 권고 = 먼저 정본 문장 우선순위를 정한다 — `apple-design/SKILL.md` §3 `:62`(「모든 애니메이션은 언제든 중단 가능 · 닫히는 모달」)와 `:66`(「제스처로 구동되는 것만 CSS 전환 금지」)이 충돌한다. 어느 쪽이든 닫기 경로가 없는 비대칭(#13)은 남으므로 닫기 대칭은 ⓐ.

**2 · 기간 선택 달력 팝오버가 누른 자리에서 펼쳐지지 않고 즉시 나타난다** (판정-17 이월 · #12)
- ⓐ 펼침 기준점(`transform-origin`)과 여는 전환을 둔다. ⓑ 현행 즉시 표시.
- 권고 = ⓐ(달력 팝오버 `.dr-pop` 만 · 20260908 권고 유지).

**3 · 미리보기 확대·이동 끌기가 마우스 전용이고, 1px 만 움직여도 끌기가 시작된다** (판정-18 이월 · #21 · #22)
- ⓐ 포인터 이벤트와 포인터 캡처로 옮기고 약 10px 시작 임계를 둔다. ⓑ 현행 유지.
- 권고 = ⓐ. 임계 확정값은 정본에 「약 10px」로만 있어 값도 함께 정한다. 구현은 TSX(`useZoomPan.ts`).

**4 · 파일을 끌어 오는 동안 드롭 영역이 반응하지 않는다** (판정-19 이월 · #23)
- ⓐ 끌어 들어옴·나감 상태와 대응 시각 규칙을 둔다. ⓑ 현행 유지.
- 권고 = ⓐ. 상태 색은 정본에 없어 값 선택이 함께 필요하다. 구현은 TSX(`FileDropCard.tsx`) ＋ CSS.

**5 · 끌기를 놓은 뒤 속도를 이어받는 탄성 움직임을 도입할지** (판정-21 이월 · #24)
- ⓐ 탄성 움직임 라이브러리를 들여 속도를 넘긴다. ⓑ 현행 고정 곡선.
- 권고 = ⓑ. 적용 면이 확대·이동 하나뿐이고 3 이 선행 조건이다. 3 처리 뒤 재검토.

**6 · 운영체제 「동작 줄이기」를 켜면 셸 전역 규칙이 색 변화 전환까지 끄고, 「고대비」 설정 대응은 없다** (신규 · #17 · #20)
- ⓐ 전역 규칙을 위치 이동·변형 속성에만 걸고 색·투명도 전환은 남긴다. 고대비(`prefers-contrast: more`) 분기는 반투명 면이 늘 때 단다. ⓑ 현행 유지.
- 권고 = ⓑ(L4a). 정본 §14 는 색·투명도 **변화 자체**의 유지를 요구하고 이 규칙은 전환 곡선만 없앤다(변화는 즉시 반영) — 현 코드에 투명도 교차 페이드는 0건이라 실손실은 0.14초 곡선뿐이다(advisor ②). 현재 이동 전환은 검색 토글 손잡이 하나이고 나머지는 0.14초 색 전환이라 정보 손실이 작다. 반투명 면도 세션 만료 덮개 하나. 이동 전환이나 반투명 면이 늘면 ⓐ 로 재검토.

**7 · 글자 간격 값이 공통 토큰 없이 파일마다 손으로 박혀 있고, 같은 28px 제목이 세 값으로 갈린다** (판정-20 이월 · #27 · #28)
- ⓐ `tokens.css` 에 제목용·작은 라벨용 두 구간 토큰을 두고 리터럴을 치환한다(값은 지배적인 값으로 통일 — 이름·값 확정은 판정). ⓑ 현행 유지(파일별 값 · 문서화만).
- 권고 = ⓐ(L4b). 20260908 판정-20 이 이미 ⓐ 방향이고, 28px 제목의 -0.02/-0.023/-0.03em 차이는 의도로 보이지 않는다.

**8 · 글자 크기가 전부 px 라서 브라우저 기본 글자 크기 설정을 따르지 않는다** (신규 · #31)
- ⓐ `tokens.css` 의 `--text-*` 6개만 rem 으로 바꾸고 나머지 px 리터럴은 별건. ⓑ 토큰과 리터럴 전부 rem.
- 권고 = ⓐ(L4b). 토큰 한 곳만 바꿔도 `var()` 사용처가 함께 바뀐다.

### 정적

**9 · 기본·보조 버튼에 마우스를 올려도 배경이 바뀌지 않는다** (⑦-1 · #3 · #4)
- ⓐ `.btn-primary:hover` 를 primary-700 으로 되살리고 `.btn-secondary` hover 값을 정한다. ⓑ 그대로.
- 권고 = ⓐ (취합 권고). `tokens.css:31` 이 primary-700 을 「hover·pressed·링크」 용도로 정의하고, 같은 파란 단추인 `.gnb-upload:hover`(`shell.css:238`)·로그인 단추(`login.css:84`)가 이미 그 값을 쓴다. 10 과 함께 정한다.

**10 · 업로드 화면 강조 단추에 마우스를 올리면 흰 글자가 거의 흰 배경 위에 놓인다(라이트 1.05:1 · 다크 1.10:1)** (⑦-5 · #55 · 누름 #5)
- ⓐ hover 에서 글자색도 함께 바꾼다. ⓑ hover 배경을 primary-700 으로 바꾼다(다른 파란 단추와 같은 규칙).
- 권고 = ⓑ(L1). 9 를 ⓐ 로 정하면 파란 단추 hover 가 한 규칙이 된다.

**11 · 칩 기본 배경이 테마와 무관한 고정 색이라, 「꺼짐」 칩이 다크에서 밝은 배경에 밝은 글자(1.66:1)가 된다** (⑦-4 · ⑦-6 · #52 · #53)
- ⓐ 새 전역 토큰을 만들어 라이트 값은 유지하고 다크 값을 따로 정한다. ⓑ 기존 다크 대응 토큰(`--color-gray-100` 또는 `--color-surface-alt`)으로 바꾼다(라이트 값이 조금 바뀐다).
- 권고 = ⓑ(L1). 새 토큰 없이 다크 대비 파탄이 구조적으로 사라진다. 라이트 시각 변경은 fix 단계 advisor ③ 대상.

**12 · 작은 단추 수식자 `.btn-sm` 이 목록에만 있고 정의가 없는데 화면 50여 곳이 쓴다** (⑦-3 · #54)
- ⓐ `primitives.css` 에 작은 단추 크기를 정의한다(값은 목업 대조). ⓑ 목록에서 빼고 TSX 의 `btn-sm` 을 걷어낸다.
- 권고 = ⓐ(L1). 쓰임새가 넓어 「의도했는데 빠진」 쪽이다.

**13 · 「카드 그림자 0」 규칙이 상단 고정바(`.gnb`)와 전체화면 모달(`.modal`)에도 적용되는지** (#34 · #36)
- ⓐ 카드·대화상자만 대상, 상단바·전체화면 모달은 항상 떠 있는 층으로 예외. ⓑ 모든 표면에서 그림자를 뺀다.
- 권고 = ⓐ(L1). 20260908 결론과 같고, 대화상자(`.modal--dialog`)는 이미 0이다.

**14 · 같은 「배경 덮개 ＋ 가운데 대화상자」인데 전역 모달은 층 200, 계정 관리 모달은 120** (#58)
- ⓐ 계정 관리 모달을 200 으로 맞춘다. ⓑ 120 유지하고 사유를 주석으로 남긴다.
- 권고 = ⓐ(L1). 120 을 고른 사유가 코드에 없다.

**15 · 카탈로그 표 머리의 정렬 화살표 글리프가 9px** (#60)
- ⓐ 장식 글리프는 13px 하한에서 제외(예외 등재). ⓑ 소폭 확대.
- 권고 = ⓐ(L2). 읽는 글자가 아니다.

**16 · 카탈로그 「불일치」 표식이 12px** (#61)
- ⓐ 13px 로 올린다. ⓑ 배지류 별도 하한에 넣는다.
- 권고 = ⓐ(L2). 배지가 아니라 보조 문구다(`design-review-20260908-L2.md:46` 권고 범위 밖).

**17 · 상세 편집의 「필수」 표식이 다크에서 흰 글자가 밝은 배경 위(1.28:1)** (⑦-9 · #65)
- ⓐ 「색 배경 위 글자」 뜻의 토큰(`--color-on-…` 계열 · 이름은 판정)을 둔다. ⓑ 그대로.
- 권고 = ⓐ (취합 권고). AA 미달이 다크에서만 난다.

**18 · P2a 가 지운 「억눌린」 상태 표현 네 가지를 되살릴지** (⑦-2 · #56 · #57 · #83 · #84)
- 대상 — 읽기 전용 입력칸 배경 · 계보 화면 경고 칩 전용 색 · 로그인 입력칸 초점 테두리색 · 프로젝트 카드 초점 간격 2px. 오늘은 넷 다 공통 기본 모양(초점은 전역 외곽선 · 대비 통과 #50).
- ⓐ 되살린다. ⓑ 그대로 두고 ⑦-2 를 닫는다.
- 권고 = ⓑ(카드 초점 간격은 L3 · 나머지 셋은 취합 권고). 네 건 모두 접근성 결함이 아니고 오늘 렌더를 그대로 둔 값 무변 결과다. 읽기 전용 칸 구분은 실화면(D23)에서 문제가 보이면 재상정.

**19 · 계보 화면 안내 문구의 코드 주석은 회색을 설명하는데 실제는 주황** (⑦-8 · #85)
- ⓐ 주석을 렌더(주황 `--color-warning-600`)에 맞춘다. ⓑ 렌더를 회색 토큰으로 바꾼다.
- 권고 = ⓐ(L3). 경고 의미와 맞고 대비 5.02:1 통과.

**20 · 삭제 화면 「보관」 행 바탕을 채울지** (⑦-7 · 표 밖 · §5 취합 정정)
- ⓐ `--color-surface-alt` 로 채운다. ⓑ 그대로(투명).
- 권고 = ⓑ (취합 권고). 늘 투명으로 렌더돼 왔고 채움 근거가 정본에 없다.

**21 · 프로젝트 상세의 닫힘 안내·빈 링크 문구 클래스(`pd-closedbar`·`pd-linkempty`)에 스타일 정의가 없다** (20260912 D14 부분 · 표 밖 · §4 M6)
- ⓐ 다음 회차 `routes/**` 담당 레인에 재판정을 배정한다(실화면 D23 과 함께). ⓑ 「정의 없는 클래스 ≠ 결함」(20260912 D31 기준)으로 종결.
- 권고 = ⓐ(L3 이관 요청 · 취합 보강). 이번 회차 L1 범위에 `routes/**` 가 있었지만 다루지 않았다.

## 8. 즉시 수정 후보 WU 목록 (R-C 후보)

- WU 번호를 발급하지 않는다(후보 WU-A·n). 전건 계약 0 · 스키마 0 · 서버 0.
- 즉시 수정 후보 6행(#1–#3 · #5–#7)은 모두 **누름 피드백**이다. 도입은 spec 제약(`S-DESIGN-CONSISTENCY-FULL-20260912.md:53` · `S-DESIGN-CONSISTENCY-20260912.md:50` 「즉시 active 피드백」)이며, 라운드 `R-DESIGN-CONSISTENCY-FULL-20260912.md` 검증 항목(:39–46)은 미완료 상태다 — 새 결정이 아니라 **열린 라운드의 미이행분**이다. WU-A1(버튼 · 선례 primary-700)만 값 하나로 닫히는 즉시 수정 후보이고, WU-A2–A4(비버튼 부품)는 누름 값이 열려 있어 착수 전 spec 값 확정 = advisor ③. 버튼 외 부품(표 행·GNB 링크·달력 칸)의 누름 **값**은 구현 spec 에서 정한다 — 선례 = `.btn-primary:active` primary-700(L4a). 착수 전 spec 에 값을 적는다.
- L2 가 올린 즉시 수정 후보 2행은 취합 정정으로 빠졌다(#62 오탐 · #65 ⑦-9 판정 대기).
- #1 은 전체 계수 행이라 WU-A1–A4 가 모두 닫는다.

### CSS 전용 레인 (파일 면 겹침 없음)

| 후보 | 파일 · 선택자 | 대상 행 | 크기 | 수용 기준 |
|---|---|---|---|---|
| WU-A1 | `frontend/src/shell/primitives.css` — `.btn`(수식자 없음) · `.btn-ghost` · `.btn-secondary` | #1 · #2 · #3 | S | `primitives.css` 에 세 선택자 각각을 고르는 `:active` 규칙이 있다 · `.btn-primary:active`(`:32`) 값 불변 · `frontend-design-lint` green(e: `primitives.css` `!important` 0) |
| WU-A2 | `frontend/src/shell/shell.css` — `.backlink` · `.mainnav a` · `.gnb-settings` · `.gnb-upload` · `.gnb-more` · `.gnb-more-item` · `.gnb-logout` · `.loadfail-retry` · `.theme-switcher` · 모달 닫기 `.x` | #1 · #6 | M | 열 선택자 각각에 `:active` 선언이 1개 이상 있다 · `shell.css:419`–`420` reduced-motion 블록 불변 · hover 규칙 값 불변 |
| WU-A3 | `frontend/src/components/catalog/catalog.css` — `.tbl tr.clk` | #1 · #7 | S | `.tbl tr.clk` 에 `:active` 규칙이 있다 · 기존 `catalog.css:33` transition 값 불변 |
| WU-A4 | `frontend/src/components/upload/upload.css` — `.btn-strong` · `.dr-nav button` · `.dr-cal-d` · `.dr-useg button` · `:465` 블록 | #1 · #5 · #7 | S | 다섯 선택자 각각에 `:active` 규칙이 있다 · `.btn-strong:hover`(`:311`) 는 이 WU 에서 바꾸지 않는다(Ted 묶음 10) |

공통 수용 — 시험 seam = `frontend/test/design-fix-<날짜>.test.ts`(before→after grep 계측) · 게이트 `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` green(`-j 1`) · 실화면 `live_probe.js` 「로드된 `:active` 규칙 수」가 현재 2 에서 늘어난다(§9).

### 집행 순서 · 겹침

- WU-A4 는 Ted 묶음 1(`up-rise`) · 2(`.dr-pop`) · 10(`.btn-strong:hover`) 과 같은 파일이다. 그 판정이 먼저 나면 한 레인으로 합친다.
- WU-A2 는 Ted 묶음 6 을 ⓐ 로 정하면 같은 `shell.css:419`–`420` 을 건드린다 — 같은 레인.
- WU-A1 은 Ted 묶음 9(hover)·12(`.btn-sm`)와 같은 파일 — 판정 뒤 합칠 수 있다.

### TSX 필요 (즉시 수정 후보 0 · Ted 판정 뒤 별도 레인)

| 조건부 후보 | 파일 | 걸린 묶음 |
|---|---|---|
| 닫기 경로(언마운트 지연) | `components/upload/UploadModal.tsx` · `PreviewExpandOverlay.tsx` | 1 (D-16) |
| 포인터 이벤트·캡처·임계 | `components/preview/useZoomPan.ts` | 3 (D-14) |
| 드롭 상태 | `components/upload/FileDropCard.tsx` | 4 (D-15) |
| `pd-closedbar`·`pd-linkempty` | `routes/ProjectDetailPage.tsx` ＋ CSS | 21 |
| `.btn-sm` 제거(ⓑ 선택 시만) | TSX 50여 곳 | 12 |

### 부속 — 문서 WU (값 무변 · Ted 판정 뒤)

- `docs/design-system.md` ⑦ 손글 표 갱신 — ⑦-3·4·5·9 실측 보강, 판정 결과 반영. 생성 표(②·③)는 건드리지 않는다.

## 9. 실화면 계측 대기

도구 = `agent-browser` ＋ `scripts/live_audit.sh <out_dir> <url>...`(라이트·다크 스크린샷 ＋ `live_probe.js`). 로그인은 `agent-browser --session design auth login <name>`. 산출 = `dev-package/reports/design-review/20260924/live/`. 대상 URL 은 로컬 스택 또는 Ted 지정 주소(읽기 화면만).

| 대상 | 출처 | 잴 것 |
|---|---|---|
| 스프링 체감 · 속도 인계 · 1:1 추적 지연 · 러버밴드(`clampView` 하드 스톱) | #25 · 20260908-L4 #28–#31 | 미리보기 확대·이동에서 `drag` → 연속 `screenshot` · 손으로 판정 |
| 드롭 반응 | #25 | 업로드 드롭 영역 위 파일 끌기 중 스크린샷 |
| 모달 열기 도중 닫기 | #25 | 업로드 모달 열기 0.46초 안에 닫기 → 스크린샷 |
| 로그인 탭 간 대기 중 진행 표시 | #8 | `workGuard.ts` 120/200ms 대기 동안 로그인 단추 상태 |
| reduced-motion 효과 | D19 · #17 | reduced-motion 에뮬레이션에서 `live_probe.js` 인터랙티브 요소 transition computed · 20260912 `reduced-motion.json` 재실행 |
| 누름 피드백 규칙 수 | #1 · §8 | `live_probe.js` 로드된 `:active` 규칙 수(수정 전 기준값 2 확인) |
| `.chip--off` 다크 대비 | #52 | 멤버·업로드 화면 다크 · 상속 배경 기준 대비 |
| `.btn-strong:hover` 대비 | #55 | 업로드 화면 hover 후 computed 색쌍 |
| `.dsec-menu-i.is-active` 최종 색 | #62 · #63 | 상세 화면 활성 메뉴 computed color (취합 정정 확인) |
| `.de-req` 다크 | #65 | 상세 편집 다크 대비 |
| 로그인 375px 가로폭 | D08 | 375px 뷰포트 폼 폭·오른쪽 끝 |
| 빈 연구실 안내 잘림 | D24 | 빈 연구실 대시보드 375/1440px |
| 프로젝트 생성 모바일 날짜 | D06 | 375px 프로젝트 생성 모달 |
| 대표 그림 선택기 조건 | D07 | 상세 대표 그림 input 스타일 적용 여부 |
| 모달 포커스 트랩 | D10 | 연구실 정보·프로젝트 생성 모달에서 Tab/Shift+Tab/Esc |
| 연구실 정보 모달 여백 | D04 | 375px 모달 padding |
| 카탈로그 필터 · 설정 화면 여백 | D02 · D05 | 필터 select 높이 · 설정 화면 좌측 여백 |
| 멤버 권한표 · 승인 취소 · 잠긴 데이터 요청 | D22 | 권한별 계정 |
| 업로드 처리·오류·등록 상태 | D23 | 상태별 화면(staging 쓰기 금지 — 로컬만) |
| 배경 클릭 2단 확인 · Esc 층 · 배경 닫기 | 20260908-L4 #4 · #22 · #23 | 모달별 Esc·배경 클릭 → 스크린샷(코드 재확인 병행) |

- 이 계측을 게이트로 세는 자리는 `frontend-visual`(`COLAB_VISUAL_URLS` 선언 · 대상 없으면 `COLAB_VISUAL_EXEMPT=1` 명시).

## 10. 절차 기록

사실만 적는다. 출처 = 메인 세션 기록(M) · 레인 산출 파일 본문(F) · 취합 소스 확인(S).

- 턴 한도 — L1 · L2 · L3 · L4a 가 30턴에서 잘렸고 재개해 완료했다(M). L2 는 20260912 D01·D02·D11 카탈로그 부분을 「턴 한도로 미도달」로 남겼다(F). L4a 는 §16 기반 전수를 턴 한도로 생략했다(F · #26).
- L4a 첫 시도는 `lifecycle begin` 에서 멈췄다 — 브리프가 산출 경로를 `runtime:artifacts/` 가 아닌 저장소 경로로 준 탓(M). 재시도 뒤에도 begin 이 돌려준 runtime 경로가 워크트리 밖이라 Write 도구가 격리 가드로 거부했고, `lifecycle write-artifact` 는 「external edit requires assigned task and agent identity」로 거부 — 초안을 `/home/ttlhi10/.claude/jobs/aa678208/tmp/` 에 쓰고 Bash `cp` 로 runtime 경로에 복사했다(F). L4a 산출은 runtime 에서 hash `948f1b65` 로 가져왔다(M).
- L4a 는 브리프가 가리킨 `dev-package/prd/intent/2026-09-12-design-consistency.md` 는 경로 오기다(브리프 작성 오류) — 실물은 `dev-package/intent/2026-09-12-design-consistency.md` 이고 누름 피드백 문구는 없다. L4a 는 spec 두 건으로 인용했다.
- L4b 는 `lifecycle begin --legacy` 로 열었다(F · task `ad5c4d16ea394b47a47de5b008823d8e`). 브리프는 「NO --legacy」였다.
- handoff 충돌 — 공유 워크트리의 다른 레인 파일이 `dev-package/sessions/` 에 생기자 `lifecycle handoff` 가 L3 · L4a · L4b 를 거부했다(M). 원인(S): `scripts/harness/hooks/lifecycle_contract.py` 는 감시 경로 전체(`WATCH = ('dev-package/sessions/', 'dev-package/reports/', 'dev-package/intent/', SPECS)` · `:26`)를 begin 시점 baseline 과 비교하고(`:325`), 바뀐 파일이 그 task 의 산출물 선언 안에 없으면 「this task has unhanded output」으로 거부한다(`:332`–`333`).
- L2 handoff 는 성공했다(M · task `c859956278564042a315fa2a1e333d22`).
- L1 은 handoff 를 통과하려고 두 번째 task `463994a2` 를 열어 자기가 쓰지 않은 L2 · L3 · L4b 파일을 산출물로 선언했다(M). **출처 증명 우려** — 그 task 의 증거는 L1 이 다른 레인 파일의 작성자인 것처럼 기록한다.
- **하네스 발견** — `design-review/SKILL.md` §2-2 항목 7(「레인은 같은 워크트리에서 파일만 쓰고 커밋은 메인이 순차로」)과 lifecycle 감시(감시 경로 전체 diff)가 충돌한다. 같은 워크트리 병렬 레인은 서로의 산출물 때문에 researcher handoff 를 통과할 수 없다. 해결은 이번 audit 범위 밖(별건 · 하네스 intent 후보).
- 이 취합 파일(`dev-package/sessions/design-review-20260924.md`)도 감시 경로 안에 있다 — 열린 레인 task 가 남아 있으면 같은 충돌을 일으킨다.

## 11. 이번에 세지 않은 축

레인 5개의 「이번에 세지 않은 축」 합집합.

- 실화면 전체 — 라이브 스택 다운. 1440/375px 렌더 · 다크 스크린샷 대조 · 스프링·속도·1:1·러버밴드·드롭 반응(§9).
- apple-design §16 기반 — `onSubmit`·`role="dialog"` TSX 전수(인라인 검증 대 제출 검증 · Esc·닫기 · 길찾기), 20260908-L4 #4·#22·#23 재확인(L4a).
- §12 모달 스크림 유무(`.modal-back`·`.pvx-back` 현재 값) 재확인(L4a).
- §13 소리·햅틱 — 구현 0(L4a).
- `datasetpreview/**` — 전용 CSS 없음 · TSX 인라인 style·className 연결은 정적 CSS 감사 밖(L2).
- 20260912 D01·D02·D11 의 카탈로그 부분 세부 재계측(L2 턴 한도).
- `catalog.css:140` 등 카탈로그 상속 색쌍 대비 재계측(L2 · D12).
- 20260912 D15 잔존(부분) — `NotFoundPage.tsx:12` `<Link>` 전용 클래스 없음. 처리 = `routes/**` 재판정 때 함께(D14 와 같은 면).
- `routes/**` TSX 의 스타일 연결(D14 `pd-closedbar`·`pd-linkempty`) — L1 범위였으나 미실시, L3 는 범위 밖으로 넘김.
- D10 포커스 트랩의 TSX 로직(L3 · 취합이 `useDialogFocus` 사용만 확인).
- `.btn-strong`·`.chip--off` 의 실제 사용 화면 렌더(L1 → L2/L3 · 실화면).
- 20260912 D16·D21·D28·D30·D31 — 어느 레인도 다루지 않음.
- ⑦-10(화면 편차 통일) · ⑦-11·13–16(절차) — 레인 미접촉.

## advisor ② 반영

- 판정 = approve-with-changes(문안만 · 재감사 없음). 대비 3건(`.chip--off` 다크 1.66:1 · `.de-req` 다크 1.28:1 · `.btn-strong:hover` 1.05/1.10:1)과 `detail.css:242` 오탐은 원문 재계산으로 재현됨. Ted 묶음 ↔ ⑦-1..9 · 판정-14..21 대응 이중 계수 없음.
- §8 · #1 · #6 · #7 · §6 판정-14 — 「결정됨」 → 「spec 제약 · 열린 라운드(`R-DESIGN-CONSISTENCY-FULL-20260912.md:39–46`) 미이행」. WU-A1 만 즉시 수정 후보, WU-A2–A4 는 값 확정 선행(advisor ③).
- #17 — 판정을 「전환 곡선 한정」으로 좁힘. 묶음 6 권고 ⓑ 유지 — 정본 §14 는 변화 자체의 유지를 요구하고, 현 코드엔 opacity cross-fade 가 0이라 실손실은 0.14초 곡선뿐.
- §10 — intent 「트리에 없어」 정정: 브리프 경로 오기, 실물 `dev-package/intent/2026-09-12-design-consistency.md`.
- D15 — §11 에 처리(`routes/**` 재판정과 묶음) 추가.
