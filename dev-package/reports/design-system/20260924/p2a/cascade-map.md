# P2a cascade map — design-system.css 규칙별 경쟁 · 오늘의 승자 · 되살아남 후보

생성: `node frontend/scripts/cascade-map.mjs map --rev 7967e00146b8387092e94cf1c3d15efa84fb5d21` · 적재 순서 19파일 · 규칙 1307 · design-system.css 규칙 192. 조사 부록 A(휴리스틱 쌍)를 대체한다.

적재 순서: `components/catalog/catalog.css` → `components/detail/detail.css` → `components/project/project.css` → `components/members/members.css` → `components/lab/lab.css` → `components/search/search.css` → `components/dashboard/dashboard.css` → `components/preview/preview.css` → `components/lineage/lineage.css` → `components/lineage/lineageGraph.css` → `components/upload/upload.css` → `components/approval/approval.css` → `components/common/toast.css` → `components/common/variableTable.css` → `auth/login.css` → `shell/tokens.css` → `shell/design-system.css` → `shell/shell.css` → `components/detail/deletion.css`

판정: 경쟁 규칙 = 속성(longhand)과 미디어 범위가 겹치고, 마지막 compound 가 클래스·속성·id 이름을 공유(`key` · 표에 싣는 것)하거나 요소 이름만 공유·키 없는 요소·전체 compound 인 규칙(`type`·`universal` · 같은 요소에 걸리는지 선택자만으로 알 수 없어 건수만 싣고, 렌더 장면의 계산값 전수 대조로 확인한다). 오늘의 승자 = !important → 특이도(접두 포함) → 순서. 되살아남 = 오늘 DS 가 이기고 값이 다른데, 접두를 뗀 특이도로는 C 가 이기는 것(`필연` = 특이도가 더 큼 · `순서` = 같은 특이도라 새 위치보다 뒤면 이김 · `순서(셸 본문)` = 같은 특이도로 `shell.css` 본문에 있어 셸 맨 앞에 두어도 이김). `⊆S` = C 가 맞는 요소는 전부 S 도 맞는다(선택자·미디어로 증명 · 오늘 그 선언은 모든 문맥에서 죽음 → 삭제 가능).

## 합계

| 항목 | 값 |
|---|---:|
| DS 규칙 | 192 |
| (선택자 인자 × 선언) 단위 | 621 |
| 오늘 어떤 경쟁 규칙에 지는 선언 단위(값 다름) | 49 |
| 되살아남 후보(값 다름) | 394 |
| 그중 상태 선택자(:hover·:focus·[readonly]·[aria-*] 등) | 5 |
| 요소·전체 compound 호환 후보(`type`·`universal` · 표 밖 · 렌더 대조로 확인) | 6804 |

## 되살아남 후보 (값 다름)

| DS# | S(인자) | spec 뒤 | 속성 | DS 값 | 경쟁 C | 위치 | spec C | 미디어 C | C 값 | 종류 | 상태 | ⊆S |
|---:|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | `.catalog-page` | 0,1,0 | padding | `var(--space-page)` | `.catalog-page` | components/catalog/catalog.css:5 | 0,1,0 | - | `24px 20px 40px` | 순서 | - | 예 |
| 4 | `.catalog-page` | 0,1,0 | padding | `var(--space-page)` | `.catalog-page` | components/catalog/catalog.css:157 | 0,1,0 | (max-width: 640px) | `16px 12px 32px` | 순서 | - | 예 |
| 4 | `.catalog-page` | 0,1,0 | padding | `var(--space-page)` | `.catalog-page` | components/catalog/catalog.css:158 | 0,1,0 | (max-width: 640px) | `max(12px, env(safe-area-inset-left))` | 순서 | - | 예 |
| 4 | `.catalog-page` | 0,1,0 | padding | `var(--space-page)` | `.catalog-page` | components/catalog/catalog.css:159 | 0,1,0 | (max-width: 640px) | `max(12px, env(safe-area-inset-right))` | 순서 | - | 예 |
| 4 | `.catalog-page` | 0,1,0 | padding | `var(--space-page)` | `.catalog-page` | components/catalog/catalog.css:160 | 0,1,0 | (max-width: 640px) | `max(32px, env(safe-area-inset-bottom))` | 순서 | - | 예 |
| 4 | `.catalog-page` | 0,1,0 | padding | `var(--space-page)` | `.catalog-page` | components/catalog/catalog.css:180 | 0,1,0 | (max-width: 640px) | `20px 16px 32px` | 순서 | - | 예 |
| 4 | `.catalog-page` | 0,1,0 | padding-bottom | `48px` | `.catalog-page` | components/catalog/catalog.css:5 | 0,1,0 | - | `24px 20px 40px` | 순서 | - | 예 |
| 4 | `.catalog-page` | 0,1,0 | padding-bottom | `48px` | `.catalog-page` | components/catalog/catalog.css:157 | 0,1,0 | (max-width: 640px) | `16px 12px 32px` | 순서 | - | 예 |
| 4 | `.catalog-page` | 0,1,0 | padding-bottom | `48px` | `.catalog-page` | components/catalog/catalog.css:160 | 0,1,0 | (max-width: 640px) | `max(32px, env(safe-area-inset-bottom))` | 순서 | - | 예 |
| 4 | `.catalog-page` | 0,1,0 | padding-bottom | `48px` | `.catalog-page` | components/catalog/catalog.css:180 | 0,1,0 | (max-width: 640px) | `20px 16px 32px` | 순서 | - | 예 |
| 4 | `.lab-page` | 0,1,0 | max-width | `1280px` | `.lab-page` | components/dashboard/dashboard.css:10 | 0,1,0 | - | `1200px` | 순서 | - | 예 |
| 4 | `.lab-page` | 0,1,0 | margin-inline | `auto` | `.lab-page` | components/dashboard/dashboard.css:11 | 0,1,0 | - | `0 auto` | 순서 | - | 예 |
| 4 | `.lab-page` | 0,1,0 | padding | `var(--space-page)` | `.lab-page` | components/dashboard/dashboard.css:12 | 0,1,0 | - | `24px 20px 40px` | 순서 | - | 예 |
| 4 | `.lab-page` | 0,1,0 | padding | `var(--space-page)` | `.lab-page` | components/dashboard/dashboard.css:378 | 0,1,0 | (max-width: 640px) | `20px 16px 32px` | 순서 | - | 예 |
| 4 | `.lab-page` | 0,1,0 | padding-bottom | `48px` | `.lab-page` | components/dashboard/dashboard.css:12 | 0,1,0 | - | `24px 20px 40px` | 순서 | - | 예 |
| 4 | `.lab-page` | 0,1,0 | padding-bottom | `48px` | `.lab-page` | components/dashboard/dashboard.css:378 | 0,1,0 | (max-width: 640px) | `20px 16px 32px` | 순서 | - | 예 |
| 4 | `.project-page` | 0,1,0 | max-width | `1280px` | `.project-page` | components/project/project.css:12 | 0,1,0 | - | `1200px` | 순서 | - | 예 |
| 4 | `.project-page` | 0,1,0 | margin-inline | `auto` | `.project-page` | components/project/project.css:13 | 0,1,0 | - | `0 auto` | 순서 | - | 예 |
| 4 | `.project-page` | 0,1,0 | padding | `var(--space-page)` | `.project-page` | components/project/project.css:11 | 0,1,0 | - | `24px 20px 40px` | 순서 | - | 예 |
| 4 | `.project-page` | 0,1,0 | padding-bottom | `48px` | `.project-page` | components/project/project.css:11 | 0,1,0 | - | `24px 20px 40px` | 순서 | - | 예 |
| 5 | `.page-head h1` | 0,1,1 | font-size | `var(--text-h2)` | `.catalog-page .page-head h1` | components/catalog/catalog.css:7 | 0,2,1 | - | `var(--text-h2, 24px)` | 필연 | - | 예 |
| 5 | `.page-head h1` | 0,1,1 | font-size | `var(--text-h2)` | `.search-page .page-head h1` | components/search/search.css:24 | 0,2,1 | - | `var(--text-h2, 24px)` | 필연 | - | 예 |
| 5 | `.page-head h1` | 0,1,1 | letter-spacing | `-0.02em` | `.catalog-page .page-head h1` | components/catalog/catalog.css:7 | 0,2,1 | - | `-0.023em` | 필연 | - | 예 |
| 5 | `.page-head h1` | 0,1,1 | letter-spacing | `-0.02em` | `.project-page .page-head h1` | components/project/project.css:25 | 0,2,1 | - | `-0.023em` | 필연 | - | 예 |
| 5 | `.search-hero h1` | 0,1,1 | font-size | `var(--text-h2)` | `.search-hero h1` | components/search/search.css:6 | 0,1,1 | - | `var(--text-h2, 24px)` | 순서 | - | 예 |
| 5 | `.search-hero h1` | 0,1,1 | letter-spacing | `-0.02em` | `.search-hero h1` | components/search/search.css:6 | 0,1,1 | - | `-0.023em` | 순서 | - | 예 |
| 6 | `.catalog-page .page-head` | 0,2,0 | gap | `8px 12px` | `.catalog-page .page-head` | components/catalog/catalog.css:6 | 0,2,0 | - | `10px` | 순서 | - | 예 |
| 6 | `.catalog-page .page-head` | 0,2,0 | margin-bottom | `var(--space-section)` | `.catalog-page .page-head` | components/catalog/catalog.css:6 | 0,2,0 | - | `14px` | 순서 | - | 예 |
| 7 | `.catalog-page .desc` | 0,2,0 | font-size | `var(--text-body-sm)` | `.catalog-page .desc` | components/catalog/catalog.css:9 | 0,2,0 | - | `var(--text-caption)` | 순서 | - | 예 |
| 9 | `.card` | 0,1,0 | border-color | `var(--color-border-strong)` | `.catalog-page .card` | components/catalog/catalog.css:13 | 0,2,0 | - | `1px solid var(--color-border-strong)` | 필연 | - | 예 |
| 9 | `.card` | 0,1,0 | border-color | `var(--color-border-strong)` | `.project-detail .card` | components/project/project.css:267 | 0,2,0 | - | `1px solid var(--color-border)` | 필연 | - | 예 |
| 9 | `.card` | 0,1,0 | border-color | `var(--color-border-strong)` | `.card` | components/members/members.css:6 | 0,1,0 | - | `1px solid var(--color-border)` | 순서 | - | 예 |
| 9 | `.card` | 0,1,0 | border-radius | `var(--radius-lg)` | `.project-detail .card` | components/project/project.css:268 | 0,2,0 | - | `10px` | 필연 | - | 예 |
| 9 | `.card` | 0,1,0 | border-radius | `var(--radius-lg)` | `.card` | components/members/members.css:7 | 0,1,0 | - | `var(--radius-md)` | 순서 | - | 예 |
| 9 | `.dash-card` | 0,1,0 | border-color | `var(--color-border-strong)` | `.dash-card` | components/dashboard/dashboard.css:64 | 0,1,0 | - | `1px solid var(--color-border)` | 순서 | - | 예 |
| 9 | `.dash-card` | 0,1,0 | border-radius | `var(--radius-lg)` | `.dash-card` | components/dashboard/dashboard.css:65 | 0,1,0 | - | `10px` | 순서 | - | 예 |
| 9 | `.dash-tile` | 0,1,0 | border-color | `var(--color-border-strong)` | `.dash-tile` | components/dashboard/dashboard.css:185 | 0,1,0 | - | `1px solid var(--color-border)` | 순서 | - | 예 |
| 9 | `.dash-tile` | 0,1,0 | border-radius | `var(--radius-lg)` | `.dash-tile` | components/dashboard/dashboard.css:186 | 0,1,0 | - | `10px` | 순서 | - | 예 |
| 9 | `.pj-modal` | 0,1,0 | border-color | `var(--color-border-strong)` | `.pj-modal` | components/project/project.css:345 | 0,1,0 | - | `1px solid var(--color-border)` | 순서 | - | 예 |
| 9 | `.pj-modal` | 0,1,0 | border-radius | `var(--radius-lg)` | `.pj-modal` | components/project/project.css:346 | 0,1,0 | - | `10px` | 순서 | - | 예 |
| 10 | `.catalog-filters` | 0,1,0 | padding | `var(--space-card)` | `.catalog-filters` | components/catalog/catalog.css:171 | 0,1,0 | - | `20px` | 순서 | - | 예 |
| 10 | `.catalog-filters` | 0,1,0 | padding | `var(--space-card)` | `.catalog-filters` | components/catalog/catalog.css:181 | 0,1,0 | (max-width: 640px) | `16px` | 순서 | - | 예 |
| 10 | `.catalog-filters` | 0,1,0 | gap | `20px` | `.catalog-filters` | components/catalog/catalog.css:171 | 0,1,0 | - | `16px` | 순서 | - | 예 |
| 10 | `.catalog-filters` | 0,1,0 | gap | `20px` | `.catalog-filters` | components/catalog/catalog.css:181 | 0,1,0 | (max-width: 640px) | `14px 12px` | 순서 | - | 예 |
| 11 | `.catalog-filters .axis-pick` | 0,2,0 | gap | `8px` | `.catalog-filters .axis-pick` | components/catalog/catalog.css:173 | 0,2,0 | - | `6px` | 순서 | - | 예 |
| 12 | `.axis-k` | 0,1,0 | font-size | `var(--text-caption)` | `.catalog-filters .axis-k` | components/catalog/catalog.css:174 | 0,2,0 | - | `13px` | 필연 | - | 예 |
| 13 | `.catalog-filters select` | 0,1,1 | height | `var(--control-height)` | `.catalog-filters select` | components/catalog/catalog.css:175 | 0,1,1 | - | `38px` | 순서 | - | 예 |
| 13 | `.catalog-filters select` | 0,1,1 | height | `var(--control-height)` | `.catalog-filters select` | components/catalog/catalog.css:182 | 0,1,1 | (max-width: 640px) | `40px` | 순서 | - | 예 |
| 13 | `.catalog-filters select` | 0,1,1 | padding-inline | `12px` | `.catalog-filters select` | components/catalog/catalog.css:175 | 0,1,1 | - | `0 10px` | 순서 | - | 예 |
| 13 | `.catalog-filters select` | 0,1,1 | border-color | `var(--color-border-control)` | `.catalog-filters select` | components/catalog/catalog.css:175 | 0,1,1 | - | `1px solid var(--color-border-strong)` | 순서 | - | 예 |
| 14 | `.tblwrap` | 0,1,0 | max-height | `none` | `.tblwrap` | components/catalog/catalog.css:20 | 0,1,0 | - | `calc(100vh - 232px)` | 순서 | - | 예 |
| 14 | `.tblwrap` | 0,1,0 | max-height | `none` | `.tblwrap` | components/catalog/catalog.css:20 | 0,1,0 | - | `calc(100dvh - 232px)` | 순서 | - | 예 |
| 16 | `.tbl th` | 0,1,1 | color | `var(--color-text-muted)` | `.tbl th` | components/catalog/catalog.css:23 | 0,1,1 | - | `var(--color-gray-500)` | 순서 | - | 예 |
| 16 | `.tbl th` | 0,1,1 | font-weight | `600` | `.tbl th` | components/catalog/catalog.css:23 | 0,1,1 | - | `700` | 순서 | - | 예 |
| 16 | `.tbl th` | 0,1,1 | letter-spacing | `0` | `.tbl th` | components/catalog/catalog.css:23 | 0,1,1 | - | `0.05em` | 순서 | - | 예 |
| 17 | `.tbl th .thf` | 0,2,1 | padding-inline | `16px` | `.tbl thead th > .thf` | components/catalog/catalog.css:44 | 0,2,2 | - | `10px 14px` | 필연 | - | 예 |
| 18 | `.tbl td` | 0,1,1 | padding | `10px 12px` | `.tbl td` | components/catalog/catalog.css:29 | 0,1,1 | - | `13px 14px` | 순서 | - | 예 |
| 18 | `.tbl td` | 0,1,1 | padding | `10px 12px` | `.tbl td.empty` | components/catalog/catalog.css:39 | 0,2,1 | - | `36px 14px` | 필연 | - | 예 |
| 18 | `.tbl td` | 0,1,1 | padding | `10px 12px` | `.tbl td.rowact` | components/catalog/catalog.css:135 | 0,2,1 | - | `14px` | 필연 | - | 예 |
| 19 | `.tbl .fname` | 0,2,0 | font-size | `var(--text-body-sm)` | `.tbl .fname` | components/catalog/catalog.css:36 | 0,2,0 | - | `13px` | 순서 | - | 예 |
| 19 | `.tbl .fname` | 0,2,0 | letter-spacing | `0` | `.tbl .fname` | components/catalog/catalog.css:36 | 0,2,0 | - | `-0.01em` | 순서 | - | 예 |
| 24 | `.tbl .rowact .ra` | 0,3,0 | opacity | `1` | `.tbl td.rowact .ra` | components/catalog/catalog.css:136 | 0,3,1 | - | `0` | 필연 | - | 예 |
| 25 | `.tbl .rowact .rab` | 0,3,0 | width | `36px` | `.tbl td.rowact .rab` | components/catalog/catalog.css:139 | 0,3,1 | - | `26px` | 필연 | - | 예 |
| 25 | `.tbl .rowact .rab` | 0,3,0 | height | `36px` | `.tbl td.rowact .rab` | components/catalog/catalog.css:139 | 0,3,1 | - | `26px` | 필연 | - | 예 |
| 26 | `.fchips` | 0,1,0 | padding | `12px var(--space-card)` | `.fchips` | components/catalog/catalog.css:91 | 0,1,0 | - | `10px 14px` | 순서 | - | 예 |
| 26 | `.fchips` | 0,1,0 | gap | `8px` | `.fchips` | components/catalog/catalog.css:91 | 0,1,0 | - | `6px` | 순서 | - | 예 |
| 27 | `.fchips .fc` | 0,2,0 | height | `32px` | `.fchips .fc` | components/catalog/catalog.css:96 | 0,2,0 | - | `24px` | 순서 | - | 예 |
| 30 | `.crosslink` | 0,1,0 | padding | `16px 20px` | `.crosslink` | components/catalog/catalog.css:148 | 0,1,0 | - | `13px 15px` | 순서 | - | 예 |
| 31 | `.lab-page .search-hero` | 0,2,0 | max-width | `720px` | `.lab-page .search-hero` | components/dashboard/dashboard.css:22 | 0,2,0 | - | `680px` | 순서 | - | 예 |
| 32 | `.search-hero h1` | 0,1,1 | margin-bottom | `24px` | `.search-hero h1` | components/search/search.css:6 | 0,1,1 | - | `0 0 16px` | 순서 | - | 예 |
| 33 | `.search-hero input` | 0,1,1 | border-color | `var(--color-border-control)` | `.search-hero input` | components/search/search.css:10 | 0,1,1 | - | `1px solid var(--color-border-control, #848c94)` | 순서 | - | 예 |
| 33 | `.search-hero input` | 0,1,1 | padding | `14px 16px` | `.search-hero input` | components/search/search.css:9 | 0,1,1 | - | `12px 14px` | 순서 | - | 예 |
| 35 | `.search-hero .hero-note` | 0,2,0 | margin-top | `16px` | `.search-hero .hero-note` | components/search/search.css:18 | 0,2,0 | - | `12px 2px 0` | 순서 | - | 예 |
| 35 | `.search-hero .hero-note` | 0,2,0 | font-size | `var(--text-body-sm)` | `.search-hero .hero-note` | components/search/search.css:18 | 0,2,0 | - | `var(--text-caption, 12px)` | 순서 | - | 예 |
| 36 | `.dash-columns` | 0,1,0 | margin-top | `8px` | `.dash-columns` | components/dashboard/dashboard.css:31 | 0,1,0 | - | `20px` | 순서 | - | 예 |
| 36 | `.dash-columns` | 0,1,0 | gap | `var(--space-section)` | `.dash-columns` | components/dashboard/dashboard.css:30 | 0,1,0 | - | `20px` | 순서 | - | 예 |
| 36 | `.dash-columns` | 0,1,0 | grid-template-columns | `minmax(0, 3fr) minmax(0, 2fr)` | `.dash-columns` | components/dashboard/dashboard.css:36 | 0,1,0 | (max-width: 900px) | `minmax(0, 1fr)` | 순서 | - | 예 |
| 37 | `.dash-col` | 0,1,0 | gap | `20px` | `.dash-col` | components/dashboard/dashboard.css:43 | 0,1,0 | - | `16px` | 순서 | - | 예 |
| 38 | `.dash-section-label` | 0,1,0 | font-size | `var(--text-section)` | `.dash-section-label` | components/dashboard/dashboard.css:53 | 0,1,0 | - | `15px` | 순서 | - | 예 |
| 38 | `.dash-section-label` | 0,1,0 | font-weight | `600` | `.dash-section-label` | components/dashboard/dashboard.css:54 | 0,1,0 | - | `700` | 순서 | - | 예 |
| 39 | `.dash-card` | 0,1,0 | padding | `var(--space-card)` | `.dash-card` | components/dashboard/dashboard.css:66 | 0,1,0 | - | `20px` | 순서 | - | 예 |
| 39 | `.dash-card` | 0,1,0 | padding | `var(--space-card)` | `.dash-card` | components/dashboard/dashboard.css:379 | 0,1,0 | (max-width: 640px) | `16px` | 순서 | - | 예 |
| 40 | `.dash-card-head` | 0,1,0 | align-items | `center` | `.dash-card-head` | components/dashboard/dashboard.css:72 | 0,1,0 | - | `baseline` | 순서 | - | 예 |
| 40 | `.dash-card-head` | 0,1,0 | gap | `8px 16px` | `.dash-card-head` | components/dashboard/dashboard.css:73 | 0,1,0 | - | `8px` | 순서 | - | 예 |
| 40 | `.dash-card-head` | 0,1,0 | margin-bottom | `20px` | `.dash-card-head` | components/dashboard/dashboard.css:74 | 0,1,0 | - | `10px` | 순서 | - | 예 |
| 41 | `.dash-card-head h2` | 0,1,1 | font-size | `var(--text-section)` | `.dash-card-head h2` | components/dashboard/dashboard.css:79 | 0,1,1 | - | `14px` | 순서 | - | 예 |
| 42 | `.dash-bar` | 0,1,0 | font-size | `var(--text-body-sm)` | `.dash-bar` | components/dashboard/dashboard.css:111 | 0,1,0 | - | `13px` | 순서 | - | 예 |
| 42 | `.dash-bar` | 0,1,0 | padding-block | `8px` | `.dash-bar` | components/dashboard/dashboard.css:108 | 0,1,0 | - | `5px 0` | 순서 | - | 예 |
| 42 | `.dash-bar` | 0,1,0 | grid-template-columns | `100px minmax(0, 1fr) 40px` | `.dash-bar` | components/dashboard/dashboard.css:102 | 0,1,0 | - | `96px minmax(0, 1fr) 48px` | 순서 | - | 예 |
| 43 | `.dash-bar-track` | 0,1,0 | height | `6px` | `.dash-bar-track` | components/dashboard/dashboard.css:116 | 0,1,0 | - | `8px` | 순서 | - | 예 |
| 44 | `.dash-bar-fill` | 0,1,0 | background | `var(--accent-neutral)` | `.dash-bar-fill` | components/dashboard/dashboard.css:125 | 0,1,0 | - | `var(--accent-neutral, #5b7089)` | 순서 | - | 예 |
| 46 | `.dash-calc` | 0,1,0 | margin | `8px 0 20px` | `.dash-calc` | components/dashboard/dashboard.css:144 | 0,1,0 | - | `4px 0 12px` | 순서 | - | 예 |
| 47 | `.dash-tiles` | 0,1,0 | gap | `12px` | `.dash-tiles` | components/dashboard/dashboard.css:178 | 0,1,0 | - | `10px` | 순서 | - | 예 |
| 48 | `.dash-tile` | 0,1,0 | padding | `16px` | `.dash-tile` | components/dashboard/dashboard.css:187 | 0,1,0 | - | `10px 12px` | 순서 | - | 예 |
| 49 | `.dash-tile strong` | 0,1,1 | font-size | `28px` | `.dash-tile strong` | components/dashboard/dashboard.css:192 | 0,1,1 | - | `22px` | 순서 | - | 예 |
| 51 | `.dash-open-catalog` | 0,1,0 | min-height | `var(--control-height)` | `.dash-open-catalog` | components/dashboard/dashboard.css:162 | 0,1,0 | - | `38px` | 순서 | - | 예 |
| 51 | `.dash-open-catalog` | 0,1,0 | font-size | `var(--text-body-sm)` | `.dash-open-catalog` | components/dashboard/dashboard.css:169 | 0,1,0 | - | `14px` | 순서 | - | 예 |
| 51 | `.dash-open-catalog` | 0,1,0 | margin-top | `20px` | `.dash-open-catalog` | components/dashboard/dashboard.css:163 | 0,1,0 | - | `16px` | 순서 | - | 예 |
| 51 | `.dash-open-catalog` | 0,1,0 | padding-inline | `16px` | `.dash-open-catalog` | components/dashboard/dashboard.css:164 | 0,1,0 | - | `8px 14px` | 순서 | - | 예 |
| 52 | `.dash-recent button` | 0,1,1 | font-size | `var(--text-body-sm)` | `.dash-recent button` | components/dashboard/dashboard.css:234 | 0,1,1 | - | `13px` | 순서 | - | 예 |
| 52 | `.dash-recent button` | 0,1,1 | padding-block | `12px` | `.dash-recent button` | components/dashboard/dashboard.css:231 | 0,1,1 | - | `6px 0` | 순서 | - | 예 |
| 52 | `.dash-recent button` | 0,1,1 | padding-block | `12px` | `.dash-recent button` | components/dashboard/dashboard.css:381 | 0,1,1 | (max-width: 640px) | `10px 0` | 순서 | - | 예 |
| 53 | `.todo-grp h3` | 0,1,1 | font-size | `var(--text-body-sm)` | `.todo-grp h3` | components/dashboard/dashboard.css:254 | 0,1,1 | - | `13px` | 순서 | - | 예 |
| 53 | `.todo-grp h3` | 0,1,1 | margin-bottom | `12px` | `.todo-grp h3` | components/dashboard/dashboard.css:253 | 0,1,1 | - | `0 0 6px` | 순서 | - | 예 |
| 54 | `.titem` | 0,1,0 | font-size | `var(--text-body-sm)` | `.titem` | components/dashboard/dashboard.css:274 | 0,1,0 | - | `13px` | 순서 | - | 예 |
| 54 | `.titem` | 0,1,0 | padding | `14px 0` | `.titem` | components/dashboard/dashboard.css:273 | 0,1,0 | - | `6px 0` | 순서 | - | 예 |
| 54 | `.titem` | 0,1,0 | gap | `6px 16px` | `.titem` | components/dashboard/dashboard.css:272 | 0,1,0 | - | `4px 10px` | 순서 | - | 예 |
| 56 | `.titem button` | 0,1,1 | padding-inline | `8px` | `.titem button` | components/dashboard/dashboard.css:289 | 0,1,1 | - | `0` | 순서 | - | 예 |
| 58 | `.dash-steps` | 0,1,0 | gap | `12px 20px` | `.dash-steps` | components/dashboard/dashboard.css:311 | 0,1,0 | - | `10px` | 순서 | - | 예 |
| 58 | `.dash-steps` | 0,1,0 | margin-top | `20px` | `.dash-steps` | components/dashboard/dashboard.css:312 | 0,1,0 | - | `8px 0 0` | 순서 | - | 예 |
| 58 | `.dash-steps` | 0,1,0 | margin-top | `20px` | `.dash-steps` | components/dashboard/dashboard.css:370 | 0,1,0 | - | `16px` | 순서 | - | 예 |
| 59 | `.dash-step-no` | 0,1,0 | width | `28px` | `.dash-step-no` | components/dashboard/dashboard.css:372 | 0,1,0 | - | `24px` | 순서 | - | 예 |
| 59 | `.dash-step-no` | 0,1,0 | height | `28px` | `.dash-step-no` | components/dashboard/dashboard.css:372 | 0,1,0 | - | `24px` | 순서 | - | 예 |
| 59 | `.dash-step-no` | 0,1,0 | line-height | `28px` | `.dash-step-no` | components/dashboard/dashboard.css:372 | 0,1,0 | - | `24px` | 순서 | - | 예 |
| 60 | `.pj-modal-back` | 0,1,0 | padding | `24px` | `.pj-modal-back` | components/project/project.css:559 | 0,1,0 | (max-width: 640px) | `16px` | 순서 | - | 예 |
| 60 | `.pj-modal-back` | 0,1,0 | background | `var(--color-overlay)` | `.pj-modal-back` | components/project/project.css:334 | 0,1,0 | - | `rgb(15 20 28 / 45%)` | 순서 | - | 예 |
| 61 | `.pj-modal` | 0,1,0 | width | `min(600px, 100%)` | `.pj-modal` | components/project/project.css:341 | 0,1,0 | - | `min(560px, 100%)` | 순서 | - | 예 |
| 61 | `.pj-modal` | 0,1,0 | max-height | `calc(100dvh - 48px)` | `.pj-modal` | components/project/project.css:342 | 0,1,0 | - | `90vh` | 순서 | - | 예 |
| 61 | `.pj-modal` | 0,1,0 | max-height | `calc(100dvh - 48px)` | `.pj-modal` | components/project/project.css:560 | 0,1,0 | (max-width: 640px) | `calc(100dvh - 32px)` | 순서 | - | 예 |
| 62 | `.pj-modal-h` | 0,1,0 | padding | `20px var(--space-card)` | `.pj-modal-h` | components/project/project.css:354 | 0,1,0 | - | `14px 16px` | 순서 | - | 예 |
| 63 | `.pj-modal-h h3` | 0,1,1 | font-size | `20px` | `.pj-modal-h h3` | components/project/project.css:360 | 0,1,1 | - | `15px` | 순서 | - | 예 |
| 64 | `.pj-x` | 0,1,0 | font-size | `24px` | `.pj-x` | components/project/project.css:366 | 0,1,0 | - | `18px` | 순서 | - | 예 |
| 65 | `.pj-modal-b` | 0,1,0 | padding | `var(--space-card)` | `.pj-modal-b` | components/project/project.css:373 | 0,1,0 | - | `16px` | 순서 | - | 예 |
| 66 | `.pj-modal-f` | 0,1,0 | padding | `16px var(--space-card)` | `.pj-modal-f` | components/project/project.css:381 | 0,1,0 | - | `12px 16px` | 순서 | - | 예 |
| 67 | `.pj-row` | 0,1,0 | margin-bottom | `24px` | `.pj-row` | components/project/project.css:387 | 0,1,0 | - | `14px` | 순서 | - | 예 |
| 68 | `.pj-row label` | 0,1,1 | font-size | `var(--text-body-sm)` | `.pj-row label` | components/project/project.css:393 | 0,1,1 | - | `13px` | 순서 | - | 예 |
| 68 | `.pj-row label` | 0,1,1 | margin-bottom | `8px` | `.pj-row label` | components/project/project.css:392 | 0,1,1 | - | `5px` | 순서 | - | 예 |
| 68 | `.pj-row label` | 0,1,1 | color | `var(--color-text)` | `.pj-row label` | components/project/project.css:394 | 0,1,1 | - | `var(--color-text-muted)` | 순서 | - | 예 |
| 69 | `.pj-inp` | 0,1,0 | padding | `10px 12px` | `.pj-inp` | components/project/project.css:400 | 0,1,0 | - | `7px 9px` | 순서 | - | 예 |
| 69 | `.pj-inp` | 0,1,0 | font-size | `var(--text-body)` | `.pj-inp` | components/project/project.css:403 | 0,1,0 | - | `inherit` | 순서 | - | 예 |
| 69 | `.pj-inp` | 0,1,0 | font-size | `var(--text-body)` | `.pj-inp` | components/project/project.css:404 | 0,1,0 | - | `13px` | 순서 | - | 예 |
| 69 | `.pj-inp` | 0,1,0 | font-size | `var(--text-body)` | `.pj-inp` | components/project/project.css:561 | 0,1,0 | (max-width: 640px) | `16px` | 순서 | - | 예 |
| 69 | `.pj-inp` | 0,1,0 | line-height | `1.5` | `.pj-inp` | components/project/project.css:403 | 0,1,0 | - | `inherit` | 순서 | - | 예 |
| 69 | `.pj-inp` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.pj-inp` | components/project/project.css:401 | 0,1,0 | - | `1px solid var(--color-border)` | 순서 | - | 예 |
| 69 | `.pj-inp` | 0,1,0 | border-radius | `var(--radius-sm)` | `.pj-inp` | components/project/project.css:402 | 0,1,0 | - | `6px` | 순서 | - | 예 |
| 69 | `.pj-tarea` | 0,1,0 | min-height | `var(--control-height)` | `.pj-tarea` | components/project/project.css:408 | 0,1,0 | - | `72px` | 순서 | - | 예 |
| 69 | `.pj-tarea` | 0,1,0 | padding | `10px 12px` | `.pj-tarea` | components/project/project.css:400 | 0,1,0 | - | `7px 9px` | 순서 | - | 예 |
| 69 | `.pj-tarea` | 0,1,0 | font-size | `var(--text-body)` | `.pj-tarea` | components/project/project.css:403 | 0,1,0 | - | `inherit` | 순서 | - | 예 |
| 69 | `.pj-tarea` | 0,1,0 | font-size | `var(--text-body)` | `.pj-tarea` | components/project/project.css:404 | 0,1,0 | - | `13px` | 순서 | - | 예 |
| 69 | `.pj-tarea` | 0,1,0 | font-size | `var(--text-body)` | `.pj-tarea` | components/project/project.css:561 | 0,1,0 | (max-width: 640px) | `16px` | 순서 | - | 예 |
| 69 | `.pj-tarea` | 0,1,0 | line-height | `1.5` | `.pj-tarea` | components/project/project.css:403 | 0,1,0 | - | `inherit` | 순서 | - | 예 |
| 69 | `.pj-tarea` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.pj-tarea` | components/project/project.css:401 | 0,1,0 | - | `1px solid var(--color-border)` | 순서 | - | 예 |
| 69 | `.pj-tarea` | 0,1,0 | border-radius | `var(--radius-sm)` | `.pj-tarea` | components/project/project.css:402 | 0,1,0 | - | `6px` | 순서 | - | 예 |
| 70 | `.pj-tarea` | 0,1,0 | min-height | `96px` | `.pj-tarea` | components/project/project.css:408 | 0,1,0 | - | `72px` | 순서 | - | 예 |
| 70 | `.pj-tarea` | 0,1,0 | min-height | `96px` | `:is(.colab-ui, .design-preview) :is(.pj-inp, .pj-tarea)` | shell/design-system.css:70 | 0,2,0 | - | `var(--control-height)` | DS쌍(순서) | - | 아니오 |
| 71 | `.pj-seg` | 0,1,0 | border-color | `var(--color-border-strong)` | `.pj-seg` | components/project/project.css:419 | 0,1,0 | - | `1px solid var(--color-border)` | 순서 | - | 예 |
| 71 | `.pj-seg` | 0,1,0 | border-radius | `var(--radius-sm)` | `.pj-seg` | components/project/project.css:420 | 0,1,0 | - | `6px` | 순서 | - | 예 |
| 72 | `.pj-seg button` | 0,1,1 | font-size | `var(--text-body-sm)` | `.pj-seg button` | components/project/project.css:428 | 0,1,1 | - | `inherit` | 순서 | - | 예 |
| 72 | `.pj-seg button` | 0,1,1 | font-size | `var(--text-body-sm)` | `.pj-seg button` | components/project/project.css:429 | 0,1,1 | - | `13px` | 순서 | - | 예 |
| 72 | `.pj-seg button` | 0,1,1 | padding-inline | `20px` | `.pj-seg button` | components/project/project.css:425 | 0,1,1 | - | `6px 14px` | 순서 | - | 예 |
| 73 | `.pj-seg button.on` | 0,2,1 | background | `var(--color-surface)` | `.pj-views button.on` | components/project/project.css:82 | 0,2,1 | - | `var(--color-gray-100)` | 순서 | - | 아니오 |
| 73 | `.pj-seg button.on` | 0,2,1 | background | `var(--color-surface)` | `.pj-seg button.on` | components/project/project.css:434 | 0,2,1 | - | `var(--color-gray-100)` | 순서 | - | 예 |
| 73 | `.pj-seg button.on` | 0,2,1 | background | `var(--color-surface)` | `.dr-useg button.on` | components/upload/upload.css:518 | 0,2,1 | - | `var(--color-primary-600)` | 순서 | - | 아니오 |
| 73 | `.pj-seg button.on` | 0,2,1 | color | `var(--color-text)` | `.search-page .vfilter.on` | components/search/search.css:115 | 0,3,0 | - | `var(--color-success-600, #1f8b4c)` | 필연 | - | 아니오 |
| 73 | `.pj-seg button.on` | 0,2,1 | color | `var(--color-text)` | `.dr-useg button.on` | components/upload/upload.css:518 | 0,2,1 | - | `var(--color-text-on-primary)` | 순서 | - | 아니오 |
| 74 | `.pj-defnote` | 0,1,0 | font-size | `var(--text-caption)` | `.pj-defnote` | components/project/project.css:461 | 0,1,0 | - | `13px` | 순서 | - | 예 |
| 74 | `.pj-defnote` | 0,1,0 | line-height | `1.7` | `.pj-defnote` | components/project/project.css:462 | 0,1,0 | - | `1.6` | 순서 | - | 예 |
| 74 | `.pj-hint` | 0,1,0 | font-size | `var(--text-caption)` | `.pj-hint` | components/project/project.css:451 | 0,1,0 | - | `13px` | 순서 | - | 예 |
| 75 | `.pj-fgroup` | 0,1,0 | padding | `20px` | `.pj-fgroup` | components/project/project.css:469 | 0,1,0 | - | `12px` | 순서 | - | 예 |
| 75 | `.pj-fgroup` | 0,1,0 | margin-top | `24px` | `.pj-fgroup` | components/project/project.css:468 | 0,1,0 | - | `4px 0 14px` | 순서 | - | 예 |
| 75 | `.pj-fgroup` | 0,1,0 | border-color | `var(--color-border-strong)` | `.pj-fgroup` | components/project/project.css:470 | 0,1,0 | - | `1px solid var(--color-border)` | 순서 | - | 예 |
| 77 | `.pj-fgroup-h` | 0,1,0 | margin-bottom | `16px` | `.pj-fgroup-h` | components/project/project.css:478 | 0,1,0 | - | `10px` | 순서 | - | 예 |
| 79 | `.pj-err` | 0,1,0 | color | `var(--fg-danger)` | `.pj-err` | components/project/project.css:525 | 0,1,0 | - | `var(--color-warning-600)` | 순서 | - | 예 |
| 80 | `.btn` | 0,1,0 | padding | `10px 18px` | `.btn` | components/members/members.css:47 | 0,1,0 | - | `0 12px` | 순서 | - | 예 |
| 80 | `.btn` | 0,1,0 | padding | `10px 18px` | `.btn` | components/upload/upload.css:304 | 0,1,0 | - | `8px 14px` | 순서 | - | 예 |
| 80 | `.btn` | 0,1,0 | font-size | `var(--text-body-sm)` | `.btn` | components/upload/upload.css:304 | 0,1,0 | - | `inherit` | 순서 | - | 예 |
| 80 | `.btn` | 0,1,0 | border-radius | `var(--radius-sm)` | `.btn` | components/upload/upload.css:304 | 0,1,0 | - | `8px` | 순서 | - | 예 |
| 81 | `.btn-primary` | 0,1,0 | background | `var(--color-primary-600)` | `.btn-primary:hover` | components/members/members.css:64 | 0,2,0 | - | `var(--color-primary-700)` | 필연 | :hover | 예 |
| 81 | `.btn-primary` | 0,1,0 | color | `var(--color-on-primary)` | `.btn-primary` | components/members/members.css:62 | 0,1,0 | - | `var(--color-white)` | 순서 | - | 예 |
| 81 | `.btn-primary` | 0,1,0 | border-color | `var(--color-primary-600)` | `.btn-primary` | components/upload/upload.css:306 | 0,1,0 | - | `var(--up-ink)` | 순서 | - | 예 |
| 84 | `.dash-columns` | 0,1,0 | grid-template-columns | `minmax(0, 1fr)` | `.dash-columns` | components/dashboard/dashboard.css:29 | 0,1,0 | - | `minmax(0, 3fr) minmax(0, 2fr)` | 순서 | - | 아니오 |
| 84 | `.dash-columns` | 0,1,0 | grid-template-columns | `minmax(0, 1fr)` | `:is(.colab-ui, .design-preview) .dash-columns` | shell/design-system.css:37 | 0,2,0 | - | `minmax(0, 3fr) minmax(0, 2fr)` | DS쌍(순서) | - | 아니오 |
| 85 | `.catalog-filters` | 0,1,0 | gap | `16px 12px` | `.catalog-filters` | components/catalog/catalog.css:171 | 0,1,0 | - | `16px` | 순서 | - | 아니오 |
| 85 | `.catalog-filters` | 0,1,0 | gap | `16px 12px` | `.catalog-filters` | components/catalog/catalog.css:181 | 0,1,0 | (max-width: 640px) | `14px 12px` | 순서 | - | 예 |
| 85 | `.catalog-filters` | 0,1,0 | gap | `16px 12px` | `:is(.colab-ui, .design-preview) .catalog-filters` | shell/design-system.css:11 | 0,2,0 | - | `20px` | DS쌍(순서) | - | 아니오 |
| 86 | `.lab-page .search-hero` | 0,2,0 | padding-top | `16px` | `:is(.colab-ui, .design-preview) .lab-page .search-hero` | shell/design-system.css:32 | 0,3,0 | - | `24px` | DS쌍(순서) | - | 아니오 |
| 86 | `.lab-page .search-hero` | 0,2,0 | padding-bottom | `32px` | `:is(.colab-ui, .design-preview) .lab-page .search-hero` | shell/design-system.css:32 | 0,3,0 | - | `40px` | DS쌍(순서) | - | 아니오 |
| 87 | `.search-hero h1` | 0,1,1 | font-size | `24px` | `.search-hero h1` | components/search/search.css:6 | 0,1,1 | - | `var(--text-h2, 24px)` | 순서 | - | 아니오 |
| 87 | `.search-hero h1` | 0,1,1 | font-size | `24px` | `:is(.colab-ui, .design-preview) :is(.page-head h1, .search-hero h1)` | shell/design-system.css:6 | 0,2,1 | - | `var(--text-h2)` | DS쌍(순서) | - | 아니오 |
| 88 | `.dash-tiles` | 0,1,0 | grid-template-columns | `repeat(2, minmax(0, 1fr))` | `.dash-tiles` | components/dashboard/dashboard.css:177 | 0,1,0 | - | `repeat(4, minmax(0, 1fr))` | 순서 | - | 아니오 |
| 89 | `.dash-tile` | 0,1,0 | padding | `16px` | `.dash-tile` | components/dashboard/dashboard.css:187 | 0,1,0 | - | `10px 12px` | 순서 | - | 아니오 |
| 90 | `.dash-bar` | 0,1,0 | min-height | `44px` | `:is(.colab-ui, .design-preview) .dash-bar` | shell/design-system.css:43 | 0,2,0 | - | `40px` | DS쌍(순서) | - | 아니오 |
| 90 | `.dash-bar` | 0,1,0 | grid-template-columns | `96px minmax(0, 1fr) 36px` | `.dash-bar` | components/dashboard/dashboard.css:102 | 0,1,0 | - | `96px minmax(0, 1fr) 48px` | 순서 | - | 아니오 |
| 90 | `.dash-bar` | 0,1,0 | grid-template-columns | `96px minmax(0, 1fr) 36px` | `:is(.colab-ui, .design-preview) .dash-bar` | shell/design-system.css:43 | 0,2,0 | - | `100px minmax(0, 1fr) 40px` | DS쌍(순서) | - | 아니오 |
| 91 | `.dash-steps` | 0,1,0 | gap | `12px` | `.dash-steps` | components/dashboard/dashboard.css:311 | 0,1,0 | - | `10px` | 순서 | - | 아니오 |
| 91 | `.dash-steps` | 0,1,0 | gap | `12px` | `.dash-steps` | components/dashboard/dashboard.css:370 | 0,1,0 | - | `12px 20px` | 순서 | - | 아니오 |
| 91 | `.dash-steps` | 0,1,0 | gap | `12px` | `:is(.colab-ui, .design-preview) .dash-steps` | shell/design-system.css:59 | 0,2,0 | - | `12px 20px` | DS쌍(순서) | - | 아니오 |
| 92 | `.pj-modal-back` | 0,1,0 | padding | `12px` | `.pj-modal-back` | components/project/project.css:333 | 0,1,0 | - | `24px` | 순서 | - | 아니오 |
| 92 | `.pj-modal-back` | 0,1,0 | padding | `12px` | `.pj-modal-back` | components/project/project.css:559 | 0,1,0 | (max-width: 640px) | `16px` | 순서 | - | 예 |
| 92 | `.pj-modal-back` | 0,1,0 | padding | `12px` | `:is(.colab-ui, .design-preview) .pj-modal-back` | shell/design-system.css:61 | 0,2,0 | - | `24px` | DS쌍(순서) | - | 아니오 |
| 93 | `.pj-modal` | 0,1,0 | max-height | `calc(100dvh - 24px)` | `.pj-modal` | components/project/project.css:342 | 0,1,0 | - | `90vh` | 순서 | - | 아니오 |
| 93 | `.pj-modal` | 0,1,0 | max-height | `calc(100dvh - 24px)` | `.pj-modal` | components/project/project.css:560 | 0,1,0 | (max-width: 640px) | `calc(100dvh - 32px)` | 순서 | - | 예 |
| 93 | `.pj-modal` | 0,1,0 | max-height | `calc(100dvh - 24px)` | `:is(.colab-ui, .design-preview) .pj-modal` | shell/design-system.css:62 | 0,2,0 | - | `calc(100dvh - 48px)` | DS쌍(순서) | - | 아니오 |
| 94 | `.pj-modal-h` | 0,1,0 | padding | `16px var(--space-card)` | `.pj-modal-h` | components/project/project.css:354 | 0,1,0 | - | `14px 16px` | 순서 | - | 아니오 |
| 94 | `.pj-modal-h` | 0,1,0 | padding | `16px var(--space-card)` | `:is(.colab-ui, .design-preview) .pj-modal-h` | shell/design-system.css:63 | 0,2,0 | - | `20px var(--space-card)` | DS쌍(순서) | - | 아니오 |
| 95 | `.pj-fgroup` | 0,1,0 | padding | `16px` | `.pj-fgroup` | components/project/project.css:469 | 0,1,0 | - | `12px` | 순서 | - | 아니오 |
| 95 | `.pj-fgroup` | 0,1,0 | padding | `16px` | `:is(.colab-ui, .design-preview) .pj-fgroup` | shell/design-system.css:76 | 0,2,0 | - | `20px` | DS쌍(순서) | - | 아니오 |
| 96 | `.pj-seg button` | 0,1,1 | min-height | `44px` | `:is(.colab-ui, .design-preview) .pj-seg button` | shell/design-system.css:73 | 0,2,1 | - | `36px` | DS쌍(순서) | - | 아니오 |
| 97 | `.colmenu button` | 0,1,1 | min-height | `44px` | `:is(.colab-ui, .design-preview) .colmenu button` | shell/design-system.css:30 | 0,2,1 | - | `36px` | DS쌍(순서) | - | 아니오 |
| 98 | `.tbl .rowact .rab` | 0,3,0 | width | `44px` | `.tbl td.rowact .rab` | components/catalog/catalog.css:139 | 0,3,1 | - | `26px` | 필연 | - | 아니오 |
| 98 | `.tbl .rowact .rab` | 0,3,0 | width | `44px` | `:is(.colab-ui, .design-preview) .tbl .rowact .rab` | shell/design-system.css:26 | 0,4,0 | - | `36px` | DS쌍(순서) | - | 아니오 |
| 98 | `.tbl .rowact .rab` | 0,3,0 | height | `44px` | `.tbl td.rowact .rab` | components/catalog/catalog.css:139 | 0,3,1 | - | `26px` | 필연 | - | 아니오 |
| 98 | `.tbl .rowact .rab` | 0,3,0 | height | `44px` | `:is(.colab-ui, .design-preview) .tbl .rowact .rab` | shell/design-system.css:26 | 0,4,0 | - | `36px` | DS쌍(순서) | - | 아니오 |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.colmenu .cm-box` | components/catalog/catalog.css:74 | 0,2,0 | - | `13px` | 순서 | - | 예 |
| 102 | `.colmenu .cm-box` | 0,2,0 | height | `16px` | `.colmenu .cm-box` | components/catalog/catalog.css:74 | 0,2,0 | - | `13px` | 순서 | - | 예 |
| 102 | `.colmenu .cm-box` | 0,2,0 | font-size | `var(--text-caption)` | `.colmenu .cm-box` | components/catalog/catalog.css:75 | 0,2,0 | - | `9px` | 순서 | - | 예 |
| 102 | `.colmenu .cm-box` | 0,2,0 | color | `var(--color-on-primary)` | `.colmenu .cm-box` | components/catalog/catalog.css:75 | 0,2,0 | - | `#fff` | 순서 | - | 예 |
| 105 | `.inp` | 0,1,0 | padding | `10px 12px` | `.labinfo-modal .inp` | components/lab/lab.css:60 | 0,2,0 | - | `8px 10px` | 필연 | - | 예 |
| 105 | `.inp` | 0,1,0 | padding | `10px 12px` | `.inp` | components/upload/upload.css:250 | 0,1,0 | - | `8px 10px` | 순서 | - | 예 |
| 105 | `.inp` | 0,1,0 | padding | `10px 12px` | `.vartable td .inp` | components/common/variableTable.css:73 | 0,2,1 | - | `0 9px` | 필연 | - | 예 |
| 105 | `.inp` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.labinfo-modal .inp` | components/lab/lab.css:61 | 0,2,0 | - | `1px solid var(--color-border)` | 필연 | - | 예 |
| 105 | `.inp` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.inp` | components/upload/upload.css:250 | 0,1,0 | - | `1px solid var(--up-line)` | 순서 | - | 예 |
| 105 | `.inp` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.modal-takeover .inp` | components/upload/upload.css:595 | 0,2,0 | - | `var(--color-border-control)` | 필연 | - | 예 |
| 105 | `.inp` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.vartable td .inp` | components/common/variableTable.css:74 | 0,2,1 | - | `none` | 필연 | - | 예 |
| 105 | `.inp` | 0,1,0 | border-radius | `var(--radius-sm)` | `.labinfo-modal .inp` | components/lab/lab.css:62 | 0,2,0 | - | `8px` | 필연 | - | 예 |
| 105 | `.inp` | 0,1,0 | border-radius | `var(--radius-sm)` | `.inp` | components/upload/upload.css:250 | 0,1,0 | - | `8px` | 순서 | - | 예 |
| 105 | `.inp` | 0,1,0 | border-radius | `var(--radius-sm)` | `.vartable td .inp` | components/common/variableTable.css:75 | 0,2,1 | - | `0` | 필연 | - | 예 |
| 105 | `.inp` | 0,1,0 | background | `var(--color-surface)` | `.inp[readonly]` | components/upload/upload.css:252 | 0,2,0 | - | `var(--color-surface-alt)` | 필연 | [readonly] | 예 |
| 105 | `.inp` | 0,1,0 | background | `var(--color-surface)` | `.vartable td .inp` | components/common/variableTable.css:76 | 0,2,1 | - | `none` | 필연 | - | 예 |
| 105 | `.inp` | 0,1,0 | color | `var(--color-text)` | `.inp[readonly]` | components/upload/upload.css:252 | 0,2,0 | - | `var(--up-muted)` | 필연 | [readonly] | 예 |
| 105 | `.inp` | 0,1,0 | font | `inherit` | `.labinfo-modal .inp` | components/lab/lab.css:80 | 0,2,0 | (max-width: 640px) | `16px` | 필연 | - | 예 |
| 105 | `.inp` | 0,1,0 | font | `inherit` | `textarea.inp` | components/upload/upload.css:251 | 0,1,1 | - | `1.5` | 필연 | - | 예 |
| 105 | `.inp` | 0,1,0 | font | `inherit` | `.modal-takeover .inp` | components/upload/upload.css:595 | 0,2,0 | - | `14px` | 필연 | - | 예 |
| 105 | `.inp` | 0,1,0 | font | `inherit` | `.vartable td .inp` | components/common/variableTable.css:77 | 0,2,1 | - | `var(--text-body-sm)` | 필연 | - | 예 |
| 105 | `.sel` | 0,1,0 | padding | `10px 12px` | `.labinfo-modal .sel` | components/lab/lab.css:60 | 0,2,0 | - | `8px 10px` | 필연 | - | 예 |
| 105 | `.sel` | 0,1,0 | padding | `10px 12px` | `.sel` | components/upload/upload.css:250 | 0,1,0 | - | `8px 10px` | 순서 | - | 예 |
| 105 | `.sel` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.labinfo-modal .sel` | components/lab/lab.css:61 | 0,2,0 | - | `1px solid var(--color-border)` | 필연 | - | 예 |
| 105 | `.sel` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.sel` | components/upload/upload.css:250 | 0,1,0 | - | `1px solid var(--up-line)` | 순서 | - | 예 |
| 105 | `.sel` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.modal-takeover .sel` | components/upload/upload.css:595 | 0,2,0 | - | `var(--color-border-control)` | 필연 | - | 예 |
| 105 | `.sel` | 0,1,0 | border-radius | `var(--radius-sm)` | `.labinfo-modal .sel` | components/lab/lab.css:62 | 0,2,0 | - | `8px` | 필연 | - | 예 |
| 105 | `.sel` | 0,1,0 | border-radius | `var(--radius-sm)` | `.sel` | components/upload/upload.css:250 | 0,1,0 | - | `8px` | 순서 | - | 예 |
| 105 | `.sel` | 0,1,0 | font | `inherit` | `.labinfo-modal .sel` | components/lab/lab.css:80 | 0,2,0 | (max-width: 640px) | `16px` | 필연 | - | 예 |
| 105 | `.sel` | 0,1,0 | font | `inherit` | `.modal-takeover .sel` | components/upload/upload.css:595 | 0,2,0 | - | `14px` | 필연 | - | 예 |
| 105 | `.login-input` | 0,1,0 | padding | `10px 12px` | `.login-input` | auth/login.css:58 | 0,1,0 | - | `0 12px` | 순서 | - | 예 |
| 105 | `.login-input` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.login-input` | auth/login.css:62 | 0,1,0 | - | `1px solid var(--color-border-strong)` | 순서 | - | 예 |
| 105 | `.login-input` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.login-input:focus-visible` | auth/login.css:69 | 0,2,0 | - | `var(--color-primary)` | 필연 | :focus-visible | 예 |
| 108 | `.detail-page` | 0,1,0 | max-width | `1280px` | `.detail-page` | components/detail/detail.css:5 | 0,1,0 | - | `1200px` | 순서 | - | 예 |
| 108 | `.detail-page` | 0,1,0 | margin-inline | `auto` | `.detail-page` | components/detail/detail.css:5 | 0,1,0 | - | `0 auto` | 순서 | - | 예 |
| 108 | `.detail-page` | 0,1,0 | padding | `var(--space-page)` | `.detail-page` | components/detail/detail.css:5 | 0,1,0 | - | `32px 24px 96px` | 순서 | - | 예 |
| 108 | `.detail-page` | 0,1,0 | padding-bottom | `48px` | `.detail-page` | components/detail/detail.css:5 | 0,1,0 | - | `32px 24px 96px` | 순서 | - | 예 |
| 108 | `.project-detail` | 0,1,0 | max-width | `1280px` | `.project-detail` | components/project/project.css:17 | 0,1,0 | - | `1200px` | 순서 | - | 예 |
| 108 | `.project-detail` | 0,1,0 | margin-inline | `auto` | `.project-detail` | components/project/project.css:18 | 0,1,0 | - | `0 auto` | 순서 | - | 예 |
| 108 | `.project-detail` | 0,1,0 | padding | `var(--space-page)` | `.project-detail` | components/project/project.css:19 | 0,1,0 | - | `32px 24px 96px` | 순서 | - | 예 |
| 108 | `.project-detail` | 0,1,0 | padding-bottom | `48px` | `.project-detail` | components/project/project.css:19 | 0,1,0 | - | `32px 24px 96px` | 순서 | - | 예 |
| 108 | `.preview-page` | 0,1,0 | max-width | `1280px` | `.preview-page` | components/preview/preview.css:8 | 0,1,0 | - | `1080px` | 순서 | - | 예 |
| 108 | `.preview-page` | 0,1,0 | padding | `var(--space-page)` | `.preview-page` | components/preview/preview.css:7 | 0,1,0 | - | `20px 24px 48px` | 순서 | - | 예 |
| 108 | `.preview-page` | 0,1,0 | padding-bottom | `48px` | `.preview-page` | components/preview/preview.css:7 | 0,1,0 | - | `20px 24px 48px` | 순서 | - | 예 |
| 108 | `.settings-page` | 0,1,0 | max-width | `1280px` | `.settings-page` | shell/shell.css:103 | 0,1,0 | - | `1200px` | 순서(셸 본문) | - | 예 |
| 108 | `.settings-page` | 0,1,0 | margin-inline | `auto` | `.settings-page` | shell/shell.css:103 | 0,1,0 | - | `0 auto` | 순서(셸 본문) | - | 예 |
| 108 | `.settings-page` | 0,1,0 | padding | `var(--space-page)` | `.settings-page` | shell/shell.css:103 | 0,1,0 | - | `24px 20px 40px` | 순서(셸 본문) | - | 예 |
| 108 | `.settings-page` | 0,1,0 | padding | `var(--space-page)` | `.settings-page` | shell/shell.css:419 | 0,1,0 | (max-width: 640px) | `20px 16px 32px` | 순서(셸 본문) | - | 예 |
| 108 | `.settings-page` | 0,1,0 | padding-bottom | `48px` | `.settings-page` | shell/shell.css:103 | 0,1,0 | - | `24px 20px 40px` | 순서(셸 본문) | - | 예 |
| 108 | `.settings-page` | 0,1,0 | padding-bottom | `48px` | `.settings-page` | shell/shell.css:419 | 0,1,0 | (max-width: 640px) | `20px 16px 32px` | 순서(셸 본문) | - | 예 |
| 109 | `.search-page` | 0,1,0 | max-width | `920px` | `.search-page` | components/search/search.css:22 | 0,1,0 | - | `880px` | 순서 | - | 예 |
| 109 | `.search-page` | 0,1,0 | padding | `var(--space-page)` | `.search-page` | components/search/search.css:22 | 0,1,0 | - | `24px 20px 40px` | 순서 | - | 예 |
| 110 | `.up-card` | 0,1,0 | border-radius | `var(--radius-lg)` | `.up-card` | components/upload/upload.css:86 | 0,1,0 | - | `var(--up-radius)` | 순서 | - | 예 |
| 110 | `.mapstage` | 0,1,0 | border-radius | `var(--radius-lg)` | `.mapstage` | components/upload/upload.css:86 | 0,1,0 | - | `var(--up-radius)` | 순서 | - | 예 |
| 110 | `.reggate` | 0,1,0 | border-radius | `var(--radius-lg)` | `.reggate` | components/upload/upload.css:86 | 0,1,0 | - | `var(--up-radius)` | 순서 | - | 예 |
| 110 | `.reggate` | 0,1,0 | border-radius | `var(--radius-lg)` | `.up-empty .reggate` | components/upload/upload.css:577 | 0,2,0 | - | `0` | 필연 | - | 예 |
| 110 | `.regarea` | 0,1,0 | border-radius | `var(--radius-lg)` | `.regarea` | components/upload/upload.css:86 | 0,1,0 | - | `var(--up-radius)` | 순서 | - | 예 |
| 111 | `.card-h` | 0,1,0 | padding | `20px var(--space-card)` | `.card-h` | components/members/members.css:13 | 0,1,0 | - | `14px 18px` | 순서 | - | 예 |
| 111 | `.card-b` | 0,1,0 | padding | `20px var(--space-card)` | `.card-b` | components/members/members.css:37 | 0,1,0 | - | `6px 18px` | 순서 | - | 예 |
| 111 | `.card-b` | 0,1,0 | padding | `20px var(--space-card)` | `.memgrid .card-b` | components/members/members.css:177 | 0,2,0 | (max-width: 640px) | `6px 12px` | 필연 | - | 예 |
| 112 | `.card-h h3` | 0,1,1 | font-size | `var(--text-section)` | `.card-h h3` | components/members/members.css:18 | 0,1,1 | - | `var(--text-body)` | 순서 | - | 예 |
| 112 | `.pv-h2` | 0,1,0 | font-size | `var(--text-section)` | `.pv-h2` | components/preview/preview.css:59 | 0,1,0 | - | `15px` | 순서 | - | 예 |
| 113 | `.card-h` | 0,1,0 | gap | `12px` | `.card-h` | components/members/members.css:12 | 0,1,0 | - | `10px` | 순서 | - | 예 |
| 114 | `.search-page .hit` | 0,2,0 | padding | `var(--space-card)` | `.search-page .hit` | components/search/search.css:56 | 0,2,0 | - | `14px 16px` | 순서 | - | 예 |
| 115 | `.search-page .hits` | 0,2,0 | gap | `16px` | `.search-page .hits` | components/search/search.css:54 | 0,2,0 | - | `10px` | 순서 | - | 예 |
| 116 | `.form-row` | 0,1,0 | gap | `8px` | `.labinfo-modal .form-row` | components/lab/lab.css:49 | 0,2,0 | - | `4px` | 필연 | - | 예 |
| 116 | `.form-row` | 0,1,0 | gap | `8px` | `.form-row` | components/upload/upload.css:223 | 0,1,0 | - | `4px` | 순서 | - | 예 |
| 116 | `.form-row` | 0,1,0 | gap | `8px` | `.modal-takeover .form-row` | components/upload/upload.css:594 | 0,2,0 | - | `5px` | 필연 | - | 예 |
| 116 | `.pv-control` | 0,1,0 | gap | `8px` | `.pv-control` | components/preview/preview.css:158 | 0,1,0 | - | `4px` | 순서 | - | 예 |
| 117 | `.labinfo-modal` | 0,1,0 | border-radius | `var(--radius-lg)` | `.labinfo-modal` | components/lab/lab.css:39 | 0,1,0 | - | `12px` | 순서 | - | 예 |
| 117 | `.labinfo-modal` | 0,1,0 | padding | `var(--space-card)` | `.labinfo-modal` | components/lab/lab.css:38 | 0,1,0 | - | `18px` | 순서 | - | 예 |
| 117 | `.approval-dialog` | 0,1,0 | padding | `var(--space-card)` | `.approval-dialog` | components/approval/approval.css:3 | 0,1,0 | - | `24px` | 순서 | - | 예 |
| 119 | `.labinfo-modal h3` | 0,1,1 | font-size | `20px` | `.labinfo-modal h3` | components/lab/lab.css:44 | 0,1,1 | - | `var(--text-body)` | 순서 | - | 예 |
| 119 | `.labinfo-modal h3` | 0,1,1 | margin-bottom | `20px` | `.labinfo-modal h3` | components/lab/lab.css:44 | 0,1,1 | - | `0 0 12px` | 순서 | - | 예 |
| 120 | `.labinfo-modal .form-row` | 0,2,0 | margin-bottom | `20px` | `.labinfo-modal .form-row` | components/lab/lab.css:50 | 0,2,0 | - | `10px` | 순서 | - | 예 |
| 120 | `.labinfo-modal .form-row` | 0,2,0 | margin-bottom | `20px` | `.dr-times .form-row` | components/upload/upload.css:484 | 0,2,0 | - | `0` | 순서 | - | 아니오 |
| 120 | `.labinfo-modal .form-row` | 0,2,0 | margin-bottom | `20px` | `.modal-takeover .form-row` | components/upload/upload.css:594 | 0,2,0 | - | `0` | 순서 | - | 아니오 |
| 121 | `.modal-takeover .up-steps .card-b` | 0,3,0 | gap | `20px` | `.modal-takeover .up-steps .card-b` | components/upload/upload.css:593 | 0,3,0 | - | `12px` | 순서 | - | 예 |
| 121 | `.modal-takeover .up-steps .card-b` | 0,3,0 | padding | `var(--space-card)` | `.modal-takeover .up-steps .card-b` | components/upload/upload.css:593 | 0,3,0 | - | `20px 22px` | 순서 | - | 예 |
| 122 | `.modal-takeover .form-row` | 0,2,0 | gap | `8px` | `.labinfo-modal .form-row` | components/lab/lab.css:49 | 0,2,0 | - | `4px` | 순서 | - | 아니오 |
| 122 | `.modal-takeover .form-row` | 0,2,0 | gap | `8px` | `.modal-takeover .form-row` | components/upload/upload.css:594 | 0,2,0 | - | `5px` | 순서 | - | 예 |
| 123 | `.modal-takeover .reg-actions .btn` | 0,3,0 | height | `auto` | `.modal-takeover .reg-actions .btn` | components/upload/upload.css:618 | 0,3,0 | - | `34px` | 순서 | - | 예 |
| 125 | `.gnb` | 0,1,0 | gap | `12px` | `.gnb` | shell/shell.css:113 | 0,1,0 | - | `10px` | 순서(셸 본문) | - | 예 |
| 125 | `.gnb` | 0,1,0 | gap | `12px` | `.gnb` | shell/shell.css:365 | 0,1,0 | (max-width: 1180px) | `8px` | 순서(셸 본문) | - | 예 |
| 125 | `.gnb` | 0,1,0 | gap | `12px` | `.gnb` | shell/shell.css:393 | 0,1,0 | (max-width: 560px) | `4px` | 순서(셸 본문) | - | 예 |
| 126 | `.gnb-settings` | 0,1,0 | display | `inline-flex` | `.gnb-settings` | shell/shell.css:376 | 0,1,0 | (max-width: 880px) | `none` | 순서(셸 본문) | - | 예 |
| 130 | `.gnb` | 0,1,0 | height | `auto` | `.gnb` | shell/shell.css:110 | 0,1,0 | - | `var(--shell-gnb-height)` | 순서(셸 본문) | - | 아니오 |
| 130 | `.gnb` | 0,1,0 | gap | `8px` | `:is(.colab-ui, .design-preview) .gnb` | shell/design-system.css:137 | 0,2,0 | - | `12px` | DS쌍(순서) | - | 아니오 |
| 130 | `.gnb` | 0,1,0 | gap | `8px` | `.gnb` | shell/shell.css:113 | 0,1,0 | - | `10px` | 순서(셸 본문) | - | 아니오 |
| 130 | `.gnb` | 0,1,0 | gap | `8px` | `.gnb` | shell/shell.css:393 | 0,1,0 | (max-width: 560px) | `4px` | 순서(셸 본문) | - | 예 |
| 130 | `.gnb` | 0,1,0 | padding | `10px 16px` | `.gnb` | shell/shell.css:114 | 0,1,0 | - | `0 20px` | 순서(셸 본문) | - | 아니오 |
| 130 | `.gnb` | 0,1,0 | padding | `10px 16px` | `.gnb` | shell/shell.css:365 | 0,1,0 | (max-width: 1180px) | `0 14px` | 순서(셸 본문) | - | 아니오 |
| 130 | `.gnb` | 0,1,0 | padding | `10px 16px` | `.gnb` | shell/shell.css:393 | 0,1,0 | (max-width: 560px) | `0 10px` | 순서(셸 본문) | - | 예 |
| 130 | `.gnb` | 0,1,0 | padding | `10px 16px` | `.gnb` | shell/shell.css:407 | 0,1,0 | (max-width: 640px) | `max(10px, env(safe-area-inset-left))` | 순서(셸 본문) | - | 예 |
| 130 | `.gnb` | 0,1,0 | padding | `10px 16px` | `.gnb` | shell/shell.css:408 | 0,1,0 | (max-width: 640px) | `max(10px, env(safe-area-inset-right))` | 순서(셸 본문) | - | 예 |
| 138 | `.inp` | 0,1,0 | font-size | `16px` | `.labinfo-modal .inp` | components/lab/lab.css:63 | 0,2,0 | - | `inherit` | 필연 | - | 아니오 |
| 138 | `.inp` | 0,1,0 | font-size | `16px` | `.inp` | components/upload/upload.css:250 | 0,1,0 | - | `inherit` | 순서 | - | 아니오 |
| 138 | `.inp` | 0,1,0 | font-size | `16px` | `.modal-takeover .inp` | components/upload/upload.css:595 | 0,2,0 | - | `14px` | 필연 | - | 아니오 |
| 138 | `.inp` | 0,1,0 | font-size | `16px` | `.vartable td .inp` | components/common/variableTable.css:77 | 0,2,1 | - | `var(--text-body-sm)` | 필연 | - | 아니오 |
| 138 | `.inp` | 0,1,0 | font-size | `16px` | `:is(.colab-ui, .design-preview) :is(.inp, .sel, .login-input, .pv-control select)` | shell/design-system.css:117 | 0,2,1 | - | `inherit` | DS쌍(특이도) | - | 아니오 |
| 138 | `.sel` | 0,1,0 | font-size | `16px` | `.labinfo-modal .sel` | components/lab/lab.css:63 | 0,2,0 | - | `inherit` | 필연 | - | 아니오 |
| 138 | `.sel` | 0,1,0 | font-size | `16px` | `.sel` | components/upload/upload.css:250 | 0,1,0 | - | `inherit` | 순서 | - | 아니오 |
| 138 | `.sel` | 0,1,0 | font-size | `16px` | `.modal-takeover .sel` | components/upload/upload.css:595 | 0,2,0 | - | `14px` | 필연 | - | 아니오 |
| 138 | `.sel` | 0,1,0 | font-size | `16px` | `:is(.colab-ui, .design-preview) :is(.inp, .sel, .login-input, .pv-control select)` | shell/design-system.css:117 | 0,2,1 | - | `inherit` | DS쌍(특이도) | - | 아니오 |
| 138 | `.login-input` | 0,1,0 | font-size | `16px` | `.login-input` | auth/login.css:59 | 0,1,0 | - | `inherit` | 순서 | - | 아니오 |
| 138 | `.login-input` | 0,1,0 | font-size | `16px` | `:is(.colab-ui, .design-preview) :is(.inp, .sel, .login-input, .pv-control select)` | shell/design-system.css:117 | 0,2,1 | - | `inherit` | DS쌍(특이도) | - | 아니오 |
| 138 | `.pv-control select` | 0,1,1 | font-size | `16px` | `:is(.colab-ui, .design-preview) :is(.inp, .sel, .login-input, .pv-control select)` | shell/design-system.css:117 | 0,2,1 | - | `inherit` | DS쌍(순서) | - | 아니오 |
| 139 | `.theme-switcher` | 0,1,0 | min-height | `44px` | `.theme-switcher` | shell/design-system.css:115 | 0,1,0 | - | `36px` | DS쌍(순서) | - | 아니오 |
| 139 | `.theme-switcher` | 0,1,0 | max-width | `92px` | `.theme-switcher` | shell/design-system.css:115 | 0,1,0 | - | `104px` | DS쌍(순서) | - | 아니오 |
| 140 | `.gnb` | 0,1,0 | gap | `6px` | `:is(.colab-ui, .design-preview) .gnb` | shell/design-system.css:137 | 0,2,0 | - | `12px` | DS쌍(순서) | - | 아니오 |
| 140 | `.gnb` | 0,1,0 | gap | `6px` | `.colab-ui .gnb` | shell/design-system.css:143 | 0,2,0 | (max-width: 900px) | `8px` | DS쌍(순서) | - | 아니오 |
| 140 | `.gnb` | 0,1,0 | gap | `6px` | `.gnb` | shell/shell.css:113 | 0,1,0 | - | `10px` | 순서(셸 본문) | - | 아니오 |
| 140 | `.gnb` | 0,1,0 | gap | `6px` | `.gnb` | shell/shell.css:365 | 0,1,0 | (max-width: 1180px) | `8px` | 순서(셸 본문) | - | 아니오 |
| 140 | `.gnb` | 0,1,0 | gap | `6px` | `.gnb` | shell/shell.css:393 | 0,1,0 | (max-width: 560px) | `4px` | 순서(셸 본문) | - | 예 |
| 140 | `.gnb` | 0,1,0 | padding-inline | `12px` | `.colab-ui .gnb` | shell/design-system.css:143 | 0,2,0 | (max-width: 900px) | `10px 16px` | DS쌍(순서) | - | 아니오 |
| 140 | `.gnb` | 0,1,0 | padding-inline | `12px` | `.gnb` | shell/shell.css:114 | 0,1,0 | - | `0 20px` | 순서(셸 본문) | - | 아니오 |
| 140 | `.gnb` | 0,1,0 | padding-inline | `12px` | `.gnb` | shell/shell.css:365 | 0,1,0 | (max-width: 1180px) | `0 14px` | 순서(셸 본문) | - | 아니오 |
| 140 | `.gnb` | 0,1,0 | padding-inline | `12px` | `.gnb` | shell/shell.css:393 | 0,1,0 | (max-width: 560px) | `0 10px` | 순서(셸 본문) | - | 예 |
| 140 | `.gnb` | 0,1,0 | padding-inline | `12px` | `.gnb` | shell/shell.css:407 | 0,1,0 | (max-width: 640px) | `max(10px, env(safe-area-inset-left))` | 순서(셸 본문) | - | 예 |
| 140 | `.gnb` | 0,1,0 | padding-inline | `12px` | `.gnb` | shell/shell.css:408 | 0,1,0 | (max-width: 640px) | `max(10px, env(safe-area-inset-right))` | 순서(셸 본문) | - | 예 |
| 144 | `.pv-basic-grid` | 0,1,0 | grid-template-columns | `minmax(0, 1fr)` | `.pv-basic-grid` | components/preview/preview.css:66 | 0,1,0 | - | `repeat(auto-fill, minmax(220px, 1fr))` | 순서 | - | 아니오 |
| 146 | `.dr-pop` | 0,1,0 | position | `fixed` | `.dr-pop` | components/upload/upload.css:480 | 0,1,0 | - | `absolute` | 순서 | - | 아니오 |
| 146 | `.dr-pop` | 0,1,0 | inset | `auto 12px 12px` | `.dr-pop` | components/upload/upload.css:480 | 0,1,0 | - | `calc(100% + 6px)` | 순서 | - | 아니오 |
| 146 | `.dr-pop` | 0,1,0 | inset | `auto 12px 12px` | `.dr-pop` | components/upload/upload.css:480 | 0,1,0 | - | `0` | 순서 | - | 아니오 |
| 146 | `.dr-pop` | 0,1,0 | width | `auto` | `.dr-pop` | components/upload/upload.css:482 | 0,1,0 | - | `576px` | 순서 | - | 아니오 |
| 146 | `.dr-pop` | 0,1,0 | width | `auto` | `.dr-pop` | components/upload/upload.css:520 | 0,1,0 | (max-width:760px) | `308px` | 순서 | - | 아니오 |
| 146 | `.dr-pop` | 0,1,0 | max-width | `none` | `.dr-pop` | components/upload/upload.css:482 | 0,1,0 | - | `calc(100vw - 48px)` | 순서 | - | 아니오 |
| 147 | `.dr-cal-d` | 0,1,0 | height | `44px` | `.dr-cal-d` | components/upload/upload.css:498 | 0,1,0 | - | `32px` | 순서 | - | 아니오 |
| 150 | `.chip--warning` | 0,1,0 | background | `var(--color-warning-50)` | `.search-page .chip--warning` | components/search/search.css:86 | 0,2,0 | - | `var(--color-warning-50, #fff6ed)` | 필연 | - | 예 |
| 150 | `.chip--warning` | 0,1,0 | background | `var(--color-warning-50)` | `.lin .chip--warning` | components/lineage/lineage.css:236 | 0,2,0 | - | `var(--lin-over-bg)` | 필연 | - | 예 |
| 150 | `.chip--warning` | 0,1,0 | color | `var(--color-warning-600)` | `.search-page .chip--warning` | components/search/search.css:86 | 0,2,0 | - | `var(--color-warning-600, #a85400)` | 필연 | - | 예 |
| 150 | `.chip--warning` | 0,1,0 | color | `var(--color-warning-600)` | `.lin .chip--warning` | components/lineage/lineage.css:237 | 0,2,0 | - | `var(--lin-over-ink)` | 필연 | - | 예 |
| 151 | `.detail-page .dt-header h1` | 0,2,1 | font-size | `var(--text-h2)` | `.detail-page .dt-header h1` | components/detail/detail.css:11 | 0,2,1 | - | `31px` | 순서 | - | 예 |
| 151 | `.detail-page .dt-header h1` | 0,2,1 | line-height | `1.3` | `.detail-page .dt-header h1` | components/detail/detail.css:12 | 0,2,1 | - | `1.25` | 순서 | - | 예 |
| 152 | `.detail-page .dsec-h h2` | 0,2,1 | font-size | `20px` | `.detail-page .locked-hero h2` | components/detail/detail.css:70 | 0,2,1 | - | `var(--text-h2)` | 순서 | - | 아니오 |
| 152 | `.detail-page .dsec-h h2` | 0,2,1 | font-size | `20px` | `.detail-page .dsec-h h2` | components/lineage/lineageGraph.css:15 | 0,2,1 | - | `var(--text-h2)` | 순서 | - | 예 |
| 153 | `.chip:where(:not([class*="chip--"]))` | 0,1,0 | background | `var(--color-surface-alt)` | `.chip` | components/members/members.css:87 | 0,1,0 | - | `var(--color-surface-hover)` | 순서 | - | 아니오 |
| 153 | `.chip:where(:not([class*="chip--"]))` | 0,1,0 | background | `var(--color-surface-alt)` | `.chip` | components/upload/upload.css:256 | 0,1,0 | - | `#eef2f7` | 순서 | - | 아니오 |
| 156 | `.detail-page .ln .arw` | 0,3,0 | color | `var(--color-text-muted)` | `.detail-page .ln .arw` | components/lineage/lineageGraph.css:52 | 0,3,0 | - | `var(--color-primary-700)` | 순서 | - | 예 |
| 156 | `.detail-page .ln .arw` | 0,3,0 | color | `var(--color-text-muted)` | `.detail-page .lrow .ln-go .arw` | components/lineage/lineageGraph.css:86 | 0,4,0 | - | `var(--color-gray-400)` | 필연 | - | 아니오 |
| 156 | `.detail-page .ln .arw` | 0,3,0 | opacity | `1` | `.detail-page .ln .arw` | components/lineage/lineageGraph.css:52 | 0,3,0 | - | `.5` | 순서 | - | 예 |
| 156 | `.detail-page .ln-go .arw` | 0,3,0 | color | `var(--color-text-muted)` | `.detail-page .ln .arw` | components/lineage/lineageGraph.css:52 | 0,3,0 | - | `var(--color-primary-700)` | 순서 | - | 아니오 |
| 156 | `.detail-page .ln-go .arw` | 0,3,0 | color | `var(--color-text-muted)` | `.detail-page .lrow .ln-go .arw` | components/lineage/lineageGraph.css:86 | 0,4,0 | - | `var(--color-gray-400)` | 필연 | - | 예 |
| 156 | `.detail-page .ln-go .arw` | 0,3,0 | opacity | `1` | `.detail-page .ln .arw` | components/lineage/lineageGraph.css:52 | 0,3,0 | - | `.5` | 순서 | - | 아니오 |
| 157 | `.up-empty .up-card > .card-b` | 0,3,0 | padding | `0` | `.modal-takeover .up-steps .card-b` | components/upload/upload.css:593 | 0,3,0 | - | `20px 22px` | 순서 | - | 아니오 |
| 157 | `.up-empty .up-card > .card-b` | 0,3,0 | padding | `0` | `:is(.colab-ui, .design-preview) .modal-takeover .up-steps .card-b` | shell/design-system.css:133 | 0,4,0 | - | `var(--space-card)` | DS쌍(순서) | - | 아니오 |
| 162 | `.filecard .fmeta` | 0,2,0 | flex-basis | `100%` | `.filecard .fmeta` | components/upload/upload.css:128 | 0,2,0 | - | `1` | 순서 | - | 아니오 |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.pv-pick-f .sel` | components/preview/preview.css:501 | 0,2,0 | - | `0` | 순서 | - | 아니오 |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.itv .sel` | components/upload/upload.css:477 | 0,2,0 | - | `78px` | 순서 | - | 아니오 |
| 165 | `.reggate` | 0,1,0 | align-items | `start` | `.reggate` | components/upload/upload.css:186 | 0,1,0 | - | `center` | 순서 | - | 아니오 |
| 165 | `.reggate` | 0,1,0 | gap | `12px` | `.reggate` | components/upload/upload.css:186 | 0,1,0 | - | `16px` | 순서 | - | 아니오 |
| 166 | `.reggate .rg-a` | 0,2,0 | flex-basis | `100%` | `.up-empty .reggate .rg-a` | components/upload/upload.css:578 | 0,3,0 | - | `1` | 필연 | - | 아니오 |
| 171 | `.lin-find .modal-h .x` | 0,3,0 | background | `transparent` | `.modal-takeover .modal-h .x` | components/upload/upload.css:42 | 0,3,0 | - | `none` | 순서 | - | 아니오 |
| 171 | `.lin-find .modal-h .x` | 0,3,0 | font-size | `24px` | `.modal-takeover .modal-h .x` | components/upload/upload.css:42 | 0,3,0 | - | `20px` | 순서 | - | 아니오 |
| 171 | `.lin-fix .modal-h .x` | 0,3,0 | background | `transparent` | `.modal-takeover .modal-h .x` | components/upload/upload.css:42 | 0,3,0 | - | `none` | 순서 | - | 아니오 |
| 171 | `.lin-fix .modal-h .x` | 0,3,0 | font-size | `24px` | `.modal-takeover .modal-h .x` | components/upload/upload.css:42 | 0,3,0 | - | `20px` | 순서 | - | 아니오 |
| 171 | `.modal-takeover .modal-h .x` | 0,3,0 | background | `transparent` | `.modal-takeover .modal-h .x` | components/upload/upload.css:42 | 0,3,0 | - | `none` | 순서 | - | 예 |
| 171 | `.modal-takeover .modal-h .x` | 0,3,0 | font-size | `24px` | `.modal-takeover .modal-h .x` | components/upload/upload.css:42 | 0,3,0 | - | `20px` | 순서 | - | 예 |
| 172 | `.pj-toolbar` | 0,1,0 | padding | `var(--space-card)` | `.pj-toolbar` | components/project/project.css:61 | 0,1,0 | - | `10px 12px` | 순서 | - | 예 |
| 172 | `.pj-toolbar` | 0,1,0 | gap | `16px` | `.pj-toolbar` | components/project/project.css:60 | 0,1,0 | - | `12px` | 순서 | - | 예 |
| 172 | `.pj-toolbar` | 0,1,0 | border-color | `var(--color-border-strong)` | `.pj-toolbar` | components/project/project.css:62 | 0,1,0 | - | `1px solid var(--color-border)` | 순서 | - | 예 |
| 172 | `.pj-toolbar` | 0,1,0 | border-radius | `var(--radius-lg)` | `.pj-toolbar` | components/project/project.css:63 | 0,1,0 | - | `8px` | 순서 | - | 예 |
| 172 | `.pj-toolbar` | 0,1,0 | margin-bottom | `var(--space-section)` | `.pj-toolbar` | components/project/project.css:64 | 0,1,0 | - | `14px` | 순서 | - | 예 |
| 173 | `.pj-ctl` | 0,1,0 | display | `grid` | `.pj-ctl` | components/project/project.css:68 | 0,1,0 | - | `inline-flex` | 순서 | - | 예 |
| 173 | `.pj-ctl` | 0,1,0 | gap | `8px` | `.pj-ctl` | components/project/project.css:70 | 0,1,0 | - | `6px` | 순서 | - | 예 |
| 176 | `.pj-views button` | 0,1,1 | font | `inherit` | `.pj-views button.on` | components/project/project.css:83 | 0,2,1 | - | `600` | 필연 | - | 예 |
| 178 | `.pj-views button:last-child` | 0,2,1 | border-radius | `0 var(--radius-sm) var(--radius-sm) 0` | `:is(.colab-ui, .design-preview) .pj-views button:first-child` | shell/design-system.css:202 | 0,3,1 | - | `var(--radius-sm) 0 0 var(--radius-sm)` | DS쌍(순서) | :first-child | 아니오 |
| 179 | `.pj-new` | 0,1,0 | padding | `8px 14px` | `.pj-new` | components/project/project.css:536 | 0,1,0 | - | `0` | 순서 | - | 예 |
| 179 | `.pj-new` | 0,1,0 | border | `1px solid var(--color-primary-600)` | `.pj-new` | components/project/project.css:532 | 0,1,0 | - | `0` | 순서 | - | 예 |
| 179 | `.pj-new` | 0,1,0 | background | `var(--color-primary-600)` | `.pj-new` | components/project/project.css:533 | 0,1,0 | - | `none` | 순서 | - | 예 |
| 179 | `.pj-new` | 0,1,0 | color | `var(--color-on-primary)` | `.pj-new` | components/project/project.css:535 | 0,1,0 | - | `inherit` | 순서 | - | 예 |
| 179 | `.pj-new` | 0,1,0 | font-size | `var(--text-body-sm)` | `.pj-new` | components/project/project.css:534 | 0,1,0 | - | `inherit` | 순서 | - | 예 |
| 182 | `.pj-table` | 0,1,0 | min-width | `680px` | `.pj-table` | components/project/project.css:213 | 0,1,0 | - | `900px` | 순서 | - | 예 |
| 183 | `.table-scroll-hint` | 0,1,0 | display | `block` | `.table-scroll-hint` | shell/design-system.css:206 | 0,1,0 | - | `none` | DS쌍(순서) | - | 아니오 |
| 184 | `.gnb` | 0,1,0 | gap | `4px` | `:is(.colab-ui, .design-preview) .gnb` | shell/design-system.css:137 | 0,2,0 | - | `12px` | DS쌍(순서) | - | 아니오 |
| 184 | `.gnb` | 0,1,0 | gap | `4px` | `.colab-ui .gnb` | shell/design-system.css:143 | 0,2,0 | (max-width: 900px) | `8px` | DS쌍(순서) | - | 아니오 |
| 184 | `.gnb` | 0,1,0 | gap | `4px` | `.colab-ui .gnb` | shell/design-system.css:159 | 0,2,0 | (max-width: 640px) | `6px` | DS쌍(순서) | - | 예 |
| 184 | `.gnb` | 0,1,0 | gap | `4px` | `.gnb` | shell/shell.css:113 | 0,1,0 | - | `10px` | 순서(셸 본문) | - | 아니오 |
| 184 | `.gnb` | 0,1,0 | gap | `4px` | `.gnb` | shell/shell.css:365 | 0,1,0 | (max-width: 1180px) | `8px` | 순서(셸 본문) | - | 아니오 |
| 185 | `.theme-switcher` | 0,1,0 | max-width | `88px` | `.theme-switcher` | shell/design-system.css:115 | 0,1,0 | - | `104px` | DS쌍(순서) | - | 아니오 |
| 185 | `.theme-switcher` | 0,1,0 | max-width | `88px` | `.theme-switcher` | shell/design-system.css:158 | 0,1,0 | (max-width: 640px) | `92px` | DS쌍(순서) | - | 예 |
| 185 | `.theme-switcher` | 0,1,0 | padding-inline | `6px` | `.theme-switcher` | shell/design-system.css:115 | 0,1,0 | - | `6px 8px` | DS쌍(순서) | - | 아니오 |
| 186 | `.pj-toolbar` | 0,1,0 | display | `grid` | `.pj-toolbar` | components/project/project.css:57 | 0,1,0 | - | `flex` | 순서 | - | 아니오 |
| 186 | `.pj-toolbar` | 0,1,0 | gap | `16px 12px` | `.pj-toolbar` | components/project/project.css:60 | 0,1,0 | - | `12px` | 순서 | - | 아니오 |
| 186 | `.pj-toolbar` | 0,1,0 | gap | `16px 12px` | `:is(.colab-ui, .design-preview) .pj-toolbar` | shell/design-system.css:197 | 0,2,0 | - | `16px` | DS쌍(순서) | - | 아니오 |
| 188 | `.pj-ctl select` | 0,1,1 | font-size | `16px` | `:is(.colab-ui, .design-preview) .pj-ctl select` | shell/design-system.css:199 | 0,2,1 | - | `inherit` | DS쌍(순서) | - | 아니오 |
| 188 | `.pj-ctl select` | 0,1,1 | font-size | `16px` | `:is(.colab-ui, .design-preview) .pj-ctl select` | shell/design-system.css:199 | 0,2,1 | - | `var(--text-body-sm)` | DS쌍(순서) | - | 아니오 |
| 189 | `.pj-count` | 0,1,0 | margin-left | `0` | `.pj-count` | components/project/project.css:87 | 0,1,0 | - | `auto` | 순서 | - | 아니오 |
| 191 | `.search-page .vfilter` | 0,2,0 | height | `auto` | `.search-page .vfilter` | components/search/search.css:103 | 0,2,0 | - | `28px` | 순서 | - | 예 |
| 191 | `.search-page .empty-acts .quiet` | 0,3,0 | height | `auto` | `.search-page .notice--empty .empty-acts .quiet` | components/search/search.css:47 | 0,4,0 | - | `32px` | 필연 | - | 예 |
| 191 | `.search-page .empty-acts .strong` | 0,3,0 | height | `auto` | `.search-page .notice--empty .empty-acts .strong` | components/search/search.css:47 | 0,4,0 | - | `32px` | 필연 | - | 예 |

## 요소·전체 compound 호환 후보 중 상태 선택자 (값 다름 · 계산값 전수 대조가 못 보는 것)

상태(:hover·:focus·:focus-visible·:active·:disabled·[readonly]·[aria-*])는 캡처와 렌더 계산값 대조에 보이지 않는다. 같은 요소에 걸리는지는 선택자만으로 알 수 없어 요소 종류를 확인해 처리한다.

| DS# | S(인자) | spec 뒤 | 속성 | DS 값 | 경쟁 C | 위치 | spec C | C 값 | 종류 | 상태 |
|---:|---|---|---|---|---|---|---|---|---|---|
| 8 | `.catalog-page .hcnt` | 0,2,0 | padding | `2px 9px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 8 | `.catalog-page .hcnt` | 0,2,0 | padding | `2px 9px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 8 | `.catalog-page .hcnt` | 0,2,0 | padding | `2px 9px` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:66 | 0,2,2 | `0` | 필연 | :has(input[type='radio']) |
| 8 | `.catalog-page .hcnt` | 0,2,0 | background | `var(--color-gray-100)` | `.dr-nav button:hover` | components/upload/upload.css:489 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 8 | `.catalog-page .hcnt` | 0,2,0 | background | `var(--color-gray-100)` | `.dr-useg button:hover` | components/upload/upload.css:517 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 8 | `.catalog-page .hcnt` | 0,2,0 | background | `var(--color-gray-100)` | `.dh-menu button:hover` | components/approval/approval.css:13 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 8 | `.catalog-page .hcnt` | 0,2,0 | background | `var(--color-gray-100)` | `.account-table thead th:last-child` | auth/login.css:214 | 0,2,2 | `var(--color-surface)` | 필연 | :last-child |
| 8 | `.catalog-page .hcnt` | 0,2,0 | background | `var(--color-gray-100)` | `.mainnav a:hover` | shell/shell.css:181 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 8 | `.catalog-page .hcnt` | 0,2,0 | color | `var(--color-text-muted)` | `.mainnav a:hover` | shell/shell.css:182 | 0,2,1 | `var(--color-text)` | 필연 | :hover |
| 17 | `.tbl th .thf` | 0,2,1 | padding-inline | `16px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 순서 | :has(.inp) |
| 17 | `.tbl th .thf` | 0,2,1 | padding-inline | `16px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 순서 | :has(.vt-del) |
| 17 | `.tbl th .thf` | 0,2,1 | padding-inline | `16px` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:66 | 0,2,2 | `0` | 필연 | :has(input[type='radio']) |
| 18 | `.tbl td` | 0,1,1 | padding | `10px 12px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 18 | `.tbl td` | 0,1,1 | padding | `10px 12px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 19 | `.tbl .fname` | 0,2,0 | white-space | `normal` | `.pj-table th:not(:first-child)` | components/project/project.css:223 | 0,2,1 | `nowrap` | 필연 | :not(:first-child) |
| 19 | `.tbl .fname` | 0,2,0 | white-space | `normal` | `.pj-table td:not(:first-child)` | components/project/project.css:223 | 0,2,1 | `nowrap` | 필연 | :not(:first-child) |
| 22 | `.tbl td:nth-child(4)` | 0,2,1 | white-space | `normal` | `.pj-table td:not(:first-child)` | components/project/project.css:223 | 0,2,1 | `nowrap` | 순서 | :not(:first-child) |
| 31 | `.lab-page .search-hero` | 0,2,0 | padding-top | `24px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 31 | `.lab-page .search-hero` | 0,2,0 | padding-top | `24px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 31 | `.lab-page .search-hero` | 0,2,0 | padding-top | `24px` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:66 | 0,2,2 | `0` | 필연 | :has(input[type='radio']) |
| 31 | `.lab-page .search-hero` | 0,2,0 | padding-bottom | `40px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 31 | `.lab-page .search-hero` | 0,2,0 | padding-bottom | `40px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 31 | `.lab-page .search-hero` | 0,2,0 | padding-bottom | `40px` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:66 | 0,2,2 | `0` | 필연 | :has(input[type='radio']) |
| 73 | `.pj-seg button.on` | 0,2,1 | background | `var(--color-surface)` | `.colmenu button.cm-i:hover` | components/catalog/catalog.css:71 | 0,3,1 | `var(--color-gray-100)` | 필연 | :hover |
| 73 | `.pj-seg button.on` | 0,2,1 | background | `var(--color-surface)` | `.dr-nav button:hover` | components/upload/upload.css:489 | 0,2,1 | `var(--color-surface-hover)` | 순서 | :hover |
| 73 | `.pj-seg button.on` | 0,2,1 | background | `var(--color-surface)` | `.dr-useg button:hover` | components/upload/upload.css:517 | 0,2,1 | `var(--color-surface-hover)` | 순서 | :hover |
| 73 | `.pj-seg button.on` | 0,2,1 | background | `var(--color-surface)` | `.dh-menu button:hover` | components/approval/approval.css:13 | 0,2,1 | `var(--color-surface-hover)` | 순서 | :hover |
| 73 | `.pj-seg button.on` | 0,2,1 | outline | `1px solid var(--color-border-strong)` | `.modal-takeover button:focus-visible` | components/upload/upload.css:596 | 0,2,1 | `2px solid var(--color-primary-600)` | 순서 | :focus-visible |
| 83 | `.btn-primary:active` | 0,2,0 | background | `var(--color-primary-700)` | `.dr-nav button:hover` | components/upload/upload.css:489 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 83 | `.btn-primary:active` | 0,2,0 | background | `var(--color-primary-700)` | `.dr-useg button:hover` | components/upload/upload.css:517 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 83 | `.btn-primary:active` | 0,2,0 | background | `var(--color-primary-700)` | `.dh-menu button:hover` | components/approval/approval.css:13 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 83 | `.btn-primary:active` | 0,2,0 | background | `var(--color-primary-700)` | `.account-table thead th:last-child` | auth/login.css:214 | 0,2,2 | `var(--color-surface)` | 필연 | :last-child |
| 83 | `.btn-primary:active` | 0,2,0 | background | `var(--color-primary-700)` | `.mainnav a:hover` | shell/shell.css:181 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 83 | `.search-hero button:active` | 0,2,1 | background | `var(--color-primary-700)` | `.colmenu button.cm-i:hover` | components/catalog/catalog.css:71 | 0,3,1 | `var(--color-gray-100)` | 필연 | :hover |
| 83 | `.search-hero button:active` | 0,2,1 | background | `var(--color-primary-700)` | `.dr-nav button:hover` | components/upload/upload.css:489 | 0,2,1 | `var(--color-surface-hover)` | 순서 | :hover |
| 83 | `.search-hero button:active` | 0,2,1 | background | `var(--color-primary-700)` | `.dr-useg button:hover` | components/upload/upload.css:517 | 0,2,1 | `var(--color-surface-hover)` | 순서 | :hover |
| 83 | `.search-hero button:active` | 0,2,1 | background | `var(--color-primary-700)` | `.dh-menu button:hover` | components/approval/approval.css:13 | 0,2,1 | `var(--color-surface-hover)` | 순서 | :hover |
| 86 | `.lab-page .search-hero` | 0,2,0 | padding-top | `16px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 86 | `.lab-page .search-hero` | 0,2,0 | padding-top | `16px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 86 | `.lab-page .search-hero` | 0,2,0 | padding-top | `16px` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:66 | 0,2,2 | `0` | 필연 | :has(input[type='radio']) |
| 86 | `.lab-page .search-hero` | 0,2,0 | padding-bottom | `32px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 86 | `.lab-page .search-hero` | 0,2,0 | padding-bottom | `32px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 86 | `.lab-page .search-hero` | 0,2,0 | padding-bottom | `32px` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:66 | 0,2,2 | `0` | 필연 | :has(input[type='radio']) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.pj-table th:first-child` | components/project/project.css:216 | 0,2,1 | `36%` | 필연 | :first-child |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.pj-table th:nth-child(2)` | components/project/project.css:217 | 0,2,1 | `11%` | 필연 | :nth-child(2) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.pj-table th:nth-child(3)` | components/project/project.css:218 | 0,2,1 | `12%` | 필연 | :nth-child(3) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.pj-table th:nth-child(4)` | components/project/project.css:219 | 0,2,1 | `180px` | 필연 | :nth-child(4) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.pj-table th:nth-child(5)` | components/project/project.css:220 | 0,2,1 | `11%` | 필연 | :nth-child(5) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.pj-table th:nth-child(6)` | components/project/project.css:221 | 0,2,1 | `10%` | 필연 | :nth-child(6) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:90 | 0,2,2 | `1%` | 필연 | :has(input[type='radio']) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.vartable th:last-child` | components/common/variableTable.css:90 | 0,2,1 | `1%` | 필연 | :last-child |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(2)` | auth/login.css:161 | 0,2,2 | `64px` | 필연 | :nth-child(2) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(3)` | auth/login.css:162 | 0,2,2 | `92px` | 필연 | :nth-child(3) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(4)` | auth/login.css:163 | 0,2,2 | `96px` | 필연 | :nth-child(4) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(5)` | auth/login.css:164 | 0,2,2 | `68px` | 필연 | :nth-child(5) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(6)` | auth/login.css:165 | 0,2,2 | `104px` | 필연 | :nth-child(6) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(7)` | auth/login.css:166 | 0,2,2 | `104px` | 필연 | :nth-child(7) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(8)` | auth/login.css:170 | 0,2,2 | `576px` | 필연 | :nth-child(8) |
| 101 | `.tbl .colmenu` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(8)` | auth/login.css:236 | 0,2,2 | `195px` | 필연 | :nth-child(8) |
| 101 | `.tbl .colmenu` | 0,2,0 | overflow-y | `auto` | `.account-table td:not(.account-row-actions-cell)` | auth/login.css:175 | 0,2,1 | `hidden` | 필연 | :not(.account-row-actions-cell) |
| 101 | `.tbl .colmenu` | 0,2,0 | padding | `12px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 101 | `.tbl .colmenu` | 0,2,0 | padding | `12px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 101 | `.tbl .colmenu` | 0,2,0 | padding | `12px` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:66 | 0,2,2 | `0` | 필연 | :has(input[type='radio']) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.pj-table th:first-child` | components/project/project.css:216 | 0,2,1 | `36%` | 필연 | :first-child |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.pj-table th:nth-child(2)` | components/project/project.css:217 | 0,2,1 | `11%` | 필연 | :nth-child(2) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.pj-table th:nth-child(3)` | components/project/project.css:218 | 0,2,1 | `12%` | 필연 | :nth-child(3) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.pj-table th:nth-child(4)` | components/project/project.css:219 | 0,2,1 | `180px` | 필연 | :nth-child(4) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.pj-table th:nth-child(5)` | components/project/project.css:220 | 0,2,1 | `11%` | 필연 | :nth-child(5) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.pj-table th:nth-child(6)` | components/project/project.css:221 | 0,2,1 | `10%` | 필연 | :nth-child(6) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:90 | 0,2,2 | `1%` | 필연 | :has(input[type='radio']) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.vartable th:last-child` | components/common/variableTable.css:90 | 0,2,1 | `1%` | 필연 | :last-child |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.account-table thead th:nth-child(2)` | auth/login.css:161 | 0,2,2 | `64px` | 필연 | :nth-child(2) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.account-table thead th:nth-child(3)` | auth/login.css:162 | 0,2,2 | `92px` | 필연 | :nth-child(3) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.account-table thead th:nth-child(4)` | auth/login.css:163 | 0,2,2 | `96px` | 필연 | :nth-child(4) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.account-table thead th:nth-child(5)` | auth/login.css:164 | 0,2,2 | `68px` | 필연 | :nth-child(5) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.account-table thead th:nth-child(6)` | auth/login.css:165 | 0,2,2 | `104px` | 필연 | :nth-child(6) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.account-table thead th:nth-child(7)` | auth/login.css:166 | 0,2,2 | `104px` | 필연 | :nth-child(7) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.account-table thead th:nth-child(8)` | auth/login.css:170 | 0,2,2 | `576px` | 필연 | :nth-child(8) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.account-table thead th:nth-child(2)` | auth/login.css:226 | 0,2,2 | `100px` | 필연 | :nth-child(2) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.account-table thead th:nth-child(4)` | auth/login.css:227 | 0,2,2 | `148px` | 필연 | :nth-child(4) |
| 102 | `.colmenu .cm-box` | 0,2,0 | width | `16px` | `.account-table thead th:nth-child(8)` | auth/login.css:236 | 0,2,2 | `195px` | 필연 | :nth-child(8) |
| 102 | `.colmenu .cm-box` | 0,2,0 | color | `var(--color-on-primary)` | `.mainnav a:hover` | shell/shell.css:182 | 0,2,1 | `var(--color-text)` | 필연 | :hover |
| 105 | `.inp` | 0,1,0 | padding | `10px 12px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 105 | `.inp` | 0,1,0 | padding | `10px 12px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 105 | `.inp` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.vartable th:last-child` | components/common/variableTable.css:39 | 0,2,1 | `none` | 필연 | :last-child |
| 105 | `.inp` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.vartable td:last-child` | components/common/variableTable.css:39 | 0,2,1 | `none` | 필연 | :last-child |
| 105 | `.inp` | 0,1,0 | background | `var(--color-surface)` | `.dr-nav button:hover` | components/upload/upload.css:489 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 105 | `.inp` | 0,1,0 | background | `var(--color-surface)` | `.dr-useg button:hover` | components/upload/upload.css:517 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 105 | `.inp` | 0,1,0 | background | `var(--color-surface)` | `.dh-menu button:hover` | components/approval/approval.css:13 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 105 | `.sel` | 0,1,0 | padding | `10px 12px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 105 | `.sel` | 0,1,0 | padding | `10px 12px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 105 | `.sel` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.vartable th:last-child` | components/common/variableTable.css:39 | 0,2,1 | `none` | 필연 | :last-child |
| 105 | `.sel` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.vartable td:last-child` | components/common/variableTable.css:39 | 0,2,1 | `none` | 필연 | :last-child |
| 105 | `.sel` | 0,1,0 | background | `var(--color-surface)` | `.dr-nav button:hover` | components/upload/upload.css:489 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 105 | `.sel` | 0,1,0 | background | `var(--color-surface)` | `.dr-useg button:hover` | components/upload/upload.css:517 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 105 | `.sel` | 0,1,0 | background | `var(--color-surface)` | `.dh-menu button:hover` | components/approval/approval.css:13 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 105 | `.login-input` | 0,1,0 | padding | `10px 12px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 105 | `.login-input` | 0,1,0 | padding | `10px 12px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 105 | `.login-input` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.vartable th:last-child` | components/common/variableTable.css:39 | 0,2,1 | `none` | 필연 | :last-child |
| 105 | `.login-input` | 0,1,0 | border | `1px solid var(--color-border-control)` | `.vartable td:last-child` | components/common/variableTable.css:39 | 0,2,1 | `none` | 필연 | :last-child |
| 105 | `.login-input` | 0,1,0 | background | `var(--color-surface)` | `.dr-nav button:hover` | components/upload/upload.css:489 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 105 | `.login-input` | 0,1,0 | background | `var(--color-surface)` | `.dr-useg button:hover` | components/upload/upload.css:517 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 105 | `.login-input` | 0,1,0 | background | `var(--color-surface)` | `.dh-menu button:hover` | components/approval/approval.css:13 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 114 | `.search-page .hit` | 0,2,0 | padding | `var(--space-card)` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 114 | `.search-page .hit` | 0,2,0 | padding | `var(--space-card)` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 114 | `.search-page .hit` | 0,2,0 | padding | `var(--space-card)` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:66 | 0,2,2 | `0` | 필연 | :has(input[type='radio']) |
| 129 | `button:focus-visible` | 0,1,1 | outline-offset | `3px` | `.modal-takeover button:focus-visible` | components/upload/upload.css:596 | 0,2,1 | `2px` | 필연 | :focus-visible |
| 141 | `.gnb .labswitch` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 141 | `.gnb .labswitch` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 141 | `.gnb .labswitch` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:66 | 0,2,2 | `0` | 필연 | :has(input[type='radio']) |
| 141 | `.gnb .gnb-settings` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 141 | `.gnb .gnb-settings` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 141 | `.gnb .gnb-settings` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:66 | 0,2,2 | `0` | 필연 | :has(input[type='radio']) |
| 141 | `.gnb .gnb-upload` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 141 | `.gnb .gnb-upload` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 141 | `.gnb .gnb-upload` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:66 | 0,2,2 | `0` | 필연 | :has(input[type='radio']) |
| 141 | `.gnb .gnb-more` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 141 | `.gnb .gnb-more` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 141 | `.gnb .gnb-more` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:66 | 0,2,2 | `0` | 필연 | :has(input[type='radio']) |
| 141 | `.gnb .avatar` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(.inp)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.inp) |
| 141 | `.gnb .avatar` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(.vt-del)` | components/common/variableTable.css:66 | 0,2,1 | `0` | 필연 | :has(.vt-del) |
| 141 | `.gnb .avatar` | 0,2,0 | padding-inline | `6px` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:66 | 0,2,2 | `0` | 필연 | :has(input[type='radio']) |
| 163 | `.filecard .fkind` | 0,2,0 | flex | `1` | `.lin-findbar > label:first-child` | components/lineage/lineage.css:309 | 0,2,1 | `2` | 필연 | :first-child |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.pj-table th:first-child` | components/project/project.css:216 | 0,2,1 | `36%` | 필연 | :first-child |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.pj-table th:nth-child(2)` | components/project/project.css:217 | 0,2,1 | `11%` | 필연 | :nth-child(2) |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.pj-table th:nth-child(3)` | components/project/project.css:218 | 0,2,1 | `12%` | 필연 | :nth-child(3) |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.pj-table th:nth-child(4)` | components/project/project.css:219 | 0,2,1 | `180px` | 필연 | :nth-child(4) |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.pj-table th:nth-child(5)` | components/project/project.css:220 | 0,2,1 | `11%` | 필연 | :nth-child(5) |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.pj-table th:nth-child(6)` | components/project/project.css:221 | 0,2,1 | `10%` | 필연 | :nth-child(6) |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.vartable td:has(input[type='radio'])` | components/common/variableTable.css:90 | 0,2,2 | `1%` | 필연 | :has(input[type='radio']) |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.vartable th:last-child` | components/common/variableTable.css:90 | 0,2,1 | `1%` | 필연 | :last-child |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(2)` | auth/login.css:161 | 0,2,2 | `64px` | 필연 | :nth-child(2) |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(3)` | auth/login.css:162 | 0,2,2 | `92px` | 필연 | :nth-child(3) |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(4)` | auth/login.css:163 | 0,2,2 | `96px` | 필연 | :nth-child(4) |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(5)` | auth/login.css:164 | 0,2,2 | `68px` | 필연 | :nth-child(5) |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(6)` | auth/login.css:165 | 0,2,2 | `104px` | 필연 | :nth-child(6) |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(7)` | auth/login.css:166 | 0,2,2 | `104px` | 필연 | :nth-child(7) |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(8)` | auth/login.css:170 | 0,2,2 | `576px` | 필연 | :nth-child(8) |
| 164 | `.filecard .sel` | 0,2,0 | width | `auto` | `.account-table thead th:nth-child(8)` | auth/login.css:236 | 0,2,2 | `195px` | 필연 | :nth-child(8) |
| 169 | `.lin-picker li > button` | 0,1,2 | background | `transparent` | `.dr-nav button:hover` | components/upload/upload.css:489 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 169 | `.lin-picker li > button` | 0,1,2 | background | `transparent` | `.dr-useg button:hover` | components/upload/upload.css:517 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 169 | `.lin-picker li > button` | 0,1,2 | background | `transparent` | `.dh-menu button:hover` | components/approval/approval.css:13 | 0,2,1 | `var(--color-surface-hover)` | 필연 | :hover |
| 170 | `.lin-picker li > button[aria-pressed="true"]` | 0,2,2 | background | `var(--color-surface-hover)` | `.colmenu button.cm-i:hover` | components/catalog/catalog.css:71 | 0,3,1 | `var(--color-gray-100)` | 필연 | :hover |
| 180 | `.pd-linkurl:visited` | 0,2,0 | color | `var(--color-primary-700)` | `.mainnav a:hover` | shell/shell.css:182 | 0,2,1 | `var(--color-text)` | 필연 | :hover |
| 190 | `.search-page .notice a:where(:not(.strong, .quiet))` | 0,2,1 | color | `var(--color-primary-700)` | `.mainnav a:hover` | shell/shell.css:182 | 0,2,1 | `var(--color-text)` | 순서(셸 본문) | :hover |
| 190 | `.notfound a:where(:not(.strong, .quiet))` | 0,1,1 | color | `var(--color-primary-700)` | `.mainnav a:hover` | shell/shell.css:182 | 0,2,1 | `var(--color-text)` | 필연 | :hover |
| 190 | `.notfound a:where(:not(.strong, .quiet)):visited` | 0,2,1 | color | `var(--color-primary-700)` | `.mainnav a:hover` | shell/shell.css:182 | 0,2,1 | `var(--color-text)` | 순서(셸 본문) | :hover |

## 규칙별 표

`DS 짐` = 오늘 그 선언이 지는 경쟁(값 다름) · `되살` = 되살아남 후보 수. 경쟁 전수는 `cascade-map.json`.

| # | 행 | 미디어 | 선택자 인자 | spec 오늘→뒤 | 선언 | DS 짐 | 되살 | 조사 owner | 조사 target |
|---:|---:|---|---|---|---:|---|---|---|---|
| 1 | 2 | - | `:is(.colab-ui, .design-preview)` | 0,1,0→0,1,0 | 3 | - | - | shell | shell.css (base) |
| 2 | 3 | - | `button` | 0,1,1→0,0,1 | 1 | - | - | shell | shell.css (base) |
| 2 | 3 | - | `a` | 0,1,1→0,0,1 | 1 | - | - | shell | shell.css (base) |
| 2 | 3 | - | `input` | 0,1,1→0,0,1 | 1 | - | - | shell | shell.css (base) |
| 2 | 3 | - | `select` | 0,1,1→0,0,1 | 1 | - | - | shell | shell.css (base) |
| 2 | 3 | - | `textarea` | 0,1,1→0,0,1 | 1 | - | - | shell | shell.css (base) |
| 3 | 4 | - | `input::placeholder` | 0,1,2→0,0,2 | 2 | - | - | primitive:field | primitives.css .field |
| 3 | 4 | - | `textarea::placeholder` | 0,1,2→0,0,2 | 2 | - | - | primitive:field | primitives.css .field |
| 4 | 5 | - | `.catalog-page` | 0,2,0→0,1,0 | 5 | - | padding(6) padding-bottom(4) | pattern:page | patterns.css .page |
| 4 | 5 | - | `.lab-page` | 0,2,0→0,1,0 | 5 | - | max-width(1) margin-inline(1) padding(2) padding-bottom(2) | pattern:page | patterns.css .page |
| 4 | 5 | - | `.project-page` | 0,2,0→0,1,0 | 5 | - | max-width(1) margin-inline(1) padding(1) padding-bottom(1) | pattern:page | patterns.css .page |
| 5 | 6 | - | `.page-head h1` | 0,2,1→0,1,1 | 4 | - | font-size(2) letter-spacing(2) | pattern:page-head | patterns.css .page-head h1 |
| 5 | 6 | - | `.search-hero h1` | 0,2,1→0,1,1 | 4 | font-size(1) | font-size(1) letter-spacing(1) | pattern:page-head | patterns.css .page-head h1 |
| 6 | 7 | - | `.catalog-page .page-head` | 0,3,0→0,2,0 | 2 | - | gap(1) margin-bottom(1) | screen | catalog.css |
| 7 | 8 | - | `.catalog-page .desc` | 0,3,0→0,2,0 | 3 | - | font-size(1) | screen | catalog.css |
| 8 | 9 | - | `.catalog-page .hcnt` | 0,3,0→0,2,0 | 4 | - | - | screen | catalog.css |
| 9 | 10 | - | `.card` | 0,2,0→0,1,0 | 4 | border-color(1) border-radius(1) | border-color(3) border-radius(2) | mixed | primitives.css .card + dashboard.css + project.css |
| 9 | 10 | - | `.dash-card` | 0,2,0→0,1,0 | 4 | - | border-color(1) border-radius(1) | mixed | primitives.css .card + dashboard.css + project.css |
| 9 | 10 | - | `.dash-tile` | 0,2,0→0,1,0 | 4 | - | border-color(1) border-radius(1) | mixed | primitives.css .card + dashboard.css + project.css |
| 9 | 10 | - | `.pj-modal` | 0,2,0→0,1,0 | 4 | - | border-color(1) border-radius(1) | mixed | primitives.css .card + dashboard.css + project.css |
| 10 | 11 | - | `.catalog-filters` | 0,2,0→0,1,0 | 2 | gap(1) | padding(2) gap(2) | screen | catalog.css |
| 11 | 12 | - | `.catalog-filters .axis-pick` | 0,3,0→0,2,0 | 1 | - | gap(1) | screen | catalog.css |
| 12 | 13 | - | `.axis-k` | 0,2,0→0,1,0 | 2 | - | font-size(1) | screen | catalog.css |
| 13 | 14 | - | `.catalog-filters select` | 0,2,1→0,1,1 | 3 | - | height(2) padding-inline(1) border-color(1) | screen | catalog.css |
| 14 | 15 | - | `.tblwrap` | 0,2,0→0,1,0 | 1 | - | max-height(2) | primitive:table | primitives.css .table-scroll |
| 15 | 16 | - | `.tbl` | 0,2,0→0,1,0 | 2 | - | - | primitive:table | primitives.css .table |
| 16 | 17 | - | `.tbl th` | 0,2,1→0,1,1 | 3 | - | color(1) font-weight(1) letter-spacing(1) | primitive:table | primitives.css .table |
| 17 | 18 | - | `.tbl th .thf` | 0,3,1→0,2,1 | 2 | - | padding-inline(1) | screen | catalog.css |
| 18 | 19 | - | `.tbl td` | 0,2,1→0,1,1 | 1 | - | padding(3) | primitive:table | primitives.css .table |
| 19 | 20 | - | `.tbl .fname` | 0,3,0→0,2,0 | 5 | - | font-size(1) letter-spacing(1) | screen | catalog.css |
| 20 | 21 | - | `.fname .catalog-open` | 0,3,0→0,2,0 | 4 | - | - | screen | catalog.css |
| 21 | 22 | - | `.fname .chip` | 0,3,0→0,2,0 | 1 | - | - | screen | catalog.css |
| 22 | 23 | - | `.tbl td:nth-child(4)` | 0,3,1→0,2,1 | 3 | - | - | screen | catalog.css |
| 23 | 24 | - | `.tbl .catalog-open` | 0,3,0→0,2,0 | 1 | - | - | screen | catalog.css |
| 24 | 25 | - | `.tbl .rowact .ra` | 0,4,0→0,3,0 | 1 | - | opacity(1) | screen | catalog.css |
| 25 | 26 | - | `.tbl .rowact .rab` | 0,4,0→0,3,0 | 2 | width(1) height(1) | width(1) height(1) | screen | catalog.css |
| 26 | 27 | - | `.fchips` | 0,2,0→0,1,0 | 2 | - | padding(1) gap(1) | screen | catalog.css |
| 27 | 28 | - | `.fchips .fc` | 0,3,0→0,2,0 | 1 | - | height(1) | screen | catalog.css |
| 28 | 29 | - | `.fchips .fc button` | 0,3,1→0,2,1 | 2 | - | - | screen | catalog.css |
| 29 | 30 | - | `.colmenu button` | 0,2,1→0,1,1 | 1 | min-height(1) | - | screen | catalog.css |
| 30 | 31 | - | `.crosslink` | 0,2,0→0,1,0 | 2 | - | padding(1) | screen | catalog.css + search.css |
| 31 | 32 | - | `.lab-page .search-hero` | 0,3,0→0,2,0 | 3 | padding-top(1) padding-bottom(1) | max-width(1) | screen | search.css |
| 32 | 33 | - | `.search-hero h1` | 0,2,1→0,1,1 | 1 | - | margin-bottom(1) | screen | search.css |
| 33 | 34 | - | `.search-hero input` | 0,2,1→0,1,1 | 3 | - | border-color(1) padding(1) | screen | search.css |
| 34 | 35 | - | `.search-hero button` | 0,2,1→0,1,1 | 1 | - | - | screen | search.css |
| 35 | 36 | - | `.search-hero .hero-note` | 0,3,0→0,2,0 | 2 | - | margin-top(1) font-size(1) | screen | search.css |
| 36 | 37 | - | `.dash-columns` | 0,2,0→0,1,0 | 3 | grid-template-columns(1) | margin-top(1) gap(1) grid-template-columns(1) | screen | dashboard.css |
| 37 | 38 | - | `.dash-col` | 0,2,0→0,1,0 | 1 | - | gap(1) | screen | dashboard.css |
| 38 | 39 | - | `.dash-section-label` | 0,2,0→0,1,0 | 4 | - | font-size(1) font-weight(1) | screen | dashboard.css |
| 39 | 40 | - | `.dash-card` | 0,2,0→0,1,0 | 1 | - | padding(2) | screen | dashboard.css |
| 40 | 41 | - | `.dash-card-head` | 0,2,0→0,1,0 | 3 | - | align-items(1) gap(1) margin-bottom(1) | screen | dashboard.css |
| 41 | 42 | - | `.dash-card-head h2` | 0,2,1→0,1,1 | 3 | - | font-size(1) | screen | dashboard.css |
| 42 | 43 | - | `.dash-bar` | 0,2,0→0,1,0 | 5 | min-height(1) grid-template-columns(1) | font-size(1) padding-block(1) grid-template-columns(1) | screen | dashboard.css |
| 43 | 44 | - | `.dash-bar-track` | 0,2,0→0,1,0 | 1 | - | height(1) | screen | dashboard.css |
| 44 | 45 | - | `.dash-bar-fill` | 0,2,0→0,1,0 | 1 | - | background(1) | screen | dashboard.css |
| 45 | 46 | - | `.dash-note` | 0,2,0→0,1,0 | 1 | - | - | screen | dashboard.css |
| 45 | 46 | - | `.dash-calc` | 0,2,0→0,1,0 | 1 | - | - | screen | dashboard.css |
| 45 | 46 | - | `.dash-zero` | 0,2,0→0,1,0 | 1 | - | - | screen | dashboard.css |
| 45 | 46 | - | `.dash-lead` | 0,2,0→0,1,0 | 1 | - | - | screen | dashboard.css |
| 46 | 47 | - | `.dash-calc` | 0,2,0→0,1,0 | 1 | - | margin(1) | screen | dashboard.css |
| 47 | 48 | - | `.dash-tiles` | 0,2,0→0,1,0 | 1 | - | gap(1) | screen | dashboard.css |
| 48 | 49 | - | `.dash-tile` | 0,2,0→0,1,0 | 1 | - | padding(1) | screen | dashboard.css |
| 49 | 50 | - | `.dash-tile strong` | 0,2,1→0,1,1 | 5 | - | font-size(1) | screen | dashboard.css |
| 50 | 51 | - | `.dash-quiet` | 0,2,0→0,1,0 | 2 | - | - | screen | dashboard.css |
| 51 | 52 | - | `.dash-open-catalog` | 0,2,0→0,1,0 | 4 | - | min-height(1) font-size(1) margin-top(1) padding-inline(1) | screen | dashboard.css |
| 52 | 53 | - | `.dash-recent button` | 0,2,1→0,1,1 | 3 | - | font-size(1) padding-block(2) | screen | dashboard.css |
| 53 | 54 | - | `.todo-grp h3` | 0,2,1→0,1,1 | 2 | - | font-size(1) margin-bottom(1) | screen | dashboard.css |
| 54 | 55 | - | `.titem` | 0,2,0→0,1,0 | 4 | border-bottom(1) | font-size(1) padding(1) gap(1) | screen | dashboard.css |
| 55 | 56 | - | `.titem:last-child` | 0,3,0→0,2,0 | 1 | - | - | screen | dashboard.css |
| 56 | 57 | - | `.titem button` | 0,2,1→0,1,1 | 4 | - | padding-inline(1) | screen | dashboard.css |
| 57 | 58 | - | `.todo-more` | 0,2,0→0,1,0 | 2 | - | - | screen | dashboard.css |
| 57 | 58 | - | `.todo-all` | 0,2,0→0,1,0 | 2 | - | - | screen | dashboard.css |
| 58 | 59 | - | `.dash-steps` | 0,2,0→0,1,0 | 2 | gap(1) | gap(1) margin-top(2) | screen | dashboard.css |
| 59 | 60 | - | `.dash-step-no` | 0,2,0→0,1,0 | 3 | - | width(1) height(1) line-height(1) | screen | dashboard.css |
| 60 | 61 | - | `.pj-modal-back` | 0,2,0→0,1,0 | 2 | padding(1) | padding(1) background(1) | screen | project.css |
| 61 | 62 | - | `.pj-modal` | 0,2,0→0,1,0 | 2 | max-height(1) | width(1) max-height(2) | screen | project.css |
| 62 | 63 | - | `.pj-modal-h` | 0,2,0→0,1,0 | 1 | padding(1) | padding(1) | screen | project.css |
| 63 | 64 | - | `.pj-modal-h h3` | 0,2,1→0,1,1 | 3 | - | font-size(1) | screen | project.css |
| 64 | 65 | - | `.pj-x` | 0,2,0→0,1,0 | 5 | - | font-size(1) | screen | project.css |
| 65 | 66 | - | `.pj-modal-b` | 0,2,0→0,1,0 | 1 | - | padding(1) | screen | project.css |
| 66 | 67 | - | `.pj-modal-f` | 0,2,0→0,1,0 | 1 | - | padding(1) | screen | project.css |
| 67 | 68 | - | `.pj-row` | 0,2,0→0,1,0 | 1 | margin-bottom(1) | margin-bottom(1) | screen | project.css |
| 68 | 69 | - | `.pj-row label` | 0,2,1→0,1,1 | 4 | - | font-size(1) margin-bottom(1) color(1) | screen | project.css |
| 69 | 70 | - | `.pj-inp` | 0,2,0→0,1,0 | 8 | - | padding(1) font-size(3) line-height(1) border(1) border-radius(1) | screen | project.css |
| 69 | 70 | - | `.pj-tarea` | 0,2,0→0,1,0 | 8 | min-height(1) | min-height(1) padding(1) font-size(3) line-height(1) border(1) border-radius(1) | screen | project.css |
| 70 | 71 | - | `.pj-tarea` | 0,2,0→0,1,0 | 1 | - | min-height(2) | screen | project.css |
| 71 | 72 | - | `.pj-seg` | 0,2,0→0,1,0 | 5 | - | border-color(1) border-radius(1) | screen | project.css |
| 72 | 73 | - | `.pj-seg button` | 0,2,1→0,1,1 | 4 | min-height(1) | font-size(2) padding-inline(1) | screen | project.css |
| 73 | 74 | - | `.pj-seg button.on` | 0,3,1→0,2,1 | 3 | - | background(3) color(2) | screen | project.css |
| 74 | 75 | - | `.pj-defnote` | 0,2,0→0,1,0 | 3 | - | font-size(1) line-height(1) | screen | project.css |
| 74 | 75 | - | `.pj-hint` | 0,2,0→0,1,0 | 3 | - | font-size(1) | screen | project.css |
| 75 | 76 | - | `.pj-fgroup` | 0,2,0→0,1,0 | 4 | padding(1) | padding(1) margin-top(1) border-color(1) | screen | project.css |
| 76 | 77 | - | `.pj-fgroup .pj-row` | 0,3,0→0,2,0 | 1 | - | - | screen | project.css |
| 77 | 78 | - | `.pj-fgroup-h` | 0,2,0→0,1,0 | 1 | - | margin-bottom(1) | screen | project.css |
| 78 | 79 | - | `.chip--lineage` | 0,2,0→0,1,0 | 2 | - | - | primitive:chip | primitives.css .chip |
| 79 | 80 | - | `.pj-err` | 0,2,0→0,1,0 | 2 | - | color(1) | screen | project.css |
| 80 | 81 | - | `.btn` | 0,2,0→0,1,0 | 4 | padding(1) | padding(2) font-size(1) border-radius(1) | primitive:btn | primitives.css .btn |
| 81 | 82 | - | `.btn-primary` | 0,2,0→0,1,0 | 3 | background(1) | background(1) color(1) border-color(1) | primitive:btn | primitives.css .btn |
| 82 | 83 | - | `.btn-secondary` | 0,2,0→0,1,0 | 3 | - | - | primitive:btn | primitives.css .btn |
| 83 | 84 | - | `.btn-primary:active` | 0,3,0→0,2,0 | 1 | - | - | mixed | primitives.css .btn + search.css |
| 83 | 84 | - | `.search-hero button:active` | 0,3,1→0,2,1 | 1 | - | - | mixed | primitives.css .btn + search.css |
| 84 | 86 | (max-width: 900px) | `.dash-columns` | 0,2,0→0,1,0 | 1 | - | grid-template-columns(2) | screen | dashboard.css |
| 85 | 89 | (max-width: 640px) | `.catalog-filters` | 0,2,0→0,1,0 | 1 | - | gap(3) | screen | catalog.css |
| 86 | 90 | (max-width: 640px) | `.lab-page .search-hero` | 0,3,0→0,2,0 | 2 | - | padding-top(1) padding-bottom(1) | screen | search.css |
| 87 | 91 | (max-width: 640px) | `.search-hero h1` | 0,2,1→0,1,1 | 1 | - | font-size(2) | screen | search.css |
| 88 | 92 | (max-width: 640px) | `.dash-tiles` | 0,2,0→0,1,0 | 1 | - | grid-template-columns(1) | screen | dashboard.css |
| 89 | 93 | (max-width: 640px) | `.dash-tile` | 0,2,0→0,1,0 | 1 | - | padding(1) | drop | - |
| 90 | 94 | (max-width: 640px) | `.dash-bar` | 0,2,0→0,1,0 | 2 | - | min-height(1) grid-template-columns(2) | screen | dashboard.css |
| 91 | 95 | (max-width: 640px) | `.dash-steps` | 0,2,0→0,1,0 | 2 | - | gap(3) | screen | dashboard.css |
| 92 | 96 | (max-width: 640px) | `.pj-modal-back` | 0,2,0→0,1,0 | 1 | - | padding(3) | screen | project.css |
| 93 | 97 | (max-width: 640px) | `.pj-modal` | 0,2,0→0,1,0 | 1 | - | max-height(3) | screen | project.css |
| 94 | 98 | (max-width: 640px) | `.pj-modal-h` | 0,2,0→0,1,0 | 1 | - | padding(2) | screen | project.css |
| 95 | 99 | (max-width: 640px) | `.pj-fgroup` | 0,2,0→0,1,0 | 1 | - | padding(2) | screen | project.css |
| 96 | 100 | (max-width: 640px) | `.pj-seg button` | 0,2,1→0,1,1 | 1 | - | min-height(1) | screen | project.css |
| 97 | 101 | (max-width: 640px) | `.colmenu button` | 0,2,1→0,1,1 | 1 | - | min-height(1) | screen | catalog.css |
| 98 | 102 | (max-width: 640px) | `.tbl .rowact .rab` | 0,4,0→0,3,0 | 2 | - | width(2) height(2) | screen | catalog.css |
| 99 | 105 | - | `.fname .lock` | 0,3,0→0,2,0 | 3 | - | - | screen | catalog.css |
| 100 | 106 | - | `body:has(.pj-modal-back)` | 0,2,1→0,1,1 | 1 | - | - | screen | project.css |
| 101 | 109 | (max-width: 640px) | `.tbl .colmenu` | 0,3,0→0,2,0 | 8 | inset(2) | - | screen | catalog.css |
| 102 | 112 | - | `.colmenu .cm-box` | 0,3,0→0,2,0 | 4 | - | width(1) height(1) font-size(1) color(1) | screen | catalog.css |
| 103 | 115 | - | `.theme-switcher` | 0,1,0→0,1,0 | 10 | min-height(1) max-width(2) padding(1) | - | shell | shell.css |
| 104 | 116 | - | `.login-theme` | 0,1,0→0,1,0 | 3 | - | - | screen | login.css |
| 105 | 117 | - | `.inp` | 0,2,1→0,1,0 | 7 | font(1) | padding(3) border(4) border-radius(3) background(2) color(1) font(4) | primitive:field | primitives.css .field |
| 105 | 117 | - | `.sel` | 0,2,1→0,1,0 | 7 | font(1) | padding(2) border(3) border-radius(2) font(2) | primitive:field | primitives.css .field |
| 105 | 117 | - | `.login-input` | 0,2,1→0,1,0 | 7 | font(1) | padding(1) border(2) | primitive:field | primitives.css .field |
| 105 | 117 | - | `.pv-control select` | 0,2,1→0,1,1 | 7 | font(1) | - | primitive:field | primitives.css .field |
| 106 | 118 | - | `.lin button:where(:not(.btn))` | 0,2,1→0,1,1 | 1 | - | - | mixed | primitives.css .modal + lineage.css + preview.css |
| 106 | 118 | - | `.pv-zoom button:where(:not(.btn))` | 0,2,1→0,1,1 | 1 | - | - | mixed | primitives.css .modal + lineage.css + preview.css |
| 106 | 118 | - | `.pv-shot button:where(:not(.btn))` | 0,2,1→0,1,1 | 1 | - | - | mixed | primitives.css .modal + lineage.css + preview.css |
| 106 | 118 | - | `.modal-h button:where(:not(.btn))` | 0,2,1→0,1,1 | 1 | - | - | mixed | primitives.css .modal + lineage.css + preview.css |
| 107 | 119 | - | `input[type="checkbox"]` | 0,2,1→0,1,1 | 1 | - | - | primitive:field | primitives.css .field |
| 107 | 119 | - | `input[type="radio"]` | 0,2,1→0,1,1 | 1 | - | - | primitive:field | primitives.css .field |
| 108 | 120 | - | `.detail-page` | 0,2,0→0,1,0 | 5 | - | max-width(1) margin-inline(1) padding(1) padding-bottom(1) | pattern:page | patterns.css .page |
| 108 | 120 | - | `.project-detail` | 0,2,0→0,1,0 | 5 | - | max-width(1) margin-inline(1) padding(1) padding-bottom(1) | pattern:page | patterns.css .page |
| 108 | 120 | - | `.preview-page` | 0,2,0→0,1,0 | 5 | - | max-width(1) padding(1) padding-bottom(1) | pattern:page | patterns.css .page |
| 108 | 120 | - | `.settings-page` | 0,2,0→0,1,0 | 5 | - | max-width(1) margin-inline(1) padding(2) padding-bottom(2) | pattern:page | patterns.css .page |
| 109 | 121 | - | `.search-page` | 0,2,0→0,1,0 | 3 | - | max-width(1) padding(1) | pattern:page | patterns.css .page--narrow 또는 search.css |
| 110 | 122 | - | `.dt-header` | 0,2,0→0,1,0 | 2 | - | - | mixed | upload.css + detail.css |
| 110 | 122 | - | `.dt-card` | 0,2,0→0,1,0 | 2 | - | - | mixed | upload.css + detail.css |
| 110 | 122 | - | `.pj-card` | 0,2,0→0,1,0 | 2 | - | - | mixed | upload.css + detail.css |
| 110 | 122 | - | `.up-card` | 0,2,0→0,1,0 | 2 | - | border-radius(1) | mixed | upload.css + detail.css |
| 110 | 122 | - | `.mapstage` | 0,2,0→0,1,0 | 2 | - | border-radius(1) | mixed | upload.css + detail.css |
| 110 | 122 | - | `.reggate` | 0,2,0→0,1,0 | 2 | - | border-radius(2) | mixed | upload.css + detail.css |
| 110 | 122 | - | `.regarea` | 0,2,0→0,1,0 | 2 | - | border-radius(1) | mixed | upload.css + detail.css |
| 111 | 123 | - | `.card-h` | 0,2,0→0,1,0 | 1 | padding(1) | padding(1) | primitive:card | primitives.css .card |
| 111 | 123 | - | `.card-b` | 0,2,0→0,1,0 | 1 | padding(3) | padding(2) | primitive:card | primitives.css .card |
| 112 | 124 | - | `.card-h h3` | 0,2,1→0,1,1 | 3 | font-size(1) | font-size(1) | mixed | primitives.css .card + preview.css |
| 112 | 124 | - | `.pv-h2` | 0,2,1→0,1,0 | 3 | - | font-size(1) | mixed | primitives.css .card + preview.css |
| 112 | 124 | - | `.dt-card h3` | 0,2,1→0,1,1 | 3 | - | - | mixed | primitives.css .card + preview.css |
| 113 | 125 | - | `.card-h` | 0,2,0→0,1,0 | 2 | gap(1) | gap(1) | primitive:card | primitives.css .card |
| 114 | 126 | - | `.search-page .hit` | 0,3,0→0,2,0 | 1 | - | padding(1) | screen | search.css |
| 115 | 127 | - | `.search-page .hits` | 0,3,0→0,2,0 | 1 | - | gap(1) | screen | search.css |
| 116 | 128 | - | `.form-row` | 0,2,0→0,1,0 | 1 | - | gap(3) | pattern:form | patterns.css .form-row |
| 116 | 128 | - | `.pv-control` | 0,2,0→0,1,0 | 1 | - | gap(1) | pattern:form | patterns.css .form-row |
| 117 | 129 | - | `.labinfo-modal` | 0,2,0→0,1,0 | 4 | - | border-radius(1) padding(1) | primitive:modal | primitives.css .modal |
| 117 | 129 | - | `.approval-dialog` | 0,2,0→0,1,0 | 4 | - | padding(1) | primitive:modal | primitives.css .modal |
| 117 | 129 | - | `.modal--dialog` | 0,2,0→0,1,0 | 4 | padding(1) | - | primitive:modal | primitives.css .modal |
| 118 | 130 | - | `.modal--dialog:has(.modal-h)` | 0,3,0→0,2,0 | 1 | - | - | primitive:modal | primitives.css .modal |
| 119 | 131 | - | `.labinfo-modal h3` | 0,2,1→0,1,1 | 2 | - | font-size(1) margin-bottom(1) | screen | lab.css |
| 120 | 132 | - | `.labinfo-modal .form-row` | 0,3,0→0,2,0 | 1 | - | margin-bottom(3) | screen | lab.css |
| 121 | 133 | - | `.modal-takeover .up-steps .card-b` | 0,4,0→0,3,0 | 2 | padding(1) | gap(1) padding(1) | screen | upload.css |
| 122 | 134 | - | `.modal-takeover .form-row` | 0,3,0→0,2,0 | 1 | - | gap(2) | screen | upload.css |
| 123 | 135 | - | `.modal-takeover .reg-actions .btn` | 0,4,0→0,3,0 | 2 | - | height(1) | screen | upload.css |
| 124 | 136 | - | `.pv-register` | 0,2,0→0,1,0 | 1 | - | - | screen | preview.css |
| 125 | 137 | - | `.gnb` | 0,2,0→0,1,0 | 1 | gap(3) | gap(3) | shell | shell.css |
| 126 | 138 | - | `.gnb-settings` | 0,2,0→0,1,0 | 1 | display(1) | display(1) | shell | shell.css |
| 127 | 139 | - | `.gnb-upload` | 0,2,0→0,1,0 | 1 | - | - | shell | shell.css |
| 128 | 140 | - | `.login-submit` | 0,2,0→0,1,0 | 1 | - | - | screen | login.css |
| 129 | 141 | - | `button:focus-visible` | 0,2,1→0,1,1 | 2 | - | - | drop | - |
| 129 | 141 | - | `a:focus-visible` | 0,2,1→0,1,1 | 2 | - | - | drop | - |
| 129 | 141 | - | `input:focus-visible` | 0,2,1→0,1,1 | 2 | - | - | drop | - |
| 129 | 141 | - | `select:focus-visible` | 0,2,1→0,1,1 | 2 | - | - | drop | - |
| 129 | 141 | - | `textarea:focus-visible` | 0,2,1→0,1,1 | 2 | - | - | drop | - |
| 130 | 143 | (max-width: 900px) | `.gnb` | 0,2,0→0,1,0 | 5 | gap(2) padding(1) | height(1) gap(3) padding(5) | shell | shell.css |
| 131 | 144 | (max-width: 900px) | `.gnb .mainnav` | 0,3,0→0,2,0 | 4 | - | - | shell | shell.css |
| 132 | 145 | (max-width: 900px) | `.gnb .mainnav a` | 0,3,1→0,2,1 | 3 | - | - | shell | shell.css |
| 133 | 146 | (max-width: 900px) | `.gnb .labswitch` | 0,3,0→0,2,0 | 1 | - | - | shell | shell.css |
| 134 | 147 | (max-width: 900px) | `.gnb .avatar-wrap` | 0,3,0→0,2,0 | 1 | - | - | shell | shell.css |
| 135 | 152 | (max-width: 900px) | `.gnb .gnb-upload` | 0,3,0→0,2,0 | 1 | - | - | shell | shell.css |
| 135 | 152 | (max-width: 900px) | `.gnb .gnb-settings` | 0,3,0→0,2,0 | 1 | - | - | shell | shell.css |
| 136 | 153 | (max-width: 900px) | `.gnb .gnb-more-wrap` | 0,3,0→0,2,0 | 2 | - | - | shell | shell.css |
| 137 | 154 | (max-width: 900px) | `.gnb .gnb-more` | 0,3,0→0,2,0 | 1 | - | - | shell | shell.css |
| 138 | 157 | (max-width: 640px) | `.inp` | 0,2,1→0,1,0 | 1 | - | font-size(5) | primitive:field | primitives.css .field |
| 138 | 157 | (max-width: 640px) | `.sel` | 0,2,1→0,1,0 | 1 | - | font-size(4) | primitive:field | primitives.css .field |
| 138 | 157 | (max-width: 640px) | `.login-input` | 0,2,1→0,1,0 | 1 | - | font-size(2) | primitive:field | primitives.css .field |
| 138 | 157 | (max-width: 640px) | `.pv-control select` | 0,2,1→0,1,1 | 1 | - | font-size(1) | primitive:field | primitives.css .field |
| 139 | 158 | (max-width: 640px) | `.theme-switcher` | 0,1,0→0,1,0 | 2 | max-width(1) | min-height(1) max-width(1) | shell | shell.css |
| 140 | 159 | (max-width: 640px) | `.gnb` | 0,2,0→0,1,0 | 2 | gap(1) | gap(5) padding-inline(6) | shell | shell.css |
| 141 | 160 | (max-width: 640px) | `.gnb .labswitch` | 0,3,0→0,2,0 | 3 | - | - | shell | shell.css |
| 141 | 160 | (max-width: 640px) | `.gnb .gnb-settings` | 0,3,0→0,2,0 | 3 | - | - | shell | shell.css |
| 141 | 160 | (max-width: 640px) | `.gnb .gnb-upload` | 0,3,0→0,2,0 | 3 | - | - | shell | shell.css |
| 141 | 160 | (max-width: 640px) | `.gnb .gnb-more` | 0,3,0→0,2,0 | 3 | - | - | shell | shell.css |
| 141 | 160 | (max-width: 640px) | `.gnb .avatar` | 0,3,0→0,2,0 | 3 | - | - | shell | shell.css |
| 142 | 161 | (max-width: 640px) | `.gnb .avatar` | 0,3,0→0,2,0 | 1 | - | - | shell | shell.css |
| 143 | 162 | (max-width: 640px) | `.gnb .gnb-logout` | 0,3,0→0,2,0 | 1 | - | - | shell | shell.css |
| 144 | 163 | (max-width: 640px) | `.pv-basic-grid` | 0,2,0→0,1,0 | 1 | - | grid-template-columns(1) | screen | preview.css |
| 145 | 164 | (max-width: 640px) | `.pv-basic-row dd` | 0,2,1→0,1,1 | 2 | - | - | screen | preview.css |
| 146 | 165 | (max-width: 640px) | `.dr-pop` | 0,2,0→0,1,0 | 6 | - | position(1) inset(2) width(2) max-width(1) | screen | upload.css |
| 147 | 166 | (max-width: 640px) | `.dr-cal-d` | 0,2,0→0,1,0 | 1 | - | height(1) | screen | upload.css |
| 148 | 167 | (max-width: 640px) | `.pv-zoom button` | 0,2,1→0,1,1 | 1 | - | - | screen | preview.css |
| 148 | 167 | (max-width: 640px) | `.pv-shot button` | 0,2,1→0,1,1 | 1 | - | - | screen | preview.css |
| 148 | 167 | (max-width: 640px) | `.lin button` | 0,2,1→0,1,1 | 1 | - | - | screen | preview.css |
| 149 | 170 | - | `.chip--neutral` | 0,2,0→0,1,0 | 2 | - | - | primitive:chip | primitives.css .chip |
| 150 | 171 | - | `.chip--warning` | 0,2,0→0,1,0 | 2 | - | background(2) color(2) | primitive:chip | primitives.css .chip |
| 151 | 172 | - | `.detail-page .dt-header h1` | 0,3,1→0,2,1 | 3 | - | font-size(1) line-height(1) | screen | detail.css |
| 152 | 173 | - | `.detail-page .dsec-h h2` | 0,3,1→0,2,1 | 1 | - | font-size(2) | screen | detail.css |
| 153 | 175 | - | `.chip:where(:not([class*="chip--"]))` | 0,2,0→0,1,0 | 2 | - | background(2) | primitive:chip | primitives.css .chip |
| 154 | 176 | - | `.pj-ds-scroll` | 0,2,0→0,1,0 | 2 | - | - | screen | project.css |
| 155 | 177 | - | `.pj-ds` | 0,2,0→0,1,0 | 1 | - | - | screen | project.css |
| 156 | 178 | - | `.detail-page .ln .arw` | 0,4,0→0,3,0 | 2 | - | color(2) opacity(1) | screen | lineageGraph.css |
| 156 | 178 | - | `.detail-page .ln-go .arw` | 0,4,0→0,3,0 | 2 | - | color(2) opacity(1) | screen | lineageGraph.css |
| 157 | 179 | - | `.up-empty .up-card > .card-b` | 0,4,0→0,3,0 | 1 | - | padding(2) | screen | upload.css |
| 158 | 180 | - | `.up-body` | 0,2,0→0,1,0 | 1 | - | - | screen | upload.css |
| 159 | 181 | - | `.up-body > *` | 0,2,0→0,1,0 | 1 | - | - | screen | upload.css |
| 160 | 182 | - | `.reggate` | 0,2,0→0,1,0 | 1 | - | - | screen | upload.css |
| 161 | 184 | (max-width: 640px) | `.filecard` | 0,2,0→0,1,0 | 1 | - | - | screen | upload.css |
| 162 | 185 | (max-width: 640px) | `.filecard .fmeta` | 0,3,0→0,2,0 | 1 | - | flex-basis(1) | screen | upload.css |
| 163 | 186 | (max-width: 640px) | `.filecard .fkind` | 0,3,0→0,2,0 | 1 | - | - | screen | upload.css |
| 164 | 187 | (max-width: 640px) | `.filecard .sel` | 0,3,0→0,2,0 | 1 | - | width(2) | screen | upload.css |
| 165 | 188 | (max-width: 640px) | `.reggate` | 0,2,0→0,1,0 | 2 | - | align-items(1) gap(1) | screen | upload.css |
| 166 | 189 | (max-width: 640px) | `.reggate .rg-a` | 0,3,0→0,2,0 | 2 | - | flex-basis(1) | screen | upload.css |
| 167 | 191 | - | `.lin-findbar > label` | 0,2,1→0,1,1 | 1 | - | - | screen | lineage.css |
| 168 | 192 | - | `.lin-findbar input` | 0,2,1→0,1,1 | 3 | - | - | screen | lineage.css |
| 168 | 192 | - | `.lin-findbar select` | 0,2,1→0,1,1 | 3 | - | - | screen | lineage.css |
| 169 | 193 | - | `.lin-picker li > button` | 0,2,2→0,1,2 | 5 | background(1) | - | screen | lineage.css |
| 170 | 194 | - | `.lin-picker li > button[aria-pressed="true"]` | 0,3,2→0,2,2 | 1 | - | - | screen | lineage.css |
| 171 | 195 | - | `.lin-find .modal-h .x` | 0,4,0→0,3,0 | 9 | - | background(1) font-size(1) | primitive:modal | primitives.css .modal-x |
| 171 | 195 | - | `.lin-fix .modal-h .x` | 0,4,0→0,3,0 | 9 | - | background(1) font-size(1) | primitive:modal | primitives.css .modal-x |
| 171 | 195 | - | `.modal-takeover .modal-h .x` | 0,4,0→0,3,0 | 9 | - | background(1) font-size(1) | primitive:modal | primitives.css .modal-x |
| 172 | 197 | - | `.pj-toolbar` | 0,2,0→0,1,0 | 6 | gap(1) | padding(1) gap(1) border-color(1) border-radius(1) margin-bottom(1) | screen | project.css |
| 173 | 198 | - | `.pj-ctl` | 0,2,0→0,1,0 | 3 | - | display(1) gap(1) | screen | project.css |
| 174 | 199 | - | `.pj-ctl select` | 0,2,1→0,1,1 | 8 | font(1) font-size(1) | - | screen | project.css |
| 175 | 200 | - | `.pj-views` | 0,2,0→0,1,0 | 2 | - | - | screen | project.css |
| 176 | 201 | - | `.pj-views button` | 0,2,1→0,1,1 | 4 | - | font(1) | screen | project.css |
| 177 | 202 | - | `.pj-views button:first-child` | 0,3,1→0,2,1 | 1 | border-radius(1) | - | screen | project.css |
| 178 | 203 | - | `.pj-views button:last-child` | 0,3,1→0,2,1 | 1 | - | border-radius(1) | screen | project.css |
| 179 | 204 | - | `.pj-new` | 0,2,0→0,1,0 | 9 | - | padding(1) border(1) background(1) color(1) font-size(1) | screen | project.css |
| 180 | 205 | - | `.pd-linkurl` | 0,2,0→0,1,0 | 2 | - | - | screen | project.css |
| 180 | 205 | - | `.pd-linkurl:visited` | 0,3,0→0,2,0 | 2 | - | - | screen | project.css |
| 181 | 206 | - | `.table-scroll-hint` | 0,1,0→0,1,0 | 1 | display(1) | - | primitive:table | primitives.css .table-scroll-hint |
| 182 | 207 | - | `.pj-table` | 0,2,0→0,1,0 | 1 | - | min-width(1) | screen | project.css |
| 183 | 209 | (max-width: 1100px) | `.table-scroll-hint` | 0,1,0→0,1,0 | 5 | - | display(1) | primitive:table | primitives.css .table-scroll-hint |
| 184 | 212 | (max-width: 640px) | `.gnb` | 0,2,0→0,1,0 | 1 | - | gap(5) | shell | shell.css |
| 185 | 213 | (max-width: 640px) | `.theme-switcher` | 0,2,0→0,1,0 | 2 | - | max-width(2) padding-inline(1) | shell | shell.css |
| 186 | 214 | (max-width: 640px) | `.pj-toolbar` | 0,2,0→0,1,0 | 3 | - | display(1) gap(2) | screen | project.css |
| 187 | 215 | (max-width: 640px) | `.pj-ctl` | 0,2,0→0,1,0 | 1 | - | - | screen | project.css |
| 188 | 216 | (max-width: 640px) | `.pj-ctl select` | 0,2,1→0,1,1 | 2 | - | font-size(2) | screen | project.css |
| 189 | 217 | (max-width: 640px) | `.pj-count` | 0,2,0→0,1,0 | 2 | - | margin-left(1) | screen | project.css |
| 190 | 220 | - | `.search-page .notice a:where(:not(.strong, .quiet))` | 0,3,1→0,2,1 | 2 | - | - | screen | search.css |
| 190 | 220 | - | `.notfound a:where(:not(.strong, .quiet))` | 0,3,1→0,1,1 | 2 | - | - | screen | search.css |
| 190 | 220 | - | `.search-page .notice a:where(:not(.strong, .quiet)):visited` | 0,4,1→0,3,1 | 2 | - | - | screen | search.css |
| 190 | 220 | - | `.notfound a:where(:not(.strong, .quiet)):visited` | 0,4,1→0,2,1 | 2 | - | - | screen | search.css |
| 191 | 222 | - | `.search-page .vfilter` | 0,4,0→0,2,0 | 2 | - | height(1) | screen | search.css |
| 191 | 222 | - | `.search-page .empty-acts .quiet` | 0,4,0→0,3,0 | 2 | - | height(1) | screen | search.css |
| 191 | 222 | - | `.search-page .empty-acts .strong` | 0,4,0→0,3,0 | 2 | - | height(1) | screen | search.css |
| 192 | 223 | - | `.search-page .empty-acts` | 0,3,0→0,2,0 | 1 | - | - | screen | search.css |
