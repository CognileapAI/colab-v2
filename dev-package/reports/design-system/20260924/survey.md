# frontend 스타일링 현황 조사 (읽기 전용)

- 기준: `develop` @ `ea21d8c2` (2026-09-18 병합 #123) · 조사일 2026-09-24
- 범위: `frontend/` (node_modules·dist 제외). 파일 수정 없음.
- 계측 방법: grep/python 정규식. 주석(`/* */`) 제거 후 계수한 항목은 명시함.

## 요약 수치

| 항목 | 값 |
|---|---|
| CSS 파일 | 19개 / 4,850행 (`frontend/src/**/*.css`) |
| `tokens.css` 커스텀 프로퍼티 선언 | 95건 (4개 블록: 기본 `:root` · `[data-design="calm"]` · `[data-theme="dark"]` · 640px 이하) |
| tokens.css 밖 `:root` 토큰 선언 | 77건 (detail 26 · catalog 18 · upload 18 · project 8 · lineage 3 · toast 3 · preview 1) |
| 여러 파일에 중복 선언된 토큰 이름 | 17종, 그중 값 충돌 5종(아래 §1-4) |
| 정의 없이 참조되는 토큰 | 2종 — `--color-surface-muted`(`detail/deletion.css:10`), `--text-title-sm`(`auth/login.css:198`), 둘 다 fallback 있음 |
| TSX 파일 | 91개 |
| inline `style={{` | 7건 / 5파일, 전부 동적 값(폭 %·transform·절대 좌표·팔레트 색) + 정적 1건 |
| TSX/TS 하드코딩 색 리터럴 | 0건 (정규식 매치 20건은 전부 주석 속 이슈 번호 `#120`·`#121`) |
| CSS 하드코딩 색(주석 제외, 토큰 정의·var fallback 제외) | 5건 |
| CSS `var(--x, #색)` fallback 색 | 67건 (search.css 40) |
| CSS `font-size` literal px vs var | 213 vs 142 |
| CSS padding/margin/gap literal px vs `var(--space-*)` | 729 vs 29 |
| `border-radius` literal px vs `var(--radius-*)` | 66 vs 95 |
| `<button>` 요소 | 202개 |
| 라우트 페이지 | `src/routes/` 10개 + `src/auth/` 페이지 2개(Login·PasswordChange) = 12 |
| 테마 | 있음 — system/light/dark 3상태, `data-theme` + `prefers-color-scheme` + localStorage `colab.theme` |
| 스타일 게이트 | `frontend-visual`(실화면 13px·대비 4.5:1, agent-browser), CSS 원문 계측 vitest 5종, design-review `css_audit.py`(측정 전용·항상 exit 0). stylelint 없음 |

## 1. 기존 디자인 시스템 산출물

### 1-1. 파일별 개요

| 파일 | 행 | 정의 내용 | 로드 경로 |
|---|---|---|---|
| `frontend/src/shell/tokens.css` | 128 | 토큰 정본. 헤더 주석: 값의 정본은 목업 `mockups/제품_260817.html` `:root`, "셸이 실제로 쓰는 토큰만" 옮김. 이후 calm·dark 블록 추가 | `shell/shell.css:1` `@import './tokens.css'`; `components/members/members.css:3`에서도 `@import` (중복) |
| `frontend/src/shell/design-system.css` | 223 | 2026-09-12 승인 대표 디자인. 모든 규칙이 `:is(.colab-ui, .design-preview)` 스코프로 기존 화면 클래스를 덮어쓰는 override 층. 자체 토큰 정의 0 | `shell/shell.css:2` `@import './design-system.css'` |
| `frontend/src/shell/shell.css` | 427 | GNB·셸 레이아웃. 브레이크포인트 1180/1000/880/740/640/560, `prefers-reduced-motion` | `src/shell/styles.ts:18` (마지막 import) |
| `frontend/src/auth/login.css` | 241 | 로그인·비밀번호 변경 + 계정 관리(`AccountAdminPage`) 스타일(`.account-table` 등, #121 작업) | `styles.ts:17`, `LoginPage.tsx`, `PasswordChangePage.tsx`, `routes/AccountAdminPage.tsx:10` |
| `frontend/src/shell/styles.ts` | – | 단일 CSS 진입점: `pretendard` variable dynamic-subset → 화면 CSS 14개 → `login.css` → `shell.css`(tokens·design-system) 순 | `src/main.tsx:1`, `audit-design.tsx:1`, `audit-upload.tsx`, `audit-selected-preview.tsx` |
| `frontend/design-preview.html` / `.js` | 5 / 20 | 디자인 검토 셸. iframe 으로 `audit-design.html?scene=&design=calm&theme=` 를 열고 화면·디자인(calm/before)·테마·폭(full/1440/768/375) 선택. 자체 인라인 CSS는 하드코딩 색 | audit 빌드 |
| `frontend/audit-design.html` / `.tsx` | 1 / 153 | 모의 fixture 로 실제 컴포넌트 렌더. scene 약 25종(catalog, lab, empty, lab-dialog, projects, project-dialog, project-close, project-detail, detail, search*, preview*, members, settings, login, access, pending, approval*, lineage-picker, not-found). `design=full` 이면 `.colab-ui`+`data-design=calm`+`data-theme` 설정 | `audit.vite.config.ts`, `npm run audit:build` / `audit:preview` (`frontend/README-audit.md`) |

- 앱 활성화 방식: `frontend/index.html` `<html data-design="calm">`, `<body class="colab-ui">`, 인라인 스크립트가 첫 렌더 전 `data-theme`·`data-theme-preference` 설정.
- 결과: calm 토큰 블록과 design-system.css 는 `data-design="calm"` / `.colab-ui` 가 있어야만 적용되는 조건부 층이다.

### 1-2. `tokens.css` 커스텀 프로퍼티 (이름만, 블록·범주별)

기본 `:root` (라이트 기본값)
- 색 — 회색: `--color-white` `--color-gray-50` `--color-gray-400` `--color-gray-500`
- 색 — primary: `--color-primary-600` `--color-primary-700` `--color-primary`
- 색 — 면: `--color-bg` `--color-surface` `--color-surface-hover`
- 색 — 선: `--color-border` `--color-border-strong` `--color-border-shell`
- 색 — 글자: `--color-text` `--color-text-body` `--color-text-muted`
- 셸: `--shell-gnb-height` `--shell-gnb-offset` (900px 이하 110px)
- 타이포: `--font-sans`(Pretendard Variable 우선) `--font-mono` `--text-body`(15px) `--leading-body` `--tracking-body` `--text-body-sm`(14px) `--text-caption`(13px)
- 반경: `--radius-sm`(8) `--radius-md`(10)
- 그림자·모션: `--shadow-sm` `--ease`

`:root[data-design="calm"], body.design-preview` (승인 intent 2026-09-12)
- 타이포: `--text-h2`(28px) `--text-section`(16px) `--leading-body`(1.6) `--tracking-body`(0)
- 여백: `--space-page`(32→16) `--space-card`(24→20) `--space-section`(24→20) `--control-height`(40→44), 괄호는 640px 이하 값
- 색: `--color-overlay` `--color-on-primary` `--accent-neutral` `--color-surface-alt` `--color-border-control` `--color-danger` `--color-danger-solid` `--color-on-danger` `--color-text-on-primary` `--color-text-subtle` `--color-danger-600` `--fg-danger` `--bg-danger`
- `color-scheme: light`

`:root[data-theme="dark"], body.design-preview[data-theme="dark"]` — 43개 재정의
- 면·선·글자: `--color-bg` `--color-surface` `--color-surface-alt` `--color-surface-hover` `--color-border` `--color-border-strong` `--color-border-shell` `--color-border-control` `--color-text` `--color-text-body` `--color-text-muted`
- 회색: `--color-gray-50/100/200/400/500/600/700`
- primary: `--color-primary-50/100/200/600/700/800` `--color-on-primary`
- success: `--color-success-50/100/600` · warning: `--color-warning-50/600`
- accent(AI): `--color-accent-50/200/500/700`
- danger: `--color-danger` `--color-danger-solid` `--color-on-danger` `--fg-danger` `--bg-danger`
- 기타: `--accent-neutral` `--color-overlay`; `color-scheme: dark`

주의: 다크 블록은 `--color-gray-100/200/600/700`, `--color-primary-50/100/200/800`, `--color-success-*`, `--color-warning-*`, `--color-accent-*` 를 재정의하지만 이들의 **라이트 값은 tokens.css 에 없다**. 라이트 값은 화면 CSS(`detail.css`, `catalog.css`, `project.css`, `upload.css`)의 `:root` 블록에 흩어져 있다.
- 토큰 체계에 없는 것: spacing 스케일(단 `--space-page/card/section` 3개와 detail.css 로컬 `--space-1..6`), z-index, 폰트 굵기(detail.css `--weight-heading` 만), 반경 lg/pill(화면 CSS에만), shadow-lg(catalog·upload에만).

### 1-3. tokens.css 밖 토큰 선언
- `components/detail/detail.css:5-33` — gray-100/600/700, warning-50/600, primary-50/100/200/800, accent-50/200/500/700, `--color-ai`, `--color-band-dark-2`, `--color-on-dark(-muted)`, `--font-data`, `--radius-lg`, `--radius-pill`, `--text-h2`(24px), `--text-h3`, `--weight-heading`, `--space-4/5/6` 등 26
- `components/catalog/catalog.css:5-25` — gray-100/200/600/700, success-50/600, warning-50/600, primary-50/100/200/800, `--color-surface-alt`, `--color-border-control`, `--font-data`, `--radius-lg`, `--radius-pill`, `--shadow-lg` 등 18
- `components/upload/upload.css` — `--up-line/muted/ink/warn/warn-bg/radius` 별칭 + primary-50/100, `--color-danger-600`, `--color-text-subtle`, `--color-text-on-primary`, `--shadow-lg` 등 18
- `components/project/project.css:9-18` — 8; `lineage.css:169` `--lin-over-*` 3; `toast.css:5` `--toast-*` 3; `preview.css:392` `--pv-frame-ratio`
- 이 드리프트를 막는 시험: `frontend/test/shared-css-tokens.test.ts`(BF-13, catalog·detail·project 세 파일의 같은 이름 값 일치만 검사), `project-css-tokens.test.ts`(BF-11)

### 1-4. 값 충돌 (같은 이름, 다른 값 · 다크 제외)
| 토큰 | 값들 | 실효 |
|---|---|---|
| `--color-border-control` | catalog·upload `:root` #848c94 / tokens calm #a9b3bf | calm 이 specificity 로 승리 |
| `--color-surface-alt` | catalog·project #f4f7fb / tokens calm #f5f7fa | calm 승리 |
| `--text-h2` | detail·project 24px / tokens calm 28px | calm 승리 |
| `--color-danger-600` | upload #ba3125 / calm `var(--fg-danger)`=#a3222b | calm 승리 |
| `--color-text-subtle` | upload #697077 / calm `var(--color-text-muted)` | calm 승리 |
- 즉 화면 CSS의 `:root` 값은 calm 모드에서 일부가 조용히 무시된다. 동일값 중복은 gray-100(3파일), primary-50/100(3파일), radius-lg/pill(3파일), warning-600(3파일) 등 12종.

### 1-5. `design-system.css` 클래스 패밀리
모든 규칙이 기존 화면 클래스를 `:is(.colab-ui, .design-preview)` 아래에서 재정의한다. 독립 컴포넌트 클래스(BEM·`ds-` 접두)는 없다. 참조 셀렉터 약 190개를 패밀리로 묶으면:
- 공통 primitive: `.btn` `.btn-primary` `.btn-secondary` `.inp` `.sel` `.login-input` `.chip`(`--warning/--neutral/--lineage`) `.card` `.card-h` `.card-b` `.tbl` `.tblwrap` `.table-scroll-hint` `.thf` `.notice` `.avatar` `.form-row` `.lbl` `.x` `.quiet` `.strong` `.on`
- 모달: `.modal-takeover` `.modal-h` `.modal--dialog` `.pj-modal(-h/-b/-f/-back)` `.labinfo-modal` `.approval-dialog` `.lin-fix`
- 셸: `.gnb` `.gnb-settings` `.gnb-upload` `.gnb-more(-wrap)` `.gnb-logout` `.mainnav` `.labswitch` `.theme-switcher` `.login-theme` `.login-submit`
- 페이지 컨테이너: `.catalog-page` `.lab-page` `.project-page` `.project-detail` `.detail-page` `.preview-page` `.search-page` `.settings-page` `.notfound` `.page-head` `.desc` `.hcnt`
- 카탈로그: `.catalog-filters` `.axis-pick` `.axis-k` `.fchips` `.fc` `.fname` `.catalog-open` `.colmenu` `.rowact` `.ra` `.rab` `.crosslink` `.lock`
- 대시보드: `.dash-*` 약 25종(`dash-card` `dash-tile(s)` `dash-columns` `dash-col` `dash-bar(-track/-fill)` `dash-steps` `dash-section-label` …), `.todo-*`, `.titem`, `.empty-acts`
- 검색: `.search-hero` `.hero-note` `.hits` `.hit`
- 프로젝트: `.pj-*` 약 20종(`pj-row` `pj-card` `pj-table` `pj-toolbar` `pj-seg` `pj-views` `pj-ctl` `pj-inp` `pj-err` `pj-hint` `pj-ds` …), `.pd-linkurl`
- 상세: `.dt-header` `.dt-card` `.dsec-h`
- 업로드·미리보기: `.up-card` `.up-body` `.up-steps` `.up-empty` `.filecard` `.fmeta` `.fkind` `.reggate` `.regarea` `.reg-actions` `.rg-a` `.dr-pop` `.dr-cal-d` `.mapstage` `.pv-control` `.pv-zoom` `.pv-shot` `.pv-register` `.pv-h2` `.pv-basic-row/grid` `.vfilter`
- 계보: `.lin` `.ln` `.ln-go` `.lin-picker` `.lin-findbar` `.lin-find` `.cm-box` `.css`
- 브레이크포인트: 1100 / 900 / 640px

## 2. TSX 스타일링 방식 (91개 `.tsx`, `src/generated` 는 `.ts`)

(a) inline `style={{`: 총 7건 / 5파일
| 파일 | 건 | 내용 |
|---|---|---|
| `src/components/upload/PreviewPanel.tsx` | 2 | `:631`, `:794` transform translate/scale (zoom) |
| `src/components/preview/PreviewPanels.tsx` | 2 | `:391` 범례 swatch `background: c.color`(데이터 색) · `:487` 절대 좌표 left/top/width/height px |
| `src/components/upload/RegisterArea.tsx` | 1 | `:1007` `marginTop: 16` — 유일한 정적 inline 스타일 |
| `src/components/search/SearchHitCard.tsx` | 1 | `:60` 관련도 막대 `width` |
| `src/components/dashboard/DataMapCard.tsx` | 1 | `:37` 막대 폭 % |
- px 리터럴이 inline 에 들어간 곳: `RegisterArea.tsx:1007`(16) 1건 + 동적 템플릿 px 6건(`PreviewPanels.tsx:487` 4 · transform 2).

(b) className 으로 design-system 클래스 사용: `<button>` 202개 중 className 첫 클래스 분포 — `btn` 67, `btn-secondary` 29, `btn-sm` 28, `btn-primary` 10, `btn-ghost` 7, `btn-strong` 5, 그 외 화면 전용(`quiet` `login-submit` `dash-quiet` `pj-x` `x` `todo-more` `pv-register` `gnb-logout` …) 약 25종. `className` 에 `btn` 포함 131곳, `btn-secondary` 50, `btn-primary` 19, `ghost` 21, `btn-danger` 2.
- `btn-sm` `btn-ghost` `btn-strong` `btn-danger` 는 design-system.css 에 없고 화면 CSS(upload.css `.btn-strong, .btn-primary` 등)에만 있다.

(c) 하드코딩 색 리터럴
- TSX/TS: 실질 0건 (정규식 매치 20건 = 주석 속 `#120`/`#121`; 파일 분포 `useZoomPan.ts` 10 · `PreviewPanels.tsx` 4 · `AccountAdminPage.tsx` 3 · `PreviewPanel.tsx` 2 · `PreviewSlot.tsx` 1). 단 `audit-design.tsx` fixture 범례 `#21918c` 1건.
- CSS(주석 제거 후): 토큰 정의 112건 (tokens.css 66 + 화면 CSS 46), `var()` fallback 67건 (search 40 · upload 9 · shell 6 · detail 3 · lineage 3 · dashboard 2 · lab 2 · preview 2), 생 리터럴 5건:
  - `catalog.css` `color: #fff` (9px 아이콘 글자)
  - `detail.css` `.de-req` 1건
  - `project.css` `background: rgb(15 20 28 / 45%)` (오버레이, `--color-overlay` 와 동일값)
  - `search.css` `background: #fff` (스위치 손잡이)
  - `upload.css:258` `.chip { background: #eef2f7 }`
- `frontend/design-preview.html` 인라인 CSS 는 전부 하드코딩(검토용 셸, 앱 밖).

(d) px 폰트·여백
- TSX 에는 폰트 px 0건, 여백 px 1건(`RegisterArea.tsx:1007`).
- CSS: `font-size` literal px 213 vs var 142. 파일별 literal: upload 50 · project 32 · dashboard 22 · detail 21 · catalog 20 · preview 15 · lineageGraph 14 · lineage 13 · design-system 9 · approval 6.
- padding/margin/gap literal px 729 vs `var(--space-*)` 29. border-radius literal 66 vs `var(--radius-*)` 95.
- 결론: 스타일은 거의 전부 CSS 파일 + 전역 클래스명으로 이뤄지며, 문제는 TSX 가 아니라 CSS 쪽의 토큰 미사용(폰트·여백 수치)과 전역 클래스 충돌이다.

## 3. 컴포넌트 인벤토리

### 3-1. `src/shell/`
| 파일 | 역할 |
|---|---|
| `AppLayout.tsx` (26) | 셸 = GNB + 화면 한 자리 |
| `Gnb.tsx` (219) | 전역 GNB(탭·연구실 전환·업로드·설정·테마·로그아웃) |
| `GnbMoreMenu.tsx` (73) | 좁은 폭 「더보기」 메뉴 |
| `ThemeSwitcher.tsx` (14) | system/light/dark 선택 컨트롤 (GNB·로그인에서 사용) |
| `theme.ts` | 테마 상태·저장·OS/탭 동기화 |
| `styles.ts` | CSS 단일 진입점 |
| `tokens.css` · `design-system.css` · `shell.css` | §1 |

### 3-2. `src/components/` (도메인 폴더별)
- `common/` — **재사용 primitive 후보**: `Toast.tsx`(공통 토스트 1개, PRD-43), `LoadFailure.tsx`(「못 불러왔다」 공통), `VariableTable.tsx`(변수 5열 표, 업로드·상세 공용), `TargetLabSelect.tsx`(연구실 select)
- `approval/` — `VerifiedBadge.tsx`(표시 전용 배지), `VerificationAction.tsx`(승인 요청/승인/취소), `AccessRequestPanel.tsx`(잠김+접근 요청)
- `catalog/` — `CatalogTable.tsx`(8열 표), `AxisFilterBar.tsx`(3축 select 필터), `ColumnMenu.tsx`(열 정렬·값 메뉴 팝오버), `AppliedConditions.tsx`(조건 칩 줄)
- `dashboard/` — `SummaryTiles`, `DataMapCard`, `RecentActivity`, `TodoInbox`, `EmptyLabOnboarding`, `LabInfoModal`
- `datasetpreview/` — `DatasetPreviewSection`(566행), `ScreenshotButton`, `ValueLookupPanel`
- `detail/` — `DetailHeader`, `BasicInfoGrid`, `FileList`, `PieceList`, `UsageSection`, `SectionMenu`(sticky 구역 메뉴), `LockedNotice`, `DatasetEditEntry/Form`, `DatasetDeleteEntry`, `DeleteConfirmModal`, `DefaultGridButton`, `RepresentativeImageSection`, `SearchEvidenceEditor`
- `lab/` — `LabInfoGrid`(읽기 표시), `LabInfoPanel`(설정 편집)
- `lineage/` — `LineageSection`(532), `LineageStep`(402), `LineageFixModal`, `ParentPicker`(311, 등록·상세 공용)
- `members/` — `MemberPermissionGrid`(권한 스위치 표)
- `preview/` — `PreviewPanels`(521), `PreviewPickRow`, `PreviewControls`, `PreviewZoomControls`, `PreviewOverlay`, `PreviewSlot`(4:3 틀), `BasemapLayer`(SVG 기본 지도)
- `project/` — `ProjectCards`, `ProjectTable`, `ProjectDatasetTable`, `ProjectToolbar`, `ProjectFormModal`, `ProjectCloseModal`
- `search/` — `SearchHero`, `SearchHitCard`
- `upload/` — `UploadModal`(1,806행), `RegisterArea`(1,322), `PreviewPanel`(825), `FileDropCard`, `PeriodCalendarPopover`, `GridUploadBlock`, `GridAttachEntry`, `PreviewExpandOverlay`, `UnfinishedUploads`, `UploadEntry`
- `permission/` — `PermissionGate`, `LockedContent`, `session.tsx` (스타일 없음); `placeholders/` 2개(빈 슬롯)

### 3-3. React 컴포넌트 primitive 부재
- `Button`, `Input`, `Select`, `Modal`, `Dialog`, `Table`, `Badge/Chip`, `Card`, `Tabs` 같은 **React primitive 컴포넌트는 하나도 없다.** 모든 화면이 `<button className="btn btn-secondary">`, `<div className="modal-takeover">` 식으로 원시 요소 + 전역 클래스를 직접 쓴다. 재사용 컴포넌트는 도메인 단위(`Toast`, `VariableTable`, `ParentPicker`, `VerifiedBadge`)뿐.

### 3-4. 중복된 primitive (CSS 수준)
| primitive | 정의 위치 |
|---|---|
| `.btn` | `design-system.css:81`(스코프) · `members/members.css:46`(**전역**) · `upload/upload.css:312`(**전역**) — 세 곳이 서로 다른 padding·radius. 로드 순서로 결과가 결정 |
| `.btn-primary` | design-system.css:82 · upload.css:314(`.btn-strong, .btn-primary`) · members.css:60 |
| `.chip` | 전역: `catalog.css:127`, `project.css:322`, `members.css:82`, `upload.css:264` / 스코프: `detail.css:63`(.detail-page), `search.css:82`(.search-page), `lineage.css:233`(.lin) — 7곳 |
| 모달 | `.modal-takeover`(upload, 57 참조) · `.modal`/`.modal-h/-b/-f/-back` · `.pj-modal*`(project) · `.labinfo-modal*`(lab) · `.account-modal`(login.css) · `.modal--dialog` · `.lin-fix` — 최소 6계열 |
| 표 | `.tbl`(catalog, 43) · `.vartable`(20) · `.memtbl`(20) · `.account-table`(18) · `.pj-table`(16) · `.projtable`(7) — 6계열 |
| 입력 | `.inp`/`.sel`(upload 전역 `:258`) · `.pj-inp` · `.login-input` · `.dr-field`; design-system.css:117 이 `.inp, .sel, .login-input, .pv-control select` 를 묶어 정규화 |
| 버튼 유사 | `.login-submit` `.ln-go` `.slicebtn` `.ub-btn` `.rab` `.pj-x` `.x` `.rs-x` `.dash-quiet` `.quiet` 등 |

## 4. 라우트·페이지

`src/app/routes.tsx`(43행, 라우팅 표) · `src/app/App.tsx`(15).

| 페이지 | 역할 | 스타일 원천 · 판단 |
|---|---|---|
| `routes/LabPage.tsx` S-01 | 연구실 대시보드 | dashboard.css + search.css; design-system.css `.dash-*` `.lab-page` 재정의 多 → DS 적용 |
| `routes/DatasetsPage.tsx` S-03 | 카탈로그 | catalog.css; design-system.css `.catalog-*` `.tbl` 재정의 → DS 적용(대표 화면) |
| `routes/DatasetDetailPage.tsx` S-05 | 데이터셋 상세 | detail.css(로컬 토큰 26) + preview/lineage; DS 는 `.dt-header/.dt-card/.dsec-h` 소수 → 부분 |
| `routes/ProjectsPage.tsx` S-02 | 프로젝트 목록 | project.css; DS `.pj-*` 다수 → DS 적용(대표 화면 중 입력 모달) |
| `routes/ProjectDetailPage.tsx` S-02b | 프로젝트 상세 | project.css; DS `.project-detail` → 부분 |
| `routes/SearchResultsPage.tsx` S-06 | 검색 결과 | search.css(fallback 색 40) ; DS `.search-page .hits .hit` → 부분 |
| `routes/UnregisteredPreviewPage.tsx` S-08 | 미등록 미리보기 | preview.css; DS `.preview-page .pv-*` → 부분 |
| `routes/LabSettingsPage.tsx` S-07 | 연구실 설정(정보·구성원 탭) | lab.css·members.css(전역 `.btn` `.chip` 재정의); DS `.settings-page` → 부분·ad hoc |
| `routes/AccountAdminPage.tsx` | 운영자 계정 관리 | `auth/login.css` 에 `.account-*` 직접(#121) → ad hoc |
| `routes/NotFoundPage.tsx` | 없는 주소 | DS `.notfound` |
| `auth/LoginPage.tsx` | 로그인 | login.css; DS `.login-input .login-submit .login-theme` |
| `auth/PasswordChangePage.tsx` | 비밀번호 변경 | login.css |
- 업로드(S-04)는 라우트가 아니라 GNB 에서 여는 전체 화면 모달(`UploadModal`, upload.css 669행).
- 판정 근거: design-system.css 셀렉터 커버리지. 「적용」은 calm 대표 3화면(데이터셋 목록·대시보드·입력 모달) 계열, 나머지는 전체 확장 회차에서 부분 재정의만 받음.

## 5. 테마·폰트·반응형

- 다크 모드: 있음. `index.html` 인라인 스크립트(첫 렌더 전) + `src/shell/theme.ts`(`startThemeSync`, `setThemePreference`, storage key `colab.theme`, 이벤트 `colab:theme`, `matchMedia('(prefers-color-scheme: dark)')` 구독, 다른 탭 `storage` 이벤트 동기화) + `ThemeSwitcher.tsx`. 시험 `frontend/test/theme.test.tsx`.
- CSS 는 `@media (prefers-color-scheme)` 를 쓰지 않고 `:root[data-theme="dark"]` 한 가지로 분기. `color-scheme` 선언 있음.
- 제약: 다크 값은 tokens.css 에 있으나 라이트 값 일부는 화면 CSS 에 분산(§1-2 주의).
- `data-design="calm"` 스위치: `index.html` 고정값. 없으면 calm 토큰·design-system.css 미적용(「before」 모드 = 다크 없음, `design-preview.js` 가 명시).
- 폰트: npm `pretendard` 의존성, `styles.ts:2` 에서 `pretendardvariable-dynamic-subset.css` import. `--font-sans` 첫 항목 `"Pretendard Variable"`. `--font-data` 는 `var(--font-sans)` 별칭(화면 CSS 3곳에 정의).
- 브레이크포인트: 통일 체계 없음. 사용값 — 1536(min) · 1180 · 1100 · 1024(min) · 1000 · 900 · 880 · 740 · 640 · 560. 공통으로 수렴한 값은 640(모바일)·900(GNB 두 줄).
- 접근성 미디어: `prefers-reduced-motion`(shell.css), `prefers-reduced-transparency`(login.css).

## 6. 스타일 관련 시험·게이트

| 이름 | 위치·명령 | 검사 내용 |
|---|---|---|
| `frontend-visual` 게이트 | `gates/tools/frontend-visual.sh`, `gates/run.sh frontend-visual`; 입력 `COLAB_VISUAL_URLS` 또는 `COLAB_VISUAL_EXEMPT=1`(미선언 시 78) | agent-browser 로 페이지를 열어 computed 글자 13px 미만·대비 4.5:1 미만 계수, 라이트·다크 스크린샷. 판정부는 `.agents/skills/design-review/scripts/live_audit.sh` + `live_probe.js` 를 그대로 호출. 허용 목록 `gates/fixtures/frontend-visual/allow.txt`(현재 승인 예외 0). 앱에 읽기 전용 |
| `frontend-visual-selftest` | `gates/tools/frontend-visual-selftest.sh`, fixture `green.html`/`red.html`; CI `.github/workflows/ci.yml:721` 에서 실제 Chromium 으로 실행 | 게이트 자체의 판정 대조 |
| `frontend-test` / `frontend-typecheck` / `frontend-fixture-reach` | `gates/run.sh` (`vitest run`, `tsc --noEmit`, `frontend/scripts/reachable-from-entry.mjs`) | 일반 회귀; 아래 CSS 원문 시험이 여기서 돈다 |
| CSS 원문 계측 vitest | `frontend/test/design-fix-20260908.test.ts`(카드 그림자 0·13px 미만 0·음수 상쇄·미정의 토큰 0, 지정 파일), `css-residual-rc11.test.ts`(Lv 칩 대비·액센트 토큰·미정의 토큰 0), `shared-css-tokens.test.ts`(catalog/detail/project 동명 토큰 값 일치), `project-css-tokens.test.ts`, `account-admin-layout-20260918.test.ts`(#121 레이아웃 선언), `preview-slot-4x3.test.tsx`(`--pv-frame-ratio`) | jsdom 은 스타일을 계산하지 않으므로 CSS 텍스트를 regex 로 읽어 판정. 파일 범위가 개별 지정이라 전역 규칙은 아님 |
| `css_audit.py` | `python3 .agents/skills/design-review/scripts/css_audit.py [--root frontend/src] [--md] [--json]` | 13px 미만, 음수 margin, 미정의 토큰, box-shadow, motion vs reduced-motion, 같은 규칙 색 대비, tokens.css 밖 토큰 정의. **측정 전용, 항상 exit 0** — 게이트 아님 |
| design-review 스킬 | `.agents/skills/design-review/SKILL.md` | audit(판정표 `dev-package/sessions/design-review-<날짜>.md`, 코드 0) → fix(승인 항목만) 2단계. 토큰 정본 = `frontend/src/shell/tokens.css` 로 명시. 정적 합격선: 4.5:1, 13px, 미정의 토큰 0, 음수 여백 0, 카드 그림자 0 |
| apple-design 스킬 | `.agents/skills/apple-design/SKILL.md` (vendored, `disable-model-invocation: true`) | 모션·인터랙션 원칙 참고서, 검사 도구 없음 |
| audit 빌드 | `npm run audit:build` / `audit:preview -- --port 4187` (`frontend/README-audit.md`) | 수동 시각 검수용 fixture 화면 |
- 없는 것: stylelint, 토큰 사용 강제 lint(예: literal px/색 금지), 스크린샷 픽셀 diff 회귀. `frontend-visual-*` 이름의 별도 스킬 디렉터리 없음(게이트 도구만).

## 7. 디자인 관련 기록·결정

- `dev-package/intent/2026-09-12-design-consistency.md` (Ted 승인 2026-09-12): 「절제된 색상, 명확한 글자 위계, 일정한 여백으로 차분하고 정돈된 업무 도구의 인상」; 목록은 촘촘, 입력·안내는 여유; 대표 3화면 먼저 → 전체 확장; 모바일 전 기능·양 테마 동일 기준. 제약: 「구체적인 서체·크기·간격·색상 값은 이 intent의 확정 사항이 아니다」.
- `dev-package/prd/specs/S-DESIGN-CONSISTENCY-20260912.md`(대표안), `S-DESIGN-CONSISTENCY-FULL-20260912.md`(전체 확장: 「화면별 토큰 및 상태색은 토큰 정본에 정의한다」, 테마 3상태·기본 system), `S-DESIGN-REPAIR-20260912.md`(선행 결함 복구).
- `dev-package/prd/rounds/R-DESIGN-CONSISTENCY-FULL-20260912.md`: Architecture 「tokens.css + 공통 디자인 CSS와 테마 제어 모듈. 기존 업무 컴포넌트/source 유지」. 체크리스트 중 계측·게이트·인계 항목이 미체크로 남아 있으나 결과 보고서가 완료를 기록.
- `dev-package/reports/design-consistency/20260912/full/result.md`: 30 장면 × 3폭 × 2테마 = 180 캡처, 13px 미만·대비 미달·가로 넘침 각 0, 4게이트 통과, 회귀 1,216. 「선언한 범위의 미달·미해결 항목은 없다」.
- `dev-package/sessions/design-review-20260912.md`: 정비 직전 검수 — CSS16/TSX82, 판정 주제 31(있음20), 공식 시각 검사 작은 글자 95·대비 미달 23.
- `dev-package/sessions/design-review-20260908*.md`(L1~L4 포함), `p3-design-audit-20260905.md`(WU-A11 11항목 판정표), `p3-design-fix-20260908.md`.
- design-review 스킬 §0: v1 목업 `01 CoLAB-Plan/design/`(`ds-` 어휘, `component-library.html`)은 「v2 정본이 아니다」, `planning-base/design-tokens/tokens.md` 는 빈 템플릿.
- `docs/` 에는 디자인 시스템 결정 문서 없음(매치는 `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` 등 무관). `planning/` 디렉터리 없음.
- 관찰: 컴포넌트 라이브러리·primitive 도입, 토큰 스케일(space/radius/type) 확정, 전역 클래스 충돌 해소에 대한 결정·계획 기록은 찾지 못했다.

### 최근 60커밋 중 frontend 변경 (merge 제외)
| 커밋 | 날짜 | CSS 파일 | 요지 |
|---|---|---|---|
| `f078011d` | 09-18 | 1 | #121 넘침 처리 모든 칸 |
| `db1946c0` | 09-18 | 1 | #121 탭~카드 여백 소유자 1개, 액션 열 고정 |
| `0dcfc205` | 09-18 | 2 | #120 미리보기 도구 층 고정 |
| `315fb85f` | 09-17 | 1 | 계정 생성 폼 |
| `288a52ba` | 09-17 | 1 | 미리보기 팔레트·구간 수 위치 |
| `d0328875` | 09-16 | 5 | 프로젝트 날짜 입력·업로드·상세 사용성 |
| `cf07186d` | 09-16 | 1 | 선택 파일만 미리보기 |
| 그 외 | 09-16~17 | 0 | `bafae4a7`(권한 분리, fe 38파일) 등 로직 |
- 병합 PR 중 UI: #108 `issue-97-93-84-92-ui-fixes`, #100 `codex/issue-ui-polish`, #122 (#120), #123 (#121). 모두 이슈 단위 국소 CSS 수정이며 토큰·공통 층 개편은 없음.

## 8. 이슈 #121 (계정 관리 여백·표) 관례
- 변경 파일: `frontend/src/auth/login.css`, `frontend/src/routes/AccountAdminPage.tsx`, 시험 `frontend/test/account-admin-layout-20260918.test.ts`(CSS 원문 선언 검사), 근거 `dev-package/reports/issue-121/`(전후 화면, `frontend-visual-index.md`), intent/spec `dev-package/intent/2026-09-18-issue-121-account-admin-gap-table.md`, `dev-package/prd/specs/2026-09-18-issue-121-account-admin-gap-table.md`.
- 관례: 화면 CSS 에 국소 규칙 추가 + `⭑ ⟨2026-09-18 · #121⑵⟩` 형태의 날짜·이슈 주석(CSS·TSX 양쪽); 「여백의 소유자는 부모 컨테이너 하나」 원칙; `table-layout: fixed` + 생략 부호; 공용 primitive 추출 없이 `.account-*` 클래스 신설; 시험은 CSS 텍스트 regex 로 선언 존재 확인; agent-browser 전후 캡처 + frontend-visual 인덱스를 근거로 남김.
- 계정 표 스타일이 `auth/login.css` 에 있는 점은 도메인 배치 불일치(로그인 CSS 가 백오피스 표를 소유).

## 9. 디자인 시스템 작업을 위한 시사점 (사실 기반)
1. 토큰 정본이 불완전: 다크 재정의 대상의 라이트 값이 화면 CSS 4곳에 있고 5종은 값 충돌.
2. 스케일 부재: 여백 literal px 729 vs 토큰 29, 폰트 literal 213 vs 142.
3. 전역 클래스 충돌: `.btn` 3곳, `.chip` 7곳, 모달 6계열, 표 6계열.
4. React primitive 0개 — 표준화 단위가 클래스뿐.
5. design-system.css 는 override 층(`:is(.colab-ui, .design-preview)`)이라 원 규칙과 이중 관리.
6. 자동 방어선은 13px·대비 4.5 두 축(frontend-visual)과 파일 지정 regex 시험뿐. 토큰 사용·literal 금지 lint 없음.
