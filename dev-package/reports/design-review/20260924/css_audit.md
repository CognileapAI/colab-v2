# css_audit — static measurement

files 21 · tokens defined 85 · thresholds: font ≥13px · contrast ≥4.5:1 (AA)

| file | <13px | neg margin | undefined token | local token def | box-shadow | motion decl | reduced-motion | contrast <4.5 |
|---|---|---|---|---|---|---|---|---|
| `auth/login.css` | 0 | 0 | 0 | 0 | 0 | 2 | NO | 0 |
| `components/approval/approval.css` | 0 | 0 | 0 | 0 | 1 | 0 | — | 0 |
| `components/catalog/catalog.css` | 2 | 0 | 0 | 0 | 2 | 2 | NO | 0 |
| `components/common/toast.css` | 0 | 0 | 0 | 3 | 0 | 0 | — | 0 |
| `components/common/variableTable.css` | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 |
| `components/dashboard/dashboard.css` | 0 | 0 | 1 | 0 | 1 | 0 | — | 0 |
| `components/detail/deletion.css` | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 |
| `components/detail/detail.css` | 0 | 0 | 0 | 0 | 1 | 0 | — | 1 |
| `components/lab/lab.css` | 0 | 0 | 0 | 0 | 1 | 0 | — | 0 |
| `components/lineage/lineage.css` | 0 | 0 | 0 | 0 | 2 | 0 | — | 0 |
| `components/lineage/lineageGraph.css` | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 |
| `components/members/members.css` | 0 | 0 | 0 | 0 | 1 | 0 | — | 0 |
| `components/preview/preview.css` | 0 | 0 | 6 | 1 | 1 | 0 | — | 0 |
| `components/project/project.css` | 0 | 0 | 0 | 0 | 3 | 0 | — | 0 |
| `components/search/search.css` | 0 | 0 | 1 | 0 | 0 | 2 | NO | 0 |
| `components/upload/upload.css` | 0 | 0 | 0 | 0 | 3 | 14 | yes | 0 |
| `shell/base.css` | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 |
| `shell/layers.css` | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 |
| `shell/primitives.css` | 0 | 0 | 0 | 0 | 3 | 1 | NO | 0 |
| `shell/shell.css` | 0 | 0 | 0 | 0 | 1 | 7 | yes | 0 |
| `shell/tokens.css` | 0 | 0 | 0 | 0 | 0 | 0 | — | 0 |

## Detail (path:line · value)

### components/approval/approval.css
- `components/approval/approval.css:4` box-shadow `none`

### components/catalog/catalog.css
- `components/catalog/catalog.css:48` font-size 9.0px
- `components/catalog/catalog.css:138` font-size 12.0px
- `components/catalog/catalog.css:35` box-shadow `inset 2px 0 0 var(--color-primary-600)`
- `components/catalog/catalog.css:63` box-shadow `var(--shadow-lg)`

### components/common/toast.css
- `components/common/toast.css:7` local token def `--toast-fg` (outside tokens.css)
- `components/common/toast.css:8` local token def `--toast-bg` (outside tokens.css)
- `components/common/toast.css:9` local token def `--toast-radius` (outside tokens.css)

### components/dashboard/dashboard.css
- `components/dashboard/dashboard.css:134` undefined `--dash-bar-w` (no fallback → declaration invalid)
- `components/dashboard/dashboard.css:408` box-shadow `none`

### components/detail/detail.css
- `components/detail/detail.css:317` box-shadow `none`
- `components/detail/detail.css:205` `.detail-page .dsec-menu-i.is-active` #1369e9 on #edf4ff → **4.49:1** (AA fail)

### components/lab/lab.css
- `components/lab/lab.css:42` box-shadow `none`

### components/lineage/lineage.css
- `components/lineage/lineage.css:299` box-shadow `none`
- `components/lineage/lineage.css:343` box-shadow `none`

### components/members/members.css
- `components/members/members.css:49` box-shadow `inset 0 0 0 1px var(--color-primary-600)`

### components/preview/preview.css
- `components/preview/preview.css:150` undefined `--pv-swatch-bg` (no fallback → declaration invalid)
- `components/preview/preview.css:293` undefined `--pv-layers-transform` (no fallback → declaration invalid)
- `components/preview/preview.css:368` undefined `--pv-piece-left` (no fallback → declaration invalid)
- `components/preview/preview.css:369` undefined `--pv-piece-top` (no fallback → declaration invalid)
- `components/preview/preview.css:370` undefined `--pv-piece-w` (no fallback → declaration invalid)
- `components/preview/preview.css:371` undefined `--pv-piece-h` (no fallback → declaration invalid)
- `components/preview/preview.css:265` box-shadow `none`
- `components/preview/preview.css:418` local token def `--pv-frame-ratio` (outside tokens.css)

### components/project/project.css
- `components/project/project.css:270` box-shadow `none`
- `components/project/project.css:345` box-shadow `none`
- `components/project/project.css:592` box-shadow `none`

### components/search/search.css
- `components/search/search.css:92` undefined `--hit-relbar-w` (no fallback → declaration invalid)

### components/upload/upload.css
- `components/upload/upload.css:467` box-shadow `0 0 0 3px var(--color-primary-100)`
- `components/upload/upload.css:486` box-shadow `var(--shadow-lg)`
- `components/upload/upload.css:654` box-shadow `none`

### shell/primitives.css
- `shell/primitives.css:77` box-shadow `none`
- `shell/primitives.css:122` box-shadow `var(--shadow-sm)`
- `shell/primitives.css:130` box-shadow `none`

### shell/shell.css
- `shell/shell.css:114` box-shadow `var(--shadow-sm)`

