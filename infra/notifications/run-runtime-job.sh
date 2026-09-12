#!/usr/bin/env bash
set -uo pipefail

CONFIG=""; JOB=""
usage() { echo '사용: run-runtime-job.sh --config <root 전용 0600 env> <job>' >&2; exit 2; }
while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) CONFIG="${2:-}"; shift 2 ;;
    check|export|daily|spool|retry|receive|stage-relay|probe-service-health|probe-backup-freshness|probe-deploy-verification)
      [ -z "$JOB" ] || usage; JOB="$1"; shift ;;
    *) usage ;;
  esac
done
[ -n "$CONFIG" ] && [ -n "$JOB" ] || usage
case "$CONFIG" in /*) ;; *) echo 'runtime 준비 실패 — config는 절대경로여야 한다' >&2; exit 78 ;; esac
[ -f "$CONFIG" ] && [ ! -L "$CONFIG" ] || { echo 'runtime 준비 실패 — config 파일 부재' >&2; exit 78; }
[ "$(stat -c %a "$CONFIG" 2>/dev/null)" = 600 ] || { echo 'runtime 준비 실패 — config는 0600이어야 한다' >&2; exit 78; }
[ "$(stat -c %u "$CONFIG" 2>/dev/null)" = "$(id -u)" ] || { echo 'runtime 준비 실패 — 실행 계정 소유 config가 아니다' >&2; exit 78; }

set -a
# shellcheck source=/dev/null
. "$CONFIG"
set +a

valid_absolute() { [[ "${1:-}" = /* && "$1" != *$'\n'* && "$1" != *$'\r'* ]]; }
case "${COLAB_NOTIFICATION_ENVIRONMENT:-}" in dev|staging) ;; *) echo 'runtime 준비 실패 — environment' >&2; exit 78 ;; esac
for required in COLAB_NOTIFICATION_ROOT COLAB_NOTIFICATION_PYTHON COLAB_OPERATOR_MANIFEST COLAB_OPERATOR_SPOOL; do
  valid_absolute "${!required:-}" || { echo "runtime 준비 실패 — $required" >&2; exit 78; }
done
[ -x "$COLAB_NOTIFICATION_PYTHON" ] && [ -r "$COLAB_OPERATOR_MANIFEST" ] || { echo 'runtime 준비 실패 — 실행 입력 부재' >&2; exit 78; }
mkdir -p "$COLAB_OPERATOR_SPOOL" "${COLAB_OPERATOR_STATE:-/var/lib/colab/operator}" || exit 78
chmod 0700 "$COLAB_OPERATOR_SPOOL" "${COLAB_OPERATOR_STATE:-/var/lib/colab/operator}" 2>/dev/null || exit 78
cd "$COLAB_NOTIFICATION_ROOT" || exit 78
[ "$JOB" != check ] || exit 0

PY=("$COLAB_NOTIFICATION_PYTHON")
CLI=("${PY[@]}" -m infra.notifications.cli)
MANIFEST=(--manifest "$COLAB_OPERATOR_MANIFEST")
STATE="${COLAB_OPERATOR_STATE:-/var/lib/colab/operator}"

case "$JOB" in
  export)
    [ "$COLAB_NOTIFICATION_ENVIRONMENT" = dev ] || exit 78
    exec "${PY[@]}" services/core-api/ops/operator_audit_export.py sync --manifest "$COLAB_OPERATOR_MANIFEST" ;;
  daily)
    [ "$COLAB_NOTIFICATION_ENVIRONMENT" = dev ] || exit 78
    exec "${CLI[@]}" daily "${MANIFEST[@]}" --profile connected ;;
  spool)
    [ "$COLAB_NOTIFICATION_ENVIRONMENT" = dev ] || exit 78
    exec "${CLI[@]}" drain-spool --profile connected --spool "$COLAB_OPERATOR_SPOOL" ;;
  retry)
    [ "$COLAB_NOTIFICATION_ENVIRONMENT" = dev ] || exit 78
    exec "${CLI[@]}" publish-pending "${MANIFEST[@]}" --profile connected ;;
  receive)
    [ "$COLAB_NOTIFICATION_ENVIRONMENT" = dev ] || exit 78
    exec "${PY[@]}" -m infra.notifications.relay receive ;;
  stage-relay)
    [ "$COLAB_NOTIFICATION_ENVIRONMENT" = staging ] || exit 78 ;;
  probe-*) ;;
esac

if [ "$COLAB_NOTIFICATION_ENVIRONMENT" = dev ]; then
  TARGET="${JOB#probe-}"
  exec "${CLI[@]}" probe "${MANIFEST[@]}" --profile connected --target "$TARGET" \
    --state "$STATE/$TARGET.json" --spool "$COLAB_OPERATOR_SPOOL"
fi

for required in COLAB_STAGE_SSH_TARGET COLAB_STAGE_SSH_KEY COLAB_STAGE_REMOTE_WRAPPER COLAB_STAGE_REMOTE_CONFIG; do
  [ -n "${!required:-}" ] || { echo "runtime 준비 실패 — $required" >&2; exit 78; }
done
valid_absolute "$COLAB_STAGE_SSH_KEY" && valid_absolute "$COLAB_STAGE_REMOTE_WRAPPER" && valid_absolute "$COLAB_STAGE_REMOTE_CONFIG" \
  || { echo 'runtime 준비 실패 — Stage relay 경로' >&2; exit 78; }
RECEIVER=("$COLAB_STAGE_REMOTE_WRAPPER" --config "$COLAB_STAGE_REMOTE_CONFIG" receive)
RELAY=("${PY[@]}" -m infra.notifications.relay)
relay_spool() {
  exec 8>"$STATE/stage-relay.lock" || return 78
  flock -w 30 8 || return 75
  "${RELAY[@]}" send --spool "$COLAB_OPERATOR_SPOOL" --ssh-target "$COLAB_STAGE_SSH_TARGET" \
    --ssh-key "$COLAB_STAGE_SSH_KEY" --receiver-command "${RECEIVER[@]}"
}
[ "$JOB" != stage-relay ] || { relay_spool; exit $?; }

TARGET="${JOB#probe-}"
"${CLI[@]}" probe "${MANIFEST[@]}" --profile relay --target "$TARGET" \
  --state "$STATE/$TARGET.json" --spool "$COLAB_OPERATOR_SPOOL"
PROBE_RC=$?
HEARTBEAT_RC=0
if [ "$PROBE_RC" -eq 0 ] || [ "$PROBE_RC" -eq 1 ]; then
  OBSERVED_AT="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"
  "${RELAY[@]}" heartbeat --environment staging --target "$TARGET" --observed-at "$OBSERVED_AT" \
    --ssh-target "$COLAB_STAGE_SSH_TARGET" --ssh-key "$COLAB_STAGE_SSH_KEY" \
    --receiver-command "${RECEIVER[@]}"
  HEARTBEAT_RC=$?
fi
relay_spool
RELAY_RC=$?
[ "$PROBE_RC" -eq 0 ] || exit "$PROBE_RC"
[ "$HEARTBEAT_RC" -eq 0 ] || exit "$HEARTBEAT_RC"
exit "$RELAY_RC"
