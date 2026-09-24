# P2a cascade verify

기준 `7967e00146b8387092e94cf1c3d15efa84fb5d21` → 작업 트리 · DS 선언 단위 621 · 옮겨짐 610 · 버림/불일치(면제 밖) 0 · 비DS 선언 변경 146(오늘 죽음 증명 139) · 면제 21 · 문제 0

## 면제 (선택자·미디어만으로 증명할 수 없어 사유로 판정한 것)

미디어 열은 P2b 에서 더했다(P2a 후속 · 규칙이 속한 `@media` 조건 · 없으면 `-`). 행과 판정은 그대로다.

| 종류 | DS# | 미디어 | 대상 | 사유 |
|---|---:|---|---|---|
| changed-live | - | - | `.login-input:focus-visible` outline | `.login-input` 은 `<input>`(LoginPage.tsx) — 오늘 DS#129(0,2,1)가 `.login-input:focus-visible { outline: none }`(0,2,0)을 이겨 초점 윤곽이 렌더된다. #129 를 버리면 none 이 되살아나므로 죽은 선언을 지웠다 |
| changed-live | - | - | `.up-empty .up-card` border | `border:0` 중 색 longhand(currentcolor)만 죽어 있었다 — 오늘 DS#9 `.card { border-color }`(접두 포함 0,2,0 · 뒤)가 덮는다(`className="card up-card"`). 흡수 뒤 색이 currentcolor 로 바뀌는 것을 upload 계산값 대조로 확인해 `border-width:0; border-style:none` 으로 값을 맞췄다(폭 0 그대로) |
| changed-live | - | (max-width: 640px) | `.modal.lab-info` padding | `.lab-info` 는 `className="modal modal--dialog lab-info"`(LabInfoModal.tsx) 한 곳 — 오늘 DS#117 `.modal--dialog { padding: var(--space-card) }`(접두 포함 0,2,0 · 뒤)가 이 선언 둘(기본 · 640px · 0,2,0)을 덮는다. 죽은 선언 삭제 |
| changed-live | - | - | `.modal.lab-info` padding | `.lab-info` 는 `className="modal modal--dialog lab-info"`(LabInfoModal.tsx) 한 곳 — 오늘 DS#117 `.modal--dialog { padding: var(--space-card) }`(접두 포함 0,2,0 · 뒤)가 이 선언 둘(기본 · 640px · 0,2,0)을 덮는다. 죽은 선언 삭제 |
| changed-live | - | (max-width: 640px) | `.memgrid .memtbl td` padding | `.memtbl` 표는 `className="tbl memtbl"`(MemberPermissionGrid.tsx) — 오늘 DS#18 `.tbl td { padding: 10px 12px }`(접두 포함 0,2,1 · 뒤)가 이 640px 선언(0,2,1)을 덮는다. 흡수 뒤 되살아나는 것을 members-375 계산값 대조로 확인해 죽은 선언을 지웠다 |
| changed-live | - | - | `.btn:hover` background | 선택자를 `.btn:where(:not(.btn-primary, .btn-secondary)):hover`(특이도 0,2,0 그대로)로 좁혔다 — 오늘 DS#81 `.btn-primary`·#82 `.btn-secondary`(접두 포함 0,2,0 · 뒤)가 hover 배경을 덮는다. 흡수 뒤 둘이 0,1,0 이 되면 hover 가 되살아나는 것을 계산값 전수 대조(마우스가 놓인 upload-link·upload-metadata 의 주 버튼)로 확인했다. 그 밖의 `.btn` 에는 그대로 걸린다 |
| changed-live | - | - | `.pcard:focus-visible` outline-offset | `.pcard` 는 `<a>`(ProjectCards.tsx) — 오늘 DS#129 `:is(button, a, input, select, textarea):focus-visible`(0,2,1)이 `.pcard:focus-visible`(0,2,0)을 이겨 초점 간격 3px 이 렌더된다. #129 를 중복으로 버리면(셸 `:where()` 규칙 0,1,0) 2px 이 되살아나므로 죽은 선언을 지웠다 |
| flip | 120 | - | `.dr-times .form-row · .modal-takeover .form-row` margin-bottom | `.labinfo-modal`(연구실 정보 모달)과 `.dr-times`(업로드 기간 선택 팝오버)는 서로 다른 컴포넌트 루트다 / `.labinfo-modal`(연구실 정보 모달)과 `.modal-takeover`(업로드 전면 모달)는 서로 다른 모달 루트다 |
| flip | 73 | - | `.search-page .vfilter.on · .dr-useg button.on` color | 공유 키는 상태 클래스 `.on` 하나 — `.pj-seg`(프로젝트 만들기 모달의 구분 단추)와 `.dr-useg`(업로드 기간 선택의 단위 단추)는 서로 다른 컴포넌트 루트라 한 요소에 함께 걸리지 않는다 / 공유 키는 상태 클래스 `.on` 하나 — `.vfilter` 는 검색 결과 화면(`.search-page`)의 필터 단추이고 `.pj-seg` 는 프로젝트 모달의 구분 단추다 |
| flip | 73 | - | `.dr-useg button.on` background | 공유 키는 상태 클래스 `.on` 하나 — `.pj-seg`(프로젝트 만들기 모달의 구분 단추)와 `.dr-useg`(업로드 기간 선택의 단위 단추)는 서로 다른 컴포넌트 루트라 한 요소에 함께 걸리지 않는다 |
| missing | 129 | - | `textarea:focus-visible` outline-offset | 조사 drop — `shell.css` 의 `:where(button, a, input, select, textarea):focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: 3px; }` 와 같은 값. #129 가 오늘 이기던 경쟁 셋은 지우거나 선택자에서 뺐다(`.login-input:focus-visible` outline · `.pcard:focus-visible` outline-offset · `.modal-takeover button:focus-visible`) |
| missing | 129 | - | `textarea:focus-visible` outline | 조사 drop — `shell.css` 의 `:where(button, a, input, select, textarea):focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: 3px; }` 와 같은 값. #129 가 오늘 이기던 경쟁 셋은 지우거나 선택자에서 뺐다(`.login-input:focus-visible` outline · `.pcard:focus-visible` outline-offset · `.modal-takeover button:focus-visible`) |
| missing | 129 | - | `select:focus-visible` outline-offset | 조사 drop — `shell.css` 의 `:where(button, a, input, select, textarea):focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: 3px; }` 와 같은 값. #129 가 오늘 이기던 경쟁 셋은 지우거나 선택자에서 뺐다(`.login-input:focus-visible` outline · `.pcard:focus-visible` outline-offset · `.modal-takeover button:focus-visible`) |
| missing | 129 | - | `select:focus-visible` outline | 조사 drop — `shell.css` 의 `:where(button, a, input, select, textarea):focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: 3px; }` 와 같은 값. #129 가 오늘 이기던 경쟁 셋은 지우거나 선택자에서 뺐다(`.login-input:focus-visible` outline · `.pcard:focus-visible` outline-offset · `.modal-takeover button:focus-visible`) |
| missing | 129 | - | `input:focus-visible` outline-offset | 조사 drop — `shell.css` 의 `:where(button, a, input, select, textarea):focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: 3px; }` 와 같은 값. #129 가 오늘 이기던 경쟁 셋은 지우거나 선택자에서 뺐다(`.login-input:focus-visible` outline · `.pcard:focus-visible` outline-offset · `.modal-takeover button:focus-visible`) |
| missing | 129 | - | `input:focus-visible` outline | 조사 drop — `shell.css` 의 `:where(button, a, input, select, textarea):focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: 3px; }` 와 같은 값. #129 가 오늘 이기던 경쟁 셋은 지우거나 선택자에서 뺐다(`.login-input:focus-visible` outline · `.pcard:focus-visible` outline-offset · `.modal-takeover button:focus-visible`) |
| missing | 129 | - | `a:focus-visible` outline-offset | 조사 drop — `shell.css` 의 `:where(button, a, input, select, textarea):focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: 3px; }` 와 같은 값. #129 가 오늘 이기던 경쟁 셋은 지우거나 선택자에서 뺐다(`.login-input:focus-visible` outline · `.pcard:focus-visible` outline-offset · `.modal-takeover button:focus-visible`) |
| missing | 129 | - | `a:focus-visible` outline | 조사 drop — `shell.css` 의 `:where(button, a, input, select, textarea):focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: 3px; }` 와 같은 값. #129 가 오늘 이기던 경쟁 셋은 지우거나 선택자에서 뺐다(`.login-input:focus-visible` outline · `.pcard:focus-visible` outline-offset · `.modal-takeover button:focus-visible`) |
| missing | 129 | - | `button:focus-visible` outline-offset | 조사 drop — `shell.css` 의 `:where(button, a, input, select, textarea):focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: 3px; }` 와 같은 값. #129 가 오늘 이기던 경쟁 셋은 지우거나 선택자에서 뺐다(`.login-input:focus-visible` outline · `.pcard:focus-visible` outline-offset · `.modal-takeover button:focus-visible`) |
| missing | 129 | - | `button:focus-visible` outline | 조사 drop — `shell.css` 의 `:where(button, a, input, select, textarea):focus-visible { outline: 2px solid var(--color-primary-600); outline-offset: 3px; }` 와 같은 값. #129 가 오늘 이기던 경쟁 셋은 지우거나 선택자에서 뺐다(`.login-input:focus-visible` outline · `.pcard:focus-visible` outline-offset · `.modal-takeover button:focus-visible`) |
| missing | 89 | (max-width: 640px) | `.dash-tile` padding | 조사 drop — `@media (max-width: 640px) .dash-tile { padding: 16px }` 는 DS#48 `.dash-tile { padding: 16px }`(미디어 없음)과 같은 값. #48 은 dashboard.css 의 `.dash-tile` 규칙에 병합됐고 그 뒤 같은 선택자로 padding 을 다시 쓰는 규칙이 없다 |

## 버림·불일치 (DS 선언이 새 자리에서 같은 값으로 발견되지 않음)

| DS# | 인자 | 속성 | DS 값 | 상태 | 찾은 값 |
|---:|---|---|---|---|---|

## 비DS 선언 변경 (삭제·값 일치)

| 파일:행 | 선택자 | 미디어 | 속성 | 원래 값 | 뒤 | 오늘 죽음 증명 |
|---|---|---|---|---|---|---|
| components/catalog/catalog.css:6 | `.catalog-page .page-head` | - | gap | `10px` | `8px 12px` | DS#6 `.catalog-page .page-head` |
| components/catalog/catalog.css:6 | `.catalog-page .page-head` | - | margin-bottom | `14px` | `var(--space-section)` | DS#6 `.catalog-page .page-head` |
| components/catalog/catalog.css:7 | `.catalog-page .page-head h1` | - | font-size | `var(--text-h2, 24px)` | 삭제 | DS#5 `.page-head h1` |
| components/catalog/catalog.css:7 | `.catalog-page .page-head h1` | - | letter-spacing | `-0.023em` | 삭제 | DS#5 `.page-head h1` |
| components/catalog/catalog.css:9 | `.catalog-page .desc` | - | font-size | `var(--text-caption)` | `var(--text-body-sm)` | DS#7 `.catalog-page .desc` |
| components/catalog/catalog.css:36 | `.tbl .fname` | - | font-size | `13px` | `var(--text-body-sm)` | DS#19 `.tbl .fname` |
| components/catalog/catalog.css:36 | `.tbl .fname` | - | letter-spacing | `-0.01em` | `0` | DS#19 `.tbl .fname` |
| components/catalog/catalog.css:39 | `.tbl td.empty` | - | padding | `36px 14px` | 삭제 | DS#18 `.tbl td` |
| components/catalog/catalog.css:44 | `.tbl thead th > .thf` | - | padding | `10px 14px` | `10px 16px` | DS#17 `.tbl th .thf` |
| components/catalog/catalog.css:74 | `.colmenu .cm-box` | - | width | `13px` | `16px` | DS#102 `.colmenu .cm-box` |
| components/catalog/catalog.css:74 | `.colmenu .cm-box` | - | height | `13px` | `16px` | DS#102 `.colmenu .cm-box` |
| components/catalog/catalog.css:75 | `.colmenu .cm-box` | - | font-size | `9px` | `var(--text-caption)` | DS#102 `.colmenu .cm-box` |
| components/catalog/catalog.css:75 | `.colmenu .cm-box` | - | color | `#fff` | `var(--color-on-primary)` | DS#102 `.colmenu .cm-box` |
| components/catalog/catalog.css:91 | `.fchips` | - | gap | `6px` | `8px` | DS#26 `.fchips` |
| components/catalog/catalog.css:91 | `.fchips` | - | padding | `10px 14px` | `12px var(--space-card)` | DS#26 `.fchips` |
| components/catalog/catalog.css:96 | `.fchips .fc` | - | height | `24px` | `32px` | DS#27 `.fchips .fc` |
| components/catalog/catalog.css:135 | `.tbl th.rowact, .tbl td.rowact` | - | padding-right | `14px` | 삭제 | DS#18 `.tbl td` |
| components/catalog/catalog.css:136 | `.tbl td.rowact .ra` | - | opacity | `0` | 삭제 | DS#24 `.tbl .rowact .ra` |
| components/catalog/catalog.css:139 | `.tbl td.rowact .rab` | - | width | `26px` | 삭제 | DS#25 `.tbl .rowact .rab` |
| components/catalog/catalog.css:139 | `.tbl td.rowact .rab` | - | height | `26px` | 삭제 | DS#25 `.tbl .rowact .rab` |
| components/catalog/catalog.css:148 | `.crosslink` | - | padding | `13px 15px` | `16px 20px` | DS#30 `.crosslink` |
| components/catalog/catalog.css:171 | `.catalog-filters` | - | gap | `16px` | `20px` | DS#10 `.catalog-filters` |
| components/catalog/catalog.css:171 | `.catalog-filters` | - | padding | `20px` | `var(--space-card)` | DS#10 `.catalog-filters` |
| components/catalog/catalog.css:173 | `.catalog-filters .axis-pick` | - | gap | `6px` | `8px` | DS#11 `.catalog-filters .axis-pick` |
| components/catalog/catalog.css:174 | `.catalog-filters .axis-k` | - | font-size | `13px` | 삭제 | DS#12 `.axis-k` |
| components/catalog/catalog.css:175 | `.catalog-filters select` | - | height | `38px` | `var(--control-height)` | DS#13 `.catalog-filters select` |
| components/catalog/catalog.css:181 | `.catalog-filters` | (max-width: 640px) | padding | `16px` | 삭제 | DS#10 `.catalog-filters` |
| components/catalog/catalog.css:182 | `.catalog-filters select` | (max-width: 640px) | height | `40px` | 삭제 | DS#13 `.catalog-filters select` |
| components/detail/detail.css:11 | `.detail-page .dt-header h1` | - | font-size | `31px` | `var(--text-h2)` | DS#151 `.detail-page .dt-header h1` |
| components/detail/detail.css:12 | `.detail-page .dt-header h1` | - | line-height | `1.25` | `1.3` | DS#151 `.detail-page .dt-header h1` |
| components/project/project.css:25 | `.project-page .page-head h1` | - | letter-spacing | `-0.023em` | 삭제 | DS#5 `.page-head h1` |
| components/project/project.css:60 | `.pj-toolbar` | - | gap | `12px` | `16px` | DS#172 `.pj-toolbar` |
| components/project/project.css:61 | `.pj-toolbar` | - | padding | `10px 12px` | `var(--space-card)` | DS#172 `.pj-toolbar` |
| components/project/project.css:63 | `.pj-toolbar` | - | border-radius | `8px` | `var(--radius-lg)` | DS#172 `.pj-toolbar` |
| components/project/project.css:64 | `.pj-toolbar` | - | margin-bottom | `14px` | `var(--space-section)` | DS#172 `.pj-toolbar` |
| components/project/project.css:68 | `.pj-ctl` | - | display | `inline-flex` | `grid` | DS#173 `.pj-ctl` |
| components/project/project.css:70 | `.pj-ctl` | - | gap | `6px` | `8px` | DS#173 `.pj-ctl` |
| components/project/project.css:83 | `.pj-views button.on` | - | font-weight | `600` | 삭제 | DS#176 `.pj-views button` |
| components/project/project.css:115 | `.pcard:focus-visible` | - | outline-offset | `2px` | 삭제 | **없음** |
| components/project/project.css:213 | `.pj-table` | - | min-width | `900px` | `680px` | DS#182 `.pj-table` |
| components/project/project.css:267 | `.project-detail .card` | - | border | `1px solid var(--color-border)` | `1px solid var(--color-border-strong)` | DS#9 `.card` |
| components/project/project.css:268 | `.project-detail .card` | - | border-radius | `10px` | `var(--radius-lg)` | DS#9 `.card` |
| components/project/project.css:334 | `.pj-modal-back` | - | background | `rgb(15 20 28 / 45%)` | `var(--color-overlay)` | DS#60 `.pj-modal-back` |
| components/project/project.css:341 | `.pj-modal` | - | width | `min(560px, 100%)` | `min(600px, 100%)` | DS#61 `.pj-modal` |
| components/project/project.css:342 | `.pj-modal` | - | max-height | `90vh` | `calc(100dvh - 48px)` | DS#61 `.pj-modal` |
| components/project/project.css:346 | `.pj-modal` | - | border-radius | `10px` | `var(--radius-lg)` | DS#9 `.pj-modal` |
| components/project/project.css:354 | `.pj-modal-h` | - | padding | `14px 16px` | `20px var(--space-card)` | DS#62 `.pj-modal-h` |
| components/project/project.css:360 | `.pj-modal-h h3` | - | font-size | `15px` | `20px` | DS#63 `.pj-modal-h h3` |
| components/project/project.css:373 | `.pj-modal-b` | - | padding | `16px` | `var(--space-card)` | DS#65 `.pj-modal-b` |
| components/project/project.css:381 | `.pj-modal-f` | - | padding | `12px 16px` | `16px var(--space-card)` | DS#66 `.pj-modal-f` |
| components/project/project.css:387 | `.pj-row` | - | margin-bottom | `14px` | `24px` | DS#67 `.pj-row` |
| components/project/project.css:392 | `.pj-row label` | - | margin-bottom | `5px` | `8px` | DS#68 `.pj-row label` |
| components/project/project.css:393 | `.pj-row label` | - | font-size | `13px` | `var(--text-body-sm)` | DS#68 `.pj-row label` |
| components/project/project.css:394 | `.pj-row label` | - | color | `var(--color-text-muted)` | `var(--color-text)` | DS#68 `.pj-row label` |
| components/project/project.css:420 | `.pj-seg` | - | border-radius | `6px` | `var(--radius-sm)` | DS#71 `.pj-seg` |
| components/project/project.css:429 | `.pj-seg button` | - | font-size | `13px` | `var(--text-body-sm)` | DS#72 `.pj-seg button` |
| components/project/project.css:434 | `.pj-seg button.on` | - | background | `var(--color-gray-100)` | `var(--color-surface)` | DS#73 `.pj-seg button.on` |
| components/project/project.css:469 | `.pj-fgroup` | - | padding | `12px` | `20px` | DS#75 `.pj-fgroup` |
| components/project/project.css:478 | `.pj-fgroup-h` | - | margin-bottom | `10px` | `16px` | DS#77 `.pj-fgroup-h` |
| components/members/members.css:58 | `.btn:hover` | - | background | `var(--color-gray-50)` | 삭제 | **없음** |
| components/members/members.css:64 | `.btn-primary:hover` | - | background | `var(--color-primary-700)` | 삭제 | DS#81 `.btn-primary` |
| components/members/members.css:177 | `.memgrid .card-b` | (max-width: 640px) | padding | `6px 12px` | 삭제 | DS#111 `.card-b` |
| components/members/members.css:188 | `.memgrid .memtbl td` | (max-width: 640px) | padding | `3px 0` | 삭제 | **없음** |
| components/lab/lab.css:38 | `.labinfo-modal` | - | padding | `18px` | `var(--space-card)` | DS#117 `.labinfo-modal` |
| components/lab/lab.css:39 | `.labinfo-modal` | - | border-radius | `12px` | `var(--radius-lg)` | DS#117 `.labinfo-modal` |
| components/lab/lab.css:44 | `.labinfo-modal h3` | - | font-size | `var(--text-body)` | `20px` | DS#119 `.labinfo-modal h3` |
| components/lab/lab.css:49 | `.labinfo-modal .form-row` | - | gap | `4px` | 삭제 | DS#116 `.form-row` |
| components/lab/lab.css:50 | `.labinfo-modal .form-row` | - | margin-bottom | `10px` | `20px` | DS#120 `.labinfo-modal .form-row` |
| components/lab/lab.css:60 | `.labinfo-modal .inp, .labinfo-modal .sel` | - | padding | `8px 10px` | 삭제 | DS#105 `.inp` · DS#105 `.sel` |
| components/lab/lab.css:61 | `.labinfo-modal .inp, .labinfo-modal .sel` | - | border | `1px solid var(--color-border)` | 삭제 | DS#105 `.inp` · DS#105 `.sel` |
| components/lab/lab.css:62 | `.labinfo-modal .inp, .labinfo-modal .sel` | - | border-radius | `8px` | 삭제 | DS#105 `.inp` · DS#105 `.sel` |
| components/lab/lab.css:63 | `.labinfo-modal .inp, .labinfo-modal .sel` | - | font | `inherit` | 삭제 | DS#105 `.inp` · DS#105 `.sel` |
| components/lab/lab.css:80 | `.labinfo-modal .inp, .labinfo-modal .sel` | (max-width: 640px) | font-size | `16px` | 삭제 | DS#105 `.inp` · DS#105 `.sel` · DS#138 `.inp` |
| components/search/search.css:6 | `.search-hero h1` | - | font-size | `var(--text-h2, 24px)` | `var(--text-h2)` | DS#5 `.search-hero h1` |
| components/search/search.css:6 | `.search-hero h1` | - | letter-spacing | `-0.023em` | `-0.02em` | DS#5 `.search-hero h1` |
| components/search/search.css:9 | `.search-hero input` | - | padding | `12px 14px` | `14px 16px` | DS#33 `.search-hero input` |
| components/search/search.css:18 | `.search-hero .hero-note` | - | font-size | `var(--text-caption, 12px)` | `var(--text-body-sm)` | DS#35 `.search-hero .hero-note` |
| components/search/search.css:24 | `.search-page .page-head h1` | - | font-size | `var(--text-h2, 24px)` | 삭제 | DS#5 `.page-head h1` |
| components/search/search.css:47 | `.search-page .notice--empty .empty-acts .quiet, .search-page .notice--empty .empty-acts .strong` | - | height | `32px` | 삭제 | DS#191 `.search-page .empty-acts .quiet` · DS#191 `.search-page .empty-acts .strong` |
| components/search/search.css:54 | `.search-page .hits` | - | gap | `10px` | `16px` | DS#115 `.search-page .hits` |
| components/search/search.css:56 | `.search-page .hit` | - | padding | `14px 16px` | `var(--space-card)` | DS#114 `.search-page .hit` |
| components/search/search.css:86 | `.search-page .chip--warning` | - | background | `var(--color-warning-50, #fff6ed)` | 삭제 | DS#150 `.chip--warning` |
| components/search/search.css:86 | `.search-page .chip--warning` | - | color | `var(--color-warning-600, #a85400)` | 삭제 | DS#150 `.chip--warning` |
| components/dashboard/dashboard.css:22 | `.lab-page .search-hero` | - | max-width | `680px` | 삭제 | DS#31 `.lab-page .search-hero` |
| components/dashboard/dashboard.css:30 | `.dash-columns` | - | gap | `20px` | `var(--space-section)` | DS#36 `.dash-columns` |
| components/dashboard/dashboard.css:31 | `.dash-columns` | - | margin-top | `20px` | `8px` | DS#36 `.dash-columns` |
| components/dashboard/dashboard.css:43 | `.dash-col` | - | gap | `16px` | `20px` | DS#37 `.dash-col` |
| components/dashboard/dashboard.css:53 | `.dash-section-label` | - | font-size | `15px` | `var(--text-section)` | DS#38 `.dash-section-label` |
| components/dashboard/dashboard.css:54 | `.dash-section-label` | - | font-weight | `700` | `600` | DS#38 `.dash-section-label` |
| components/dashboard/dashboard.css:66 | `.dash-card` | - | padding | `20px` | `var(--space-card)` | DS#39 `.dash-card` |
| components/dashboard/dashboard.css:79 | `.dash-card-head h2` | - | font-size | `14px` | `var(--text-section)` | DS#41 `.dash-card-head h2` |
| components/dashboard/dashboard.css:102 | `.dash-bar` | - | grid-template-columns | `96px minmax(0, 1fr) 48px` | `100px minmax(0, 1fr) 40px` | DS#42 `.dash-bar` |
| components/dashboard/dashboard.css:111 | `.dash-bar` | - | font-size | `13px` | `var(--text-body-sm)` | DS#42 `.dash-bar` |
| components/dashboard/dashboard.css:116 | `.dash-bar-track` | - | height | `8px` | `6px` | DS#43 `.dash-bar-track` |
| components/dashboard/dashboard.css:125 | `.dash-bar-fill` | - | background | `var(--accent-neutral, #5b7089)` | `var(--accent-neutral)` | DS#44 `.dash-bar-fill` |
| components/dashboard/dashboard.css:144 | `.dash-calc` | - | margin | `4px 0 12px` | `8px 0 20px` | DS#46 `.dash-calc` |
| components/dashboard/dashboard.css:162 | `.dash-open-catalog` | - | min-height | `38px` | `var(--control-height)` | DS#51 `.dash-open-catalog` |
| components/dashboard/dashboard.css:163 | `.dash-open-catalog` | - | margin-top | `16px` | `20px` | DS#51 `.dash-open-catalog` |
| components/dashboard/dashboard.css:169 | `.dash-open-catalog` | - | font-size | `14px` | `var(--text-body-sm)` | DS#51 `.dash-open-catalog` |
| components/dashboard/dashboard.css:178 | `.dash-tiles` | - | gap | `10px` | `12px` | DS#47 `.dash-tiles` |
| components/dashboard/dashboard.css:187 | `.dash-tile` | - | padding | `10px 12px` | `16px` | DS#48 `.dash-tile` |
| components/dashboard/dashboard.css:192 | `.dash-tile strong` | - | font-size | `22px` | `28px` | DS#49 `.dash-tile strong` |
| components/dashboard/dashboard.css:234 | `.dash-recent button` | - | font-size | `13px` | `var(--text-body-sm)` | DS#52 `.dash-recent button` |
| components/dashboard/dashboard.css:254 | `.todo-grp h3` | - | font-size | `13px` | `var(--text-body-sm)` | DS#53 `.todo-grp h3` |
| components/dashboard/dashboard.css:272 | `.titem` | - | gap | `4px 10px` | `6px 16px` | DS#54 `.titem` |
| components/dashboard/dashboard.css:273 | `.titem` | - | padding | `6px 0` | `14px 0` | DS#54 `.titem` |
| components/dashboard/dashboard.css:274 | `.titem` | - | font-size | `13px` | `var(--text-body-sm)` | DS#54 `.titem` |
| components/dashboard/dashboard.css:370 | `.dash-steps` | - | margin-top | `16px` | `20px` | DS#58 `.dash-steps` |
| components/dashboard/dashboard.css:372 | `.dash-step-no` | - | width | `24px` | `28px` | DS#59 `.dash-step-no` |
| components/dashboard/dashboard.css:372 | `.dash-step-no` | - | height | `24px` | `28px` | DS#59 `.dash-step-no` |
| components/dashboard/dashboard.css:372 | `.dash-step-no` | - | line-height | `24px` | `28px` | DS#59 `.dash-step-no` |
| components/dashboard/dashboard.css:373 | `.modal.lab-info` | - | padding | `24px` | 삭제 | **없음** |
| components/dashboard/dashboard.css:379 | `.dash-card` | (max-width: 640px) | padding | `16px` | 삭제 | DS#39 `.dash-card` |
| components/dashboard/dashboard.css:381 | `.dash-recent button` | (max-width: 640px) | padding | `10px 0` | `12px 0` | DS#52 `.dash-recent button` |
| components/dashboard/dashboard.css:383 | `.modal.lab-info` | (max-width: 640px) | padding | `20px` | 삭제 | **없음** |
| components/preview/preview.css:59 | `.pv-h2` | - | font-size | `15px` | `var(--text-section)` | DS#112 `.pv-h2` |
| components/preview/preview.css:158 | `.pv-control` | - | gap | `4px` | `8px` | DS#116 `.pv-control` |
| components/lineage/lineage.css:236 | `.lin .chip--warning` | - | background | `var(--lin-over-bg)` | 삭제 | DS#150 `.chip--warning` |
| components/lineage/lineage.css:237 | `.lin .chip--warning` | - | color | `var(--lin-over-ink)` | 삭제 | DS#150 `.chip--warning` |
| components/lineage/lineageGraph.css:15 | `.detail-page .dsec-h h2` | - | font-size | `var(--text-h2)` | 삭제 | DS#152 `.detail-page .dsec-h h2` |
| components/lineage/lineageGraph.css:86 | `.detail-page .lrow .ln-go .arw` | - | color | `var(--color-gray-400)` | 삭제 | DS#156 `.detail-page .ln-go .arw` |
| components/upload/upload.css:251 | `textarea.inp` | - | line-height | `1.5` | 삭제 | DS#105 `.inp` |
| components/upload/upload.css:252 | `.inp[readonly]` | - | background | `var(--color-surface-alt)` | 삭제 | DS#105 `.inp` |
| components/upload/upload.css:252 | `.inp[readonly]` | - | color | `var(--up-muted)` | 삭제 | DS#105 `.inp` |
| components/upload/upload.css:559 | `.up-empty .up-card` | - | border | `0` | 삭제 | **없음** |
| components/upload/upload.css:577 | `.up-empty .reggate` | - | border-radius | `0` | 삭제 | DS#110 `.reggate` |
| components/upload/upload.css:593 | `.modal-takeover .up-steps .card-b` | - | gap | `12px` | `20px` | DS#121 `.modal-takeover .up-steps .card-b` |
| components/upload/upload.css:593 | `.modal-takeover .up-steps .card-b` | - | padding | `20px 22px` | `var(--space-card)` | DS#121 `.modal-takeover .up-steps .card-b` |
| components/upload/upload.css:594 | `.modal-takeover .form-row` | - | gap | `5px` | `8px` | DS#116 `.form-row` · DS#122 `.modal-takeover .form-row` |
| components/upload/upload.css:595 | `.modal-takeover .inp, .modal-takeover .sel` | - | font-size | `14px` | 삭제 | DS#105 `.inp` · DS#105 `.sel` |
| components/upload/upload.css:596 | `.modal-takeover .inp:focus-visible, .modal-takeover .sel:focus-visible, .modal-takeover button:focus-visible` | - | outline | `2px solid var(--color-primary-600)` | 삭제 | DS#129 `button:focus-visible` |
| components/upload/upload.css:596 | `.modal-takeover .inp:focus-visible, .modal-takeover .sel:focus-visible, .modal-takeover button:focus-visible` | - | outline-offset | `2px` | 삭제 | DS#129 `button:focus-visible` |
| components/upload/upload.css:618 | `.modal-takeover .reg-actions .btn` | - | height | `34px` | `auto` | DS#123 `.modal-takeover .reg-actions .btn` |
| components/approval/approval.css:3 | `.approval-dialog` | - | padding | `24px` | `var(--space-card)` | DS#117 `.approval-dialog` |
| components/common/variableTable.css:73 | `.vartable td .inp` | - | padding | `0 9px` | 삭제 | DS#105 `.inp` |
| components/common/variableTable.css:74 | `.vartable td .inp` | - | border | `none` | 삭제 | DS#105 `.inp` |
| components/common/variableTable.css:75 | `.vartable td .inp` | - | border-radius | `0` | 삭제 | DS#105 `.inp` |
| components/common/variableTable.css:76 | `.vartable td .inp` | - | background | `none` | 삭제 | DS#105 `.inp` |
| components/common/variableTable.css:77 | `.vartable td .inp` | - | font-size | `var(--text-body-sm)` | 삭제 | DS#105 `.inp` |
| auth/login.css:58 | `.login-input` | - | padding | `0 12px` | `10px 12px` | DS#105 `.login-input` |
| auth/login.css:62 | `.login-input` | - | border | `1px solid var(--color-border-strong)` | `1px solid var(--color-border-control)` | DS#105 `.login-input` |
| auth/login.css:68 | `.login-input:focus-visible` | - | outline | `none` | 삭제 | **없음** |
| auth/login.css:69 | `.login-input:focus-visible` | - | border-color | `var(--color-primary)` | 삭제 | DS#105 `.login-input` |
| shell/shell.css:113 | `.gnb` | - | gap | `10px` | `12px` | DS#125 `.gnb` |
| shell/shell.css:365 | `.gnb` | (max-width: 1180px) | gap | `8px` | 삭제 | DS#125 `.gnb` |
| shell/shell.css:376 | `.gnb-settings` | (max-width: 880px) | display | `none` | 삭제 | DS#126 `.gnb-settings` |

## 문제

| 종류 | 내용 |
|---|---|
