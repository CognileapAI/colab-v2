#!/usr/bin/env bash
# 실패 픽스처 — preflight 가 **fail-closed** 임을 증명한다.
#
# 무엇을 증명하는가 = 조건이 어긋나면 preflight 가 ⑴ 미달 항목을 **이름으로** 내고
# ⑵ 비영 종료하며 ⑶ 뒤 단계(deploy·reset…)를 **시작하지 않는다**.
#
# dev·AWS 무접촉 = `ssh`·`scp`·`docker`·`aws`·`agent-browser` 를 PATH 앞머리의 대역으로 가린다.
# 대역은 전부 「없다·못 붙는다·fail 이 있다」를 흉내 내므로 실물에 한 바이트도 나가지 않는다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEED="$HERE/../reseed.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/bin" "$TMP/empty-ref-root" "$TMP/run"

# ── 대역 ─────────────────────────────────────────────────────────────────
cat > "$TMP/bin/ssh" <<'STUB'
#!/usr/bin/env bash
echo "ssh: connect to host <대역> port 22: Connection refused" >&2
exit 255
STUB
cp "$TMP/bin/ssh" "$TMP/bin/scp"
cat > "$TMP/bin/docker" <<'STUB'
#!/usr/bin/env bash
# buildx 목록에 linux/arm64 가 없다 — QEMU 등록 소실 상태를 흉내 낸다(이슈 #48 ⑶).
[ "${1:-}" = buildx ] && { echo "NAME/NODE  DRIVER  STATUS  PLATFORMS"; echo "default    docker  running linux/amd64"; exit 0; }
exit 1
STUB
cat > "$TMP/bin/aws" <<'STUB'
#!/usr/bin/env bash
echo "Unable to locate credentials" >&2
exit 255
STUB
cat > "$TMP/bin/agent-browser" <<'STUB'
#!/usr/bin/env bash
[ "${1:-}" = doctor ] && { echo "8 pass · 0 warn · 2 fail"; exit 0; }
exit 0
STUB
chmod +x "$TMP/bin"/*

# ── 실행 ─────────────────────────────────────────────────────────────────
# 어긋나게 둔 것 —
#   ⓐ 대상 ref 가 없는 이름이다               → git
#   ⓑ 참조자료 뿌리가 빈 폴더다               → ref-root · build-plan
#   ⓒ 자원 하한을 실물보다 크게 잡았다        → resources
#   ⓓ ssh 가 붙지 않는다                      → dev-sha · secrets · leftovers
#   ⓔ agent-browser doctor 가 fail 2 를 낸다  → agent-browser
#   ⓕ AWS 자격이 어느 갈래로도 풀리지 않는다  → aws
OUT="$TMP/out.txt"
PATH="$TMP/bin:$PATH" \
COLAB_DEV_SSH='ec2-user@<대역>' COLAB_DEV_KEY_FILE="$TMP/no-such-key" \
COLAB_DEV_URL='https://<대역>' COLAB_REF_ROOT="$TMP/empty-ref-root" \
COLAB_DEV_SECRETS_DIR=/etc/colab \
COLAB_RESEED_MIN_MEM_MIB=99999999 COLAB_RESEED_MIN_DISK_GIB=99999999 \
AWS_ACCESS_KEY_ID= AWS_SECRET_ACCESS_KEY= \
  bash "$RESEED" --target-ref refs/colab-reseed-red-fixture --run-dir "$TMP/run" > "$OUT" 2>&1
RC=$?

echo "── 픽스처 출력 (미달 판정 줄)"
grep -E '  ✗ |미달 항목|단계 preflight 에서 멈췄다|⛔' "$OUT" || true
echo "── 종료코드 = $RC"

# ── 판정 ─────────────────────────────────────────────────────────────────
fail=0
note() { echo "  ✗ $1"; fail=1; }

[ "$RC" -ne 0 ] || note "종료코드가 0 이다 — fail-closed 아님"

for item in git ref-root build-plan resources dev-sha secrets agent-browser aws qemu leftovers; do
  grep -qE "  ✗ $item — " "$OUT" || note "미달 항목 이름에 $item 이 없다"
done

grep -q '단계 deploy 시작' "$OUT" && note "preflight 가 미달인데 deploy 단계가 시작됐다"
grep -q '단계 reset 시작' "$OUT" && note "preflight 가 미달인데 reset 단계가 시작됐다"

# 비밀 값이 로그로 새지 않는지 — 이름만 나와야 한다.
grep -qE '://[^:/@[:space:]]+:[^@[:space:]*]+@' "$OUT" && note "출력에 접속 문자열의 비밀번호 필드가 있다"

if [ "$fail" -eq 0 ]; then
  echo "preflight-red — green (미달 10 항목을 이름으로 내고 비영 종료 · 뒤 단계 미시작)"
  exit 0
fi
echo "preflight-red — red" >&2
exit 1
