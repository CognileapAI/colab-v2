#!/usr/bin/env bash
# 실제 Cloudflare/Terraform 없이 IS4 입력·plan 판정부를 검증한다.
set -uo pipefail
ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
RUNNER="$ROOT/infra/staging/tunnel/rehearse-state-recovery.sh"
JUDGE="$ROOT/infra/staging/tunnel/validate-recovery-plan.py"
FAILED=0
red() { echo "::error::is4-recovery-selftest red — $*"; FAILED=1; }
[ -x "$RUNNER" ] || { red "runner가 없다: $RUNNER"; exit 1; }
[ -r "$JUDGE" ] || { red "plan 판정부가 없다: $JUDGE"; exit 1; }
TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" is4-selftest-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT INT TERM

OUT="$(COLAB_IS4_ENV_FILE="$TMP/missing.env" "$RUNNER" 2>&1)"; RC=$?
[ "$RC" -eq 78 ] || red "입력 env 부재는 78이어야 한다: $RC"
[[ "$OUT" != *"CF_API_TOKEN="* ]] || red "입력 실패가 토큰 값을 출력했다"
echo "  ✓ ⓐ 입력 부재 readiness"

expect_plan() { # want label json
  local want="$1" label="$2" file="$3" out rc
  out="$(python3 "$JUDGE" "$file" 2>&1)"; rc=$?
  if [ "$want" = green ] && [ "$rc" -ne 0 ]; then red "$label — $out"
  elif [ "$want" = red ] && [ "$rc" -eq 0 ]; then red "$label — red여야 한다"
  else echo "  ✓ $label ($want)"; fi
  [[ "$out" != *"sensitive-account-id"* ]] || red "$label — 민감 ID가 출력됐다"
}

cat > "$TMP/noop.json" <<'EOF'
{"format_version":"1.2","resource_changes":[{"address":"cloudflare_zero_trust_tunnel_cloudflared_config.staging","mode":"managed","type":"cloudflare_zero_trust_tunnel_cloudflared_config","change":{"actions":["no-op"],"before":{"id":"sensitive-account-id"},"after":{"id":"sensitive-account-id"},"before_sensitive":{"id":true},"after_sensitive":{"id":true},"after_unknown":{},"replace_paths":[]}}]}
EOF
expect_plan green "ⓑ no-op plan" "$TMP/noop.json"

cat > "$TMP/sensitivity.json" <<'EOF'
{"format_version":"1.2","resource_changes":[{"address":"cloudflare_zero_trust_tunnel_cloudflared_config.staging","mode":"managed","type":"cloudflare_zero_trust_tunnel_cloudflared_config","change":{"actions":["update"],"before":{"id":"sensitive-account-id","ingress":"same"},"after":{"id":"sensitive-account-id","ingress":"same"},"before_sensitive":{},"after_sensitive":{"id":true},"after_unknown":{},"replace_paths":[]}}]}
EOF
expect_plan green "ⓒ sensitivity-only update" "$TMP/sensitivity.json"

cat > "$TMP/wrong-address.json" <<'EOF'
{"format_version":"1.2","resource_changes":[{"address":"cloudflare_zero_trust_tunnel_cloudflared_config.other","change":{"actions":["update"],"before":{"id":"sensitive-account-id"},"after":{"id":"sensitive-account-id"},"before_sensitive":{},"after_sensitive":{"id":true}}}]}
EOF
expect_plan red "ⓒ-1 다른 resource address 거부" "$TMP/wrong-address.json"

cat > "$TMP/multiple.json" <<'EOF'
{"format_version":"1.2","resource_changes":[{"address":"cloudflare_zero_trust_tunnel_cloudflared_config.staging","change":{"actions":["update"],"before":{"id":"sensitive-account-id"},"after":{"id":"sensitive-account-id"},"before_sensitive":{},"after_sensitive":{"id":true}}},{"address":"x.extra","change":{"actions":["no-op"],"before":{},"after":{}}}]}
EOF
expect_plan red "ⓒ-2 resource 복수 건 거부" "$TMP/multiple.json"

cat > "$TMP/unknown.json" <<'EOF'
{"format_version":"1.2","resource_changes":[{"address":"cloudflare_zero_trust_tunnel_cloudflared_config.staging","mode":"managed","type":"cloudflare_zero_trust_tunnel_cloudflared_config","change":{"actions":["update"],"before":{"id":"sensitive-account-id"},"after":{"id":"sensitive-account-id"},"before_sensitive":{},"after_sensitive":{"id":true},"after_unknown":{"ingress":[{"hostname":true}]},"replace_paths":[]}}]}
EOF
expect_plan red "ⓒ-3 unknown 값 거부" "$TMP/unknown.json"

cat > "$TMP/output-change.json" <<'EOF'
{"format_version":"1.2","output_changes":{"secret":{"actions":["update"]}},"resource_changes":[{"address":"cloudflare_zero_trust_tunnel_cloudflared_config.staging","mode":"managed","type":"cloudflare_zero_trust_tunnel_cloudflared_config","change":{"actions":["update"],"before":{"id":"sensitive-account-id"},"after":{"id":"sensitive-account-id"},"before_sensitive":{},"after_sensitive":{"id":true},"after_unknown":{},"replace_paths":[]}}]}
EOF
expect_plan red "ⓒ-4 output 변경 거부" "$TMP/output-change.json"

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

make_bundle() {
  local dir="$1" image="${2:-repo@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa}"
  mkdir -m 0700 "$dir"
  for name in versions.tf variables.tf tunnel.tf terraform.tfvars.example .terraform.lock.hcl; do
    install -m 0600 "$ROOT/infra/staging/tunnel/$name" "$dir/$name"
  done
  install -m 0600 /dev/null "$dir/final.tfplan"
  printf 'state-fixture' >"$dir/terraform.tfstate"
  install -m 0600 "$TMP/sensitivity.json" "$dir/final-plan.json"
  chmod 0600 "$dir/terraform.tfstate"
  python3 - "$dir" "$image" <<'PY'
import hashlib, json, pathlib, sys
b=pathlib.Path(sys.argv[1]); names=("versions.tf","variables.tf","tunnel.tf","terraform.tfvars.example",".terraform.lock.hcl")
h=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
m={"schema":"colab-is4-recovery/1","address":"cloudflare_zero_trust_tunnel_cloudflared_config.staging",
   "plan_sha256":h(b/"final.tfplan"),"state_sha256":h(b/"terraform.tfstate"),
   "terraform_image":sys.argv[2],"terraform_version":"1.9.8","declarations":{n:h(b/n) for n in names}}
(b/"manifest.json").write_text(json.dumps(m)+"\n")
PY
  chmod 0600 "$dir/manifest.json"
}
expect_bundle() {
  local want="$1" label="$2" dir="$3" sha out rc
  sha="$(sha256sum "$dir/final.tfplan" | cut -d' ' -f1)"
  out="$(python3 "$JUDGE" --verify-bundle "$dir" "$sha" "$ROOT/infra/staging/tunnel" \
    'repo@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' '1.9.8' 2>&1)"; rc=$?
  if [ "$want" = green ] && [ "$rc" -ne 0 ]; then red "$label — $out"
  elif [ "$want" = red ] && [ "$rc" -eq 0 ]; then red "$label — red여야 한다"
  else echo "  ✓ $label ($want)"; fi
}

make_bundle "$TMP/bundle-valid"
expect_bundle green "ⓗ 승인 bundle 대조군" "$TMP/bundle-valid"
make_bundle "$TMP/bundle-image" 'repo@sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
expect_bundle red "ⓘ Terraform image digest 바꿔치기 거부" "$TMP/bundle-image"
make_bundle "$TMP/bundle-plan"
printf x >>"$TMP/bundle-plan/final.tfplan"
expect_bundle red "ⓙ saved plan 바꿔치기 거부" "$TMP/bundle-plan"
make_bundle "$TMP/bundle-permission"
chmod 0644 "$TMP/bundle-permission/terraform.tfstate"
expect_bundle red "ⓚ private file 권한 완화 거부" "$TMP/bundle-permission"
make_bundle "$TMP/bundle-link"
mv "$TMP/bundle-link/final.tfplan" "$TMP/linked-plan"
ln -s "$TMP/linked-plan" "$TMP/bundle-link/final.tfplan"
expect_bundle red "ⓛ saved plan symlink 거부" "$TMP/bundle-link"
make_bundle "$TMP/bundle-declaration"
printf x >>"$TMP/bundle-declaration/tunnel.tf"
expect_bundle red "ⓜ 선언 바꿔치기 거부" "$TMP/bundle-declaration"

mkdir "$TMP/bin"
cat >"$TMP/bin/docker" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
if [ "${1:-}" = image ]; then
  echo 'repo@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
  exit 0
fi
case "$*" in
  *'terraform version -json'*) echo '1.9.8'; exit 0 ;;
esac
work=""
for ((i=1; i<=$#; i++)); do
  if [ "${!i}" = -v ]; then j=$((i+1)); work="${!j%%:/work}"; fi
done
case " $* " in
  *' init -input=false -no-color -lockfile=readonly '*) printf '%s\n' "$*" >"$COLAB_IS4_MOCK_INIT" ;;
  *' show -json final.tfplan '*) cat "$COLAB_IS4_MOCK_PLAN" ;;
  *' plan -refresh-only '*) : >"$work/approval-drift.tfplan" ;;
  *' plan -detailed-exitcode '*) : >"$work/post-apply.tfplan" ;;
  *' apply -input=false -no-color final.tfplan '*) printf '%s\n' "$*" >>"$COLAB_IS4_MOCK_LOG" ;;
  *) exit 1 ;;
esac
SH
chmod 0755 "$TMP/bin/docker"
make_bundle "$TMP/bundle-apply"
cat >"$TMP/apply.env" <<'EOF'
CF_API_TOKEN=test-token
CF_ACCOUNT_ID=test-account
CF_TUNNEL_ID=test-tunnel
EOF
chmod 0600 "$TMP/apply.env"
APPLY_SHA="$(sha256sum "$TMP/bundle-apply/final.tfplan" | cut -d' ' -f1)"
OUT="$(PATH="$TMP/bin:$PATH" COLAB_IS4_ENV_FILE="$TMP/apply.env" \
  COLAB_IS4_MOCK_PLAN="$TMP/sensitivity.json" COLAB_IS4_MOCK_LOG="$TMP/mock.log" \
  COLAB_IS4_MOCK_INIT="$TMP/mock-init.log" \
  "$RUNNER" --apply-approved "$TMP/bundle-apply" --plan-sha256 "$APPLY_SHA" 2>&1)"; RC=$?
[ "$RC" -eq 0 ] || red "ⓝ exact saved plan mock apply — $OUT"
[ "$(wc -l <"$TMP/mock.log" 2>/dev/null || echo 0)" -eq 1 ] || red "ⓝ apply는 정확히 1회여야 한다"
grep -Fq 'apply -input=false -no-color final.tfplan' "$TMP/mock.log" \
  || red "ⓝ apply가 saved final.tfplan을 소비하지 않았다"
grep -Fq 'init -input=false -no-color -lockfile=readonly' "$TMP/mock-init.log" 2>/dev/null \
  || red "ⓝ apply 전 provider lock 검증을 하지 않았다"
echo "  ✓ ⓝ exact saved plan 1회 소비와 후속 No changes (green)"
OUT="$(PATH="$TMP/bin:$PATH" COLAB_IS4_ENV_FILE="$TMP/apply.env" \
  COLAB_IS4_MOCK_PLAN="$TMP/sensitivity.json" COLAB_IS4_MOCK_LOG="$TMP/mock.log" \
  COLAB_IS4_MOCK_INIT="$TMP/mock-init.log" \
  "$RUNNER" --apply-approved "$TMP/bundle-apply" --plan-sha256 "$APPLY_SHA" 2>&1)"; RC=$?
[ "$RC" -ne 0 ] || red "ⓞ 소비한 plan 재사용은 red여야 한다"
echo "  ✓ ⓞ 소비한 plan 재사용 거부 (red)"

[ "$FAILED" -eq 0 ] || exit 1
echo "is4-recovery-selftest green — 검사 19건 전건 기대대로"
