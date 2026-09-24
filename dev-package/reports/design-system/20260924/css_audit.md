# css_audit — static measurement

files 19 · tokens defined 94 · thresholds: font ≥13px · contrast ≥4.5:1 (AA)

| file | <13px | neg margin | undefined token | local token def | box-shadow | motion decl | reduced-motion | contrast <4.5 |
|---|---|---|---|---|---|---|---|---|
| `auth/login.css` | 0 | 0 | 1 | 0 | 0 | 2 | NO | 0 |
| `components/approval/approval.css` | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 |
| `components/catalog/catalog.css` | 3 | 0 | 0 | 18 | 2 | 2 | NO | 0 |
| `components/common/toast.css` | 0 | 0 | 0 | 3 | 0 | 0 | — | 0 |
| `components/common/variableTable.css` | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 |
| `components/dashboard/dashboard.css` | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 |
| `components/detail/deletion.css` | 0 | 0 | 1 | 0 | 0 | 0 | — | 0 |
| `components/detail/detail.css` | 0 | 0 | 0 | 26 | 0 | 0 | — | 1 |
| `components/lab/lab.css` | 0 | 0 | 0 | 0 | 1 | 0 | — | 0 |
| `components/lineage/lineage.css` | 0 | 0 | 0 | 3 | 2 | 0 | — | 0 |
| `components/lineage/lineageGraph.css` | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 |
| `components/members/members.css` | 0 | 0 | 0 | 0 | 2 | 1 | NO | 0 |
| `components/preview/preview.css` | 0 | 0 | 0 | 1 | 1 | 0 | — | 0 |
| `components/project/project.css` | 0 | 0 | 0 | 8 | 1 | 0 | — | 0 |
| `components/search/search.css` | 0 | 0 | 0 | 0 | 0 | 2 | NO | 0 |
| `components/upload/upload.css` | 0 | 0 | 0 | 18 | 2 | 14 | yes | 0 |
| `shell/design-system.css` | 0 | 0 | 0 | 0 | 3 | 0 | — | 0 |
| `shell/shell.css` | 0 | 0 | 0 | 0 | 1 | 7 | yes | 0 |
| `shell/tokens.css` | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 |

## Detail (path:line · value)

### auth/login.css
- `auth/login.css:198` undefined `--text-title-sm` (has fallback)

### components/catalog/catalog.css
- `components/catalog/catalog.css:71` font-size 9.0px
- `components/catalog/catalog.css:98` font-size 9.0px
- `components/catalog/catalog.css:143` font-size 12.0px
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

### components/common/toast.css
- `components/common/toast.css:6` local token def `--toast-fg` (outside tokens.css)
- `components/common/toast.css:7` local token def `--toast-bg` (outside tokens.css)
- `components/common/toast.css:8` local token def `--toast-radius` (outside tokens.css)

### components/detail/deletion.css
- `components/detail/deletion.css:10` undefined `--color-surface-muted` (has fallback)

### components/detail/detail.css
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
- `components/detail/detail.css:229` `.detail-page .dsec-menu-i.is-active` #1369e9 on #edf4ff → **4.49:1** (AA fail)

### components/lab/lab.css
- `components/lab/lab.css:41` box-shadow `none`

### components/lineage/lineage.css
- `components/lineage/lineage.css:306` box-shadow `none`
- `components/lineage/lineage.css:350` box-shadow `none`
- `components/lineage/lineage.css:170` local token def `--lin-over-bg` (outside tokens.css)
- `components/lineage/lineage.css:171` local token def `--lin-over-ink` (outside tokens.css)
- `components/lineage/lineage.css:172` local token def `--lin-over-name` (outside tokens.css)

### components/members/members.css
- `components/members/members.css:94` box-shadow `inset 0 0 0 1px var(--color-primary-600)`
- `components/members/members.css:138` box-shadow `var(--shadow-sm)`

### components/preview/preview.css
- `components/preview/preview.css:260` box-shadow `none`
- `components/preview/preview.css:393` local token def `--pv-frame-ratio` (outside tokens.css)

### components/project/project.css
- `components/project/project.css:279` box-shadow `none`
- `components/project/project.css:10` local token def `--color-gray-100` (outside tokens.css)
- `components/project/project.css:11` local token def `--color-surface-alt` (outside tokens.css)
- `components/project/project.css:12` local token def `--color-success-50` (outside tokens.css)
- `components/project/project.css:14` local token def `--color-success-100` (outside tokens.css)
- `components/project/project.css:15` local token def `--color-success-600` (outside tokens.css)
- `components/project/project.css:16` local token def `--color-warning-600` (outside tokens.css)
- `components/project/project.css:17` local token def `--text-h2` (outside tokens.css)
- `components/project/project.css:18` local token def `--radius-pill` (outside tokens.css)

### components/upload/upload.css
- `components/upload/upload.css:485` box-shadow `0 0 0 3px var(--color-primary-100)`
- `components/upload/upload.css:504` box-shadow `var(--shadow-lg)`
- `components/upload/upload.css:6` local token def `--up-line` (outside tokens.css)
- `components/upload/upload.css:7` local token def `--up-muted` (outside tokens.css)
- `components/upload/upload.css:8` local token def `--up-ink` (outside tokens.css)
- `components/upload/upload.css:9` local token def `--up-warn` (outside tokens.css)
- `components/upload/upload.css:10` local token def `--up-warn-bg` (outside tokens.css)
- `components/upload/upload.css:11` local token def `--up-radius` (outside tokens.css)
- `components/upload/upload.css:451` local token def `--color-border-control` (outside tokens.css)
- `components/upload/upload.css:452` local token def `--color-primary-50` (outside tokens.css)
- `components/upload/upload.css:453` local token def `--color-primary-100` (outside tokens.css)
- `components/upload/upload.css:454` local token def `--color-text-on-primary` (outside tokens.css)
- `components/upload/upload.css:455` local token def `--color-text-subtle` (outside tokens.css)
- `components/upload/upload.css:456` local token def `--color-danger-600` (outside tokens.css)
- `components/upload/upload.css:457` local token def `--font-data` (outside tokens.css)
- `components/upload/upload.css:458` local token def `--leading-body-sm` (outside tokens.css)
- `components/upload/upload.css:459` local token def `--radius-lg` (outside tokens.css)
- `components/upload/upload.css:460` local token def `--shadow-lg` (outside tokens.css)
- `components/upload/upload.css:461` local token def `--space-1` (outside tokens.css)
- `components/upload/upload.css:462` local token def `--space-2` (outside tokens.css)

### shell/design-system.css
- `shell/design-system.css:10` box-shadow `none`
- `shell/design-system.css:122` box-shadow `none`
- `shell/design-system.css:129` box-shadow `none`

### shell/shell.css
- `shell/shell.css:117` box-shadow `var(--shadow-sm)`

