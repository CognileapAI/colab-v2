# design-review 20260924 · L4a apple-design (코드 검증 가능 항목)

- 기준 트리 dc05531c · 모드 AUDIT(수정 0) · task b6485251c9b94ae783658ce31269d232 · 정본 `.agents/skills/apple-design/SKILL.md`
- 판정 = 항목 문구가 서술한 결함의 존재 여부(있음 = 결함 있음).
- 결정됨 인용: `dev-package/prd/specs/S-DESIGN-CONSISTENCY-FULL-20260912.md:53` 「모든 변경 컨트롤은 pointer-down 피드백과 focus-visible을 갖고 reduced-motion을 지킨다」 · `S-DESIGN-CONSISTENCY-20260912.md:50` 「즉시 active 피드백 … reduced-motion」. 따라서 누름 피드백 도입 여부(구 판정-14)는 Ted 판정이 아니라 결정됨 → 즉시 수정 후보로 분류한다.
- 브리프가 가리킨 `dev-package/prd/intent/2026-09-12-design-consistency.md` 는 이 트리에 없다. spec 두 건으로 대신 인용했다.

## 1. 판정표

| # | 축 | 항목 | 판정 | 근거 path:line · 실측값 | 처리 |
|---|---|---|---|---|---|
| 1 | §1 응답 | `:active`(누름 순간) 규칙이 거의 없음 | 있음 | `frontend/src` 전체 `:active` 2건 = `shell/primitives.css:32` `.btn-primary:active { background: var(--color-primary-700); }` · `components/search/search.css:155` `.search-hero button:active { background: var(--color-primary-700); }` | 즉시 수정 후보(결정됨 spec :53) |
| 2 | §1 응답 | primitives `.btn`(수식자 없음)·`.btn-ghost` 누름 피드백 없음 | 있음 | `primitives.css:28` `.btn:where(:not(.btn-primary, .btn-secondary)):hover` 만 · `:30` `.btn-ghost` · `:active` 0 | 즉시 수정 후보 |
| 3 | §1 응답 | `.btn-secondary` 포인터 피드백 0(hover·active 모두 없음) | 있음 | `primitives.css:31` 정의만 · `:28` hover 에서 제외 · `:active` 0 · `docs/design-system.md` ⑦-1 | 즉시 수정 후보(누름) · hover 값은 ⑦-1 그대로 |
| 4 | §1 응답 | ⑦-1 `.btn-primary:hover` 억눌림이 누름 피드백까지 없앰 | 없음 | hover 는 없지만(`primitives.css:28` 제외) `:32` `:active` 존재 — 누름 순간 피드백 있음. hover 값 판정은 ⑦-1 소관 | — |
| 5 | §1 응답 | ⑦-5 `.btn-strong` 누름 피드백 없음(응답 측면만, 대비는 L1) | 있음 | `.btn-strong:hover` gray-50 만(`docs/design-system.md` ③ 편차 표 · `upload.css`) · 전수 `:active` 2건에 없음 | 즉시 수정 후보 |
| 6 | §1 응답 | 셸 대화형 클래스 누름 피드백 없음 | 있음 | `shell/shell.css` `.backlink:hover`(:72) · `.mainnav a:hover`(:177) · `.gnb-settings:hover`(:215) · `.gnb-upload:hover`(:238) · `.gnb-more:hover`(:288) · `.gnb-more-item:hover`(:323) · `.gnb-logout:hover`(:343) — 전부 hover 전용 · `.loadfail-retry`(:38 `cursor: pointer`)·`.theme-switcher`(:431)·모달 닫기 `.x`(:456) 는 hover·active 모두 0 | 즉시 수정 후보 |
| 7 | §1 응답 | 화면 CSS 대화형 클래스 누름 피드백 없음 | 있음 | `catalog.css:33` `.tbl tr.clk td { transition: background …, box-shadow … }`(hover 전용) · `upload.css:465`·`492`·`504`·`519` hover 전환 · 화면 CSS `:active` = `search.css:155` 1건뿐 | 즉시 수정 후보 |
| 8 | §1·§10 응답 | 입력 경로의 인위적 지연(debounce·피드백 앞 setTimeout) | 없음 | `debounce` 0건. setTimeout 은 폴링(`UploadModal.tsx:588`·`603` · `PreviewPanel.tsx:250` · `usePreviewRender.ts:75`·`122`)·재시도(`backoff.ts:14` · `logoutQueue.ts:56`)·정지 감시(`xhrPut.ts:36`)·토스트 수명(`Toast.tsx:50`)·포커스 이동 지연 0(`UploadModal.tsx:1113`–`1178`)·blob 회수(`ScreenshotButton.tsx:93`)·세션 만료 시계(`AuthGate.tsx:75`). 신규 `auth/workGuard.ts:136` 120ms · `:177` 120ms · `:229` 200ms 는 탭 간 probe/discard 응답 대기(기능 대기). 그 대기 동안 로그인 단추의 진행 표시 여부는 실화면 필요 | — |
| 9 | §3 중단 | 사용자 구동 상태 전환이 고정 animation | 없음 | 전부 `transition`: `primitives.css:25` · `shell.css:70`·`175`·`213`·`236`·`286`·`340` · `catalog.css:33`·`155` · `search.css:130`·`134` · `login.css:65`·`79` · `upload.css:355`·`360`·`465`·`492`·`504`·`519` | — |
| 10 | §3 중단 | 모달 열기가 고정 길이 `@keyframes`·고정 시작값 | 있음 | `upload.css:24` `animation: up-rise 0.46s ease;` · `:26` `@keyframes up-rise` | Ted 판정(판정-16 이월) |
| 11 | §3 | 무한 반복 animation(제스처 대상 아님) | 없음 | `upload.css:162`·`172` `up-spin 0.8s linear infinite` · `:644` `up-analyze-pulse 1.4s` — 로딩·분석 표시, 각 reduced-motion 분기 있음(#18) | — |
| 12 | §7 공간 | 팝오버가 트리거 기준점(`transform-origin`)·여는 전환 없이 즉시 표시 | 있음 | `upload.css:482` 주석 「`display:none` ＋ `.dr-pop.open{display:block}` 로 여닫는다」 · `:484` `.dr-pop{position:absolute;top:calc(100% + 6px);left:0;…}` · 전수 `transform-origin` 선언 1건 = `preview.css:294` `0 0`(확대 층 좌표계) | Ted 판정(판정-17 이월) |
| 13 | §7 공간 | 열기·닫기 경로 비대칭(닫기 전환 없음) | 있음 | `UploadModal.tsx`·`PreviewExpandOverlay.tsx` 에 `closing`·`isClosing`·`onAnimationEnd`·`onTransitionEnd` 0건 — 조건부 렌더 해제로 즉시 사라짐 · 열기는 #10 | Ted 판정(판정-16 이월) |
| 14 | §12 재질 | `backdrop-filter` 사용처 | 없음 | 전수 0건(열거만) | — |
| 15 | §12 재질 | 반투명 차단층 열거 | 없음 | 신규 `login.css:238` `.auth-expiry-overlay { position: fixed; inset: 0; z-index: 10000; … background: color-mix(in srgb, var(--color-bg) 96%, transparent); }` — 세션 만료 차단(모달 과업 = 스크림형, §12 부합) · `:239` reduced-transparency 분기 있음 | — |
| 16 | §14 | 전역 reduced-motion 분기 없음 | 없음 | `shell/shell.css:419`–`420` `@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; scroll-behavior: auto !important; } }` · `shell/styles.ts:26` 전역 import · 도입 커밋 `fc45a9aa` | — |
| 17 | §14 | 전역 규칙이 색·불투명도 전환까지 끔 | 있음 | #16 이 `*` 전체의 `transition` 을 끔 — `.btn`·GNB·`.tbl tr.clk` 의 background/color/opacity 전환 포함. 정본 §14 「Keep opacity/color changes that aid comprehension」 · 20260908 판정-15 권고(ⓑ 파일별)와 반대 방향 | Ted 판정(신규) |
| 18 | §14 | `animation` 의 reduced-motion 분기 누락 | 없음 | 전역 규칙은 transition 만 끔. animation 은 파일 분기: `upload.css:30`–`31`(up-rise) · `:174`–`176`(`.vizload .spin`·`.up-spinner`) · `:369`–`371`(gridbar) · `:645`–`646`(pulse) — animation 4종 모두 분기 있음 | — |
| 19 | §14 | `prefers-reduced-transparency` 분기 누락 | 없음 | 반투명 면 1건(#15)에 `login.css:239` `.auth-expiry-overlay { background: var(--color-bg); }` · 도입 커밋 `fc45a9aa` | — |
| 20 | §14 | `prefers-contrast: more` 분기 없음 | 있음 | 전수 grep 0건 · 정본 §14 「Respond to three independent signals」 | Ted 판정(신규 · #17 과 묶음) |
| 21 | §2 직접조작 | 확대·이동 드래그가 마우스 전용(Pointer Events·캡처 없음) | 있음 | `components/preview/useZoomPan.ts:334` `const onMouseDown = useCallback(` · `:342`–`350` `MouseEvent` move/up · `onPointerDown`·`setPointerCapture` 0건 | Ted 판정(판정-18 이월) |
| 22 | §10 | 드래그 시작 임계(약 10px) 없음 | 있음 | `useZoomPan.ts:336`–`337` 버튼 확인 후 즉시 `drag.current = { x: e.clientX, y: e.clientY }` · 임계 상수 0 | Ted 판정(판정-18 이월) |
| 23 | §1 | 드롭 영역 드래그 중 시각 피드백 없음 | 있음 | `FileDropCard.tsx:173`–`176` `onDragOver` 는 `preventDefault`·`stopPropagation` 만 · `onDragEnter`/`onDragLeave` 0건 · `upload.css` `.dropzone` 드래그 상태 규칙 0(히트 `:604` 는 analyze 장면 숨김) | Ted 판정(판정-19 이월) |
| 24 | §4·§5 | 스프링·속도 계승 미도입 | 있음 | `frontend/package.json` 에 `motion`·`framer-motion`·`react-spring` 0 · `useZoomPan.ts:346` 매 move 델타 가산, 속도 기록 0 | Ted 판정(판정-21 이월) |
| 25 | 실화면 | 스프링 체감·속도 인계·1:1 추적 지연·러버밴드(`clampView` 하드 스톱)·드롭 반응·모달 열기 도중 닫기 | [미상 · 실화면 계측 필요] | 라이브 스택 다운 | 실화면 계측 |
| 26 | §16 기반 | `onSubmit`·`role="dialog"` TSX 의 피드백 종류·Esc/닫기·길찾기 | [미상] | 이번 회차 미전수(§6) | — |

## 2. 이월 재판정

### 판정-14..21 · D-10..D-16 · D19

| 이월 항목 | 재판정 | 근거 |
|---|---|---|
| 판정-14 누름 피드백 0 | 변경 | `:active` 0 → 2(`primitives.css:32` · `search.css:155`) · 도입 커밋(-S`:active`) = `bdf62a31`·`d9aafcee`·`fc45a9aa`. 도입 여부는 spec(`S-DESIGN-CONSISTENCY-FULL-20260912.md:53`)로 결정됨 → Ted 묶음에서 빠지고 #1–#7 즉시 수정 후보로 이관 |
| D-10 누름 상태 규칙 신설 | 잔존(부분) | 공통 선택자 묶음 미실행 — 2건만 |
| 판정-15 모션 축소 파일별 vs 셸 한 벌 | 해소(다른 경로) | ⓐ(셸 전역)로 실행됨 `shell.css:419`–`420`(`fc45a9aa`) — 권고 ⓑ 와 반대. 결과로 #17 신규 발생 |
| D-11 검색 토글 손잡이 분기 | 해소 | `search.css:134` `transition: left var(--ease)` 가 전역 규칙으로 무력화. 파일 분기는 없음(css_audit NO) |
| 판정-16 모달 열기 고정·닫기 경로 없음 | 잔존 | `upload.css:24`·`26`(종전 `:31`·`:33`, 값 동일) · 닫기 0(#13). 정본 §3 내부 충돌(`:62` vs `:66`) 미해결 |
| D-16 모달 닫기 경로(TSX 언마운트 지연) | 잔존(미실행) | 닫기 상태·전환종료 핸들러 0건 |
| 판정-17 팝오버 기준점 | 잔존 | `.dr-pop` `upload.css:484`, 여닫기는 `display` 전환 · `transform-origin` 0 |
| D-12 `.dr-pop` 기준점·여는 전환 | 잔존(미실행) | 상동 |
| 판정-18 드래그 마우스 전용·임계 없음 | 잔존 | `useZoomPan.ts:334`(종전 `:228`) `onMouseDown` · 임계 0 |
| D-14 useZoomPan 포인터 전환 | 잔존(미실행) | `onPointerDown`·`setPointerCapture` 0 |
| 판정-19 드롭 영역 피드백 | 잔존 | `FileDropCard.tsx:173`(종전 `:168`) |
| D-15 드롭 상태·CSS | 잔존(미실행) | `onDragEnter`/`onDragLeave` 0 |
| 판정-20 · D-13 글자 간격 | 이 레인 제외 | L4b(§15) |
| 판정-21 스프링·속도 계승 | 잔존 | 의존성 0 · 판정-18 선행 조건도 미충족 |
| D19(20260912) reduce 에서도 셸 transition 0.14s | 해소(코드) | `shell.css:419`–`420` `transition: none !important` · 실화면 재측정(reduced-motion.json 재실행) 미실시 → 효과는 [미상 · 실화면 계측 필요] |

### 20260908-L4 행(#1–#31)

| 행 | 재판정 | 근거 |
|---|---|---|
| #1 `:active` 0 | 변경 | 2건(#1) |
| #2 hover 전용 | 잔존 | #6·#7 |
| #3 입력 지연 없음 | 유지(없음) | #8 · 신규 `workGuard.ts` 대기는 기능 대기 |
| #4 배경 클릭 2단 확인 | [미상] | 이번 미재확인 |
| #5 transition 사용 | 유지 | #9 |
| #6·#7 up-rise | 잔존 | #10 |
| #8 무한 반복 | 유지 · 확대 | up-spin 2곳 ＋ `up-analyze-pulse` 신규(`upload.css:643`–`644`) |
| #9 upload 분기 | 유지 · 확대 | 분기 2 → 4(#18) |
| #10·#11·#12·#14 login·catalog·members·shell 분기 불요 | 변경 | 전역 규칙으로 transition 일괄 차단(#16·#17) |
| #13 search `transition: left` | 해소 | 전역 규칙 |
| #15 transparency·contrast 0 | 변경 | transparency 1건 신설(#19) · contrast 0 잔존(#20) |
| #16–#18 타이포 | 제외 | L4b |
| #19 backdrop-filter 0 | 유지 | #14 · 반투명 차단층 1 신규(#15) |
| #20 기준점 없음 | 잔존 | #12 |
| #21 대칭 없음 | 잔존 | #13 |
| #22·#23 Esc·배경 닫기 | [미상] | 이번 미재확인(§16 전수 생략) |
| #24·#25 드래그 | 잔존 | #21·#22 |
| #26 드롭 피드백 | 잔존 | #23 |
| #27 스프링 | 잔존 | #24 |
| #28–#31 실화면 | [미상] 유지 | #25 |

## 3. 소계

- 판정표 26행: 있음 15 · 없음 9 · [미상] 2
- 처리: 즉시 수정 후보 6(#1·#2·#3·#5·#6·#7) · Ted 판정 9행(#10·#12·#13·#17·#20·#21·#22·#23·#24) · 실화면 계측 1(#25) · — 10
- 이월: 해소 3(판정-15 · D-11 · D19 코드) · 변경 1(판정-14 → 결정됨 이관) · 잔존 10(판정-16·17·18·19·21 · D-10 부분 · D-12·14·15·16) · 제외 1(판정-20/D-13 → L4b)

## 4. Ted 판정 후보 (판정-14..21 대비 차이 · 신규만)

차이(이월)
- 판정-14 → 삭제. 누름 피드백 도입은 spec `S-DESIGN-CONSISTENCY-FULL-20260912.md:53` 으로 이미 결정됨. 남은 것은 구현(즉시 수정 후보 #1–#7). 버튼 외 부품(표 행·GNB 링크)의 누름 값은 구현 spec 에서 정한다 — 선례 = `.btn-primary:active` primary-700.
- 판정-15 → 해소. 셸 전역 한 벌(ⓐ)로 실행됨. 대신 아래 신규 1 이 생겼다.
- 판정-16 · 17 · 18 · 19 · 21 → 변경 없음(잔존). 줄 번호만 이동: 판정-16 `upload.css:24`·`26` · 판정-18 `useZoomPan.ts:334` · 판정-19 `FileDropCard.tsx:173`. 판정-16 의 정본 내부 충돌(§3 `:62` 「Every animation」 vs `:66` 「gesture-driven」) 선결 과제도 그대로.
- 판정-20 → 이 레인 밖(L4b).

신규 1 · 「동작 줄이기」 전역 규칙이 색 변화까지 끈다 (#17 · #20)
- 문제 — 운영체제의 「동작 줄이기」를 켜면 `shell/shell.css:419`–`420` 규칙이 화면의 모든 전환(transition)을 없앤다. 정본은 위치 이동·확대 같은 움직임만 줄이고 색·투명도 변화는 이해를 돕는 한 남기라고 한다. 정본이 말하는 세 신호 중 「고대비 선호」(`prefers-contrast`) 분기는 0건이다.
- ⓐ 전역 규칙을 이동·변형 속성에 한정한다(색·투명도 전환 유지). 고대비 분기는 반투명 면이 늘 때 단다.
- ⓑ 현행 유지(모든 전환 차단 · 고대비 분기 없음).
- 권고 = ⓑ. 현재 이동 전환은 `search.css:134` 토글 손잡이 하나이고 나머지는 0.14초 색 전환이라 모두 꺼도 정보 손실이 작다. 반투명 면도 `.auth-expiry-overlay`(배경 96%) 하나라 고대비 분기의 효과가 작다. 이동·변형 전환이나 반투명 면이 늘면 ⓐ 로 재검토.

## 5. css_audit 오탐

- `reduced-motion` 열 NO 4건(`auth/login.css` · `components/catalog/catalog.css` · `components/search/search.css` · `shell/primitives.css`) — 파일 단위로는 사실이나 효과상 오탐. 네 파일의 motion decl 은 모두 `transition`(login `:65`·`:79` · catalog `:33`·`:155` · search `:130`·`:134` · primitives `:25`)이고 `shell/shell.css:419`–`420` 전역 규칙(`styles.ts:26` 전역 import · `!important`)이 모두 덮는다.
- `motion decl` 열 값(login 2 · catalog 2 · search 2 · primitives 1 · shell 7)은 실물과 일치. `upload.css` 14 는 개별 대조하지 않음(animation 4종·분기만 확인).

## 6. 이번에 세지 않은 축

- §16 기반 — `onSubmit`·`role="dialog"` TSX 전수(인라인 검증 대 제출 시 검증, Esc·닫기 단추, 길찾기) 미실시(턴 한도). 20260908 #4·#22·#23(배경 클릭 2단·Esc 층·배경 닫기)도 미재확인.
- §12 모달 스크림 유무(`.modal-back`·`.pvx-back` 현재 값) 미재확인.
- 실화면 전용(스프링·속도·1:1·러버밴드·드롭 반응) — #25.
- §15 타이포(L4b) · 정적 축(대비·13px·토큰·그림자, L1–L3) · §13 소리·햅틱(구현 0).

## 산출 경위

- begin 이 돌려준 runtime 경로는 worktree 밖이라 Write 도구가 격리 가드로 거부했고, `lifecycle write-artifact` 는 task 에 agent-id 가 없어 거부(「external edit requires assigned task and agent identity」). 초안을 `/home/ttlhi10/.claude/jobs/aa678208/tmp/` 에 쓰고 Bash `cp` 로 runtime 경로에 복사했다.
