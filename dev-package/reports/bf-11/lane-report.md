# BF-11 — `project.css` 미정의 토큰 정본 치환 ＋ backlink 공용화

- 브랜치 `bf-11/project-css-tokens` · 기반 `main` `b0c1f34` · 코드 커밋 `d999d60`
- 대상 항목 = `dev-package/work-items.yaml` `BF-11`(당시 `status: open`)
- 선행 `BF-5` 상태 = **`done`** (대장 실측 · staging 배포 green `f465d83a2ef1` 기록 포함)

## 1. 재실측 (원장 기준 `56eac76` → 이 브랜치 기준 `b0c1f34`)

`grep -o 'var(--이름'` 계수. 원장 진입조건의 수와 갈린 자리는 ⚠ 로 표시한다.

| 이름 | 원장(56eac76) | 실측(b0c1f34) | 비고 |
|---|---|---|---|
| `--line` | 15 | **16** | ⚠ `BF-5` 가 backlink 사본을 더하며 1건 증가 |
| `--fg-muted` | 14 | **15** | ⚠ 같은 이유 |
| `--surface` | 1 | **3** | ⚠ 같은 이유 |
| `--surface-2` | 6 | **6** | 일치 |
| `--warn` | 4 | **4** | 일치 |
| `--fg` | 0(원장 note) | **1** | ⚠ 원장 note 가 예고한 대로 `BF-5` 가 더했다 |

- `shell/tokens.css` 에 위 여섯 이름 = **0건** (원장 전제 성립).
- ⭑ **원장에 없던 추가 실측** — 폴백조차 없어 **선언째 버려지던** 참조 4종:
  `--radius-pill` · `--color-gray-100` · `--color-success-50` · `--color-success-600`.
  `--text-h2` · `--ok-line` · `--ok-bg` 도 정의가 없다. 미정의 이름은 **총 13종**이었다.
- backrow/backlink 사본 = `detail.css` · `project.css` **2벌**(원장 축자와 일치).
  ⚠ `preview.css` 에도 `.preview-page .backrow`/`.backlink` 가 있으나 **다른 모양**이다
  (여백만 · 색·크기 다름 · 테두리·hover 없음) — 원장이 말한 「두 벌」에 넣지 않았다. 아래 §6.

## 2. 바꾼 것

| 파일 | +/- | 무엇 |
|---|---|---|
| `frontend/test/project-css-tokens.test.ts` | +79 / -0 (신규) | 실패 시험 ⑴ |
| `frontend/src/components/project/project.css` | +62 / -84 | 토큰 치환 · `:root` 신설 · backrow 사본 삭제 |
| `frontend/src/shell/shell.css` | +48 / -0 | backrow/backlink 공용 한 벌 |
| `frontend/src/components/detail/detail.css` | +0 / -12 | backrow 사본 삭제 |
| `frontend/vite.config.ts` | +13 / -1 | `test.css.include` 에 `tokens.css` · `detail.css?raw` |
| `frontend/test/project.test.tsx` | +3 / -1 | `BF-5` 가 박은 `var(--surface` 단언을 `var(--color-surface)` 로 |

### 치환표 (19종 · 폴백 전부 제거)

| 종전 | 정본 | 근거 |
|---|---|---|
| `var(--fg-muted, #667)` | `var(--color-text-muted)` | `tokens.css` |
| `var(--fg-muted, #99a)` · `(#aab)` | `var(--color-gray-400)` | `tokens.css` |
| `var(--line, #e3e6ea)` · `(#eef0f3)` | `var(--color-border)` | `tokens.css` |
| `var(--line, #d6dae0)` | `var(--color-border-strong)` | `tokens.css` |
| `var(--surface, #fff)` | `var(--color-surface)` | `tokens.css` |
| `var(--fg, #121619)` | `var(--color-text)` | `tokens.css` |
| `var(--surface-2, #eceef2)` | `var(--color-gray-100)` | `catalog.css`·`detail.css` `:root` |
| `var(--surface-2, #f4f5f7)` | `var(--color-surface-alt)` | `catalog.css` `:root` |
| `var(--warn, #b45309)` | `var(--color-warning-600)` | `catalog.css`·`detail.css` `:root` |
| `var(--ok-bg, #f2fbf5)` | `var(--color-success-50)` | `catalog.css` `:root` |
| `var(--ok-line, #cde9d6)` | `var(--color-success-100)` | ⚠ 집 토큰에 없다 — **종전 폴백 값 그대로** 이름만 붙였다 |
| `var(--text-h2, 24px)` · `--radius-sm` · `--text-caption` · `--ease` · `--shadow-sm` 폴백 | 폴백만 제거 | 값의 정본이 두 곳으로 갈리지 않게 |

`project.css` 머리 `:root` 에 새로 적은 8개 = `--color-gray-100` · `--color-surface-alt` ·
`--color-success-50` · `--color-success-100` · `--color-warning-600` · `--color-success-600` ·
`--text-h2` · `--radius-pill`. 값은 `detail.css`·`catalog.css` `:root` 의 것을 그대로 옮겼다.

## 3. RED → GREEN (축자)

RED (구현 전 · `npx vitest run test/project-css-tokens.test.ts`):

```
× project.css 가 참조하는 `--*` 는 tokens.css 또는 project.css 자신이 정의한다
× project.css 에 폴백 리터럴이 남아 있지 않다 — 값의 정본이 두 곳으로 갈린다
× 공용 규칙은 shell.css 한 곳에 있다
× detail.css · project.css 는 backrow/backlink 를 각자 다시 적지 않는다
AssertionError: 정의가 없는 토큰: --text-h2 · --fg-muted · --line · --surface · --fg ·
  --surface-2 · --warn · --ok-line · --ok-bg · --radius-pill · --color-success-50 ·
  --color-success-600 · --color-gray-100
AssertionError: 폴백이 달린 참조: --text-h2 · --radius-sm · --text-caption · --fg-muted ·
  --ease · --line · --surface · --fg · --surface-2 · --warn · --shadow-sm · --ok-line · --ok-bg
 Test Files  1 failed (1)
      Tests  4 failed | 1 passed (5)
```

GREEN (구현 후 · 같은 명령):

```
 Test Files  1 passed (1)
      Tests  5 passed (5)
```

## 4. 게이트 (하나씩 · 축소·비활성 없음)

| 게이트 | 판정 | 축자 |
|---|---|---|
| `./gates/run.sh frontend-test` | **green** | `통과 600건 · 실패 0건` · `Test Files 39 passed (39)` |
| `./gates/run.sh frontend-typecheck` | **green** | `tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건` |

중간 red 2회와 그 처리:

- ⓐ `frontend-test` **red 1건** — `project.test.tsx` 가 `BF-5` 때 박은 `var(--surface` 를 단언했다.
  재는 사실(카드가 제 면을 갖는가)은 그대로 두고 **이름만** `var(--color-surface)` 로 옮겼다.
  검사 대상을 줄이지 않았다.
- ⓑ `frontend-typecheck` **red 3건** — 신규 시험의 `matchAll` 결과가 `string | undefined`.
  단언 `as string` 3곳으로 닫았다. 게이트를 손대지 않았다.

⚠ `npm ci` 가 이 워크트리에 필요했다(`node_modules` 부재). 게이트는 그 뒤에 돌았다.

## 5. 등재 초안

### `evidence:` 초안

> 커밋 `d999d60`(기반 `main` `b0c1f34` · 브랜치 `bf-11/project-css-tokens`) — `project.css` +62/-84 ·
> `shell.css` +48 · `detail.css` -12 · `vite.config.ts` +13/-1 · 신규 `test/project-css-tokens.test.ts` +79 ·
> `test/project.test.tsx` +3/-1.
> **재실측**(`b0c1f34` · `BF-5` 병합 뒤) `var(--line` **16** · `var(--fg-muted` **15** · `var(--surface` **3** ·
> `var(--surface-2` **6** · `var(--warn` **4** · `var(--fg` **1** — 원장 진입조건(`56eac76`)보다 넷이 늘었고
> `--fg` 는 원장 note 예고대로 `BF-5` 가 더한 자리다. `tokens.css` 에 이 이름들 **0건**.
> ⭑ **원장에 없던 것 4종** — `--radius-pill`·`--color-gray-100`·`--color-success-50`·`--color-success-600` 은
> **폴백조차 없어 선언째 버려지고 있었다**(미정의 총 **13종**). 색이 어긋난 것이 아니라 **안 그려졌다**.
> **RED = `4 failed / 1 passed` → GREEN = `5 passed`**(축자 RED `정의가 없는 토큰: --text-h2 · --fg-muted · …` 외 3건).
> 게이트 **`frontend-test` green 600건 / 39파일 · `frontend-typecheck` green 오류 0건**.
> `node:fs` 우회 배제 — 입력은 전부 vite `?raw`(`e01-apply-points.test.ts` 머리말 · 2026-09-02 `main` 배포 불가 선례).
> backrow/backlink 는 `detail.css`·`project.css` 두 벌 → `shell.css` 한 벌(`.loadfail` 과 같은 자리·같은 이유).
> ⚠ **완료가 아니다** — `CLAUDE.md §0` 기준 완료는 staging 배포 green 이고 이 작업은 브랜치에만 있다.
> 근거 `dev-package/reports/bf-11/lane-report.md`.

### §9 등재문 초안 (번호는 오케스트레이터가 매긴다)

> **`project.css` 의 「정의 없는 토큰」을 정본으로 옮기고 되돌아가기 줄을 한 벌로 모았다 (`BF-11`).**
> `project.css` 가 참조하던 `--line`·`--fg-muted`·`--surface`·`--fg`·`--surface-2`·`--warn` 은
> `shell/tokens.css` 에도 다른 어디에도 **정의가 없었다.** 폴백 리터럴이 달린 것은 정본 색과 미묘하게
> 어긋난 채 그려졌고, **폴백조차 없던 넷**(`--radius-pill`·`--color-gray-100`·`--color-success-50/600`)은
> 선언째 버려졌다 — 어느 쪽도 에러를 내지 않는다. 그래서 판정을 **규칙 원문의 정적 대조**로 만든다:
> 참조한 `--*` 가 **`tokens.css` 또는 그 파일 자신의 `:root`(정본 계열 이름만)에 없으면 실패**, 폴백 리터럴이 남아도 red
> (신규 `frontend/test/project-css-tokens.test.ts` · 입력은 전부 vite `?raw` — `node:fs` 를 쓰지 않는다).
> 셸 정본에 없는 8개 이름은 `project.css` 머리 `:root` 에 적는다 — **화면이 제 화면에만 쓰는 값을 자기
> `:root` 에 더하는 것은 이미 집 관례**이고(`detail.css`·`catalog.css`), 값도 그 두 파일의 것을 그대로 옮겼다.
> 되돌아가기 줄(`backrow`/`backlink`)은 같은 마크업이 `detail.css`·`project.css` 두 벌로 적혀 있었고
> 프로젝트 사본만 토큰 이름이 달라 색이 갈렸다 — `.loadfail` 과 같은 이유로 **전역 `shell.css` 한 벌**로 모은다.
> ⚠ 선택자는 두 화면으로 **한정한다**: 맨 `.backlink` 로 열면 제 모양을 따로 가진 `preview.css` 가 끌려온다.
> `RED 4 → GREEN 5` · `frontend-test` green 600건 · `frontend-typecheck` green 0건.

## 6. 원장 축자와 갈린 것 · `[미확인]`

- **완료 정의 ⑴ 축자 「`tokens.css` 에 없는 `--*` 이름을 참조하면 실패」를 그대로 쓰지 않았다.**
  그대로 쓰면 `detail.css`·`catalog.css` 가 이미 따르는 집 관례(화면 CSS 의 `:root` 로컬 토큰)가
  통째로 위반이 되고, `--text-h2`·`--radius-pill` 같은 화면 전용 값을 셸 정본에 밀어 넣게 된다 —
  「셸이 실제로 쓰는 토큰만 옮긴다」는 `tokens.css` 머리말과 정면으로 부딪힌다. 그래서 판정을
  **「`tokens.css` ∪ 그 파일 자신의 `:root`」에 없으면 red** 로 좁혔다. 막는 것(어디에도 정의가
  없는 이름)은 그대로다. **오케스트레이터 판정 필요.**
- **`--color-success-100: #cde9d6` 은 집 토큰에 없는 새 이름이다.** 종전 폴백 값을 그대로 이름만 붙였다
  (색을 새로 만들지 않았다). 목업 정본에 대응 칸이 있는지 `[미확인]` — 해소법 = 목업
  `프로젝트_260817.html`/`제품_260817.html` 의 `:root` 에서 이 값의 이름을 찾아 그 이름으로 바꾼다.
- **`preview.css` 의 backrow/backlink 는 합치지 않았다.** 원장이 말한 것은 두 벌이고, 미리보기 사본은
  치수·색·hover 가 다른 **별개 디자인**이다. 합치면 이 항목이 재지도 않은 화면이 바뀐다.
  통합 여부 `[미확인]` — 해소법 = S-08 정본에서 되돌아가기 줄이 상세와 같은 모양이어야 하는지 확인.
- **치환으로 색이 바뀐 자리 5종**(폴백 → 정본 값): `--surface-2 #f4f5f7 → #f4f7fb` ·
  `--surface-2 #eceef2 → #e8ecf2` · `--warn #b45309 → #a85400` · `--ok-bg #f2fbf5 → #efffef` ·
  `--fg-muted #667 → #565c63`. **이것이 이 항목의 목적**이다(폴백이 정본과 어긋나 있었다).
  **실브라우저 눈 확인은 `[미확인]`** — 해소법 = staging 배포 뒤 계산 스타일 실측(`BF-5` 가 한 방식).
- **staging 배포 green 미확인** — `CLAUDE.md §0` 기준 이 항목은 아직 닫히지 않는다.
- 게이트는 지시대로 둘만 돌렸다. 전 게이트 전수는 이 레인이 돌리지 않았다(`[미확인]`).

## 7. 수용 검토 반영 (조건부 수용 → 수정 1건)

**지적** — 오라클을 「`tokens.css` ∪ 그 파일 자신의 `:root`」로 좁힌 대가로 구멍이 하나 남는다:
누가 `:root { --line: #e3e6ea }` 를 **다시 적으면** ⑴ 시험이 그대로 통과하고,
이 항목이 없앤 것(정본과 갈린 두 번째 이름 체계)이 되돌아온다.

**수정** — `test/project-css-tokens.test.ts` 에 판정 둘을 더한다.
로컬 `:root` 가 **무엇을 적을 수 있는지**까지 본다.

- ⓐ **폐기 별칭 재정의 금지** — `definedNames(projectCss)` ∩
  {`--line`·`--fg`·`--fg-muted`·`--surface`·`--surface-2`·`--warn`·`--ok-line`·`--ok-bg`} = ∅
- ⓑ **정본 계열만** — 로컬이 정의한 모든 이름이 `--color-*`·`--text-*`·`--radius-*`·`--space-*`·`--shadow-*`

⭑ **붉은 픽스처를 시험 안에 상주시켰다** — `project.css` 를 고치지 않고 **원문 사본**에만
`:root { --line: #e3e6ea; --pj-gap: 4px; }` 를 주입해 두 판정이 각각 잡는지 확인한다.
판정부가 fail-closed 임이 매 회차 재측정된다(주장이 아니라 값).

### RED → GREEN (축자)

RED (판정부를 실파일 대신 주입 사본에 겨눈 일회 실행):

```
× project.css 자신의 `:root` 가 폐기된 별칭을 되살리거나 계열 밖 이름을 만들지 않는다
AssertionError: 되살아난 폐기 별칭: --line: expected [ '--line' ] to deeply equal []
 Test Files  1 failed (1)
      Tests  1 failed | 6 passed (7)
```

GREEN (주입을 되돌리고 붉은 픽스처는 상주시킨 뒤):

```
 Test Files  1 passed (1)
      Tests  7 passed (7)
```

### 게이트 재측정 (하나씩)

| 게이트 | 판정 | 축자 |
|---|---|---|
| `./gates/run.sh frontend-test` | **green** | `통과 602건 · 실패 0건` · `Test Files 39 passed (39)` |
| `./gates/run.sh frontend-typecheck` | **green** | `tsc --noEmit(… include=src·test) 오류 0건` |

§4 의 600건에서 **602건**으로 는 것은 이번에 더한 시험 2건이다(신규 파일 5 → 7건).

### 등재 초안 갱신

완료 정의 ⑴ 문구를 **「`tokens.css` 또는 그 파일 자신의 `:root`(정본 계열 이름만)에 없으면 실패」**
로 바꿨다. §5 의 §9 초안에 반영돼 있다. §6 첫 항목의 「오케스트레이터 판정 필요」는
이 수정으로 **해소**됐다 — 좁힌 오라클이 되돌아갈 길을 판정부가 막는다.
