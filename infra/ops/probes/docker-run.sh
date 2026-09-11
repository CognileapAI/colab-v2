#!/usr/bin/env bash
# 고유 이름의 probe container를 제한 시간 뒤 반드시 제거한다.
set -uo pipefail
NAME="${1:-}"; LIMIT="${2:-110}"; shift 2 || exit 2
[[ "$NAME" =~ ^colab-ops-(deploy-verification|backup-freshness)-[0-9]+$ ]] || exit 2
[ "${1:-}" = -- ] || exit 2; shift
timeout --signal=TERM --kill-after=5 "$LIMIT" docker run --name "$NAME" "$@"; RC=$?
docker rm -f "$NAME" >/dev/null 2>&1 || true
exit "$RC"
