#!/usr/bin/env bash
# frontend-design-lint 가 red fixture 로 **fail-closed** 임을 증명한다.
#
# 픽스처 원본 = `gates/fixtures/frontend-design-lint/` 트리 여섯. 판정부는 읽기만 하므로 사본 없이
# 각 트리를 그대로 `COLAB_FRONTEND_DIR` 로 가리키고, 면제 목록은 트리 안의 `same-in-dark.txt` 를 준다.
# 판정부는 픽스처 트리에 사본을 두지 않는다 — 게이트가 저장소의 `frontend/scripts/design-lint.mjs`
# 하나를 부르므로 게이트가 보는 판정부와 selftest 가 보는 판정부가 갈리지 않는다.
#
# 케이스 — green 2 · red 7 · red(준비) 3 = 12.
#   ⓐ green/       정본 라이트·다크 짝 · 화면 루트 범위 토큰 · 면제 1건(사유 있음) → green
#   ⓑ red-a/       화면 CSS `:root` 정의 + 화면 범위의 정본 계열 이름            → red
#   ⓒ red-b/       어디에도 없는 var() 참조(폴백 있음)                          → red
#   ⓓ red-c/       라이트에만 있는 색 이름 · 다크에만 있는 이름                  → red
#   ⓔ red-d/       화면 CSS 와 셸 CSS(`src/shell/shell.css`)의 `@import`(P2a · 정본 밖 전 CSS) → red
#   ⓘ green-layer/ 정본·화면 CSS 가 `@layer` 블록 안에 있어도 같은 판정(P2a)            → green
#   ⓙ red-root-html/ 층 블록 안의 `html:root` 정의(P2a · 사각 1)                         → red
#   ⓚ red-accent/  화면 범위의 `--accent-` 정의(P2a · 사각 2)                            → red
#   ⓛ 판정부에 디스크에 없는 대상 파일(P2a · 사각 3 · 추적 중 삭제)                      → red(준비 · 78)
#   ⓕ red-exempt/  면제 목록의 사유 없음 · 낡은 항목 · 다크에 이미 있는 항목     → red
#   ⓖ empty/       대상 CSS 0건(빈 트리)                                                   → red(준비 · 78)
#   ⓗ node 부재(COLAB_NODE_BIN 을 없는 경로로)                                  → red(준비 · 78)
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/frontend-design-lint.sh"
FIX="$REPO_ROOT/gates/fixtures/frontend-design-lint"
FAILED=0

red() { echo "::error::frontend-design-lint-selftest red — $*"; FAILED=1; }

# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

[ -x "$GATE" ] || { echo "::error::frontend-design-lint-selftest red — 판정 재료가 없다: $GATE"; exit 1; }
[ -d "$FIX" ]  || { echo "::error::frontend-design-lint-selftest red — 픽스처 자리가 없다: $FIX"; exit 1; }

expect() { # $1=기대(green|red|ready) $2=이름 $3=픽스처 디렉터리 [$4..=추가 환경]
  local want="$1" label="$2" dir="$3" out rc
  shift 3
  out="$(env COLAB_FRONTEND_DIR="$dir" COLAB_DESIGN_LINT_SAME_IN_DARK="$dir/same-in-dark.txt" "$@" "$GATE" 2>&1)"; rc=$?
  if expect_intercept_readiness "$rc" "$out" "$label" "$want"; then
    return
  fi
  if [ "$want" = green ] && [ "$rc" -ne 0 ]; then
    red "$label — green 이어야 하는데 red 다(rc=$rc):
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  if [ "$want" = red ] && [ "$rc" -eq 0 ]; then
    red "$label — red 여야 하는데 통과했다:
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  echo "  ✓ $label ($want)"
}

expect_line() { # $1=이름 $2=픽스처 $3=출력에 있어야 할 문자열 — red 가 **그 규칙 때문**인지 확인한다.
  local label="$1" dir="$2" needle="$3" out
  out="$(env COLAB_FRONTEND_DIR="$dir" COLAB_DESIGN_LINT_SAME_IN_DARK="$dir/same-in-dark.txt" "$GATE" 2>&1)"
  if ! printf '%s\n' "$out" | grep -qF -- "$needle"; then
    red "$label — 출력에 「$needle」이 없다(다른 이유로 red 일 수 있다):
$(printf '%s\n' "$out" | sed 's/^/     /')"
  fi
}

# ⓐ 대조군 — 이것이 green 이 아니면 아래 red 들은 아무 말도 하지 않는다.
expect green "ⓐ 정본 짝·루트 범위·면제 1건" "$FIX/green"
expect_line "ⓐ 면제 건수 노출" "$FIX/green" "다크 누락 0(면제 1)"
# ⓑ a — 화면 :root 정의와 범위 안 정본 계열 이름.
expect red "ⓑ a 화면 :root 정의 · 범위의 정본 계열 이름" "$FIX/red-a"
expect_line "ⓑ a 는 두 갈래를 다 센다" "$FIX/red-a" "a_root=1 a_scoped=1"
# ⓒ b — 미정의 참조(폴백이 있어도).
expect red "ⓒ b 미정의 var() 참조" "$FIX/red-b"
expect_line "ⓒ b 계수" "$FIX/red-b" " b=1 "
# ⓓ c — 다크 누락 · 다크에만 있는 이름.
expect red "ⓓ c 다크 누락 · 다크 전용" "$FIX/red-c"
expect_line "ⓓ c 두 갈래" "$FIX/red-c" "c_missing=1 c_dark_only=1"
# ⓔ d — 정본 밖 CSS 의 @import(화면 + 셸).
expect red "ⓔ d 화면·셸 CSS @import" "$FIX/red-d"
expect_line "ⓔ d 계수" "$FIX/red-d" " d=2 "
expect_line "ⓔ d 셸 CSS 도 센다" "$FIX/red-d" "src/shell/shell.css:1 @import"
# ⓘ 층 블록은 투명하다 — 정본 :root·다크 짝과 화면 범위 토큰을 층 밖과 똑같이 읽는다.
expect green "ⓘ @layer 블록 안의 정본·화면 CSS" "$FIX/green-layer"
expect_line "ⓘ 층 안 정본도 다크 짝을 읽는다" "$FIX/green-layer" "a=0 a_root=0 a_scoped=0 b=0 c=0"
# ⓙ html:root — `:root` 앞에 요소 이름이 붙어도 :root 다.
expect red "ⓙ 층 블록 안 html:root 정의" "$FIX/red-root-html"
expect_line "ⓙ a·d 계수" "$FIX/red-root-html" "a_root=1 a_scoped=0"
expect_line "ⓙ d 계수" "$FIX/red-root-html" " d=1 "
# ⓚ --accent- 는 정본 계열 이름이다.
expect red "ⓚ 화면 범위 --accent- 정의" "$FIX/red-accent"
expect_line "ⓚ a_scoped 계수" "$FIX/red-accent" "a_root=0 a_scoped=1"
# ⓕ 면제 목록 구멍 셋.
expect red "ⓕ 면제 사유 없음 · 낡은 항목 · 다크에 이미 있음" "$FIX/red-exempt"
expect_line "ⓕ 구멍 셋 전부" "$FIX/red-exempt" "c_holes=3"
# ⓖ 대상 CSS 0건 — 못 돌았음을 통과로 세지 않는다.
expect ready "ⓖ 대상 CSS 0건" "$FIX/empty"
# ⓗ node 부재.
expect ready "ⓗ node 부재" "$FIX/green" COLAB_NODE_BIN=/nonexistent/node
# ⓛ 대상 목록의 파일이 디스크에 없다(추적 중 삭제) — 조용히 건너뛰지 않는다. 게이트는 Git 목록을 주므로
#    판정부를 직접 불러 없는 경로를 섞는다.
MISSING_OUT="$(cd "$FIX/green" && node "${COLAB_DESIGN_LINT_SCRIPT:-$REPO_ROOT/frontend/scripts/design-lint.mjs}" --root . --same-in-dark same-in-dark.txt -- src/shell/tokens.css src/components/x/x.css src/shell/gone.css 2>&1)"; MISSING_RC=$?
if [ "$MISSING_RC" -eq 78 ] && printf '%s\n' "$MISSING_OUT" | grep -qF "src/shell/gone.css"; then
  echo "  ✓ ⓛ 디스크에 없는 대상 파일 (ready)"
else
  red "ⓛ 디스크에 없는 대상 파일 — 78 이어야 하는데 rc=$MISSING_RC:
$(printf '%s\n' "$MISSING_OUT" | sed 's/^/     /')"
fi

if [ "$FAILED" -ne 0 ]; then
  echo "::error::frontend-design-lint-selftest red — 위 케이스가 기대와 다르다."
  exit 1
fi
expect_readiness_verdict frontend-design-lint-selftest
echo "frontend-design-lint-selftest green — 검사 12건 전건 기대대로 (green 2 · red 7 · red(준비) 3)."
