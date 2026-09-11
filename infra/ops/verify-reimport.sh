#!/usr/bin/env bash
# 같은 SHA 재반입: untrusted incoming은 동일성 비교에만 쓰고 resident 정본만 검증한다.
set -uo pipefail
SOURCE=""; INCOMING=""; CURRENT=""
while [ $# -gt 0 ]; do case "$1" in
  --source) SOURCE="${2:-}"; shift 2;; --incoming-manifest) INCOMING="${2:-}"; shift 2;;
  --current-sha) CURRENT="${2:-}"; shift 2;; *) exit 2;; esac; done
RESIDENT="$SOURCE/OPS_SOURCE_MANIFEST"
TRUST="$(dirname "$(dirname "$SOURCE")")"; VERIFIER="$TRUST/bin/verify-source.sh"
[ -f "$INCOMING" ] && [ -f "$RESIDENT" ] || { echo "::gate-readiness-failure::gate=ops-reimport|missing=manifest" >&2; exit 78; }
cmp -s "$INCOMING" "$RESIDENT" || { echo "ops reimport red — 같은 SHA의 manifest가 다르다; 기존 version은 바꾸지 않는다" >&2; exit 1; }
exec "$VERIFIER" --source "$SOURCE" --manifest "$RESIDENT" --current-sha "$CURRENT"
