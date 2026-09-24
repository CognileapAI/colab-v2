# Spec: 디자인 구조 P2b — 프리미티브 단일 소유(`primitives.css` · `patterns.css`) · 게이트 e
출처 intent: `dev-package/intent/2026-09-24-design-system-structure.md` (승인 2026-09-24 · Q2 `@layer` · Q4 시각 변경 0)
계획: `dev-package/reports/design-system/20260924/architecture.md §2-1·§2-2 e·§3 P2b` · 조사: `p2/design-system-map.md §2`(계열별 정의 전수·충돌) · 선행 결과: `p2a/report.md`(흡수 · `cascade-map.mjs` `verify` · 계산값 전수 대조) · P3(리터럴·폴백 정리 · 게이트 f·g)
선행: P0 · P1 · P2a · **P3**(P3 병합 뒤 착수 · 두 단계가 `upload.css` 를 함께 건드린다)

## 문제 진술
- 공통 부품의 기본 규칙이 여전히 여러 파일에 있다 — 조사 §2: `.btn` 40곳/11파일 · 입력(`.inp`·`.sel`·`.login-input`) 63곳/13파일 · `.card` 38곳/9파일 · `.chip` 26곳/9파일 · 모달 115곳/8파일(계열 5개 병존) · 표 106곳/7파일(공유 기반 없음) · 탭 17곳(계열 3개). P2a 는 보정 층의 프리미티브·패턴 규칙 22+5 를 `shell.css` 끝(433행 아래)에 **임시로** 두었다.
- `@layer primitives`·`patterns` 는 이름만 선언돼 있고 비어 있다. 클래스 이름의 소유자가 하나가 아니므로 게이트 e(맨 클래스 정의는 한 파일에만)를 세울 수 없다.
- **층 순위 함정**: `shell.css` 끝의 규칙은 screens 층의 마지막이라 같은 특이도의 화면 규칙을 **순서**로 이긴다. 그대로 primitives 층으로 내리면 화면 규칙이 이겨 렌더가 바뀐다. 「먼저 옮기고 보자」는 시각 변경 0 이 아니다.

## 해법 개요
- 0단계(`base` 층 · 원소 규칙)를 먼저 하고, 계열마다(btn → field → chip → card → table → modal) ① 오늘의 **기본값**(문맥 없는 맨 클래스에서 이기는 선언 집합)을 `primitives.css`/`patterns.css` 로 옮기고 ② 그 기본값이 오늘 **순서**로만 이기던 화면 파일의 경쟁 선언(죽은 선언)을 삭제·일치시키며 ③ 오늘 **특이도**로 이기는 화면 편차(`.memgrid .btn` 류)는 그대로 둔다(값 통일은 시각 결정 · 범위 밖). 판정은 P2a 의 `cascade-map.mjs verify` + 계산값 전수 대조 + 캡처 196장.
- 게이트 e: `primitives.css` 밖 CSS 에서 프리미티브 클래스의 **맨 정의**(문맥 없는 `.btn { }` · `.btn:hover { }` · `.btn--x { }` · 목록 인자 포함)가 있으면 red. 화면 범위 선택자(`.memgrid .btn`)는 허용.
- `--up-*` 6종·`--lin-over-*` 3종(P1 에서 정본으로 승격)은 **9/9 전부 값이 같은 정본 토큰이 있다**(`tokens.css` 별칭 실측 · 다크에서도 재정의 없음): `--up-line`→`--color-border` · `--up-muted`·`--lin-over-name`→`--color-text-muted` · `--up-ink`→`--color-text` · `--up-warn`·`--lin-over-ink`→`--color-warning-600` · `--up-warn-bg`·`--lin-over-bg`→`--color-warning-50` · `--up-radius`(12px)→`--radius-lg`. 참조를 전부 바꾸고 9개 이름을 `tokens.css` 에서 지운다(값 무변 · 게이트 b 가 남은 참조를 잡는다). 기대 결과 「9/9 치환 · 이름 삭제 9」.
- 보이는 값은 바뀌지 않는다 — 196장 엄격 차이 0 · 계산값 전수 대조 0 · 상태 강제 계측(P2a 16건 + focus-visible 추가).

## 사용자 스토리
1. 화면을 만드는 작업자로서 버튼·입력·칩·카드·표·모달의 기본 모양을 한 파일에서 보고, 내 화면의 편차만 내 파일에 적고 싶다.
2. 검토자로서 새 PR 이 `.btn { }` 을 화면 파일에 다시 정의하면 게이트가 red 를 내길 바란다.
3. Ted 로서 계열별로 「기본값 · 화면별 편차 목록」을 표로 보고, 편차를 통일할지는 나중에 따로 판정하고 싶다.

## 구현 결정
- **0단계 — `base` 층을 먼저 채운다(층 함정의 두 번째 면)**: primitives 층은 screens 층의 **어떤 특이도**에도 진다. 그래서 오늘 특이도로 지던 낮은 특이도 규칙이 이동 뒤 이긴다 — 실물 = `shell.css` 의 `*` 리셋(11행) · `button, input, select, textarea { font-family: inherit; letter-spacing: inherit }` · `button { font-size: var(--text-body-sm) }` · `:where(button, a, input, select, textarea):focus-visible` · 640px 분기의 `input, select, textarea { font-size: 16px }`(100~106 · 416행 근방). 이 원소·`:where()`·전체 선택자 규칙을 새 `frontend/src/shell/base.css` = `@layer base { … }` 로 옮기고 `verify`·계산값 대조를 돌린 뒤 계열 작업에 들어간다. `!important` 2건(`shell.css` 미디어 블록)은 screens 층에 남긴다. **`primitives.css`·`base.css` 에서는 `!important` 를 금지**한다(게이트 e 의 부조건).
- **파일·층**: `frontend/src/shell/base.css` · `frontend/src/shell/primitives.css` = `@layer primitives { … }`. `patterns.css` 는 **P5 로 미룬다**(아래). `styles.ts` 순서 = `layers.css` → pretendard → `tokens.css` → `base.css` → `primitives.css` → 화면 CSS → `shell.css`. `vite.config.ts` `test.css.include` 에 두 파일 추가.
- **계열 정의(프리미티브 클래스 목록 = 게이트 e 의 정본)**: 파일 = `gates/fixtures/frontend-design-lint/primitives.txt`(P1 의 `same-in-dark.txt` 와 같은 자리·주입 방식 — env `COLAB_DESIGN_LINT_PRIMITIVES` · `design-lint.mjs --primitives` · `frontend-design-lint.sh` 의 78 조건 한 줄 「목록 부재」). 형식 = 한 줄에 클래스 하나, 접두사 표기 `.chip--*` 허용. 내용: btn = `.btn` `.btn-primary` `.btn-secondary` `.btn-ghost` `.btn-danger` `.btn-sm` · field = `.inp` `.sel` · chip = `.chip` `.chip--*` · card = `.card` `.card-h` `.card-b` · table = `.tbl` `.tblwrap` `.table-scroll-hint` · modal = `.modal-back` `.modal` `.modal--dialog` `.modal-h` `.modal-b` `.modal-f`. **목록은 계열 커밋마다 그 계열 클래스만 추가**한다 — 그래야 모든 계열 경계에서 `frontend-design-lint` 가 green 이다(부분 레인 대비). 탭(`.settabs`·`.pj-seg`·`.pj-views` 3계열) · `.login-input`·`.login-card`·`.pj-modal*`·`.labinfo-modal`·`.approval-dialog`·`.account-table`·`.pj-table`·`.vartable` 같은 **별 계열 이름은 이번 범위가 아니다** — 이름을 합치는 것은 TSX 변경(className)이라 별건(우려 2). 목록에 없는 이름은 게이트 e 대상이 아니다.
- **임시 블록의 비프리미티브 규칙**(`shell.css` 433행 아래 · `.theme-switcher` · `.gnb` 미디어 블록 · `:is(.lin-find, .lin-fix, .modal-takeover) .modal-h .x` 등)은 screens 층에 남긴다 — `shell.css` 본문 자리로 올리거나 소유 화면 파일로(값 무변 · `verify`).
- **칩 수식자 규칙**: `.chip--` 접두사는 프리미티브 이름공간이다. `.chip--verified`(`approval.css`)·`.chip--off`(`members.css`)의 색·배경·테두리 선언은 `primitives.css` 로 옮기고, `.chip--off` 의 `margin-left: 6px` 같은 **레이아웃 선언은 화면 범위 선택자**로 남긴다. `catalog.css` 의 `.chip--neutral`·`.chip--warning`(같은 값 중복)은 삭제. `members.css` 의 `.btn:where(:not(.btn-primary, .btn-secondary)):hover` 는 맨 정의이고 전 화면에 걸리므로 btn 기본값에 넣는다.
- **계열별 절차**(계열마다 커밋 1 · `verify` 와 계산값 대조를 계열마다 돈다):
  1. `cascade-map.mjs` 로 그 계열의 맨 클래스 선택자에 대해 전 파일의 정의를 모으고, 문맥 없는 요소(맨 클래스만 가진 요소)에서 오늘 이기는 선언 집합 = **기본값**을 낸다(P2a 가 `shell.css` 끝에 둔 규칙이 대부분 · 조사 §2 표 대조).
  2. 기본값을 `primitives.css`(패턴 계열은 `patterns.css`)에 접두사 없이 쓴다. `shell.css` 끝의 해당 규칙은 지운다.
  3. 화면 파일의 **경쟁 선언 전부**(같은 맨 클래스 정의 `members.css:46 .btn` 만이 아니라, 같은 요소에 같은 속성을 주는 더 낮은 특이도 규칙 — 원소·`:where()`·전체 선택자 — 까지 · `cascade-map.mjs` 가 낸다)를 선언 단위로 판정 — 기본값과 같은 값 → 삭제 · 오늘 순서**또는 특이도**로 지던 값 → 삭제(죽은 선언 · 이름·값 표기 · 0단계로 `base` 층에 간 것은 제외) · 기본값에 없는 속성으로 오늘 살아 있는 값 → 그 화면의 **범위 선택자**(`.memgrid .btn` · `.modal-takeover .btn`)로 옮긴다(특이도가 올라가므로 다른 문맥에 새는지 `verify` 로 확인).
  4. 오늘 특이도로 이기는 화면 편차(`.memgrid .btn` 류)는 무변.
  5. `verify` 문제 0 · 계산값 대조 0 을 확인하고 커밋.
- **패턴은 P5 로 미룬다**(advisor ① 권고): 페이지 컨테이너 `:is(.catalog-page, …)` · `.page-head h1` · `.form-row` 는 선택자에 화면 이름이 있어 층을 옮기면 층 함정 면이 하나 더 늘고, `.page` 로 이름을 바꾸는 TSX 변경 없이는 소유권 이득이 없다. `shell.css` 에 「P5 이관 대기」 표지 주석을 달고 남긴다. `.card-h h3` 만 card 계열로 `primitives.css` 에.
- **정리 항목(P2a 후속)**: 같은 조건 미디어 블록이 한 파일에 둘 생긴 곳을 합친다(`verify` 로 순서 안전 확인 · 값 무변) · `p2a/cascade-verify.md` 면제표에 미디어 열 추가 · `vite.config.ts` 껍질 제거 플러그인에 이스케이프 따옴표 한계 주석 · `.pj-seg button.on` outline 의 focus-visible 강제 계측 1건 추가. `.lin-picker li > button` 규칙 2개는 fixture DOM 에 안 걸릴 뿐 제품에서 죽었다는 증거가 없으므로 **지우지 않는다**(후속 항목으로 남김).
- **게이트 e**(`design-lint.mjs` 확장 · 요약줄 `프리미티브 맨 정의 밖 e(면제 m)`): 대상 = `primitives.css` 밖 전 CSS. red 조건 = 선택자 목록의 어느 인자든 **compound 하나**로 이루어져 있고 그 compound 가 `primitives.txt` 의 클래스(+가상 클래스/요소 · 속성 선택자)만으로 되어 있으면(`.btn` · `.btn:hover` · `.chip--warning`) red. 경계: `:is()`/`:where()` 인자는 **펼쳐서** 판정(펼친 compound 중 하나라도 해당하면 red · `:is(.btn, .foo)` 포함) · `:has()`·`:not()` 인자는 제외 · 비프리미티브 클래스와 섞인 compound(`.btn.foo`)는 허용 · 조상·자손 문맥(`.memgrid .btn` · `.btn .icon`)은 허용. `primitives.css`·`base.css` 안 `!important` → red. 목록 파일 부재 → 78. 면제 파일은 **따로**(`gates/fixtures/frontend-design-lint/primitives-exempt.txt` · 파일 · 선택자 · 사유 · 사유 없음 red · 낡은 항목 red · 건수 노출 — `same-in-dark.txt` 는 토큰 이름 형식이라 못 쓴다). selftest `red-e`(맨 정의 · 상태 맨 정의 · `:is()` 펼침 · `!important` · 목록 부재 78 · 사유 없는 면제) → 케이스 수 갱신(README 행).
- 스키마 · 마이그레이션: 없음. API 계약: 비파괴.

## 시험 결정
- ⓐ 게이트 e 착수 red — **전체 목록으로 한 번만 실행해 기록**(커밋하지 않는다 · 맨 정의 수를 계열별로 · 조사 §2 의 곳수와 대조) → 이후 목록은 계열 커밋마다 늘려 **매 계열 경계에서 green** → 최종 green 0(면제 n 노출). selftest 전건 기대대로. `frontend-design-lint` 나머지 조건 green 유지.
- ⓑ 시각 변경 0 — `visual:capture` 전·후(빌드 포함) → 196장 엄격 차이 0. `verify`·계산값 대조는 0단계와 계열마다. **레인이 계열 경계에서 멈추면 그 지점에서 ⓑ·ⓒ 를 실행**하고 진행표에 남은 계열을 적는다(handoff complete 는 그 지점의 green 게이트로 성립).
- ⓒ 상태 강제 계측 — P2a 의 16건 재실행 + `.pj-seg button.on` focus-visible + 프리미티브 계열의 `:hover`·`:focus-visible`·`:active`·`:disabled`(각 계열 대표 요소 1개씩) 전후 동일.
- ⓓ 계열별 표 — 기본값 선언 수 · 삭제한 죽은 선언(파일·이름·값) · 범위 선택자로 옮긴 편차(파일·선택자) · 남긴 특이도 편차. 합계가 조사 §2 의 곳수와 맞는지.
- ⓔ `frontend-typecheck`·`frontend-test`(계산값 시험 6 it 무변 · `test.css.include` 갱신)·`frontend-fixture-reach`·`frontend-design-lint`(+selftest) green.
- green-by-skip 방지: 목록 파일 부재 78 · 착수 red 기록 · 면제 건수 노출 · 계열별 `verify` 문제 0 을 표로.

## 정책 대조
- `product.md §3·§5` 저촉 없음(의존성 0 · 값 변경 0 · 절대경로 0 · TSX 변경 0). 계약 동결 해제: 아니오.

### 디자인 제약 확인
대상 화면: 전 화면(정의 위치만 바뀐다) · 값 무변 — 캡처 차이 0 · 계산값 대조 0 이 증거.

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 화면별 편차(`.memgrid .btn` 높이 32 vs 기본 40 등)를 이번에 통일할까 | 두 채로 둔다(시각 변경 0 · 편차 표만) | 통일(시각 변경 · Ted 판정) | ⓐ · 표를 P5 문서 「편차 목록」으로 |
| 2 | 별 계열 이름(`.login-input`·`.pj-modal`·`.account-table` 등)을 프리미티브로 합칠까 | 이번엔 목록 밖(게이트 e 미대상) | 합친다(TSX className 변경) | ⓐ · 별건 |
| 3 | P2b 가 200턴 안에 7계열을 다 못 끝낼 수 있다 | 계열 경계에서 끊고 이어 받는다(PR 1건 안 커밋 여러 개) | 두 PR 로 나눔 | ⓐ · 끊긴 자리는 보고서 진행표에 |

## 범위 밖
- 값 통일 · 이름 합치기 · TSX 변경 · 토큰 값·이름 변경 · `.lin-picker li > button` 삭제 · 커밋·push·PR 게시(사용자).

## 산출 계획
- 레인 1(직렬) · `lane-worker` · `isolation: worktree` · 기준 = P3 병합 뒤 통합 브랜치. 보고서 `dev-package/reports/design-system/20260924/p2b/report.md` + `p2b/visual/`. PR 본문 `~/.claude/pr-bodies/PR-BODY-design-structure-p2b.md`.
