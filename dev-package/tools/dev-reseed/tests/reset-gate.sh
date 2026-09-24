#!/usr/bin/env bash
# reset 정지 게이트 픽스처 — 비어 있지 않은 dev 를 **파괴 걸음 앞에서** 멈추는가.
#
# 왜 있나 = 2026-09-24 08:33Z `reseed.sh --from reset` 이 비어 있지 않은 dev DB 를 지웠다.
#   초기화 도구 자신이 d3_dataset 35 · d3_file 585 · d6_project 6 · d4_lineage_edge 22 를 셌는데
#   `stage_reset` 은 `test -s count-before.json` 만 보고 앱 정지·DROP SCHEMA 로 갔고,
#   s3 단계가 DB 가 가리키던 키 1,778 건을 지웠다. 같은 도구가 09-15·09-16 에도 사람이 만든 자료를 지웠다.
#   2026-09-25 검토가 첫 게이트의 빈자리를 더 찾았다 — `--from s3` 가 지난 회차 계수로 겹침 0 을 내고,
#   DB 0 · 고아 객체를 빈 DB 로 읽고, 거부 메시지가 붙여 넣을 명령을 찍고, 토큰이 회차·시각에 묶이지 않았다.
#
# 무엇을 증명하는가 —
#   ⓐ 비어 있지 않고 토큰이 없으면 비영 ＋ 파괴 호출 0 ＋ 표별 계수 · 시드 기준선 초과분(첫 줄) · 토큰을 찍는다.
#      붙여 넣을 완성 명령(`COLAB_RESEED_ACK_NONEMPTY=…` · `reseed.sh --from reset`)은 찍지 않는다.
#      1회용 challenge(nonce · 만료)가 원격에 선다.
#   ⓑ 지난 challenge 의 토큰 · nonce 없는 sha256(계수) · 꼴 틀린 토큰은 거부한다 — 파괴 호출 0
#   ⓒ GO 근거(COLAB_RESEED_ACK_BASIS)가 없으면 거부한다
#   ⓓ 이번 challenge 토큰 ＋ 근거면 진행한다 — 순서 계수>정지>DROP · reset-ack.json 에 근거·nonce ·
#      challenge 소진 · 같은 토큰 재사용 거부 · 만료 거부 · 도구에 재계수 sha256 ack 를 넘긴다
#   ⓔ 빈 DB 는 토큰 없이 진행한다 · DB 0 이어도 uploads/ 객체·멀티파트가 있으면 멈추고 고아 건수를 찍는다
#   ⓕ 계수 파일을 못 받으면 · 옛 모양(경계 경로 · 표 넷 · 지문 없음)이면 판정 불가로 멈춘다
#   ⓖ 계수는 BYPASSRLS URL 파일 둘로 돈다 · 그 파일이 없으면 원격이 먼저 멈춘다
#   ⓗ reset ① 이 계수 전에 원격의 옛 계수·계획 파일을 지운다
#   ⓘ 초기화 도구가 **실제로 쓴** 계수 파일(가짜 DB·S3 위 `--phase count`)을 게이트가 같은 뜻으로 읽는다
#   ⓙ `--from s3` 가 같은 실행 자리의 reset 판정 없이 s3-plan 을 부르지 않는다(지난 회차 파일 · 내보낸 토큰)
#   ⓚ s3-plan 은 이번 reset 의 DROP 직전 계수와 그 sha256 · 계수 URL 을 받고, 환경의 토큰을 쓰지 않는다
#
# 실물 무접촉 = `ssh`·`docker`·`sudo` 를 PATH 대역으로 가린다. 원격 자리는 임시 폴더다 — argv 명령
# (읽기·지우기·challenge 쓰기)은 그 폴더 위에서 로컬로 돌고, `bash -s` 본문은 적기만 한다
# (계수·재계수 본문은 픽스처 계수 파일을 원격 자리에 놓는 것으로 흉내 낸다).
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEED_DIR="$HERE/.."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/remote"

fail=0
note() { echo "  ✗ $1"; fail=1; }

cat > "$TMP/bin/ssh" <<'STUB'
#!/usr/bin/env bash
last="${!#}"
if [ "$last" = "bash -s" ]; then
  body="$(cat)"
  printf 'BODY %s\n' "$(printf '%s' "$body" | tr '\n' '~')" >> "$FIXTURE_SSH_LOG"
  case "$body" in *master.url*) echo 0; exit 0 ;; esac
  case "$body" in *"--phase count --report /out/count-before.json"*)
    [ -z "${FIXTURE_COUNT_BEFORE:-}" ] || cp "$FIXTURE_COUNT_BEFORE" "$FIXTURE_REMOTE/count-before.json" ;;
  esac
  case "$body" in *"--phase schema"*)
    src="${FIXTURE_COUNT_AT_DROP:-${FIXTURE_COUNT_BEFORE:-}}"
    [ -z "$src" ] || cp "$src" "$FIXTURE_REMOTE/count-at-drop.json" ;;
  esac
  exit 0
fi
printf 'CMD %s\n' "$last" >> "$FIXTURE_SSH_LOG"
bash -c "$last"
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
EXPECT_DATASETS=28
EXPECT_EDGES=18
EXPECT_PROJECTS=4
COLAB_DEV_SSH='ec2-user@<대역>'
COLAB_DEV_KEY_FILE="$TMP/no-such-key"
CURRENT_STAGE=reset
STAGE_LOG="$RUN_DIR/logs/reset.log"
export FIXTURE_SSH_LOG="$TMP/ssh.log" FIXTURE_REMOTE="$TMP/remote"
export COLAB_RESEED_OPERATOR=fixture
relpath() { printf '%s' "$1"; }

# shellcheck source=../lib.sh
. "$RESEED_DIR/lib.sh"
# shellcheck source=../stages.sh
. "$RESEED_DIR/stages.sh"
REMOTE_OUT="$FIXTURE_REMOTE"      # 실물 `/tmp/colab-reseed-out` 을 건드리지 않는다

NONEMPTY="$HERE/fixtures/count-before-nonempty.json"
EMPTY="$HERE/fixtures/count-before-empty.json"
ORPHANS="$HERE/fixtures/count-before-orphans.json"
CONTENT_SHA="$(sha256sum "$NONEMPTY" | cut -d' ' -f1)"   # nonce 없는 옛 꼴 토큰
CHALLENGE="$FIXTURE_REMOTE/reset-challenge.json"

# 이번 challenge 의 토큰 = sha256(계수 바이트 ‖ "\n" ‖ nonce).
token_for() { # $1=계수 파일
  python3 - "$1" "$CHALLENGE" <<'PY'
import hashlib, json, sys
raw = open(sys.argv[1], "rb").read()
nonce = json.load(open(sys.argv[2]))["nonce"]
print(hashlib.sha256(raw + b"\n" + nonce.encode("ascii")).hexdigest())
PY
}

reset_case() {
  : > "$FIXTURE_SSH_LOG"; : > "$STAGE_LOG"
  rm -f "$RUN_DIR/blocked.jsonl" "$RUN_DIR/recovery.jsonl" "$RUN_DIR/reset-ack.json" \
        "$RUN_DIR/count-before.json" "$RUN_DIR/count-at-drop.json"
}
fresh_remote() { rm -rf "$FIXTURE_REMOTE"; mkdir -p "$FIXTURE_REMOTE"; }
destructive_calls() { grep -cE 'stop core-api|start core-api|phase schema|phase s3-' "$FIXTURE_SSH_LOG" || true; }
unset COLAB_RESEED_ACK_NONEMPTY COLAB_RESEED_ACK_BASIS

# ── ⓐ 비어 있지 않음 · 토큰 없음 ─────────────────────────────────────────
fresh_remote; reset_case
export FIXTURE_COUNT_BEFORE="$NONEMPTY"
out="$(stage_reset 2>&1)"; rc=$?
[ "$rc" -ne 0 ] || note "ⓐ 비어 있지 않은 계수인데 stage_reset 이 0 으로 끝났다"
n="$(destructive_calls)"
[ "$n" = 0 ] || note "ⓐ′ 비어 있지 않은 계수인데 파괴 호출이 $n 건 나갔다: $(grep -oE 'stop core-api|phase schema|phase s3-[a-z]+' "$FIXTURE_SSH_LOG" | tr '\n' ' ')"
[ -s "$CHALLENGE" ] || note "ⓐ″ 거부 회차가 원격에 1회용 challenge(nonce · 만료)를 남기지 않았다"
TOKEN1="$( [ -s "$CHALLENGE" ] && token_for "$NONEMPTY" )"
for want in "d3_dataset 35" "d3_file 585" "d6_project 6" "d4_lineage_edge 22" "d1_account 5" \
            "account_admin.login_credential 5" "d5_upload 40" "참조 키 3" "COLAB_RESEED_ACK_NONEMPTY" \
            "COLAB_RESEED_ACK_BASIS" "${TOKEN1:-<토큰 없음>}"; do
  printf '%s' "$out" | grep -qF -- "$want" || note "ⓐ‴ 정지 메시지에 「$want」 이 없다"
done
first="$(printf '%s\n' "$out" | grep -m1 '⛔' || true)"
for want in "d3_dataset +7" "d4_lineage_edge +4" "d6_project +2"; do
  printf '%s' "$first" | grep -qF -- "$want" || note "ⓐ⁗ 정지 메시지 첫 줄에 시드 기준선 초과분 「$want」 이 없다: $first"
done
printf '%s' "$out" | grep -qE 'COLAB_RESEED_ACK_NONEMPTY=|reseed\.sh --from reset' \
  && note "ⓐ⁗′ 거부 메시지가 붙여 넣을 완성 명령을 찍었다 — 에이전트가 그대로 복사해 넘기는 자리다"
grep -q '"name": *"reset"' "$RUN_DIR/blocked.jsonl" 2>/dev/null || note "ⓐ⁗″ blocked.jsonl 에 reset 차단 기록이 없다"
grep -q '"decision": *"refused"' "$RUN_DIR/reset-ack.json" 2>/dev/null || note "ⓐ⁗‴ reset-ack.json 에 refused 판정이 없다"

# ── ⓑ 지난 challenge 토큰 · nonce 없는 토큰 · 꼴 틀린 토큰 ────────────────
export COLAB_RESEED_ACK_BASIS="fixture — 사용자 GO(시험)"
reset_case
stage_reset >/dev/null 2>&1                       # 새 거부 회차 = 새 nonce
TOKEN2="$(token_for "$NONEMPTY")"
[ "$TOKEN2" != "$TOKEN1" ] || note "ⓑ 거부 회차마다 nonce 가 바뀌지 않는다 — 토큰이 회차에 묶이지 않는다"
for stale in "$TOKEN1" "$CONTENT_SHA" "yes"; do
  reset_case
  export COLAB_RESEED_ACK_NONEMPTY="$stale"
  stage_reset >/dev/null 2>&1; rc=$?
  [ "$rc" -ne 0 ] || note "ⓑ′ 이번 challenge 가 아닌 토큰(${stale:0:12}…)을 받아들였다"
  n="$(destructive_calls)"; [ "$n" = 0 ] || note "ⓑ″ 어긋난 토큰(${stale:0:12}…)인데 파괴 호출이 $n 건 나갔다"
done

# ── ⓒ GO 근거 없음 ──────────────────────────────────────────────────────
reset_case
TOKEN="$(token_for "$NONEMPTY")"
export COLAB_RESEED_ACK_NONEMPTY="$TOKEN"
unset COLAB_RESEED_ACK_BASIS
stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓒ 사용자 GO 근거(COLAB_RESEED_ACK_BASIS) 없이 토큰만으로 넘어갔다"
n="$(destructive_calls)"; [ "$n" = 0 ] || note "ⓒ′ 근거 없는 토큰인데 파괴 호출이 $n 건 나갔다"

# ── ⓓ 이번 challenge 토큰 ＋ 근거 ─────────────────────────────────────────
reset_case
TOKEN="$(token_for "$NONEMPTY")"
export COLAB_RESEED_ACK_NONEMPTY="$TOKEN" COLAB_RESEED_ACK_BASIS="fixture — 사용자 GO(시험)"
stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" = 0 ] || note "ⓓ 이번 challenge 토큰을 줬는데 stage_reset 이 비영($rc)이다: $(tail -2 "$STAGE_LOG" | tr '\n' ' ')"
order="$(grep -oE 'phase count|stop core-api|phase schema' "$FIXTURE_SSH_LOG" | tr '\n' '>')"
[ "$order" = 'phase count>stop core-api>phase schema>' ] || note "ⓓ′ 걸음 순서가 [$order] 다(기대 계수>정지>DROP)"
python3 - "$RUN_DIR/reset-ack.json" "$TOKEN" "$CONTENT_SHA" <<'PY' || note "ⓓ″ reset-ack.json 의 ack 기록이 모자라다"
import json, sys
b = json.load(open(sys.argv[1]))
ok = (b.get("decision") == "acknowledged" and b.get("ackToken") == sys.argv[2]
      and b.get("toolAckSha256") == sys.argv[3] and b.get("ackBasis")
      and (b.get("challenge") or {}).get("nonce"))
sys.exit(0 if ok else 1)
PY
[ -e "$CHALLENGE" ] && note "ⓓ‴ 쓴 challenge 가 소진되지 않았다 — 같은 토큰이 다시 통한다"
schema_body="$(grep -m1 'phase schema' "$FIXTURE_SSH_LOG" || true)"
printf '%s' "$schema_body" | grep -q -- "--ack-sha256 $CONTENT_SHA" \
  || note "ⓓ⁗ 도구 --phase schema 에 재계수 대조용 ack(계수 sha256)가 실리지 않았다"
printf '%s' "$schema_body" | grep -q -- '--count-report /out/count-at-drop.json' \
  || note "ⓓ⁗′ 도구 --phase schema 가 DROP 직전 재계수 자리를 받지 않는다"
printf '%s' "$schema_body" | grep -q -- '--count-ai-url-file /s/count-ai.url' \
  || note "ⓓ⁗″ 도구 --phase schema 가 계수 URL(두 체인)을 받지 않는다"
cmp -s "$RUN_DIR/count-at-drop.json" "$FIXTURE_REMOTE/count-at-drop.json" \
  || note "ⓓ⁗‴ 실행 기록의 count-at-drop.json 이 원격 바이트와 다르다"
got="$(sha256sum "$RUN_DIR/count-before.json" 2>/dev/null | cut -d' ' -f1)"
[ "$got" = "$CONTENT_SHA" ] || note "ⓓ⁵ 실행 기록의 count-before.json 이 원격 바이트와 다르다"
# 같은 토큰 재사용 — 소진됐다
reset_case
stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓓ⁶ 한 번 쓴 토큰이 다시 통했다"
n="$(destructive_calls)"; [ "$n" = 0 ] || note "ⓓ⁶′ 재사용 토큰인데 파괴 호출이 $n 건 나갔다"
# 만료 — 새 challenge 의 만료 시각을 과거로 돌린다
reset_case
python3 - "$CHALLENGE" <<'PY'
import json, sys
p = sys.argv[1]; b = json.load(open(p)); b["expiresAt"] = "2000-01-01T00:00:00+00:00"
json.dump(b, open(p, "w"))
PY
export COLAB_RESEED_ACK_NONEMPTY="$(token_for "$NONEMPTY")"
stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓓ⁷ 만료된 challenge 의 토큰을 받아들였다"
n="$(destructive_calls)"; [ "$n" = 0 ] || note "ⓓ⁷′ 만료 토큰인데 파괴 호출이 $n 건 나갔다"
unset COLAB_RESEED_ACK_NONEMPTY COLAB_RESEED_ACK_BASIS

# ── ⓔ 빈 DB 는 토큰 없이 · 고아 객체는 멈춘다 ─────────────────────────────
fresh_remote; reset_case
export FIXTURE_COUNT_BEFORE="$EMPTY"
stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" = 0 ] || note "ⓔ 빈 DB 인데 stage_reset 이 비영($rc)이다: $(tail -2 "$STAGE_LOG" | tr '\n' ' ')"
grep -q 'phase schema' "$FIXTURE_SSH_LOG" || note "ⓔ′ 빈 DB 인데 DROP 걸음에 닿지 않았다"
grep -m1 'phase schema' "$FIXTURE_SSH_LOG" | grep -q -- '--ack-sha256' && note "ⓔ″ 빈 DB 인데 도구에 ack 가 실렸다"
grep -q '"decision": *"empty"' "$RUN_DIR/reset-ack.json" 2>/dev/null || note "ⓔ‴ reset-ack.json 에 empty 판정이 없다"
fresh_remote; reset_case
export FIXTURE_COUNT_BEFORE="$ORPHANS"
out="$(stage_reset 2>&1)"; rc=$?
[ "$rc" -ne 0 ] || note "ⓔ⁗ DB 0 · uploads/ 객체 5 · 멀티파트 1 을 빈 DB 로 읽었다 — 업로드 원본은 백업 경로가 없다"
n="$(destructive_calls)"; [ "$n" = 0 ] || note "ⓔ⁗′ 고아 객체가 있는데 파괴 호출이 $n 건 나갔다"
printf '%s' "$out" | grep -q '고아 5' || note "ⓔ⁗″ DB 가 가리키지 않는 객체(고아) 건수를 따로 찍지 않았다"

# ── ⓕ 판정 불가 — 파일 없음 · 옛 모양 ────────────────────────────────────
fresh_remote; reset_case
export FIXTURE_COUNT_BEFORE=""
stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓕ 계수 파일을 못 받았는데 0 으로 끝났다"
n="$(destructive_calls)"; [ "$n" = 0 ] || note "ⓕ′ 계수 파일 없이 파괴 호출이 $n 건 나갔다"
# 옛 도구의 보고서 — 경계 경로로 센 표 넷(전부 0). 이것을 「비어 있다」로 읽으면 사고가 되풀이된다.
printf '%s\n' '{"db":{"platform":{"labs":1,"rows":{"d3_dataset":0,"d3_file":0,"d4_lineage_edge":0,"d6_project":0},"schemas":["account_admin","public"]}},"phase":"count","schema":"colab-dev-reset-report/1"}' > "$TMP/legacy.json"
# 첫 게이트 세대의 보고서 — 전수 경로 표지는 있지만 표 지문·AI 계수·S3 키 목록 지문이 없다(토큰 밖 편집).
python3 - "$EMPTY" "$TMP/gen1.json" <<'PY'
import json, sys
b = json.load(open(sys.argv[1]))
b["db"]["platform"].pop("tables"); b["db"]["ai"] = {"schemas": ["public"]}
b["s3"].pop("objectsSha256"); b["s3"].pop("multipartSha256")
open(sys.argv[2], "w").write(json.dumps(b, sort_keys=True, indent=2) + "\n")
PY
for shape in legacy gen1; do
  fresh_remote; reset_case
  export FIXTURE_COUNT_BEFORE="$TMP/$shape.json"
  stage_reset >/dev/null 2>&1; rc=$?
  [ "$rc" -ne 0 ] || note "ⓕ″ 옛 모양($shape) 계수를 빈 DB 로 읽었다"
  n="$(destructive_calls)"; [ "$n" = 0 ] || note "ⓕ‴ 옛 모양($shape) 계수에 파괴 호출이 $n 건 나갔다"
done

# ── ⓖ 계수 경로 ──────────────────────────────────────────────────────────
fresh_remote; reset_case
export FIXTURE_COUNT_BEFORE="$EMPTY"
stage_reset >/dev/null 2>&1
body="$(grep -m1 'phase count' "$FIXTURE_SSH_LOG" || true)"
for want in '--count-url-file /s/count.url' '--count-ai-url-file /s/count-ai.url' \
            'backup-platform-db.url:/s/count.url:ro' 'backup-ai-db.url:/s/count-ai.url:ro' \
            'test -f /etc/colab/backup-platform-db.url' 'test -f /etc/colab/backup-ai-db.url'; do
  printf '%s' "$body" | grep -qF -- "$want" || note "ⓖ 계수 본문에 「$want」 이 없다(BYPASSRLS 계수 URL 두 체인)"
done

# ── ⓗ 옛 원격 파일은 계수 전에 지운다 ──────────────────────────────────────
fresh_remote; reset_case
for f in plan.json s3-plan.json schema.json count-at-drop.json count-after.json; do printf 'stale\n' > "$FIXTURE_REMOTE/$f"; done
export FIXTURE_COUNT_BEFORE="$NONEMPTY"
stage_reset >/dev/null 2>&1
for f in plan.json s3-plan.json schema.json count-at-drop.json count-after.json; do
  [ -e "$FIXTURE_REMOTE/$f" ] && note "ⓗ reset ① 이 원격의 옛 $f 를 지우지 않았다"
done
order="$(grep -oE 'rm -f [^ ]*count-before.json|phase count' "$FIXTURE_SSH_LOG" | sed 's/rm -f .*/rm/' | tr '\n' '>')"
[ "$order" = 'rm>phase count>' ] || note "ⓗ′ 옛 파일 지우기와 계수의 순서가 [$order] 다(기대 rm>phase count)"

# ── ⓘ 도구가 실제로 쓰는 계수 파일 ↔ 정지 게이트 판독 ─────────────────────
# 위 픽스처는 손으로 쓴 모양이다. 도구(`reset_dev_environment.py --phase count`)를 가짜 DB·S3 로
# 실제로 돌려 나온 파일을 게이트에 넣는다 — 두 쪽 모양이 갈리면 게이트가 늘 「판정 불가」로 서거나
# 더 나쁘게 빈 DB 로 읽는 자리를 여기서 잡는다.
cat > "$TMP/run_tool.py" <<'PY'
import importlib.util, os, sys
tool, out, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
spec = importlib.util.spec_from_file_location("reset_tool", tool)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class Cur:
    def __init__(self): self.rows = []
    def execute(self, sql, params=None):
        s = sql.lower()
        self.rows = ([("public", "d3_dataset"), ("public", "d3_dataset_description")] if "relkind" in s else
                     [("public",), ("account_admin",)] if "pg_namespace" in s else
                     [(True,)] if "rolbypassrls" in s else
                     [] if "to_regclass" in s else
                     [("uploads/L/%d.nc" % i,) for i in range(n)] if "storage_key" in s else
                     [(n, "0" * 32)] if "string_agg" in s else
                     [(n,)] if "count(*)" in s else [])
    def fetchone(self): return self.rows[0] if self.rows else None
    def fetchall(self): return list(self.rows)
    def __enter__(self): return self
    def __exit__(self, *a): return False
class Conn:
    def cursor(self): return Cur()
    def rollback(self): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
class S3:
    def list_objects(self, prefix): return iter([("uploads/L/%d.nc" % i, 3) for i in range(n)] if prefix == "uploads/" else [])
    def list_multipart_uploads(self, prefix=""): return []
d = os.path.dirname(out)
for name, db, user in (("p", "colab_platform", "colab_owner"), ("a", "colab_ai", "colab_owner"),
                       ("c", "colab_platform", "colab_backup"), ("ca", "colab_ai", "colab_backup")):
    with open(os.path.join(d, name + ".url"), "w") as f:
        f.write("postgresql://%s:x@colab-v2-dev-pg.invalid:5432/%s" % (user, db))
os.environ.update(COLAB_CORE_S3_BUCKET="colab-platform-data-dev", COLAB_CORE_S3_REGION="ap-northeast-2")
sys.exit(m.main(["--target", "dev", "--yes-reset-dev", "--phase", "count",
                 "--platform-url-file", os.path.join(d, "p.url"), "--ai-url-file", os.path.join(d, "a.url"),
                 "--count-url-file", os.path.join(d, "c.url"), "--count-ai-url-file", os.path.join(d, "ca.url"),
                 "--report", out],
                connect=lambda url: Conn(), s3_factory=lambda **kw: S3()))
PY
mkdir -p "$TMP/tool"
TOOL="$REPO_ROOT/services/core-api/ops/reset_dev_environment.py"
export COLAB_RESEED_ACK_BASIS="fixture — 사용자 GO(시험)"
for n in 0 2; do
  if python3 "$TMP/run_tool.py" "$TOOL" "$TMP/tool/count-$n.json" "$n" >/dev/null 2>"$TMP/tool/err"; then :; else
    note "ⓘ 도구 --phase count 가 가짜 DB 위에서 비영 종료했다: $(tail -1 "$TMP/tool/err")"; continue
  fi
  fresh_remote; reset_case
  export FIXTURE_COUNT_BEFORE="$TMP/tool/count-$n.json"
  unset COLAB_RESEED_ACK_NONEMPTY
  stage_reset >/dev/null 2>&1; rc=$?
  if [ "$n" = 0 ]; then
    [ "$rc" = 0 ] || note "ⓘ′ 도구가 쓴 빈 계수를 게이트가 통과시키지 않았다: $(grep -m1 '정지 게이트' "$STAGE_LOG")"
  else
    [ "$rc" -ne 0 ] || note "ⓘ″ 도구가 쓴 비어 있지 않은 계수를 게이트가 통과시켰다"
    n2="$(destructive_calls)"; [ "$n2" = 0 ] || note "ⓘ‴ 도구 계수가 비어 있지 않은데 파괴 호출이 $n2 건 나갔다"
    reset_case
    export COLAB_RESEED_ACK_NONEMPTY="$(token_for "$FIXTURE_COUNT_BEFORE")"
    stage_reset >/dev/null 2>&1 || note "ⓘ⁗ 도구 계수 파일의 이번 challenge 토큰을 줬는데 거부됐다"
    unset COLAB_RESEED_ACK_NONEMPTY
  fi
done
unset COLAB_RESEED_ACK_BASIS

# ── ⓙ `--from s3` — 같은 실행 자리의 reset 판정 없이는 계획을 세우지 않는다 ─────
CURRENT_STAGE=s3
fresh_remote; reset_case
cp "$EMPTY" "$FIXTURE_REMOTE/count-before.json"          # 지난 회차가 남긴 파일(그 키는 이미 지워졌다)
export COLAB_RESEED_ACK_NONEMPTY="$CONTENT_SHA"          # 옛 회차에 export 해 둔 토큰
stage_s3 >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓙ 이번 실행 자리에 reset 판정이 없는데 stage_s3 가 0 으로 끝났다"
grep -q 'phase s3-' "$FIXTURE_SSH_LOG" \
  && note "ⓙ′ reset 판정 없이 s3-plan/s3-apply 를 불렀다 — 지난 회차 계수로 겹침 0 을 낸다"

# ── ⓚ 이번 reset 의 DROP 직전 계수에 묶인 계획 ─────────────────────────────
fresh_remote; reset_case
export FIXTURE_COUNT_BEFORE="$EMPTY"
CURRENT_STAGE=reset; stage_reset >/dev/null 2>&1 || note "ⓚ 준비 — 빈 DB reset 이 비영이다"
CURRENT_STAGE=s3
: > "$FIXTURE_SSH_LOG"
AT_DROP_SHA="$(sha256sum "$RUN_DIR/count-at-drop.json" 2>/dev/null | cut -d' ' -f1)"
stage_s3 >/dev/null 2>&1
plan="$(grep -m1 'phase s3-plan' "$FIXTURE_SSH_LOG" || true)"
for want in '--referenced-keys /out/count-at-drop.json' "--referenced-sha256 $AT_DROP_SHA" \
            '--count-url-file /s/count.url'; do
  printf '%s' "$plan" | grep -qF -- "$want" || note "ⓚ′ s3-plan 에 「$want」 이 없다"
done
printf '%s' "$plan" | grep -q -- '--ack-sha256' && note "ⓚ″ 빈 reset 인데 환경의 토큰이 s3-plan 에 실렸다"
order="$(printf '%s' "$plan" | grep -oE 'rm -f [^~]*plan.json|--phase s3-plan' | sed 's/rm -f .*/rm/' | tr '\n' '>')"
[ "$order" = 'rm>--phase s3-plan>' ] || note "ⓚ‴ 계획 전에 원격의 옛 plan.json 을 지우지 않는다: [$order]"
# acknowledged reset 이면 그 판정의 도구 ack 를 싣는다
python3 - "$RUN_DIR/reset-ack.json" <<'PY'
import json, sys
p = sys.argv[1]; b = json.load(open(p))
b.update(decision="acknowledged", toolAckSha256="a" * 64)
json.dump(b, open(p, "w"))
PY
: > "$FIXTURE_SSH_LOG"
stage_s3 >/dev/null 2>&1
grep -m1 'phase s3-plan' "$FIXTURE_SSH_LOG" | grep -q -- "--ack-sha256 $(printf 'a%.0s' $(seq 64))" \
  || note "ⓚ⁗ acknowledged reset 의 도구 ack 가 s3-plan 에 실리지 않았다"
# 실행 후 계수(④)도 전수 경로여야 한다 — 도구가 계수 URL 없는 계수를 거부한다.
after="$(declare -f stage_s3 | grep -c 'reset_count_cmd' || true)"
[ "$after" -ge 2 ] || note "ⓚ⁵ stage_s3 의 계획·실행 후 계수가 전수 경로(reset_count_cmd)를 쓰지 않는다"
unset COLAB_RESEED_ACK_NONEMPTY
CURRENT_STAGE=reset

if [ "$fail" -eq 0 ]; then
  echo "reset-gate — green (비어 있음 정지 · 기준선 초과 첫 줄 · 완성 명령 무출력 · 1회용 challenge · 지난·옛 꼴 토큰 거부 · 근거 필수 · 소진·만료 · 빈 DB 무토큰 · 고아 객체 정지 · 판정 불가 정지 · BYPASSRLS 두 체인 · 옛 원격 파일 삭제 · 도구 계수 ↔ 게이트 · --from s3 무판정 거부 · s3 계획 이번 reset 묶임)"
  exit 0
fi
echo "reset-gate — red" >&2
exit 1
