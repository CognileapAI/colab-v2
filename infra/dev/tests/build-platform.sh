#!/usr/bin/env bash
# Both real build entrypoints use a selected-builder stub; no image build or registration occurs.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"
cat > "$TMP/bin/docker" <<'STUB'
#!/usr/bin/env bash
echo "$*" >> "$BUILD_TRACE"
case "$1 $2" in
  'buildx version') exit 0 ;;
  'buildx inspect')
    [ "$BUILD_MODE" != unavailable ] || exit 1
    echo "Name: ${BUILDX_BUILDER}"
    case "$BUILD_MODE" in
      unsupported) echo 'Platforms: linux/amd64' ;;
      native_arm) echo 'Platforms: linux/arm64' ;;
      native_amd) echo 'Platforms: linux/amd64*' ;;
      remote) echo 'Platforms: linux/amd64, linux/arm64/v8*' ;;
    esac ;;
  'buildx ls') echo 'other-builder linux/arm64'; exit 0 ;;
  'buildx build') exit 0 ;;
  'image inspect') echo "${COLAB_BUILD_PLATFORM#linux/}" ;;
  'save -o') : > "$3" ;;
  *) exit 99 ;;
esac
STUB
chmod +x "$TMP/bin/docker"
PASS=0; FAIL=0
for environment in dev prod; do
  for mode in unavailable unsupported native_arm native_amd remote; do
    trace="$TMP/$environment-$mode.trace"; : > "$trace"
    target=linux/arm64; want=0; builds=5
    [ "$mode" != native_amd ] || target=linux/amd64
    case "$mode" in unavailable|unsupported) want=78; builds=0 ;; esac
    ec=0
    out="$(PATH="$TMP/bin:$PATH" BUILD_TRACE="$trace" BUILD_MODE="$mode" \
      BUILDX_BUILDER=selected COLAB_BUILD_PLATFORM="$target" \
      bash "$ROOT/infra/$environment/build.sh" "$TMP/$environment-$mode" 2>&1)" || ec=$?
    actual="$(grep -c '^buildx build ' "$trace" || true)"
    if [ "$ec" -eq "$want" ] && [ "$actual" -eq "$builds" ] &&
       grep -q '^buildx inspect --bootstrap$' "$trace" && ! grep -q '^buildx ls' "$trace"; then
      echo "  ✓ $environment $mode — exit $ec · builds $actual"
      PASS=$((PASS+1))
    else
      echo "  ✗ $environment $mode — expected exit $want/builds $builds, got $ec/$actual"
      printf '%s\n' "$out" | tail -5
      FAIL=$((FAIL+1))
    fi
  done
done
echo "build-platform selftest — 통과 $PASS · 실패 $FAIL"
[ "$FAIL" -eq 0 ]
