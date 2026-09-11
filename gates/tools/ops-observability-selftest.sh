#!/usr/bin/env bash
# I4 관측 게이트와 알람 상태기가 red fixture를 실제로 거부하는지 증명한다.
set -uo pipefail

ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
CHECK="$ROOT/gates/tools/ops_observability.py"
ALARM="$ROOT/infra/ops/alarm_runner.py"
BASE_RES="$ROOT/infra/ops/data-residency.toml"
BASE_ALARMS="$ROOT/infra/ops/alarms.toml"
COMPOSE="$ROOT/infra/dev/compose.yml"
FAILED=0

red() { echo "::error::ops-observability-selftest red — $*"; FAILED=1; }
[ -x "$CHECK" ] || { red "검사기가 없다: $CHECK"; exit 1; }
[ -x "$ALARM" ] || { red "알람 상태기가 없다: $ALARM"; exit 1; }

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" ops-observe-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT INT TERM

expect() { # want label command...
  local want="$1" label="$2" out rc; shift 2
  out="$("$@" 2>&1)"; rc=$?
  if [ "$want" = green ] && [ "$rc" -ne 0 ]; then
    red "$label — green 기대, exit $rc: $out"
  elif [ "$want" = red ] && [ "$rc" -eq 0 ]; then
    red "$label — red 기대인데 통과: $out"
  else
    echo "  ✓ $label ($want)"
  fi
  LAST_OUT="$out"; LAST_RC="$rc"
}

expect green "ⓐ 정본 대조군" "$CHECK" --residency "$BASE_RES" --alarms "$BASE_ALARMS" --compose "$COMPOSE" --repo "$ROOT"

cp "$BASE_RES" "$TMP/region.toml"
sed -i '0,/ap-northeast-2/s//us-east-1/' "$TMP/region.toml"
expect red "ⓑ home region drift" "$CHECK" --residency "$TMP/region.toml" --alarms "$BASE_ALARMS" --compose "$COMPOSE" --repo "$ROOT"

cp "$BASE_RES" "$TMP/ai.toml"
sed -i 's/korea_guaranteed = false/korea_guaranteed = true/' "$TMP/ai.toml"
expect red "ⓒ 외부 AI 국내 고정 거짓 선언" "$CHECK" --residency "$TMP/ai.toml" --alarms "$BASE_ALARMS" --compose "$COMPOSE" --repo "$ROOT"

cp "$BASE_ALARMS" "$TMP/slow.toml"
sed -i 's/interval_seconds = 300/interval_seconds = 600/' "$TMP/slow.toml"
expect red "ⓓ 5분 주기 drift" "$CHECK" --residency "$BASE_RES" --alarms "$TMP/slow.toml" --compose "$COMPOSE" --repo "$ROOT"

STATE="$TMP/state.json"
expect red "ⓔ 첫 실패는 아직 raise 전" "$ALARM" --state "$STATE" --target health --threshold 2 --observe-only -- /bin/false
[[ "$LAST_OUT" != *'alarm.raised'* ]] || red "첫 실패가 곧바로 raise 됐다"
expect red "ⓕ 둘째 실패가 raise" "$ALARM" --state "$STATE" --target health --threshold 2 --observe-only -- /bin/false
[[ "$LAST_OUT" == *'alarm.raised'* ]] || red "임계 실패에 alarm.raised가 없다"
expect red "ⓖ 반복 실패는 재통지 안 함" "$ALARM" --state "$STATE" --target health --threshold 2 --observe-only -- /bin/false
[[ "$LAST_OUT" != *'alarm.raised'* ]] || red "활성 alarm을 반복 통지했다"
expect green "ⓗ 회복은 clear 1회" "$ALARM" --state "$STATE" --target health --threshold 2 --observe-only -- /bin/true
[[ "$LAST_OUT" == *'alarm.cleared'* ]] || red "회복에 alarm.cleared가 없다"

printf '{broken' > "$STATE"
expect red "ⓘ 손상 state fail-closed" "$ALARM" --state "$STATE" --target health --threshold 2 --observe-only -- /bin/true

MISSING="$TMP/missing-webhook"
expect red "ⓙ webhook 미선언 readiness" "$ALARM" --state "$TMP/fresh.json" --target health --threshold 2 --webhook-file "$MISSING" -- /bin/true
[ "$LAST_RC" -eq 78 ] || red "webhook 미선언은 exit 78이어야 한다: $LAST_RC"

[ "$FAILED" -eq 0 ] || exit 1
echo "ops-observability-selftest green — 검사 10건 전건 기대대로"
