#!/usr/bin/env bash
# 실제 Cloudflare/Terraform 없이 IS4 입력·plan 판정부를 검증한다.
set -uo pipefail
ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
RUNNER="$ROOT/infra/staging/tunnel/rehearse-state-recovery.sh"
JUDGE="$ROOT/infra/staging/tunnel/validate-recovery-plan.py"
FAILED=0
red() { echo "::error::is4-recovery-selftest red — $*"; FAILED=1; }
[ -x "$RUNNER" ] || { red "runner가 없다: $RUNNER"; exit 1; }
[ -x "$JUDGE" ] || { red "plan 판정부가 없다: $JUDGE"; exit 1; }
TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" is4-selftest-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT INT TERM

OUT="$(COLAB_IS4_ENV_FILE="$TMP/missing.env" "$RUNNER" 2>&1)"; RC=$?
[ "$RC" -eq 78 ] || red "입력 env 부재는 78이어야 한다: $RC"
[[ "$OUT" != *"CF_API_TOKEN="* ]] || red "입력 실패가 토큰 값을 출력했다"
echo "  ✓ ⓐ 입력 부재 readiness"

expect_plan() { # want label json
  local want="$1" label="$2" file="$3" out rc
  out="$("$JUDGE" "$file" 2>&1)"; rc=$?
  if [ "$want" = green ] && [ "$rc" -ne 0 ]; then red "$label — $out"
  elif [ "$want" = red ] && [ "$rc" -eq 0 ]; then red "$label — red여야 한다"
  else echo "  ✓ $label ($want)"; fi
  [[ "$out" != *"sensitive-account-id"* ]] || red "$label — 민감 ID가 출력됐다"
}

cat > "$TMP/noop.json" <<'EOF'
{"format_version":"1.2","resource_changes":[{"address":"x.a","change":{"actions":["no-op"],"before":{"id":"sensitive-account-id"},"after":{"id":"sensitive-account-id"},"before_sensitive":{"id":true},"after_sensitive":{"id":true}}}]}
EOF
expect_plan green "ⓑ no-op plan" "$TMP/noop.json"

cat > "$TMP/sensitivity.json" <<'EOF'
{"format_version":"1.2","resource_changes":[{"address":"x.a","change":{"actions":["update"],"before":{"id":"sensitive-account-id","ingress":"same"},"after":{"id":"sensitive-account-id","ingress":"same"},"before_sensitive":{},"after_sensitive":{"id":true}}}]}
EOF
expect_plan green "ⓒ sensitivity-only update" "$TMP/sensitivity.json"

cat > "$TMP/delete.json" <<'EOF'
{"format_version":"1.2","resource_changes":[{"address":"x.a","change":{"actions":["delete"],"before":{"id":"sensitive-account-id"},"after":null}}]}
EOF
expect_plan red "ⓓ delete 거부" "$TMP/delete.json"

cat > "$TMP/change.json" <<'EOF'
{"format_version":"1.2","resource_changes":[{"address":"x.a","change":{"actions":["update"],"before":{"ingress":"www"},"after":{"ingress":"other"}}}]}
EOF
expect_plan red "ⓔ 실제 값 update 거부" "$TMP/change.json"

cat > "$TMP/empty.json" <<'EOF'
{"format_version":"1.2","resource_changes":[]}
EOF
expect_plan red "ⓕ 대상 0건 거부" "$TMP/empty.json"

if rg -n 'cp .*terraform\.tfstate|cp .*\.terraform' "$RUNNER" >/dev/null; then
  red "runner가 기존 state/.terraform을 복사한다"
else
  echo "  ✓ ⓖ 기존 state·plugin 복사 0"
fi

[ "$FAILED" -eq 0 ] || exit 1
echo "is4-recovery-selftest green — 검사 7건 전건 기대대로"
