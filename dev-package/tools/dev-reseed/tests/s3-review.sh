#!/usr/bin/env bash
# 계획 검토 픽스처 — `stage_s3` ② 와 리허설 ⑸ 가 **같이 쓰는** 계획 검토 본문을 판정한다.
#
# 왜 있나 = 2026-09-14 3회차 실모드가 `s3` ② 에서 멈췄다. 검토 본문이 호스트 ssh 사용자
#   (uid 1000)로 돌면서 초기화 도구 컨테이너(`--user 0`)가 쓴 uid 0 · 0600 계획 파일에
#   `st.st_uid == os.getuid()` 를 걸었다 — 실모드에서 통과할 수 없는 검사다
#   (`dev-package/sessions/DR-4-run-20260914T020005Z.md §7`). 그 경로는 `--dry-run` 이 한 줄을
#   찍기만 하고 `--rehearse` 도 밟지 않아 **어느 검사에도 걸리지 않았다.**
#
# 무엇을 증명하는가 —
#   ⓐ 계획을 쓴 uid 와 검토가 도는 uid 가 같으면 통과하고 키·멀티파트·sha256 을 낸다.
#   ⓑ 두 uid 가 다르면 red — 소유자 단언이 살아 있다(호스트에서 돌리면 이 자리에 걸린다).
#   ⓒ 모드가 0600 이 아니면 red.
#   ⓓ `_ops/` 키가 섞이면 red.
#   ⓔ 허용 밖 접두사가 섞이면 red.
#   ⓕ 계획에 sha256 이 없으면 red(기록할 값이 없다).
#   ⓖ 리허설 ⑸ 가 **같은 본문**을 실제 계획에 돌린다(계획만 · 적용 없음).
#   ⓗ 호스트 쪽에서 계획 파일을 여는 자리가 `stages.sh` 에 0건이다(정적 대조).
#
# 실물 무접촉 = `ssh`·`docker`·`sudo`·`agent-browser` 를 PATH 대역으로 가린다.
# 컨테이너 대역은 `-v <호스트>:<컨테이너>` 를 풀어 경로를 되돌리고, `--user 0` 컨테이너의 uid 를
# `FIXTURE_CONTAINER_UID` 로 흉내 낸다 — 픽스처는 root 가 아니므로 chown 으로는 재현할 수 없다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEED_DIR="$HERE/.."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"

fail=0
note() { echo "  ✗ $1"; fail=1; }

# ── 대역 ─────────────────────────────────────────────────────────────────
cat > "$TMP/bin/ssh" <<'STUB'
#!/usr/bin/env bash
last="${!#}"
if [ "$last" = "bash -s" ]; then
  body="$(cat)"
  printf 'BODY %s\n' "$(printf '%s' "$body" | tr '\n' '~')" >> "$FIXTURE_SSH_LOG"
  bash -s <<<"$body"
  exit $?
fi
printf 'CMD %s\n' "$last" >> "$FIXTURE_SSH_LOG"
exit 0
STUB

cat > "$TMP/bin/docker" <<'STUB'
#!/usr/bin/env bash
maps=()
while [ $# -gt 0 ]; do
  case "$1" in
    run|--rm) shift ;;
    -v) maps+=("$2"); shift 2 ;;
    --network|--user|-e) shift 2 ;;
    -*) shift ;;
    *) break ;;
  esac
done
shift                       # 이미지 이름
cmd=("$@")

unmap() {                   # 컨테이너 경로 → 호스트 경로
  local p="$1" m h c
  for m in ${maps+"${maps[@]}"}; do
    h="${m%%:*}"; c="${m#*:}"; c="${c%%:*}"
    case "$p" in
      "$c")   printf '%s' "$h"; return ;;
      "$c"/*) printf '%s%s' "$h" "${p#"$c"}"; return ;;
    esac
  done
  printf '%s' "$p"
}

case " ${cmd[*]} " in
  *" --phase s3-plan "*)
      out="$(unmap /out)"
      exec python3 "$FIXTURE_PLANGEN" "$out/plan.json" ;;
  *"/tmp/review.py"*)
      exec python3 "$FIXTURE_UIDRUN" "$(unmap "${cmd[1]}")" "$(unmap "${cmd[2]}")" ;;
esac
printf '%s\n' "${FIXTURE_DOCKER_STDOUT:-0}"
exit "${FIXTURE_DOCKER_RC:-0}"
STUB

cat > "$TMP/bin/sudo" <<'STUB'
#!/usr/bin/env bash
while [ $# -gt 0 ]; do case "$1" in -E|-n) shift ;; *=*) shift ;; *) break ;; esac; done
exec "$@"
STUB

cat > "$TMP/bin/agent-browser" <<'STUB'
#!/usr/bin/env bash
printf '%s\n' "${FIXTURE_BROWSER_TITLE-CoLAB}"
exit 0
STUB
chmod +x "$TMP/bin"/*
export PATH="$TMP/bin:$PATH"

# 계획 생성기 — 초기화 도구 `_phase_s3_plan` 과 **같은 정규 직렬화**로 sha256 을 낸다.
export FIXTURE_PLANGEN="$TMP/plangen.py"
cat > "$FIXTURE_PLANGEN" <<'PY'
import hashlib, json, os, sys
path = sys.argv[1]
keys = [k for k in os.environ.get("FIXTURE_PLAN_KEYS", "previews/a.png,uploads/a.tif").split(",") if k]
mp = [p.split("|") for p in os.environ.get("FIXTURE_PLAN_MP", "").split(",") if p]
payload = {"schema": "colab-dev-reset-plan/1",
           "bucket": os.environ.get("FIXTURE_PLAN_BUCKET", "colab-platform-data-dev"),
           "keys": keys, "multipartUploads": mp}
body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
full = dict(payload, sha256=digest)
if os.environ.get("FIXTURE_PLAN_NO_SHA") == "1":
    full.pop("sha256")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    f.write(json.dumps(full, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
os.chmod(path, int(os.environ.get("FIXTURE_PLAN_MODE", "600"), 8))
print("── 계획 %s — 키 %d 건 · 진행 중 멀티파트 %d 건" % (path, len(keys), len(mp)))
print("   sha256 %s" % digest)
PY

# 컨테이너 안 실행 대역 — `--user 0` 컨테이너의 uid 를 흉내 내고 검토 본문을 그대로 돌린다.
export FIXTURE_UIDRUN="$TMP/uidrun.py"
cat > "$FIXTURE_UIDRUN" <<'PY'
import os, sys
script, plan = sys.argv[1], sys.argv[2]
uid = os.environ.get("FIXTURE_CONTAINER_UID", "")
if uid:
    _u = int(uid)
    os.getuid = lambda: _u
sys.argv = [script, plan]
with open(script, encoding="utf-8") as f:
    src = f.read()
exec(compile(src, script, "exec"), {"__name__": "__main__"})
PY

# ── 도구 적재 ────────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$RESEED_DIR/../../.." && pwd)"
RUN_DIR="$TMP/run"; mkdir -p "$RUN_DIR/logs" "$RUN_DIR/stages"
RUN_ID=19700101T000000Z
DRY_RUN=0
TARGET_SHA=deadbeefcafe
S3_BUCKET=colab-platform-data-dev
S3_REGION=ap-northeast-2
EC2_SECRETS_DIR=/etc/colab
DEV_URL='https://dev.invalid'
EXPECT_DATASETS=28
MD_ROOT=""
SEED_WORK_DIR="$TMP/seed-work"
BUILD_PLAN_PY="$TMP/build_plan_stub.py"
COLAB_DEV_SSH='ec2-user@<대역>'
COLAB_DEV_KEY_FILE="$TMP/no-such-key"
CURRENT_STAGE=s3
STAGE_LOG="$RUN_DIR/logs/s3.log"
export FIXTURE_SSH_LOG="$TMP/ssh.log"
: > "$FIXTURE_SSH_LOG"
printf 'print("datasets 28 edges 18")\n' > "$BUILD_PLAN_PY"

relpath() { printf '%s' "$1"; }

# shellcheck source=../lib.sh
. "$RESEED_DIR/lib.sh"
# shellcheck source=../stages.sh
. "$RESEED_DIR/stages.sh"

# 원격 자리를 픽스처 폴더로 돌린다 — 실물 `/tmp/colab-reseed-out` 을 건드리지 않는다.
REMOTE_OUT="$TMP/remote-out"
mkdir -p "$REMOTE_OUT"

# 검토 본문이 아예 없으면 아래 전부가 뜻을 잃는다 — 먼저 판정한다.
if ! declare -F s3_review_script >/dev/null; then
  note "ⓞ stages.sh 에 공용 계획 검토 본문(s3_review_script)이 없다 — ② 와 리허설 ⑸ 가 같은 길을 쓰지 않는다"
  echo "s3-review — red" >&2
  exit 1
fi

reset_logs() { : > "$FIXTURE_SSH_LOG"; : > "$STAGE_LOG"; rm -f "$RUN_DIR/blocked.jsonl"; }

# `stage_s3` 를 통째로 돌린다 — ① 계획 → ② 검토 → ③ 적용 → ④ 계수.
run_s3() {
  reset_logs
  rm -f "$REMOTE_OUT/plan.json"
  stage_s3 >/dev/null 2>&1
}

# ── ⓐ 같은 uid · 0600 · 허용 접두사 → 통과 ────────────────────────────────
unset FIXTURE_CONTAINER_UID FIXTURE_PLAN_MODE FIXTURE_PLAN_KEYS FIXTURE_PLAN_NO_SHA
run_s3; rc=$?
[ "$rc" -eq 0 ] || note "ⓐ 계획을 쓴 uid 와 검토 uid 가 같은데 stage_s3 가 비영 종료했다(rc=$rc): $(grep -m1 -i 'error\|assert' "$STAGE_LOG" || true)"
grep -qE '계획 검토 ok — 키 2 건 · 멀티파트 0 건 .* sha256 [0-9a-f]{64}' "$STAGE_LOG" \
  || note "ⓐ′ 검토 판정줄(키·멀티파트·sha256)이 로그에 없다: $(grep -m1 '계획 검토' "$STAGE_LOG" || echo '<줄 없음>')"

# ── ⓑ 계획을 쓴 uid ≠ 검토 uid → red ──────────────────────────────────────
export FIXTURE_CONTAINER_UID=0          # 계획 파일 소유자는 픽스처 실행자(≠0)다
run_s3; rc=$?
[ "$rc" -ne 0 ] || note "ⓑ 소유자가 다른 계획을 검토가 통과시켰다 — 소유자 단언이 죽었다"
grep -q '소유자' "$STAGE_LOG" || note "ⓑ′ 소유자 불일치가 사유로 남지 않았다"
unset FIXTURE_CONTAINER_UID

# ── ⓒ 모드 0644 → red ────────────────────────────────────────────────────
export FIXTURE_PLAN_MODE=644
run_s3; rc=$?
[ "$rc" -ne 0 ] || note "ⓒ 모드 0644 계획을 검토가 통과시켰다"
grep -q '0600' "$STAGE_LOG" || note "ⓒ′ 모드 미달이 사유로 남지 않았다"
unset FIXTURE_PLAN_MODE

# ── ⓓ `_ops/` 키 → red ───────────────────────────────────────────────────
export FIXTURE_PLAN_KEYS='uploads/a.tif,_ops/backup.sql'
run_s3; rc=$?
[ "$rc" -ne 0 ] || note "ⓓ _ops/ 키가 든 계획을 검토가 통과시켰다"
grep -q '_ops/' "$STAGE_LOG" || note "ⓓ′ _ops/ 키가 사유로 남지 않았다"

# ── ⓔ 허용 밖 접두사 → red ───────────────────────────────────────────────
export FIXTURE_PLAN_KEYS='uploads/a.tif,exports/b.csv'
run_s3; rc=$?
[ "$rc" -ne 0 ] || note "ⓔ 허용 밖 접두사가 든 계획을 검토가 통과시켰다"
grep -q '접두사' "$STAGE_LOG" || note "ⓔ′ 접두사 미달이 사유로 남지 않았다"
unset FIXTURE_PLAN_KEYS

# ── ⓕ sha256 부재 → red ──────────────────────────────────────────────────
export FIXTURE_PLAN_NO_SHA=1
run_s3; rc=$?
[ "$rc" -ne 0 ] || note "ⓕ sha256 이 없는 계획을 검토가 통과시켰다 — 기록할 값이 없다"
grep -q 'sha256' "$STAGE_LOG" || note "ⓕ′ sha256 부재가 사유로 남지 않았다"
unset FIXTURE_PLAN_NO_SHA

# ── ⓖ 리허설 ⑸ 가 같은 본문을 돈다 ───────────────────────────────────────
reset_logs
CURRENT_STAGE=rehearse
STAGE_LOG="$RUN_DIR/logs/rehearse.log"; : > "$STAGE_LOG"
out="$(stage_rehearse 2>&1)"
printf '%s' "$out" | grep -qE '✓ reset_tool_s3_plan' \
  || note "ⓖ 리허설 ⑸ 가 검토 판정줄을 내지 않았다: $(printf '%s' "$out" | grep -m1 'reset_tool_s3_plan' || echo '<줄 없음>')"
printf '%s' "$out" | grep -q '계획 검토 ok' \
  || note "ⓖ′ 리허설 ⑸ 응답에 검토 본문의 판정줄이 없다 — 같은 길을 타지 않았다"
grep -q 's3-apply' "$FIXTURE_SSH_LOG" \
  && note "ⓖ″ 리허설이 s3-apply 를 냈다 — 리허설은 계획까지다"

# ── ⓗ 호스트 쪽에서 계획 파일을 여는 자리 0건 ─────────────────────────────
bad="$(grep -nF 'python3 - "$REMOTE_OUT/plan.json"' "$RESEED_DIR/stages.sh" || true)"
[ -z "$bad" ] || note "ⓗ 호스트 python3 가 계획 파일을 직접 연다:
$(printf '%s' "$bad" | sed 's/^/       /')"
n="$(grep -c 's3_review_script' "$RESEED_DIR/stages.sh")"
[ "$n" -ge 3 ] || note "ⓗ′ 공용 검토 본문 호출이 $n 자리뿐이다(기대 = 정의 1 ＋ stage_s3 ② ＋ 리허설 ⑸)"

if [ "$fail" -eq 0 ]; then
  echo "s3-review — green (uid 일치 통과 · uid 불일치 red · 0644 red · _ops/ red · 접두사 red · sha256 부재 red · 리허설 ⑸ 동일 본문 · 호스트 개봉 0건)"
  exit 0
fi
echo "s3-review — red" >&2
exit 1
