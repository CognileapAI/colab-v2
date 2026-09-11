#!/usr/bin/env bash
# 지정 commit의 운영 probe 소스만 git archive로 묶고 hash manifest를 만든다.
set -euo pipefail
REPO=""; SHA=""; OUT=""
while [ $# -gt 0 ]; do case "$1" in
  --repo) REPO="${2:-}"; shift 2;; --sha) SHA="${2:-}"; shift 2;; --output) OUT="${2:-}"; shift 2;; *) exit 2;; esac; done
[ -n "$REPO" ] && [ -n "$SHA" ] && [ -n "$OUT" ] || exit 2
FULL="$(git -C "$REPO" rev-parse "$SHA^{commit}")"; [[ "$FULL" == "$SHA"* ]] || exit 1
PATHS=(infra/ops services/core-api/ops db/platform db/ai gates/tools/rls_coverage.py gates/config/rls-allowlist.toml)
for path in "${PATHS[@]}"; do git -C "$REPO" cat-file -e "$FULL:$path" || { echo "bundle red — commit에 $path 부재" >&2; exit 1; }; done
mkdir -p "$OUT"; TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
ARCHIVE="$OUT/colab-ops-source-$SHA.tar.gz"; MANIFEST="$OUT/colab-ops-source-$SHA.manifest"
git -C "$REPO" archive --format=tar "$FULL" "${PATHS[@]}" | gzip -n > "$ARCHIVE"
tar xzf "$ARCHIVE" -C "$TMP"
{
  echo "# colab-ops-source-manifest/1"; echo "# source_sha=$SHA"; echo "# archive_sha256=$(sha256sum "$ARCHIVE" | cut -d' ' -f1)"
  (cd "$TMP" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
} > "$MANIFEST"
chmod 0600 "$MANIFEST"
echo "ops source bundle green — commit $SHA"
