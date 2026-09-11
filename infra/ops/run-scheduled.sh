#!/usr/bin/env bash
# cron 한 회차: 고정 probe를 상태형 runner에 연결한다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVNAME=""; TARGET=""; WEBHOOK=""
while [ $# -gt 0 ]; do
  case "$1" in
    --env) ENVNAME="${2:-}"; shift 2 ;;
    --target) TARGET="${2:-}"; shift 2 ;;
    --webhook-file) WEBHOOK="${2:-}"; shift 2 ;;
    *) echo "ops schedule red — 알 수 없는 인자" >&2; exit 2 ;;
  esac
done
[ "$ENVNAME" = dev ] && [ -n "$WEBHOOK" ] || { echo "ops schedule red — --env dev와 webhook 파일 경로가 필요하다" >&2; exit 2; }
case "$TARGET" in
  deploy-verification|service-health|backup-freshness) ;;
  *) echo "ops schedule red — target allowlist 위반" >&2; exit 2 ;;
esac

STATE_DIR="${COLAB_OPS_STATE_DIR:-/opt/colab-v2/ops-alerts}"
mkdir -p "$STATE_DIR/locks" || exit 78
chmod 0700 "$STATE_DIR" "$STATE_DIR/locks" 2>/dev/null || exit 78
LOCK="$STATE_DIR/locks/$TARGET.lock"
exec 9>"$LOCK" || exit 78
if ! flock -n 9; then
  printf '{"schema":"colab.ops.v1","event":"probe.already-running","service":"ops-alarm","target":"%s"}\n' "$TARGET"
  exit 75
fi

case "$TARGET" in
  deploy-verification) PROBE=("$HERE/probes/deploy-verification.sh") ;;
  service-health) PROBE=("$HERE/probes/service-health.sh") ;;
  backup-freshness) PROBE=("$HERE/probes/backup-freshness.sh") ;;
esac
CONTAINER_NAME=""
case "$TARGET" in
  deploy-verification|backup-freshness) CONTAINER_NAME="colab-ops-$TARGET-$$"; export COLAB_OPS_CONTAINER_NAME="$CONTAINER_NAME" ;;
esac
LOG="$STATE_DIR/$TARGET.log"
STATE="$STATE_DIR/$TARGET.state.json"
"$HERE/alarm_runner.py" --state "$STATE" --target "$TARGET" --threshold 2 \
  --webhook-file "$WEBHOOK" --timeout 120 -- "${PROBE[@]}" >> "$LOG" 2>&1
RC=$?
[ -z "$CONTAINER_NAME" ] || docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
chmod 0600 "$LOG" "$STATE" 2>/dev/null || true
exit "$RC"
