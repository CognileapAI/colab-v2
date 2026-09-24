# 디자인 구조 P2b 결과 — 프리미티브 단일 소유(`primitives.css`) · `base` 층 · 게이트 e

spec: `dev-package/prd/specs/S-DESIGN-STRUCTURE-P2B-20260924.md` · 조사: `p2/design-system-map.md §2` · 선행: `p2a/report.md` · `p3/report.md`

착수 HEAD `60d63683` · task `db68dcd9c7224b1db66052498645e56a` · 레인 1(직렬)

## 결론

- 6계열(btn → field → chip → card → table → modal)을 전부 옮겼다. 기본값 선언 **114**(btn 20 · field 8 · chip 25 · card 16 · table 18 · modal 27)가 `frontend/src/shell/primitives.css`(`@layer primitives`) 한 파일에 있고, 원소 규칙 5는 `frontend/src/shell/base.css`(`@layer base`)에 있다. `shell.css` 끝 임시 블록의 프리미티브 규칙은 0이다.
- 게이트 e: 착수 전체 목록 측정 **48**(btn 12 · field 4 · chip 12 · card 6 · table 6 · modal 8) → 최종 **0(면제 0)** · 목록 22클래스. selftest 19 → **23건**.
- 토큰 별칭 **9/9 치환**(참조 73) · 이름 삭제 9.
- 시각 변경 0 — `visual:diff` **196 captures · red 0 · strict px 0 · exit 0**(후보 HEAD `f0d8baf0` · `gitDirty` false · 다시 빌드).
- 계산값 전수 대조 — 0단계 · 계열마다 · 토큰+후속, 9회 모두 **196 페이지 · 26962 항목 · 차이 0**.
- 상태 강제 계측 **43건 전후 동일**(P2a 16 + `.pj-seg button.on` focus-visible 1 + 계열 대표 6 × 4상태 24 + `.btn-strong:hover`·`.btn-secondary:disabled` 2). 비폼 요소의 `:disabled` 4건은 상태가 성립하지 않는다([미측정] · 아래).
- 게이트 `gates/run.sh task` → **green 5 / red(판정) 0 / red(준비) 0 · exit 0**.
- 판정 필요 1: `cascade-map.mjs verify` 를 P2b 용으로 일반화했다 — spec 은 P2a 도구를 그대로 쓴다고 적었지만 그 `verify` 는 `design-system.css` 전용이라 착수 트리에서 쓸 수 없다(「spec 과 다르게 한 점」 1).

## 진행 상태

| 단계 · 계열 | 상태 | 커밋 |
|---|---|---|
| 1 착수 캡처 `p2b-before` · 게이트 e 전체 목록 측정 | 완료 | — |
| 2 게이트 e · selftest 23 | 완료 | `2a3ffe8c` |
| 3 0단계 `base` 층 · verify 일반화 | 완료 | `37344117` |
| 4 btn | 완료 | `bdf62a31` |
| 4 field | 완료 | `3def802e` |
| 4 chip | 완료 | `7cf498a2` |
| 4 card | 완료 | `d425e667` |
| 4 table | 완료 | `2468afa0` |
| 4 modal | 완료 | `ba2e214c` |
| 5 토큰 9/9 | 완료 | `3bc7f018` |
| 6 P2a 후속 | 완료(같은 조건 미디어 블록은 이웃한 3곳만 합침) | `f0d8baf0` |
| 7 증명(캡처 · 계산값 · 상태) | 완료 | 이 커밋 |
| 8 게이트 | 완료 — green 5 · exit 0 | — |
| 9 보고서 | 이 문서 | 이 커밋 |

## 단계 1 — 착수

- `npm run visual:capture -- --label p2b-before`(audit 빌드 포함) · 07:00:21~07:08:13 UTC · PNG 196장. 빌드는 착수 트리(`60d63683`) 내용이다. `index.json` 의 `gitHead` `2a3ffe8c` 는 캡처 도중 커밋한 게이트 e(`frontend/src` 무변)다.
- 같은 빌드를 `frontend/.visual/p2b-dist-before/` 에 두고 계산값 대조·상태 계측의 「전」 쪽으로 썼다(로컬 · 추적 안 함).
- 게이트 e 착수 측정(전체 목록 22클래스 · 커밋하지 않음): **48** — 선택자 인자 단위.

| 계열 | 착수 맨 정의(게이트 e) | 파일별 | 조사 §2 정의 곳수 |
|---|---:|---|---:|
| btn | 12 | members 4 · upload 4 · shell 4 | 40 |
| field | 4 | upload 2 · shell 2 | 63 |
| chip | 12 | approval 1 · catalog 3 · members 2 · project 1 · upload 1 · shell 4 | 26 |
| card | 6 | members 3 · shell 3 | 38 |
| table | 6 | catalog 2 · shell 4 | 106 |
| modal | 8 | members 6 · shell 2 | 115 |
| **계** | **48** | | **388** |

- 조사 §2 곳수는 P2a 이전(보정 층 포함)에 문맥 규칙(`.memgrid .card-b` · `.pj-table td` …)과 별 계열 이름(`.login-input` · `.pj-modal*` · `.account-table` …)까지 센 수라 「맨 정의」와 단위가 다르다. 맨 정의만 보면 조사의 기반 서술(btn 기반이 members·upload 두 화면 파일 · modal 기반은 members 에만 · 문맥 없는 `.chip` 기반 5곳 · `.card` 기반이 공용에 없음)과 착수 측정이 맞는다. 조사 곳수 중 이번 범위 밖(별 계열 이름 · 탭 · 문맥 규칙)은 옮기지 않았다(우려 2 · 편차 무변).

## 단계 2 — 게이트 e(ⓐ)

- 판정부 `frontend/scripts/design-lint.mjs` · 셸 `gates/tools/frontend-design-lint.sh`. 목록 `gates/fixtures/frontend-design-lint/primitives.txt`(env `COLAB_DESIGN_LINT_PRIMITIVES` · `--primitives`) · 면제 `primitives-exempt.txt`(env `COLAB_DESIGN_LINT_PRIMITIVES_EXEMPT` · `--primitives-exempt` · `파일 · 선택자 · 사유`). 둘 다 부재 = 78.
- 규칙: `primitives.css` 밖 CSS 의 선택자 인자마다 `:is()`/`:where()` 를 펼쳐 compound 하나가 목록 클래스(+가상 클래스/요소 · 속성)만이면 1건. `:not()`·`:has()` 인자는 보지 않는다 · 목록 밖 클래스·요소·id 와 섞인 compound 와 조상·자손 문맥은 허용. `primitives.css`·`base.css` 안 `!important` 1건. 면제 사유 없음·낡음 red. 요약줄 끝 `프리미티브 맨 정의 밖 e(면제 m)` · 계수 줄 `e e_bare e_important e_holes e_exempt e_exempted_hits primitives`.
- red 확인: 새 selftest 케이스를 종전 판정부(`60d63683`)로 돌림 → exit 1(ⓣ 요약줄 e 없음 · ⓤ·ⓥ 「red 여야 하는데 통과했다」). 새 판정부 → `검사 23건 전건 기대대로 (green 5 · red 13 · red(준비) 5)`.
- 새 케이스 4: ⓣ `green-e`(맨 정의는 `primitives.css` · 문맥·섞인 compound·`button.btn`·`:not()`/`:has()` 인자·목록 밖 이름 · 사유 있는 면제 1건이 실제 맨 정의에 걸림) · ⓤ `red-e`(맨 정의 · 상태 맨 정의 · `:is()` 펼침 · 사유 없는 면제는 면제 안 함 · 낡은 면제 → `e=6 e_bare=4 e_important=0 e_holes=2`) · ⓥ `red-e-important`(→ `e=2 e_important=2` · 화면 파일의 `!important` 는 대상 밖) · ⓦ 목록 부재 78. 기존 트리 16개에 빈 목록·면제 파일(게이트가 두 파일에 fail-closed). `gates/README.md` 두 행.
- 목록은 빈 채로 시작해 계열 커밋마다 그 계열만 더했다 — 모든 계열 경계에서 `frontend-design-lint` green · 최종 `프리미티브 맨 정의 밖 0(면제 0)` · `primitives=22`.

## 단계 3 — 0단계 `base` 층

- `base.css` = `@layer base { * 리셋 · button/input/select/textarea 글꼴 · button 글자 크기 · :where(button, a, input, select, textarea):focus-visible · 640px input/select/textarea 16px }`(`shell.css` 에서 옮김). `!important` 2건은 screens 층 `shell.css` 에 남는다.
- `styles.ts` 순서 = layers → pretendard → tokens → base → primitives → 화면 → shell · `vite.config.ts` `test.css.include` 에 `base.css`·`primitives.css` · `scripts/layer-count.mjs` 가 두 파일의 층 이름을 안다(`files=21 wrapped=20 unlayered=0 red=0`).
- verify 문제 0(옮김 15) · 계산값 196 페이지 차이 0.

### 판정 도구 — `cascade-map.mjs verify` 일반화

- 기준 트리에 `design-system.css` 가 없으면 **전 선언 단위**(규칙 × `:is()` 인자 × 선언 · 4882)를 본다. 새 자리 = 같은 파일·선택자·값이면 그 자리, 아니면 같은 인자(또는 선택자)·미디어·속성·값의 작업 트리 선언(토큰 별칭 9종은 정본 이름으로 맞춰 비교 · 여러 파일의 같은 선언이 한 자리로 모이면 오늘 이기던 것이 주인이고 나머지는 삭제로 센다).
- 뒤집힘 = 오늘 이기던 경쟁(값 다름)에 새 자리로 지는 것. 비교 순서 **!important → 층 순위 → 특이도 → 순서(규칙 안 선언 순서 포함)**. 모든 단위를 보므로 새로 이기는 쪽은 상대 단위의 뒤집힘으로 드러난다.
- 경쟁 = P2a 의 키 공유(`key`) + 요소 호환(`type`·`universal` · TSX 에서 그 클래스가 쓰인 태그로 거름) + **공존 클래스(`co`)** — TSX `className` 식 안에 함께 적힌 클래스(`.btn` ↔ `.btn-strong`). P2a 가 계산값 대조로 뒤늦게 찾은 「같은 요소의 다른 클래스」 사각을 선택자 단계에서 본다(과대 근사).
- 삭제 = 오늘 모든 문맥에서 지는 것(경쟁 선택자·미디어 포함 관계 증명) · 새 선언 = 어떤 단위의 새 자리도 아닌 것. 증명이 없으면 사유 면제(`p2b/cascade-exempt.json` · 사유 없음·낡음은 문제).
- 자체 확인: `.btn` 을 일부러 `base` 층으로 옮기면 upload·members `.btn` 의 padding·radius·font 뒤집힘 3건이 잡힌다(되돌림). 층 순위를 먼저 보게 고친 뒤 `.btn-strong` hover(공존 클래스)를 잡았다.
- 한계: 공존 클래스·태그는 TSX 문자열로만 안다(변수로 조립한 클래스는 모든 태그 가능) · DOM 포함 관계는 모른다 — 그런 요소 호환 경쟁은 TSX 를 읽고 사유로 면제했다(아래 표).
- 최종: `p2b/cascade-verify.md` — 단위 4882 · 자리 무변 4678 · 옮김 137 · 삭제 67(증명 60 · 사유 7) · 새 선언 4 · 면제 20 · **문제 0**.

## 단계 4 — 계열(ⓓ)

기본값 = 문맥 없는 맨 클래스 요소에서 착수 트리가 이기던 선언 집합. 같은 선택자는 한 규칙으로 합치고 선언 순서를 지켰다(`font: inherit` 뒤 `font-size` · `border` 뒤 `border-color`).

| 계열 | 조사 §2 곳수 | 착수 맨 정의 | 기본값 선언 | 삭제한 죽은 선언 | 범위·화면 규칙으로 옮긴 편차 | 남긴 특이도 편차(무변) |
|---|---:|---:|---:|---:|---|---|
| btn | 40 | 12 | 20 | 20 | `upload.css` `.btn-strong:hover { background: gray-50 }` | `.modal-takeover .reg-actions .btn` · `.detail-page label.btn` · `.labinfo-card .card-h .btn` · `.account-row-actions > .btn` · `.approval-dialog .btn-danger` · `.detail-page .btn-danger(:disabled)` |
| field | 63 | 4 | 8 | 8 | — | `.modal-takeover .inp/.sel(:focus-visible)` · `.vartable td .inp(:focus/-visible)` · `textarea.inp` · 배치 문맥 9(`.pv-pick-f .sel` 등) |
| chip | 26 | 12 | 25 | 24 | `members.css` `.memtbl .chip--off { margin-left: 6px }` | `.detail-page .chip(--neutral/--warning)` · `.search-page .chip` · `.lin .chip` · `.pc-m/.pd-m .chip` · `.fname .chip` · `.up-analyze .chip.is-analyzing` |
| card | 38 | 6 | 16 | 6 | `upload.css` `.up-card { border-width; border-style }`(색만 죽어 있던 단축을 나눔) | `.catalog-page .card` · `.project-detail .card` · `.memgrid .card-b` · `.up-card > .card-b` · `.modal-takeover .up-steps .card(-h/-b)` · `.up-empty .up-card > .card-b` |
| table | 106 | 6 | 18 | 8 | `members.css` 머리 칸 padding 을 `.memtbl th` 로(몸 칸 것은 죽어 있었다) | 없음(`.tbl` 표는 카탈로그·구성원 둘 · `.pj-table`·`.vartable`·`.account-table` 은 별 계열) |
| modal | 115 | 8 | 27 | 0 | — | `.modal.modal-takeover` · `.modal-back.mb-takeover/.pvx-back` · `.modal.pvx/.lab-info` · `.confirm-back .modal(-h/-b/-f)` · `.lin-find/.lin-fix .modal-h/-b/-f` · `.modal-takeover .modal-h` · `.up-empty .modal-h` |
| **계** | **388** | **48** | **114** | **66** | 4 | |

### 삭제한 죽은 선언(파일 · 선택자 · 속성 · 값 — 오늘 이기던 것)

- **btn 20** — `members.css` `.btn`: padding `0 12px` · border-radius `var(--radius-sm)` · border `1px solid var(--color-border-strong)` · background `var(--color-surface)` · font-family `inherit` · font-size `var(--text-body-sm)` · font-weight `600` · cursor `pointer`(upload `.btn` 뒤 순서 · `font: inherit` 가 굵기를 덮음) · `.btn-primary` background `var(--color-primary-600)`·border-color `var(--color-primary-600)`·color `var(--color-white)`(upload·셸 끝 `.btn-primary`) · `.btn-ghost` border-color `transparent`·background `transparent`(upload `.btn`) — `upload.css` `.btn` border-radius `8px`·padding `8px 14px`(셸 끝 `.btn`) · `.btn-sm` padding `6px 10px`·font-size `13px`(모든 `.btn-sm` 요소가 `.btn` · 셸 끝 `.btn` 뒤 순서) · `.btn-primary`(목록 인자) background·color `var(--color-on-primary)`·border-color `var(--up-ink)`(셸 끝 `.btn-primary`).
- **field 8** — `upload.css` `.inp, .sel` padding `8px 10px` · border `1px solid var(--up-line)` · border-radius `8px` · font `inherit` × 인자 2(셸 끝 `:is(.inp, .sel)`).
- **chip 24** — `catalog.css` `.chip` display·align-items·gap `5px`·height `21px`·border-radius `var(--radius-pill)`·padding `0 9px`·font-size `13px`·white-space 8 · `.chip--neutral`·`.chip--warning` background·color 4(셸 끝 같은 값) — `project.css` `.chip` display `inline-block`·padding `1px 7px`·border-radius `999px`·font-size `13px` 4 — `members.css` `.chip` display·align-items·padding `0 9px`·border-radius `999px`·background `var(--color-surface-hover)`·font-size `var(--text-caption)` 6(upload `.chip` 뒤 순서) · `.chip--off` background `var(--color-gray-50)`(upload `.chip` 배경 `#eef2f7` 뒤 순서 · 보인 적 없음) · `.chip--off` margin-left `6px`(범위 선택자로 옮김 · 값은 기본값과 같음).
- **card 6** — `members.css` `.card` background(같은 값)·border-radius `var(--radius-md)` · `.card-h` gap `10px`·padding `14px 18px` · `.card-h h3` font-size `var(--text-body)` · `.card-b` padding `6px 18px`(셸 끝 규칙).
- **table 8** — `catalog.css` `.tblwrap` max-height `calc(100vh - 232px)`·`calc(100dvh - 232px)` · `.tbl` font-size(같은 값) · `.tbl th` color `var(--color-gray-500)`·font-weight `700`·letter-spacing `0.05em` · `.tbl td` padding `13px 14px` — `members.css` `.memtbl td` padding `10px 8px`(구성원 표는 늘 `tbl memtbl` · 셸 끝 `.tbl td` 뒤 순서).
- 계열 밖 1 — `upload.css` `.up-card` border 단축(색 longhand 만 죽어 있었다 · 굵기·모양은 새 규칙).

### 면제(`p2b/cascade-exempt.json` · 52줄 · 전부 사용 · 낡음 0)

| 종류 | 줄 | 내용 |
|---|---:|---|
| 뒤집힘 · 요소 호환(type) | 39 | `.btn` hover·`.btn-primary:active` × 컨테이너 안 `button` 규칙 13종(`.pj-views` `.pj-seg` `.search-hero` `.dash-tile--linked` `.dash-recent` `.titem` `.pv-zoom` `.pv-shot` `.lin-picker li >` `.regsteps` `.dr-nav` `.dr-useg` `.dh-menu`) 26 · `.card-h h3` × 다른 머리 `h3` 6 · `.tbl th/td` × 다른 표 5 · `.modal-back`·`.modal` × `body` 2 — TSX 로 같은 요소에 안 걸림을 확인 |
| 뒤집힘 · 공존 클래스(co) | 2 | `.btn` hover × `.btn-strong`(화면 규칙 `.btn-strong:hover` 로 같은 값 복원) · `.modal--dialog:has(.modal-h)` × `.approval-dialog`(두 대화상자 모두 `.modal-h` 없음) |
| 삭제(오늘 죽음 · 선택자만으로 증명 불가) | 7 | `.btn-ghost` background · `.btn-sm` 2 · `.chip--off` background·margin-left · `.up-card` border · `.memtbl td` padding |
| 새 선언 | 4 | `.btn-strong:hover` · `.memtbl .chip--off` · `.up-card` border-width·border-style |

## 단계 5 — 토큰(9/9)

| 별칭 | 정본 | 값 동일 근거(라이트 · 다크) | 참조 |
|---|---|---|---:|
| `--up-line` | `--color-border` | `var(--color-border)` 별칭 · 다크·미디어 재정의 없음 | 17 |
| `--up-muted` | `--color-text-muted` | 별칭 · 재정의 없음 | 28 |
| `--lin-over-name` | `--color-text-muted` | 별칭 · 재정의 없음 | 2 |
| `--up-ink` | `--color-text` | 별칭 · 재정의 없음 | 6 |
| `--up-warn` | `--color-warning-600` | 별칭 · 재정의 없음 | 4 |
| `--lin-over-ink` | `--color-warning-600` | 별칭 · 재정의 없음 | 6 |
| `--up-warn-bg` | `--color-warning-50` | 별칭 · 재정의 없음 | 2 |
| `--lin-over-bg` | `--color-warning-50` | 별칭 · 재정의 없음 | 2 |
| `--up-radius` | `--radius-lg` | `12px` = `12px` · 두 이름 모두 재정의 없음 | 6 |

- 참조 73(`upload.css` 62 · `lineage.css` 10 · `primitives.css` 1) 치환 → 이름 9 삭제. 게이트 b 미정의 참조 0 · verify 문제 0(별칭은 정본 이름으로 맞춰 비교) · 계산값 차이 0(커스텀 속성 제외 대조).

## 단계 6 — P2a 후속

- 같은 조건 미디어 블록: 파일별 중복 조건 12종 중 **이웃한 3곳**(사이 규칙 없음)을 합쳤다 — `shell.css` 640px 2 · `upload.css` 640px 1. 나머지는 사이에 규칙이 있어 합치면 순서가 바뀐다 — 두었다(후속 1).
- `p2a/cascade-verify.md` 면제표에 미디어 열(21행 · 판정 무변).
- `vite.config.ts` 껍질 제거 플러그인에 이스케이프 따옴표 한계 주석(저장소 CSS 에 해당 문자열 0).
- `.lin-picker li > button` 규칙 2개는 그대로.
- `shell.css` 끝 블록 머리 주석: 프리미티브는 `primitives.css` · 페이지 컨테이너·`.page-head h1`·`.form-row` 「P5 이관 대기」.

## ⓑ 시각 변경 0(단계 7)

- 기준 `p2b-before`: 착수 트리 빌드 · 07:00:21~07:08:13 UTC · 196장.
- 후보 `p2b-after`: HEAD `f0d8baf0` · `gitDirty` false · audit 다시 빌드 · 08:31:49~08:39:50 UTC · 196장.
- `npm run visual:diff -- .visual/p2b-before .visual/p2b-after .visual/p2b-report` → **196 captures · red 0 · strict px 0 · exit 0** · 보조 차이 0 · 크기 차이 0 · 명세 sha256 `d6983d71…` 같음. 보고 `p2b/visual/report.md`·`report.json`. red 0 이라 `visual/red/` 없음.

### ⓑ′ 계산값 전수 대조

- 도구 = P3 `cdump_p3.py`·`compare.py`(커스텀 속성 제외 · 요소 키 = 순번:태그) 사본 `p2b/states/cdump.py`·`compare.py`. 착수 빌드 ↔ 단계별 빌드, 캡처와 같은 196 페이지.

| 시점 | 트리(내용) | 결과 |
|---|---|---|
| 0단계 | `37344117` | 196 페이지 · 26962 항목 · 차이 0 |
| btn · field · chip · card · table · modal | 각 계열 커밋 | 각 196 페이지 · 차이 0 |
| 토큰 + P2a 후속 | `f0d8baf0` | 196 페이지 · 차이 0 |

## ⓒ 상태 강제 계측

agent-browser 로 착수 빌드와 최종 빌드에서 같은 장면·폭 1440 에 상태를 강제하고 계산값을 쟀다(한 스크립트 · `p2b/states/states.py` · 원자료 `states-before.json`·`states-after.json`). hover = 포인터 이동 · focus-visible = Shift 뒤 초점(초점을 못 받는 요소는 계측용 `tabindex=-1`) · active = mouse down · disabled = `disabled` 속성. 표의 「상태」는 실제로 성립한 가상 클래스다.

| 대상 | 장면 | 상태 | 값(전 = 후 · 주요 속성) | 전후 |
|---|---|---|---|---|
| btn-primary:hover (members.css 삭제 · .btn:hover 좁힘) | upload-link | hover | background-color rgb(19, 105, 233) | 같음 |
| btn-secondary:hover (.btn:hover 좁힘) | lab-dialog | hover,focusVisible | background-color rgb(255, 255, 255) | 같음 |
| plain .btn:hover (.btn:hover 유지) | upload-link | hover | background-color rgb(249, 250, 251) | 같음 |
| btn-primary:active (DS#83) | upload-link | hover,active | background-color rgb(15, 98, 224) | 같음 |
| search-hero button:active (DS#83) | lab | hover,active | background-color rgb(15, 98, 224) | 같음 |
| .inp[readonly] (upload.css 삭제) | upload-metadata | - | background-color rgb(255, 255, 255); color rgb(18, 22, 25) | 같음 |
| .login-input:focus-visible (login.css 삭제) | login | focusVisible | border-top-color rgb(169, 179, 191); outline-offset 3px; outline-style solid; outline-width 2px | 같음 |
| .pcard:focus-visible (project.css outline-offset 삭제) | projects | focusVisible | outline-offset 3px; outline-style solid; outline-width 2px | 같음 |
| .modal-takeover button:focus-visible (선택자에서 뺌) | upload | focusVisible | outline-offset 3px; outline-style solid; outline-width 2px | 같음 |
| .modal-takeover .inp:focus-visible (유지) | upload-metadata | focusVisible | border-top-color rgb(169, 179, 191); outline-offset 2px; outline-style solid; outline-width 2px | 같음 |
| button:focus-visible 일반 (DS#129 버림) | catalog | focusVisible | outline-offset 3px; outline-style solid; outline-width 2px | 같음 |
| .lin-picker li > button[aria-pressed="true"] (DS#170) | lineage-picker | - | background-color rgba(105, 112, 119, 0.08) | 같음 |
| .lin-picker li > button:hover | lineage-picker | hover | background-color rgba(0, 0, 0, 0); color rgb(18, 22, 25) | 같음 |
| .mainnav a:hover | catalog | hover | background-color rgba(105, 112, 119, 0.08); color rgb(18, 22, 25) | 같음 |
| .gnb-upload:hover (DS#127 color) | catalog | hover | background-color rgb(15, 98, 224); color rgb(255, 255, 255) | 같음 |
| .tbl td.rowact .ra 행 hover (opacity 삭제) | catalog | hover |  | 같음 |
| P2b .pj-seg button.on focus-visible | project-dialog | focusVisible | background-color rgb(255, 255, 255); border-top-color rgb(18, 22, 25); color rgb(18, 22, 25); opacity 1; outline-offset 3px; outline-style solid; outline-width 1px | 같음 |
| P2b btn .btn.btn-ghost :hover | approval-dialog | hover | background-color rgb(249, 250, 251); border-top-color rgba(0, 0, 0, 0); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b btn .btn.btn-ghost :focus-visible | approval-dialog | focusVisible | background-color rgb(255, 255, 255); border-top-color rgba(0, 0, 0, 0); color rgb(18, 22, 25); opacity 1; outline-offset 3px; outline-style solid; outline-width 2px | 같음 |
| P2b btn .btn.btn-ghost :active | approval-dialog | hover,active | background-color rgb(249, 250, 251); border-top-color rgba(0, 0, 0, 0); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b btn .btn.btn-ghost :disabled | approval-dialog | disabled | background-color rgb(255, 255, 255); border-top-color rgba(0, 0, 0, 0); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b btn .btn.btn-strong :hover (편차 이동) | project-close | hover | background-color rgb(249, 250, 251); border-top-color rgb(18, 22, 25); color rgb(255, 255, 255); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b btn .btn.btn-secondary :disabled | project-close | disabled | background-color rgb(255, 255, 255); border-top-color rgb(169, 179, 191); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b field .inp :hover | upload-metadata | hover | background-color rgb(255, 255, 255); border-top-color rgb(169, 179, 191); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b field .inp :focus-visible | upload-metadata | focusVisible | background-color rgb(255, 255, 255); border-top-color rgb(169, 179, 191); color rgb(18, 22, 25); opacity 1; outline-offset 2px; outline-style solid; outline-width 2px | 같음 |
| P2b field .inp :active | upload-metadata | hover,focusVisible,active | background-color rgb(255, 255, 255); border-top-color rgb(169, 179, 191); color rgb(18, 22, 25); opacity 1; outline-offset 2px; outline-style solid; outline-width 2px | 같음 |
| P2b field .inp :disabled | upload-metadata | disabled | background-color rgb(255, 255, 255); border-top-color rgb(169, 179, 191); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b chip .chip :hover | catalog | hover | background-color rgb(232, 236, 242); border-top-color rgb(232, 236, 242); color rgb(67, 73, 80); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b chip .chip :focus-visible | catalog | focusVisible | background-color rgb(232, 236, 242); border-top-color rgb(232, 236, 242); color rgb(67, 73, 80); opacity 1; outline-offset 0px; outline-style auto; outline-width 1px | 같음 |
| P2b chip .chip :active | catalog | hover,active | background-color rgb(232, 236, 242); border-top-color rgb(232, 236, 242); color rgb(67, 73, 80); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b chip .chip :disabled | catalog | - | background-color rgb(232, 236, 242); border-top-color rgb(232, 236, 242); color rgb(67, 73, 80); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b card .card :hover | settings | hover | background-color rgb(255, 255, 255); border-top-color rgb(223, 227, 232); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b card .card :focus-visible | settings | focusVisible | background-color rgb(255, 255, 255); border-top-color rgb(223, 227, 232); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style auto; outline-width 1px | 같음 |
| P2b card .card :active | settings | hover,active | background-color rgb(255, 255, 255); border-top-color rgb(223, 227, 232); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b card .card :disabled | settings | - | background-color rgb(255, 255, 255); border-top-color rgb(223, 227, 232); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b table .tbl th :hover | catalog | hover | background-color rgb(245, 247, 250); border-top-color rgb(86, 92, 99); color rgb(86, 92, 99); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b table .tbl th :focus-visible | catalog | focusVisible | background-color rgb(245, 247, 250); border-top-color rgb(86, 92, 99); color rgb(86, 92, 99); opacity 1; outline-offset 0px; outline-style auto; outline-width 1px | 같음 |
| P2b table .tbl th :active | catalog | hover,active | background-color rgb(245, 247, 250); border-top-color rgb(86, 92, 99); color rgb(86, 92, 99); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b table .tbl th :disabled | catalog | - | background-color rgb(245, 247, 250); border-top-color rgb(86, 92, 99); color rgb(86, 92, 99); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b modal .modal--dialog :hover | approval-dialog | hover | background-color rgb(255, 255, 255); border-top-color rgb(223, 227, 232); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b modal .modal--dialog :focus-visible | approval-dialog | focusVisible | background-color rgb(255, 255, 255); border-top-color rgb(223, 227, 232); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style auto; outline-width 1px | 같음 |
| P2b modal .modal--dialog :active | approval-dialog | hover,active | background-color rgb(255, 255, 255); border-top-color rgb(223, 227, 232); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |
| P2b modal .modal--dialog :disabled | approval-dialog | - | background-color rgb(255, 255, 255); border-top-color rgb(223, 227, 232); color rgb(18, 22, 25); opacity 1; outline-offset 0px; outline-style none; outline-width 3px | 같음 |

- **43/43 같음.** P2a 16건은 P2a 표의 값과 같다.
- [미측정] `:disabled` 가 성립하지 않는 4건 — `.chip`(span) · `.card`(div) · `.tbl th`(th) · `.modal--dialog`(div)는 `disabled` 속성으로 `:disabled` 가 걸리지 않는다(표 「상태 -」 · 값은 기본 상태와 같음). 이 계열에는 `:disabled` 규칙도 없다.

## ⓔ 게이트(단계 8)

`COLAB_TASK_ID=db68dcd9c7224b1db66052498645e56a bash gates/run.sh task` → **exit 0 · 계 green 5 / red(판정) 0 / red(준비) 0**(트리 = `f0d8baf0` + 미커밋 증거 파일 · `~/.colab-v2-test.env` 존재 확인 뒤). 요약 JSON = git common dir 기준 `colab-harness/12892b7b10681bc41b9b2b92347660f5/db68dcd9c7224b1db66052498645e56a/02376e5bd5f24df8a2ecd1aaa791d7a3/gate-summary.json`. 이 커밋 뒤 handoff 용으로 같은 명령을 한 번 더 돌리며 그 run id 는 `COLAB_HANDOFF` 줄에 실린다.

| 게이트 | 결과 | 요약 |
|---|---|---|
| `frontend-design-lint` | green | 파일 21 · :root 정의 밖 0 · 미정의 참조 0 · 다크 누락 0(면제 6) · :root/@import 0 · 범위 색 토큰 0 · 색 리터럴 0(면제 1) · 인라인 0(변수 대입 7) · **프리미티브 맨 정의 밖 0(면제 0)** |
| `frontend-design-lint-selftest` | green | 검사 23건 전건 기대대로 (green 5 · red 13 · red(준비) 5) |
| `frontend-typecheck` | green | tsc --noEmit 오류 0건 |
| `frontend-test` | green | Test Files 130 passed (130) · Tests 1613 passed (1613) — P3 와 같은 건수 · 폐기 0 |
| `frontend-fixture-reach` | green | 진입점 src/main.tsx 도달 207(진입점 제외 206) · 금지 모듈 0 |

## 시험 변경

| 시험 | 변경 |
|---|---|
| `frontend/test/account-admin-layout-20260918.test.ts` | `DESIGN` 이 읽는 파일 `shell.css` → `primitives.css`(`.table-scroll-hint` · 1100px 블록) · it 제목의 파일명 · 주석 1줄 — 단언 무변 |
| `frontend/test/lv-rules-20260907.test.tsx` | 대비 계측이 읽는 토큰 이름 `--lin-over-ink`·`--lin-over-bg`·`--lin-over-name` → 같은 값의 정본 `--color-warning-600`·`--color-warning-50`·`--color-text-muted` — spec 이 이름 삭제를 요구해 생긴 변경(단언·값 무변) · 경로·include 밖이라 적는다 |
| `frontend/vite.config.ts` `test.css.include` | `base.css`·`primitives.css` 추가 |
| selftest 픽스처 | `green-e` · `red-e` · `red-e-important` 신설 · 기존 16트리에 빈 `primitives.txt`·`primitives-exempt.txt` |

- 계산값 시험 6 it 무변.

## spec 과 다르게 한 점

- ⟨advisor ② 반영⟩ `dev-package/reports/design-system/20260924/p2a/cascade-verify.md` 가 이 레인 diff 에서 48줄 바뀐 것은 P2b spec 「정리 항목(P2a 후속)」의 **면제표 미디어 열 추가**(`f0d8baf0`)다 — P2a 판정 내용은 그대로이고 표 형식만 바뀌었다.

1. **`cascade-map.mjs verify` 일반화** — spec 은 P2a `verify` 를 그대로 쓴다고 적었으나 그 모드는 `design-system.css` 선언만 추적한다(착수 트리에 그 파일이 없어 모든 이동이 「증명 없는 변경」이 된다). 기준 트리에 `design-system.css` 가 없을 때 전 선언 단위를 보는 판정을 더했다(P2a 판정은 그대로 · `family` 모드 추가). 지시 「spec 과 코드가 다르면 멈춤」에 해당하는지 판단이 갈릴 수 있어 적는다 — 제품 코드·값의 사실(토큰 9/9 · `.chip--verified`·`.chip--off`·`catalog.css` 중복·`members.css` hover · `shell.css` 임시 블록)은 spec 과 같았다.
2. `.chip--off` — spec 은 「색·배경·테두리를 primitives 로」라 했으나 배경 gray-50 은 오늘 업로드 화면 `.chip` 배경에 순서로 져 보인 적이 없다. 옮기면 되살아나므로 **삭제**하고 색·테두리만 옮겼다. margin-left 는 spec 대로 범위 선택자로.
3. `.btn-sm` 은 오늘 모든 요소에서 셸 끝 `.btn` 에 지는 **죽은 규칙**이다 — 목록에는 두되 `primitives.css` 에 정의가 없다(되살리면 시각 변경).
4. 화면 쪽 편차를 새로 적은 곳 4(`.btn-strong:hover` · `.memtbl .chip--off` · `.up-card` 굵기·모양 · `.memtbl th` padding) — 모두 오늘 값의 보존이다.
5. 비프리미티브 규칙(`.theme-switcher` · `.gnb` 미디어 · `.modal-h .x` · `.modal-h button:where(:not(.btn))`)은 `shell.css` 끝 자리에 그대로 두었다(자리 이동은 순서 위험만 늘린다).
6. 단계 5·6 은 합친 트리에서 계산값을 한 번 쟀다(커밋은 둘).
7. 커밋 꼬리의 모델 표기는 세션 표기(Claude Opus 5.5)를 따랐다 — 지시문의 「Claude Fable 5.1」과 다르다.

## 하지 않은 것

- **vitest 는 층 순서를 검증하지 못한다** — test 전용 플러그인이 층 껍질을 벗기므로 시험의 계산값은 층 없는 캐스케이드다. 층 판정의 증거는 캡처(ⓑ) · 계산값 대조(ⓑ′) · 상태 계측(ⓒ) · verify 다.
- **패턴(`patterns.css`)은 P5 로 미뤘다** — 페이지 컨테이너 · `.page-head h1` · `.form-row` 는 `shell.css` 에 「P5 이관 대기」 표지로 남았다.
- 화면 편차의 값 통일(우려 1) · 별 계열 이름 합치기(우려 2) · 탭 3계열 · TSX 변경 0 · `scenes.json` 무변 · 토큰 값·새 이름 0 · 새 의존성 0 · push·PR 게시.
- 이웃하지 않은 같은 조건 미디어 블록 병합.
- 게이트 e 는 요소 이름이 붙은 compound(`button.btn`)를 허용한다(spec 문면) — 이 형태의 맨 정의는 막지 못한다.
- 비폼 요소의 `:disabled` 계측 4건([미측정] · 성립 불가).

## 후속 항목

1. 같은 조건 미디어 블록(이웃하지 않은 것) — 사이 규칙과 경쟁 없음을 verify 로 보이며 하나씩 합칠지.
2. [Ted 판정] 억눌린 값 — `.btn-sm`(전 요소에서 죽음) · `.chip--off` 배경 gray-50 · `.btn-strong` hover 배경 gray-50(흰 글자 위 · 대비 낮음) · P2a 후속 1(`.btn-primary:hover` 등) · `.chip` `#eef2f7`(P3 우려 1).
3. 화면 편차 표(위 「남긴 특이도 편차」)를 P5 문서 「편차 목록」으로.
4. 계산값 대조·상태 계측 도구를 `frontend/scripts/visual-baseline/` 로 올릴지(P2a 후속 3 · P3 후속 7).
5. `.lin-picker li > button` 규칙 2개 — 제품 DOM 증거가 나오면 삭제 판정.
6. 게이트 e 가 `요소.클래스` compound 를 맨 정의로 볼지.
