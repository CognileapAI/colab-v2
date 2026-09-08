# design-review-20260908 · L1 셸·공통 — 판정표

레인 L1 = `shell/shell.css`·`shell/tokens.css`·`components/common/toast.css`·`components/common/variableTable.css`·`auth/login.css`·`components/dashboard/dashboard.css` ＋ 해당 디렉터리 `.tsx`(인라인 style·className 맥락만).
정본 = `.claude/skills/design-review/SKILL.md` §0·§2-2·§2-3·§4 · `dev-package/reports/design-review/20260908/css_audit.md` · `dev-package/sessions/p3-design-audit-20260905.md`.
⛔ CSS·TSX 를 한 자도 고치지 않았다. `.tsx` 인라인 `style=` 는 `DataMapCard.tsx:37`(막대 폭 `%`, 동적 값) 1건뿐이고 디자인 판정 대상이 아니다.

| # | 축 | 항목 | 판정 | 근거 path:line · 실측값 | 처리 |
|---|---|---|---|---|---|
| 1 | 정적 | Lv 칩 글자색 | 없음 | L1 대상 파일에 Lv 칩 요소 0건(요소 부재) | — |
| 2 | 정적 | 제약 안내 초록→파랑 | 없음 | L1 대상 파일에 해당 요소 0건(요소 부재) | — |
| 3 | 정적 | 연결 불가 후보 행 흐림 | 없음 | L1 대상 파일에 해당 요소 0건(요소 부재) | — |
| 4 | 정적 | 상단 메뉴 활성 탭 파랑 밑줄 | 없음 | `shell/shell.css:184-192` `.mainnav a.is-active::after` 3px `--color-primary-600` 밑줄 존재(2026-09-05 판정과 동일 유지) | — |
| 5 | 정적 | 상단 버튼 알약→둥근 사각 | 없음 | `shell/shell.css:135·167·204·225·245` 전부 `--radius-sm`/`--radius-md`. `--radius-pill`·`9999px` 사용 0건 | — |
| 6 | 정적 | 카드 그림자 0(팝오버 허용) | 있음 | `auth/login.css:20` `.login-card { box-shadow: var(--shadow-sm) }` — `login-card` 는 카드다(팝오버·메뉴·토스트 아님) | 즉시 수정 후보 |
| 6-1 | 정적 | 카드 그림자 0 | 없음 | `components/dashboard/dashboard.css:63-68` `.dash-card` 는 `border`·`padding`·`background` 만 있고 `box-shadow` 선언 0건 | — |
| 6-2 | 정적 | 셸 상단바 그림자 | [미상 · 판정 보류] | `shell/shell.css:107` `.gnb { box-shadow: var(--shadow-sm) }` — `.gnb` 는 「카드」가 아니라 셸 고정바다. §0 정본의 카드 그림자 축이 셸 상단바에도 적용되는지 정본이 침묵 | Ted 판정 |
| 7 | 정적 | 계보 그래프 라벨 13px | 없음 | L1 범위에 `lineageGraph.css` 없음(다른 레인) | — |
| 8 | 접근성 | 글자 13px 미만 | 있음 | `shell/shell.css:82` `.backlink .bl-a` 11.0px · `components/common/toast.css:17` `.toast` 12.0px · `components/dashboard/dashboard.css:140·185·190·228·268·288·326·337·352` 9건 12.0px. 합계 **11건** | 즉시 수정 후보 |
| 9 | 정적 | 보더 2층 토큰 분리(컨테이너 vs 구분선) | 있음 | `components/dashboard/dashboard.css:64` `.dash-card` 컨테이너 보더 `var(--line, #e3e6ea)` · `:150` `.dash-device-note` 내부 구분선 `border-top: 1px solid var(--line, #e3e6ea)` · `:235` `.todo-grp + .todo-grp` 구분선도 동일 `var(--line, #e3e6ea)`. 컨테이너와 구분선이 같은 토큰(같은 폴백값)이라 층이 안 갈린다 | Ted 판정 |
| 9-1 | 정적 | 보더 2층 토큰 분리 | 없음 | `shell/shell.css` `.gnb` 보더 `--color-border-shell`(:106) vs `.avatar` 보더 `--color-border`(:244)·hover `--color-border-strong`(:255) — 서로 다른 요소·상태라 컨테이너/구분선 대조 대상 아님. `auth/login.css` 도 `.login-card` 보더(:18) `--color-border` 하나뿐, 내부 구분선 없음 | — |
| 10 | 정적 | 여백 컨테이너 소유(음수 상쇄 0) | 없음 | L1 6파일 전수 `margin: -` 패턴 0건(`grep` 실측). `shell/shell.css:57-59` 주석에 남은 종전 `margin-left: -7px` 는 이미 제거됐고 현재는 `padding: 3px 9px 3px 0`로 대체 | — |
| 11 | 정적 | 죽은 스타일(미사용 규칙·덮인 선언·미정의 토큰 무폴백) | 없음 | L1 6파일에서 셀렉터 중복·값 덮어쓰기 육안 확인 0건. `components/common/variableTable.css:24·49` `--line`(폴백 있음) · `components/dashboard/dashboard.css` 20건 전부(`:55·64·67·87·118·125·139·150·154·173·186·191·227·235·247·267·287·310·325·336`) 폴백 있음 → 선언 무효화 0건 | — |
| 12 | 접근성 | 대비 ≥4.5:1(같은 규칙 내 + 상속 색쌍) | 없음 | 계산값(WCAG 상대휘도) — `toast.css:6-7` `--toast-fg` `#a85400` on `--toast-bg` `#fff6ed` → **5.00:1**. `auth/login.css:95` `.login-error` `#c62828` on 상속 배경 `.login-card`(`--color-surface` `#fff`, `login.css:17`) → **5.63:1**. `dashboard.css:87` 등 `--fg-muted` 폴백 `#667`→`#667777` on 상속 배경 `#fff`(`--bg-card` 폴백, `:67`) → **5.63:1**. `dashboard.css:154` `--fg-danger` 폴백 `#a3222b` on `#fff` → **7.45:1**. `shell.css:260` `.avatar .cv` `--color-gray-500`(`#697077`) on `--color-surface`(`#fff`) → **5.02:1**. 전부 AA 4.5 통과 | — |
| 13 | 정적 | 파일 내 토큰 정의 ⓐ 컴포넌트 전용 | 없음 | `components/common/toast.css:6-8` `--toast-fg`·`--toast-bg`·`--toast-radius` — 접두사가 화면 고유(`--toast-*`). 컴포넌트 전용 변수라 승격 대상 아님 | — |
| 14 | 정적 | 파일 내 토큰 정의 ⓑ 전역 어휘 로컬 정의 | 없음 | L1 6파일에 `--color-*`·`--radius-*`·`--space-*`·`--shadow-*`·`--font-*` 형태를 파일 안에서 새로 `:root{}` 정의한 사례 0건(`css_audit.md` local token def 열 = shell 0·tokens 0·toast 3(ⓐ만)·variableTable 0·login 0·dashboard 0) | — |
| 15 | 정적 | 어휘 불일치(ⓐ/ⓑ 밖 · 정의 없이 폴백만 있는 이질 어휘) | 있음 | `components/dashboard/dashboard.css` 가 `tokens.css`(§0 정본) 의 `--color-*`·`--text-*` 어휘를 전혀 쓰지 않고 `--fg`·`--bg-card`·`--fg-muted`·`--bg-subtle`·`--accent-neutral`·`--fg-danger`·`--line` 7종(총 20 참조)을 쓴다. 이 7종은 `tokens.css` 에도 `dashboard.css` 안에도 **정의된 곳이 없다** — 전부 인라인 폴백(`#1b1f24`·`#fff`·`#667`·`#eef1f4`·`#5b7089`·`#a3222b`·`#e3e6ea`)만으로 버틴다. ⓐ(컴포넌트 전용)도 ⓑ(파일 내 전역 어휘 복제)도 아닌 제3의 형태 — SKILL.md §2-2-9 의 이분류에 없는 사례라 판정 보류 후 Ted 상정 | Ted 판정 |
| 16 | 모션 | `:active` 피드백 유무 | [미상] | L1 6개 CSS 에 `:active` 셀렉터 0건(`grep` 실측). 코드상 판정 가능한 범위에서는 「없음」이나, 클릭 피드백이 브라우저 기본 동작으로 충분한지는 실화면 확인이 필요해 apple-design 축 판정은 이번 표에 올리지 않음(L1 은 apple-design 전담 레인이 아님) | 실화면 계측 |

**있음 = 4건 / 16 · 없음 = 10건 / 16 · `[미상]`·판정 보류 = 2건 / 16.**
(§0 이월 항목 1~11 은 이번 레인 범위에 다시 실었다 — 7 항은 L1 파일에 존재하지 않아 판정 대상 자체가 없다.)

## css_audit 오탐

- `css_audit.md` 의 `components/common/variableTable.css` 「undefined token」 2건(`--line`, 폴백 있음)은 스크립트가 「미정의」로 표기했으나 SKILL.md §0 정본의 접근성 floor 정의(「폴백 없음 → 선언 무효화」)로는 **무효 선언이 아니다** — 폴백이 있어 렌더링 값이 존재한다. 「선언 무효화」 의미로는 오탐, 「전역 어휘와 다른 값으로 살아있다」는 사실 자체는 유효(→ #15 항목으로 승격).
- `components/dashboard/dashboard.css` 의 「undefined token」 20건도 동일 — 전부 폴백 보유. 스크립트 열 이름이 "undefined"라 무효 선언처럼 읽히기 쉬우나 값은 폴백으로 채워진다.
- 그 외 L1 파일(`shell.css`·`tokens.css`·`login.css`)에는 스크립트 표에 행 자체가 없어 오탐 검증 대상 없음.

## Ted 판정 후보

1. **`shell/shell.css:107` `.gnb` box-shadow** — ⓐ 「카드 그림자 0」 축을 셸 고정바(`.gnb`)까지 확대 적용해 제거 vs ⓑ `.gnb` 는 카드가 아니므로 축 적용 대상에서 제외하고 유지. 권고: ⓑ(제외·유지) — §0 정본 문구가 「카드 그림자」로 카드류를 특정했고, `.gnb` 는 목업(`제품_260817.html`)에 이미 그림자가 있는 셸 고정 요소라 팝오버·메뉴처럼 항상-떠있는 층 구분 목적으로 볼 수 있다.
2. **`auth/login.css:20` `.login-card` box-shadow** — ⓐ 「카드 그림자 0」 축 그대로 적용해 제거 vs ⓑ 로그인 카드는 유일한 화면 요소(단독 중앙 배치)라 예외 인정. 권고: ⓐ(제거) — `.login-card` 는 클래스명부터 「카드」이고 §0 축 문구에 예외 조건(단독 배치)이 없다. 제거 시 `border`(`--color-border`)만으로 경계가 남는지 실물 확인 필요.
3. **`components/dashboard/dashboard.css` 의 보더 2층 미분리(#9)** — ⓐ `--line` 하나로 컨테이너·구분선을 함께 쓰는 현재 방식을 유지(단일 토큰이 이미 셸 `--color-border`(`#e8ecf2`)와 값이 달라 화면 자체 결이 있다고 볼 여지) vs ⓑ `tokens.css` 의 `--color-border`/`--color-border-strong` 2층 체계로 갈아끼워 셸과 통일. 권고: ⓑ(2층 분리로 통일) — §0 정적 합격선이 「보더 2층 토큰 분리」를 명시 축으로 못박았고, 항목 #15 어휘 통일과 함께 처리하면 중복 작업을 피한다.
4. **`components/dashboard/dashboard.css` 어휘 불일치(#15) — 7종 20참조** — ⓐ `tokens.css` 에 `--fg`·`--bg-card`·`--fg-muted`·`--bg-subtle`·`--accent-neutral`·`--fg-danger`·`--line` 를 새 전역 토큰으로 승격(값은 현재 폴백 값 그대로 또는 기존 `--color-*` 동의어로 매핑) vs ⓑ `dashboard.css` 코드를 고쳐 기존 `tokens.css` 어휘(`--color-text`·`--color-surface`·`--color-text-muted`·`--color-bg`·`--color-border` 등)로 치환하고 새 토큰을 만들지 않는다. 권고: ⓑ(기존 어휘로 치환) — `tokens.css` 머리말(1-5행)이 "화면 토큰은 그 화면을 만드는 WU 가 필요할 때 옮긴다"고 적었지만, `--fg-muted`(`#667777`)·`--fg-danger`(`#a3222b`) 등은 이미 `--color-text-muted`(`#565c63`)·기존 danger류 토큰(정본에 미등재)과 개념이 겹쳐 새 이름을 늘리면 두 어휘가 공존한다. 단, `--accent-neutral`(`#5b7089`)처럼 대응 토큰이 tokens.css 에 없는 것은 ⓐ(승격) 로 갈 여지가 있어 항목별로 갈릴 수 있다 — 세부는 WU 단계에서 값별로 재확인.

## 이번에 세지 않은 축

- apple-design 인터랙션·모션 심화 축(스프링 느낌·속도 계승·재질·깊이) — L4 전담 레인이 아니면 실화면 계측 필요, L1 은 코드에서 판정 가능한 `:active`·`transition`·`reduced-motion`·`letter-spacing`만 훑었고(#16), L1 6파일에 `transition`·`animation`·`@keyframes` 자체가 `toast.css`(0건)·`shell.css`(다수, 색·배경 전환뿐 고정길이 애니메이션 아님)·`login.css`(2건, 색 전환) 정도라 apple-design 심화 판정표는 이번 표에 올리지 않았다.
- `reduced-motion` 분기 — L1 6파일 전부 `@media (prefers-reduced-motion)` 0건. `css_audit.md` 상 L1 대상 파일은 이 열이 `NO`이거나 `—`(모션 선언 자체 없음)이라 「모션 있는데 분기 없음」 결함으로 셀 만한 파일이 없다(`shell.css` 는 모션 7건 존재하나 전부 `color`/`background`/`border-color` transition 이라 SKILL.md 판정 범위인 "고정 길이 animation" 대비 성격이 다름 — 참고로만 남기고 판정하지 않음).
- 실화면 계측이 필요한 나머지 apple-design 항목(포인터 다운 피드백의 시각적 강도, 스프링 계승) 전부.
- L1 밖 파일(`catalog`·`detail`·`lineage`·`upload`·`preview`·`project`·`search`·`members`·`lab`) — 다른 레인 소관.
