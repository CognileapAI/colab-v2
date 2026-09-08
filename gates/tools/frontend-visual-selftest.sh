#!/usr/bin/env bash
# frontend-visual 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 픽스처 원본 = `gates/fixtures/frontend-visual/{green,red}.html`.
# ⚠ **사본을 뜬다.** 이 레포의 경로에는 공백이 들어 있고(`00 CoLAB`), `COLAB_VISUAL_URLS` 는
#   공백으로 나눈 목록이라 원본 자리를 그대로 `file://` 로 가리키면 URL 이 갈라진다.
#   그래서 `mktemp -d`(공백 없는 자리)로 복사해 거기를 가리킨다 — 원본은 읽기만 한다.
#   `agent-browser 0.27.0` 이 `file://` 을 여는 것은 이 세션에서 실측했다(오프라인 동작).
#
# 케이스 — green 하나 · red(판정) 하나 · red(준비) 하나 · green(명시 면제) 하나.
#   ⓐ green.html   13px 이상 · 대비 ≥4.5 · `:active` 규칙 · reduced-motion 블록 → green
#   ⓑ red.html     11px 글자 ＋ 4.2:1 짝                                        → red(판정)
#   ⓒ 미선언        COLAB_VISUAL_URLS·COLAB_VISUAL_EXEMPT 둘 다 없음            → red(준비 · 78 · 입력미선언)
#   ⓓ 명시 면제     COLAB_VISUAL_EXEMPT=1 — 건수를 보이며 건너뛴다              → green
#
# ⓑ 가 통과해 버리면 이 게이트는 아무것도 막지 않는다 — 그 케이스가 이 셀프테스트의 존재 이유다.
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/frontend-visual.sh"
FIX="$REPO_ROOT/gates/fixtures/frontend-visual"
FAILED=0

red() { echo "::error::frontend-visual-selftest red — $*"; FAILED=1; }

# 판정 갈래(green·red·ready·미선언)의 정본 = `_expect.sh` 하나 — 78 을 「기대한 red」로 접지 않는다.
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

[ -x "$GATE" ] || { echo "::error::frontend-visual-selftest red — 판정 재료가 없다: $GATE"; exit 1; }
for f in green.html red.html; do
  [ -f "$FIX/$f" ] || { echo "::error::frontend-visual-selftest red — 픽스처가 없다: $FIX/$f"; exit 1; }
done

WORK="$(mktemp -d -t frontend-visual-selftest-XXXXXX)"
REPORTS="$(mktemp -d -t frontend-visual-reports-XXXXXX)"
cleanup() { rm -rf "$WORK" "$REPORTS"; }
trap cleanup EXIT
cp "$FIX/green.html" "$FIX/red.html" "$WORK/"

expect() { # $1=기대(green|red|미선언) $2=이름 $3=케이스 키
  local want="$1" label="$2" key="$3" out rc
  case "$key" in
    green|red)
      out="$(COLAB_GATE_REPORT_DIR="$REPORTS/$key" COLAB_VISUAL_URLS="file://$WORK/$key.html" \
             COLAB_VISUAL_EXEMPT= "$GATE" 2>&1)"; rc=$? ;;
    undeclared)
      out="$(COLAB_GATE_REPORT_DIR="$REPORTS/$key" COLAB_VISUAL_URLS= COLAB_VISUAL_EXEMPT= "$GATE" 2>&1)"; rc=$? ;;
    exempt)
      out="$(COLAB_GATE_REPORT_DIR="$REPORTS/$key" COLAB_VISUAL_URLS= COLAB_VISUAL_EXEMPT=1 "$GATE" 2>&1)"; rc=$? ;;
    *) red "$label — 알 수 없는 케이스 키: $key"; return ;;
  esac
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
  # 면제 케이스는 **건수를 출력에 보여야** 한다 — 조용히 넘어가면 green-by-skip 이다.
  if [ "$key" = exempt ] && ! printf '%s' "$out" | grep -q '페이지 0건'; then
    red "$label — 면제인데 건수를 출력하지 않았다(조용한 건너뛰기):
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  # red 케이스는 무엇이 걸렸는지 **이름으로** 내야 한다.
  if [ "$key" = red ] && ! printf '%s' "$out" | grep -q 'p\.tiny'; then
    red "$label — red 인데 위반 요소를 셀렉터로 내지 않았다:
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  echo "  ✓ $label ($want)"
}

# ⓐ 대조군 — 이것이 green 이 아니면 아래 red 는 아무 말도 하지 않는다.
expect green  "ⓐ 13px 이상 · 대비 ≥4.5 · :active · reduced-motion" green
# ⓑ 이 게이트의 존재 이유 — jsdom 이 못 보는 자리(computed px · 상속 배경 대비)를 실화면이 잡는다.
expect red    "ⓑ 11px 글자 ＋ 대비 4.2:1" red
# ⓒ 입력 미선언 — 기본값으로 green 을 만들지 않는다.
expect 미선언 "ⓒ COLAB_VISUAL_URLS 미선언" undeclared
# ⓓ 명시 면제 — 건너뛰되 건수를 보인다.
expect green  "ⓓ COLAB_VISUAL_EXEMPT=1 명시 면제" exempt

if [ "$FAILED" -ne 0 ]; then
  echo "::error::frontend-visual-selftest red — 위 케이스가 기대와 다르다."
  exit 1
fi
# 판정 결함이 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다** (`_expect.sh`).
expect_readiness_verdict frontend-visual-selftest
echo "frontend-visual-selftest green — 검사 4건 전건 기대대로 (green 2 · red(판정) 1 · red(준비·입력미선언) 1)."
