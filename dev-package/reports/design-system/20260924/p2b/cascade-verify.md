# P2b cascade verify (전 선언 단위)

기준 `60d63683` → 작업 트리 · 선언 단위 4882 · 자리 무변 4678 · 옮겨짐 137 · 삭제 67(오늘 죽음 증명 60) · 새 선언 4 · 면제 20 · 문제 0

판정: 단위 = 규칙 × 선택자 인자(`:is()` 펼침) × 선언. 새 자리 = 같은 인자(또는 같은 선택자)·미디어·속성·값(토큰 별칭 9종은 정본 이름으로 맞춰 비교)의 작업 트리 선언 중 마지막. 뒤집힘 = 오늘 이기던 경쟁(값 다름 · `key`/`type`/`universal`)에 새 자리(층·순서·특이도)로 지는 것. 삭제 = 오늘 모든 문맥에서 지는 것(경쟁 선택자·미디어 포함 관계로 증명). 새 선언 = 어떤 단위의 새 자리도 아닌 것(면제 사유 · 계산값 대조로 판정).

## 면제

| 종류 | 대상 | 사유 |
|---|---|---|
| flip | shell/shell.css:456 `.modal--dialog:has(.modal-h)` padding ← `.approval-dialog` | 공존 클래스(co) 경쟁이지만 .approval-dialog 두 곳(AccessRequestPanel · VerificationAction)은 .modal-h 를 품지 않아 :has(.modal-h) 가 걸리지 않는다(TSX 확인 · h3 제목) |
| flip | shell/shell.css:452 `.card-h h3` font-size ← `.pj-modal-h h3` · `.modal-h h3` · `.labinfo-modal h3` · `.todo-grp h3` · `.approval-dialog h3` · `.account-modal h3` | 요소 호환(type) 경쟁이지만 프로젝트 모달 머리 — .card-h 와 같은 파일에 없다(요소 공유 없음) — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 .card-h h3 는 모달 몸(UploadModal 생성 중·완료 카드)·설정 카드에만 있고 .modal-h 안이 아니다(TSX 확인) — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 LabInfoPanel 의 편집 모달 제목 — .card-h 는 카드 머리에서 닫힌 뒤다(h2 사용) — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 TodoInbox — .card-h 없음(dash-card-head 는 다른 클래스) — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 승인 대화상자 — .card-h 없음 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 계정 모달 — .card-h 없음 — 같은 요소에 걸리지 않는다 |
| flip | shell/shell.css:445 `.btn-primary:active` background ← `.pj-views button` · `.pj-seg button` · `.search-hero button` · `.dash-tile--linked button` · `.dash-recent button` · `.titem button` · `.pv-zoom button` · `.pv-shot button` · `.lin-picker li > button` · `.regsteps button` · `.dr-nav button` · `.dr-useg button` · `.dh-menu button` | 요소 호환(type) 경쟁이지만 ProjectsPage 의 보기 전환 버튼 — className 에 btn 없음(TSX 전수) — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 ProjectFormModal 의 유형 세그먼트 — .pj-seg 안에 .btn 없음(btn 은 모달 발 footer) — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 SearchHero 의 검색 버튼 — 같은 파일에 btn 클래스 없음 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 대시보드 타일 — 같은 파일에 btn 클래스 없음 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 대시보드 최근 목록 — 같은 파일에 btn 클래스 없음 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 대시보드 목록 항목 — 같은 파일에 btn 클래스 없음 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 미리보기 확대 버튼 — 같은 파일에 btn 클래스 없음 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 미리보기 스크린샷 버튼 — 같은 파일에 btn 클래스 없음 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 ParentPicker 의 .btn 은 li 의 자식이 아니다(오류·더 보기·발 버튼 · TSX 확인) — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 RegisterArea 의 단계 버튼 — className 은 is-active 뿐(.btn 없음) — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 PeriodCalendarPopover 의 달 이동 버튼 — .btn 없음(.btn 은 팝오버 발) — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 PeriodCalendarPopover 의 단위 세그먼트 — className 은 on 뿐 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 VerificationAction 의 메뉴 항목 — className 없음(.btn 은 확인 모달 안) — 같은 요소에 걸리지 않는다 |
| flip | shell/shell.css:440 `.tbl td` padding ← `.pj-table td` · `.pj-ds td` · `.projtable td` · `.vartable td` · `.vartable td` | 요소 호환(type) 경쟁이지만 className 에 tbl 을 쓰는 표는 CatalogTable(tbl catalog)·MemberPermissionGrid(tbl memtbl) 둘뿐이다(TSX 전수) — .pj-table 는 다른 표 / 요소 호환(type) 경쟁이지만 className 에 tbl 을 쓰는 표는 CatalogTable(tbl catalog)·MemberPermissionGrid(tbl memtbl) 둘뿐이다(TSX 전수) — .pj-ds 는 다른 표 / 요소 호환(type) 경쟁이지만 className 에 tbl 을 쓰는 표는 CatalogTable(tbl catalog)·MemberPermissionGrid(tbl memtbl) 둘뿐이다(TSX 전수) — .projtable 는 다른 표 / 요소 호환(type) 경쟁이지만 className 에 tbl 을 쓰는 표는 CatalogTable(tbl catalog)·MemberPermissionGrid(tbl memtbl) 둘뿐이다(TSX 전수) — .vartable 는 다른 표 |
| flip | shell/shell.css:439 `.tbl th` font-weight ← `.vartable th` | 요소 호환(type) 경쟁이지만 className 에 tbl 을 쓰는 표는 CatalogTable(tbl catalog)·MemberPermissionGrid(tbl memtbl) 둘뿐이다(TSX 전수) — .vartable 은 다른 표 |
| flip | shell/shell.css:439 `.tbl th` color ← `.vartable th` | 요소 호환(type) 경쟁이지만 className 에 tbl 을 쓰는 표는 CatalogTable(tbl catalog)·MemberPermissionGrid(tbl memtbl) 둘뿐이다(TSX 전수) — .vartable 은 다른 표 |
| flip | components/members/members.css:136 `.modal` background ← `body` | 요소 호환(type) 경쟁이지만 .modal 은 div 판이다(body 가 아님 · TSX 전수) |
| flip | components/members/members.css:127 `.modal-back` background ← `body` | 요소 호환(type) 경쟁이지만 .modal-back 은 div 뒤판이다(body 가 아님 · TSX 전수) |
| flip | components/members/members.css:60 `.btn:where(:not(.btn-primary, .btn-secondary)):hover` background ← `.pj-views button` · `.pj-seg button` · `.search-hero button` · `.dash-tile--linked button` · `.dash-recent button` · `.titem button` · `.pv-zoom button` · `.pv-shot button` · `.lin-picker li > button` · `.regsteps button` · `.btn-strong` · `.dr-nav button` · `.dr-useg button` · `.dh-menu button` | 요소 호환(type) 경쟁이지만 ProjectsPage 의 보기 전환 버튼 — className 에 btn 없음(TSX 전수) — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 ProjectFormModal 의 유형 세그먼트 — .pj-seg 안에 .btn 없음(btn 은 모달 발 footer) — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 SearchHero 의 검색 버튼 — 같은 파일에 btn 클래스 없음 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 대시보드 타일 — 같은 파일에 btn 클래스 없음 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 대시보드 최근 목록 — 같은 파일에 btn 클래스 없음 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 대시보드 목록 항목 — 같은 파일에 btn 클래스 없음 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 미리보기 확대 버튼 — 같은 파일에 btn 클래스 없음 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 미리보기 스크린샷 버튼 — 같은 파일에 btn 클래스 없음 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 ParentPicker 의 .btn 은 li 의 자식이 아니다(오류·더 보기·발 버튼 · TSX 확인) — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 RegisterArea 의 단계 버튼 — className 은 is-active 뿐(.btn 없음) — 같은 요소에 걸리지 않는다 / 공존 클래스(co) 뒤집힘을 upload.css .btn-strong:hover { background: var(--color-gray-50) }(screens · 0,2,0)가 같은 값으로 되돌린다 — .btn-strong 요소는 전부 .btn · primary/secondary 아님 / 요소 호환(type) 경쟁이지만 PeriodCalendarPopover 의 달 이동 버튼 — .btn 없음(.btn 은 팝오버 발) — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 PeriodCalendarPopover 의 단위 세그먼트 — className 은 on 뿐 — 같은 요소에 걸리지 않는다 / 요소 호환(type) 경쟁이지만 VerificationAction 의 메뉴 항목 — className 없음(.btn 은 확인 모달 안) — 같은 요소에 걸리지 않는다 |
| added | components/upload/upload.css:311 `.btn-strong:hover` background | 편차 이동 — 오늘 .btn:where(:not(.btn-primary,.btn-secondary)):hover(0,2,0)가 .btn-strong 배경(0,1,0)을 이겨 hover 배경이 gray-50 이다. hover 규칙이 primitives 층으로 내려가면 .btn-strong(screens)이 이기므로 같은 값을 화면 규칙으로 둔다(.btn-strong 요소는 전부 .btn · primary/secondary 아님) |
| added | components/upload/upload.css:91 `.up-card` border-style | 종전 .up-card border 단축의 모양(solid) — 값 무변 |
| added | components/upload/upload.css:91 `.up-card` border-width | 종전 .up-card border 단축의 굵기(1px) — 값 무변 |
| added | components/members/members.css:61 `.memtbl .chip--off` margin-left | 범위 선택자로 옮긴 편차 — 값 6px 는 기본값 .chip margin-left 와 같다 · 걸리는 요소는 구성원 표의 비활성 칩 하나(새는 문맥 없음) |
| deleted-live | components/upload/upload.css:307 `.btn-sm` font-size | 오늘 죽음 — .btn-sm 요소는 전부 .btn 을 함께 가진다 · 셸 끝 .btn font-size(뒤 순서 · 동률)가 덮었다 |
| deleted-live | components/upload/upload.css:307 `.btn-sm` padding | 오늘 죽음 — .btn-sm 요소는 전부 .btn 을 함께 가진다(TSX 전수 36곳) · 셸 끝 .btn padding(뒤 순서 · 동률)이 덮었다(억눌린 작은 버튼 · 후속) |
| deleted-live | components/upload/upload.css:86 `.up-card` border | 색만 죽어 있던 단축 선언을 굵기·모양으로 나눔 — .up-card 요소는 늘 .card(FileDropCard) · 테두리 색은 셸 끝 .card border-color(뒤 순서)가 이겼다 · 굵기·모양은 .up-card { border-width; border-style } 로 남김 |
| deleted-live | components/members/members.css:108 `.chip--off` margin-left | 범위 선택자로 옮김 — 같은 값을 .memtbl .chip--off(members.css)에 둔다(spec 칩 수식자 규칙 · 레이아웃 선언은 화면 범위) · 요소는 .memtbl 표 안에만 있다(MemberPermissionGrid) |
| deleted-live | components/members/members.css:105 `.chip--off` background | 오늘 죽음 — .chip--off 요소는 .chip 을 함께 가진다(MemberPermissionGrid 1곳 chip chip--off) · upload.css .chip background #eef2f7(뒤 순서 · 동률)이 덮었다(보인 적 없는 gray-50 · 후속 판정) |
| deleted-live | components/members/members.css:71 `.memtbl td` padding | 오늘 죽음 — 구성원 표는 늘 tbl memtbl · 셸 끝 .tbl td padding 10px 12px(같은 0,1,1 · 뒤 순서)이 덮었다 |
| deleted-live | components/members/members.css:66 `.btn-ghost` background | 오늘 죽음 — .btn-ghost 요소는 전부 .btn 을 함께 가진다(TSX 전수 btn btn-ghost …) · upload.css .btn background(뒤 순서 · 동률)가 덮었다 |

## 삭제 (오늘 죽음 증명)

| 파일:행 | 선택자 인자 | 미디어 | 속성 | 값 | 증명(이기는 경쟁) |
|---|---|---|---|---|---|
| components/catalog/catalog.css:21 | `.tblwrap` | - | max-height | `calc(100vh - 232px)` | `.tblwrap` shell/shell.css:437 max-height=`none` |
| components/catalog/catalog.css:21 | `.tblwrap` | - | max-height | `calc(100dvh - 232px)` | `.tblwrap` shell/shell.css:437 max-height=`none` |
| components/catalog/catalog.css:22 | `.tbl` | - | font-size | `var(--text-body-sm)` | `.tbl` shell/shell.css:438 font-size=`var(--text-body-sm)` |
| components/catalog/catalog.css:24 | `.tbl th` | - | color | `var(--color-gray-500)` | `.tbl th` shell/shell.css:439 color=`var(--color-text-muted)` |
| components/catalog/catalog.css:24 | `.tbl th` | - | font-weight | `700` | `.tbl th` shell/shell.css:439 font-weight=`600` |
| components/catalog/catalog.css:24 | `.tbl th` | - | letter-spacing | `0.05em` | `.tbl th` shell/shell.css:439 letter-spacing=`0` |
| components/catalog/catalog.css:30 | `.tbl td` | - | padding | `13px 14px` | `.tbl td` shell/shell.css:440 padding=`10px 12px` |
| components/catalog/catalog.css:125 | `.chip` | - | display | `inline-flex` | `.chip` components/project/project.css:314 display=`inline-block` |
| components/catalog/catalog.css:125 | `.chip` | - | align-items | `center` | `.chip` components/members/members.css:84 align-items=`center` |
| components/catalog/catalog.css:125 | `.chip` | - | gap | `5px` | `.chip` components/upload/upload.css:256 gap=`4px` |
| components/catalog/catalog.css:125 | `.chip` | - | height | `21px` | `.chip` components/members/members.css:85 height=`24px` |
| components/catalog/catalog.css:125 | `.chip` | - | border-radius | `var(--radius-pill)` | `.chip` components/project/project.css:316 border-radius=`999px` |
| components/catalog/catalog.css:125 | `.chip` | - | padding | `0 9px` | `.chip` components/project/project.css:315 padding=`1px 7px` |
| components/catalog/catalog.css:125 | `.chip` | - | font-size | `13px` | `.chip` components/project/project.css:318 font-size=`13px` |
| components/catalog/catalog.css:125 | `.chip` | - | white-space | `nowrap` | `.chip` components/members/members.css:90 white-space=`nowrap` |
| components/catalog/catalog.css:126 | `.chip--neutral` | - | background | `var(--color-gray-100)` | `.chip--neutral` shell/shell.css:475 background=`var(--color-gray-100)` |
| components/catalog/catalog.css:126 | `.chip--neutral` | - | color | `var(--color-gray-700)` | `.chip--neutral` shell/shell.css:475 color=`var(--color-gray-700)` |
| components/catalog/catalog.css:127 | `.chip--warning` | - | background | `var(--color-warning-50)` | `.chip--warning` shell/shell.css:476 background=`var(--color-warning-50)` |
| components/catalog/catalog.css:127 | `.chip--warning` | - | color | `var(--color-warning-600)` | `.chip--warning` shell/shell.css:476 color=`var(--color-warning-600)` |
| components/project/project.css:314 | `.chip` | - | display | `inline-block` | `.chip` components/members/members.css:83 display=`inline-flex` |
| components/project/project.css:315 | `.chip` | - | padding | `1px 7px` | `.chip` components/members/members.css:86 padding=`0 9px` |
| components/project/project.css:316 | `.chip` | - | border-radius | `999px` | `.chip` components/members/members.css:87 border-radius=`999px` |
| components/project/project.css:318 | `.chip` | - | font-size | `13px` | `.chip` components/members/members.css:89 font-size=`var(--text-caption)` |
| components/members/members.css:6 | `.card` | - | background | `var(--color-surface)` | `.card` shell/shell.css:436 background=`var(--color-surface)` |
| components/members/members.css:8 | `.card` | - | border-radius | `var(--radius-md)` | `.card` shell/shell.css:436 border-radius=`var(--radius-lg)` |
| components/members/members.css:13 | `.card-h` | - | gap | `10px` | `.card-h` shell/shell.css:453 gap=`12px` |
| components/members/members.css:14 | `.card-h` | - | padding | `14px 18px` | `:is(.card-h, .card-b)` shell/shell.css:451 padding=`20px var(--space-card)` |
| components/members/members.css:19 | `.card-h h3` | - | font-size | `var(--text-body)` | `.card-h h3` shell/shell.css:452 font-size=`var(--text-section)` |
| components/members/members.css:38 | `.card-b` | - | padding | `6px 18px` | `:is(.card-h, .card-b)` shell/shell.css:451 padding=`20px var(--space-card)` |
| components/members/members.css:48 | `.btn` | - | padding | `0 12px` | `.btn` components/upload/upload.css:306 padding=`8px 14px` |
| components/members/members.css:49 | `.btn` | - | border-radius | `var(--radius-sm)` | `.btn` components/upload/upload.css:306 border-radius=`8px` |
| components/members/members.css:50 | `.btn` | - | border | `1px solid var(--color-border-strong)` | `.btn` components/upload/upload.css:306 border=`1px solid var(--up-line)` |
| components/members/members.css:51 | `.btn` | - | background | `var(--color-surface)` | `.btn` components/upload/upload.css:306 background=`var(--color-surface)` |
| components/members/members.css:52 | `.btn` | - | font-family | `inherit` | `.btn` components/upload/upload.css:306 font=`inherit` |
| components/members/members.css:53 | `.btn` | - | font-size | `var(--text-body-sm)` | `.btn` components/upload/upload.css:306 font=`inherit` |
| components/members/members.css:54 | `.btn` | - | font-weight | `600` | `.btn` components/upload/upload.css:306 font=`inherit` |
| components/members/members.css:56 | `.btn` | - | cursor | `pointer` | `.btn` components/upload/upload.css:306 cursor=`pointer` |
| components/members/members.css:62 | `.btn-primary` | - | background | `var(--color-primary-600)` | `.btn-primary` components/upload/upload.css:308 background=`var(--color-primary-600)` |
| components/members/members.css:63 | `.btn-primary` | - | border-color | `var(--color-primary-600)` | `.btn-primary` components/upload/upload.css:308 border-color=`var(--up-ink)` |
| components/members/members.css:64 | `.btn-primary` | - | color | `var(--color-white)` | `.btn-primary` components/upload/upload.css:308 color=`var(--color-on-primary)` |
| components/members/members.css:66 | `.btn-ghost` | - | border-color | `transparent` | `.btn-ghost` components/upload/upload.css:309 border-color=`transparent` |
| components/members/members.css:66 | `.btn-ghost` | - | background | `transparent` | **없음** |
| components/members/members.css:71 | `.memtbl td` | - | padding | `10px 8px` | **없음** |
| components/members/members.css:83 | `.chip` | - | display | `inline-flex` | `.chip` components/upload/upload.css:256 display=`inline-flex` |
| components/members/members.css:84 | `.chip` | - | align-items | `center` | `.chip` components/upload/upload.css:256 align-items=`center` |
| components/members/members.css:86 | `.chip` | - | padding | `0 9px` | `.chip` components/upload/upload.css:256 padding=`2px 10px` |
| components/members/members.css:87 | `.chip` | - | border-radius | `999px` | `.chip` components/upload/upload.css:256 border-radius=`9999px` |
| components/members/members.css:88 | `.chip` | - | background | `var(--color-surface-hover)` | `.chip` components/upload/upload.css:256 background=`#eef2f7` |
| components/members/members.css:89 | `.chip` | - | font-size | `var(--text-caption)` | `.chip` components/upload/upload.css:256 font-size=`13px` |
| components/members/members.css:105 | `.chip--off` | - | background | `var(--color-gray-50)` | **없음** |
| components/members/members.css:108 | `.chip--off` | - | margin-left | `6px` | **없음** |
| components/upload/upload.css:86 | `.up-card` | - | border | `1px solid var(--up-line)` | **없음** |
| components/upload/upload.css:251 | `.inp` | - | padding | `8px 10px` | `:is(.inp, .sel)` shell/shell.css:447 padding=`10px 12px` |
| components/upload/upload.css:251 | `.inp` | - | border | `1px solid var(--up-line)` | `:is(.inp, .sel)` shell/shell.css:447 border=`1px solid var(--color-border-control)` |
| components/upload/upload.css:251 | `.inp` | - | border-radius | `8px` | `:is(.inp, .sel)` shell/shell.css:447 border-radius=`var(--radius-sm)` |
| components/upload/upload.css:251 | `.inp` | - | font | `inherit` | `:is(.inp, .sel)` shell/shell.css:447 font=`inherit` |
| components/upload/upload.css:251 | `.sel` | - | padding | `8px 10px` | `:is(.inp, .sel)` shell/shell.css:447 padding=`10px 12px` |
| components/upload/upload.css:251 | `.sel` | - | border | `1px solid var(--up-line)` | `:is(.inp, .sel)` shell/shell.css:447 border=`1px solid var(--color-border-control)` |
| components/upload/upload.css:251 | `.sel` | - | border-radius | `8px` | `:is(.inp, .sel)` shell/shell.css:447 border-radius=`var(--radius-sm)` |
| components/upload/upload.css:251 | `.sel` | - | font | `inherit` | `:is(.inp, .sel)` shell/shell.css:447 font=`inherit` |
| components/upload/upload.css:306 | `.btn` | - | border-radius | `8px` | `.btn` shell/shell.css:442 border-radius=`var(--radius-sm)` |
| components/upload/upload.css:306 | `.btn` | - | padding | `8px 14px` | `.btn` shell/shell.css:442 padding=`10px 18px` |
| components/upload/upload.css:307 | `.btn-sm` | - | padding | `6px 10px` | **없음** |
| components/upload/upload.css:307 | `.btn-sm` | - | font-size | `13px` | **없음** |
| components/upload/upload.css:308 | `.btn-primary` | - | background | `var(--color-primary-600)` | `.btn-primary` shell/shell.css:443 background=`var(--color-primary-600)` |
| components/upload/upload.css:308 | `.btn-primary` | - | color | `var(--color-on-primary)` | `.btn-primary` shell/shell.css:443 color=`var(--color-on-primary)` |
| components/upload/upload.css:308 | `.btn-primary` | - | border-color | `var(--up-ink)` | `.btn-primary` shell/shell.css:443 border-color=`var(--color-primary-600)` |

## 옮겨짐

| 원래 | 선택자 인자 | 미디어 | 속성 | 값 | 새 자리 | 층 |
|---|---|---|---|---|---|---|
| components/catalog/catalog.css:21 | `.tblwrap` | - | overflow | `auto` | shell/primitives.css:95 | primitives |
| components/catalog/catalog.css:21 | `.tblwrap` | - | -webkit-overflow-scrolling | `touch` | shell/primitives.css:95 | primitives |
| components/catalog/catalog.css:22 | `.tbl` | - | width | `100%` | shell/primitives.css:96 | primitives |
| components/catalog/catalog.css:22 | `.tbl` | - | min-width | `940px` | shell/primitives.css:96 | primitives |
| components/catalog/catalog.css:22 | `.tbl` | - | border-collapse | `collapse` | shell/primitives.css:96 | primitives |
| components/catalog/catalog.css:125 | `.chip` | - | font-weight | `600` | shell/primitives.css:57 | primitives |
| components/catalog/catalog.css:125 | `.chip` | - | line-height | `1` | shell/primitives.css:58 | primitives |
| components/project/project.css:317 | `.chip` | - | border | `1px solid var(--color-border)` | shell/primitives.css:53 | primitives |
| components/project/project.css:319 | `.chip` | - | margin-left | `6px` | shell/primitives.css:60 | primitives |
| components/members/members.css:7 | `.card` | - | border | `1px solid var(--color-border)` | shell/primitives.css:74 | primitives |
| components/members/members.css:11 | `.card-h` | - | display | `flex` | shell/primitives.css:80 | primitives |
| components/members/members.css:12 | `.card-h` | - | align-items | `center` | shell/primitives.css:81 | primitives |
| components/members/members.css:15 | `.card-h` | - | border-bottom | `1px solid var(--color-border)` | shell/primitives.css:85 | primitives |
| components/members/members.css:18 | `.card-h h3` | - | margin | `0` | shell/primitives.css:87 | primitives |
| components/members/members.css:47 | `.btn` | - | height | `32px` | shell/primitives.css:15 | primitives |
| components/members/members.css:55 | `.btn` | - | color | `var(--color-text)` | shell/primitives.css:23 | primitives |
| components/members/members.css:57 | `.btn` | - | transition | `background var(--ease), border-color var(--ease)` | shell/primitives.css:25 | primitives |
| components/members/members.css:60 | `.btn:where(:not(.btn-primary, .btn-secondary)):hover` | - | background | `var(--color-gray-50)` | shell/primitives.css:28 | primitives |
| components/members/members.css:85 | `.chip` | - | height | `24px` | shell/primitives.css:51 | primitives |
| components/members/members.css:90 | `.chip` | - | white-space | `nowrap` | shell/primitives.css:59 | primitives |
| components/members/members.css:106 | `.chip--off` | - | border | `1px solid var(--color-border)` | shell/primitives.css:62 | primitives |
| components/members/members.css:107 | `.chip--off` | - | color | `var(--color-text-muted)` | shell/primitives.css:62 | primitives |
| components/members/members.css:122 | `.modal-back` | - | position | `fixed` | shell/primitives.css:110 | primitives |
| components/members/members.css:123 | `.modal-back` | - | inset | `0` | shell/primitives.css:111 | primitives |
| components/members/members.css:124 | `.modal-back` | - | display | `flex` | shell/primitives.css:112 | primitives |
| components/members/members.css:125 | `.modal-back` | - | align-items | `center` | shell/primitives.css:113 | primitives |
| components/members/members.css:126 | `.modal-back` | - | justify-content | `center` | shell/primitives.css:114 | primitives |
| components/members/members.css:127 | `.modal-back` | - | background | `var(--color-overlay)` | shell/primitives.css:115 | primitives |
| components/members/members.css:128 | `.modal-back` | - | z-index | `200` | shell/primitives.css:116 | primitives |
| components/members/members.css:135 | `.modal` | - | width | `100%` | shell/primitives.css:119 | primitives |
| components/members/members.css:136 | `.modal` | - | background | `var(--color-surface)` | shell/primitives.css:120 | primitives |
| components/members/members.css:137 | `.modal` | - | border-radius | `var(--radius-md)` | shell/primitives.css:121 | primitives |
| components/members/members.css:138 | `.modal` | - | box-shadow | `var(--shadow-sm)` | shell/primitives.css:122 | primitives |
| components/members/members.css:140 | `.modal--dialog` | - | max-width | `520px` | shell/primitives.css:125 | primitives |
| components/members/members.css:140 | `.modal--dialog` | - | max-height | `calc(100dvh - 32px)` | shell/primitives.css:126 | primitives |
| components/members/members.css:140 | `.modal--dialog` | - | overflow-y | `auto` | shell/primitives.css:127 | primitives |
| components/members/members.css:141 | `.modal-h` | - | padding | `16px 18px` | shell/primitives.css:134 | primitives |
| components/members/members.css:141 | `.modal-h` | - | border-bottom | `1px solid var(--color-border)` | shell/primitives.css:134 | primitives |
| components/members/members.css:143 | `.modal-b` | - | padding | `16px 18px` | shell/primitives.css:135 | primitives |
| components/members/members.css:146 | `.modal-f` | - | display | `flex` | shell/primitives.css:137 | primitives |
| components/members/members.css:147 | `.modal-f` | - | justify-content | `flex-end` | shell/primitives.css:138 | primitives |
| components/members/members.css:148 | `.modal-f` | - | gap | `8px` | shell/primitives.css:139 | primitives |
| components/members/members.css:149 | `.modal-f` | - | padding | `14px 18px` | shell/primitives.css:140 | primitives |
| components/members/members.css:150 | `.modal-f` | - | border-top | `1px solid var(--color-border)` | shell/primitives.css:141 | primitives |
| components/upload/upload.css:256 | `.chip` | - | display | `inline-flex` | shell/primitives.css:48 | primitives |
| components/upload/upload.css:256 | `.chip` | - | align-items | `center` | shell/primitives.css:49 | primitives |
| components/upload/upload.css:256 | `.chip` | - | gap | `4px` | shell/primitives.css:50 | primitives |
| components/upload/upload.css:256 | `.chip` | - | border-radius | `9999px` | shell/primitives.css:54 | primitives |
| components/upload/upload.css:256 | `.chip` | - | padding | `2px 10px` | shell/primitives.css:52 | primitives |
| components/upload/upload.css:256 | `.chip` | - | background | `#eef2f7` | shell/primitives.css:55 | primitives |
| components/upload/upload.css:256 | `.chip` | - | font-size | `13px` | shell/primitives.css:56 | primitives |
| components/upload/upload.css:306 | `.btn` | - | border | `1px solid var(--up-line)` | shell/primitives.css:18 | primitives |
| components/upload/upload.css:306 | `.btn` | - | background | `var(--color-surface)` | shell/primitives.css:20 | primitives |
| components/upload/upload.css:306 | `.btn` | - | font | `inherit` | shell/primitives.css:21 | primitives |
| components/upload/upload.css:306 | `.btn` | - | cursor | `pointer` | shell/primitives.css:24 | primitives |
| components/upload/upload.css:309 | `.btn-ghost` | - | border-color | `transparent` | shell/primitives.css:29 | primitives |
| components/approval/approval.css:16 | `.chip--verified` | - | color | `var(--color-success-600)` | shell/primitives.css:63 | primitives |
| components/approval/approval.css:16 | `.chip--verified` | - | background | `var(--color-success-50)` | shell/primitives.css:63 | primitives |
| shell/shell.css:11 | `*` | - | box-sizing | `border-box` | shell/base.css:7 | base |
| shell/shell.css:101 | `button` | - | font-family | `inherit` | shell/base.css:10 | base |
| shell/shell.css:101 | `button` | - | letter-spacing | `inherit` | shell/base.css:10 | base |
| shell/shell.css:101 | `input` | - | font-family | `inherit` | shell/base.css:10 | base |
| shell/shell.css:101 | `input` | - | letter-spacing | `inherit` | shell/base.css:10 | base |
| shell/shell.css:101 | `select` | - | font-family | `inherit` | shell/base.css:10 | base |
| shell/shell.css:101 | `select` | - | letter-spacing | `inherit` | shell/base.css:10 | base |
| shell/shell.css:101 | `textarea` | - | font-family | `inherit` | shell/base.css:10 | base |
| shell/shell.css:101 | `textarea` | - | letter-spacing | `inherit` | shell/base.css:10 | base |
| shell/shell.css:102 | `button` | - | font-size | `var(--text-body-sm)` | shell/base.css:11 | base |
| shell/shell.css:104 | `:where(button, a, input, select, textarea):focus-visible` | - | outline | `2px solid var(--color-primary-600)` | shell/base.css:13 | base |
| shell/shell.css:105 | `:where(button, a, input, select, textarea):focus-visible` | - | outline-offset | `3px` | shell/base.css:14 | base |
| shell/shell.css:416 | `input` | (max-width: 640px) | font-size | `16px` | shell/base.css:19 | base |
| shell/shell.css:416 | `select` | (max-width: 640px) | font-size | `16px` | shell/base.css:19 | base |
| shell/shell.css:416 | `textarea` | (max-width: 640px) | font-size | `16px` | shell/base.css:19 | base |
| shell/shell.css:436 | `.card` | - | box-shadow | `none` | shell/primitives.css:77 | primitives |
| shell/shell.css:436 | `.card` | - | background | `var(--color-surface)` | shell/primitives.css:73 | primitives |
| shell/shell.css:436 | `.card` | - | border-color | `var(--color-border-strong)` | shell/primitives.css:75 | primitives |
| shell/shell.css:436 | `.card` | - | border-radius | `var(--radius-lg)` | shell/primitives.css:76 | primitives |
| shell/shell.css:437 | `.tblwrap` | - | max-height | `none` | shell/primitives.css:95 | primitives |
| shell/shell.css:438 | `.tbl` | - | font-size | `var(--text-body-sm)` | shell/primitives.css:96 | primitives |
| shell/shell.css:438 | `.tbl` | - | line-height | `1.5` | shell/primitives.css:96 | primitives |
| shell/shell.css:439 | `.tbl th` | - | color | `var(--color-text-muted)` | shell/primitives.css:97 | primitives |
| shell/shell.css:439 | `.tbl th` | - | font-weight | `600` | shell/primitives.css:97 | primitives |
| shell/shell.css:439 | `.tbl th` | - | letter-spacing | `0` | shell/primitives.css:97 | primitives |
| shell/shell.css:440 | `.tbl td` | - | padding | `10px 12px` | shell/primitives.css:98 | primitives |
| shell/shell.css:441 | `.chip--lineage` | - | background | `var(--color-gray-100)` | shell/primitives.css:64 | primitives |
| shell/shell.css:441 | `.chip--lineage` | - | color | `var(--color-text-muted)` | shell/primitives.css:64 | primitives |
| shell/shell.css:442 | `.btn` | - | min-height | `var(--control-height)` | shell/primitives.css:16 | primitives |
| shell/shell.css:442 | `.btn` | - | padding | `10px 18px` | shell/primitives.css:17 | primitives |
| shell/shell.css:442 | `.btn` | - | font-size | `var(--text-body-sm)` | shell/primitives.css:22 | primitives |
| shell/shell.css:442 | `.btn` | - | border-radius | `var(--radius-sm)` | shell/primitives.css:19 | primitives |
| shell/shell.css:443 | `.btn-primary` | - | background | `var(--color-primary-600)` | shell/primitives.css:30 | primitives |
| shell/shell.css:443 | `.btn-primary` | - | color | `var(--color-on-primary)` | shell/primitives.css:30 | primitives |
| shell/shell.css:443 | `.btn-primary` | - | border-color | `var(--color-primary-600)` | shell/primitives.css:30 | primitives |
| shell/shell.css:444 | `.btn-secondary` | - | background | `var(--color-surface)` | shell/primitives.css:31 | primitives |
| shell/shell.css:444 | `.btn-secondary` | - | color | `var(--color-text)` | shell/primitives.css:31 | primitives |
| shell/shell.css:444 | `.btn-secondary` | - | border-color | `var(--color-border-control)` | shell/primitives.css:31 | primitives |
| shell/shell.css:445 | `.btn-primary:active` | - | background | `var(--color-primary-700)` | shell/primitives.css:32 | primitives |
| shell/shell.css:447 | `.inp` | - | min-height | `var(--control-height)` | shell/primitives.css:37 | primitives |
| shell/shell.css:447 | `.sel` | - | min-height | `var(--control-height)` | shell/primitives.css:37 | primitives |
| shell/shell.css:447 | `.inp` | - | padding | `10px 12px` | shell/primitives.css:37 | primitives |
| shell/shell.css:447 | `.sel` | - | padding | `10px 12px` | shell/primitives.css:37 | primitives |
| shell/shell.css:447 | `.inp` | - | border | `1px solid var(--color-border-control)` | shell/primitives.css:37 | primitives |
| shell/shell.css:447 | `.sel` | - | border | `1px solid var(--color-border-control)` | shell/primitives.css:37 | primitives |
| shell/shell.css:447 | `.inp` | - | border-radius | `var(--radius-sm)` | shell/primitives.css:37 | primitives |
| shell/shell.css:447 | `.sel` | - | border-radius | `var(--radius-sm)` | shell/primitives.css:37 | primitives |
| shell/shell.css:447 | `.inp` | - | background | `var(--color-surface)` | shell/primitives.css:37 | primitives |
| shell/shell.css:447 | `.sel` | - | background | `var(--color-surface)` | shell/primitives.css:37 | primitives |
| shell/shell.css:447 | `.inp` | - | color | `var(--color-text)` | shell/primitives.css:37 | primitives |
| shell/shell.css:447 | `.sel` | - | color | `var(--color-text)` | shell/primitives.css:37 | primitives |
| shell/shell.css:447 | `.inp` | - | font | `inherit` | shell/primitives.css:37 | primitives |
| shell/shell.css:447 | `.sel` | - | font | `inherit` | shell/primitives.css:37 | primitives |
| shell/shell.css:451 | `.card-h` | - | padding | `20px var(--space-card)` | shell/primitives.css:84 | primitives |
| shell/shell.css:451 | `.card-b` | - | padding | `20px var(--space-card)` | shell/primitives.css:88 | primitives |
| shell/shell.css:452 | `.card-h h3` | - | font-size | `var(--text-section)` | shell/primitives.css:87 | primitives |
| shell/shell.css:452 | `.card-h h3` | - | line-height | `1.5` | shell/primitives.css:87 | primitives |
| shell/shell.css:452 | `.card-h h3` | - | font-weight | `600` | shell/primitives.css:87 | primitives |
| shell/shell.css:453 | `.card-h` | - | gap | `12px` | shell/primitives.css:82 | primitives |
| shell/shell.css:453 | `.card-h` | - | flex-wrap | `wrap` | shell/primitives.css:83 | primitives |
| shell/shell.css:455 | `.modal--dialog` | - | border | `1px solid var(--color-border-strong)` | shell/primitives.css:128 | primitives |
| shell/shell.css:455 | `.modal--dialog` | - | border-radius | `var(--radius-lg)` | shell/primitives.css:129 | primitives |
| shell/shell.css:455 | `.modal--dialog` | - | box-shadow | `none` | shell/primitives.css:130 | primitives |
| shell/shell.css:455 | `.modal--dialog` | - | padding | `var(--space-card)` | shell/primitives.css:131 | primitives |
| shell/shell.css:456 | `.modal--dialog:has(.modal-h)` | - | padding | `0` | shell/primitives.css:133 | primitives |
| shell/shell.css:468 | `.inp` | (max-width: 640px) | font-size | `16px` | shell/primitives.css:39 | primitives |
| shell/shell.css:468 | `.sel` | (max-width: 640px) | font-size | `16px` | shell/primitives.css:39 | primitives |
| shell/shell.css:475 | `.chip--neutral` | - | background | `var(--color-gray-100)` | shell/primitives.css:65 | primitives |
| shell/shell.css:475 | `.chip--neutral` | - | color | `var(--color-gray-700)` | shell/primitives.css:65 | primitives |
| shell/shell.css:476 | `.chip--warning` | - | background | `var(--color-warning-50)` | shell/primitives.css:66 | primitives |
| shell/shell.css:476 | `.chip--warning` | - | color | `var(--color-warning-600)` | shell/primitives.css:66 | primitives |
| shell/shell.css:477 | `.chip:where(:not([class*="chip--"]))` | - | background | `var(--color-surface-alt)` | shell/primitives.css:67 | primitives |
| shell/shell.css:477 | `.chip:where(:not([class*="chip--"]))` | - | color | `var(--color-text-muted)` | shell/primitives.css:67 | primitives |
| shell/shell.css:479 | `.table-scroll-hint` | - | display | `none` | shell/primitives.css:99 | primitives |
| shell/shell.css:481 | `.table-scroll-hint` | (max-width: 1100px) | display | `block` | shell/primitives.css:101 | primitives |
| shell/shell.css:481 | `.table-scroll-hint` | (max-width: 1100px) | margin | `0` | shell/primitives.css:101 | primitives |
| shell/shell.css:481 | `.table-scroll-hint` | (max-width: 1100px) | padding | `12px 16px` | shell/primitives.css:101 | primitives |
| shell/shell.css:481 | `.table-scroll-hint` | (max-width: 1100px) | font-size | `var(--text-caption)` | shell/primitives.css:101 | primitives |
| shell/shell.css:481 | `.table-scroll-hint` | (max-width: 1100px) | color | `var(--color-text-muted)` | shell/primitives.css:101 | primitives |

## 문제

| 종류 | 내용 |
|---|---|
