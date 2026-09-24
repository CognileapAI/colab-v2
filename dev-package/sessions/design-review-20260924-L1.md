# design-review-20260924 · L1 셸·공통 — 판정표

레인 L1 = `frontend/src/shell/**`(tokens.css·primitives.css·shell.css·base.css·layers.css + TSX)·`components/common/**`·`auth/**`·`components/dashboard/**`·`app/**`·`routes/**`·`placeholders/**`.
Mode = AUDIT. CSS·TSX 미수정. 기준 트리 dc05531c.
정본 = `.agents/skills/design-review/SKILL.md` §0·§2-2·§2-3·§4 · `.agents/skills/apple-design/SKILL.md` · `dev-package/reports/design-review/20260924/css_audit.md` · `dev-package/sessions/p3-design-audit-20260905.md` · `frontend/src/shell/tokens.css` · `docs/design-system.md`.
축 = STATIC only(11항목 baseline + AA 4.5:1[라이트/다크] + 글자 13px + 미정의 토큰 + 음수 여백 + 카드 그림자 + 보더 2층 + 컨테이너 여백 + 로컬 토큰 ⓐ/ⓑ + 게이트 a~h). 모션/`:active`/reduced-motion 응답성/타이포 tracking 은 L4 담당 — hover/모션은 사실만 기록(선언값/억제), 응답 판정 없음.

## 1. 판정표

| # | 축 | 항목 | 판정 | 근거 path:line · 실측값 | 처리 |
|---|---|---|---|---|---|
| 1 | 정적 | 카드 그림자 0 — `.gnb` | [미상 · 정본 침묵] | `shell/shell.css:114` `.gnb { box-shadow: var(--shadow-sm) }`. `.gnb` 는 카드가 아니라 셸 고정바다 — §0 정본이 「카드」로 적었지 셸 상단바를 특정하지 않아 20260908 판정(6-2) 이후 여전히 정본 부재 | Ted 판정 |
| 2 | 정적 | 카드 그림자 0 — `.card` | 없음 | `shell/primitives.css:77` `.card { box-shadow: none }` | — |
| 3 | 정적 | 카드 그림자 0 — `.modal`(비대화상자) vs `.modal--dialog` | [미상 · 정본 침묵] | `shell/primitives.css:122` `.modal { box-shadow: var(--shadow-sm) }` vs `:130` `.modal--dialog { box-shadow: none }`. 대화상자류는 이미 0인데 `.modal--dialog` 를 안 붙이는 전체화면 모달(예: 업로드)은 그림자가 남는다 — 팝오버 예외로 볼지 카드 그림자 축 적용 대상인지 정본 침묵 | Ted 판정 |
| 4 | 정적 | 카드 그림자 0 — `.dash-card`/`.dash-tile` | 없음 | `components/dashboard/dashboard.css:408` `:is(.dash-card, .dash-tile) { box-shadow: none }` | — |
| 5 | 정적 | 카드 그림자 0 — `.login-card` | 없음(해소) | `auth/login.css:14-24` `.login-card` 규칙에 `box-shadow` 선언 자체가 없다(20260908 판정 6 은 `box-shadow: var(--shadow-sm)` 존재 「있음」이었다 — 그 사이 제거됨) | — |
| 6 | 접근성 | 글자 13px 미만 | 없음(해소) | `css_audit.md` L1 대상 파일(auth/login.css·common/toast.css·common/variableTable.css·dashboard/dashboard.css·shell/*) 전부 `<13px` 열 0. 수기 확인 — `shell/shell.css:87` `.bl-a` 13px(20260908 당시 11px) · `components/common/toast.css:15` 13px(당시 12px) · `dashboard.css` 전 13px 리터럴(당시 12px 9건) | — |
| 7 | 정적 | 미정의 토큰 — `--dash-bar-w` | 오탐 | `dashboard.css:134` `width: var(--dash-bar-w)` — `DataMapCard.tsx:37` 가 `style={{'--dash-bar-w': ...}}` 로 TSX 인라인에서 매 렌더 주입(게이트 g 패턴). CSS 파일만 보면 미정의이나 런타임엔 항상 값이 있다 | — |
| 8 | 정적 | 음수 여백 | 없음 | L1 8개 CSS 파일 `margin: -` 패턴 0건(`css_audit.md` neg margin 열 전부 0) | — |
| 9 | 정적 | 보더 2층 분리 — `.dash-card` 컨테이너 vs 내부 구분선 | 없음(해소) | `dashboard.css:66` `.dash-card` 자체 선언은 `border: 1px solid var(--color-border)` 이나 `:408` `:is(.dash-card, .dash-tile) { border-color: var(--color-border-strong) }` 가 같은 특이도(0,1,0)로 파일 뒤에서 이겨 컨테이너 보더가 `--color-border-strong` 로 최종 확정된다. 내부 구분선(`:159` `.dash-device-note`·`:263` `.todo-grp + .todo-grp`·`:292` `.titem`·`:397` `.lab-info .modal-foot`)은 전부 `--color-border` 그대로라 컨테이너/구분선이 서로 다른 토큰으로 갈렸다(20260908 판정 9 는 「같은 토큰이라 층이 안 갈린다·있음」이었다) | — |
| 10 | 정적 | 보더 2층 분리 — `.card`/`.modal--dialog` | 없음 | `primitives.css:75` `.card { border-color: var(--color-border-strong) }`(컨테이너) vs `:85` `.card-h { border-bottom: var(--color-border) }`(구분선). `.modal--dialog`(`:128` `--color-border-strong`) vs `.modal-h/.modal-f`(`:134·141` `--color-border`) 동일 구조 | — |
| 11 | 정적 | 컨테이너 여백 소유 | 없음 | `.lab-page`(`dashboard.css:10-14`) 가 자기 좌우·하단 패딩을 소유, 내부 `.dash-columns`·`.dash-card` 는 margin 없이 gap 만 사용. `.login`(`login.css:5-12`)도 동일 | — |
| 12 | 정적 | 파일 내 토큰 정의 ⓐ 컴포넌트 전용 | 없음 | `components/common/toast.css:7-9` `--toast-fg`·`--toast-bg`·`--toast-radius` — 접두 `--toast-*`, 화면 고유. 승격 대상 아님 | — |
| 13 | 정적 | 파일 내 토큰 정의 ⓑ 전역 어휘 로컬 정의 | 없음 | L1 8파일 전수 `:root{}`·`--color-*`/`--radius-*`/`--space-*`/`--shadow-*`/`--font-*` 재정의 0건(`grep '^\s*--[a-z-]*:' ` 실측 — 결과는 toast.css 3건(ⓐ)뿐) | — |
| 14 | 정적 | 어휘 통일 — `dashboard.css` 대체 토큰(구 D18/§0-#15) | 없음(해소) | 20260908/20260912 당시 미정의 대체 어휘 `--fg`·`--bg-card`·`--fg-muted`·`--bg-subtle`·`--accent-neutral`·`--fg-danger`·`--line` 7종 중 `--fg`·`--bg-card`·`--fg-muted`·`--bg-subtle`·`--line` 는 `dashboard.css` 에서 전부 사라지고 `tokens.css` 어휘(`--color-text`·`--color-surface`·`--color-text-muted`·`--color-border` 등)로 치환됐다. 남은 `--accent-neutral`(`dashboard.css:136`)·`--fg-danger`(`:163`)는 이제 `tokens.css:52·75`(라이트)·`:173·171`(다크)에 전역 토큰으로 정식 승격돼 있다 — 미정의 상태 자체가 해소 | — |
| 15 | 접근성 | 대비 — `.dash-error`/`.login-error`(`--fg-danger`) | 없음 | 라이트 `#a3222b` on `#ffffff` = **7.44:1** · 다크 `#ffadb6` on `#1a222c` = **9.09:1**(WCAG 상대휘도 수기 계산). 둘 다 AA 통과 | — |
| 16 | 접근성 | 대비 — `.labswitch .ln-ro`(`--color-gray-500`) | 없음 | `shell.css:260-265` 라이트 `#697077` on `--color-surface` `#ffffff` = **5.02:1** · 다크 `#b2bfce` on `#1a222c` = **8.58:1** | — |
| 17 | 접근성 | 대비 — 포커스 링(`base.css:12-15` `:focus-visible` outline `--color-primary-600`) | 없음 | 라이트 `#1369e9` on `#ffffff` = **4.97:1** · 다크 `#92c2ff` on `#1a222c` = **8.70:1** | — |
| 18 | 접근성 | 대비 — `.chip:where(:not([class*="chip--"]))`(수식자 없는 칩) | 없음 | `primitives.css:67` `background: var(--color-surface-alt)` · `color: var(--color-text-muted)`. 라이트 `#565c63` on `#f5f7fa` = **6.30:1** · 다크 `#b2bfce` on `#202b37` = **7.69:1** | — |
| 19 | 접근성 | 대비 — `.chip--off`(도장 없는 칩·배경은 base `.chip` 의 리터럴 `#eef2f7` 상속) | 있음(다크만) | `primitives.css:55` 배경 `#eef2f7`(테마 무관 리터럴) 위 `primitives.css:62` `color: var(--color-text-muted)`. 라이트 `#565c63` on `#eef2f7` = **6.01:1**(통과) · **다크 `#b2bfce` on `#eef2f7` = 1.66:1 — AA 대폭 미달**(리터럴이 다크에서 안 바뀌어 어두운 배경용 밝은 글자가 밝은 리터럴 배경 위에 얹힌다) | Ted 판정 |
| 20 | 정적 | `.chip` 배경 리터럴 `#eef2f7`(docs ⑦-6) | 있음 | `primitives.css:55`. `gates/fixtures/frontend-design-lint/same-in-dark.txt` 가 이미 게이트 f 면제(사유: 「같은 값 토큰 없음 · Ted 판정 대기」)로 등록해 게이트는 통과하나 정본 색 미정이며, #19 의 다크 대비 파탄이 이 리터럴에서 직접 나온다 — 토큰화가 대비 결함과 묶인 사안임을 새로 확인 | Ted 판정 |
| 21 | 정적 | `.chip--off`(docs ⑦-4 · 프리미티브) | 있음(위 #19 와 동일 근거) | `primitives.css:62` `.chip--off { border: 1px solid var(--color-border); color: var(--color-text-muted); }` — 배경을 스스로 정의하지 않아 `.chip` 리터럴을 그대로 물려받는다. 업로드·멤버 화면 사용처는 L3 소관이라 여기선 프리미티브 정의 자체만 판정 | Ted 판정(#19·#20 과 묶어 처리) |
| 22 | 정적 | `.btn-sm`(docs ⑦-3) | 있음 | `gates/fixtures/frontend-design-lint/primitives.txt` 가 `.btn-sm` 을 프리미티브 목록에 등재했으나 `shell/primitives.css` 전체에 `.btn-sm` 정의가 **0건**(`grep '\.btn-sm' frontend/src --include='*.css'` 결과 없음). 반면 TSX 는 `btn btn-sm`/`btn-primary btn-sm`/`btn-secondary btn-sm` 조합을 detail·upload·lineage·members·lab 등 50회 이상 쓴다(예 `components/detail/FileList.tsx:140` 등, 전부 L1 밖 화면). 스타일 없는 수식자라 지금은 아무 시각 효과가 없다 — 등재된 프리미티브가 구현되지 않은 공백 | Ted 판정 |
| 23 | 정적 | `.btn-strong:hover` 대비(docs ⑦-5) | 있음(파일은 L1 밖) | `components/upload/upload.css:309` `.btn-strong { background: var(--color-primary-600); color: var(--color-on-primary) }` · `:311` `:hover { background: var(--color-gray-50) }`(color 재선언 없음 → on-primary 유지). 라이트 `#ffffff` on `#f9fafb` = **1.05:1** · 다크 `#10233c` on `#202b37` = **1.10:1** — 둘 다 AA 대폭 미달. `.btn-strong` 은 프리미티브 목록에 없는 upload.css 전용 화면 클래스(L3 파일)라 여기선 값만 확인하고 처리는 L3/취합 몫으로 넘긴다 | Ted 판정(파일 소유 L3) |
| 24 | 정적 | `.inp[readonly]` 배경(docs ⑦-2 sub) | 없음(요소 부재) | `grep -rn "readonly\]" frontend/src --include='*.css'` 0건. 정본 어디에도 `[readonly]` 배경 규칙이 없다 — 판정 대상 셀렉터 자체가 없다(재판정 결과: 이전 항목이 가리킨 규칙이 존재한 적 없거나 이미 제거됨) | — |
| 25 | 정적 | `.login-input:focus-visible` 테두리색(docs ⑦-2 sub) | 변경 | `auth/login.css` 에 `.login-input:focus-visible` 전용 규칙 없음(`grep` 0건). 대신 `base.css:12-15` `:where(button, a, input, select, textarea):focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: 3px }` 가 전역으로 대신한다 — 「테두리색 변경」방식에서 「외곽 outline 링」방식으로 접근 자체가 바뀌었다(대비값은 #17 참고, 통과) | — |
| 26 | 정적 | z-index 층 일관성(게이트 h 성격) | 있음 | 같은 「배경 덮개+가운데 대화상자」패턴인데 `primitives.css:116` `.modal-back { z-index: 200 }` 와 `auth/login.css:187` `.account-modal-back { z-index: 120 }` 가 서로 다른 값을 쓴다. `shell.css:106` `.gnb` 100 · `:296` `.gnb-more-list` 40(자기 트리거 안이라 무관) · `auth/login.css:238` `.auth-expiry-overlay` 10000(세션 만료 최상위, 의도적 이례) | Ted 판정 |
| 27 | 정적 | 화면 뿌리 여백 관례 준수 | 없음 | `dashboard.css` 머리 주석이 스스로 명시한 대로 `.lab-page` 가 자기 여백을 갖고(`:10-14`), `login.css` `.login`(`:5-12`)도 동일 — 화면마다 다른 소유자가 아니다 | — |
| 28 | 모션(사실만) | `transition`/`reduced-motion` 선언 현황(판정 없음 · L4 축) | 사실 | `css_audit.md` — `auth/login.css` motion 2 declared/reduced-motion NO · `shell/shell.css` motion 7/ yes(전역 `@media (prefers-reduced-motion: reduce)` 블록이 `shell.css:419-421` 에 있음. `*, *::before, *::after { transition: none !important }`) · `shell/primitives.css` motion 1/NO · `dashboard.css`·`toast.css`·`variableTable.css` motion 0. 응답성(빠르기·억제 체감)은 판정하지 않는다 | — |

## 2. 이월 재판정

레인 파일에 걸리는 20260912 D-행(20260908-L1 은 20260912 가 상위 대조로 이미 포함) — 현재 값 기준 재판정.

| ID | 원 판정 | 이번 값 | 근거 |
|---|---|---|---|
| D01 | 있음 — 본문/폼 글꼴 불일치(`shell.css:85`) | 해소 | `base.css:10` `button, input, select, textarea { font-family: inherit; letter-spacing: inherit }` 가 새로 생겨 폼 요소가 `body`(`shell.css:94` `font-family: var(--font-sans)`)를 상속한다. `login.css:60` `.login-input { font: inherit }` 도 동일 계열 |
| D03 | 있음 — 대시보드 카탈로그 버튼 외형 누락(`dashboard.css:158` 당시 margin-top 만) | 해소 | `dashboard.css:167-182` `.dash-open-catalog` 는 이제 border·radius·background·color·font-size·padding 을 전부 선언한 완전한 버튼이다 |
| D04 | 있음 — 연구실 정보 모달 본문·하단 여백 누락(`LabInfoModal.tsx:34`) | 해소 | `LabInfoModal.tsx` 는 `.modal-h` 를 쓰지 않으므로 `primitives.css:133` `.modal--dialog:has(.modal-h){padding:0}` 가 걸리지 않고 `:131` 기본 `padding: var(--space-card)` 가 남아 본문 전체가 패딩을 갖는다. 하단은 `dashboard.css:397` `.lab-info .modal-foot { margin-top:24px; padding-top:16px; border-top:1px solid var(--color-border) }` 로 별도 여백·구분선까지 있다 |
| D08 | 있음 — 로그인 카드 모바일 가로폭 초과(`login.css:4·12`) | [미상 · 실화면 계측 필요] | 코드상 `.login`(`login.css:9`) `grid-template-columns: minmax(0, 1fr)` 로 그리드 트랙이 축소 가능하게 바뀌어 있어 원인으로 지목됐던 intrinsic 최소폭 문제에 대한 수정 시도로 읽힌다. 실제 375px 렌더는 로컬 스택 없이 판정 불가 |
| D09 | 있음 — 프로젝트 모달 z-index < GNB(`project.css:307`, `shell.css:96`) | [미상 · L2/L3 파일 혼재] | `shell.css` 의 `.gnb` z-index 는 100(`:106`, 불변). `project.css` 는 L1 밖(다른 레인 소관)이라 그 파일의 현재 값은 이 레인에서 재확인하지 않았다 — L1 쪽 값만 확정하고 나머지는 취합 시 L2/L3 산출과 대조 필요 |
| D10 | 있음 — 모달 키보드 포커스가 배경으로 빠짐(`LabInfoModal.tsx:34`) | 해소(코드 근거) | `components/common/useDialogFocus.ts` 가 열림 시 첫 컨트롤 포커스·`Tab`/`Shift+Tab` 순환 트랩·`focusin` 이탈 시 되돌리기·`Escape` 닫기·언마운트 시 트리거로 포커스 복귀를 전부 구현한다(`:15-65`). 코드 근거로는 결함이 없다 — 실제 브라우저 탭 이동 확인은 L4/실화면 몫으로 남긴다 |
| D11 | 있음 — 11~12px 다수(`catalog.css`·`dashboard.css:140` 등) | 해소(L1 범위) | `dashboard.css` 는 `css_audit.md` <13px 열 0, 전 리터럴 13px 로 정정됐다. `catalog.css` 등 L2 파일은 이 레인 밖 |
| D15 | 있음 — 없는 주소 화면 스타일 없음(`NotFoundPage.tsx:10`) | 잔존(부분 해소) | `shell.css:100·413` `.settings-page, .notfound` 가 페이지 컨테이너(최대폭·중앙정렬·패딩)를 이제 갖는다 — 「문장이 x0 에 붙는다」는 해소. 다만 `NotFoundPage.tsx:12` 의 `<Link>` 는 여전히 전용 클래스가 없어 브라우저 기본 링크색(파랑/방문색)을 그대로 쓴다 — 부분 잔존 |
| D18 | 있음 — 대체 토큰 어휘 혼용(`dashboard.css` 등) | 해소(L1 범위, #14 참고) | 위 판정표 #14 |
| D19 | 있음 — reduced-motion 인데 셸 transition 유지(`shell.css:137`, `login.css:54`) | (판정 보류 · L4 축) | 이 레인은 모션 응답성을 판정하지 않는다(브리프 축 제외). `shell.css:419-421` 에 전역 reduced-motion 강제 블록이 있다는 사실만 §1-#28 에 기록 |
| D20 | 있음 — 카드 그림자·음수 여백 잔존(`login.css:12` 등) | 해소(L1 범위) | `login.css` 의 `.login-card` 는 box-shadow 선언 자체가 없다(§1-#5). `project.css`/`members.css` 행은 L1 밖 |
| D24 | 미상 — 빈 연구실 안내 우측 잘림 원인(`EmptyLabOnboarding.tsx`, `dashboard.css:133`) | 변경(코드 근거만) | `dashboard.css:391` `.dash-lead { line-height:1.7; overflow-wrap: anywhere }` — 이전엔 없던 `overflow-wrap: anywhere` 가 추가돼 긴 문자열의 잘림 방지를 시도한 흔적이 있다. 실제 뷰포트 재현은 여전히 미확인 | [미상 · 실화면 계측 필요] |
| D25 | 없음 — CSS 전수 미연결 | 없음(변화 없음) | `app/routes.tsx`·`shell/shell.css:1` 경로 구조 그대로, L1 대상 CSS 8개 전부 화면에서 import 됨(수기 확인) |

## 3. 소계

판정표(§1) 28행 — **있음 8 / 없음 17 / [미상] 3**.
있음 8행 중 **Ted 판정 6**(#1·#3·#19·#20·#21·#22·#23·#26 — 실제로는 8건, 아래 정정) · **즉시 수정 후보 0** · **실화면 계측 0**(있음 행은 전부 정본 충돌·색 선택이라 즉시 수정으로 안 닫힌다).

정정 — 있음 판정 행 번호: #1, #3, #19, #20, #21, #22, #23, #26 = **8행, 전부 처리=Ted 판정**(#23 은 파일 소유가 L3).
[미상] 행: #7 은 오탐 처리(있음/없음 집계에서 제외), 이월 재판정의 D08·D09·D24 는 §2 표에 [미상]으로 남음(§1 본표에는 없음 — 이월 전용 카운트는 별도).

이월 재판정(§2) 13건 — **해소 8**(D01·D03·D04·D10·D11·D18·D20 + D25 무변화 포함 시 9) · **잔존(부분) 1**(D15) · **[미상 유지] 2**(D08·D24) · **레인 밖이라 미확인 1**(D09) · **판정 보류(L4 축) 1**(D19).

## 4. Ted 판정 후보

1. **`.gnb` box-shadow(#1) vs `.modal`(비대화상자) box-shadow(#3)** — 둘 다 「카드 그림자 0」 축이 셸 고정바·전체화면 모달까지 미치는지 정본이 침묵한다. ⓐ 카드류(`.card`·`.dash-card`·`.modal--dialog`처럼 명시적으로 떠 있는 대화상자)만 적용 대상으로 좁히고 `.gnb`·`.modal`(비대화상자)은 팝오버와 같은 「항상 뜬 층」으로 예외 인정 vs ⓑ 「카드 그림자 0」을 모든 표면(셸 고정바 포함)으로 확대해 `.gnb`·`.modal` 도 그림자를 뺀다. 권고: ⓐ — 20260908 판정 당시에도 같은 결론이었고(`.gnb` 는 목업에 이미 그림자가 있는 셸 요소), `.modal--dialog` 는 이미 0으로 맞춰져 있어 「대화상자는 0·상시 표면은 유지」로 이미 일관된 실무 규칙이 서 있다.
2. **`.chip`/`.chip--off` 배경 리터럴 `#eef2f7`과 다크 대비 파탄(#19·#20·#21)** — `same-in-dark.txt` 가 이미 Ted 판정 대기로 등록했지만 이번에 다크 대비 **1.66:1**(AA 4.5 미달)이 새로 확인됐다. ⓐ 새 전역 토큰(예 `--color-chip-bg` 라이트 `#eef2f7`/다크는 어두운 톤으로 분리 정의)을 만들어 다크에서 값이 바뀌게 한다 vs ⓑ 가까운 기존 토큰(`--color-gray-100` 라이트 `#e8ecf2`/다크 `#2b3745` 또는 `--color-surface-alt` 라이트 `#f5f7fa`/다크 `#202b37`)으로 리터럴을 치환해 다크에서 자동으로 어두워지게 한다. 권고: ⓑ — 새 토큰을 늘리지 않고 기존 다크 대응 토큰으로 바꾸면 대비 파탄이 구조적으로 사라진다. 다만 라이트 시각값이 `#eef2f7`→`#f5f7fa`(surface-alt) 또는 `#e8ecf2`(gray-100)로 살짝 바뀌는 점은 사용자 노출 변경이라 fix 단계 advisor ③ 대상이다.
3. **`.btn-sm`(#22)** — 게이트 목록엔 있고 구현은 없다. ⓐ `primitives.css` 에 `.btn-sm { height: …; padding: …; font-size: … }` 를 실제로 추가한다(값은 `.btn`(32px/40px min-height) 대비 축소값을 목업에서 확인해 정한다) vs ⓑ 목록에서 `.btn-sm` 을 빼고 TSX 50여 곳의 `btn-sm` 클래스를 걷어낸다(작은 버튼을 포기). 권고: ⓐ — TSX 전역에 이미 「작은 버튼」의도로 광범위하게 쓰여 있어(detail·upload·lineage·members·lab) 지금 상태는 「의도했는데 구현이 빠진」쪽에 가깝다. 값은 목업 대조가 필요해 이번 표에서 임의 수치를 짓지 않는다.
4. **`.btn-strong:hover` 대비(#23)** — 파일은 L3(`upload.css`) 소유라 처리 자체는 L3/취합 몫이지만, 값(라이트 1.05:1·다크 1.10:1)은 명백한 AA 위반이다. ⓐ `:hover` 에서 `background` 만 바꾸지 말고 `color` 도 함께 `var(--color-on-primary)` → `var(--color-text)`(어두운 표면 위 대비 확보 가능한 값)로 바꾼다 vs ⓑ `background` 를 `--color-gray-50` 대신 `--color-primary-700`(기존 hover 관례, `.btn-primary`/`.gnb-upload`/`.login-submit` 전부 이 패턴)로 바꿔 밝은 배경 실수 자체를 없앤다. 권고: ⓑ — 나머지 프리미티브·화면이 전부 `hover → primary-700` 관례를 쓰고 있어 `.btn-strong` 만 다른 규칙(회색 배경)을 쓴 것 자체가 오타에 가깝다.
5. **z-index 층 일관성(#26)** — `.modal-back`(전역 프리미티브) 200 vs `.account-modal-back`(로그인 화면 전용) 120. ⓐ `.account-modal-back` 값을 200 으로 맞춰 전역 모달과 통일한다 vs ⓑ 계정 관리 모달이 GNB(100) 위·전역 모달(200) 아래에 있어야 할 독자적 이유가 있다면 120 을 유지하고 주석으로 사유를 남긴다. 권고: ⓐ — 코드에 120 을 고른 이유를 적은 주석이 없고, 같은 배경 덮개+가운데 대화상자 패턴이 서로 다른 값을 쓸 이유가 보이지 않는다.

## 5. css_audit 오탐

- `dashboard.css:134` `--dash-bar-w`(undefined token) — `DataMapCard.tsx:37` 가 TSX 인라인 `style={{ '--dash-bar-w': ... }}` 로 매 렌더 주입한다(브리프 KNOWN 패턴과 일치). CSS 정적 스캔만으로는 미정의로 보이나 런타임 값은 항상 있다 — 「선언 무효화」류 결함이 아니다.
- 그 외 L1 대상 8개 CSS 파일 중 `css_audit.md` 「undefined token」열이 비어 있지 않은 행은 `dashboard.css` 1건뿐이라 추가 오탐 검증 대상이 없다.

## 6. 이번에 세지 않은 축

- apple-design 인터랙션·모션 심화(스프링 느낌·속도 계승·재질·깊이) — L4 전담. §1-#28 에 `transition`/`reduced-motion` 선언 유무 **사실만** 기록했고 응답 체감 판정은 하지 않았다.
- `:active` 피드백 유무 — 코드에서 셀렉터 존재 확인은 가능하나 이번 표에는 올리지 않았다(브리프가 L1 을 apple-design 전담 레인에서 제외).
- 타이포 tracking(`letter-spacing`) 심화 판정 — L4b 축.
- D09(프로젝트 모달 z-index)의 `project.css` 쪽 현재 값 — L2/L3 파일이라 이 레인에서 재확인하지 않았다. L1 쪽(`shell.css` GNB z-index=100, 불변)만 확정했다.
- D08(로그인 모바일 가로폭 초과)·D24(빈 연구실 안내 잘림) 의 최종 판정 — 코드 근거로 수정 시도 흔적은 확인했으나 실제 375px 렌더 결과는 로컬 스택이 꺼져 있어 계측 불가. `[미상 · 실화면 계측 필요]` 로 남긴다.
- `.btn-strong`(upload.css)·`.chip--off`/`.chip--*` 실제 화면 사용처(업로드·멤버 화면 렌더 결과) — 값·정의는 확인했으나 그 클래스가 실제로 쓰이는 화면은 L2/L3 소관이라 그 레인 산출과 대조가 필요하다.
