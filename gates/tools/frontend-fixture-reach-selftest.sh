#!/usr/bin/env bash
# frontend-fixture-reach 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 픽스처 원본 = `gates/fixtures/frontend-fixture-reach/`(트리 여섯 ＋ README). 워커는 상대 import 만
# 따라가고 파일 시스템 밖에 아무것도 쓰지 않으므로, `mktemp -d` 로 복사하지 않고 각 트리를 그대로
# `COLAB_FRONTEND_DIR` 로 가리켜 돈다 — 읽기만 하니 사본을 뜰 이유가 없다.
#
# 케이스 — red 넷 · red(준비) 둘 · green 하나.
#   ⓐ clean/           깨끗한 진입점(도달 2 · 진입점 제외 1)         → green
#   ⓑ reachable/        진입점이 fixture.ts(금지 모듈)에 실제로 닿는다 → red
#   ⓒ empty-entry/      진입점이 아무것도 당기지 않는다(0 모듈 도달)   → red
#   ⓓ alias-declared/   tsconfig 가 paths·baseUrl 을 선언 — 워커가 별칭 뒤를 못 본다 → red
#   ⓔ no-script/        판정부 스크립트 자체가 없다                   → red(준비 · 78)
#   ⓕ no-entry/         운영 진입점(src/main.tsx)이 없다              → red(준비 · 78)
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/frontend-fixture-reach.sh"
FIX="$REPO_ROOT/gates/fixtures/frontend-fixture-reach"
FAILED=0

red() { echo "::error::frontend-fixture-reach-selftest red — $*"; FAILED=1; }

# 판정 갈래(green·red·ready·미선언)의 정본 = `_expect.sh` 하나 — 종료코드 78(준비 실패)을
# 「기대한 red」로 접지 않는다(2026-09-03 코드리뷰 #6 · `CLAUDE.md §4` green-by-skip).
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

[ -x "$GATE" ] || { echo "::error::frontend-fixture-reach-selftest red — 판정 재료가 없다: $GATE"; exit 1; }
[ -d "$FIX" ]  || { echo "::error::frontend-fixture-reach-selftest red — 픽스처 자리가 없다: $FIX"; exit 1; }

expect() { # $1=기대(green|red|ready) $2=이름 $3=픽스처 디렉터리
  local want="$1" label="$2" dir="$3" out rc
  out="$(COLAB_FRONTEND_DIR="$dir" "$GATE" 2>&1)"; rc=$?
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

# ⓐ 대조군 — 이것이 green 이 아니면 아래 red 들은 아무 말도 하지 않는다.
expect green "ⓐ 깨끗한 진입점" "$FIX/clean"
# ⓑ 진입점이 금지 모듈에 실제로 닿는다 — 이 게이트의 존재 이유.
expect red "ⓑ 진입점이 fixture.ts 에 닿는다" "$FIX/reachable"
# ⓒ 진입점이 아무것도 당기지 않는다 — 그래프가 비면 검사한 것이 아니다.
expect red "ⓒ 진입점 말고 도달 0건" "$FIX/empty-entry"
# ⓓ 경로 별칭 선언 — 워커가 못 보는 영역이 생기면 스스로 red 를 낸다(능력을 크게 말하지 않는다).
expect red "ⓓ tsconfig paths·baseUrl 선언" "$FIX/alias-declared"
# ⓔ 판정부 스크립트 부재 — 못 돌았음을 통과로 세지 않는다.
expect ready "ⓔ 판정부 스크립트 부재" "$FIX/no-script"
# ⓕ 운영 진입점 부재.
expect ready "ⓕ 운영 진입점 부재" "$FIX/no-entry"

if [ "$FAILED" -ne 0 ]; then
  echo "::error::frontend-fixture-reach-selftest red — 위 케이스가 기대와 다르다."
  exit 1
fi
# 판정 결함이 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다** (`_expect.sh`).
expect_readiness_verdict frontend-fixture-reach-selftest
echo "frontend-fixture-reach-selftest green — 검사 6건 전건 기대대로 (red 3 · red(준비) 2 · green 1)."
