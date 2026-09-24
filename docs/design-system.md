# 디자인 시스템 — 층 · 토큰 · 프리미티브 · 새 화면 점검표

이 문서는 게이트 `frontend-design-lint`(조건 a~h)가 재는 규칙을 사람 말로 적은 것이다.
새 화면을 만들 때 ⑤ 점검표대로 하면 게이트가 green 이다. red 가 나면 ⑥ 표에서 그 글자를 찾는다.

- ② 토큰 표와 ③ 프리미티브 표의 **표지 안쪽**은 `frontend/scripts/design-docs.mjs` 가 실물(`tokens.css` · `primitives.css` · 게이트 목록 파일)에서 다시 쓴다. 손으로 고치지 않는다 — 게이트 h 가 표지 안쪽이 실물과 같은지 잰다.
- 표지 밖 문장(이 머리말 · 화면 편차 목록 · 점검표 · 판정 대기 목록)은 손글이다. 표지 밖만 고친 변경은 h 에 걸리지 않는다.
- 표를 마지막으로 다시 쓴 때: 2026-09-24(P5). 입력 파일의 sha256 은 각 표지 안 첫 줄에 있다.
- 근거: spec `dev-package/prd/specs/S-DESIGN-STRUCTURE-P5-20260924.md` · 계획과 단계 결과 `dev-package/reports/design-system/20260924/architecture.md`.
- 실물 모양은 프리미티브 갤러리에서 본다: audit 빌드의 `/audit-design.html?design=full&scene=primitives`(⑧).

## ① 층

```css
@layer tokens, base, primitives, patterns, screens;
```

선언 자리 = `frontend/src/shell/layers.css`. `frontend/src/shell/styles.ts` 가 이 파일을 가장 먼저 불러오므로 층 순서는 import 순서와 무관하게 이 한 줄이 정한다.

| 층 | 파일 | 소유하는 것 | 금지(게이트) |
|---|---|---|---|
| tokens | `frontend/src/shell/tokens.css` | 저장소 유일의 `:root` — 라이트 한 블록 · 900px 분기 · 다크 `:root[data-theme="dark"]` 한 블록 · 640px 분기 | 정본 밖 `:root` 정의(a) · 정본 밖 `:root` 선택자·`@import`(d) |
| base | `frontend/src/shell/base.css` | 원소 규칙 — `*` box-sizing · 폼 원소 글꼴 · `:focus-visible` 윤곽 · 640px 입력 글자 바닥 | 클래스 규칙(관례) · `!important`(e) |
| primitives | `frontend/src/shell/primitives.css` | 공통 부품 6계열의 **기본값** — btn · field · chip · card · table · modal | 화면 선택자(관례) · `!important`(e) · 이 파일 밖의 맨 정의(e) |
| patterns | (파일 없음 · 이름만 선언) | 후보 — ④ | — |
| screens | `frontend/src/components/**/*.css` · `frontend/src/auth/login.css` · `frontend/src/shell/shell.css` | 화면 배치와 화면 편차(범위 선택자) · 한 화면 전용 토큰(화면 루트 클래스 범위) | `:root`(a·d) · `@import`(d) · 색 리터럴(f) · 프리미티브 맨 정의(e) |

**층 함정** — 뒤 층은 앞 층을 특이도와 무관하게 이긴다. 그래서 `primitives.css` 의 `.btn` 기본값은 화면 파일의 `button` 원소 규칙에도 진다 — 원소 규칙을 `base` 층에 두는 이유다. 반대로 **층에 넣지 않은 규칙은 모든 층을 이긴다.** 새 CSS 파일은 첫 글자부터 끝까지 `@layer screens { … }` 한 블록으로 감싼다(`tokens.css` 만 `@layer tokens`). 같은 층 안의 동률은 `styles.ts` 의 import 순서가 정한다. vitest 는 층 껍질을 벗긴 CSS 를 싣기 때문에 층 순서를 검증하지 못한다 — 층 판정의 증거는 캡처 대조와 계산값 대조다.

## ② 토큰

- 값은 `var(--이름)` 으로만 쓴다. 정본에 없는 이름은 새로 만든다 — **둘 이상 화면이 쓰는 이름만** 정본(`tokens.css`)에, 한 화면 전용 이름은 그 화면 루트 클래스 범위(`.catalog-page { --cat-…: }`)에 둔다.
- 화면 범위 이름에는 정본 계열 접두사(아래 표)를 쓰지 않는다 — 게이트 a.
- 정본에 색 계열 이름(`--color-` · `--fg-` · `--bg-` · `--accent-` · `--shadow-`)을 더하면 다크 블록에도 값을 둔다. 두 테마 값이 같아야 하면 `gates/fixtures/frontend-design-lint/same-in-dark.txt` 에 사유와 함께 적는다 — 게이트 c.
- 토큰 이름·값을 바꾸면 `node frontend/scripts/design-docs.mjs` 로 아래 표를 다시 쓴다 — 게이트 h.

<!-- generated:tokens -->
입력(sha256):

- `frontend/src/shell/tokens.css` `f38b9e8ec68c4163683958965f5a100a7a919ce1f57b97899e41cfd24503e0dc`
- `gates/fixtures/frontend-design-lint/same-in-dark.txt` `9044234beb8cd83d066ae525bb0838601009a411dde6daea49ce5acb544d4545`

라이트 `:root` 이름 81 · 다크 블록 이름 41 · 폭 분기에서 다시 정의하는 이름 5 · 다크 동일 면제 6

다크 칸: 값 = 다크 블록의 값 · 동일(면제) = `same-in-dark.txt` 에 사유와 함께 적힌 이름 · 별칭 따라감 = 라이트 값이 `var(--x)` 라 대상 이름의 다크 값을 따른다 · — = 색 계열이 아니라 다크 판정 대상이 아니다 · **누락** = 게이트 c red.

| 이름 | 라이트 | 다크 | 폭 분기 |
|---|---|---|---|
| `--color-white` | `#ffffff` | 동일(면제) |  |
| `--color-gray-50` | `#f9fafb` | `#202b37` |  |
| `--color-gray-100` | `#e8ecf2` | `#2b3745` |  |
| `--color-gray-200` | `#dfe3e8` | `#45566a` |  |
| `--color-gray-400` | `#848c94` | `#a3b2c3` |  |
| `--color-gray-500` | `#697077` | `#b2bfce` |  |
| `--color-gray-600` | `#565c63` | `#c4d0df` |  |
| `--color-gray-700` | `#434950` | `#dce4ed` |  |
| `--color-primary-50` | `#edf4ff` | `#203954` |  |
| `--color-primary-100` | `#e2eeff` | `#284769` |  |
| `--color-primary-200` | `#bad7ff` | `#315779` |  |
| `--color-primary-600` | `#1369e9` | `#92c2ff` |  |
| `--color-primary-700` | `#0f62e0` | `#add2ff` |  |
| `--color-primary-800` | `#0b4eb6` | `#d4e7ff` |  |
| `--color-success-50` | `#efffef` | `#163b2b` |  |
| `--color-success-100` | `#cde9d6` | `#244c37` |  |
| `--color-success-600` | `#067506` | `#90dcb2` |  |
| `--color-warning-50` | `#fff6ed` | `#45321c` |  |
| `--color-warning-600` | `#a85400` | `#f4c37e` |  |
| `--color-accent-50` | `#f1e8ff` | `#302445` |  |
| `--color-accent-200` | `#d2b6ff` | `#69518b` |  |
| `--color-accent-500` | `#6742f5` | `#c6afff` |  |
| `--color-accent-700` | `#4821db` | `#d8c7ff` |  |
| `--color-primary` | `var(--color-primary-600)` | 별칭 따라감 |  |
| `--color-on-primary` | `#ffffff` | `#10233c` |  |
| `--color-text-on-primary` | `var(--color-on-primary)` | 별칭 따라감 |  |
| `--color-ai` | `var(--color-accent-500)` | 별칭 따라감 |  |
| `--accent-neutral` | `#5b7089` | `#91a8c2` |  |
| `--color-bg` | `#f9fafb` | `#11161d` |  |
| `--color-surface` | `var(--color-white)` | `#1a222c` |  |
| `--color-surface-hover` | `#69707714` | `#2b3745` |  |
| `--color-surface-alt` | `#f5f7fa` | `#202b37` |  |
| `--color-overlay` | `rgb(15 20 28 / 45%)` | `rgb(3 7 12 / 65%)` |  |
| `--color-border` | `#e8ecf2` | `#344251` |  |
| `--color-border-strong` | `#dfe3e8` | `#45566a` |  |
| `--color-border-control` | `#a9b3bf` | `#718397` |  |
| `--color-border-shell` | `#bfc6cc` | `#45566a` |  |
| `--color-text` | `#121619` | `#edf2f7` |  |
| `--color-text-body` | `#21272ae0` | `#dce4ed` |  |
| `--color-text-muted` | `#565c63` | `#b2bfce` |  |
| `--color-text-subtle` | `var(--color-text-muted)` | 별칭 따라감 |  |
| `--color-danger` | `#a3222b` | `#ffadb6` |  |
| `--color-danger-solid` | `#a3222b` | `#ffadb6` |  |
| `--color-on-danger` | `#ffffff` | `#361016` |  |
| `--color-danger-600` | `var(--fg-danger)` | 별칭 따라감 |  |
| `--fg-danger` | `#a3222b` | `#ffadb6` |  |
| `--bg-danger` | `#fff0f1` | `#452832` |  |
| `--color-band-dark-2` | `#121619` | 동일(면제) |  |
| `--color-on-dark` | `#ffffff` | 동일(면제) |  |
| `--color-on-dark-muted` | `rgba(255, 255, 255, 0.72)` | 동일(면제) |  |
| `--font-sans` | `"Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Segoe UI", "Malgun Gothic", "Noto Sans KR", sans-serif` | — |  |
| `--font-mono` | `ui-monospace, SFMono-Regular, Consolas, monospace` | — |  |
| `--font-data` | `var(--font-sans)` | 별칭 따라감 |  |
| `--text-h2` | `28px` | — |  |
| `--text-h3` | `18px` | — |  |
| `--text-section` | `16px` | — |  |
| `--text-body` | `15px` | — |  |
| `--text-body-sm` | `14px` | — |  |
| `--text-caption` | `13px` | — |  |
| `--leading-body` | `1.6` | — |  |
| `--leading-body-sm` | `1.429` | — |  |
| `--tracking-body` | `0` | — |  |
| `--weight-heading` | `600` | — |  |
| `--space-1` | `4px` | — |  |
| `--space-2` | `8px` | — |  |
| `--space-4` | `16px` | — |  |
| `--space-5` | `20px` | — |  |
| `--space-6` | `24px` | — |  |
| `--space-page` | `32px` | — | `(max-width: 640px): 16px` |
| `--space-card` | `24px` | — | `(max-width: 640px): 20px` |
| `--space-section` | `24px` | — | `(max-width: 640px): 20px` |
| `--control-height` | `40px` | — | `(max-width: 640px): 44px` |
| `--radius-sm` | `8px` | — |  |
| `--radius-md` | `10px` | — |  |
| `--radius-lg` | `12px` | — |  |
| `--radius-pill` | `9999px` | — |  |
| `--shadow-sm` | `0px 1px 2px -1px #1717171a` | 동일(면제) |  |
| `--shadow-lg` | `0px 6px 10px -4px #17171714, 0px 16px 24px -6px #17171714` | 동일(면제) |  |
| `--ease` | `0.14s cubic-bezier(0.4, 0, 0.2, 1)` | — |  |
| `--shell-gnb-height` | `64px` | — |  |
| `--shell-gnb-offset` | `var(--shell-gnb-height)` | 별칭 따라감 | `(max-width: 900px): 110px` |

정본 계열 접두사(게이트 a 가 화면 범위 정의를 막는 이름 · c 는 그중 `--color-` `--fg-` `--bg-` `--accent-` `--shadow-`) — 라이트 이름 수:

| 접두사 | 이름 수 |
|---|---:|
| `--color-` | 47 |
| `--space-` | 8 |
| `--text-` | 6 |
| `--radius-` | 4 |
| `--font-` | 3 |
| `--shadow-` | 2 |
| `--leading-` | 2 |
| `--tracking-` | 1 |
| `--fg-` | 1 |
| `--bg-` | 1 |
| `--accent-` | 1 |
| 계열 밖 | 5 |

계열 밖 이름: `--weight-heading` · `--control-height` · `--ease` · `--shell-gnb-height` · `--shell-gnb-offset`

다크 동일 면제(`same-in-dark.txt` 이름 줄 6):

- `--color-white` — 테마 무관 원시 흰색 — 다크에서 바뀌는 흰 면은 의미 토큰(`--color-surface` 등)이 맡는다
- `--shadow-sm` — 다크 값이 정의된 적 없음 — 현재 다크에서도 이 값으로 렌더된다(값 무변 원칙 · 다크 그림자 결정은 별건)
- `--shadow-lg` — 다크 값이 정의된 적 없음 — 현재 다크에서도 이 값으로 렌더된다(값 무변 원칙 · 다크 그림자 결정은 별건)
- `--color-band-dark-2` — 상세 잠금 안내 띠(`.locked-hero`)의 어두운 바탕 — 두 테마에서 같은 값으로 렌더된다(다크 값 정의된 적 없음)
- `--color-on-dark` — 위 어두운 띠 위 글자색 — 띠가 테마 무관이라 글자도 테마 무관
- `--color-on-dark-muted` — 위 어두운 띠 위 보조 글자색 — 띠가 테마 무관이라 글자도 테마 무관
<!-- /generated:tokens -->

## ③ 프리미티브

기본값은 `primitives.css` 한 파일이 가진다. 화면은 클래스를 붙여 쓰고, 다른 모양이 필요하면 **그 화면의 범위 선택자**(`.memgrid .card-b` 류)로 편차를 적는다. 맨 클래스 규칙(`.btn { }` · `.btn:hover { }` · `:is(.inp, .sel) { }`)을 화면 파일에 쓰면 게이트 e 가 red 다. 목록 = `gates/fixtures/frontend-design-lint/primitives.txt`(계열별 클래스).

| 계열 | 마크업 | 수식자·조각 |
|---|---|---|
| btn | `<button class="btn" type="button">` | `.btn-primary` · `.btn-secondary` · `.btn-ghost` · `.btn-danger` · `.btn-sm`(아래 표의 「정의 없음」 참고) |
| field | `<input class="inp">` · `<select class="sel">` | `disabled` · `textarea.inp`(크기 조절은 업로드 화면 규칙) |
| chip | `<span class="chip">` | `.chip--off` · `.chip--verified` · `.chip--lineage` · `.chip--neutral` · `.chip--warning` |
| card | `<div class="card"><div class="card-h"><h3>…</h3></div><div class="card-b">…</div></div>` | — |
| table | `<div class="tblwrap"><table class="tbl">…</table></div>` | `.table-scroll-hint`(1100px 이하에서 보임) |
| modal | `<div class="modal-back"><div class="modal modal--dialog" role="dialog"><div class="modal-h">…</div><div class="modal-b">…</div><div class="modal-f">…</div></div></div>` | `.modal` 은 골격만 — 가운데 대화상자는 `.modal--dialog` 를 붙인다 |

<!-- generated:primitives -->
입력(sha256):

- `frontend/src/shell/primitives.css` `5a5cb5334dffd0c19999cd2e7e5d032f5d562ddf65a63df71bbca96da9881f63`
- `gates/fixtures/frontend-design-lint/primitives.txt` `82e423d8d2ffd7e4e92cab80301bcbf15e6ea87437310a0f99568aab4c14253f`
- `gates/fixtures/frontend-design-lint/primitives-exempt.txt` `25f7aa495f529320af9ae53c064479bac5a3c08f1b07ee8cf9b631dc3f001eda`
- `gates/fixtures/frontend-design-lint/same-in-dark.txt` `9044234beb8cd83d066ae525bb0838601009a411dde6daea49ce5acb544d4545`

목록 클래스 22(계열 6) · `primitives.css` 규칙 32 · 선언 114

| 계열 | 목록 클래스 | 규칙 | 기본값 선언 |
|---|---:|---:|---:|
| btn | 6 | 6 | 20 |
| field | 2 | 2 | 8 |
| chip | 2 | 7 | 25 |
| card | 3 | 4 | 16 |
| table | 3 | 6 | 18 |
| modal | 6 | 7 | 27 |
| **계** | 22 | 32 | 114 |

규칙 = 그 클래스가 `:not()`·`:has()` 인자 밖에 나오는 `primitives.css` 규칙(폭 분기 포함). 한 규칙이 두 클래스에 걸리면(`:is(.inp, .sel)`) 아래 표의 두 행에 모두 세고, 계열 합계는 한 번만 센다. 「정의 없음」 = 목록에는 있어 화면 파일의 맨 정의가 막히지만 기본값이 없다.

| 계열 | 클래스 | 규칙 | 선언 | 선택자 |
|---|---|---:|---:|---|
| btn | `.btn` | 2 | 12 | `.btn`<br>`.btn:where(:not(.btn-primary, .btn-secondary)):hover` |
| btn | `.btn-primary` | 2 | 4 | `.btn-primary`<br>`.btn-primary:active` |
| btn | `.btn-secondary` | 1 | 3 | `.btn-secondary` |
| btn | `.btn-ghost` | 1 | 1 | `.btn-ghost` |
| btn | `.btn-danger` | 정의 없음 | — |  |
| btn | `.btn-sm` | 정의 없음 | — |  |
| field | `.inp` | 2 | 8 | `:is(.inp, .sel)`<br>`:is(.inp, .sel)` · (max-width: 640px) |
| field | `.sel` | 2 | 8 | `:is(.inp, .sel)`<br>`:is(.inp, .sel)` · (max-width: 640px) |
| chip | `.chip` | 2 | 15 | `.chip`<br>`.chip:where(:not([class*="chip--"]))` |
| chip | `.chip--*` | 5 | 10 | `.chip--off`<br>`.chip--verified`<br>`.chip--lineage`<br>`.chip--neutral`<br>`.chip--warning` |
| card | `.card` | 1 | 5 | `.card` |
| card | `.card-h` | 2 | 10 | `.card-h`<br>`.card-h h3` |
| card | `.card-b` | 1 | 1 | `.card-b` |
| table | `.tbl` | 3 | 9 | `.tbl`<br>`.tbl th`<br>`.tbl td` |
| table | `.tblwrap` | 1 | 3 | `.tblwrap` |
| table | `.table-scroll-hint` | 2 | 6 | `.table-scroll-hint`<br>`.table-scroll-hint` · (max-width: 1100px) |
| modal | `.modal-back` | 1 | 7 | `.modal-back` |
| modal | `.modal` | 1 | 4 | `.modal` |
| modal | `.modal--dialog` | 2 | 8 | `.modal--dialog`<br>`.modal--dialog:has(.modal-h)` |
| modal | `.modal-h` | 1 | 2 | `.modal-h` |
| modal | `.modal-b` | 1 | 1 | `.modal-b` |
| modal | `.modal-f` | 1 | 5 | `.modal-f` |

목록 클래스에 걸리지 않는 `primitives.css` 규칙: 없음

프리미티브 맨 정의 면제(`primitives-exempt.txt` · 게이트 e): 0 — 없음

색 리터럴 면제(`same-in-dark.txt` 의 `f` 줄 · 게이트 f): 1

- `src/shell/primitives.css` `.chip` `background: #eef2f7` — 같은 값 토큰 없음(가까운 --color-gray-100 #e8ecf2 · --color-surface-alt #f4f7fb 는 값이 다르다) — 새 토큰 vs 기존 토큰으로 값 변경(시각 변경)을 Ted 판정 대기 · spec P3 우려 1
<!-- /generated:primitives -->

### 화면 편차 목록 (손글 · P2b 결과 · 값 무변)

P2b 가 기본값을 모으면서 **오늘 값 그대로 남긴** 화면 쪽 편차다. 출처 = `dev-package/reports/design-system/20260924/p2b/report.md` 「단계 4 — 계열」 표. 모두 화면 범위 선택자라 게이트 e 대상이 아니다. **값을 통일할지는 Ted 판정**(⑦ · 통일하면 시각 변경이 생긴다).

| 계열 | 화면 범위 규칙으로 옮긴 편차(P2b 신설) | 남긴 특이도 편차 |
|---|---|---|
| btn | `upload.css` `.btn-strong:hover { background: gray-50 }` | `.modal-takeover .reg-actions .btn` · `.detail-page label.btn` · `.labinfo-card .card-h .btn` · `.account-row-actions > .btn` · `.approval-dialog .btn-danger` · `.detail-page .btn-danger(:disabled)` |
| field | — | `.modal-takeover .inp/.sel(:focus-visible)` · `.vartable td .inp(:focus/-visible)` · `textarea.inp` · 배치 문맥 9(`.pv-pick-f .sel` 등) |
| chip | `members.css` `.memtbl .chip--off { margin-left: 6px }` | `.detail-page .chip(--neutral/--warning)` · `.search-page .chip` · `.lin .chip` · `.pc-m/.pd-m .chip` · `.fname .chip` · `.up-analyze .chip.is-analyzing` |
| card | `upload.css` `.up-card { border-width; border-style }` | `.catalog-page .card` · `.project-detail .card` · `.memgrid .card-b` · `.up-card > .card-b` · `.modal-takeover .up-steps .card(-h/-b)` · `.up-empty .up-card > .card-b` |
| table | `members.css` 머리 칸 padding → `.memtbl th` | 없음 — `.tbl` 표는 카탈로그·구성원 둘. `.pj-table` · `.vartable` · `.account-table` 은 별 계열 이름(목록 밖) |
| modal | — | `.modal.modal-takeover` · `.modal-back.mb-takeover/.pvx-back` · `.modal.pvx/.lab-info` · `.confirm-back .modal(-h/-b/-f)` · `.lin-find/.lin-fix .modal-h/-b/-f` · `.modal-takeover .modal-h` · `.up-empty .modal-h` |

별 계열 이름(`.login-input` · `.pj-modal*` · `.account-table` 등)과 탭 3계열은 프리미티브 목록 밖이다 — 합칠지는 ⑦.

## ④ 패턴 (후보 · 이관 전)

patterns 층은 이름만 선언돼 있고 파일이 없다. 아래 규칙은 `frontend/src/shell/shell.css` 끝의 「P5 이관 대기」 표지 아래(screens 층)에 있다.

| 후보 | 규칙 |
|---|---|
| 페이지 컨테이너 | `:is(.catalog-page, .lab-page, .project-page)` · `:is(.detail-page, .project-detail, .preview-page, .settings-page)` — 폭 100% · 최대 1280px · 가운데 · `--space-page` 여백 · 아래 48px |
| 검색 컨테이너 | `.search-page` — 최대 920px |
| 페이지 머리 | `.page-head h1` — `--text-h2` · 행간 1.3 · 굵기 700 · 자간 -0.02em |
| 폼 줄 | `.form-row` — gap 8px |

**옮기지 않은 이유(P5 · advisor ① 실측)** — patterns 층으로 내리면 층이 screens 보다 앞이 되어, 지금 셸 규칙에 순서로 지던 화면 7파일의 같은 선택자 선언(`catalog.css` · `dashboard.css` · `detail.css` · `preview.css` · `project.css` · `search.css` · `upload.css`)과 죽어 있던 `@media` padding 규칙이 살아난다. 「값 무변」 범위를 넘는다.
**이관 조건** — 화면 이름이 든 컨테이너 선택자를 공통 이름 `.page`(TSX 변경)로 바꾸는 별건과 묶어, 화면 쪽 경쟁 선언 정리 · 캡처 대조 · 계산값 대조를 한 번에 한다. 그때 `patterns.css` 를 만들고 게이트에 「패턴 맨 정의」 조건을 둘지 판정한다.

## ⑤ 새 화면을 만들 때 — 점검표

게이트가 재는 항목(글자 = ⑥ 의 조건):

1. [a] 화면 CSS 에 `:root { --x: … }` 를 쓰지 않는다. 한 화면 전용 토큰은 화면 루트 클래스 범위에 두고, 정본 계열 접두사(`--color-` 등)를 붙이지 않는다.
2. [b] `var(--x)` 로 부르는 이름은 정본·화면 범위·TSX 의 `'--x'` 문자열 중 어딘가에 정의돼 있다. 폴백이 있어도 미정의는 red 다.
3. [c] 정본에 색 계열 이름을 더하면 다크 블록에도 값을 둔다(또는 `same-in-dark.txt` 에 사유).
4. [d] 화면 CSS 에 `:root` 선택자와 `@import` 를 쓰지 않는다.
5. [e] 프리미티브 클래스의 맨 정의(`.btn { }` · `.chip--warning { }` · `:is(.inp, .sel) { }`)를 화면 파일에 쓰지 않는다 — 편차는 화면 범위 선택자(`.x-page .btn { }`)로. `primitives.css`·`base.css` 에 `!important` 를 쓰지 않는다.
6. [f] 색은 토큰으로만 쓴다 — hex · `rgb()` · `hsl()` · `color-mix()`(리터럴 섞임) · 색 이름 금지. 직접 값이든 `var()` 폴백이든 같다.
7. [g] TSX 의 `style={{ … }}` 에는 CSS 변수 대입(`style={{ '--w': v }}`)만 쓴다. 값은 CSS 가 변수로 읽는다.
8. [h] 토큰(`tokens.css`)·프리미티브(`primitives.css`)·게이트 목록 파일을 바꿨으면 `node frontend/scripts/design-docs.mjs` 로 ②·③ 표를 다시 쓴다.

게이트 밖 항목(게이트가 재지 않는다 — 사람이 한다):

- 새 CSS 파일은 `@layer screens { … }` 한 블록으로 감싸고 `styles.ts` 에 import 를 더한다(① 층 함정).
- 새 화면·새 상태는 `frontend/scripts/visual-baseline/scenes.json` 에 캡처 장면을 더하고(3폭 × 2테마) 착수 기준 캡처와 대조한다(⑧).
- 글자 13px 이상 · 대비 4.5:1 이상 · 카드 그림자 0 · 인터랙션 하한은 `design-review` 스킬 §0 의 정적 합격선과 `frontend-visual` 게이트가 본다.

## ⑥ 게이트 `frontend-design-lint` — 조건 a~h

실행: `bash gates/run.sh frontend-design-lint`(판정부 `frontend/scripts/design-lint.mjs` + `frontend/scripts/design-docs.mjs --check` · 셸 `gates/tools/frontend-design-lint.sh`). 증명: `bash gates/run.sh frontend-design-lint-selftest`. 요약줄 끝 = `… · 프리미티브 맨 정의 밖 e(면제 m) · 문서 표 갈림 h`.

| 조건 | red 가 되는 것 | red 출력 머리 | 고치는 법 | 면제 파일 |
|---|---|---|---|---|
| a | `tokens.css` 밖 `:root` 안의 `--*` 정의 · 화면 범위 규칙의 정본 계열 이름 정의 | `a :root 안 정의(정본 밖)` · `a 화면 범위의 정본 계열 이름` | 둘 이상 화면이 쓰면 정본으로, 한 화면 전용이면 화면 루트 클래스 범위로 옮기고 계열 밖 이름(`--cat-…`)으로 | 없음 |
| b | 어디에도 정의되지 않은 `var(--x)` 참조(폴백 유무 무관) | `b 미정의 참조` | 정본의 같은 뜻 이름으로 바꾸거나 이름을 정의 | 없음 |
| c | 라이트 색 계열 이름의 다크 누락 · 다크에만 있는 이름 · 면제 목록 구멍(사유 빈칸 · 낡음 · 다크에 이미 있음) | `c 다크 누락` · `c 다크에만 있는 이름` · `c 면제 목록 구멍` | 다크 블록에 값을 더하거나 면제 줄에 사유 | `same-in-dark.txt`(이름 · 사유) |
| d | 정본 밖 `:root` 선택자(`html:root` 포함) · 정본 밖 전 CSS 의 `@import` | `d :root/@import` | 선택자를 화면 루트 클래스로 · import 는 `styles.ts` 로 | 없음 |
| e | `primitives.css` 밖의 프리미티브 맨 정의(`:is()`/`:where()` 를 펼쳐 본다 · `:not()`/`:has()` 인자는 보지 않는다) · `primitives.css`·`base.css` 안의 `!important` · 목록·면제 구멍 | `e 프리미티브 맨 정의(primitives.css 밖)` · `e primitives.css·base.css 의 !important` · `e 목록·면제 구멍` | 편차는 화면 범위 선택자로, 기본값 변경은 `primitives.css` 에서(시각 변경이면 판정) | `primitives-exempt.txt`(파일 · 선택자 · 사유) |
| f | 정본 밖 CSS 의 색 리터럴(직접 · `var()` 폴백 · 색 이름 · 리터럴이 섞인 `color-mix()`) · 면제 구멍 | `f 색 리터럴(정본 밖)` · `f 면제 목록 구멍` | 같은 값 토큰으로 · 없으면 새 토큰(이름은 판정) | `same-in-dark.txt` 의 `f · 파일 · 선택자 · 속성 · 리터럴 · 사유` 줄 |
| g | TSX `style` 속성(펼침 속성 안의 `style` 키 포함)의 값이 `--*` 키만 가진 객체 리터럴이 아님 | `g 인라인 style 의 비변수 키` | 값을 CSS 변수로 대입하고 CSS 가 `var()` 로 읽는다 | 없음 |
| h | 이 문서의 표지 안쪽(② 토큰 · ③ 프리미티브)이 실물에서 다시 만든 표와 다름 | `h tokens 갈림 — 블록 n번째 줄부터 다르다` · `h primitives 갈림 …` · 요약 `문서 표 갈림 n` | `node frontend/scripts/design-docs.mjs` 로 다시 쓰고 커밋 — 표지 안에 입력 sha256 이 있어 입력 파일의 주석만 바꿔도 다시 써야 한다 | 없음(표지 밖 손글은 비교하지 않는다) |

**red(준비 · 종료 78)** — 판정하지 못한 것은 통과가 아니다: node 부재 · 판정부 스크립트 부재 · 대상 CSS 0건 · 목록 파일(`same-in-dark.txt` · `primitives.txt` · `primitives-exempt.txt`) 부재 · Git 목록에 있으나 디스크에 없는 CSS · `typescript` 파서 부재 · (h) 이 문서 · 표지 짝 · 입력 파일 부재.
**h 의 입력** — h 는 저장소의 문서와 저장소의 실물만 비교한다(`COLAB_FRONTEND_DIR` 픽스처 교체와 무관). 문서 경로는 env `COLAB_DESIGN_LINT_DOC`(기본 `docs/design-system.md`)로 바꿀 수 있고 selftest 가 이것으로 갈림 red 와 부재 78 을 만든다.
**못 보는 것** — 화면 루트 범위 색 토큰의 다크 짝 · 여백·글자 크기 리터럴(눈금 확정 전이라 red 조건이 아니다) · 요소 이름이 붙은 compound(`button.btn`)의 맨 정의 · 층 감싸기(`layer-count.mjs` 는 P2a 계측 도구이고 게이트가 아니다) · 실제 렌더(캡처 대조가 본다).

## ⑦ 판정 대기 목록

P1~P3 · P2a · P2b · P5 보고서에서 「Ted 판정」·「판정 필요」로 남은 항목을 모았다. 시각 항목은 결정하면 **시각 변경이 생긴다** — 구조 단계(값 무변) 밖이며 각자 별건으로 처리한다.

### 시각 값

| # | 항목 | 오늘 렌더 | 선택지 | 출처 |
|---|---|---|---|---|
| 1 | 억눌린 hover — `.btn-primary:hover` · `.btn-secondary` hover | 배경이 바뀌지 않는다 | 되살림(primary-700 등) · 그대로 | P2a 후속 1 · P2b 후속 2 |
| 2 | 억눌린 상태 — `.inp[readonly]` 배경 · `.lin .chip--warning` 색 · `.login-input:focus-visible` 테두리색 · `.pcard` 초점 간격 2px | 선언이 없어 기본 모양 | 되살림 · 그대로 | P2a 후속 1 |
| 3 | `.btn-sm` — 목록에 있으나 기본값 없음(종전 규칙은 전 요소에서 셸 `.btn` 에 졌다) | `.btn` 과 같은 크기 | 작은 버튼 정의 · 목록에서 제외 | P2b 후속 2 · spec 과 다르게 한 점 3 |
| 4 | `.chip--off` 배경 gray-50 | 업로드 `.chip` 배경에 져 보인 적 없음(삭제) | 되살림 · 그대로 | P2b 후속 2 |
| 5 | `.btn-strong:hover` 배경 gray-50 — 흰 글자 위 대비 낮음 | 그대로 렌더 | 대비 맞는 값으로 · 그대로 | P2b 후속 2 |
| 6 | `.chip` 배경 `#eef2f7`(게이트 f 면제 1) | 리터럴 | 새 토큰(값 유지 · 다크 값 결정) · `--color-gray-100` 으로 값 변경 | P3 후속 1 · P3 우려 1 |
| 7 | `deletion.css` `.dl-keep` 바탕 — 이름이 뜻한 `--color-surface-muted` 는 정의된 적이 없어 늘 `transparent` | 투명 | `--color-surface-alt` 로 채움 · 그대로 | P1 후속 2 |
| 8 | `lineage.css` 안내 줄 3곳(`.lin-unknown-why` 등) — 주석은 회색 `#5b6472` 를 설명하지만 실제 렌더는 `--color-warning-600` | 주황 | 회색 토큰으로 · 주석을 렌더에 맞춤 | P1 후속 3 · P3 |
| 9 | `.detail-page .dt-edit .de-req` 다크 — 흰 글자가 밝은 배경 위(대비 낮음) | 그대로 | `--color-on-…` 뜻 토큰 · 그대로 | P3 후속 4 |
| 10 | 화면 편차 통일(③ 화면 편차 목록 · 버튼 높이·모서리·칩 여백 등) | 화면마다 다름 | 편차 목록 유지 · 통일안 | P2b 우려 1 · P5 우려 1 |

### 범위·절차

| # | 항목 | 권고 | 출처 |
|---|---|---|---|
| 11 | 패턴 이관(④) — `.page` 개명(TSX)과 묶어 별건 | 묶음 별건 | P5 우려 4 |
| 12 | 별 계열 이름 합치기(`.login-input` · `.pj-modal*` · `.account-table` …) · 탭 3계열 | 별건 | P2b 우려 2 |
| 13 | 갤러리를 제품 라우트로 노출 | audit 빌드 전용 유지 | P5 우려 2 |
| 14 | 제품 시험 6파일 14곳 단언 변경(인라인 값 → 변수 값 읽기 · 단언한 값은 같음) 수용 | 수용 여부 판정 | P3 판정 필요 1 · 후속 3 |
| 15 | `cascade-map.mjs verify` 일반화(spec 은 P2a 도구 그대로라 적음) 수용 | 수용 여부 판정 | P2b 판정 필요 1 |
| 16 | 게이트 e 가 `요소.클래스` compound(`button.btn`)를 맨 정의로 볼지 | 판정 | P2b 후속 6 |

## ⑧ 도구

모든 명령은 `frontend/` 에서 실행한다(게이트는 저장소 루트의 `gates/run.sh`).

| 도구 | 명령 | 하는 일 |
|---|---|---|
| 갤러리 | `npm run audit:build` → `npm run audit:preview -- --port 4187` → `/audit-design.html?design=full&scene=primitives`(`&theme=dark`) · `/design-preview.html` 의 화면 「프리미티브」 | 6계열 × 정적 상태(기본 · 수식자 · disabled)를 한 페이지에 그린다. 제품 컴포넌트를 import 하지 않는 정적 마크업이다 |
| 캡처 | `npm run visual:capture -- --label <이름>` | audit 빌드를 다시 만들고 `scripts/visual-baseline/scenes.json` 의 장면 × 폭 × 테마를 `frontend/.visual/<이름>/` 에 찍는다(`index.json` 에 HEAD · 명세 sha256). 준비 실패 78 |
| 대조 | `npm run visual:diff -- <기준> <후보> <보고>` | 엄격(`threshold 0` · `includeAA`) 픽셀 대조. 명세 sha256 · 장면 집합이 다르면 78. `--subset` 을 앞에 붙이면 두 쪽에 공통인 장면만 비교한다(장면을 더한 커밋과 이전 기준을 잇는 용도 · 보고에 빠진 장면을 적는다) |
| 캐스케이드 지도 | `node scripts/cascade-map.mjs map` · `verify --base <rev>` · `family --name <n> --classes <목록>` | 선언 단위 경쟁·승자 지도와 이동 검증(P2a · P2b) |
| 문서 표 | `node scripts/design-docs.mjs`(다시 쓰기) · `--check`(비교만 · 게이트 h) | ② · ③ 표지 안쪽을 실물에서 만든다. 날짜 없이 입력 sha256 만 적어 같은 입력이면 같은 글자다 |
| 게이트 | `bash gates/run.sh frontend-design-lint` · `frontend-design-lint-selftest` | ⑥ |
