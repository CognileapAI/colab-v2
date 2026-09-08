# css_audit — static measurement

files 16 · tokens defined 82 · thresholds: font ≥13px · contrast ≥4.5:1 (AA)

| file | <13px | neg margin | undefined token | local token def | box-shadow | motion decl | reduced-motion | contrast <4.5 |
|---|---|---|---|---|---|---|---|---|
| `auth/login.css` | 0 | 0 | 0 | 0 | 1 | 2 | NO | 0 |
| `components/catalog/catalog.css` | 14 | 0 | 0 | 18 | 2 | 2 | NO | 1 |
| `components/common/toast.css` | 1 | 0 | 0 | 3 | 0 | 0 | — | 0 |
| `components/common/variableTable.css` | 0 | 0 | 2 | 0 | 0 | 0 | — | 0 |
| `components/dashboard/dashboard.css` | 9 | 0 | 20 | 0 | 0 | 0 | — | 0 |
| `components/detail/detail.css` | 9 | 2 | 3 | 30 | 0 | 0 | — | 1 |
| `components/lab/lab.css` | 0 | 0 | 1 | 0 | 1 | 0 | — | 0 |
| `components/lineage/lineage.css` | 9 | 0 | 9 | 3 | 0 | 0 | — | 0 |
| `components/lineage/lineageGraph.css` | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 |
| `components/members/members.css` | 0 | 0 | 0 | 0 | 3 | 1 | NO | 0 |
| `components/preview/preview.css` | 2 | 0 | 20 | 1 | 0 | 0 | — | 0 |
| `components/project/project.css` | 14 | 1 | 0 | 8 | 1 | 0 | — | 1 |
| `components/search/search.css` | 2 | 0 | 0 | 0 | 0 | 2 | NO | 0 |
| `components/upload/upload.css` | 20 | 0 | 9 | 18 | 1 | 7 | yes | 0 |
| `shell/shell.css` | 1 | 1 | 0 | 0 | 1 | 7 | NO | 1 |
| `shell/tokens.css` | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 |

## Detail (path:line · value)

### auth/login.css
- `auth/login.css:20` box-shadow `var(--shadow-sm)`

### components/catalog/catalog.css
- `components/catalog/catalog.css:46` font-size 10.0px
- `components/catalog/catalog.css:71` font-size 9.0px
- `components/catalog/catalog.css:89` font-size 10.0px
- `components/catalog/catalog.css:92` font-size 12.0px
- `components/catalog/catalog.css:98` font-size 9.0px
- `components/catalog/catalog.css:102` font-size 11.0px
- `components/catalog/catalog.css:107` font-size 11.0px
- `components/catalog/catalog.css:117` font-size 11.0px
- `components/catalog/catalog.css:121` font-size 11.0px
- `components/catalog/catalog.css:125` font-size 11.0px
- `components/catalog/catalog.css:127` font-size 11.0px
- `components/catalog/catalog.css:130` font-size 11.0px
- `components/catalog/catalog.css:137` font-size 11.0px
- `components/catalog/catalog.css:141` font-size 11.0px
- `components/catalog/catalog.css:58` box-shadow `inset 2px 0 0 var(--color-primary-600)`
- `components/catalog/catalog.css:86` box-shadow `var(--shadow-lg)`
- `components/catalog/catalog.css:6` local token def `--color-gray-100` (outside tokens.css)
- `components/catalog/catalog.css:7` local token def `--color-gray-200` (outside tokens.css)
- `components/catalog/catalog.css:8` local token def `--color-gray-600` (outside tokens.css)
- `components/catalog/catalog.css:9` local token def `--color-gray-700` (outside tokens.css)
- `components/catalog/catalog.css:10` local token def `--color-success-50` (outside tokens.css)
- `components/catalog/catalog.css:11` local token def `--color-success-600` (outside tokens.css)
- `components/catalog/catalog.css:12` local token def `--color-warning-50` (outside tokens.css)
- `components/catalog/catalog.css:13` local token def `--color-warning-600` (outside tokens.css)
- `components/catalog/catalog.css:14` local token def `--color-primary-50` (outside tokens.css)
- `components/catalog/catalog.css:15` local token def `--color-primary-100` (outside tokens.css)
- `components/catalog/catalog.css:18` local token def `--color-primary-200` (outside tokens.css)
- `components/catalog/catalog.css:19` local token def `--color-primary-800` (outside tokens.css)
- `components/catalog/catalog.css:20` local token def `--color-surface-alt` (outside tokens.css)
- `components/catalog/catalog.css:21` local token def `--color-border-control` (outside tokens.css)
- `components/catalog/catalog.css:22` local token def `--font-data` (outside tokens.css)
- `components/catalog/catalog.css:23` local token def `--radius-lg` (outside tokens.css)
- `components/catalog/catalog.css:24` local token def `--radius-pill` (outside tokens.css)
- `components/catalog/catalog.css:25` local token def `--shadow-lg` (outside tokens.css)
- `components/catalog/catalog.css:138` `/* 승인 처리 도착 전 — 꺼진 조작처럼 (Ted 판정 2026-09-02 · `CT-1` [미확인] ㈎·` #697077 on #e8ecf2 → **4.23:1** (AA fail)

### components/common/toast.css
- `components/common/toast.css:17` font-size 12.0px
- `components/common/toast.css:6` local token def `--toast-fg` (outside tokens.css)
- `components/common/toast.css:7` local token def `--toast-bg` (outside tokens.css)
- `components/common/toast.css:8` local token def `--toast-radius` (outside tokens.css)

### components/common/variableTable.css
- `components/common/variableTable.css:24` undefined `--line` (has fallback)
- `components/common/variableTable.css:49` undefined `--line` (has fallback)

### components/dashboard/dashboard.css
- `components/dashboard/dashboard.css:140` font-size 12.0px
- `components/dashboard/dashboard.css:185` font-size 12.0px
- `components/dashboard/dashboard.css:190` font-size 12.0px
- `components/dashboard/dashboard.css:228` font-size 12.0px
- `components/dashboard/dashboard.css:268` font-size 12.0px
- `components/dashboard/dashboard.css:288` font-size 12.0px
- `components/dashboard/dashboard.css:326` font-size 12.0px
- `components/dashboard/dashboard.css:337` font-size 12.0px
- `components/dashboard/dashboard.css:352` font-size 12.0px
- `components/dashboard/dashboard.css:55` undefined `--fg` (has fallback)
- `components/dashboard/dashboard.css:64` undefined `--line` (has fallback)
- `components/dashboard/dashboard.css:67` undefined `--bg-card` (has fallback)
- `components/dashboard/dashboard.css:87` undefined `--fg-muted` (has fallback)
- `components/dashboard/dashboard.css:118` undefined `--bg-subtle` (has fallback)
- `components/dashboard/dashboard.css:125` undefined `--accent-neutral` (has fallback)
- `components/dashboard/dashboard.css:139` undefined `--fg-muted` (has fallback)
- `components/dashboard/dashboard.css:150` undefined `--line` (has fallback)
- `components/dashboard/dashboard.css:154` undefined `--fg-danger` (has fallback)
- `components/dashboard/dashboard.css:173` undefined `--line` (has fallback)
- `components/dashboard/dashboard.css:186` undefined `--fg-muted` (has fallback)
- `components/dashboard/dashboard.css:191` undefined `--fg-muted` (has fallback)
- `components/dashboard/dashboard.css:227` undefined `--fg-muted` (has fallback)
- `components/dashboard/dashboard.css:235` undefined `--line` (has fallback)
- `components/dashboard/dashboard.css:247` undefined `--fg-muted` (has fallback)
- `components/dashboard/dashboard.css:267` undefined `--fg-muted` (has fallback)
- `components/dashboard/dashboard.css:287` undefined `--fg-muted` (has fallback)
- `components/dashboard/dashboard.css:310` undefined `--bg-subtle` (has fallback)
- `components/dashboard/dashboard.css:325` undefined `--fg-muted` (has fallback)
- `components/dashboard/dashboard.css:336` undefined `--fg-muted` (has fallback)

### components/detail/detail.css
- `components/detail/detail.css:63` font-size 11.0px
- `components/detail/detail.css:66` font-size 11.0px
- `components/detail/detail.css:88` font-size 10.0px
- `components/detail/detail.css:112` font-size 11.0px
- `components/detail/detail.css:141` font-size 12.0px
- `components/detail/detail.css:154` font-size 10.0px
- `components/detail/detail.css:167` font-size 10.0px
- `components/detail/detail.css:188` font-size 10.0px
- `components/detail/detail.css:190` font-size 9.0px
- `components/detail/detail.css:86` `margin: -12px` 를 격자의 `margin-bottom` 으로 옮겼던 것을,
   WU-C11 이 컨테이너 gap 한 자리로 모았다(격자·행동 줄·목록 모두 같은 16px). */
.detail-page .infogrid .ig .k`
- `components/detail/detail.css:146` `margin: -8px 0 var(--space-4)` — 격자의 아래 여백(24px)을 8px 되당겨
   16px 를 만들던 음수 상쇄다. 여백은 부모 `.dt-split-r` 이 `gap` 으로 소유한다(같은 16px). */
.detail-page .dt-gridact`
- `components/detail/detail.css:123` undefined `--font-mono` (has fallback)
- `components/detail/detail.css:126` undefined `--color-danger` (has fallback)
- `components/detail/detail.css:142` undefined `--color-danger` (has fallback)
- `components/detail/detail.css:6` local token def `--color-gray-100` (outside tokens.css)
- `components/detail/detail.css:7` local token def `--color-gray-600` (outside tokens.css)
- `components/detail/detail.css:8` local token def `--color-gray-700` (outside tokens.css)
- `components/detail/detail.css:9` local token def `--color-warning-50` (outside tokens.css)
- `components/detail/detail.css:10` local token def `--color-warning-600` (outside tokens.css)
- `components/detail/detail.css:11` local token def `--color-primary-50` (outside tokens.css)
- `components/detail/detail.css:12` local token def `--color-primary-100` (outside tokens.css)
- `components/detail/detail.css:14` local token def `--color-primary-200` (outside tokens.css)
- `components/detail/detail.css:15` local token def `--color-primary-800` (outside tokens.css)
- `components/detail/detail.css:17` local token def `--color-accent-50` (outside tokens.css)
- `components/detail/detail.css:18` local token def `--color-accent-200` (outside tokens.css)
- `components/detail/detail.css:19` local token def `--color-accent-500` (outside tokens.css)
- `components/detail/detail.css:20` local token def `--color-accent-700` (outside tokens.css)
- `components/detail/detail.css:21` local token def `--color-ai` (outside tokens.css)
- `components/detail/detail.css:22` local token def `--color-band-dark-2` (outside tokens.css)
- `components/detail/detail.css:23` local token def `--color-on-dark` (outside tokens.css)
- `components/detail/detail.css:24` local token def `--color-on-dark-muted` (outside tokens.css)
- `components/detail/detail.css:25` local token def `--font-data` (outside tokens.css)
- `components/detail/detail.css:26` local token def `--radius-lg` (outside tokens.css)
- `components/detail/detail.css:27` local token def `--radius-pill` (outside tokens.css)
- `components/detail/detail.css:28` local token def `--text-h2` (outside tokens.css)
- `components/detail/detail.css:29` local token def `--text-h3` (outside tokens.css)
- `components/detail/detail.css:30` local token def `--weight-heading` (outside tokens.css)
- `components/detail/detail.css:31` local token def `--space-4` (outside tokens.css)
- `components/detail/detail.css:32` local token def `--space-5` (outside tokens.css)
- `components/detail/detail.css:33` local token def `--space-6` (outside tokens.css)
- `components/detail/detail.css:262` local token def `--dt-split-sticky-top` (outside tokens.css)
- `components/detail/detail.css:263` local token def `--dt-split-gap` (outside tokens.css)
- `components/detail/detail.css:265` local token def `--dt-split-right-min` (outside tokens.css)
- `components/detail/detail.css:266` local token def `--dt-split-left-min` (outside tokens.css)
- `components/detail/detail.css:229` `.detail-page .dsec-menu-i.is-active` #1369e9 on #edf4ff → **4.49:1** (AA fail)

### components/lab/lab.css
- `components/lab/lab.css:11` undefined `--color-danger` (has fallback)
- `components/lab/lab.css:39` box-shadow `0 18px 48px rgba(15, 23, 42, 0.24)`

### components/lineage/lineage.css
- `components/lineage/lineage.css:54` font-size 12.0px
- `components/lineage/lineage.css:70` font-size 12.0px
- `components/lineage/lineage.css:92` font-size 12.0px
- `components/lineage/lineage.css:194` font-size 12.0px
- `components/lineage/lineage.css:199` font-size 12.0px
- `components/lineage/lineage.css:218` font-size 12.0px
- `components/lineage/lineage.css:225` font-size 12.0px
- `components/lineage/lineage.css:265` font-size 12.0px
- `components/lineage/lineage.css:287` font-size 12.0px
- `components/lineage/lineage.css:13` undefined `--muted` (has fallback)
- `components/lineage/lineage.css:20` undefined `--line` (has fallback)
- `components/lineage/lineage.css:22` undefined `--soft` (has fallback)
- `components/lineage/lineage.css:34` undefined `--line` (has fallback)
- `components/lineage/lineage.css:57` undefined `--line` (has fallback)
- `components/lineage/lineage.css:79` undefined `--muted` (has fallback)
- `components/lineage/lineage.css:106` undefined `--line` (has fallback)
- `components/lineage/lineage.css:163` undefined `--line` (has fallback)
- `components/lineage/lineage.css:242` undefined `--line` (has fallback)
- `components/lineage/lineage.css:154` local token def `--lin-over-bg` (outside tokens.css)
- `components/lineage/lineage.css:155` local token def `--lin-over-ink` (outside tokens.css)
- `components/lineage/lineage.css:156` local token def `--lin-over-name` (outside tokens.css)

### components/members/members.css
- `components/members/members.css:9` box-shadow `var(--shadow-sm)`
- `components/members/members.css:78` box-shadow `inset 0 0 0 1px var(--color-primary-600)`
- `components/members/members.css:112` box-shadow `var(--shadow-sm)`

### components/preview/preview.css
- `components/preview/preview.css:286` font-size 12.0px
- `components/preview/preview.css:356` font-size 12.0px
- `components/preview/preview.css:20` undefined `--ink-2` (has fallback)
- `components/preview/preview.css:32` undefined `--line` (has fallback)
- `components/preview/preview.css:34` undefined `--surface-2` (has fallback)
- `components/preview/preview.css:49` undefined `--ink-1` (has fallback)
- `components/preview/preview.css:51` undefined `--ink-1` (has fallback)
- `components/preview/preview.css:74` undefined `--line` (has fallback)
- `components/preview/preview.css:81` undefined `--ink-2` (has fallback)
- `components/preview/preview.css:101` undefined `--ink-2` (has fallback)
- `components/preview/preview.css:113` undefined `--line` (has fallback)
- `components/preview/preview.css:115` undefined `--surface-2` (has fallback)
- `components/preview/preview.css:159` undefined `--ink-2` (has fallback)
- `components/preview/preview.css:165` undefined `--line` (has fallback)
- `components/preview/preview.css:172` undefined `--ink-3` (has fallback)
- `components/preview/preview.css:186` undefined `--line` (has fallback)
- `components/preview/preview.css:188` undefined `--surface-2` (has fallback)
- `components/preview/preview.css:206` undefined `--accent` (has fallback)
- `components/preview/preview.css:231` undefined `--line` (has fallback)
- `components/preview/preview.css:233` undefined `--surface-1` (has fallback)
- `components/preview/preview.css:303` undefined `--line` (has fallback)
- `components/preview/preview.css:305` undefined `--surface-2` (has fallback)
- `components/preview/preview.css:295` local token def `--pv-frame-ratio` (outside tokens.css)

### components/project/project.css
- `components/project/project.css:102` font-size 12.0px
- `components/project/project.css:142` font-size 12.0px
- `components/project/project.css:185` font-size 11.0px
- `components/project/project.css:203` font-size 12.0px
- `components/project/project.css:266` font-size 12.0px
- `components/project/project.css:292` font-size 11.0px
- `components/project/project.css:372` font-size 12.0px
- `components/project/project.css:430` font-size 11.0px
- `components/project/project.css:440` font-size 12.0px
- `components/project/project.css:461` font-size 12.0px
- `components/project/project.css:480` font-size 11.0px
- `components/project/project.css:490` font-size 12.0px
- `components/project/project.css:503` font-size 12.0px
- `components/project/project.css:525` font-size 11.0px
- `components/project/project.css:436` `margin: -6px 0 14px`
- `components/project/project.css:245` box-shadow `var(--shadow-sm)`
- `components/project/project.css:10` local token def `--color-gray-100` (outside tokens.css)
- `components/project/project.css:11` local token def `--color-surface-alt` (outside tokens.css)
- `components/project/project.css:12` local token def `--color-success-50` (outside tokens.css)
- `components/project/project.css:14` local token def `--color-success-100` (outside tokens.css)
- `components/project/project.css:15` local token def `--color-success-600` (outside tokens.css)
- `components/project/project.css:16` local token def `--color-warning-600` (outside tokens.css)
- `components/project/project.css:17` local token def `--text-h2` (outside tokens.css)
- `components/project/project.css:18` local token def `--radius-pill` (outside tokens.css)
- `components/project/project.css:527` `.project-detail .verified--pending` #697077 on #e8ecf2 → **4.23:1** (AA fail)

### components/search/search.css
- `components/search/search.css:52` font-size 11.0px
- `components/search/search.css:124` font-size 11.0px

### components/upload/upload.css
- `components/upload/upload.css:108` font-size 12.0px
- `components/upload/upload.css:137` font-size 12.0px
- `components/upload/upload.css:138` font-size 12.0px
- `components/upload/upload.css:153` font-size 12.0px
- `components/upload/upload.css:154` font-size 12.0px
- `components/upload/upload.css:159` font-size 12.0px
- `components/upload/upload.css:196` font-size 12.0px
- `components/upload/upload.css:197` font-size 12.0px
- `components/upload/upload.css:213` font-size 12.0px
- `components/upload/upload.css:214` font-size 10.0px
- `components/upload/upload.css:218` font-size 10.0px
- `components/upload/upload.css:228` font-size 12.0px
- `components/upload/upload.css:231` font-size 12.0px
- `components/upload/upload.css:239` font-size 11.0px
- `components/upload/upload.css:248` font-size 11.0px
- `components/upload/upload.css:259` font-size 12.0px
- `components/upload/upload.css:321` font-size 12.0px
- `components/upload/upload.css:325` font-size 12.0px
- `components/upload/upload.css:341` font-size 12.0px
- `components/upload/upload.css:358` font-size 12.0px
- `components/upload/upload.css:291` undefined `--line` (has fallback)
- `components/upload/upload.css:293` undefined `--surface-2` (has fallback)
- `components/upload/upload.css:296` undefined `--muted` (has fallback)
- `components/upload/upload.css:301` undefined `--muted` (has fallback)
- `components/upload/upload.css:332` undefined `--line` (has fallback)
- `components/upload/upload.css:333` undefined `--surface` (has fallback)
- `components/upload/upload.css:336` undefined `--accent` (has fallback)
- `components/upload/upload.css:338` undefined `--line` (has fallback)
- `components/upload/upload.css:341` undefined `--muted` (has fallback)
- `components/upload/upload.css:399` box-shadow `var(--shadow-lg)`
- `components/upload/upload.css:6` local token def `--up-line` (outside tokens.css)
- `components/upload/upload.css:7` local token def `--up-muted` (outside tokens.css)
- `components/upload/upload.css:8` local token def `--up-ink` (outside tokens.css)
- `components/upload/upload.css:9` local token def `--up-warn` (outside tokens.css)
- `components/upload/upload.css:10` local token def `--up-warn-bg` (outside tokens.css)
- `components/upload/upload.css:11` local token def `--up-radius` (outside tokens.css)
- `components/upload/upload.css:369` local token def `--color-border-control` (outside tokens.css)
- `components/upload/upload.css:370` local token def `--color-primary-50` (outside tokens.css)
- `components/upload/upload.css:371` local token def `--color-primary-100` (outside tokens.css)
- `components/upload/upload.css:372` local token def `--color-text-on-primary` (outside tokens.css)
- `components/upload/upload.css:373` local token def `--color-text-subtle` (outside tokens.css)
- `components/upload/upload.css:374` local token def `--color-danger-600` (outside tokens.css)
- `components/upload/upload.css:375` local token def `--font-data` (outside tokens.css)
- `components/upload/upload.css:376` local token def `--leading-body-sm` (outside tokens.css)
- `components/upload/upload.css:377` local token def `--radius-lg` (outside tokens.css)
- `components/upload/upload.css:378` local token def `--shadow-lg` (outside tokens.css)
- `components/upload/upload.css:379` local token def `--space-1` (outside tokens.css)
- `components/upload/upload.css:380` local token def `--space-2` (outside tokens.css)

### shell/shell.css
- `shell/shell.css:82` font-size 11.0px
- `shell/shell.css:57` `margin-left: -7px` 는
     자기 왼쪽 padding 을 되당기는 음수 상쇄였다. 글자 시작 위치는 그대로다 (판정 ⑩) */
  padding: 3px 9px 3px 0`
- `shell/shell.css:107` box-shadow `var(--shadow-sm)`
- `shell/shell.css:173` `.mainnav a:hover` #121619 on #69707714 → **3.62:1** (AA fail)

