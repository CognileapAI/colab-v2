#!/usr/bin/env bash
# frontend-design-lint 게이트 — 토큰 정본(`frontend/src/shell/tokens.css`) 단일화가 유지되는가.
#
# 왜 있는가 (spec `S-DESIGN-STRUCTURE-P1-20260924` · 대안 B):
#   토큰 정의가 정본 밖 7개 화면 CSS 의 `:root` 에 77건 흩어져 있었다(2026-09-24 실측). 같은 이름을
#   네 파일에서 대조해야 값을 알 수 있었고, 다크 값만 정본에 있는 이름이 17종이었다. BF-13 시험
#   (`shared-css-tokens.test.ts`)은 화면 파일끼리 값이 같은지만 봐서, 새로 흩어지는 것을 막지 못했다.
#
# 판정부 = 저장소의 `frontend/scripts/design-lint.mjs`(zero-dependency · node 만). 대상 트리가 픽스처여도
# 판정부는 저장소 것 하나를 쓴다. 이 셸은 대상 목록과 세 상태만 책임진다 (`frontend-fixture-reach.sh` 와 같은 골격).
#
# red 조건 (판정 · exit 1):
#   a. tokens.css 밖 `:root` 안의 `--*:` 정의 · 화면 범위 규칙의 정본 계열 이름
#      (`--color-` `--space-` `--text-` `--radius-` `--font-` `--shadow-` `--leading-` `--tracking-` `--fg-` `--bg-` `--accent-`)
#   b. 어디에도 정의되지 않은 `var(--x)` 참조(폴백 유무 무관)
#   c. 라이트 `:root` 의 색 계열 이름이 다크 블록·별칭·면제 목록 어디에도 없음 · 다크에만 있는 이름 ·
#      면제 목록의 구멍(사유 없음 · 라이트에 없는 낡은 항목 · 다크에 이미 있는 항목)
#   d. tokens.css 밖 `:root` 셀렉터(`html:root` 포함) · tokens.css 밖 전 CSS 의 `@import`(P2a 부터 셸 포함)
#   f. (P3 · spec `S-DESIGN-STRUCTURE-P3-20260924`) tokens.css 밖 CSS 의 색 리터럴 — hex · rgb()/rgba()/
#      hsl()/hsla()/hwb()/lab()/lch()/oklab()/oklch()/color()/color-mix()(토큰끼리의 혼합은 제외) · CSS 표준 색 이름 148개 — 직접 값이든
#      `var()` 폴백이든. 제외 = transparent · currentColor · inherit · initial · unset. 면제는 같은 목록
#      (same-in-dark.txt)의 `f · 파일 · 선택자 · 속성 · 리터럴 · 사유` 줄 — 사유 없음 · 걸리는 리터럴 없음(낡음)은 red.
#   g. (P3) `src/**/*.tsx` 의 JSX `style` 속성(펼침 속성 안의 `style` 키 포함) 값이 `--*` 키만 가진 객체 리터럴이 아님(축약형 `{ width }` ·
#      펼침 · 계산 키 · 객체 아닌 값 포함). TS 파서(`typescript` devDependency)로 읽는다 — 정규식이 아니다.
#   e. (P2b · spec `S-DESIGN-STRUCTURE-P2B-20260924`) `src/shell/primitives.css` 밖 CSS 의 프리미티브 **맨 정의** —
#      선택자 목록의 인자가 (`:is()`/`:where()` 를 펼친 뒤) compound 하나이고 그 compound 가 프리미티브 목록
#      (`primitives.txt` · 한 줄에 클래스 하나 · 접두 표기 `.chip--*`)의 클래스 + 가상 클래스/요소 · 속성 선택자만으로
#      되어 있음(`.btn` · `.btn:hover` · `.chip--warning` · `:is(.inp, .sel)`). `:not()`·`:has()` 인자는 보지 않는다 ·
#      목록 밖 클래스·요소와 섞인 compound(`.btn.foo`)와 조상·자손 문맥(`.memgrid .btn`)은 허용 ·
#      `primitives.css`·`base.css` 안의 `!important`. 면제 = `primitives-exempt.txt`(`파일 · 선택자 · 사유`) —
#      사유 없음 · 걸리는 맨 정의 없음(낡음)은 red.
#   h. (P5 · spec `S-DESIGN-STRUCTURE-P5-20260924`) 문서 `docs/design-system.md` 의 생성 표지 두 블록
#      (`<!-- generated:tokens -->` · `<!-- generated:primitives -->`)이 실물(`tokens.css` · `primitives.css` ·
#      목록 파일 셋)에서 다시 만든 표와 다름 — 판정부 `frontend/scripts/design-docs.mjs --check`(블록 안만 비교 ·
#      블록 밖 손글은 보지 않는다). h 는 **저장소의 문서 ↔ 저장소의 실물**만 본다 — `COLAB_FRONTEND_DIR`·목록 env 로
#      픽스처를 가리켜도 h 의 입력은 바뀌지 않는다(문서가 설명하는 것은 저장소다). 문서 경로만
#      env `COLAB_DESIGN_LINT_DOC`(기본 `docs/design-system.md`)로 바꿀 수 있다(selftest 가 갈림·부재를 만든다).
# 요약줄 끝 = `색 리터럴 f(면제 m) · 인라인 g(변수 대입 v) · 프리미티브 맨 정의 밖 e(면제 m) · 문서 표 갈림 h`.
# fail-closed (green-by-skip 금지 · red(준비) · exit 78):
#   · node 실행 파일 부재 · 판정부 스크립트 부재 · 대상 CSS 0건 · 면제 목록(same-in-dark.txt) 부재 ·
#     프리미티브 목록(primitives.txt) 부재 · 프리미티브 면제 목록(primitives-exempt.txt) 부재(P2b) ·
#     대상 목록(Git)에 있으나 디스크에 없는 CSS(추적 중 삭제 · P2a) · `typescript` 를 불러오지 못함(P3 · g) ·
#     (P5 · h) 문서 표 판정부(`design-docs.mjs`) 부재 · 문서 부재 · 표지 짝 부재·중복 · h 입력 파일 부재
#
# 입력: COLAB_FRONTEND_DIR(기본 frontend) · COLAB_DESIGN_LINT_SAME_IN_DARK(기본
#   gates/fixtures/frontend-design-lint/same-in-dark.txt) · COLAB_DESIGN_LINT_PRIMITIVES(기본
#   gates/fixtures/frontend-design-lint/primitives.txt) · COLAB_DESIGN_LINT_PRIMITIVES_EXEMPT(기본
#   gates/fixtures/frontend-design-lint/primitives-exempt.txt) · COLAB_NODE_BIN(기본 node · selftest 용) ·
#   COLAB_DESIGN_LINT_DOC(기본 docs/design-system.md · h 의 문서 경로 · design-docs.mjs 가 직접 읽는다).
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
FE="${COLAB_FRONTEND_DIR:-$REPO_ROOT/frontend}"
SAME_IN_DARK="${COLAB_DESIGN_LINT_SAME_IN_DARK:-$REPO_ROOT/gates/fixtures/frontend-design-lint/same-in-dark.txt}"
PRIMITIVES="${COLAB_DESIGN_LINT_PRIMITIVES:-$REPO_ROOT/gates/fixtures/frontend-design-lint/primitives.txt}"
PRIMITIVES_EXEMPT="${COLAB_DESIGN_LINT_PRIMITIVES_EXEMPT:-$REPO_ROOT/gates/fixtures/frontend-design-lint/primitives-exempt.txt}"
NODE_BIN="${COLAB_NODE_BIN:-node}"
READINESS_EXIT=78

red() { echo "::error::frontend-design-lint red — $*"; exit 1; }
ready_red() {
  printf '::gate-readiness-failure::gate=%s|waited_for=%s|limit=%s|elapsed=%s|detail=%s\n' \
    frontend-design-lint "$1" "대기 없음" "0초" "$2"
  echo "::error::frontend-design-lint red(준비) — **검사기가 돌지 못했다.** 판정 red 가 아니다.
   기다린 것: $1
   사유: $2
   ⚠ 준비 실패도 **red 다.** 건너뛰기로 green 을 만들지 않는다."
  exit "$READINESS_EXIT"
}

[ -d "$FE" ] || ready_red "$FE" "프런트 자리가 없다. 대상 0건은 통과가 아니다."
command -v "$NODE_BIN" >/dev/null 2>&1 || ready_red "node 실행 파일($NODE_BIN)" "node 가 PATH 에 없다. 판정부는 zero-dependency 지만 node 자체는 있어야 한다."
SCRIPT="${COLAB_DESIGN_LINT_SCRIPT:-$REPO_ROOT/frontend/scripts/design-lint.mjs}"
[ -f "$SCRIPT" ] || ready_red "$SCRIPT" "판정부 스크립트가 없다."
DOCS="${COLAB_DESIGN_DOCS_SCRIPT:-$REPO_ROOT/frontend/scripts/design-docs.mjs}"
[ -f "$DOCS" ] || ready_red "$DOCS" "문서 표 판정부가 없다 — h 를 판정할 수 없다."
[ -f "$SAME_IN_DARK" ] || ready_red "$SAME_IN_DARK" "다크 동일 면제 목록이 없다 — 선언이 없으면 c 를 판정할 수 없다."
[ -f "$PRIMITIVES" ] || ready_red "$PRIMITIVES" "프리미티브 목록 부재 — 목록이 없으면 e 를 판정할 수 없다."
[ -f "$PRIMITIVES_EXEMPT" ] || ready_red "$PRIMITIVES_EXEMPT" "프리미티브 면제 목록 부재 — 선언이 없으면 e 의 면제를 셀 수 없다."

# 대상 = Git 이 아는 CSS(추적 + 추적 전 · .gitignore 제외). 아직 add 하지 않은 새 화면 CSS 도 본다.
mapfile -t FILES < <(cd "$FE" && git ls-files --cached --others --exclude-standard -- ':(glob)src/**/*.css' | sort -u)
[ "${#FILES[@]}" -gt 0 ] || ready_red "$FE/src/**/*.css" "대상 CSS 가 0건이다 — 아무것도 검사하지 않은 것을 통과로 세지 않는다."

OUT="$(cd "$FE" && "$NODE_BIN" "$SCRIPT" --root . --same-in-dark "$SAME_IN_DARK" --primitives "$PRIMITIVES" --primitives-exempt "$PRIMITIVES_EXEMPT" -- "${FILES[@]}" 2>&1)"; rc=$?
printf '%s\n' "$OUT"
# h — 문서 표(P5). a~g 와 따로 돌려 둘 다 출력한 뒤 합친다(한쪽 red 가 다른 쪽 판정을 가리지 않게).
DOUT="$("$NODE_BIN" "$DOCS" --check 2>&1)"; drc=$?
printf '%s\n' "$DOUT"
H="$(printf '%s\n' "$DOUT" | sed -n 's/^문서 표 갈림 \([0-9][0-9]*\)$/\1/p' | tail -1)"
SUMMARY="$(printf '%s\n' "$OUT" | grep '^파일 ' | tail -1) · 문서 표 갈림 ${H:-?}"
case "$rc" in
  0|1) ;;
  78) ready_red "판정부 입력" "$(printf '%s\n' "$OUT" | grep '^design-lint readiness' | tail -1)" ;;
  *) red "판정부가 비정상 종료했다(rc=$rc)." ;;
esac
case "$drc" in
  0|1) [ -n "$H" ] || red "문서 표 판정부가 요약(문서 표 갈림 n)을 내지 않았다(rc=$drc)." ;;
  78) ready_red "문서 표(h) 입력" "$(printf '%s\n' "$DOUT" | grep '^design-docs readiness' | tail -1)" ;;
  *) red "문서 표 판정부가 비정상 종료했다(rc=$drc)." ;;
esac
if [ "$rc" -eq 0 ] && [ "$drc" -eq 0 ]; then
  echo "frontend-design-lint green — $SUMMARY"
else
  red "위 목록을 고친다. $SUMMARY"
fi
