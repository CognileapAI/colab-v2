# 디자인 시스템 — 층 · 토큰 · 프리미티브 · 새 화면 점검표

이 문서는 게이트 `frontend-design-lint`(조건 a~i)가 재는 규칙을 사람 말로 적은 것이다.
새 화면을 만들 때 ⑤ 점검표대로 하면 게이트가 green 이다. red 가 나면 ⑥ 표에서 그 글자를 찾는다.

- ② 토큰 표와 ③ 프리미티브 표의 **표지 안쪽**은 `frontend/scripts/design-docs.mjs` 가 실물(`tokens.css` · `primitives.css` · 게이트 목록 파일)에서 다시 쓴다. 손으로 고치지 않는다 — 게이트 h 가 표지 안쪽이 실물과 같은지 잰다.
- 표지 밖 문장(이 머리말 · 화면 편차 목록 · 점검표 · 판정 대기 목록 · ⑨ 폭 단계 · 입력 방식)은 손글이다. 표지 밖만 고친 변경은 h 에 걸리지 않는다.
- 표의 기준 = 각 표지 안 입력 sha256(날짜는 적지 않는다 — 같은 입력이면 같은 표다).
- 근거: spec `dev-package/prd/specs/S-DESIGN-STRUCTURE-P5-20260924.md` · 계획과 단계 결과 `dev-package/reports/design-system/20260924/architecture.md`.
- 실물 모양은 프리미티브 갤러리에서 본다: audit 빌드의 `/audit-design.html?design=full&scene=primitives`(⑧).

## ① 층

```css
@layer tokens, base, primitives, patterns, screens;
```

선언 자리 = `frontend/src/shell/layers.css`. `frontend/src/shell/styles.ts` 가 이 파일을 가장 먼저 불러오므로 층 순서는 import 순서와 무관하게 이 한 줄이 정한다.

| 층 | 파일 | 소유하는 것 | 금지(게이트) |
|---|---|---|---|
| tokens | `frontend/src/shell/tokens.css` | 저장소 유일의 `:root` — 라이트 한 블록 · 900px 분기 · 다크 `:root[data-theme="dark"]` 한 블록 · 640px 분기 · 터치 기기 분기(`(pointer: coarse)` · `--control-height` 44px · ⑨) | 정본 밖 `:root` 정의(a) · 정본 밖 `:root` 선택자·`@import`(d) |
| base | `frontend/src/shell/base.css` | 원소 규칙 — `*` box-sizing · 폼 원소 글꼴 · `:focus-visible` 윤곽(입력 글자 16px 바닥은 강제 우선이 필요해 `shell.css` 의 「640px 이하 또는 터치 기기」 블록 한 곳에 둔다) | 클래스 규칙(관례) · `!important`(e) |
| primitives | `frontend/src/shell/primitives.css` | 공통 부품 6계열의 **기본값** — btn · field · chip · card · table · modal | 화면 선택자(관례) · `!important`(e) · 이 파일 밖의 맨 정의(e) |
| patterns | (파일 없음 · 이름만 선언) | 후보 — ④ | — |
| screens | `frontend/src/components/**/*.css` · `frontend/src/auth/login.css` · `frontend/src/shell/shell.css` | 화면 배치와 화면 편차(범위 선택자) · 한 화면 전용 토큰(화면 루트 클래스 범위) | `:root`(a·d) · `@import`(d) · 색 리터럴(f) · 프리미티브 맨 정의(e) |

**층 함정** — 뒤 층은 앞 층을 특이도와 무관하게 이긴다. 그래서 `primitives.css` 의 `.btn` 기본값은 화면 파일의 `button` 원소 규칙에도 진다 — 원소 규칙을 `base` 층에 두는 이유다. 반대로 **층에 넣지 않은 규칙은 모든 층을 이긴다.** 새 CSS 파일은 첫 글자부터 끝까지 `@layer screens { … }` 한 블록으로 감싼다(`tokens.css` 만 `@layer tokens`). 같은 층 안의 동률은 `styles.ts` 의 import 순서가 정한다. vitest 는 층 껍질을 벗긴 CSS 를 싣기 때문에 층 순서를 검증하지 못한다 — 층 판정의 증거는 캡처 대조와 계산값 대조다.

## ② 토큰

- 값은 `var(--이름)` 으로만 쓴다. 정본에 없는 이름은 새로 만든다 — **둘 이상 화면이 쓰는 이름만** 정본(`tokens.css`)에, 한 화면 전용 이름은 그 화면 루트 클래스 범위(`.catalog-page { --cat-…: }`)에 둔다.
- 화면 범위 이름에는 정본 계열 접두사(아래 표)를 쓰지 않는다 — 게이트 a.
- 정본에 색 계열 이름(`--color-` · `--fg-` · `--bg-` · `--accent-` · `--shadow-`)을 더하면 다크 블록에도 값을 둔다. 두 테마 값이 같아야 하면 `gates/fixtures/frontend-design-lint/same-in-dark.txt` 에 사유와 함께 적는다 — 게이트 c.
- 토큰 이름·값을 바꾸면 `node frontend/scripts/design-docs.mjs` 로 아래 표를 다시 쓴다 — 게이트 h.
- `--color-on-text-body` 는 한 화면(상세 편집 `.de-req`)만 쓰지만 다크 값이 필요해 정본에 둔다 — 화면 범위에서는 다크 값을 줄 수 없고(d) 정본 계열 이름은 화면 범위에 둘 수 없다(a) · design-fix 20260924 #17.
- 자간 토큰 두 구간 — `--tracking-heading`(−0.02em)은 제목, `--tracking-label`(0.05em)은 작은 굵은 라벨이 쓴다. 로고 글자 `.login-brand`(0.01em)는 브랜드 예외로 리터럴을 둔다 · design-fix 20260924 #7.
- `--color-surface-pressed` 는 hover 가 `--color-surface-hover` 인 자리의 누름(`:active`) 바탕이다 — 라이트 = gray-100(#e8ecf2) · 다크 = gray-200(#45566a). 다크 gray-100 은 surface-hover 와 같은 값이라 누름이 hover 와 구분되지 않았다(다크 누름 대 hover 1.61:1) · design-fix 20260924 값 19.

<!-- generated:tokens -->
입력(sha256):

- `frontend/src/shell/tokens.css` `b626fef9b9a274eb7858a85d77e5b2ebb2b23356cab46a3d45df399c852082a2`
- `gates/fixtures/frontend-design-lint/same-in-dark.txt` `d3c7cc75de6a409954ab2b6f85fda6d929882a19dc84922b5b79ae9428325c40`

라이트 `:root` 이름 85 · 다크 블록 이름 43 · 폭 분기에서 다시 정의하는 이름 5 · 다크 동일 면제 6

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
| `--color-surface-pressed` | `var(--color-gray-100)` | `var(--color-gray-200)` |  |
| `--color-overlay` | `rgb(15 20 28 / 45%)` | `rgb(3 7 12 / 65%)` |  |
| `--color-border` | `#e8ecf2` | `#344251` |  |
| `--color-border-strong` | `#dfe3e8` | `#45566a` |  |
| `--color-border-control` | `#a9b3bf` | `#718397` |  |
| `--color-border-shell` | `#bfc6cc` | `#45566a` |  |
| `--color-text` | `#121619` | `#edf2f7` |  |
| `--color-text-body` | `#21272ae0` | `#dce4ed` |  |
| `--color-text-muted` | `#565c63` | `#b2bfce` |  |
| `--color-text-subtle` | `var(--color-text-muted)` | 별칭 따라감 |  |
| `--color-on-text-body` | `#ffffff` | `#1a222c` |  |
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
| `--text-h2` | `1.75rem` | — |  |
| `--text-h3` | `1.125rem` | — |  |
| `--text-section` | `1rem` | — |  |
| `--text-body` | `0.9375rem` | — |  |
| `--text-body-sm` | `0.875rem` | — |  |
| `--text-caption` | `0.8125rem` | — |  |
| `--leading-body` | `1.6` | — |  |
| `--leading-body-sm` | `1.429` | — |  |
| `--tracking-body` | `0` | — |  |
| `--tracking-heading` | `-0.02em` | — |  |
| `--tracking-label` | `0.05em` | — |  |
| `--weight-heading` | `600` | — |  |
| `--space-1` | `4px` | — |  |
| `--space-2` | `8px` | — |  |
| `--space-4` | `16px` | — |  |
| `--space-5` | `20px` | — |  |
| `--space-6` | `24px` | — |  |
| `--space-page` | `32px` | — | `(max-width: 640px): 16px` |
| `--space-card` | `24px` | — | `(max-width: 640px): 20px` |
| `--space-section` | `24px` | — | `(max-width: 640px): 20px` |
| `--control-height` | `40px` | — | `(max-width: 640px): 44px`<br>`(pointer: coarse): 44px` |
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
| `--color-` | 49 |
| `--space-` | 8 |
| `--text-` | 6 |
| `--radius-` | 4 |
| `--font-` | 3 |
| `--shadow-` | 2 |
| `--leading-` | 2 |
| `--tracking-` | 3 |
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
| btn | `<button class="btn" type="button">` | `.btn-primary` · `.btn-secondary` · `.btn-ghost` · `.btn-danger` · `.btn-sm`(작은 단추 · 640px 이하 또는 터치가 주 입력인 기기에서는 `--control-height`) · `disabled`(opacity .5 · cursor not-allowed) |
| field | `<input class="inp">` · `<select class="sel">` | `disabled` · `textarea.inp`(크기 조절은 업로드 화면 규칙) |
| chip | `<span class="chip">` | `.chip--off` · `.chip--verified` · `.chip--lineage` · `.chip--neutral` · `.chip--warning` |
| card | `<div class="card"><div class="card-h"><h3>…</h3></div><div class="card-b">…</div></div>` | — |
| table | `<div class="tblwrap"><table class="tbl">…</table></div>` | `.table-scroll-hint`(1100px 이하에서 보임) |
| modal | `<div class="modal-back"><div class="modal modal--dialog" role="dialog"><div class="modal-h">…</div><div class="modal-b">…</div><div class="modal-f">…</div></div></div>` | `.modal` 은 골격만 — 가운데 대화상자는 `.modal--dialog` 를 붙인다 |

<!-- generated:primitives -->
입력(sha256):

- `frontend/src/shell/primitives.css` `6bfff1f57a076c8af3c36f1de68754c012a26e95fc7a9c59721251edeb302fbe`
- `gates/fixtures/frontend-design-lint/primitives.txt` `82e423d8d2ffd7e4e92cab80301bcbf15e6ea87437310a0f99568aab4c14253f`
- `gates/fixtures/frontend-design-lint/primitives-exempt.txt` `25f7aa495f529320af9ae53c064479bac5a3c08f1b07ee8cf9b631dc3f001eda`
- `gates/fixtures/frontend-design-lint/same-in-dark.txt` `d3c7cc75de6a409954ab2b6f85fda6d929882a19dc84922b5b79ae9428325c40`

목록 클래스 22(계열 6) · `primitives.css` 규칙 36 · 선언 124

| 계열 | 목록 클래스 | 규칙 | 기본값 선언 |
|---|---:|---:|---:|
| btn | 6 | 11 | 31 |
| field | 2 | 1 | 7 |
| chip | 2 | 7 | 25 |
| card | 3 | 4 | 16 |
| table | 3 | 6 | 18 |
| modal | 6 | 7 | 27 |
| **계** | 22 | 36 | 124 |

규칙 = 그 클래스가 `:not()`·`:has()` 인자 밖에 나오는 `primitives.css` 규칙(폭 분기 포함). 한 규칙이 두 클래스에 걸리면(`:is(.inp, .sel)`) 아래 표의 두 행에 모두 세고, 계열 합계는 한 번만 센다. 「정의 없음」 = 목록에는 있어 화면 파일의 맨 정의가 막히지만 기본값이 없다.

| 계열 | 클래스 | 규칙 | 선언 | 선택자 |
|---|---|---:|---:|---|
| btn | `.btn` | 4 | 15 | `.btn`<br>`.btn:where(:not(.btn-primary, :disabled)):hover` · (hover: hover)<br>`.btn:where(:not(.btn-primary)):active`<br>`.btn:disabled` |
| btn | `.btn-primary` | 3 | 5 | `.btn-primary`<br>`.btn-primary:where(:not(:disabled)):hover` · (hover: hover)<br>`.btn-primary:active` |
| btn | `.btn-secondary` | 1 | 3 | `.btn-secondary` |
| btn | `.btn-ghost` | 1 | 1 | `.btn-ghost` |
| btn | `.btn-danger` | 정의 없음 | — |  |
| btn | `.btn-sm` | 2 | 7 | `.btn-sm`<br>`.btn-sm` · (max-width: 640px), (pointer: coarse) |
| field | `.inp` | 1 | 7 | `:is(.inp, .sel)` |
| field | `.sel` | 1 | 7 | `:is(.inp, .sel)` |
| chip | `.chip` | 2 | 16 | `.chip`<br>`.chip:where(:not([class*="chip--"]))` |
| chip | `.chip--*` | 5 | 9 | `.chip--off`<br>`.chip--verified`<br>`.chip--lineage`<br>`.chip--neutral`<br>`.chip--warning` |
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

색 리터럴 면제(`same-in-dark.txt` 의 `f` 줄 · 게이트 f): 0 — 없음
<!-- /generated:primitives -->

### 화면 편차 목록 (손글 · P2b 결과 · 값 무변)

P2b 가 기본값을 모으면서 **오늘 값 그대로 남긴** 화면 쪽 편차다. 출처 = `dev-package/reports/design-system/20260924/p2b/report.md` 「단계 4 — 계열」 표. 모두 화면 범위 선택자라 게이트 e 대상이 아니다. **값을 통일할지는 Ted 판정**(⑦ · 통일하면 시각 변경이 생긴다).

| 계열 | 화면 범위 규칙으로 옮긴 편차(P2b 신설) | 남긴 특이도 편차 |
|---|---|---|
| btn | `upload.css` `.btn-strong:where(:not(:disabled)):hover { background: primary-700 }`(design-fix 20260924 #10 · 비활성 제외 F-final) | `.modal-takeover .reg-actions .btn` · `.detail-page label.btn` · `.labinfo-card .card-h .btn` · `.account-row-actions > .btn` · `.approval-dialog .btn-danger` · `.detail-page .btn-danger` |
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
9. [i] 새 폭 조건(`@media`)은 허용 값(`max-width` 640 · 900 · 1180px · `min-width` 641 · 901 · 1181px · `(pointer: coarse)` · `(hover: hover)` · `prefers-*`)만 쓰고, `:hover` 규칙은 `@media (hover: hover) { … }` 안에 둔다(⑨).

게이트 밖 항목(게이트가 재지 않는다 — 사람이 한다):

- 새 CSS 파일은 `@layer screens { … }` 한 블록으로 감싸고 `styles.ts` 에 import 를 더한다(① 층 함정).
- 새 화면·새 상태는 `frontend/scripts/visual-baseline/scenes.json` 에 캡처 장면을 더하고(6크기 × 2테마 · 1180 이하 터치 입력 · 1440 마우스) 착수 기준 캡처와 대조한다(⑧).
- 터치 기기(`(pointer: coarse)`): 누름 칸 가로·세로 44px(`--control-height`) · 입력 글자 16px 이상 · `title` 에만 있는 정보 금지(보이는 글자 · 줄바꿈 · 누르면 보이는 설명) — ⑨ 터치 기기 규칙.
- 마우스 전용 동작(더블클릭 · 마우스 이동 · 끌어다 놓기)에는 누름 대안을 둔다 — ⑨ 터치 기기 규칙.
- 새 화면·새 상태는 캡처 도구를 수치 모드로 실행한다 — `npm run visual:capture -- --label <이름> --metrics`(장면 하나 · 크기 하나는 `--metrics-only --scene <장면> --viewport <id>`) 뒤 `node scripts/visual-baseline/judge.mjs <폴더>` 로 누름 칸 44 · 입력 글자 16 · 지도 가림 · 가로 넘침을 판정한다(⑧). 게이트가 렌더된 크기를 재지 않으므로 터치 크기 회귀는 이 실행으로만 드러난다(PR 게이트 승격은 다음 intent).
- 글자 13px 이상(장식 글리프 `::before`/`::after` 는 제외 — #15) · 대비 4.5:1 이상(예외 — 누르는 동안(`:active`)만의 순간 상태는 이 합격선 밖이다. 평상시·hover·초점 상태는 그대로 4.5:1 · 실측 라이트 카탈로그 행 회색 글자 on 누름 면 4.23:1 · 다크 보조 글자 on 누름 면 4.02:1 · design-fix 20260924 값 20 · 비활성(`:disabled`) 컨트롤은 합격선 밖 — WCAG 1.4.3 · 1.4.11 비활성 예외(흐린 단추 글자 대비 라이트 2.12–3.46 · 다크 3.24–4.61 · design-fix 후속 20260925 Q1f)) · 카드 그림자 0(팝오버 · 상단 고정바 `.gnb` · 전체화면 모달 `.modal-takeover` 허용 — design-review 20260924 #13) · 인터랙션 하한은 `design-review` 스킬 §0 의 정적 합격선과 `frontend-visual` 게이트가 본다.
- 누름 피드백 = hover 의 한 단 진한 값(`:active`) — 흰 면·투명 단추는 gray-100(design-fix 20260924 WU-A1–A4), 파란 채움은 primary-800(`.btn-primary` · `.btn-strong` · `.gnb-upload` · design-fix 후속 20260925 Q3a). hover 가 `--color-surface-hover` 인 자리의 누름은 `--color-surface-pressed`(값 19)를 쓴다(예: 카탈로그 표 행 · 상단 메뉴 링크 · 업로드 달력 `.dr-nav button` · `.dr-useg button`) — 두 테마에서 누름 ≠ hover.
- 비활성 = opacity .5 · cursor not-allowed(`:disabled` · 단추 프리미티브 `.btn:disabled` 한 규칙 ＋ btn 계열 밖 단추는 화면 CSS 에 같은 두 값 · design-fix 후속 20260925 Q1a · Q1b · Q1e).

## ⑥ 게이트 `frontend-design-lint` — 조건 a~i

실행: `bash gates/run.sh frontend-design-lint`(판정부 `frontend/scripts/design-lint.mjs` + `frontend/scripts/design-docs.mjs --check` · 셸 `gates/tools/frontend-design-lint.sh`). 증명: `bash gates/run.sh frontend-design-lint-selftest`. 요약줄 끝 = `… · 프리미티브 맨 정의 밖 e(면제 m) · 폭·입력 조건 밖 i(면제 m) · 문서 표 갈림 h`(판정부 요약의 끝이 i 이고 셸이 h 를 붙인다 · 면제 m = 목록 줄 수 · 적중 수는 계수 줄 `i_exempted_hits`).

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
| i | 허용 값 밖 폭 조건(`max-width` 640·900·1180px · `min-width` 641·901·1181px 밖의 px 값) · 형식 밖 조건(높이 · 범위 문법 · em·rem · `orientation` · `aspect-ratio` · `any-pointer`·`any-hover` · `(pointer: fine)`·`(hover: none)` · `not`·`only` · 매체 종류 · 그 밖의 기능) · 선언 없는 `@container` · 면제 목록 구멍(형식 오류 · 빈 사유 · 개수 어긋남 · 맞는 것 없음 · 같은 조건 두 줄) · `(hover: hover)` 밖 `:hover`(둘러싼 모든 `@media` 의 모든 쉼표 갈래에 `and` 로 들어 있어야 한다 · 면제 없음) | `i 폭 조건(허용 값 밖)` · `i 형식 밖 조건` · `i 선언 없는 @container` · `i (hover: hover) 밖 :hover` · `i 면제 목록 구멍` · 계수 `media_rules` · `container_rules` · `hover_rules` | 가장 가까운 허용 값으로(배치가 바뀌면 판정) · 입력 조건은 `(pointer: coarse)` · `(hover: hover)` 로 · `:hover` 는 `@media (hover: hover) { … }` 로 감싼다 | `media-exempt.txt`(파일 · 조건 · 개수 · 사유 · ⑨) |

**red(준비 · 종료 78)** — 판정하지 못한 것은 통과가 아니다: node 부재 · 판정부 스크립트 부재 · 대상 CSS 0건 · 목록 파일(`same-in-dark.txt` · `primitives.txt` · `primitives-exempt.txt` · `media-exempt.txt`) 부재 · Git 목록에 있으나 디스크에 없는 CSS · `typescript` 파서 부재 · (h) 이 문서 · 표지 짝 · 입력 파일 부재.
**h 의 입력** — h 는 저장소의 문서와 저장소의 실물만 비교한다(`COLAB_FRONTEND_DIR` 픽스처 교체와 무관). 문서 경로는 env `COLAB_DESIGN_LINT_DOC`(기본 `docs/design-system.md`)로 바꿀 수 있고 selftest 가 이것으로 갈림 red 와 부재 78 을 만든다.
**못 보는 것** — 화면 루트 범위 색 토큰의 다크 짝 · 여백·글자 크기 리터럴(눈금 확정 전이라 red 조건이 아니다) · 요소 이름이 붙은 compound(`button.btn`)의 맨 정의 · 층 감싸기(`layer-count.mjs` 는 P2a 계측 도구이고 게이트가 아니다) · 실제 렌더(캡처 대조가 본다) · (i) JS 폭 측정(`ResizeObserver` 로 바꾸는 배치 — 지도 칸 경계는 vitest 가 ⑨ 표와 코드 상수를 대조한다) · TSX 안의 입력 조건 문자열(입력 방식 훅 `frontend/src/components/common/useInputMode.ts` 한 곳 · vitest 로 고정) · `src` 밖 HTML(`index.html` 등)의 조건 · 렌더된 누름 칸 · 글자 크기(캡처 도구 수치 모드가 잰다).

## ⑦ 판정 대기 목록

P1~P3 · P2a · P2b · P5 보고서에서 「Ted 판정」·「판정 필요」로 남은 항목을 모았다. 시각 항목은 결정하면 **시각 변경이 생긴다** — 구조 단계(값 무변) 밖이며 각자 별건으로 처리한다.

### 시각 값

| # | 항목 | 오늘 렌더 | 선택지 | 출처 |
|---|---|---|---|---|
| 10 | 화면 편차 통일(③ 화면 편차 목록 · 버튼 높이·모서리·칩 여백 등) | 화면마다 다름 | 편차 목록 유지 · 통일안 | P2b 우려 1 · P5 우려 1 |
| 17 | 빨간 삭제 단추 hover · 누름 없음 | 기본 = hover = 누름 | 새 빨간 단계 토큰 · 전역 `.btn-danger` | intent `dev-package/intent/2026-09-25-design-fix-followups.md` Q3b · Q5 |

### 닫힘 — design-review 20260924

Ted 판정(2026-09-25) · spec `dev-package/prd/specs/S-DESIGN-FIX-20260924.md`. 종전 시각 값 1–9 행을 여기로 옮겼다.

| ⑦ | 판정표 묶음 | 판정 | 처리 |
|---|---|---|---|
| 1 억눌린 hover | 9 | ⓐ | primary-700 · secondary gray-50(값 10) · L1 |
| 2 억눌린 상태 4종 | 18 | ⓑ | 그대로 · 코드 0 |
| 3 `.btn-sm` | 12 | ⓐ | 작은 단추 정의(값 11) · L1 |
| 4 `.chip--off` 배경 | 11 | ⓑ | `.chip` 배경을 기존 토큰으로(값 12) — 6 과 함께 닫힘 · L1 |
| 5 `.btn-strong:hover` | 10 | ⓑ | primary-700 · L2 |
| 6 `.chip` `#eef2f7` | 11 | ⓑ | 기존 토큰 · 게이트 f 면제 0 · L1 |
| 7 `.dl-keep` 바탕 | 20 | ⓑ | 그대로 · 코드 0 |
| 8 계보 안내 줄 주석 | 19 | ⓐ | 주석을 렌더에 맞춤 · L1 |
| 9 `.de-req` 다크 | 17 | ⓐ | 새 뜻 토큰(값 13) · L1 |

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
| 수치 판정 | `npm run visual:capture -- --label <이름> --metrics` → `node scripts/visual-baseline/judge.mjs [--lane <L>] <폴더>` | 캡처마다 수치 파일(누름 칸 · 입력 글자 · 지도 가림 · 가로 넘침)을 남기고 판정한다(종료 0/1/78 · 대상 목록 `targets.json` · 면제 `judge-exempt.txt`). PR 게이트가 아니다 |
| 대조 | `npm run visual:diff -- <기준> <후보> <보고>` | 엄격(`threshold 0` · `includeAA`) 픽셀 대조. 명세 sha256 · 장면 집합이 다르면 78. `--subset` 을 앞에 붙이면 두 쪽에 공통인 장면만 비교한다(장면을 더한 커밋과 이전 기준을 잇는 용도 · 보고에 빠진 장면을 적는다) |
| 캐스케이드 지도 | `node scripts/cascade-map.mjs map` · `verify --base <rev>` · `family --name <n> --classes <목록>` | 선언 단위 경쟁·승자 지도와 이동 검증(P2a · P2b) |
| 문서 표 | `node scripts/design-docs.mjs`(다시 쓰기) · `--check`(비교만 · 게이트 h) | ② · ③ 표지 안쪽을 실물에서 만든다. 날짜 없이 입력 sha256 만 적어 같은 입력이면 같은 글자다 |
| 게이트 | `bash gates/run.sh frontend-design-lint` · `frontend-design-lint-selftest` | ⑥ |

## ⑨ 폭 단계 · 입력 방식

화면 폭과 입력 방식(터치 · 마우스)에 따라 달라지는 규칙이다. 근거 = spec `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md`(intent `dev-package/intent/2026-09-26-device-width-input-rules.md` (a)).

- 이 절의 값은 손글이다. vitest(`frontend/test/device-width-input-20260926-L4.test.ts`)가 폭 표 · 허용 값 표를 공용 상수(`frontend/scripts/design-families.mjs`)와, 지도 칸 경계를 코드 상수와 대조한다.
- 게이트 i 가 폭 조건 · 입력 조건 · hover 위치를 판정한다(⑥). 렌더된 크기는 캡처 도구 수치 모드가 잰다(⑤ · ⑧).

### 폭 4단계

| 단계 | 화면 폭(px) | `@media` 표기 | 캡처 크기 |
|---|---|---|---|
| 휴대폰 | ≤640 | `(max-width: 640px)` | 390 |
| 패드 세로 | 641–900 | `(min-width: 641px) and (max-width: 900px)` | 820 · 844x390(휴대폰 가로) |
| 패드 가로 | 901–1180 | `(min-width: 901px) and (max-width: 1180px)` | 1024 · 1180 |
| PC | ≥1181 | `(min-width: 1181px)` | 1440 |

- 한 단계 안에서는 같은 배치를 쓴다. 단계 경계 밖의 폭 값은 새로 만들지 않는다(게이트 i · 기존 값은 면제 목록).
- 토큰의 640 · 900 분기(여백)는 이 단계의 경계다.

### 판단 기준

- 기본은 화면 폭(`@media` 폭 조건)이다.
- 부품 칸 폭(부품이 놓인 칸의 가로 px)은 세 자리에만 쓴다: 지도 · 그림 위 도구, 넓은 표, 표 안내.
- 부품 칸 폭은 JS 측정(`ResizeObserver`) 또는 `@container` 로 잰다. `@container` 는 면제 목록에 선언해야 한다(선언 없으면 게이트 i red · 지금 0개 · 지도 시범은 JS 측정).
- 방향(`orientation`) · 화면비(`aspect-ratio`)는 판단 기준이 아니다(게이트 i 형식 밖).

### 터치 기기 규칙

- 터치 기기 = `(pointer: coarse)` 가 참인 기기다. 판별할 수 없으면 마우스로 본다. TSX 에서는 입력 방식 훅(`frontend/src/components/common/useInputMode.ts`) 한 곳만 이 조건을 읽는다.
- 누름 칸은 가로 · 세로 44px(`--control-height`)이다. 고정 px 부품은 화면 CSS 끝의 `(pointer: coarse)` 블록 하나에서 최소 높이 · 최소 가로를 준다. 글자 크기와 마우스 모양은 바꾸지 않는다.
- 입력 글자는 16px 이상이다(iOS 초점 확대 방지). 규칙은 `shell.css` 의 「640px 이하 또는 터치 기기」 블록 한 곳이다(① 기본 층 행).
- `title` 에만 있는 정보는 두지 않는다. 보이는 글자 · 줄바꿈 · 누르면 보이는 설명(`aria-expanded` 단추) 중 하나로 보인다. 마우스에서는 `title` 을 그대로 둔다.
- hover 색 변화는 `@media (hover: hover)` 안에만 둔다(게이트 i 하위 조건). 초점 스타일은 조건 없이 둔다.
- 마우스 전용 동작에는 누름 대안을 둔다 — 더블클릭 맞춤 → 「데이터에 맞춤」 단추 · 마우스 이동 좌표 → 탭 좌표 · 끌어다 놓기 → 「파일 고르기」.
- 문구는 입력 방식에 맞춘다. 터치는 「누르면」 · 「고르면」, 마우스이거나 판별할 수 없으면 기존 문구다.

### 낮은 높이 규칙

| 항목 | 값 | 상태 |
|---|---|---|
| 낮은 높이 | 창 높이 ≈500px 이하(휴대폰 가로 844x390 등) · 메뉴 1줄 · 창 머리 · 바닥 축소 | 값 잠정 · 확정과 적용은 다음 intent(배치 정리) · 게이트 허용 값 없음(높이 조건은 i 형식 밖) |

- 판정 자료는 최종 캡처의 844x390 수치다.

### 넓은 표 원칙

| 항목 | 휴대폰(≤640) | 패드 이상(≥641) |
|---|---|---|
| 넓은 표 | 행을 카드로 바꾼다 | 이름 · 작업 열 고정(가로로 밀어도 보인다 · 선례 구성원 권한 표) |

- 카드 설계(표 3–4개)는 다음 intent(넓은 표)다.
- 표 안내(「표를 좌우로 밀면 …」) 표시 조건은 지금 `primitives.css` 의 1100px 이다(면제 목록 · 다음 intent 에서 표 칸 폭(실제 넘침) 기준으로).

### 지도 · 그림 위 도구 원칙

| 항목 | 값 | 코드 |
|---|---|---|
| 지도 칸 경계 | 810px — 지도 칸(`section.pv-map` 가로)이 이 값 미만이면 아래 배치 | `MAP_CELL_BOUNDARY`(`frontend/src/components/preview/useMapCellWidth.ts`) |

- 810 미만: 도구 층에는 확대 묶음(확대 · 축소 · 기본 배율로 · 원본 해상도 안내 ＋ 터치의 「데이터에 맞춤」)만 둔다. 좌표 표시 → 값 조회 → 범례 → 스크린샷은 지도 틀 바로 아래 블록에 둔다.
- 810 이상이거나 폭을 모르면 지도 위 배치다. 입력 방식과 무관하다(좁은 마우스 창도 아래 배치).
- 도구는 확대 · 이동과 함께 움직이지 않는다(도구 층 한 겹). 배치 규칙은 도구 층 모듈(`PreviewOverlay`) 한 곳에 둔다.
- 한 손가락 끌기는 끌 범위가 있는 축에서만 지도를 옮기고, 나머지 축은 페이지를 스크롤한다(뷰포트 `touch-action`).

### 허용 폭 값 · 면제 목록

| 조건 | 허용 값 | 비고 |
|---|---|---|
| `max-width` | 640px · 900px · 1180px | 단계 위 경계 |
| `min-width` | 641px · 901px · 1181px | 단계 아래 경계 |
| 입력 | `(pointer: coarse)` · `(hover: hover)` | 이 두 표기만 쓴다(`(pointer: fine)` · `(hover: none)` · `any-*` 는 red) |
| `prefers-*` | 판정하지 않고 센다(`media_prefers`) | `prefers-reduced-motion` 등 |
| 높이 · 범위 문법 · em·rem · `orientation` · `aspect-ratio` · `not` · `only` · 매체 종류 | 없음 | 형식 밖 red |

- 쉼표(OR) 목록은 갈래마다 판정한다. `(max-width: 640px), (pointer: coarse)` 는 허용이다.
- 면제 목록 = `gates/fixtures/frontend-design-lint/media-exempt.txt` — 16줄 · 24건(허용 값 밖의 기존 규칙). 한 줄 = `파일 · 조건 · 개수 · 사유`. 줄 번호는 적지 않고 정규화한 조건으로 대조한다(붙여 쓴 `@media(max-width:720px)` 와 띄어 쓴 표기는 같은 조건).
- 사유 종류: 이동 예정 23건(다음 intent(배치 정리)에서 640 · 900 · 1180 으로 · 표 안내 1건은 다음 intent(넓은 표)에서 표 칸 폭 기준으로) · 영구 예외 1건(로그인 계정 표 `min-width: 1536px` · 열 예산 도출값).
- 줄에 개수를 적는다. 같은 값의 새 규칙이 기존 면제 줄로 통과하지 못하게 한다 — 개수가 어긋난 줄은 red 이고 아무것도 면제하지 않는다. 빈 사유 · 맞는 것 없는 줄 · 형식 오류 · 같은 조건 두 줄도 red 다.
- 형식 밖 입력 조건 · `@container` 가 필요하면 이 목록에 사유와 개수로 선언해 판정받는다. hover 하위 조건은 면제하지 않는다.
