#!/usr/bin/env bash
# root 소유 고정 진입점: CURRENT_SHA가 고른 검증된 bundle만 실행한다.
set -uo pipefail
TRUST="${COLAB_OPS_TRUST_ROOT:-/opt/colab-ops}"
STATE="${COLAB_DEV_STATE:-/opt/colab-v2}"
CURRENT="$(tr -d '\r\n' < "$STATE/CURRENT_SHA" 2>/dev/null)"
[[ "$CURRENT" =~ ^[0-9a-f]{12,40}$ ]] || { echo "::gate-readiness-failure::gate=ops-dispatch|missing=valid-CURRENT_SHA" >&2; exit 78; }
SOURCE="$TRUST/versions/$CURRENT"; MANIFEST="$SOURCE/OPS_SOURCE_MANIFEST"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$HERE/verify-source.sh" --source "$SOURCE" --manifest "$MANIFEST" --current-sha "$CURRENT" || exit $?
if [ "${1:-}" = --check ]; then exit 0; fi
exec "$SOURCE/infra/ops/run-scheduled.sh" "$@"
