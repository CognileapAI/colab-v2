#!/usr/bin/env bash
# CURRENT_SHA와 manifest, 실제 runtime source 바이트를 함께 대조한다.
set -uo pipefail
SOURCE=""; MANIFEST=""; CURRENT=""
while [ $# -gt 0 ]; do case "$1" in
  --source) SOURCE="${2:-}"; shift 2;; --manifest) MANIFEST="${2:-}"; shift 2;; --current-sha) CURRENT="${2:-}"; shift 2;; *) exit 2;; esac; done
[ -d "$SOURCE" ] && [ -f "$MANIFEST" ] && [[ "$CURRENT" =~ ^[0-9a-f]{12,40}$ ]] || { echo "::gate-readiness-failure::gate=ops-source|missing=source-or-manifest" >&2; exit 78; }
EXPECTED_UID="$(id -u)"
for path in "$SOURCE" "$(dirname "$SOURCE")" "$(dirname "$(dirname "$SOURCE")")" \
            "$(dirname "$(dirname "$(dirname "$SOURCE")")")" "$MANIFEST"; do
  [ ! -L "$path" ] && [ "$(stat -c %u "$path" 2>/dev/null)" = "$EXPECTED_UID" ] || {
    echo "::gate-readiness-failure::gate=ops-source|invalid=owner-or-symlink" >&2; exit 78; }
  MODE="$(stat -c %a "$path" 2>/dev/null)"
  (( (8#$MODE & 8#022) == 0 )) || { echo "::gate-readiness-failure::gate=ops-source|invalid=writable-parent" >&2; exit 78; }
done
[ "$(realpath -e "$SOURCE")" = "$SOURCE" ] && [ "$(realpath -e "$MANIFEST")" = "$MANIFEST" ] || {
  echo "::gate-readiness-failure::gate=ops-source|invalid=resolved-path" >&2; exit 78; }
[ -z "$(find "$SOURCE" -type l -print -quit)" ] || { echo "ops source red — symlink 파일은 허용하지 않는다" >&2; exit 1; }
WANT="$(sed -n 's/^# source_sha=//p' "$MANIFEST")"
[ "$WANT" = "$CURRENT" ] || { echo "ops source red — manifest SHA와 CURRENT_SHA 불일치" >&2; exit 1; }
(cd "$SOURCE" && sha256sum -c "$MANIFEST" --quiet) || { echo "ops source red — runtime file 누락/변경" >&2; exit 1; }
echo "ops source green — CURRENT_SHA $CURRENT · manifest 전건 일치"
