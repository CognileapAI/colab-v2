# P2 design-system.css 해체 지도 (조사 · 2026-09-24)

대상: `frontend/src/shell/design-system.css` (223줄, 규칙 블록 **192개**). 계획: `dev-package/reports/design-system/20260924/architecture.md` §2-1.
방법: frontend/src 의 CSS 19파일(규칙 1319개)을 주석 제거 후 블록 단위로 파싱. 클래스 사용처는 src 아래 ts·tsx 전체 + audit-*.tsx 에서 단어 경계 정규식으로 셈. 충돌 판정은 휴리스틱(마지막 compound 클래스 일치 + 화면 뿌리 클래스 호환) — 과대·과소 검출 가능, 이관 시 부록 A 를 수기 확인.

## 0. 선행 사실 (cascade 순서)
- `main.tsx` → `shell/styles.ts` 한 곳이 순서를 정한다: pretendard → catalog → detail → project → members → lab → search → dashboard → preview → lineage → lineageGraph → upload → approval → toast → variableTable → login → **shell.css**. 라우트·컴포넌트의 개별 css import 는 같은 모듈이라 순서를 바꾸지 않음.
- `shell.css` 1–2행이 tokens.css, design-system.css 를 @import → design-system.css 는 **모든 화면 CSS 뒤**. 현재 DS 규칙은 (a) `:is(.colab-ui, .design-preview)` 접두의 +0,1,0, (b) 뒤 순서, 두 가지로 이긴다.
- `members.css:3` 가 tokens.css 를 다시 @import (중복 적재 — P2 에서 제거 또는 층 지정 필요).
- `.colab-ui` 부여처: index.html body, audit-selected-preview.html body, audit-design.tsx · audit-upload.tsx. `.design-preview` 는 audit-design.tsx 만. src 코드에는 없다.
- `:is()` 목록은 인자 중 **최대** 특이도를 취한다 → rule 105 `:is(.inp, .sel, .login-input, .pv-control select)` 는 `.inp` 에도 0,2,1(접두 포함)을 준다. 해체 후 `.inp` 단독 0,1,0.

## 1. 규칙 인벤토리 (192)

**소유자 집계**: shell 21 · primitive 22 · pattern 5 · screen 137 · mixed 5 · drop 2

**primitive 세부**: primitive:field 4 · primitive:table 6 · primitive:chip 4 · primitive:btn 3 · primitive:card 2 · primitive:modal 3 — btn·card 가 적은 것은 계열 규칙 다수가 화면 전용 클래스(.pj-*, .dash-*)로 쓰였기 때문.

- mixed 5 = 선택자 목록이 여러 소유자로 쪼개져야 하는 규칙(9, 83, 106, 110, 112).
- 선택자 전체가 죽은 규칙 **0**. 죽은 분기 2건: `.dt-card`(rule 110·112), `.pj-card`(rule 110) — TSX·audit 사용 0.
- drop 2 는 dead 가 아니라 **중복**: rule 89(= rule 48, @640 동일값), rule 129(= shell.css:99 의 :where() focus-visible 동일값).
- screen 137 대략 내역: project.css 약 40 · dashboard.css 약 28 · catalog.css 약 27 · upload.css 15 · search.css 12 · lineage 4 · preview 4 · detail 2 · lab 2 · login 2 · lineageGraph 1.
- 충돌 열 기호: P=PREFIX(접두로만 이김) O=ORDER(동률, 뒤 순서로 이김) S=SPEC(접두 없어도 이김) D=이미 짐.

| # | 위치 | selector (접두 제거) | decl | owner | target | note |
|---|---|---|---|---|---|---|
| 1 | L2 | :is(.colab-ui, .design-preview) | 3 | shell | shell.css (base) | 루트 타이포·tap-highlight → @layer base |
| 2 | L3 | :is(button, a, input, select, textarea) | 1 | shell | shell.css (base) | 루트 타이포·tap-highlight → @layer base |
| 3 | L4 | :is(input, textarea)::placeholder | 2 | primitive:field | primitives.css .field |  · 충돌:PD |
| 4 | L5 | :is(.catalog-page, .lab-page, .project-page) | 5 | pattern:page | patterns.css .page | max-width 1280 · padding var(--space-page) · 충돌:P |
| 5 | L6 | :is(.page-head h1, .search-hero h1) | 4 | pattern:page-head | patterns.css .page-head h1 |  · 충돌:OP |
| 6 | L7 | .catalog-page .page-head | 2 | screen | catalog.css |  · 충돌:P |
| 7 | L8 | .catalog-page .desc | 3 | screen | catalog.css |  · 충돌:P |
| 8 | L9 | .catalog-page .hcnt | 4 | screen | catalog.css | .hcnt = badge 후보 |
| 9 | L10 | :is(.card, .dash-card, .dash-tile, .pj-modal) | 4 | mixed | primitives.css .card + dashboard.css + project.css | .card→card / .dash-card·.dash-tile→dashboard / .pj-modal→project(또는 modal) · 충돌:POD |
| 10 | L11 | .catalog-filters | 2 | screen | catalog.css |  · 충돌:P |
| 11 | L12 | .catalog-filters .axis-pick | 1 | screen | catalog.css |  · 충돌:P |
| 12 | L13 | .axis-k | 2 | screen | catalog.css |  · 충돌:O |
| 13 | L14 | .catalog-filters select | 3 | screen | catalog.css |  · 충돌:PD |
| 14 | L15 | .tblwrap | 1 | primitive:table | primitives.css .table-scroll | .tblwrap max-height none · 충돌:P |
| 15 | L16 | .tbl | 2 | primitive:table | primitives.css .table | .tbl 은 catalog·members 두 화면 |
| 16 | L17 | .tbl th | 3 | primitive:table | primitives.css .table | .tbl 은 catalog·members 두 화면 · 충돌:P |
| 17 | L18 | .tbl th .thf | 2 | screen | catalog.css |  |
| 18 | L19 | .tbl td | 1 | primitive:table | primitives.css .table | .tbl 은 catalog·members 두 화면 · 충돌:POD |
| 19 | L20 | .tbl .fname | 5 | screen | catalog.css |  · 충돌:P |
| 20 | L21 | .fname .catalog-open | 4 | screen | catalog.css |  |
| 21 | L22 | .fname .chip | 1 | screen | catalog.css |  |
| 22 | L23 | .tbl td:nth-child(4) | 3 | screen | catalog.css |  · 충돌:SP |
| 23 | L24 | .tbl .catalog-open | 1 | screen | catalog.css |  |
| 24 | L25 | .tbl .rowact .ra | 1 | screen | catalog.css |  · 충돌:P |
| 25 | L26 | .tbl .rowact .rab | 2 | screen | catalog.css |  · 충돌:P |
| 26 | L27 | .fchips | 2 | screen | catalog.css |  · 충돌:P |
| 27 | L28 | .fchips .fc | 1 | screen | catalog.css |  · 충돌:P |
| 28 | L29 | .fchips .fc button | 2 | screen | catalog.css |  · 충돌:SP |
| 29 | L30 | .colmenu button | 1 | screen | catalog.css |  |
| 30 | L31 | .crosslink | 2 | screen | catalog.css + search.css | .crosslink 두 화면 · 충돌:P |
| 31 | L32 | .lab-page .search-hero | 3 | screen | search.css | search-hero · 충돌:P |
| 32 | L33 | .search-hero h1 | 1 | screen | search.css | search-hero |
| 33 | L34 | .search-hero input | 3 | screen | search.css | search-hero · 충돌:DP |
| 34 | L35 | .search-hero button | 1 | screen | search.css | search-hero · 충돌:POD |
| 35 | L36 | .search-hero .hero-note | 2 | screen | search.css | search-hero · 충돌:P |
| 36 | L37 | .dash-columns | 3 | screen | dashboard.css |  · 충돌:P |
| 37 | L38 | .dash-col | 1 | screen | dashboard.css |  · 충돌:P |
| 38 | L39 | .dash-section-label | 4 | screen | dashboard.css |  · 충돌:P |
| 39 | L40 | .dash-card | 1 | screen | dashboard.css |  · 충돌:P |
| 40 | L41 | .dash-card-head | 3 | screen | dashboard.css |  · 충돌:P |
| 41 | L42 | .dash-card-head h2 | 3 | screen | dashboard.css |  · 충돌:PO |
| 42 | L43 | .dash-bar | 5 | screen | dashboard.css |  · 충돌:P |
| 43 | L44 | .dash-bar-track | 1 | screen | dashboard.css |  · 충돌:P |
| 44 | L45 | .dash-bar-fill | 1 | screen | dashboard.css |  · 충돌:P |
| 45 | L46 | :is(.dash-note, .dash-calc, .dash-zero, .dash-lead) | 1 | screen | dashboard.css |  |
| 46 | L47 | .dash-calc | 1 | screen | dashboard.css |  · 충돌:P |
| 47 | L48 | .dash-tiles | 1 | screen | dashboard.css |  · 충돌:P |
| 48 | L49 | .dash-tile | 1 | screen | dashboard.css |  · 충돌:P |
| 49 | L50 | .dash-tile strong | 5 | screen | dashboard.css |  · 충돌:PD |
| 50 | L51 | .dash-quiet | 2 | screen | dashboard.css |  |
| 51 | L52 | .dash-open-catalog | 4 | screen | dashboard.css |  · 충돌:P |
| 52 | L53 | .dash-recent button | 3 | screen | dashboard.css |  · 충돌:OPD |
| 53 | L54 | .todo-grp h3 | 2 | screen | dashboard.css |  · 충돌:POD |
| 54 | L55 | .titem | 4 | screen | dashboard.css |  · 충돌:P |
| 55 | L56 | .titem:last-child | 1 | screen | dashboard.css |  |
| 56 | L57 | .titem button | 4 | screen | dashboard.css |  · 충돌:POD |
| 57 | L58 | :is(.todo-more, .todo-all) | 2 | screen | dashboard.css |  |
| 58 | L59 | .dash-steps | 2 | screen | dashboard.css |  · 충돌:P |
| 59 | L60 | .dash-step-no | 3 | screen | dashboard.css |  · 충돌:P |
| 60 | L61 | .pj-modal-back | 2 | screen | project.css | .pj-modal* = modal 후보(현재 .modal 과 별계열) · 충돌:P |
| 61 | L62 | .pj-modal | 2 | screen | project.css | .pj-modal* = modal 후보(현재 .modal 과 별계열) · 충돌:P |
| 62 | L63 | .pj-modal-h | 1 | screen | project.css | .pj-modal* = modal 후보(현재 .modal 과 별계열) · 충돌:P |
| 63 | L64 | .pj-modal-h h3 | 3 | screen | project.css | .pj-modal* = modal 후보(현재 .modal 과 별계열) · 충돌:POD |
| 64 | L65 | .pj-x | 5 | screen | project.css | .pj-modal* = modal 후보(현재 .modal 과 별계열) · 충돌:P |
| 65 | L66 | .pj-modal-b | 1 | screen | project.css | .pj-modal* = modal 후보(현재 .modal 과 별계열) · 충돌:P |
| 66 | L67 | .pj-modal-f | 1 | screen | project.css | .pj-modal* = modal 후보(현재 .modal 과 별계열) · 충돌:P |
| 67 | L68 | .pj-row | 1 | screen | project.css |  · 충돌:P |
| 68 | L69 | .pj-row label | 4 | screen | project.css |  · 충돌:OPD |
| 69 | L70 | :is(.pj-inp, .pj-tarea) | 8 | screen | project.css | .pj-inp·.pj-tarea = field 후보 · 충돌:P |
| 70 | L71 | .pj-tarea | 1 | screen | project.css |  · 충돌:P |
| 71 | L72 | .pj-seg | 5 | screen | project.css | .pj-seg = tabs(segmented) 후보 · 충돌:P |
| 72 | L73 | .pj-seg button | 4 | screen | project.css | .pj-seg = tabs(segmented) 후보 · 충돌:OPD |
| 73 | L74 | .pj-seg button.on | 3 | screen | project.css | .pj-seg = tabs(segmented) 후보 · 충돌:P |
| 74 | L75 | :is(.pj-defnote, .pj-hint) | 3 | screen | project.css |  · 충돌:P |
| 75 | L76 | .pj-fgroup | 4 | screen | project.css |  · 충돌:P |
| 76 | L77 | .pj-fgroup .pj-row | 1 | screen | project.css |  · 충돌:S |
| 77 | L78 | .pj-fgroup-h | 1 | screen | project.css |  · 충돌:P |
| 78 | L79 | .chip--lineage | 2 | primitive:chip | primitives.css .chip |  |
| 79 | L80 | .pj-err | 2 | screen | project.css |  · 충돌:P |
| 80 | L81 | .btn | 4 | primitive:btn | primitives.css .btn |  · 충돌:PD |
| 81 | L82 | .btn-primary | 3 | primitive:btn | primitives.css .btn |  · 충돌:PO |
| 82 | L83 | .btn-secondary | 3 | primitive:btn | primitives.css .btn |  |
| 83 | L84 | .btn-primary:active, .search-hero button:active | 1 | mixed | primitives.css .btn + search.css | .btn-primary:active / .search-hero button:active · 충돌:SPO |
| 84 | L86 (max-width: 900px) | .dash-columns | 1 | screen | dashboard.css |  · 충돌:P |
| 85 | L89 (max-width: 640px) | .catalog-filters | 1 | screen | catalog.css |  · 충돌:P |
| 86 | L90 (max-width: 640px) | .lab-page .search-hero | 2 | screen | search.css | search-hero |
| 87 | L91 (max-width: 640px) | .search-hero h1 | 1 | screen | search.css | search-hero · 충돌:OP |
| 88 | L92 (max-width: 640px) | .dash-tiles | 1 | screen | dashboard.css |  · 충돌:P |
| 89 | L93 (max-width: 640px) | .dash-tile | 1 | drop | - | rule 48 과 같은 값(padding 16px) 중복 · 충돌:P |
| 90 | L94 (max-width: 640px) | .dash-bar | 2 | screen | dashboard.css |  · 충돌:P |
| 91 | L95 (max-width: 640px) | .dash-steps | 2 | screen | dashboard.css |  · 충돌:P |
| 92 | L96 (max-width: 640px) | .pj-modal-back | 1 | screen | project.css | .pj-modal* = modal 후보(현재 .modal 과 별계열) · 충돌:P |
| 93 | L97 (max-width: 640px) | .pj-modal | 1 | screen | project.css | .pj-modal* = modal 후보(현재 .modal 과 별계열) · 충돌:P |
| 94 | L98 (max-width: 640px) | .pj-modal-h | 1 | screen | project.css | .pj-modal* = modal 후보(현재 .modal 과 별계열) · 충돌:P |
| 95 | L99 (max-width: 640px) | .pj-fgroup | 1 | screen | project.css |  · 충돌:P |
| 96 | L100 (max-width: 640px) | .pj-seg button | 1 | screen | project.css | .pj-seg = tabs(segmented) 후보 |
| 97 | L101 (max-width: 640px) | .colmenu button | 1 | screen | catalog.css |  |
| 98 | L102 (max-width: 640px) | .tbl .rowact .rab | 2 | screen | catalog.css |  · 충돌:P |
| 99 | L105 | .fname .lock | 3 | screen | catalog.css |  |
| 100 | L106 | body:is(.colab-ui, .design-preview):has(.pj-modal-back) | 1 | screen | project.css | body:has(.pj-modal-back) 스크롤 잠금 — modal 공용화 시 primitive |
| 101 | L109 (max-width: 640px) | .tbl .colmenu | 8 | screen | catalog.css |  · 충돌:S |
| 102 | L112 | .colmenu .cm-box | 4 | screen | catalog.css |  · 충돌:P |
| 103 | L115 | .theme-switcher | 10 | shell | shell.css | gnb·theme-switcher |
| 104 | L116 | .login-theme | 3 | screen | login.css | .login-submit = btn 후보 |
| 105 | L117 | :is(.inp, .sel, .login-input, .pv-control select) | 7 | primitive:field | primitives.css .field | .login-input→login / .pv-control select→preview 분리 · 충돌:SPOD |
| 106 | L118 | :is(.lin, .pv-zoom, .pv-shot, .modal-h) button:where(:not(.btn)) | 1 | mixed | primitives.css .modal + lineage.css + preview.css | button:where(:not(.btn)) |
| 107 | L119 | input:is([type="checkbox"], [type="radio"]) | 1 | primitive:field | primitives.css .field |  |
| 108 | L120 | :is(.detail-page, .project-detail, .preview-page, .settings-page) | 5 | pattern:page | patterns.css .page | max-width 1280 · padding var(--space-page) · 충돌:P |
| 109 | L121 | .search-page | 3 | pattern:page | patterns.css .page--narrow 또는 search.css | max-width 920 · 충돌:P |
| 110 | L122 | :is(.dt-header, .dt-card, .pj-card, .up-card, .mapstage, .reggate, .regarea) | 2 | mixed | upload.css + detail.css | dt-card·pj-card 분기 dead · 충돌:PO |
| 111 | L123 | :is(.card-h, .card-b) | 1 | primitive:card | primitives.css .card |  · 충돌:POD |
| 112 | L124 | :is(.card-h h3, .pv-h2, .dt-card h3) | 3 | mixed | primitives.css .card + preview.css | .dt-card h3 분기 dead · 충돌:PSOD |
| 113 | L125 | .card-h | 2 | primitive:card | primitives.css .card |  · 충돌:PD |
| 114 | L126 | .search-page .hit | 1 | screen | search.css | 190 은 .notfound(NotFoundPage) 포함 · 충돌:P |
| 115 | L127 | .search-page .hits | 1 | screen | search.css | 190 은 .notfound(NotFoundPage) 포함 · 충돌:P |
| 116 | L128 | :is(.form-row, .pv-control) | 1 | pattern:form | patterns.css .form-row | + .pv-control→preview · 충돌:OP |
| 117 | L129 | :is(.labinfo-modal, .approval-dialog, .modal--dialog) | 4 | primitive:modal | primitives.css .modal | 117 의 .labinfo-modal→lab.css · .approval-dialog→approval.css · 충돌:P |
| 118 | L130 | .modal--dialog:has(.modal-h) | 1 | primitive:modal | primitives.css .modal | 117 의 .labinfo-modal→lab.css · .approval-dialog→approval.css |
| 119 | L131 | .labinfo-modal h3 | 2 | screen | lab.css |  · 충돌:POD |
| 120 | L132 | .labinfo-modal .form-row | 1 | screen | lab.css |  · 충돌:PS |
| 121 | L133 | .modal-takeover .up-steps .card-b | 2 | screen | upload.css |  · 충돌:SP |
| 122 | L134 | .modal-takeover .form-row | 1 | screen | upload.css |  · 충돌:PS |
| 123 | L135 | .modal-takeover .reg-actions .btn | 2 | screen | upload.css |  · 충돌:SP |
| 124 | L136 | .pv-register | 1 | screen | preview.css |  |
| 125 | L137 | .gnb | 1 | shell | shell.css | gnb·theme-switcher · 충돌:P |
| 126 | L138 | .gnb-settings | 1 | shell | shell.css | gnb·theme-switcher · 충돌:P |
| 127 | L139 | .gnb-upload | 1 | shell | shell.css | gnb·theme-switcher |
| 128 | L140 | .login-submit | 1 | screen | login.css | .login-submit = btn 후보 |
| 129 | L141 | :is(button, a, input, select, textarea):focus-visible | 2 | drop | - | shell.css:99 :where() 동일값 중복 — base 로 흡수 · 충돌:O |
| 130 | L143 (max-width: 900px) | .colab-ui .gnb | 5 | shell | shell.css | gnb·theme-switcher · 충돌:P |
| 131 | L144 (max-width: 900px) | .colab-ui .gnb .mainnav | 4 | shell | shell.css | gnb·theme-switcher |
| 132 | L145 (max-width: 900px) | .colab-ui .gnb .mainnav a | 3 | shell | shell.css | gnb·theme-switcher |
| 133 | L146 (max-width: 900px) | .colab-ui .gnb .labswitch | 1 | shell | shell.css | gnb·theme-switcher |
| 134 | L147 (max-width: 900px) | .colab-ui .gnb .avatar-wrap | 1 | shell | shell.css | gnb·theme-switcher |
| 135 | L152 (max-width: 900px) | .colab-ui .gnb :is(.gnb-upload, .gnb-settings) | 1 | shell | shell.css | gnb·theme-switcher · 충돌:S |
| 136 | L153 (max-width: 900px) | .colab-ui .gnb .gnb-more-wrap | 2 | shell | shell.css | gnb·theme-switcher · 충돌:S |
| 137 | L154 (max-width: 900px) | .colab-ui .gnb .gnb-more | 1 | shell | shell.css | gnb·theme-switcher · 충돌:S |
| 138 | L157 (max-width: 640px) | :is(.inp, .sel, .login-input, .pv-control select) | 1 | primitive:field | primitives.css .field |  · 충돌:PODS |
| 139 | L158 (max-width: 640px) | .theme-switcher | 2 | shell | shell.css | gnb·theme-switcher |
| 140 | L159 (max-width: 640px) | .colab-ui .gnb | 2 | shell | shell.css | gnb·theme-switcher · 충돌:P |
| 141 | L160 (max-width: 640px) | .colab-ui .gnb :is(.labswitch, .gnb-settings, .gnb-upload, .gnb-more, .avatar) | 3 | shell | shell.css | gnb·theme-switcher · 충돌:S |
| 142 | L161 (max-width: 640px) | .colab-ui .gnb .avatar | 1 | shell | shell.css | gnb·theme-switcher · 충돌:S |
| 143 | L162 (max-width: 640px) | .colab-ui .gnb .gnb-logout | 1 | shell | shell.css | gnb·theme-switcher |
| 144 | L163 (max-width: 640px) | .pv-basic-grid | 1 | screen | preview.css |  · 충돌:P |
| 145 | L164 (max-width: 640px) | .pv-basic-row dd | 2 | screen | preview.css |  |
| 146 | L165 (max-width: 640px) | .dr-pop | 6 | screen | upload.css |  · 충돌:P |
| 147 | L166 (max-width: 640px) | .dr-cal-d | 1 | screen | upload.css |  · 충돌:P |
| 148 | L167 (max-width: 640px) | :is(.pv-zoom, .pv-shot, .lin) button | 1 | screen | preview.css |  |
| 149 | L170 | .chip--neutral | 2 | primitive:chip | primitives.css .chip |  |
| 150 | L171 | .chip--warning | 2 | primitive:chip | primitives.css .chip |  · 충돌:O |
| 151 | L172 | .detail-page .dt-header h1 | 3 | screen | detail.css |  · 충돌:PS |
| 152 | L173 | .detail-page .dsec-h h2 | 1 | screen | detail.css |  · 충돌:SP |
| 153 | L175 | .chip:where(:not([class*="chip--"])) | 2 | primitive:chip | primitives.css .chip |  · 충돌:P |
| 154 | L176 | .pj-ds-scroll | 2 | screen | project.css |  |
| 155 | L177 | .pj-ds | 1 | screen | project.css |  |
| 156 | L178 | .detail-page :is(.ln, .ln-go) .arw | 2 | screen | lineageGraph.css |  · 충돌:PO |
| 157 | L179 | .up-empty .up-card > .card-b | 1 | screen | upload.css |  · 충돌:SP |
| 158 | L180 | .up-body | 1 | screen | upload.css |  |
| 159 | L181 | .up-body > * | 1 | screen | upload.css |  |
| 160 | L182 | .reggate | 1 | screen | upload.css |  |
| 161 | L184 (max-width: 640px) | .filecard | 1 | screen | upload.css |  |
| 162 | L185 (max-width: 640px) | .filecard .fmeta | 1 | screen | upload.css |  |
| 163 | L186 (max-width: 640px) | .filecard .fkind | 1 | screen | upload.css |  |
| 164 | L187 (max-width: 640px) | .filecard .sel | 1 | screen | upload.css |  · 충돌:P |
| 165 | L188 (max-width: 640px) | .reggate | 2 | screen | upload.css |  · 충돌:P |
| 166 | L189 (max-width: 640px) | .reggate .rg-a | 2 | screen | upload.css |  |
| 167 | L191 | .lin-findbar > label | 1 | screen | lineage.css |  |
| 168 | L192 | .lin-findbar :is(input, select) | 3 | screen | lineage.css |  |
| 169 | L193 | .lin-picker li > button | 5 | screen | lineage.css |  · 충돌:SPD |
| 170 | L194 | .lin-picker li > button[aria-pressed="true"] | 1 | screen | lineage.css |  · 충돌:SP |
| 171 | L195 | :is(.lin-find, .lin-fix, .modal-takeover) .modal-h .x | 9 | primitive:modal | primitives.css .modal-x | .lin-find·.lin-fix·.modal-takeover 공용 닫기 · 충돌:P |
| 172 | L197 | .pj-toolbar | 6 | screen | project.css |  · 충돌:P |
| 173 | L198 | .pj-ctl | 3 | screen | project.css |  · 충돌:P |
| 174 | L199 | .pj-ctl select | 8 | screen | project.css |  · 충돌:PDS |
| 175 | L200 | .pj-views | 2 | screen | project.css | .pj-views = tabs 후보 |
| 176 | L201 | .pj-views button | 4 | screen | project.css | .pj-views = tabs 후보 · 충돌:OPD |
| 177 | L202 | .pj-views button:first-child | 1 | screen | project.css | .pj-views = tabs 후보 · 충돌:PSO |
| 178 | L203 | .pj-views button:last-child | 1 | screen | project.css | .pj-views = tabs 후보 · 충돌:PSO |
| 179 | L204 | .pj-new | 9 | screen | project.css |  · 충돌:P |
| 180 | L205 | .pd-linkurl, .pd-linkurl:visited | 2 | screen | project.css |  |
| 181 | L206 | .table-scroll-hint | 1 | primitive:table | primitives.css .table-scroll-hint |  |
| 182 | L207 | .pj-table | 1 | screen | project.css |  · 충돌:P |
| 183 | L209 (max-width: 1100px) | .table-scroll-hint | 5 | primitive:table | primitives.css .table-scroll-hint |  |
| 184 | L212 (max-width: 640px) | .colab-ui .gnb | 1 | shell | shell.css | gnb·theme-switcher · 충돌:P |
| 185 | L213 (max-width: 640px) | .colab-ui .theme-switcher | 2 | shell | shell.css | gnb·theme-switcher |
| 186 | L214 (max-width: 640px) | .pj-toolbar | 3 | screen | project.css |  · 충돌:P |
| 187 | L215 (max-width: 640px) | .pj-ctl | 1 | screen | project.css |  |
| 188 | L216 (max-width: 640px) | .pj-ctl select | 2 | screen | project.css |  · 충돌:PDS |
| 189 | L217 (max-width: 640px) | .pj-count | 2 | screen | project.css |  · 충돌:P |
| 190 | L220 | :is(.search-page .notice, .notfound) a:where(:not(.strong, .quiet)), :is(.search-page .not | 2 | screen | search.css | 190 은 .notfound(NotFoundPage) 포함 · 충돌:SD |
| 191 | L222 | .search-page :is(.vfilter, .empty-acts .quiet, .empty-acts .strong) | 2 | screen | search.css | 190 은 .notfound(NotFoundPage) 포함 · 충돌:OS |
| 192 | L223 | .search-page .empty-acts | 1 | screen | search.css | 190 은 .notfound(NotFoundPage) 포함 |

## 2. primitive 계열 병합 작업표 (현 정의 전수 · 충돌)

### btn — 정의 40곳 (11파일)
- 기반(display/border/cursor)이 **공용 파일에 없다**: `.btn` 을 members.css:46(height 32px · padding 0 12px · border 1px solid border-strong · bg surface) 와 upload.css:312(border up-line · radius 8px · padding 8px 14px) 두 화면 파일이 각자 정의, 둘 다 전역 적재라 서로 덮는다.
- design-system.css:81 `.btn`: min-height control-height · padding 10px 18px · font-size text-body-sm · radius-sm → members/upload 와 padding·radius 충돌(PREFIX).
- `.btn-primary`: members.css:60(color-white) · upload.css:314 `.btn-strong, .btn-primary`(border-color up-ink) · DS:82(on-primary, border primary-600) → color·border-color 충돌.
- `.btn-primary:hover`(members.css:65, 0,2,0) 가 DS `.btn-primary`(접두 포함 0,2,0, 뒤) 에 **동률 순서로 짐** → 현재 hover 배경 변화 없음. layer 도입 시 hover 가 살아남(시각 변화).
- `.btn-secondary` 는 DS:83 한 곳뿐. `.btn-ghost` members:66·upload:315, `.btn-sm` upload:313, `.btn-danger` approval.css:14 · deletion.css:35(값 동일 2중).
- 버튼형 별 클래스: `.login-submit`(login.css:72 height 40 + DS:140) · `.pj-new`(project.css:65·544 + DS:204 9속성) · `.dash-open-catalog`(dashboard.css:158 + DS:52) · `.gnb-upload`(shell.css:224 + DS:139) · `.modal-takeover .reg-actions .btn`(upload.css:640 height 34 vs DS:135 height auto).

### field (input/select/textarea) — 정의 63곳 (13파일)
- 현 기반: DS:117 `:is(.inp,.sel,.login-input,.pv-control select)` 7속성(min-height control-height · padding 10px 12px · border control · radius-sm · bg surface · color text · font inherit) + DS:157 @640 font-size 16px.
- 경쟁 정의: upload.css:258 `.inp,.sel`(8px 10px · up-line · radius 8px) · lab.css:58 `.labinfo-modal .inp/.sel`(8px 10px · color-border · 8px) · login.css:54 `.login-input`(height 40 · padding 0 12px · border-strong) · variableTable.css:69 `.vartable td .inp`(border none · radius 0 · height 32) · upload.css:617 `.modal-takeover .inp/.sel` · catalog.css:198 + DS:14 `.catalog-filters select` · DS:199 `.pj-ctl select` · DS:192 `.lin-findbar :is(input,select)`.
- 별 계열 `.pj-inp, .pj-tarea`: project.css:411(7px 9px · radius 6px · 13px) vs DS:70(10px 12px · radius-sm · text-body) 전면 충돌.
- upload.css:260 `.inp[readonly]`(bg surface-alt · color up-muted) 를 DS:117 이 **접두로 덮음** → 현재 readonly 표시가 꺼져 있음. layer 도입 시 되살아남.
- focus: shell.css:99 와 DS:141 동일값 중복. login.css:67 · variableTable.css:81 · upload.css:618 가 각자 재정의. placeholder DS:4, checkbox accent DS:119 와 variableTable.css:98 동일값.

### card — 정의 38곳 (9파일)
- `.card` 기반이 공용에 없다: catalog.css:33 `.catalog-page .card` · project.css:278 `.project-detail .card`(radius 10px · border color-border · padding 14px) · upload.css:611 `.modal-takeover .up-steps .card`.
- DS:10 `:is(.card,.dash-card,.dash-tile,.pj-modal)` border-color border-strong · radius-lg → dashboard.css:63·184(radius 10px · border color-border), project.css:352 와 충돌.
- `.card-h/.card-b`: members.css:10·38(14px 18px / 6px 18px) vs DS:123(20px space-card). upload.css:612·615(16px 22px / 20px 22px, 0,3,0) 가 DS 를 이김.
- 카드형 별 계열: `.login-card`(login.css:13) · `.dash-card` · `.dash-tile` · `.hit`(search.css:55 radius 12px) · `.up-card, .mapstage, .reggate, .regarea`(upload.css:92 up-radius) · `.dt-header`.

### chip — 정의 26곳 (9파일)
- 기반 `.chip` 7곳: catalog.css:127(height 21 · 13px · 600) · detail.css:63 `.detail-page .chip`(catalog 사본) · members.css:82(height 24 · surface-hover) · project.css:322(inline-block · border · margin-left 6px) · upload.css:264(#eef2f7 하드코딩) · search.css:82 `.search-page .chip` · lineage.css:233 `.lin .chip`.
- --neutral · --warning: catalog.css:128–129 · detail.css:64–65 · DS:170–171 **동일값 3중**, search.css:86 폴백 사본. lineage.css:238 `.lin .chip--warning` 은 다른 값(lin-over-*) → DS 가 ORDER 로 이김(현재 lineage 전용 색이 안 보임). --verified approval.css:15, --off members.css:104, --lineage DS:79.
- DS:175 `.chip:where(:not([class*=chip--]))` 가 기본 배경 surface-alt → members·upload 배경을 접두로 덮음.

### modal — 정의 115곳 (8파일, upload.css 52)
- 계열 5개 병존: ① `.modal-back / .modal / .modal--dialog / .modal-h/-b/-f` 기반은 **members.css:121–145** 에만 ② `.pj-modal*` project.css:342–391 + DS:61–67·96–98 ③ `.labinfo-modal` lab.css:33 ④ `.approval-dialog` approval.css:3 ⑤ `.modal.modal-takeover` · `.confirm-back .modal` upload.css:25·308.
- 충돌: `.pj-modal` width min(560px) vs DS min(600px), max-height 90vh vs calc(100dvh - 48px) · `.pj-modal-h` padding 14px 16px vs 20px space-card · `.pj-x` font-size 18px vs 24px · `.labinfo-modal` padding 18px · radius 12px vs DS:129 · `.approval-dialog` padding 24px vs DS:129 space-card.
- 닫기 버튼 2계열: DS:195 `.modal-h .x`(lin-find/lin-fix/modal-takeover) 와 `.pj-x`.

### table — 정의 106곳 (7파일)
- `.tbl`(catalog.css 30곳, MemberPermissionGrid 도 사용) · `.account-table`(login.css:146–236 16곳) · `.pj-table, .pj-ds`(project.css:218–264) · `.vartable`(variableTable.css) — 공유 기반 없음.
- 충돌: `.tbl th` gray-500 · 700 · 0.05em(catalog.css:45) vs DS:17 text-muted · 600 · 0 · `.tbl td` 13px 14px vs DS:19 10px 12px · `.tblwrap` max-height calc(100dvh - 232px) vs DS:15 none · `.pj-table` min-width 900px vs DS:207 680px.
- `.table-scroll-hint` 정의는 DS:206·209(≤1100px) 한 곳(접두 없음). 스크롤 래퍼 3종: `.tblwrap`, `.pj-ds-scroll`(DS:176), `.memgrid .card-b`(members.css:41).

### tabs — 정의 17곳
- `.settabs / .st / .st.on` members.css:154–167 (+login.css:118) · `.pj-seg` project.css:431–447 + DS:72–74·100 · `.pj-views` project.css:88–95 + DS:200–203 → 3계열. DS 가 pj-seg radius·padding·배경, pj-views radius 를 덮음.

### toast — toast.css:11 `.toast` 1곳(자체 --toast-* 토큰). DS 관여 없음.

### badge/status — 공용 정의 없음. `.hcnt`(catalog.css:31 + DS:9 pill 배경) 가 유일한 배지형. 상태 표시는 `.chip--verified` · `.verified--pending`(catalog).

**충돌 집계(휴리스틱)**: DS 192규칙 중 **136규칙**이 다른 파일과 값 충돌 **442쌍** — PREFIX 256쌍/124규칙 · ORDER 57/29 · SPEC 89/28 · 이미 짐 40/25. 쌍 목록은 부록 A.

## 3. @layer 도입 시 순서·특이도 위험
- **순서/접두 의존 규칙 128개** (PREFIX ∪ ORDER): 3 4 5 6 7 9 10 11 12 13 14 16 18 19 22 24 25 26 27 28 30 31 33 34 35 36 37 38 39 40 41 42 43 44 46 47 48 49 51 52 53 54 56 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 77 79 80 81 83 84 85 87 88 89 90 91 92 93 94 95 98 102 105 108 109 110 111 112 113 114 115 116 117 119 120 121 122 123 125 126 129 130 138 140 144 146 147 150 151 152 153 156 157 164 165 169 170 171 172 173 174 176 177 178 179 182 184 186 188 189 191
  - primitives/patterns 층으로 가는 규칙은 screens 층의 어떤 특이도 선언에도 진다 → 부록 A 의 상대편 화면 선언을 삭제하거나 값을 맞춰야 현재 모습 유지. 사실상 화면 파일의 옛 값 삭제 목록.
  - 화면 파일로 옮기는 규칙은 접두 0,1,0 을 잃는다 → 같은 층 옛 규칙과 동률이면 뒤 쪽이 이김. 옛 선언과 **병합(값 교체)** 해야 함.
- 되살아나는 상태 선언(현재 DS 가 덮고 있음): `.btn-primary:hover`(members.css:65) · `.inp[readonly]`(upload.css:260) · `.lin .chip--warning`(lineage.css:238).
- 이미 지는 규칙 25개(3 9 13 18 33 34 49 52 53 56 63 68 72 80 105 111 112 113 119 138 169 174 176 188 190): 화면 쪽 0,3,x 가 이김 — 층 이동 후에도 결과 동일(같은 규칙이 다른 상대에겐 이길 수 있어 위 목록과 중복 있음).
- 층 밖(unlayered) 규칙은 모든 층을 이긴다: styles.ts 가 적재하는 화면 CSS 16파일 중 하나라도 screens 층으로 감싸지 않으면 primitives·patterns 를 전부 이김. members.css 의 tokens.css @import 도 층 지정 필요.
- **important 표기**: 전체 CSS 중 shell.css 2건뿐 — 423행 body input/select/textarea 의 font-size max(16px, 1em), 426행 전 요소 transition none · scroll-behavior auto(둘 다 @media 블록 안). 다른 파일 0건. 층 도입 시 important 는 **앞 층이 이김**(역전). 화면 CSS 에 important 가 없어 실영향 없음, base 층 배치 권장.

## 4. 외부 CSS (pretendard)
- shell/styles.ts:2 에서 `pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css` 를 첫 import (패키지 pretendard ^1.3.9).
- 내용: 라이선스 주석 + **@font-face 92개뿐**(at-rule 종류 1, 일반 스타일 규칙 0). family `Pretendard Variable`, font-display swap, unicode-range 분할.
- @font-face 는 cascade 층의 영향을 받지 않는다 → 층 지정 **불필요**. `@layer tokens, base, primitives, patterns, screens;` 선언은 styles.ts 첫 CSS(또는 tokens.css 첫 줄)에 두면 된다.

## 5. P2 에서 깨질 vitest
### 직접 깨짐 — design-system.css 원문을 읽는 2파일 3 it
- test/shell-lth-20260913.test.tsx · describe `I-9 폭 조건 — 접는 단이 CSS 에 서 있다` › it `900px 단에서 「더보기」가 서고 기능 버튼이 접힌다`(DESIGN 의 900px 블록에서 .gnb-more / .gnb-upload / .gnb-settings 검사) · it `휴대전화에서 아바타를 다시 보이게 하지 않는다`(DESIGN 640px 블록의 .gnb .avatar display none). gnb 규칙을 shell.css 로 옮기면 읽는 파일 교체 필요.
- test/account-admin-layout-20260918.test.ts · it `공용 .settabs(members.css) 와 .table-scroll-hint(design-system.css) 를 고치지 않았다`(DESIGN 에 .table-scroll-hint 와 max-width 1100px 블록 포함 검사). primitives.css 로 옮기면 깨짐.
### 계산값 위험 — 3파일 6 it
- vite.config.ts 의 test.css.include 는 catalog · project · shell · tokens · dashboard · search (+ detail · upload 의 ?raw) 만 실제 적재. DS 는 shell.css @import 로 들어온다. 새 primitives.css · patterns.css 를 styles.ts 에서 직접 import 하면 include 정규식 추가 필요(또는 shell.css @import 유지).
- test/dashboard.test.tsx it `뿌리는 좌우 여백과 프로젝트·데이터셋 상세와 같은 최대폭을 갖는다`(maxWidth 1200px 기대 = dashboard.css:9) · it `검색 히어로의 좌우 여백은 뿌리 여백과 겹치지 않는다`. DS rule 4 는 1280px — 통과 중이라면 jsdom 렌더 트리에 .colab-ui 가 없어 DS 가 안 걸리는 것으로 추정 **[미확인: test setup 의 colab-ui 부여 여부]**. .page 패턴을 접두 없이 두면 1280 과 충돌.
- test/project.test.tsx it `목록 뿌리(.project-page)는 좌우 여백과 최대폭을 갖는다` · it `상세 뿌리(.project-detail)는 여백을 갖고 카드는 데이터셋 상세처럼 면(배경)을 갖는다`.
- test/catalog.test.tsx it `헤더 칸이 계산값으로 sticky · top 0 이다` · it `열 이름 버튼은 디자인 최소 본문 크기인 14px보다 작지 않다`(.tbl th .thf).
### 원문(?raw / readFileSync) 재확인 대상 — 18파일
- project, project-cards-a11y-20260913, project-css-tokens(shell.css · tokens.css 포함), shared-css-tokens, css-residual-rc11, design-fix-20260908(shell.css 포함), detail-section-menu, lv-rules-20260907, lab-settings-headings-20260913, preview-layout-20260912, preview-controls-20260912, preview-map-viewport-20260918, preview-slot-4x3, upload, upload-transfer, summary-required-20260905, prd39-rev2-build-20260906, shell(shell.css ?raw). [미완] 파일별 정규식이 이관 대상 선택자를 잡는지 대조.

## 6. 화면별 뿌리 클래스 (screens 층 스코프) [부분 — 전역 선택자 수 미계측]
| 파일 | 뿌리 클래스 | 뿌리 없이 전역인 계열 |
|---|---|---|
| catalog.css | .catalog-page | .tbl, .tblwrap, .chip 계열, .fchips, .colmenu, .lvl-n |
| dashboard.css | .lab-page | .dash-, .titem, .todo- 접두 |
| search.css | .search-page | .search-hero(lab-page 안) |
| project.css | .project-page, .project-detail | .pj-, .pd- 접두, .pcard, .chip |
| detail.css · deletion.css | .detail-page | — |
| preview.css | .preview-page | .pv- 접두(상세 미리보기와 공유) |
| lineage.css | .lin, .lin-find, .lin-fix | — |
| lineageGraph.css | .detail-page 하위 | .lrow, .ln |
| upload.css | .modal-takeover, .up-empty, .confirm-back | .btn 계열, .inp, .sel, .chip 계열, .up-, .dr- 접두 |
| members.css | .memgrid, .settabs | .modal 계열, .btn 계열, .card-h/-b, .chip 계열 |
| lab.css | .labinfo-card, .labinfo-modal | — |
| approval.css | .approval-dialog | .chip--verified |
| login.css | .login, .login.account-admin | .account-, .login- 접두 |
| variableTable.css | .vartable | — |
| toast.css | .toast | — |

## 부록 A. DS 규칙별 충돌 쌍
형식: 분류(P/O/S/D)·상대 파일:줄(@≤폭) 상대 선택자 {상대 특이도} 속성: DS값 ↔ 상대값. DS 특이도는 접두 포함.

| # | 줄 | 충돌 |
|---|---|---|
| 3 | L4 | P·approval/approval.css:7 `.ar-reason textarea` {0,1,1} color: var(--color-text-muted) ↔ var(--color-text)<br>D·detail/detail.css:202 `.detail-page .dt-edit .de-period input` {0,3,1} color: var(--color-text-muted) ↔ var(--color-text)<br>D·detail/detail.css:282 `.detail-page .de-inline input.de-v` {0,3,1} color: var(--color-text-muted) ↔ inherit<br>D·detail/detail.css:300 `.detail-page .dt-edit.de-inline input` {0,3,1} color: var(--color-text-muted) ↔ var(--color-text)<br>P·search/search.css:8 `.search-hero input` {0,1,1} color: var(--color-text-muted) ↔ inherit |
| 4 | L5 | P·catalog/catalog.css:28 `.catalog-page` {0,1,0} padding: var(--space-page) ↔ 24px 20px 40px<br>P·catalog/catalog.css:179@≤640 `.catalog-page` {0,1,0} padding: var(--space-page) ↔ 16px 12px 32px; padding-bottom: 48px ↔ max(32px, env(safe-are<br>P·catalog/catalog.css:203@≤640 `.catalog-page` {0,1,0} padding: var(--space-page) ↔ 20px 16px 32px<br>P·dashboard/dashboard.css:9 `.lab-page` {0,1,0} max-width: 1280px ↔ 1200px; padding: var(--space-page) ↔ 24px 20px 40px<br>P·dashboard/dashboard.css:378@≤640 `.lab-page` {0,1,0} padding: var(--space-page) ↔ 20px 16px 32px<br>P·project/project.css:24 `.project-page` {0,1,0} max-width: 1280px ↔ 1200px; padding: var(--space-page) ↔ 24px 20px 40px |
| 5 | L6 | O·catalog/catalog.css:30 `.catalog-page .page-head h1` {0,2,1} font-size: var(--text-h2) ↔ var(--text-h2, 24px); letter-spacing: -0.02em ↔ -0.023em<br>O·detail/detail.css:41 `.detail-page .dt-header h1` {0,2,1} font-size: var(--text-h2) ↔ 31px; line-height: 1.3 ↔ 1.25; letter-spacing: -0.02em ↔ -0.03<br>P·members/members.css:32 `.settings-page h1` {0,1,1} letter-spacing: -0.02em ↔ -0.023em<br>O·project/project.css:36 `.project-page .page-head h1` {0,2,1} letter-spacing: -0.02em ↔ -0.023em<br>O·project/project.css:42 `.project-detail .pd-head h1` {0,2,1} font-size: var(--text-h2) ↔ 31px; line-height: 1.3 ↔ 1.25; letter-spacing: -0.02em ↔ -0.03<br>P·search/search.css:6 `.search-hero h1` {0,1,1} font-size: var(--text-h2) ↔ var(--text-h2, 24px); letter-spacing: -0.02em ↔ -0.023em<br>O·search/search.css:24 `.search-page .page-head h1` {0,2,1} font-size: var(--text-h2) ↔ var(--text-h2, 24px) |
| 6 | L7 | P·catalog/catalog.css:29 `.catalog-page .page-head` {0,2,0} gap: 8px 12px ↔ 10px; margin-bottom: var(--space-section) ↔ 14px |
| 7 | L8 | P·catalog/catalog.css:32 `.catalog-page .desc` {0,2,0} font-size: var(--text-body-sm) ↔ var(--text-caption) |
| 9 | L10 | P·dashboard/dashboard.css:63 `.dash-card` {0,1,0} border-radius: var(--radius-lg) ↔ 10px<br>P·dashboard/dashboard.css:184 `.dash-tile` {0,1,0} border-radius: var(--radius-lg) ↔ 10px<br>O·project/project.css:278 `.project-detail .card` {0,2,0} border-radius: var(--radius-lg) ↔ 10px<br>P·project/project.css:352 `.pj-modal` {0,1,0} border-radius: var(--radius-lg) ↔ 10px<br>D·upload/upload.css:611 `.modal-takeover .up-steps .card` {0,3,0} border-radius: var(--radius-lg) ↔ var(--up-radius) |
| 10 | L11 | P·catalog/catalog.css:194 `.catalog-filters` {0,1,0} padding: var(--space-card) ↔ 20px; gap: 20px ↔ 16px<br>P·catalog/catalog.css:204@≤640 `.catalog-filters` {0,1,0} padding: var(--space-card) ↔ 16px; gap: 20px ↔ 14px 12px |
| 11 | L12 | P·catalog/catalog.css:196 `.catalog-filters .axis-pick` {0,2,0} gap: 8px ↔ 6px |
| 12 | L13 | O·catalog/catalog.css:197 `.catalog-filters .axis-k` {0,2,0} font-size: var(--text-caption) ↔ 13px |
| 13 | L14 | P·catalog/catalog.css:198 `.catalog-filters select` {0,1,1} height: var(--control-height) ↔ 38px<br>P·catalog/catalog.css:205@≤640 `.catalog-filters select` {0,1,1} height: var(--control-height) ↔ 40px<br>D·detail/detail.css:300 `.detail-page .dt-edit.de-inline select` {0,3,1} height: var(--control-height) ↔ 40px |
| 14 | L15 | P·catalog/catalog.css:43 `.tblwrap` {0,1,0} max-height: none ↔ calc(100dvh - 232px) |
| 16 | L17 | P·catalog/catalog.css:45 `.tbl th` {0,1,1} color: var(--color-text-muted) ↔ var(--color-gray-500); font-weight: 600 ↔ 700; letter-spa<br>P·common/variableTable.css:47 `.vartable th` {0,1,1} color: var(--color-text-muted) ↔ var(--color-gray-600); font-weight: 600 ↔ 700<br>P·upload/upload.css:272 `.projtable th` {0,1,1} color: var(--color-text-muted) ↔ var(--up-muted) |
| 18 | L19 | P·catalog/catalog.css:52 `.tbl td` {0,1,1} padding: 10px 12px ↔ 13px 14px<br>O·catalog/catalog.css:62 `.tbl td.empty` {0,2,1} padding: 10px 12px ↔ 36px 14px<br>P·common/variableTable.css:27 `.vartable td` {0,1,1} padding: 10px 12px ↔ 0<br>P·common/variableTable.css:57 `.vartable td` {0,1,1} padding: 10px 12px ↔ 7px 9px<br>O·common/variableTable.css:63 `.vartable td:has(.inp)` {0,2,1} padding: 10px 12px ↔ 0<br>P·members/members.css:69 `.memtbl td` {0,1,1} padding: 10px 12px ↔ 10px 8px<br>O·members/members.css:189@≤640 `.memgrid .memtbl td` {0,2,1} padding: 10px 12px ↔ 3px 0<br>D·members/members.css:190@≤640 `.memgrid .memtbl td.pc` {0,3,1} padding: 10px 12px ↔ 8px 0<br>D·members/members.css:205@≤640 `.memgrid .memtbl td.pc.is-chg` {0,4,1} padding: 10px 12px ↔ 8px<br>P·project/project.css:240 `.pj-table td` {0,1,1} padding: 10px 12px ↔ 8px 10px<br>O·project/project.css:256 `.pj-ds td.empty` {0,2,1} padding: 10px 12px ↔ 36px 14px<br>P·upload/upload.css:271 `.projtable td` {0,1,1} padding: 10px 12px ↔ 6px 8px |
| 19 | L20 | P·catalog/catalog.css:59 `.tbl .fname` {0,2,0} font-size: var(--text-body-sm) ↔ 13px; letter-spacing: 0 ↔ -0.01em |
| 22 | L23 | S·auth/login.css:150 `.account-table td` {0,1,1} white-space: normal ↔ nowrap<br>S·catalog/catalog.css:52 `.tbl td` {0,1,1} white-space: normal ↔ nowrap<br>S·common/variableTable.css:27 `.vartable td` {0,1,1} white-space: normal ↔ nowrap<br>P·project/project.css:236 `.pj-table td:not(:first-child)` {0,2,1} white-space: normal ↔ nowrap<br>P·upload/upload.css:273 `.projtable td.pr-k` {0,2,1} white-space: normal ↔ nowrap<br>P·upload/upload.css:275 `.projtable td.pr-x` {0,2,1} white-space: normal ↔ nowrap |
| 24 | L25 | P·catalog/catalog.css:159 `.tbl td.rowact .ra` {0,3,1} opacity: 1 ↔ 0 |
| 25 | L26 | P·catalog/catalog.css:161 `.tbl td.rowact .rab` {0,3,1} width: 36px ↔ 26px; height: 36px ↔ 26px |
| 26 | L27 | P·catalog/catalog.css:113 `.fchips` {0,1,0} padding: 12px var(--space-card) ↔ 10px 14px; gap: 8px ↔ 6px |
| 27 | L28 | P·catalog/catalog.css:118 `.fchips .fc` {0,2,0} height: 32px ↔ 24px |
| 28 | L29 | S·approval/approval.css:12 `.dh-menu button` {0,1,1} width: 24px ↔ 100%<br>P·catalog/catalog.css:90 `.colmenu button.cm-i` {0,2,1} width: 24px ↔ 100%<br>S·dashboard/dashboard.css:207 `.dash-tile--linked button` {0,1,1} width: 24px ↔ 100%<br>S·dashboard/dashboard.css:223 `.dash-recent button` {0,1,1} width: 24px ↔ 100%<br>S·upload/upload.css:508 `.dr-nav button` {0,1,1} width: 24px ↔ 28px |
| 30 | L31 | P·catalog/catalog.css:170 `.crosslink` {0,1,0} padding: 16px 20px ↔ 13px 15px |
| 31 | L32 | P·dashboard/dashboard.css:21 `.lab-page .search-hero` {0,2,0} max-width: 720px ↔ 680px |
| 33 | L34 | D·detail/detail.css:202 `.detail-page .dt-edit .de-period input` {0,3,1} padding: 14px 16px ↔ 6px 8px<br>D·detail/detail.css:282 `.detail-page .de-inline input.de-v` {0,3,1} padding: 14px 16px ↔ 8px 10px<br>D·detail/detail.css:300 `.detail-page .dt-edit.de-inline input` {0,3,1} min-height: 52px ↔ 40px; padding: 14px 16px ↔ 8px 10px<br>P·search/search.css:8 `.search-hero input` {0,1,1} padding: 14px 16px ↔ 12px 14px |
| 34 | L35 | P·approval/approval.css:12 `.dh-menu button` {0,1,1} color: var(--color-on-primary) ↔ var(--color-text)<br>O·catalog/catalog.css:90 `.colmenu button.cm-i` {0,2,1} color: var(--color-on-primary) ↔ var(--color-text-body)<br>D·catalog/catalog.css:95 `.colmenu button.cm-i.on` {0,3,1} color: var(--color-on-primary) ↔ var(--color-text)<br>O·catalog/catalog.css:124 `.fchips .fc button` {0,2,1} color: var(--color-on-primary) ↔ var(--color-gray-500)<br>P·upload/upload.css:508 `.dr-nav button` {0,1,1} color: var(--color-on-primary) ↔ var(--color-text-body)<br>P·upload/upload.css:535 `.dr-useg button` {0,1,1} color: var(--color-on-primary) ↔ var(--color-text-body)<br>O·upload/upload.css:540 `.dr-useg button.on` {0,2,1} color: var(--color-on-primary) ↔ var(--color-text-on-primary)<br>D·upload/upload.css:590 `.modal-takeover[data-scene="register"] .` {0,3,1} color: var(--color-on-primary) ↔ var(--up-muted)<br>D·upload/upload.css:591 `.modal-takeover[data-scene="register"] .` {0,4,1} color: var(--color-on-primary) ↔ var(--up-ink) |
| 35 | L36 | P·search/search.css:17 `.search-hero .hero-note` {0,2,0} font-size: var(--text-body-sm) ↔ var(--text-caption, 12px) |
| 36 | L37 | P·dashboard/dashboard.css:27 `.dash-columns` {0,1,0} margin-top: 8px ↔ 20px; gap: var(--space-section) ↔ 20px<br>P·dashboard/dashboard.css:35@≤900 `.dash-columns` {0,1,0} grid-template-columns: minmax(0, 3fr) minmax(0, 2fr) ↔ minmax(0, 1fr) |
| 37 | L38 | P·dashboard/dashboard.css:40 `.dash-col` {0,1,0} gap: 20px ↔ 16px |
| 38 | L39 | P·dashboard/dashboard.css:48 `.dash-section-label` {0,1,0} font-size: var(--text-section) ↔ 15px; font-weight: 600 ↔ 700 |
| 39 | L40 | P·dashboard/dashboard.css:63 `.dash-card` {0,1,0} padding: var(--space-card) ↔ 20px<br>P·dashboard/dashboard.css:379@≤640 `.dash-card` {0,1,0} padding: var(--space-card) ↔ 16px |
| 40 | L41 | P·dashboard/dashboard.css:70 `.dash-card-head` {0,1,0} align-items: center ↔ baseline; gap: 8px 16px ↔ 8px; margin-bottom: 20px ↔ 10px |
| 41 | L42 | P·dashboard/dashboard.css:77 `.dash-card-head h2` {0,1,1} font-size: var(--text-section) ↔ 14px<br>P·dashboard/dashboard.css:374 `.lab-info h2` {0,1,1} font-size: var(--text-section) ↔ 20px<br>O·detail/detail.css:101 `.detail-page .locked-hero h2` {0,2,1} font-size: var(--text-section) ↔ var(--text-h2); font-weight: 600 ↔ var(--weight-heading)<br>P·detail/detail.css:325 `.dt-representative-head h2` {0,1,1} font-size: var(--text-section) ↔ 16px<br>O·lineage/lineageGraph.css:15 `.detail-page .dsec-h h2` {0,2,1} font-size: var(--text-section) ↔ var(--text-h2); font-weight: 600 ↔ var(--weight-heading)<br>P·members/members.css:24 `.card-h h2` {0,1,1} font-size: var(--text-section) ↔ var(--text-body)<br>P·project/project.css:294 `.pd-sect h2` {0,1,1} font-size: var(--text-section) ↔ 14px<br>O·search/search.css:43 `.search-page .notice--empty h2` {0,2,1} font-size: var(--text-section) ↔ 18px |
| 42 | L43 | P·dashboard/dashboard.css:100 `.dash-bar` {0,1,0} font-size: var(--text-body-sm) ↔ 13px; grid-template-columns: 100px minmax(0, 1fr) 40px ↔  |
| 43 | L44 | P·dashboard/dashboard.css:114 `.dash-bar-track` {0,1,0} height: 6px ↔ 8px |
| 44 | L45 | P·dashboard/dashboard.css:122 `.dash-bar-fill` {0,1,0} background: var(--accent-neutral) ↔ var(--accent-neutral, #5b7089) |
| 46 | L47 | P·dashboard/dashboard.css:143 `.dash-calc` {0,1,0} margin: 8px 0 20px ↔ 4px 0 12px |
| 47 | L48 | P·dashboard/dashboard.css:175 `.dash-tiles` {0,1,0} gap: 12px ↔ 10px |
| 48 | L49 | P·dashboard/dashboard.css:184 `.dash-tile` {0,1,0} padding: 16px ↔ 10px 12px |
| 49 | L50 | P·dashboard/dashboard.css:190 `.dash-tile strong` {0,1,1} font-size: 28px ↔ 22px<br>D·search/search.css:45 `.search-page .notice--empty .empty-acts ` {0,4,0} font-size: 28px ↔ 13px |
| 51 | L52 | P·dashboard/dashboard.css:158 `.dash-open-catalog` {0,1,0} min-height: var(--control-height) ↔ 38px; font-size: var(--text-body-sm) ↔ 14px; margin-to |
| 52 | L53 | O·catalog/catalog.css:90 `.colmenu button.cm-i` {0,2,1} font-size: var(--text-body-sm) ↔ 13px<br>O·catalog/catalog.css:124 `.fchips .fc button` {0,2,1} font-size: var(--text-body-sm) ↔ 13px; line-height: 1.6 ↔ 1<br>P·dashboard/dashboard.css:223 `.dash-recent button` {0,1,1} font-size: var(--text-body-sm) ↔ 13px<br>P·preview/preview.css:326 `.pv-zoom button` {0,1,1} font-size: var(--text-body-sm) ↔ 13px<br>P·project/project.css:438 `.pj-seg button` {0,1,1} font-size: var(--text-body-sm) ↔ 13px<br>P·upload/upload.css:535 `.dr-useg button` {0,1,1} font-size: var(--text-body-sm) ↔ var(--text-caption)<br>D·upload/upload.css:642 `.modal-takeover .dr-useg button` {0,3,0} font-size: var(--text-body-sm) ↔ 13px |
| 53 | L54 | P·auth/login.css:198 `.account-modal h3` {0,1,1} font-size: var(--text-body-sm) ↔ var(--text-title-sm, 18px)<br>P·approval/approval.css:4 `.approval-dialog h3` {0,1,1} font-size: var(--text-body-sm) ↔ 18px<br>P·dashboard/dashboard.css:250 `.todo-grp h3` {0,1,1} font-size: var(--text-body-sm) ↔ 13px<br>P·lab/lab.css:44 `.labinfo-modal h3` {0,1,1} font-size: var(--text-body-sm) ↔ var(--text-body)<br>P·members/members.css:17 `.card-h h3` {0,1,1} font-size: var(--text-body-sm) ↔ var(--text-body)<br>P·members/members.css:142 `.modal-h h3` {0,1,1} font-size: var(--text-body-sm) ↔ var(--text-body)<br>P·project/project.css:372 `.pj-modal-h h3` {0,1,1} font-size: var(--text-body-sm) ↔ 15px<br>O·upload/upload.css:48 `.modal-takeover .modal-h h3` {0,2,1} font-size: var(--text-body-sm) ↔ 18px<br>D·upload/upload.css:613 `.modal-takeover .up-steps .card-h h3` {0,3,1} font-size: var(--text-body-sm) ↔ 16px |
| 54 | L55 | P·dashboard/dashboard.css:269 `.titem` {0,1,0} font-size: var(--text-body-sm) ↔ 13px; padding: 14px 0 ↔ 6px 0; gap: 6px 16px ↔ 4px 10px |
| 56 | L57 | P·approval/approval.css:12 `.dh-menu button` {0,1,1} color: var(--color-text-muted) ↔ var(--color-text)<br>O·catalog/catalog.css:90 `.colmenu button.cm-i` {0,2,1} color: var(--color-text-muted) ↔ var(--color-text-body)<br>D·catalog/catalog.css:95 `.colmenu button.cm-i.on` {0,3,1} color: var(--color-text-muted) ↔ var(--color-text)<br>O·catalog/catalog.css:124 `.fchips .fc button` {0,2,1} color: var(--color-text-muted) ↔ var(--color-gray-500)<br>P·preview/preview.css:326 `.pv-zoom button` {0,1,1} border-radius: var(--radius-sm) ↔ 6px<br>P·search/search.css:13 `.search-hero button` {0,1,1} border-radius: var(--radius-sm) ↔ 10px; color: var(--color-text-muted) ↔ var(--color-on-pr<br>P·upload/upload.css:201 `.regsteps button` {0,1,1} border-radius: var(--radius-sm) ↔ 9999px<br>O·upload/upload.css:208 `.regsteps button.is-active` {0,2,1} color: var(--color-text-muted) ↔ var(--color-on-primary)<br>P·upload/upload.css:508 `.dr-nav button` {0,1,1} color: var(--color-text-muted) ↔ var(--color-text-body)<br>P·upload/upload.css:535 `.dr-useg button` {0,1,1} color: var(--color-text-muted) ↔ var(--color-text-body)<br>O·upload/upload.css:540 `.dr-useg button.on` {0,2,1} color: var(--color-text-muted) ↔ var(--color-text-on-primary)<br>D·upload/upload.css:590 `.modal-takeover[data-scene="register"] .` {0,3,1} border-radius: var(--radius-sm) ↔ 0; color: var(--color-text-muted) ↔ var(--up-muted)<br>D·upload/upload.css:591 `.modal-takeover[data-scene="register"] .` {0,4,1} color: var(--color-text-muted) ↔ var(--up-ink) |
| 58 | L59 | P·dashboard/dashboard.css:307 `.dash-steps` {0,1,0} gap: 12px 20px ↔ 10px<br>P·dashboard/dashboard.css:370 `.dash-steps` {0,1,0} margin-top: 20px ↔ 16px |
| 59 | L60 | P·dashboard/dashboard.css:372 `.dash-step-no` {0,1,0} width: 28px ↔ 24px; height: 28px ↔ 24px; line-height: 28px ↔ 24px |
| 60 | L61 | P·project/project.css:342 `.pj-modal-back` {0,1,0} background: var(--color-overlay) ↔ rgb(15 20 28 / 45%)<br>P·project/project.css:573@≤640 `.pj-modal-back` {0,1,0} padding: 24px ↔ 16px |
| 61 | L62 | P·project/project.css:352 `.pj-modal` {0,1,0} width: min(600px, 100%) ↔ min(560px, 100%); max-height: calc(100dvh - 48px) ↔ 90vh<br>P·project/project.css:574@≤640 `.pj-modal` {0,1,0} max-height: calc(100dvh - 48px) ↔ calc(100dvh - 32px) |
| 62 | L63 | P·project/project.css:363 `.pj-modal-h` {0,1,0} padding: 20px var(--space-card) ↔ 14px 16px |
| 63 | L64 | P·auth/login.css:198 `.account-modal h3` {0,1,1} font-size: 20px ↔ var(--text-title-sm, 18px)<br>P·approval/approval.css:4 `.approval-dialog h3` {0,1,1} font-size: 20px ↔ 18px<br>P·dashboard/dashboard.css:250 `.todo-grp h3` {0,1,1} font-size: 20px ↔ 13px<br>P·lab/lab.css:44 `.labinfo-modal h3` {0,1,1} font-size: 20px ↔ var(--text-body)<br>P·members/members.css:17 `.card-h h3` {0,1,1} font-size: 20px ↔ var(--text-body)<br>P·members/members.css:142 `.modal-h h3` {0,1,1} font-size: 20px ↔ var(--text-body)<br>P·project/project.css:372 `.pj-modal-h h3` {0,1,1} font-size: 20px ↔ 15px<br>O·upload/upload.css:48 `.modal-takeover .modal-h h3` {0,2,1} font-size: 20px ↔ 18px<br>D·upload/upload.css:613 `.modal-takeover .up-steps .card-h h3` {0,3,1} font-size: 20px ↔ 16px |
| 64 | L65 | P·project/project.css:377 `.pj-x` {0,1,0} font-size: 24px ↔ 18px |
| 65 | L66 | P·project/project.css:386 `.pj-modal-b` {0,1,0} padding: var(--space-card) ↔ 16px |
| 66 | L67 | P·project/project.css:391 `.pj-modal-f` {0,1,0} padding: 16px var(--space-card) ↔ 12px 16px |
| 67 | L68 | P·project/project.css:400 `.pj-row` {0,1,0} margin-bottom: 24px ↔ 14px |
| 68 | L69 | O·lab/lab.css:53 `.labinfo-modal .form-row label` {0,2,1} color: var(--color-text) ↔ var(--color-text-muted)<br>P·lineage/lineage.css:112 `.lin-f label` {0,1,1} font-size: var(--text-body-sm) ↔ 13px<br>P·lineage/lineage.css:254 `.lin-unknown label` {0,1,1} font-size: var(--text-body-sm) ↔ 13px<br>D·lineage/lineage.css:267 `.lin-unknown:has(input:disabled) label` {0,2,2} color: var(--color-text) ↔ var(--lin-over-ink, #5b6472)<br>P·lineage/lineage.css:351 `.lin-findbar label` {0,1,1} font-size: var(--text-body-sm) ↔ var(--text-caption)<br>P·project/project.css:404 `.pj-row label` {0,1,1} font-size: var(--text-body-sm) ↔ 13px; margin-bottom: 8px ↔ 5px; color: var(--color-text) <br>P·upload/upload.css:232 `.form-row label` {0,1,1} font-size: var(--text-body-sm) ↔ 13px; color: var(--color-text) ↔ var(--up-muted)<br>O·upload/upload.css:604 `.modal-takeover .form-row label` {0,2,1} font-size: var(--text-body-sm) ↔ 13px |
| 69 | L70 | P·project/project.css:411 `.pj-inp` {0,1,0} padding: 10px 12px ↔ 7px 9px; font-size: var(--text-body) ↔ 13px; border: 1px solid var(--<br>P·project/project.css:421 `.pj-tarea` {0,1,0} min-height: var(--control-height) ↔ 72px<br>P·project/project.css:575@≤640 `.pj-inp` {0,1,0} font-size: var(--text-body) ↔ 16px |
| 70 | L71 | P·project/project.css:421 `.pj-tarea` {0,1,0} min-height: 96px ↔ 72px |
| 71 | L72 | P·project/project.css:431 `.pj-seg` {0,1,0} border-radius: var(--radius-sm) ↔ 6px |
| 72 | L73 | O·catalog/catalog.css:90 `.colmenu button.cm-i` {0,2,1} font-size: var(--text-body-sm) ↔ 13px<br>O·catalog/catalog.css:124 `.fchips .fc button` {0,2,1} font-size: var(--text-body-sm) ↔ 13px<br>P·dashboard/dashboard.css:223 `.dash-recent button` {0,1,1} font-size: var(--text-body-sm) ↔ 13px<br>P·preview/preview.css:326 `.pv-zoom button` {0,1,1} font-size: var(--text-body-sm) ↔ 13px; border-radius: var(--radius-sm) ↔ 6px<br>P·project/project.css:438 `.pj-seg button` {0,1,1} font-size: var(--text-body-sm) ↔ 13px<br>P·search/search.css:13 `.search-hero button` {0,1,1} border-radius: var(--radius-sm) ↔ 10px<br>P·upload/upload.css:201 `.regsteps button` {0,1,1} border-radius: var(--radius-sm) ↔ 9999px<br>P·upload/upload.css:535 `.dr-useg button` {0,1,1} font-size: var(--text-body-sm) ↔ var(--text-caption)<br>D·upload/upload.css:590 `.modal-takeover[data-scene="register"] .` {0,3,1} border-radius: var(--radius-sm) ↔ 0<br>D·upload/upload.css:642 `.modal-takeover .dr-useg button` {0,3,0} font-size: var(--text-body-sm) ↔ 13px |
| 73 | L74 | P·project/project.css:95 `.pj-views button.on` {0,2,1} background: var(--color-surface) ↔ var(--color-gray-100)<br>P·project/project.css:447 `.pj-seg button.on` {0,2,1} background: var(--color-surface) ↔ var(--color-gray-100)<br>P·search/search.css:115 `.search-page .vfilter.on` {0,3,0} color: var(--color-text) ↔ var(--color-success-600, #1f8b4c)<br>P·upload/upload.css:540 `.dr-useg button.on` {0,2,1} background: var(--color-surface) ↔ var(--color-primary-600); color: var(--color-text) ↔ va |
| 74 | L75 | P·project/project.css:462 `.pj-hint` {0,1,0} font-size: var(--text-caption) ↔ 13px<br>P·project/project.css:470 `.pj-defnote` {0,1,0} font-size: var(--text-caption) ↔ 13px; line-height: 1.7 ↔ 1.6 |
| 75 | L76 | P·project/project.css:481 `.pj-fgroup` {0,1,0} padding: 20px ↔ 12px |
| 76 | L77 | S·project/project.css:400 `.pj-row` {0,1,0} margin-bottom: 0 ↔ 14px |
| 77 | L78 | P·project/project.css:488 `.pj-fgroup-h` {0,1,0} margin-bottom: 16px ↔ 10px |
| 79 | L80 | P·project/project.css:535 `.pj-err` {0,1,0} color: var(--fg-danger) ↔ var(--color-warning-600) |
| 80 | L81 | P·members/members.css:46 `.btn` {0,1,0} padding: 10px 18px ↔ 0 12px<br>P·upload/upload.css:312 `.btn` {0,1,0} padding: 10px 18px ↔ 8px 14px; border-radius: var(--radius-sm) ↔ 8px<br>D·upload/upload.css:640 `.modal-takeover .reg-actions .btn` {0,3,0} padding: 10px 18px ↔ 0 12px |
| 81 | L82 | P·members/members.css:60 `.btn-primary` {0,1,0} color: var(--color-on-primary) ↔ var(--color-white)<br>O·members/members.css:65 `.btn-primary:hover` {0,2,0} background: var(--color-primary-600) ↔ var(--color-primary-700)<br>P·upload/upload.css:314 `.btn-primary` {0,1,0} border-color: var(--color-primary-600) ↔ var(--up-ink) |
| 83 | L84 | S·approval/approval.css:12 `.dh-menu button` {0,1,1} background: var(--color-primary-700) ↔ none<br>P·approval/approval.css:13 `.dh-menu button:hover` {0,2,1} background: var(--color-primary-700) ↔ var(--color-surface-hover)<br>P·catalog/catalog.css:90 `.colmenu button.cm-i` {0,2,1} background: var(--color-primary-700) ↔ none<br>O·catalog/catalog.css:94 `.colmenu button.cm-i:hover` {0,3,1} background: var(--color-primary-700) ↔ var(--color-gray-100)<br>P·catalog/catalog.css:124 `.fchips .fc button` {0,2,1} background: var(--color-primary-700) ↔ none<br>S·dashboard/dashboard.css:207 `.dash-tile--linked button` {0,1,1} background: var(--color-primary-700) ↔ none<br>S·dashboard/dashboard.css:223 `.dash-recent button` {0,1,1} background: var(--color-primary-700) ↔ none<br>S·dashboard/dashboard.css:283 `.titem button` {0,1,1} background: var(--color-primary-700) ↔ none<br>S·members/members.css:60 `.btn-primary` {0,1,0} background: var(--color-primary-700) ↔ var(--color-primary-600)<br>S·preview/preview.css:326 `.pv-zoom button` {0,1,1} background: var(--color-primary-700) ↔ var(--color-surface)<br>S·project/project.css:88 `.pj-views button` {0,1,1} background: var(--color-primary-700) ↔ transparent<br>P·project/project.css:95 `.pj-views button.on` {0,2,1} background: var(--color-primary-700) ↔ var(--color-gray-100)<br>S·project/project.css:438 `.pj-seg button` {0,1,1} background: var(--color-primary-700) ↔ none<br>P·project/project.css:447 `.pj-seg button.on` {0,2,1} background: var(--color-primary-700) ↔ var(--color-gray-100)<br>S·search/search.css:13 `.search-hero button` {0,1,1} background: var(--color-primary-700) ↔ var(--color-primary-600, #1f5eff)<br>S·upload/upload.css:201 `.regsteps button` {0,1,1} background: var(--color-primary-700) ↔ none<br>P·upload/upload.css:208 `.regsteps button.is-active` {0,2,1} background: var(--color-primary-700) ↔ var(--color-primary-600)<br>S·upload/upload.css:314 `.btn-primary` {0,1,0} background: var(--color-primary-700) ↔ var(--color-primary-600)<br>S·upload/upload.css:508 `.dr-nav button` {0,1,1} background: var(--color-primary-700) ↔ var(--color-surface)<br>P·upload/upload.css:511 `.dr-nav button:hover` {0,2,1} background: var(--color-primary-700) ↔ var(--color-surface-hover)<br>S·upload/upload.css:535 `.dr-useg button` {0,1,1} background: var(--color-primary-700) ↔ var(--color-surface)<br>P·upload/upload.css:539 `.dr-useg button:hover` {0,2,1} background: var(--color-primary-700) ↔ var(--color-surface-hover)<br>P·upload/upload.css:540 `.dr-useg button.on` {0,2,1} background: var(--color-primary-700) ↔ var(--color-primary-600)<br>O·upload/upload.css:590 `.modal-takeover[data-scene="register"] .` {0,3,1} background: var(--color-primary-700) ↔ transparent |
| 84 | L86 | P·dashboard/dashboard.css:27 `.dash-columns` {0,1,0} grid-template-columns: minmax(0, 1fr) ↔ minmax(0, 3fr) minmax(0, 2fr) |
| 85 | L89 | P·catalog/catalog.css:194 `.catalog-filters` {0,1,0} gap: 16px 12px ↔ 16px<br>P·catalog/catalog.css:204@≤640 `.catalog-filters` {0,1,0} gap: 16px 12px ↔ 14px 12px |
| 87 | L91 | O·catalog/catalog.css:30 `.catalog-page .page-head h1` {0,2,1} font-size: 24px ↔ var(--text-h2, 24px)<br>O·detail/detail.css:41 `.detail-page .dt-header h1` {0,2,1} font-size: 24px ↔ 31px<br>P·members/members.css:32 `.settings-page h1` {0,1,1} font-size: 24px ↔ var(--text-h2)<br>O·project/project.css:36 `.project-page .page-head h1` {0,2,1} font-size: 24px ↔ var(--text-h2)<br>O·project/project.css:42 `.project-detail .pd-head h1` {0,2,1} font-size: 24px ↔ 31px<br>P·search/search.css:6 `.search-hero h1` {0,1,1} font-size: 24px ↔ var(--text-h2, 24px)<br>O·search/search.css:24 `.search-page .page-head h1` {0,2,1} font-size: 24px ↔ var(--text-h2, 24px) |
| 88 | L92 | P·dashboard/dashboard.css:175 `.dash-tiles` {0,1,0} grid-template-columns: repeat(2, minmax(0, 1fr)) ↔ repeat(4, minmax(0, 1fr)) |
| 89 | L93 | P·dashboard/dashboard.css:184 `.dash-tile` {0,1,0} padding: 16px ↔ 10px 12px |
| 90 | L94 | P·dashboard/dashboard.css:100 `.dash-bar` {0,1,0} grid-template-columns: 96px minmax(0, 1fr) 36px ↔ 96px minmax(0, 1fr) 48px |
| 91 | L95 | P·dashboard/dashboard.css:307 `.dash-steps` {0,1,0} gap: 12px ↔ 10px<br>P·dashboard/dashboard.css:370 `.dash-steps` {0,1,0} gap: 12px ↔ 12px 20px |
| 92 | L96 | P·project/project.css:342 `.pj-modal-back` {0,1,0} padding: 12px ↔ 24px<br>P·project/project.css:573@≤640 `.pj-modal-back` {0,1,0} padding: 12px ↔ 16px |
| 93 | L97 | P·project/project.css:352 `.pj-modal` {0,1,0} max-height: calc(100dvh - 24px) ↔ 90vh<br>P·project/project.css:574@≤640 `.pj-modal` {0,1,0} max-height: calc(100dvh - 24px) ↔ calc(100dvh - 32px) |
| 94 | L98 | P·project/project.css:363 `.pj-modal-h` {0,1,0} padding: 16px var(--space-card) ↔ 14px 16px |
| 95 | L99 | P·project/project.css:481 `.pj-fgroup` {0,1,0} padding: 16px ↔ 12px |
| 98 | L102 | P·catalog/catalog.css:161 `.tbl td.rowact .rab` {0,3,1} width: 44px ↔ 26px; height: 44px ↔ 26px |
| 101 | L109 | S·catalog/catalog.css:83 `.colmenu` {0,1,0} position: fixed ↔ absolute; padding: 12px ↔ 6px<br>S·catalog/catalog.css:186@≤640 `.colmenu` {0,1,0} width: auto ↔ max-content; max-width: none ↔ calc(100vw - 40px) |
| 102 | L112 | P·catalog/catalog.css:96 `.colmenu .cm-box` {0,2,0} width: 16px ↔ 13px; height: 16px ↔ 13px; font-size: var(--text-caption) ↔ 9px; color: var( |
| 105 | L117 | S·auth/login.css:54 `.login-input` {0,1,0} padding: 10px 12px ↔ 0 12px; border: 1px solid var(--color-border-control) ↔ 1px solid var<br>P·catalog/catalog.css:198 `.catalog-filters select` {0,1,1} padding: 10px 12px ↔ 0 10px; border: 1px solid var(--color-border-control) ↔ 1px solid var<br>O·common/variableTable.css:63 `.vartable td:has(.inp)` {0,2,1} padding: 10px 12px ↔ 0<br>O·common/variableTable.css:69 `.vartable td .inp` {0,2,1} padding: 10px 12px ↔ 0 9px; border: 1px solid var(--color-border-control) ↔ none; border-r<br>D·detail/detail.css:300 `.detail-page .dt-edit.de-inline select` {0,3,1} min-height: var(--control-height) ↔ 40px; padding: 10px 12px ↔ 8px 10px<br>P·lab/lab.css:58 `.labinfo-modal .inp` {0,2,0} padding: 10px 12px ↔ 8px 10px; border: 1px solid var(--color-border-control) ↔ 1px solid v<br>S·upload/upload.css:258 `.inp` {0,1,0} padding: 10px 12px ↔ 8px 10px; border: 1px solid var(--color-border-control) ↔ 1px solid v<br>P·upload/upload.css:260 `.inp[readonly]` {0,2,0} background: var(--color-surface) ↔ var(--color-surface-alt); color: var(--color-text) ↔ va |
| 108 | L120 | P·detail/detail.css:36 `.detail-page` {0,1,0} max-width: 1280px ↔ 1200px; padding: var(--space-page) ↔ 32px 24px 96px<br>P·preview/preview.css:3 `.preview-page` {0,1,0} max-width: 1280px ↔ 1080px; padding: var(--space-page) ↔ 20px 24px 48px<br>P·project/project.css:30 `.project-detail` {0,1,0} max-width: 1280px ↔ 1200px; padding: var(--space-page) ↔ 32px 24px 96px<br>P·shell/shell.css:103 `.settings-page` {0,1,0} max-width: 1280px ↔ 1200px; padding: var(--space-page) ↔ 24px 20px 40px<br>P·shell/shell.css:419@≤640 `.settings-page` {0,1,0} padding: var(--space-page) ↔ 20px 16px 32px |
| 109 | L121 | P·search/search.css:22 `.search-page` {0,1,0} max-width: 920px ↔ 880px; padding: var(--space-page) ↔ 24px 20px 40px |
| 110 | L122 | P·upload/upload.css:92 `.up-card` {0,1,0} border-radius: var(--radius-lg) ↔ var(--up-radius)<br>O·upload/upload.css:599 `.up-empty .reggate` {0,2,0} border-radius: var(--radius-lg) ↔ 0 |
| 111 | L123 | P·members/members.css:10 `.card-h` {0,1,0} padding: 20px var(--space-card) ↔ 14px 18px<br>P·members/members.css:38 `.card-b` {0,1,0} padding: 20px var(--space-card) ↔ 6px 18px<br>O·members/members.css:178@≤640 `.memgrid .card-b` {0,2,0} padding: 20px var(--space-card) ↔ 6px 12px<br>D·upload/upload.css:612 `.modal-takeover .up-steps .card-h` {0,3,0} padding: 20px var(--space-card) ↔ 16px 22px<br>D·upload/upload.css:615 `.modal-takeover .up-steps .card-b` {0,3,0} padding: 20px var(--space-card) ↔ 20px 22px |
| 112 | L124 | P·auth/login.css:198 `.account-modal h3` {0,1,1} font-size: var(--text-section) ↔ var(--text-title-sm, 18px)<br>P·approval/approval.css:4 `.approval-dialog h3` {0,1,1} font-size: var(--text-section) ↔ 18px<br>P·dashboard/dashboard.css:250 `.todo-grp h3` {0,1,1} font-size: var(--text-section) ↔ 13px<br>P·lab/lab.css:44 `.labinfo-modal h3` {0,1,1} font-size: var(--text-section) ↔ var(--text-body)<br>P·members/members.css:17 `.card-h h3` {0,1,1} font-size: var(--text-section) ↔ var(--text-body)<br>P·members/members.css:142 `.modal-h h3` {0,1,1} font-size: var(--text-section) ↔ var(--text-body)<br>S·preview/preview.css:57 `.pv-h2` {0,1,0} font-size: var(--text-section) ↔ 15px<br>P·project/project.css:372 `.pj-modal-h h3` {0,1,1} font-size: var(--text-section) ↔ 15px<br>O·upload/upload.css:48 `.modal-takeover .modal-h h3` {0,2,1} font-size: var(--text-section) ↔ 18px<br>D·upload/upload.css:613 `.modal-takeover .up-steps .card-h h3` {0,3,1} font-size: var(--text-section) ↔ 16px |
| 113 | L125 | P·members/members.css:10 `.card-h` {0,1,0} gap: 12px ↔ 10px<br>D·upload/upload.css:612 `.modal-takeover .up-steps .card-h` {0,3,0} gap: 12px ↔ 10px |
| 114 | L126 | P·search/search.css:55 `.search-page .hit` {0,2,0} padding: var(--space-card) ↔ 14px 16px |
| 115 | L127 | P·search/search.css:54 `.search-page .hits` {0,2,0} gap: 16px ↔ 10px |
| 116 | L128 | O·lab/lab.css:46 `.labinfo-modal .form-row` {0,2,0} gap: 8px ↔ 4px<br>P·preview/preview.css:155 `.pv-control` {0,1,0} gap: 8px ↔ 4px<br>P·upload/upload.css:231 `.form-row` {0,1,0} gap: 8px ↔ 4px<br>O·upload/upload.css:616 `.modal-takeover .form-row` {0,2,0} gap: 8px ↔ 5px |
| 117 | L129 | P·approval/approval.css:3 `.approval-dialog` {0,1,0} padding: var(--space-card) ↔ 24px<br>P·lab/lab.css:33 `.labinfo-modal` {0,1,0} border-radius: var(--radius-lg) ↔ 12px; padding: var(--space-card) ↔ 18px |
| 119 | L131 | P·auth/login.css:198 `.account-modal h3` {0,1,1} font-size: 20px ↔ var(--text-title-sm, 18px)<br>P·approval/approval.css:4 `.approval-dialog h3` {0,1,1} font-size: 20px ↔ 18px<br>P·dashboard/dashboard.css:250 `.todo-grp h3` {0,1,1} font-size: 20px ↔ 13px<br>P·lab/lab.css:44 `.labinfo-modal h3` {0,1,1} font-size: 20px ↔ var(--text-body)<br>P·members/members.css:17 `.card-h h3` {0,1,1} font-size: 20px ↔ var(--text-body)<br>P·members/members.css:142 `.modal-h h3` {0,1,1} font-size: 20px ↔ var(--text-body)<br>P·project/project.css:372 `.pj-modal-h h3` {0,1,1} font-size: 20px ↔ 15px<br>O·upload/upload.css:48 `.modal-takeover .modal-h h3` {0,2,1} font-size: 20px ↔ 18px<br>D·upload/upload.css:613 `.modal-takeover .up-steps .card-h h3` {0,3,1} font-size: 20px ↔ 16px |
| 120 | L132 | P·lab/lab.css:46 `.labinfo-modal .form-row` {0,2,0} margin-bottom: 20px ↔ 10px<br>S·upload/upload.css:231 `.form-row` {0,1,0} margin-bottom: 20px ↔ 10px<br>P·upload/upload.css:506 `.dr-times .form-row` {0,2,0} margin-bottom: 20px ↔ 0<br>P·upload/upload.css:616 `.modal-takeover .form-row` {0,2,0} margin-bottom: 20px ↔ 0 |
| 121 | L133 | S·members/members.css:38 `.card-b` {0,1,0} padding: var(--space-card) ↔ 6px 18px<br>S·members/members.css:178@≤640 `.memgrid .card-b` {0,2,0} padding: var(--space-card) ↔ 6px 12px<br>S·upload/upload.css:126 `.up-card > .card-b` {0,2,0} gap: 20px ↔ 12px<br>P·upload/upload.css:615 `.modal-takeover .up-steps .card-b` {0,3,0} gap: 20px ↔ 12px; padding: var(--space-card) ↔ 20px 22px |
| 122 | L134 | P·lab/lab.css:46 `.labinfo-modal .form-row` {0,2,0} gap: 8px ↔ 4px<br>S·upload/upload.css:231 `.form-row` {0,1,0} gap: 8px ↔ 4px<br>P·upload/upload.css:616 `.modal-takeover .form-row` {0,2,0} gap: 8px ↔ 5px |
| 123 | L135 | S·members/members.css:46 `.btn` {0,1,0} height: auto ↔ 32px<br>P·upload/upload.css:640 `.modal-takeover .reg-actions .btn` {0,3,0} height: auto ↔ 34px |
| 125 | L137 | P·shell/shell.css:106 `.gnb` {0,1,0} gap: 12px ↔ 10px<br>P·shell/shell.css:365@≤1180 `.gnb` {0,1,0} gap: 12px ↔ 8px<br>P·shell/shell.css:393@≤560 `.gnb` {0,1,0} gap: 12px ↔ 4px |
| 126 | L138 | P·shell/shell.css:376@≤880 `.gnb-settings` {0,1,0} display: inline-flex ↔ none |
| 129 | L141 | O·upload/upload.css:618 `.modal-takeover button:focus-visible` {0,2,1} outline-offset: 3px ↔ 2px |
| 130 | L143 | P·shell/shell.css:106 `.gnb` {0,1,0} height: auto ↔ var(--shell-gnb-height); gap: 8px ↔ 10px; padding: 10px 16px ↔ 0 20px<br>P·shell/shell.css:365@≤1180 `.gnb` {0,1,0} padding: 10px 16px ↔ 0 14px<br>P·shell/shell.css:393@≤560 `.gnb` {0,1,0} gap: 8px ↔ 4px; padding: 10px 16px ↔ 0 10px |
| 135 | L152 | S·shell/shell.css:203 `.gnb-settings` {0,1,0} display: none ↔ inline-flex<br>S·shell/shell.css:224 `.gnb-upload` {0,1,0} display: none ↔ inline-flex |
| 136 | L153 | S·shell/shell.css:273 `.gnb-more-wrap` {0,1,0} display: inline-flex ↔ contents |
| 137 | L154 | S·shell/shell.css:274 `.gnb-more` {0,1,0} display: inline-flex ↔ none |
| 138 | L157 | P·catalog/catalog.css:198 `.catalog-filters select` {0,1,1} font-size: 16px ↔ 14px<br>O·common/variableTable.css:69 `.vartable td .inp` {0,2,1} font-size: 16px ↔ var(--text-body-sm)<br>D·detail/detail.css:300 `.detail-page .dt-edit.de-inline select` {0,3,1} font-size: 16px ↔ 14px<br>P·upload/upload.css:617 `.modal-takeover .inp` {0,2,0} font-size: 16px ↔ 14px<br>S·shell/shell.css:423@≤640 `body select` {0,0,2} font-size: 16px ↔ max(16px, 1em) !important |
| 140 | L159 | P·shell/shell.css:106 `.gnb` {0,1,0} gap: 6px ↔ 10px<br>P·shell/shell.css:365@≤1180 `.gnb` {0,1,0} gap: 6px ↔ 8px<br>P·shell/shell.css:393@≤560 `.gnb` {0,1,0} gap: 6px ↔ 4px |
| 141 | L160 | S·shell/shell.css:274 `.gnb-more` {0,1,0} min-width: 36px ↔ 34px |
| 142 | L161 | S·shell/shell.css:247 `.avatar` {0,1,0} display: none ↔ inline-flex |
| 144 | L163 | P·preview/preview.css:63 `.pv-basic-grid` {0,1,0} grid-template-columns: minmax(0, 1fr) ↔ repeat(auto-fill, minmax(220px, 1fr)) |
| 146 | L165 | P·upload/upload.css:502 `.dr-pop` {0,1,0} position: fixed ↔ absolute; width: auto ↔ 576px; max-width: none ↔ calc(100vw - 48px)<br>P·upload/upload.css:542@@media(max-width:760 `.dr-pop` {0,1,0} width: auto ↔ 308px |
| 147 | L166 | P·upload/upload.css:520 `.dr-cal-d` {0,1,0} height: 44px ↔ 32px |
| 150 | L171 | O·lineage/lineage.css:238 `.lin .chip--warning` {0,2,0} background: var(--color-warning-50) ↔ var(--lin-over-bg); color: var(--color-warning-600) <br>O·search/search.css:86 `.search-page .chip--warning` {0,2,0} background: var(--color-warning-50) ↔ var(--color-warning-50, #fff6ed); color: var(--color |
| 151 | L172 | P·detail/detail.css:41 `.detail-page .dt-header h1` {0,2,1} font-size: var(--text-h2) ↔ 31px; line-height: 1.3 ↔ 1.25<br>S·search/search.css:6 `.search-hero h1` {0,1,1} font-size: var(--text-h2) ↔ var(--text-h2, 24px) |
| 152 | L173 | S·dashboard/dashboard.css:77 `.dash-card-head h2` {0,1,1} font-size: 20px ↔ 14px<br>P·detail/detail.css:101 `.detail-page .locked-hero h2` {0,2,1} font-size: 20px ↔ var(--text-h2)<br>S·detail/detail.css:325 `.dt-representative-head h2` {0,1,1} font-size: 20px ↔ 16px<br>P·lineage/lineageGraph.css:15 `.detail-page .dsec-h h2` {0,2,1} font-size: 20px ↔ var(--text-h2)<br>S·members/members.css:24 `.card-h h2` {0,1,1} font-size: 20px ↔ var(--text-body)<br>S·project/project.css:294 `.pd-sect h2` {0,1,1} font-size: 20px ↔ 14px |
| 153 | L175 | P·members/members.css:82 `.chip` {0,1,0} background: var(--color-surface-alt) ↔ var(--color-surface-hover)<br>P·upload/upload.css:264 `.chip` {0,1,0} background: var(--color-surface-alt) ↔ #eef2f7 |
| 156 | L178 | P·lineage/lineageGraph.css:52 `.detail-page .ln .arw` {0,3,0} color: var(--color-text-muted) ↔ var(--color-primary-700); opacity: 1 ↔ .5<br>O·lineage/lineageGraph.css:86 `.detail-page .lrow .ln-go .arw` {0,4,0} color: var(--color-text-muted) ↔ var(--color-gray-400) |
| 157 | L179 | S·members/members.css:38 `.card-b` {0,1,0} padding: 0 ↔ 6px 18px<br>S·members/members.css:178@≤640 `.memgrid .card-b` {0,2,0} padding: 0 ↔ 6px 12px<br>P·upload/upload.css:615 `.modal-takeover .up-steps .card-b` {0,3,0} padding: 0 ↔ 20px 22px |
| 164 | L187 | P·preview/preview.css:500 `.pv-pick-f .sel` {0,2,0} width: auto ↔ 0<br>P·upload/upload.css:499 `.itv .sel` {0,2,0} width: auto ↔ 78px |
| 165 | L188 | P·upload/upload.css:194 `.reggate` {0,1,0} align-items: start ↔ center; gap: 12px ↔ 16px |
| 169 | L193 | S·approval/approval.css:12 `.dh-menu button` {0,1,1} padding: 8px ↔ 10px 12px; background: transparent ↔ none<br>P·approval/approval.css:13 `.dh-menu button:hover` {0,2,1} background: transparent ↔ var(--color-surface-hover)<br>P·catalog/catalog.css:90 `.colmenu button.cm-i` {0,2,1} border: 0 ↔ none; padding: 8px ↔ 7px 8px; background: transparent ↔ none; color: var(--col<br>D·catalog/catalog.css:94 `.colmenu button.cm-i:hover` {0,3,1} background: transparent ↔ var(--color-gray-100)<br>P·catalog/catalog.css:124 `.fchips .fc button` {0,2,1} border: 0 ↔ none; padding: 8px ↔ 0; background: transparent ↔ none; color: var(--color-tex<br>S·dashboard/dashboard.css:207 `.dash-tile--linked button` {0,1,1} padding: 8px ↔ 0; background: transparent ↔ none<br>S·dashboard/dashboard.css:223 `.dash-recent button` {0,1,1} padding: 8px ↔ 6px 0; background: transparent ↔ none<br>S·dashboard/dashboard.css:283 `.titem button` {0,1,1} padding: 8px ↔ 0; background: transparent ↔ none<br>S·dashboard/dashboard.css:381@≤640 `.dash-recent button` {0,1,1} padding: 8px ↔ 10px 0<br>S·preview/preview.css:326 `.pv-zoom button` {0,1,1} border: 0 ↔ 1px solid var(--color-border); border-radius: var(--radius-sm) ↔ 6px; padding:<br>S·project/project.css:88 `.pj-views button` {0,1,1} border: 0 ↔ 1px solid var(--color-border); padding: 8px ↔ 4px 10px<br>P·project/project.css:95 `.pj-views button.on` {0,2,1} background: transparent ↔ var(--color-gray-100)<br>S·project/project.css:438 `.pj-seg button` {0,1,1} padding: 8px ↔ 6px 14px; background: transparent ↔ none<br>P·project/project.css:447 `.pj-seg button.on` {0,2,1} background: transparent ↔ var(--color-gray-100)<br>S·search/search.css:13 `.search-hero button` {0,1,1} border: 0 ↔ 1px solid transparent; border-radius: var(--radius-sm) ↔ 10px; padding: 8px ↔ <br>S·upload/upload.css:201 `.regsteps button` {0,1,1} border: 0 ↔ 1px solid var(--up-line); border-radius: var(--radius-sm) ↔ 9999px; padding: 8<br>P·upload/upload.css:208 `.regsteps button.is-active` {0,2,1} background: transparent ↔ var(--color-primary-600); color: var(--color-text) ↔ var(--color<br>S·upload/upload.css:508 `.dr-nav button` {0,1,1} border: 0 ↔ 1px solid var(--color-border-strong); background: transparent ↔ var(--color-su<br>P·upload/upload.css:511 `.dr-nav button:hover` {0,2,1} background: transparent ↔ var(--color-surface-hover)<br>S·upload/upload.css:535 `.dr-useg button` {0,1,1} border: 0 ↔ none; padding: 8px ↔ 0 10px; background: transparent ↔ var(--color-surface); c<br>P·upload/upload.css:539 `.dr-useg button:hover` {0,2,1} background: transparent ↔ var(--color-surface-hover)<br>P·upload/upload.css:540 `.dr-useg button.on` {0,2,1} background: transparent ↔ var(--color-primary-600); color: var(--color-text) ↔ var(--color<br>D·upload/upload.css:590 `.modal-takeover[data-scene="register"] .` {0,3,1} border-radius: var(--radius-sm) ↔ 0; padding: 8px ↔ 14px 12px; color: var(--color-text) ↔ <br>D·upload/upload.css:591 `.modal-takeover[data-scene="register"] .` {0,4,1} color: var(--color-text) ↔ var(--up-ink) |
| 170 | L194 | S·approval/approval.css:12 `.dh-menu button` {0,1,1} background: var(--color-surface-hover) ↔ none<br>S·catalog/catalog.css:90 `.colmenu button.cm-i` {0,2,1} background: var(--color-surface-hover) ↔ none<br>P·catalog/catalog.css:94 `.colmenu button.cm-i:hover` {0,3,1} background: var(--color-surface-hover) ↔ var(--color-gray-100)<br>S·catalog/catalog.css:124 `.fchips .fc button` {0,2,1} background: var(--color-surface-hover) ↔ none<br>S·dashboard/dashboard.css:207 `.dash-tile--linked button` {0,1,1} background: var(--color-surface-hover) ↔ none<br>S·dashboard/dashboard.css:223 `.dash-recent button` {0,1,1} background: var(--color-surface-hover) ↔ none<br>S·dashboard/dashboard.css:283 `.titem button` {0,1,1} background: var(--color-surface-hover) ↔ none<br>S·preview/preview.css:326 `.pv-zoom button` {0,1,1} background: var(--color-surface-hover) ↔ var(--color-surface)<br>S·project/project.css:88 `.pj-views button` {0,1,1} background: var(--color-surface-hover) ↔ transparent<br>S·project/project.css:95 `.pj-views button.on` {0,2,1} background: var(--color-surface-hover) ↔ var(--color-gray-100)<br>S·project/project.css:438 `.pj-seg button` {0,1,1} background: var(--color-surface-hover) ↔ none<br>S·project/project.css:447 `.pj-seg button.on` {0,2,1} background: var(--color-surface-hover) ↔ var(--color-gray-100)<br>S·search/search.css:13 `.search-hero button` {0,1,1} background: var(--color-surface-hover) ↔ var(--color-primary-600, #1f5eff)<br>S·upload/upload.css:201 `.regsteps button` {0,1,1} background: var(--color-surface-hover) ↔ none<br>S·upload/upload.css:208 `.regsteps button.is-active` {0,2,1} background: var(--color-surface-hover) ↔ var(--color-primary-600)<br>S·upload/upload.css:508 `.dr-nav button` {0,1,1} background: var(--color-surface-hover) ↔ var(--color-surface)<br>S·upload/upload.css:535 `.dr-useg button` {0,1,1} background: var(--color-surface-hover) ↔ var(--color-surface)<br>S·upload/upload.css:540 `.dr-useg button.on` {0,2,1} background: var(--color-surface-hover) ↔ var(--color-primary-600)<br>P·upload/upload.css:590 `.modal-takeover[data-scene="register"] .` {0,3,1} background: var(--color-surface-hover) ↔ transparent |
| 171 | L195 | P·upload/upload.css:50 `.modal-takeover .modal-h .x` {0,3,0} background: transparent ↔ none; font-size: 24px ↔ 20px |
| 172 | L197 | P·project/project.css:70 `.pj-toolbar` {0,1,0} padding: var(--space-card) ↔ 10px 12px; gap: 16px ↔ 12px; border-radius: var(--radius-lg)  |
| 173 | L198 | P·project/project.css:81 `.pj-ctl` {0,1,0} display: grid ↔ inline-flex; gap: 8px ↔ 6px |
| 174 | L199 | P·catalog/catalog.css:198 `.catalog-filters select` {0,1,1} padding: 8px 12px ↔ 0 10px; border: 1px solid var(--color-border-control) ↔ 1px solid var(<br>P·catalog/catalog.css:205@≤640 `.catalog-filters select` {0,1,1} font-size: var(--text-body-sm) ↔ 16px<br>D·detail/detail.css:300 `.detail-page .dt-edit.de-inline select` {0,3,1} min-height: var(--control-height) ↔ 40px; padding: 8px 12px ↔ 8px 10px; font-size: var(--t<br>S·shell/shell.css:412@≤640 `select` {0,0,1} font-size: var(--text-body-sm) ↔ 16px<br>S·shell/shell.css:423@≤640 `body select` {0,0,2} font-size: var(--text-body-sm) ↔ max(16px, 1em) !important |
| 176 | L201 | O·catalog/catalog.css:90 `.colmenu button.cm-i` {0,2,1} color: var(--color-text) ↔ var(--color-text-body); font-size: var(--text-body-sm) ↔ 13px<br>O·catalog/catalog.css:124 `.fchips .fc button` {0,2,1} color: var(--color-text) ↔ var(--color-gray-500); font-size: var(--text-body-sm) ↔ 13px<br>P·dashboard/dashboard.css:223 `.dash-recent button` {0,1,1} font-size: var(--text-body-sm) ↔ 13px<br>P·preview/preview.css:326 `.pv-zoom button` {0,1,1} font-size: var(--text-body-sm) ↔ 13px<br>P·project/project.css:438 `.pj-seg button` {0,1,1} font-size: var(--text-body-sm) ↔ 13px<br>P·search/search.css:13 `.search-hero button` {0,1,1} color: var(--color-text) ↔ var(--color-on-primary)<br>O·upload/upload.css:208 `.regsteps button.is-active` {0,2,1} color: var(--color-text) ↔ var(--color-on-primary)<br>P·upload/upload.css:508 `.dr-nav button` {0,1,1} color: var(--color-text) ↔ var(--color-text-body)<br>P·upload/upload.css:535 `.dr-useg button` {0,1,1} color: var(--color-text) ↔ var(--color-text-body); font-size: var(--text-body-sm) ↔ var(--<br>O·upload/upload.css:540 `.dr-useg button.on` {0,2,1} color: var(--color-text) ↔ var(--color-text-on-primary)<br>D·upload/upload.css:590 `.modal-takeover[data-scene="register"] .` {0,3,1} color: var(--color-text) ↔ var(--up-muted)<br>D·upload/upload.css:591 `.modal-takeover[data-scene="register"] .` {0,4,1} color: var(--color-text) ↔ var(--up-ink)<br>D·upload/upload.css:642 `.modal-takeover .dr-useg button` {0,3,0} font-size: var(--text-body-sm) ↔ 13px |
| 177 | L202 | P·catalog/catalog.css:90 `.colmenu button.cm-i` {0,2,1} border-radius: var(--radius-sm) 0 0 var(--radius-sm) ↔ var(--radius-sm)<br>S·preview/preview.css:326 `.pv-zoom button` {0,1,1} border-radius: var(--radius-sm) 0 0 var(--radius-sm) ↔ 6px<br>S·search/search.css:13 `.search-hero button` {0,1,1} border-radius: var(--radius-sm) 0 0 var(--radius-sm) ↔ 10px<br>S·upload/upload.css:201 `.regsteps button` {0,1,1} border-radius: var(--radius-sm) 0 0 var(--radius-sm) ↔ 9999px<br>S·upload/upload.css:508 `.dr-nav button` {0,1,1} border-radius: var(--radius-sm) 0 0 var(--radius-sm) ↔ var(--radius-sm)<br>O·upload/upload.css:590 `.modal-takeover[data-scene="register"] .` {0,3,1} border-radius: var(--radius-sm) 0 0 var(--radius-sm) ↔ 0 |
| 178 | L203 | P·catalog/catalog.css:90 `.colmenu button.cm-i` {0,2,1} border-radius: 0 var(--radius-sm) var(--radius-sm) 0 ↔ var(--radius-sm)<br>S·preview/preview.css:326 `.pv-zoom button` {0,1,1} border-radius: 0 var(--radius-sm) var(--radius-sm) 0 ↔ 6px<br>S·search/search.css:13 `.search-hero button` {0,1,1} border-radius: 0 var(--radius-sm) var(--radius-sm) 0 ↔ 10px<br>S·upload/upload.css:201 `.regsteps button` {0,1,1} border-radius: 0 var(--radius-sm) var(--radius-sm) 0 ↔ 9999px<br>S·upload/upload.css:508 `.dr-nav button` {0,1,1} border-radius: 0 var(--radius-sm) var(--radius-sm) 0 ↔ var(--radius-sm)<br>O·upload/upload.css:590 `.modal-takeover[data-scene="register"] .` {0,3,1} border-radius: 0 var(--radius-sm) var(--radius-sm) 0 ↔ 0 |
| 179 | L204 | P·project/project.css:544 `.pj-new` {0,1,0} padding: 8px 14px ↔ 0; border: 1px solid var(--color-primary-600) ↔ 0; background: var(--c |
| 182 | L207 | P·project/project.css:225 `.pj-table` {0,1,0} min-width: 680px ↔ 900px |
| 184 | L212 | P·shell/shell.css:106 `.gnb` {0,1,0} gap: 4px ↔ 10px<br>P·shell/shell.css:365@≤1180 `.gnb` {0,1,0} gap: 4px ↔ 8px |
| 186 | L214 | P·project/project.css:70 `.pj-toolbar` {0,1,0} display: grid ↔ flex; gap: 16px 12px ↔ 12px |
| 188 | L216 | P·catalog/catalog.css:198 `.catalog-filters select` {0,1,1} font-size: 16px ↔ 14px<br>D·detail/detail.css:300 `.detail-page .dt-edit.de-inline select` {0,3,1} font-size: 16px ↔ 14px<br>S·shell/shell.css:423@≤640 `body select` {0,0,2} font-size: 16px ↔ max(16px, 1em) !important |
| 189 | L217 | P·project/project.css:100 `.pj-count` {0,1,0} margin-left: 0 ↔ auto |
| 190 | L220 | S·project/project.css:299 `.pd-sect .quiet` {0,2,0} color: var(--color-primary-700) ↔ var(--color-text-muted)<br>S·project/project.css:544 `.quiet` {0,1,0} color: var(--color-primary-700) ↔ inherit<br>D·search/search.css:50 `.search-page .notice--empty .empty-acts ` {0,4,0} color: var(--color-primary-700) ↔ var(--color-text-body, #21272a) |
| 191 | L222 | O·search/search.css:45 `.search-page .notice--empty .empty-acts ` {0,4,0} height: auto ↔ 32px<br>S·search/search.css:102 `.search-page .vfilter` {0,2,0} height: auto ↔ 28px |
