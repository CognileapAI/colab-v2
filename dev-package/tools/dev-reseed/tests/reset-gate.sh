#!/usr/bin/env bash
# reset 정지 게이트 픽스처 — 비어 있지 않은 dev 를 **파괴 걸음 앞에서** 멈추는가.
#
# 왜 있나 = 2026-09-24 08:33Z `reseed.sh --from reset` 이 비어 있지 않은 dev DB 를 지웠다.
#   초기화 도구 자신이 d3_dataset 35 · d3_file 585 · d6_project 6 · d4_lineage_edge 22 를 셌는데
#   `stage_reset` 은 `test -s count-before.json` 만 보고 앱 정지·DROP SCHEMA 로 갔고,
#   s3 단계가 DB 가 가리키던 키 1,778 건을 지웠다. 같은 도구가 09-15·09-16 에도 사람이 만든 자료를 지웠다.
#
# 무엇을 증명하는가 —
#   ⓐ 계수가 비어 있지 않고 토큰이 없으면 비영 종료 ＋ 앱 정지·DROP·S3 호출 0 건 ＋ 표별 계수와 토큰을 찍는다
#   ⓑ 토큰이 이번 계수 파일의 sha256 과 다르면(지난 회차 값) 거부한다 — 파괴 호출 0 건
#   ⓒ 토큰 꼴이 sha256 이 아니면 거부한다
#   ⓓ 토큰이 일치하면 진행하고 `reset-ack.json` 에 ack 를 남긴다 · 실행 기록의 계수 파일이 원격 바이트와 같다
#   ⓔ 빈 DB 는 토큰 없이 진행한다
#   ⓕ 계수 파일을 못 받으면 · 옛 모양(경계 경로 · 표 넷)이면 판정 불가로 멈춘다 — 0 으로 읽지 않는다
#   ⓖ 계수는 BYPASSRLS URL 파일(`backup-platform-db.url`)로 돈다 · 그 파일이 없으면 원격이 먼저 멈춘다
#   ⓗ s3 계획이 계수 파일(DB 참조 키)과 같은 토큰을 받는다 · 실행 후 계수도 같은 경로로 돈다
#
# 실물 무접촉 = `ssh`·`docker`·`sudo` 를 PATH 대역으로 가린다. 원격 스크립트는 **실행하지 않고 적기만** 한다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEED_DIR="$HERE/.."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"

fail=0
note() { echo "  ✗ $1"; fail=1; }

# ssh 대역 — `bash -s` 본문은 적기만 한다(마스터 질의에는 활성 트랜잭션 0 을 답한다).
#   argv 명령이 계수 파일을 읽는 자리면 `FIXTURE_COUNT_BEFORE` 의 바이트를 base64 한 줄로 낸다.
cat > "$TMP/bin/ssh" <<'STUB'
#!/usr/bin/env bash
last="${!#}"
if [ "$last" = "bash -s" ]; then
  body="$(cat)"
  printf 'BODY %s\n' "$(printf '%s' "$body" | tr '\n' '~')" >> "$FIXTURE_SSH_LOG"
  case "$body" in *master.url*) echo 0 ;; esac
  exit 0
fi
printf 'CMD %s\n' "$last" >> "$FIXTURE_SSH_LOG"
case "$last" in *count-before.json*)
  [ -n "${FIXTURE_COUNT_BEFORE:-}" ] && base64 -w0 < "$FIXTURE_COUNT_BEFORE"
  exit "${FIXTURE_COUNT_RC:-0}" ;;
esac
exit 0
STUB
printf '#!/usr/bin/env bash\nexit 0\n' > "$TMP/bin/docker"
printf '#!/usr/bin/env bash\nexec "$@"\n' > "$TMP/bin/sudo"
chmod +x "$TMP/bin"/*
export PATH="$TMP/bin:$PATH"

REPO_ROOT="$(cd "$RESEED_DIR/../../.." && pwd)"
RUN_DIR="$TMP/run"; mkdir -p "$RUN_DIR/logs" "$RUN_DIR/stages"
RUN_ID=19700101T000000Z
DRY_RUN=0
TARGET_SHA=deadbeefcafe
S3_BUCKET=colab-platform-data-dev
S3_REGION=ap-northeast-2
EC2_SECRETS_DIR=/etc/colab
COLAB_DEV_SSH='ec2-user@<대역>'
COLAB_DEV_KEY_FILE="$TMP/no-such-key"
CURRENT_STAGE=reset
STAGE_LOG="$RUN_DIR/logs/reset.log"
export FIXTURE_SSH_LOG="$TMP/ssh.log"
export COLAB_RESEED_OPERATOR=fixture
relpath() { printf '%s' "$1"; }

# shellcheck source=../lib.sh
. "$RESEED_DIR/lib.sh"
# shellcheck source=../stages.sh
. "$RESEED_DIR/stages.sh"

NONEMPTY="$HERE/fixtures/count-before-nonempty.json"
EMPTY="$HERE/fixtures/count-before-empty.json"
TOKEN="$(sha256sum "$NONEMPTY" | cut -d' ' -f1)"
OTHER_TOKEN="$(sha256sum "$EMPTY" | cut -d' ' -f1)"   # 꼴은 맞고 값이 다른 토큰(지난 회차 값)

reset_case() {
  : > "$FIXTURE_SSH_LOG"; : > "$STAGE_LOG"
  rm -f "$RUN_DIR/blocked.jsonl" "$RUN_DIR/recovery.jsonl" "$RUN_DIR/reset-ack.json" "$RUN_DIR/count-before.json"
}
destructive_calls() { grep -cE 'stop core-api|start core-api|phase schema|phase s3-' "$FIXTURE_SSH_LOG" || true; }

# ── ⓐ 비어 있지 않음 · 토큰 없음 ─────────────────────────────────────────
reset_case
export FIXTURE_COUNT_BEFORE="$NONEMPTY"
unset COLAB_RESEED_ACK_NONEMPTY
out="$(stage_reset 2>&1)"; rc=$?
[ "$rc" -ne 0 ] || note "ⓐ 비어 있지 않은 계수인데 stage_reset 이 0 으로 끝났다"
n="$(destructive_calls)"
[ "$n" = 0 ] || note "ⓐ′ 비어 있지 않은 계수인데 파괴 호출이 $n 건 나갔다: $(grep -oE 'stop core-api|phase schema|phase s3-[a-z]+' "$FIXTURE_SSH_LOG" | tr '\n' ' ')"
for want in "d3_dataset 35" "d3_file 585" "d6_project 6" "d4_lineage_edge 22" "d1_account 5" \
            "account_admin.login_credential 5" "d5_upload 40" "참조 키 3" "$TOKEN" "COLAB_RESEED_ACK_NONEMPTY"; do
  printf '%s' "$out" | grep -qF "$want" || note "ⓐ″ 정지 메시지에 「$want」 이 없다"
done
grep -q '"name": *"reset"' "$RUN_DIR/blocked.jsonl" 2>/dev/null || note "ⓐ‴ blocked.jsonl 에 reset 차단 기록이 없다"
grep -q '"decision": *"refused"' "$RUN_DIR/reset-ack.json" 2>/dev/null || note "ⓐ⁗ reset-ack.json 에 refused 판정이 없다"

# ── ⓑ 지난 회차 토큰 ──────────────────────────────────────────────────────
reset_case
export COLAB_RESEED_ACK_NONEMPTY="$OTHER_TOKEN"
out="$(stage_reset 2>&1)"; rc=$?
[ "$rc" -ne 0 ] || note "ⓑ 어긋난 토큰을 받아들였다"
n="$(destructive_calls)"; [ "$n" = 0 ] || note "ⓑ′ 어긋난 토큰인데 파괴 호출이 $n 건 나갔다"
printf '%s' "$out" | grep -qF "$TOKEN" || note "ⓑ″ 거부 메시지에 이번 계수의 토큰이 없다"

# ── ⓒ 꼴이 틀린 토큰 ──────────────────────────────────────────────────────
reset_case
export COLAB_RESEED_ACK_NONEMPTY="yes"
stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓒ sha256 꼴이 아닌 토큰을 받아들였다"
n="$(destructive_calls)"; [ "$n" = 0 ] || note "ⓒ′ 꼴이 틀린 토큰인데 파괴 호출이 $n 건 나갔다"

# ── ⓓ 일치하는 토큰 ──────────────────────────────────────────────────────
reset_case
export COLAB_RESEED_ACK_NONEMPTY="$TOKEN"
stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" = 0 ] || note "ⓓ 이번 계수의 토큰을 줬는데 stage_reset 이 비영($rc)이다: $(tail -2 "$STAGE_LOG" | tr '\n' ' ')"
order="$(grep -oE 'phase count|stop core-api|phase schema' "$FIXTURE_SSH_LOG" | tr '\n' '>')"
[ "$order" = 'phase count>stop core-api>phase schema>' ] || note "ⓓ′ 걸음 순서가 [$order] 다(기대 계수>정지>DROP)"
grep -q '"decision": *"acknowledged"' "$RUN_DIR/reset-ack.json" 2>/dev/null || note "ⓓ″ reset-ack.json 에 acknowledged 가 없다"
grep -qF "$TOKEN" "$RUN_DIR/reset-ack.json" 2>/dev/null || note "ⓓ‴ reset-ack.json 에 토큰이 없다"
got="$(sha256sum "$RUN_DIR/count-before.json" 2>/dev/null | cut -d' ' -f1)"
[ "$got" = "$TOKEN" ] || note "ⓓ⁗ 실행 기록의 count-before.json 이 원격 바이트와 다르다"

# ── ⓔ 빈 DB 는 토큰 없이 ──────────────────────────────────────────────────
reset_case
export FIXTURE_COUNT_BEFORE="$EMPTY"
unset COLAB_RESEED_ACK_NONEMPTY
stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" = 0 ] || note "ⓔ 빈 DB 인데 stage_reset 이 비영($rc)이다: $(tail -2 "$STAGE_LOG" | tr '\n' ' ')"
grep -q 'phase schema' "$FIXTURE_SSH_LOG" || note "ⓔ′ 빈 DB 인데 DROP 걸음에 닿지 않았다"
grep -q '"decision": *"empty"' "$RUN_DIR/reset-ack.json" 2>/dev/null || note "ⓔ″ reset-ack.json 에 empty 판정이 없다"

# ── ⓕ 판정 불가 — 파일 없음 · 옛 모양 ────────────────────────────────────
reset_case
export FIXTURE_COUNT_BEFORE=""
stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓕ 계수 파일을 못 받았는데 0 으로 끝났다"
n="$(destructive_calls)"; [ "$n" = 0 ] || note "ⓕ′ 계수 파일 없이 파괴 호출이 $n 건 나갔다"
# 옛 도구의 보고서 — 경계 경로로 센 표 넷(전부 0). 이것을 「비어 있다」로 읽으면 사고가 되풀이된다.
printf '%s\n' '{"db":{"platform":{"labs":1,"rows":{"d3_dataset":0,"d3_file":0,"d4_lineage_edge":0,"d6_project":0},"schemas":["account_admin","public"]}},"phase":"count","schema":"colab-dev-reset-report/1"}' > "$TMP/legacy.json"
reset_case
export FIXTURE_COUNT_BEFORE="$TMP/legacy.json"
stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓕ″ 옛 모양(경계 경로 · 표 넷 0)을 빈 DB 로 읽었다"
n="$(destructive_calls)"; [ "$n" = 0 ] || note "ⓕ‴ 옛 모양 계수에 파괴 호출이 $n 건 나갔다"

# ── ⓖ 계수 경로 ──────────────────────────────────────────────────────────
reset_case
export FIXTURE_COUNT_BEFORE="$EMPTY"
stage_reset >/dev/null 2>&1
body="$(grep -m1 'phase count' "$FIXTURE_SSH_LOG" || true)"
printf '%s' "$body" | grep -q -- '--count-url-file /s/count.url' || note "ⓖ 계수 명령에 --count-url-file 이 없다"
printf '%s' "$body" | grep -q 'backup-platform-db.url:/s/count.url:ro' || note "ⓖ′ 계수 컨테이너가 BYPASSRLS URL 파일을 읽기 전용으로 걸지 않는다"
printf '%s' "$body" | grep -q 'test -f /etc/colab/backup-platform-db.url' || note "ⓖ″ BYPASSRLS URL 파일 부재를 원격이 먼저 거르지 않는다"

# ── ⓗ s3 계획이 같은 토큰으로 DB 참조 키를 대조한다 ────────────────────────
reset_case
CURRENT_STAGE=s3
export COLAB_RESEED_ACK_NONEMPTY="$TOKEN"
stage_s3 >/dev/null 2>&1
plan="$(grep -m1 'phase s3-plan' "$FIXTURE_SSH_LOG" || true)"
printf '%s' "$plan" | grep -q -- '--referenced-keys /out/count-before.json' || note "ⓗ s3-plan 이 계수 파일(DB 참조 키)을 받지 않는다"
printf '%s' "$plan" | grep -q -- "--ack-sha256 $TOKEN" || note "ⓗ′ s3-plan 이 ack 토큰을 받지 않는다"
unset COLAB_RESEED_ACK_NONEMPTY
reset_case
stage_s3 >/dev/null 2>&1
plan="$(grep -m1 'phase s3-plan' "$FIXTURE_SSH_LOG" || true)"
printf '%s' "$plan" | grep -q -- '--ack-sha256' && note "ⓗ″ 토큰이 없는데 s3-plan 에 --ack-sha256 이 실렸다"
# 실행 후 계수(④)도 전수 경로여야 한다 — 도구가 --count-url-file 없는 계수를 거부한다.
after="$(declare -f stage_s3 | grep -c 'reset_count_cmd' || true)"
[ "$after" -ge 1 ] || note "ⓗ‴ stage_s3 ④ 실행 후 계수가 전수 경로(reset_count_cmd)를 쓰지 않는다"
CURRENT_STAGE=reset

if [ "$fail" -eq 0 ]; then
  echo "reset-gate — green (비어 있음 정지 · 지난 토큰 거부 · 꼴 거부 · 일치 진행·ack 기록 · 빈 DB 무토큰 · 판정 불가 정지 · BYPASSRLS 계수 경로 · s3 계획 참조 키 대조)"
  exit 0
fi
echo "reset-gate — red" >&2
exit 1
