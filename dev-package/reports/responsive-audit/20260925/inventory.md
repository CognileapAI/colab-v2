# Responsive and input-mode inventory: CoLAB v2 frontend

- Source: worktree `.claude/worktrees/mobile-preview-overlay` at `f0be4268` (develop). Read-only static inspection. No browser run, no repo edits.
- Scope: `frontend/src/**/*.css`, `frontend/src/**/*.{ts,tsx}`, `frontend/index.html`, audit entry files (`audit-*.tsx`, `design-preview.html`), `docs/design-system.md`, `db/platform/schema.sql`, `services/core-api` request models, `dev-package/SEED-DATA.md`.
- Cascade facts used below: every CSS file is one `@layer` block (`layers.css`: `tokens, base, primitives, patterns, screens`). `styles.ts` imports the screen files in this order: catalog, detail, project, members, lab, search, dashboard, preview, lineage, lineageGraph, upload, approval, toast, variableTable, login, shell. `shell.css` loads last in `screens`, so an unconditional `shell.css` rule beats a same-specificity screen rule, including one inside `@media`.
- "DEAD" means the declaration cannot win at any width because of that cascade, based on reading the code. `scripts/cascade-map.mjs map` could not confirm these statically: it exits 2 with `src/shell/design-system.css not in load order`. Check them in a browser before acting on them.

---

## 1. `@media` rules

### 1.1 Counts

| Item | Count |
|---|---|
| `@media` blocks in `frontend/src/**/*.css` | **61** in 16 files |
| … containing a width condition | 55 (52 `max-width`, 3 `min-width`) |
| … `(pointer: coarse)` | 2: `tokens.css:199` alone; `primitives.css:46` OR'd with `max-width: 640px` |
| … `prefers-reduced-motion` / `prefers-reduced-transparency` | 4 / 1 |
| `hover`, `any-pointer`, `any-hover`, `orientation`, height, `@container` | **0** |
| Units | px only, no `em`/`rem` queries, no range syntax (`width <= …`) |
| Media queries in TSX `style` or JS | **0**. JS width checks: none. `matchMedia` is used only for `prefers-color-scheme` (`shell/theme.ts:15,34`, `index.html`) and `prefers-reduced-motion` (`preview/useZoomPan.ts:469`) |
| Non-product | `design-preview.html:4` has one `@media(max-width:640px)` in the design-review shell |
| Files with no width rule | `lineage.css`, `toast.css`, `variableTable.css`, `deletion.css`. `lineage.css` modals size themselves with `min(560px, calc(100vw - 32px))` |

### 1.2 Rule by rule (61)

Type key: L = layout, S = spacing, Z = size or touch target, V = visibility, F = font, M = motion.

| # | file:line | query | selectors → change | type | status / note |
|---|---|---|---|---|---|
| 1 | `shell/tokens.css:141` | max-width: 900px | `:root --shell-gnb-offset: 110px` | L | Superseded at runtime: `Gnb.tsx:79` writes the measured `--shell-gnb-offset` inline on `<html>` through a ResizeObserver. This rule is only the value before JS runs |
| 2 | `shell/tokens.css:191` | max-width: 640px | `:root --space-page 16 · --space-card 20 · --space-section 20 · --control-height 44` | S/Z | |
| 3 | `shell/tokens.css:199` | pointer: coarse | `:root --control-height: 44px` | Z | The only token that follows input mode |
| 4 | `shell/base.css:17` | max-width: 640px | `input, select, textarea { font-size: 16px }` | F | Repeats the iOS 16px floor (see 1.4-8) |
| 5 | `shell/primitives.css:46` | (max-width: 640px), (pointer: coarse) | `.btn-sm { min-height: var(--control-height) }` | Z | |
| 6 | `shell/primitives.css:54` | max-width: 640px | `:is(.inp, .sel) { font-size: 16px }` | F | Repeat |
| 7 | `shell/primitives.css:119` | max-width: 1100px | `.table-scroll-hint` shown (block, padding, caption) | V | Used on the dataset list, project list, project detail datasets and account admin. It shows whether or not the table overflows and whatever the input device |
| 8 | `shell/shell.css:375` | max-width: 1180px | `.gnb padding 0 14px`; `.labswitch max-width 180px` | S/Z | At ≤900 the `.gnb` padding loses to `:452` |
| 9 | `shell/shell.css:380` | max-width: 1000px | `.labswitch max-width 132px`; `.avatar .nm max-width 56px` | Z | Truncates the lab name and user name |
| 10 | `shell/shell.css:385` | max-width: 880px | hides `.brand .bn` and `.avatar .nm`; `.mainnav a padding 0 9px` | V/S | |
| 11 | `shell/shell.css:392` | max-width: 740px | hides `.labswitch .ln/.ln-ro`; labswitch icon only; hides `.gnb-upload .lbl`; `.gnb-upload` padding; `.mainnav` margin | V/S | `.gnb-upload` declarations DEAD: `:457` hides `.gnb-upload` at ≤900 |
| 12 | `shell/shell.css:403` | max-width: 560px | `.gnb padding 0 10px, gap 4px`; `.mainnav overflow-x: auto`, scrollbar hidden; `.mainnav a padding 0 7px, nowrap` | L | `.gnb` padding and gap DEAD: later same-specificity `:452`, `:463`, `:468` override them |
| 13 | `shell/shell.css:415` | max-width: 640px | `.gnb padding-left/right: max(10px, env(safe-area-inset-*))`; `.appmain padding-bottom: env(safe-area-inset-bottom)`; `.avatar` gap and padding; `.gnb-logout` margin and padding; `.settings-page, .notfound padding 20 16 32`; `body input/select/textarea font-size: max(16px, 1em) !important` | S/F | **GNB safe-area padding DEAD**: `:463 .gnb { padding-inline: 12px }` comes later with the same specificity. `.avatar` DEAD because `:465` hides it. `.settings-page` padding DEAD because `:448` comes later. `.notfound` padding is live |
| 14 | `shell/shell.css:433` | prefers-reduced-motion | `*` transitions off, `scroll-behavior: auto` | M | |
| 15 | `shell/shell.css:451` | max-width: 900px | GNB becomes 2 rows: `.gnb` height auto, min 64, wrap, gap 8, padding 10 16; `.mainnav` gets its own full-width row (`order:10`); `.mainnav a flex:1, min-height 44`; hides `.gnb-upload` and `.gnb-settings`; shows `.gnb-more` | L/V/Z | Second GNB ladder (see 1.4-1) |
| 16 | `shell/shell.css:461` | max-width: 640px | `.theme-switcher min-height 44`, max-width 92 then 88; `.gnb gap 6` then 4, `padding-inline 12`; GNB controls `min-height 44, min-width 36`; hides `.gnb .avatar`; `.gnb-logout min-height 44` | Z/V/S | Declares `gap` and `max-width` twice inside one block |
| 17 | `auth/login.css:209` | **min-width: 1024px** | `.account-table` last column `position: sticky; right: 0` | L | Content-driven. The comment explains that the 576px action column would cover the 390px scroll area |
| 18 | `auth/login.css:226` | **min-width: 1536px** | `.account-table` th 2 = 100px, th 4 = 148px | Z | Content-driven (email column budget) |
| 19 | `auth/login.css:230` | max-width: 640px | `.account-row-actions` wrap; th 8 = 195px | L/Z | |
| 20 | `auth/login.css:242` | prefers-reduced-transparency | `.auth-expiry-overlay` opaque | – | |
| 21 | `auth/login.css:246` | max-width: 640px | `.login-input { font-size: 16px }` | F | Repeat |
| 22 | `components/catalog/catalog.css:186` | max-width: 640px | `.catalog-page padding 16 12 32` plus `max(…, env(safe-area-inset-left/right/bottom))`; `.colmenu min-width 0, max-content, max-width calc(100vw - 40px)`; `thead th:nth-last-child(-n+3) .colmenu { left:auto; right:8px }` | S/L | **`.catalog-page` padding DEAD twice**: `:211` shorthand later in the file, then `shell.css:443 :is(.catalog-page, .lab-page, .project-page){padding}`. `design-system.md:260` already calls these "죽어 있던 `@media` padding 규칙". The `nth-last-child` rule (0,3,2) probably still beats `:234 .tbl .colmenu{inset:…}` (0,2,0) on left and right. If so, the menu sheet for the last three columns is right-anchored and does not span the width. Browser check needed |
| 23 | `components/catalog/catalog.css:209` | max-width: 900px | `.catalog-filters` 2 columns | L | |
| 24 | `components/catalog/catalog.css:210` | max-width: 640px | `.catalog-page padding 20 16 32` (DEAD, shell); `.catalog-filters gap 14 12`; filter `select 16px`; `.desc` full row | S/L/F | |
| 25 | `components/catalog/catalog.css:227` | max-width: 640px | `.catalog-filters gap 16 12` (overrides `:212`); `.colmenu button min-height 44`; `.tbl .rowact .rab 44×44` | Z | 3rd of 4 blocks at 640 in this file |
| 26 | `components/catalog/catalog.css:233` | max-width: 640px | `.tbl .colmenu` becomes a fixed bottom sheet: `inset:auto 16px 16px`, `max-height:60dvh`, z 140 | L | No safe-area bottom |
| 27 | `components/dashboard/dashboard.css:34` | max-width: 900px | `.dash-columns` 1 column | L | **Exact duplicate** of #29 |
| 28 | `components/dashboard/dashboard.css:411` | max-width: 640px | `.lab-page padding 20 16 32` (DEAD, `shell.css:443`); `.dash-tiles` 2 columns; `.dash-recent button` grid; `.lab-info-grid` 1 column | L/S | |
| 29 | `components/dashboard/dashboard.css:424` | max-width: 900px | `.dash-columns` 1 column | L | Duplicate |
| 30 | `components/dashboard/dashboard.css:427` | max-width: 640px | `.dash-tiles` 2 columns (repeats `:413`); `.dash-bar min-height 44`, grid `96px 1fr 36px`; `.dash-steps` column | L/Z | |
| 31 | `components/detail/detail.css:37` | max-width: 860px | `.dt-header` wrap; `.dh-act width 100%` | L | Pairs with #36 (`min-width: 861px`) |
| 32 | `components/detail/detail.css:66` | max-width: 720px | `.infogrid` 3 → 2 columns, border fix-ups | L | |
| 33 | `components/detail/detail.css:153` | max-width: 860px | `.dh-edit width 100%` | L | |
| 34 | `components/detail/detail.css:182` | max-width: 860px | `.dt-edit .de-row` 1 column, gap 4 | L | |
| 35 | `components/detail/detail.css:270` | max-width: 640px | `.infogrid` 1 column; `.ig border-right 0` | L | |
| 36 | `components/approval/approval.css:18` | **min-width: 861px** | `.dt-header .dh-menu { left:auto; right:0 }` | L | The only min-width rule outside the account table |
| 37 | `components/lab/lab.css:73` | max-width: 640px | `.labinfo-modal .inp/.sel min-width 0` | Z | |
| 38 | `components/lineage/lineageGraph.css:75` | max-width: 520px | `.detail-page .lrow` `1fr auto`; `.stg` full row | L | Only use of 520 |
| 39 | `components/members/members.css:101` | max-width: 640px | `.memtbl` table becomes stacked cards: thead hidden, `td.pc::before { content: attr(data-sw) }` labels | L/V | |
| 40 | `components/preview/preview.css:593` | max-width: 640px | `.pv-control select 16px`; `.pv-basic-grid` 1 column; `dd` wrap anywhere; `:is(.pv-zoom, .pv-shot, .lin) button min-height 44` | F/L/Z | **The only width rule for the map preview.** Nothing sizes `.pv-overlay-tr/br/bl` by viewport. The 44px buttons at ≤640 make the overlay cover more of the map |
| 41 | `components/project/project.css:577` | max-width: 640px | `.pj-modal-back padding 16`; `.pj-modal max-height calc(100dvh - 32px)`; `.pj-inp/.pj-tarea 16px`; `.pj-cards` 1 column | S/F/L | |
| 42 | `components/project/project.css:590` | max-width: 640px | `.pj-modal-back padding 12`, `.pj-modal max-height calc(100dvh - 24px)`: both redefine #41's properties; `.pj-modal-h`, `.pj-fgroup` padding; `.pj-seg button min-height 44` | S/Z | Consecutive blocks at the same breakpoint set the same properties |
| 43 | `components/project/project.css:607` | max-width: 640px | `.pj-toolbar` 2-column grid; `.pj-ctl select` 100%, 16px; `.pj-count` full row | L/F | |
| 44 | `components/search/search.css:151` | max-width: 640px | `.search-hero input 16px` | F | Repeat |
| 45 | `components/search/search.css:156` | max-width: 640px | `.lab-page .search-hero` padding; `.search-hero h1 24px` | S/F | |
| 46 | `components/upload/upload.css:79` | max-width: 1023px | `.up-split` 1 column | L | |
| 47 | `components/upload/upload.css:184` | prefers-reduced-motion | spinners static | M | |
| 48 | `components/upload/upload.css:219` | max-width: 720px | `.regsteps .rs-f { display:none }` | V | Overridden in `[data-scene="register"]` by `:658 display:inline-flex` (higher specificity). `:661` then styles the element at ≤720 as if it were visible. The two rules contradict each other |
| 49 | `components/upload/upload.css:224` | max-width: 720px | `.form-2` 1 column | L | |
| 50 | `components/upload/upload.css:231` | max-width: 1100px | `.form-3` 2 columns | L | |
| 51 | `components/upload/upload.css:232` | max-width: 720px | `.form-3` 1 column | L | |
| 52 | `components/upload/upload.css:300` | max-width: 720px | `.reg-actions .uf-hint { display:none }` | V | **Hides information**: the footer hint, including `NEXT_BLOCKED_HINT` (why the next step is blocked, `RegisterArea.tsx:1278-1279`), disappears on phones and phone landscape |
| 53 | `components/upload/upload.css:387` | prefers-reduced-motion | progress transition off | M | |
| 54 | `components/upload/upload.css:558` | max-width: 760px | `.dr-pop width 308px`; second calendar hidden | Z/V | Only use of 760. Written in compact style `@media(max-width:760px)` |
| 55 | `components/upload/upload.css:617` | max-width: 600px | `.mb-takeover.up-empty padding 12`; `.up-empty .up-body padding 16`; `.modal-h` wrap | S | Only use of 600 |
| 56 | `components/upload/upload.css:629` | max-width: 720px | register `.up-body padding 16 16 88`; `.up-empty .reggate .rg-t 13px` | S/F | |
| 57 | `components/upload/upload.css:649` | max-width: 1023px | register `.up-split-preview position: static` (sticky off) | L | |
| 58 | `components/upload/upload.css:661` | max-width: 720px | register `.regsteps .rs-f max-width 100%, margin 4px 0` | Z | See #48 |
| 59 | `components/upload/upload.css:687` | prefers-reduced-motion | analysing chip pulse off | M | |
| 60 | `components/upload/upload.css:697` | max-width: 640px | `.dr-pop` becomes a fixed bottom sheet (`inset:auto 12px 12px`, `max-height 80dvh`); `.dr-cal-d height 44` | L/Z | No safe-area bottom |
| 61 | `components/upload/upload.css:704` | max-width: 640px | `.filecard` wrap, `.fmeta` full row; `.reggate` stacks, `.rg-a` full row | L | |

### 1.3 Distinct width values (17)

| value | kind | rules | where (file:line) | screens affected |
|---|---|---|---|---|
| 520 | max | 1 | lineageGraph:75 | 데이터셋 상세 (계보 행) |
| 560 | max | 1 | shell:403 | GNB (every screen) |
| 600 | max | 1 | upload:617 | 업로드 모달 (빈 상태) |
| **640** | max | **25** (24 plain + 1 OR'd with `pointer: coarse`) | tokens:191 · base:17 · primitives:46,54 · shell:415,461 · login:230,246 · catalog:186,210,227,233 · dashboard:411,427 · detail:270 · lab:73 · members:101 · preview:593 · project:577,590,607 · search:151,156 · upload:697,704 | all |
| 720 | max | 7 | detail:66 · upload:219,224,232,300,629,661 | 데이터셋 상세 (기본 정보), 업로드 등록 |
| 740 | max | 1 | shell:392 | GNB |
| 760 | max | 1 | upload:558 | 업로드 기간 달력 |
| 860 | max | 3 | detail:37,153,182 | 데이터셋 상세 (머리·편집) |
| 861 | **min** | 1 | approval:18 | 데이터셋 상세 (머리 메뉴) |
| 880 | max | 1 | shell:385 | GNB |
| 900 | max | 5 | tokens:141 · shell:451 · catalog:209 · dashboard:34,424 | GNB, 데이터셋 목록 필터, 연구실 대시보드 |
| 1000 | max | 1 | shell:380 | GNB |
| 1023 | max | 2 | upload:79,649 | 업로드 등록 (2단 → 1단) |
| 1024 | **min** | 1 | login:209 | 계정 관리 표 |
| 1100 | max | 2 | primitives:119 · upload:231 | 표 가로 스크롤 안내 (데이터셋 목록 · 프로젝트 목록 · 프로젝트 상세 · 계정 관리), 업로드 form-3 |
| 1180 | max | 1 | shell:375 | GNB |
| 1536 | **min** | 1 | login:226 | 계정 관리 표 |

Breakpoints each screen actually goes through:

| Screen | Breakpoints |
|---|---|
| GNB (every route) | 1180 · 1000 · 900 · 880 · 740 · 640 · 560 (7 steps) |
| `/datasets` 데이터셋 목록 | GNB + 1100 · 900 · 640 |
| `/datasets/:id` 데이터셋 상세 (incl. preview, lineage) | GNB + 861(min) · 860 · 720 · 640 · 520 |
| Upload modal (any route) | 1100 · 1023 · 760 · 720 · 640 · 600 |
| `/account-admin` 계정 관리 | GNB + 1536(min) · 1100 · 1024(min) · 640 |
| `/lab` 연구실 대시보드 · 검색 | GNB + 900 · 640 |
| `/projects`, `/projects/:id` | GNB + 1100 · 640. The project tables `.pj-table`/`.pj-ds` have no width rule and only scroll horizontally |
| `/lab-settings` | GNB + 640 (members cards, lab info) |
| Preview route (`UnregisteredPreviewPage`) | GNB + 640 (only `preview.css:593`) |

### 1.4 Inconsistencies

1. **One component with two ladders.** The GNB has the mockup ladder 1180/1000/880/740/560 (`shell.css:375-409`) and the P2a ladder 900/640 (`shell.css:451-470`). At ≤900 the second ladder changes the GNB to 2 rows and hides upload and settings. That kills the `.gnb-upload` parts of 740, the `.gnb` padding and gap of 560 and 1180, and the safe-area padding of 640 (`:418-419`).
2. **One tablet boundary written 4 ways:** 860 (detail), 861 min (approval), 880 (GNB), 900 (GNB, tokens, catalog, dashboard).
3. **A mid boundary written 3 ways:** 720 (detail, upload), 740 (GNB), 760 (upload calendar).
4. **The upper boundary written 5 ways:** 1000, 1023, 1024 (min), 1100, 1180.
5. **Three single-use steps below 640:** 520, 560, 600.
6. **max and min mixed:** 52 max against 3 min. The complementary pairs sit in different files: 860 (detail.css) / 861 (approval.css), and 1023 (upload.css) / 1024 (login.css, a different screen). "1023 vs 1024" is consistent only because the two rules never meet.
7. **Duplicate or fragmented blocks:** `dashboard.css:34` ≡ `:424`. `.dash-tiles` is set at `:413` and again at `:428`. `project.css:577` and `:590` redefine `padding` and `max-height`. `catalog.css` has 4 blocks at 640, with `.catalog-filters gap` set twice. `shell.css` has 2 blocks at 640, and `:461` sets `gap` and `max-width` twice. `login.css` and `search.css` each have 2 blocks at 640.
8. **The iOS 16px input floor is declared 9 times:** `base.css:19`, `primitives.css:55`, `shell.css:431` (`!important`, the one that wins), `search.css:151`, `preview.css:594`, `project.css:580`, `project.css:610`, `catalog.css:213`, `login.css:247`.
9. **Dead `@media` declarations:** `catalog.css:187-191` and `:211`, `dashboard.css:412`, `shell.css:418-419` (safe-area), `:422` (`.avatar`), `:427` (`.settings-page`), `:398-399` (`.gnb-upload`), `:404` (`.gnb` padding and gap), and `upload.css:219` inside the register scene. The token at `tokens.css:141` is overridden at runtime.
10. **Touch targets follow width, not input mode.** 44px targets apply only at ≤640 (catalog `.rab`/`.colmenu`, preview zoom and screenshot, `.pj-seg`, `.dash-bar`, `.dr-cal-d`, GNB) or ≤900 (GNB `.mainnav a`). Only `--control-height` and `.btn-sm` follow `pointer: coarse`. See 3.1.
11. **px vs em:** every query is in px (0 em). With `html` at the browser default and type tokens in rem (`tokens.css:99-104`), a user who raises the base font size keeps px breakpoints. Components then overflow earlier than the breakpoints expect.

---

## 2. Candidate scales

Reference widths in CSS px. Phones portrait are 360–430. Phones landscape are 640–932 (SE 667, iPhone 15 844, Pro Max 932). iPad portrait is 744 (mini), 768–834, and 1024 for the Pro 12.9. iPad landscape is 1024–1366 (1133 mini, 1180 Air/10th, 1194 Pro 11). Laptops are 1280–1536 and up.

- **A · 3 steps, `640 · 1024`:** phone ≤640, tablet 641–1023, PC ≥1024. Matches the owner's words: phone · tablet · PC.
- **B · 4 steps, `640 · 900 · 1180`:** phone ≤640, tablet portrait or split 641–900, tablet landscape or small laptop 901–1180, PC ≥1181. Keeps the three largest existing clusters.
- **C · 4 steps, `640 · 768 · 1024`:** phone ≤640, large phone landscape or small split 641–767, tablet portrait 768–1023, PC and tablet landscape ≥1024. The conventional sm/md/lg split.

"Band" is the width range whose behaviour changes when the rule moves. + means the rule starts applying to wider screens. − means it stops applying to that band.

| current | rules | A target (Δ · band) | B target (Δ · band) | C target (Δ · band) |
|---|---|---|---|---|
| 520 lineage row | 1 | 640 (+120 · 521–640) | 640 (+120) | 640 (+120) |
| 560 GNB nav scroll | 1 | 640 (+80 · 561–640) | 640 (+80) | 640 (+80) |
| 600 upload empty | 1 | 640 (+40 · 601–640) | 640 (+40) | 640 (+40) |
| 640 | 25 | — | — | — |
| 720 detail infogrid, upload forms/hints | 7 | 640 (−80 · 641–720: SE landscape loses stacking) | 640 (−80) | 767 (+47 · 721–767: iPad mini portrait gains stacking) |
| 740 GNB labswitch icon | 1 | 640 (−100 · 641–740) | 640 (−100) | 767 (+27) |
| 760 upload calendar | 1 | 640 (−120 · 641–760) | 640 (−120) | 767 (+7) |
| 860 detail header/edit | 3 | 1023 (+163 · 861–1023) | 900 (+40 · 861–900) | 1023 (+163) |
| 861 min approval menu | 1 | 1024 (+163) | 901 (+40) | 1024 (+163) |
| 880 GNB brand/avatar name | 1 | 1023 (+143) | 900 (+20) | 1023 (+143) |
| 900 GNB 2-row, catalog filters, dashboard, gnb-offset token | 5 | 1023 (+123 · 901–1023: 1000px laptop windows get 2-row GNB) | — | 1023 (+123) |
| 1000 GNB labswitch/avatar width | 1 | 1023 (+23) | 1180 (+180 · 1001–1180: iPad landscape gets narrower labswitch) | 1023 (+23) |
| 1023 upload split | 2 | — | 900 (−123 · 901–1023 regains 2-column upload) | — |
| 1024 min account sticky column | 1 | — | 901 (−123: sticky column at 901–1023), or keep as content exception | — |
| 1100 table scroll hint, form-3 | 2 | 1023 (−77 · 1024–1100 loses hint and 2-col form) | 1180 (+80 · 1101–1180) | 1023 (−77) |
| 1180 GNB padding/labswitch 180 | 1 | 1023 (−157 · 1024–1180 loses GNB compaction. **Risk:** iPad landscape 1133/1180, where the rule was added because the GNB did not fit) | — | 1023 (−157, same risk) |
| 1536 min account column widths | 1 | exception | exception | exception |
| **Totals (54 width rules, 1536 excluded)** | | **26 moved · 28 kept · Σ\|Δ\| 2764px** | **23 moved · 31 kept · Σ\|Δ\| 1909px** | **26 moved · 28 kept · Σ\|Δ\| 2347px** |

Where each device lands:

| Device (CSS px) | A | B | C |
|---|---|---|---|
| iPhone portrait 390 | phone | phone | phone |
| iPhone SE landscape 667 | tablet | tablet-portrait | large-phone |
| iPad mini portrait 744 | tablet | tablet-portrait | large-phone |
| iPad portrait 820 | tablet | tablet-portrait | tablet |
| iPhone Pro Max landscape 932 | tablet | tablet-landscape | tablet |
| iPad Pro 12.9 portrait / old iPad landscape 1024 | PC | tablet-landscape | PC |
| iPad Air landscape 1180 | PC | tablet-landscape | PC |
| Laptop 1280/1440 | PC | PC | PC |

Notes that apply to all three candidates:
- **Width alone cannot separate phone landscape (667–932) from tablet portrait (744–1024).** Under every scale an iPhone in landscape lands in a tablet step, and under A and C an iPad in landscape lands in the PC step. The input axis has to come from `(pointer: coarse)` / `(hover: none)`: target size, hover-free information, gesture alternatives. Short landscape viewports (map preview, fixed bottom bars) need `(max-height: ~500px)`.
- **Content-driven exceptions:** `login.css:209` (1024 min) and `:226` (1536 min) are derived from measured table column budgets, as the comments at `login.css:203-221` show. `primitives.css:119` (1100) shows a hint instead of reacting to actual overflow. These fit container queries or overflow detection better than a viewport scale. There are 0 `@container` rules today.
- Moving any rule to a lower step is a behaviour change in the "−" band. The GNB (1180, 900) and upload split (1023) moves carry the most visual risk.

---

## 3. Input mode

### 3.1 Pointer and hover media queries
- `tokens.css:199` `(pointer: coarse) { --control-height: 44px }` and `primitives.css:46` `(max-width: 640px), (pointer: coarse) { .btn-sm { min-height: var(--control-height) } }` are the only ones. There are **0** `(hover: hover|none)`, `any-pointer` or `any-hover` queries.
- On a touch tablet (>640 wide), these targets stay under 44px:
  - `.pv-zoom button, .pv-shot button`: `padding: 4px 10px; font-size: 13px`, about 28px tall (`preview.css:339-343`). 44px only at ≤640 (`preview.css:597`).
  - `.tbl .rowact .rab`: 36×36 (`catalog.css:225`). `.colmenu button`: min 36 (`catalog.css:226`). Both 44 only at ≤640.
  - `.fchips .fc button` (applied-filter remove): 24×28 (`catalog.css:124`). No touch rule at any width.
  - Period calendar: `.dr-nav button` 28×28 (`upload.css:520`), `.dr-useg button` 28 tall (`upload.css:550`), `.dr-cal-d` 32 tall (`upload.css:534`, 44 only at ≤640).

### 3.2 `:hover`
- 34 `:hover` selectors in 11 files. None is wrapped in `(hover: hover)`, so after a tap on touch the hover styling sticks. They are all colour, border or underline feedback.
- One rule reveals content on hover: `catalog.css:159` `.tbl tbody tr:hover td.rowact .ra, … :focus-within { opacity: 1 }`. It is **already neutralised** by `catalog.css:224` `.tbl .rowact .ra { opacity: 1 }`, which makes the row actions always visible. The comment at `:154` ("평소엔 자리만 잡고 있다가 행 hover·키보드 포커스에서 나타난다") is stale. No CSS-only hover content remains.

### 3.3 `title=` tooltips that carry information touch users cannot reach

| file:line | tooltip text | visible text |
|---|---|---|
| `catalog/CatalogTable.tsx:210` (text from `:56-59`) | `${day(lineageConfirmedAt)} 에 확정했는데 ${day(lastModifiedAt)} 에 파일이 바뀌었어요` | chip `확인 필요`. The comment `:57` says the dates are hover-only by design: "확정한 날과 바뀐 날은 마우스를 올렸을 때 알린다 … 칸 안에는 숫자를 넣지 않는다" |
| `catalog/CatalogTable.tsx:202` | full project list `names.join(' · ')` | representative project + chip `외 N` |
| `catalog/CatalogTable.tsx:230`, `project/ProjectDatasetTable.tsx:109` | `승인 처리가 아직 도착하지 않았다` | `승인 전` |
| `catalog/CatalogTable.tsx:196` | `가공 단계가 계보로 계산한 값과 다릅니다` (also `aria-label`) | `계산값과 다름` |
| `approval/VerifiedBadge.tsx:18` | `교수가 품질을 보증했어요` | `Verified` |
| `lineage/LineageSection.tsx:145`, `:218` (text from `:81-89`) | `연구실 밖 출처라 상세 화면이 없어요` / `지워진 데이터라 상세 화면이 없어요 · ${day(deletedAt)}` | node name only. **The deletion date exists only in the tooltip** (`:83` "묘비의 hover 문구는 지운 날짜를 함께 말한다") |
| `lineage/LineageSection.tsx:433` | full lineage method when `.lin-way` is ellipsised ("전문은 여기 남는다") | truncated method |
| `routes/AccountAdminPage.tsx:327-330` | full email, name, role and lab of ellipsised cells (`login.css:175`; `:174` "`title` 로 전체 값을 읽는 칸") | truncated values |
| `preview/PreviewPickRow.tsx:122, :148, :169` (+ options `:127, :153, :174`) | full file name, variable and time of truncated `<select>` | truncated. Lower impact: native mobile pickers show the full option text |

- Icon-only buttons are named by `aria-label`, so sighted touch users get no label: `CatalogTable.tsx:244` `엿보기` (eye icon), `:258` `다운로드`, `VariableTable.tsx:177` `변수 N 빼기` (glyph `×`).
- These tooltips repeat visible text, so nothing is lost: `upload/UploadModal.tsx:1752` (visible at `:1737` `.rg-why`) and `AccountAdminPage.tsx:357`.

### 3.4 Mouse-only handlers
- `preview/PreviewPanels.tsx:298` `onMouseMove` and `:306` `onMouseLeave` drive the cursor lat/lon HUD (`data-testid="preview-cursor-hud"`, `:416-421`). There is no pointer or touch path. On touch the HUD either stays at `HUD_IDLE` or keeps the last tapped point from compatibility mouse events (not verified).
- Double-click fits the map to the data: `PreviewPanels.tsx:317`, `upload/PreviewPanel.tsx:650`, `:810`. Nothing else does this: the zoom row (`PreviewZoomControls.tsx:21-27`) has `확대` · `축소` · `기본 배율로`, and `기본 배율로` resets the zoom instead of fitting to the data.
- Wheel zoom: `preview/useZoomPan.ts:339`, with a native listener `{ passive: false }` at `:378`. Mouse or trackpad only.
- Backdrop-dismiss guards use `onMouseDown`: `UploadModal.tsx:1402`, `lineage/LineageFixModal.tsx:105`, `lineage/ParentPicker.tsx:281`, `upload/PreviewExpandOverlay.tsx:32`. A tap produces a compatibility mousedown, so this probably works (not verified).
- Drag-and-drop upload: `upload/FileDropCard.tsx:188` `onDragOver`, `:192` `onDrop`; `UploadModal.tsx:997-1013` document-level `dragover`/`drop`. The button file chooser (`.up-file-choose`) is the touch path.
- `project/ProjectCards.tsx:39` modifier-click for a new tab. Desktop only, harmless.

### 3.5 Mouse-only wording in UI strings

| file:line | string | shown where |
|---|---|---|
| `preview/PreviewPanels.tsx:216` | `커서를 지도 위로` (`HUD_IDLE`) | map preview HUD, always shown when bounds exist (detail preview, unregistered preview) |
| `common/toastCopy.ts:54` | `휠로 확대하고 끌어서 움직여요` (`VIEWER_HINT`, row `V-01` at `:243`) | not rendered anywhere in `src` today (only the copy registry and a test). Wheel-only if it gets wired in |
| `upload/FileDropCard.tsx:207`, `:211` | `파일을 끌어다 놓으세요` · `여러 개를 한 번에, 폴더째 끌어다 놓아도 돼요` | upload drop zone |
| `upload/UploadModal.tsx:1479` | `같은 파일을 다시 끌어다 놓으면 남은 조각부터 이어서 올라가요.` | upload resume. The instruction mentions drag-and-drop only |
| The reverse case (touch wording shown by width to mouse users): `CatalogTable.tsx:96`, `ProjectDatasetTable.tsx:37`, `AccountAdminPage.tsx:307`, `ProjectTable.tsx:11` | `표를 좌우로 밀면 나머지 항목과 작업을 볼 수 있어요.` / `표를 좌우로 밀면 나머지 항목을 볼 수 있어요.` | shown at ≤1100 (`primitives.css:119`), including 1024–1100 mouse windows |

Strings that already work for both inputs: `common/toastCopy.ts:101` `각 데이터를 누르면 그 상세로 가요`, `lineage/LineageSection.tsx:25` `… 데이터 상자를 누르면 그 상세로 가요`, `datasetpreview/ValueLookupPanel.tsx:76` `지도의 한 점을 누르면 그 자리의 값을 보여 줘요.`

### 3.6 Gestures
- **Pan with Pointer Events:** `useZoomPan.ts:395-431` `onPointerDown` + `setPointerCapture` (`:424`); window `pointermove`/`pointerup`/`pointercancel` (`:531-533`); inertia. A one-finger touch drag works.
- **Pinch: not supported.** A second pointer is ignored while dragging: `useZoomPan.ts:404` "끌기 중 다른 포인터(두 번째 손가락)의 누름은 무시한다 — 첫 포인터가 끝날 때까지(A27)." There is no `gesturestart`, `TouchEvent` or two-pointer distance code.
- **`touch-action`: one rule only**, `preview.css:199` `.pv-viewport { touch-action: none; user-select: none }`. The detail and preview map (`PreviewPanels`) and the upload preview and expand viewport (`upload/PreviewPanel.tsx:645`, `:801`) share it. A touch that starts on the map cannot scroll the page, and browser pinch-zoom is off there too. With the map near full width at 390px, scrolling has to start outside the map. The only zoom paths on touch are the overlay buttons (`PreviewZoomControls`).
- `shell.css:4` `-webkit-tap-highlight-color: transparent` removes native tap feedback, so tap feedback depends on the `:active` rules.
- Orientation change is covered by the window `resize` listener (`useZoomPan.ts:575`). Nothing else listens for orientation.

### 3.7 Verification harness
- The visual baseline (`frontend/scripts/visual-baseline/capture.py:159`) only calls `agent-browser set viewport W H DPR`, with widths 375/768/1440 (34 scenes; one scene has only 375/768), height 900 and DPR 1 (`scenes.json:4-7`). There is **no touch emulation**, so the `(pointer: coarse)` branch and the hover-less state are never captured. It also has no 1024/1180 tablet-landscape width and no short landscape viewport.

---

## 4. Mobile platform

### 4.1 Viewport meta
- `frontend/index.html:5` `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />`. User zoom is not disabled. `viewport-fit=cover` makes the safe-area insets non-zero, so the app has to pad for them (see 4.2).
- `audit-design.html`, `audit-upload.html` and `audit-selected-preview.html` do **not** set `viewport-fit=cover`, so audit builds cannot show the safe-area behaviour.

### 4.2 `env(safe-area-*)`: 6 uses in 2 files, and 5 are dead

| file:line | rule | status |
|---|---|---|
| `shell.css:418-419` | `.gnb padding-left/right: max(10px, env(safe-area-inset-left/right))` (≤640) | DEAD: `shell.css:463 .gnb { padding-inline: 12px }` |
| `shell.css:421` | `.appmain { padding-bottom: env(safe-area-inset-bottom) }` (≤640) | live |
| `catalog.css:189-191` | `.catalog-page` padding left/right/bottom with insets (≤640) | DEAD: `catalog.css:211`, then `shell.css:443` |

- Every inset rule sits inside `max-width: 640px`. An iPhone in landscape (844–932 wide) has its notch inset on the left or right and gets no inset padding.
- Bottom-anchored elements without an inset: `upload.css:627` register footer `.reg-actions { position:fixed; bottom:0; left:0; right:0 }` (holds 다음/등록 buttons); `catalog.css:234` column-menu sheet at `bottom:16px`; `upload.css:698` calendar sheet at `bottom:12px`; full-screen `.mb-takeover` (`upload.css:9-16`, content `height:100%`).

### 4.3 `100vh` vs `dvh`/`svh`
- `dvh`, 11 uses: `primitives.css:147` (`.modal--dialog`), `dashboard.css:407`, `project.css:340,579,592`, `login.css:6` (`min-height:100dvh`), `login.css:194`, `lineage.css:294,338`, `catalog.css:234` (60dvh), `upload.css:698` (80dvh). `svh`/`lvh`: 0.
- `vh`, 5 uses that remain: `lab.css:37` `.labinfo-modal { max-height: 90vh }`, `lineage.css:309` `max-height: 42vh`, `upload.css:575` `.modal.pvx { max-height: 92vh }` (preview expand), `upload.css:581` `.pvx-b { height: min(70vh, 640px) }`, `upload.css:598` `.up-empty .modal-takeover { max-height: 90vh }`. On iOS Safari `vh` is the large viewport, so these can run under the browser toolbar.
- `catalog.css:19-20` has an orphan comment ("dvh 를 쓰되 vh 를 먼저 적어 폴백을 남긴다") with no rule after it that uses either unit.
- `100vw` (includes the classic scrollbar width): `lineage.css:294,338`, `catalog.css:194`, `upload.css:509,627`, and `96vw`/`94vw`/`60vw` at `upload.css:575,598`, `shell.css:63`.

### 4.4 Font sizes: px vs rem
- Type tokens are rem (`tokens.css:98-104`, "글자 크기는 rem(뿌리 16px 기준 값 무변 · 브라우저 기본 글자 설정을 따른다 …)").
- Declarations: **192 px** `font-size`, 135 `var(--text-*)`, 1 `max(16px, 1em)`. So 58% skip the tokens and do not scale with the browser font setting.
- px values: 13px ×142, 14 ×13, 16 ×12, 18 ×6, 20 ×5, 22 ×3, 24 ×3, 15 ×3, 9 ×1 (`catalog.css:51`, decorative `▾`), 17, 28, 31, 36 ×1 each.
- By file: upload 47, project 31, detail 21, preview 15, dashboard 15, catalog 15, lineageGraph 14, lineage 12, search 6, approval 6, shell 3, primitives 2, login 2, base 1, lab 1, toast 1.

### 4.5 Input `font-size` < 16px (iOS focus zoom)
- The 16px floor only applies at ≤640 (9 declarations, see 1.4-8). Above 640, `body { font-size: var(--text-body) }` (0.9375rem = 15px, `shell.css:99`) and `:is(.inp, .sel) { font: inherit }` (`primitives.css:53`) give 15px inputs.
- An **iPhone in landscape (667–932 CSS px) is above 640**, so the focus auto-zoom comes back. The `(pointer: coarse)` block does not include the floor. iPadOS behaviour was not verified.

### 4.6 Fixed and sticky bars
- Sticky:
  - `shell.css:108` `.gnb` top 0, z 100. It becomes 2 rows at ≤900, and `Gnb.tsx:79` measures its height into `--shell-gnb-offset`.
  - `detail.css:188` `.dsec-menu` top `var(--shell-gnb-offset)`, z 5.
  - `catalog.css:26`, `:60-61` table header.
  - `upload.css:295` `.reg-actions` bottom 0.
  - `upload.css:644` register `.up-split-preview` top 0, static at ≤1023.
  - `login.css:212` account table right column, ≥1024.
- Fixed:
  - Backdrops: `primitives.css:129` `.modal-back`, `lab.css:24`, `project.css:327`, `upload.css:10` (`.mb-takeover`), `:308` (`.confirm-back`), `:572` (`.pvx-back`), `login.css:190`, `:241` (`.auth-expiry-overlay`).
  - Bars and sheets: `upload.css:627` (`.reg-actions`), `catalog.css:234` (≤640 sheet), `upload.css:698` (≤640 sheet).
- On a 390px dataset detail page the sticky 2-row GNB and the sticky `.dsec-menu` stack above the map preview and reduce its visible height. Not measured in a browser.

### 4.7 Other
- Only project modals lock body scroll: `project.css:597` `body:has(.pj-modal-back) { overflow: hidden; }`. The lab-info, lineage find/fix, upload takeover, confirm and preview-expand modals do not. There is no `overscroll-behavior` anywhere, so scrolling inside a modal chains to the page on touch.
- `inputMode="numeric"` appears 3 times (`DatasetEditForm.tsx:151`, `PeriodCalendarPopover.tsx:167`, `RegisterArea.tsx:579`). There is no `enterKeyHint` and no `text-size-adjust`.
- `primitives.css:114` `-webkit-overflow-scrolling: touch` does nothing in current browsers.

---

## 5. Fixture vs real values

Fixture files checked: `components/catalog/fixture.ts`, `components/detail/fixture.ts`, `components/project/fixture.ts`, `components/lineage/graphFixture.ts`, `test/factories.ts`, `audit-design.tsx`, `audit-upload.tsx`, `audit-selected-preview.tsx`. Lengths are in characters. Hangul is about 1em wide per character and ASCII about 0.55em, so a Hangul string of the same length is roughly twice as wide.

| Field | Real limit (source) | Realistic value (source) | Fixture max (file) | Gap |
|---|---|---|---|---|
| Dataset name | DB: only `length(btrim(name)) > 0` (`db/platform/schema.sql:462`). UI: `maxLength={80}` at register (`upload/RegisterArea.tsx:432`), **none** on edit (`detail/DatasetEditForm.tsx:77`) | 39–44 chars of Hangul, spaces and brackets: `SPI/SPEI 가뭄지수 (L1 Calibrated, 2000-2025 주단위)` (44), `GK-2A NDVI 100 m 경기남부·충청권 월평균 (2023-05)` (39) (`dev-package/SEED-DATA.md` §3.1) | 26 `nakdong_precip_2025_Lv2.nc` (catalog), 25 (detail), 31 `nakdong_flood_index_2025_Lv3.nc` (lineage), 32 `nakdong_station_obs_2025_Lv1.csv` (project rows), **10** `낙동강 강우 원자료` (audit-design) | ×2.5 against the UI max, ×4.4 against seed names in the audit scenes. Fixture names are ASCII snake_case with no spaces, so they only wrap through `overflow-wrap:anywhere` |
| Project name | DB `> 0` only (`schema.sql:1318`). UI `maxLength={100}` (`project/ProjectFormModal.tsx:160`) | UI placeholder `낙동강 유역 홍수기 강우-유출 응답 분석` (22) | 22 (project fixture), 12 `홍수기 강우-유출 분석` (catalog representative), **55** in `audit-upload.tsx`, the only deliberate long string | ×4.5 against 100 everywhere except audit-upload |
| Project description | UI 500 (`ProjectFormModal.tsx:180`) | — | 85 (project fixture) | ×6 |
| Lab name | DB `> 0` only (`schema.sql:98`). No UI max | `고려대학교 수문학연구실` (12, `infra/staging` seed). `login.css:221` records a real lab name truncated to `수자원환경…` | 8 `수자원순환연구실` (factories, audit-design, audit-upload), 7 `기후예측연구실` | Unbounded. The GNB `.labswitch` is capped at 180px, then 132px at ≤1000, and is icon-only at ≤740 |
| Person name | API `max_length=128` (`core-api/app/routes/accounts.py:26`) | — | 2–5 (`호랑이`, `표범`, `사자 교수`) | ×25 |
| Email | API 320 (`accounts.py:25`) | — | 70 in `audit-design.tsx:45` (deliberately long) | covered |
| File name / relative path | DB ≤255 (`schema.sql:530, 1155-1156, 1245-1246`). `relative_path` ≤1024 (`schema.sql:802, 1171, 1248`) | 72-char relative path `01.level-data/02.vegetation/02.vegetation/Lv.1/GK2A_NDVI_mean_202305.tif` (SEED-DATA) | 26 (detail), 7 `rain.nc` (audit-design), 8 `강수_첫째.nc` (audit-selected-preview) | ×10–35. The preview file `<select>` shows the full name only in `title` (3.3) |
| Lineage method label | UI `maxLength={120}` (`lineage/LineageStep.tsx:324`) | — | 14 `유역 클리핑 · 유역 평균` (graphFixture) | ×8. The ellipsis path (`.lin-way`, `title`) is never exercised |
| Variables per dataset | DB rows unbounded (`schema.sql:638-643`), names unbounded | — | 1 variable, 17 chars `시간별 격자 강수량 (tp, mm)` (detail fixture). Catalog rows: none | lists and chips are never stressed |
| Projects per dataset (`외 N` chip) | unbounded (`d6_project_dataset`) | — | `moreCount` max 1 (catalog fixture) | the tooltip list is never long |
| Pieces per dataset | `file_count` integer (`schema.sql:378`) | D-12 has 141 pieces (SEED-DATA) | 72 (catalog, project) | small |
| Dataset summary | UI 3000 (`RegisterArea.tsx:662`) | — | 15 (detail), 22 (audit-design search) | ×136 |
| Grid description | DB and UI 1000 (`schema.sql:513`, `RegisterArea.tsx:640`) | — | none | — |
| Access-request reason / verification cancel reason | DB 300 / 120 (`schema.sql:273, 341`). UI 300 / 120 | — | none in audit scenes | — |
| Search query | UI 200 (`search/types.ts:16`) | — | short | — |

The fixtures copy the mockup ledger ("값은 정본 목업 … 그대로다. 새 데이터를 지어내지 않는다", `catalog/fixture.ts:2`). They represent the mockup, not the realistic maxima. Apart from the email and the audit-upload project name, no scene tests long Hangul names at 375 or 390px.

---

## 6. `docs/design-system.md`: what it says about width and touch

Quoted lines:
- `:22` "| tokens | `frontend/src/shell/tokens.css` | 저장소 유일의 `:root` — 라이트 한 블록 · 900px 분기 · 다크 `:root[data-theme="dark"]` 한 블록 · 640px 분기 | …". It does not mention the `(pointer: coarse)` block, although the `tokens.css:7` header does.
- `:23` "| base | … | 원소 규칙 — `*` box-sizing · 폼 원소 글꼴 · `:focus-visible` 윤곽 · 640px 입력 글자 바닥 | …"
- `:46` "라이트 `:root` 이름 85 · 다크 블록 이름 43 · 폭 분기에서 다시 정의하는 이름 5 · 다크 동일 면제 6"
- `:124-127` token rows: `--space-page` `32px` `(max-width: 640px): 16px` … `--control-height` `40px` `(max-width: 640px): 44px`<br>`(pointer: coarse): 44px`
- `:136` "`--shell-gnb-offset` | `var(--shell-gnb-height)` | 별칭 따라감 | `(max-width: 900px): 110px`"
- `:173` "`.btn-sm`(작은 단추 · 640px 이하 또는 터치가 주 입력인 기기에서는 `--control-height`)"
- `:177` "`.table-scroll-hint`(1100px 이하에서 보임)"
- `:209-211`, `:219` list the primitive rules with their media variants (`(max-width: 640px), (pointer: coarse)`, `(max-width: 640px)`, `(max-width: 1100px)`).
- `:255-256` page containers "폭 100% · 최대 1280px" and search "최대 920px".
- `:260` "… 지금 셸 규칙에 순서로 지던 화면 7파일의 같은 선택자 선언(…)과 죽어 있던 `@media` padding 규칙이 살아난다."
- `:279` "새 화면·새 상태는 `frontend/scripts/visual-baseline/scenes.json` 에 캡처 장면을 더하고(3폭 × 2테마) 착수 기준 캡처와 대조한다(⑧)."
- `:280` "글자 13px 이상 …" and `:281` "누름 피드백 = hover 의 한 단 진한 값(`:active`) …"

Not covered:
1. **No width scale.** No named steps, no list of allowed values (17 are in use), no max-width vs min-width convention, no px vs em decision. The GNB's 5-step ladder comes from the mockup (`shell.css:365` cites `데이터_찾기_260817.html:138~168`), not from this doc.
2. **No device model.** Phone, tablet and PC are not defined, and there is no landscape policy. Phone landscape overlaps tablet portrait (section 2).
3. **Input mode is covered only by `--control-height` and `.btn-sm`.** Missing: a touch-target minimum for other controls (screens set 44px only at ≤640), a policy for guarding hover styles with `(hover: hover)`, a rule against information that lives only in `title` or hover (3.3), a gesture contract (pan, pinch, wheel and double-click alternatives, `touch-action` policy), and a wording rule (`커서`, `휠`, `끌어다` vs `누르면`, `밀면`).
4. **Mobile platform is covered only by the base-layer line "640px 입력 글자 바닥".** Missing: the safe-area rule for fixed and sticky bars (and for landscape), `dvh` vs `vh`, the 16px floor above 640 on touch devices, modal scroll lock and `overscroll-behavior`, and px vs rem for font sizes (192 px declarations against rem tokens).
5. **The gate `frontend-design-lint` (⑥ a–h)** does not check `@media`: values, duplicates and dead rules pass unmeasured.
6. **The capture baseline (⑤ `:279`, ⑧)** is 3 widths (375/768/1440) at height 900 with no touch emulation, no tablet-landscape width (1024/1180) and no short landscape viewport. The fixtures use short strings (section 5).
7. **Content-driven breakpoints** (account table 1024/1536, table-scroll hint 1100) are not listed as allowed exceptions, and there is no container-query guidance.
8. **No pattern for tool overlays on a canvas or map at narrow widths.** This is the pilot screen: `.pv-overlay-tr/br/bl` have no width rules (`preview.css:211-281`), and the only preview width rule (`preview.css:593`) makes the overlay buttons bigger.
