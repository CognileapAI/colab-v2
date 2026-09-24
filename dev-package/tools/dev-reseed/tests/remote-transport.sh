#!/usr/bin/env bash
# 원격 원시동작 픽스처 — `stages.sh` 가 **원격 셸로 값을 나르는 자리**와 `reset` 의 실패 순서를 판정한다.
#
# 왜 있나 = 2026-09-14 회차의 `reset` 은 `psql_master_query` 가 SQL 을 `export SQL='<값>'` 로
#   싣는 바람에 값 속 작은따옴표가 바깥 따옴표를 닫아 멈췄다(`column "colab_platform" does not exist`).
#   그 경로는 **실모드로 돈 적이 없었고** `--dry-run` 은 본문을 찍기만 해서 어느 검사에도 걸리지 않았다.
#   같은 계열이 `prelude` ②④ 와 `login_credential` 에도 있었다.
#
# 무엇을 증명하는가 —
#   ⓐ 작은따옴표·`$`·백틱·큰따옴표가 든 SQL 이 원격 셸을 거쳐 **한 바이트도 바뀌지 않고** psql 에 닿는다.
#   ⓑ 정지(①′) 뒤의 걸음이 실패하면 앱을 **자동으로 되살리고** `recovery.jsonl` 에 적는다.
#   ⓒ 실패 한 건이 단계 로그에 **한 번만** 보인다(종전 이중 기록).
#   ⓓ `stage_rehearse` 가 `--dry-run` 에서 원격에 **한 바이트도** 내지 않는다.
#   ⓔ 원시동작의 응답이 기대와 어긋나면 **이름을 대고** 비영 종료한다(fail-closed).
#   ⓕ 값을 `='<값>'` 한 겹으로 싣는 자리가 `stages.sh` 에 0건이다(정적 대조).
#   ⓖ prelude ③ `login_credential` — 파이썬 본문은 **환경변수**로, 비밀번호는 **표준입력 한 줄**로
#      컨테이너에 닿고(둘 다 한 바이트도 바뀌지 않는다), 비밀번호가 원격 스크립트·단계 로그에 0건이며,
#      컨테이너 안에 파일을 두는 자리(`docker cp`)가 `stages.sh` 에 0건이다. 컨테이너가 비영이면 red.
#      왜 = 2026-09-14 4회차(`20260914T022417Z`)가 여기서 멈췄다 — `docker cp` 가 호스트 소유자
#      (uid 1000 · 0600)를 그대로 옮겨 앱 사용자(uid 10001)가 `/tmp/reseed_cred.py` 를 열지 못했다.
#      그 줄도 실모드로 돈 적이 없었고 `--dry-run`·`--rehearse` 어느 쪽도 밟지 않았다.
#   ⓗ 컨테이너가 받은 그 파이썬 본문을 **실제로 실행**한다 — 실물 `password.py`(표준 라이브러리만) ＋
#      sqlalchemy 대역(SQL 의 `:이름` 이 전부 params 에 있어야 한다 · 실물 `construct_params` 와 같은 조건).
#      왜 = 4회차 재개(`20260914T023145Z`)가 `:password_hash` 바인드에 `as_dict()` 의 `hash` 키를 물려
#      「A value is required for bind parameter 'password_hash'」 로 멈췄다. 본문이 돈 적이 없었다.
#   ⓘ prelude ②④ — psql `-v` 변수 값의 꼴이 **SQL 파일의 변수 꼴**과 맞는다. `:'name'` 은 원문,
#      맨 `:name` 은 감싼 값. stage_prelude 전체를 대역 위에서 돌리고 psql 대역이 적은 argv 를 실물
#      SQL 과 대조한다. 왜 = 4회차 재개 2(`20260914T023537Z`)가 ④ 에 감싼 값을 넘겨 `INSERT 0 0` 으로 멈췄다.
#
# 실물 무접촉 = `ssh`·`docker`·`sudo`·`psql`·`agent-browser` 를 PATH 대역으로 가린다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEED_DIR="$HERE/.."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"

fail=0
note() { echo "  ✗ $1"; fail=1; }

# ── 대역 ─────────────────────────────────────────────────────────────────
# ssh 대역 = 표준입력으로 받은 원격 스크립트를 **로컬 bash 로 그대로 실행**한다.
#   그래야 「원격 셸이 그 문장을 어떻게 읽는가」가 재현된다 — 따옴표 결함이 잡히는 자리다.
#   `FIXTURE_EXEC=0` 이면 본문을 적기만 하고 실행하지 않는다(순서 판정용).
cat > "$TMP/bin/ssh" <<'STUB'
#!/usr/bin/env bash
last="${!#}"
if [ "$last" = "bash -s" ]; then
  body="$(cat)"
  printf 'BODY %s\n' "$(printf '%s' "$body" | tr '\n' '~')" >> "$FIXTURE_SSH_LOG"
  if [ -n "${FIXTURE_FAIL_MATCH:-}" ]; then
    case "$body" in *"$FIXTURE_FAIL_MATCH"*) echo "대역 실패 — 본문 일치" >&2; exit 7 ;; esac
  fi
  if [ "${FIXTURE_EXEC:-0}" = 1 ]; then bash -s <<<"$body"; exit $?; fi
  case "$body" in *master.url*)
    if [ -n "${FIXTURE_TX_SEQUENCE:-}" ]; then
      n=$(cat "$FIXTURE_TX_SEQUENCE"); echo $((n + 1)) > "$FIXTURE_TX_SEQUENCE"
      [ "$n" = 0 ] && echo 0 || echo 1
    else
      printf '%s\n' "${FIXTURE_TX_REPLY:-0}"
    fi
    exit "${FIXTURE_TX_RC:-0}"
  ;; esac
  exit 0
fi
printf 'CMD %s\n' "$last" >> "$FIXTURE_SSH_LOG"
# reset 정지 게이트·DROP 직전 재계수를 되읽는 자리 — 빈 DB 계수를 낸다(정지 게이트 자체는 `reset-gate.sh` 가 판정한다).
case "$last" in *"base64 -w0"*count-before.json*|*"base64 -w0"*count-at-drop.json*)
  base64 -w0 < "$FIXTURE_COUNT_BEFORE"; exit 0 ;; esac
if [ -n "${FIXTURE_DOCTOR_FILE:-}" ]; then
  cat "$FIXTURE_DOCTOR_FILE"
  exit "${FIXTURE_DOCTOR_RC:-0}"
fi
if [ -n "${FIXTURE_FAIL_MATCH:-}" ]; then
  case "$last" in *"$FIXTURE_FAIL_MATCH"*) echo "대역 실패 — 명령 일치" >&2; exit 7 ;; esac
fi
# 원격 스크립트가 **argv** 로 오는 자리(prelude ③) — `FIXTURE_EXEC_CMD=1` 이면 표준입력을 물려 로컬 bash 로 실행한다.
if [ "${FIXTURE_EXEC_CMD:-0}" = 1 ]; then bash -c "$last"; exit $?; fi
exit 0
STUB
# docker 대역 = `-e SQL` 로 받은 값을 **있는 그대로** 파일에 적고 정해진 답을 낸다.
#   `-e RESEED_PY` 로 받은 파이썬 본문과 표준입력(비밀번호)도 그대로 적는다(ⓖ).
cat > "$TMP/bin/docker" <<'STUB'
#!/usr/bin/env bash
if [ -n "${FIXTURE_SQL_OUT:-}" ] && [ -n "${SQL:-}" ]; then
  printf '%s' "$SQL" > "$FIXTURE_SQL_OUT"
fi
if [ -n "${FIXTURE_PY_OUT:-}" ] && [ -n "${RESEED_PY:-}" ]; then
  printf '%s' "$RESEED_PY" > "$FIXTURE_PY_OUT"
  cat > "$FIXTURE_PY_OUT.stdin"
fi
# `… IMAGE sh -c '<스크립트>'` 꼴이면 그 스크립트를 로컬 sh 로 실행한다(psql 대역이 argv 를 적는다 · ⓘ).
if [ -n "${FIXTURE_PSQL_ARGS:-}" ]; then
  prev=""
  for a in "$@"; do
    if [ "$prev" = "-c" ] && [ "${seen_sh:-0}" = 1 ]; then sh -c "$a"; break; fi
    [ "$a" = "sh" ] && seen_sh=1
    prev="$a"
  done
fi
printf '%s\n' "${FIXTURE_DOCKER_STDOUT:-0}"
if [ -n "${FIXTURE_DOCKER_STDERR:-}" ]; then printf '%s\n' "$FIXTURE_DOCKER_STDERR" >&2; fi
exit "${FIXTURE_DOCKER_RC:-0}"
STUB
# sudo 대역 = `VAR=값` 인자를 실물 sudo 처럼 환경으로 넘긴다(`-e VAR` 이름 전달이 성립하는 조건).
cat > "$TMP/bin/sudo" <<'STUB'
#!/usr/bin/env bash
while [ $# -gt 0 ]; do case "$1" in -E|-n) shift ;; *=*) export "$1"; shift ;; *) break ;; esac; done
exec "$@"
STUB
# psql 대역 = 받은 argv 를 탭으로 이어 한 줄 적는다(ⓘ 변수 꼴 대조용).
cat > "$TMP/bin/psql" <<'STUB'
#!/usr/bin/env bash
{ printf 'PSQL'; for a in "$@"; do printf '\t%s' "$a"; done; printf '\n'; } >> "${FIXTURE_PSQL_ARGS:-/dev/null}"
exit 0
STUB
cat > "$TMP/bin/agent-browser" <<'STUB'
#!/usr/bin/env bash
case "${1:-}" in
  open) printf '%s\n' "${FIXTURE_BROWSER_OPEN:-ok}" ;;
  get)  printf '%s\n' "${FIXTURE_BROWSER_TITLE-CoLAB}" ;;
  *)    printf 'ok\n' ;;
esac
exit 0
STUB
chmod +x "$TMP/bin"/*
export PATH="$TMP/bin:$PATH"

# ── 도구 적재 ────────────────────────────────────────────────────────────
# `reseed.sh` 가 정하는 값만 손으로 세운다 — 단계 본문은 실물 그대로 쓴다.
REPO_ROOT="$(cd "$RESEED_DIR/../../.." && pwd)"
RUN_DIR="$TMP/run"; mkdir -p "$RUN_DIR/logs" "$RUN_DIR/stages"
RUN_ID=19700101T000000Z
DRY_RUN=0
TARGET_SHA=deadbeefcafe
S3_BUCKET=colab-platform-data-dev
S3_REGION=ap-northeast-2
EC2_SECRETS_DIR=/etc/colab
LAB_ID=00000000000000000000HYMETS
RESEED_ACCOUNT_ID=000000000000000000HYMETSP1
RESEED_ACCOUNT_EMAIL='pi@hymets.invalid'
RESEED_ACCOUNT_NAME="오'브라이언"
RESEED_ACCOUNT_ROLE='교수'
DEV_URL='https://dev.invalid'
SEED_WORK_DIR="$TMP/seed-work"
BUILD_PLAN_PY="$TMP/build_plan_stub.py"
COLAB_DEV_SSH='ec2-user@<대역>'
COLAB_DEV_KEY_FILE="$TMP/no-such-key"
CURRENT_STAGE=reset
STAGE_LOG="$RUN_DIR/logs/reset.log"
export FIXTURE_SSH_LOG="$TMP/ssh.log"
export FIXTURE_COUNT_BEFORE="$HERE/fixtures/count-before-empty.json"
: > "$FIXTURE_SSH_LOG"
cat > "$BUILD_PLAN_PY" <<'STUB'
print("datasets 28 edges 18")
STUB

relpath() { printf '%s' "$1"; }

# shellcheck source=../lib.sh
. "$RESEED_DIR/lib.sh"
# shellcheck source=../stages.sh
. "$RESEED_DIR/stages.sh"
# Remote primitive isolation; deploy-rehearsal.sh covers the real release-plan boundary.
rehearse_release_plan() { return 0; }

reset_logs() { : > "$FIXTURE_SSH_LOG"; : > "$STAGE_LOG"; rm -f "$RUN_DIR/recovery.jsonl" "$RUN_DIR/blocked.jsonl"; }

# ── ⓐ 따옴표가 든 SQL 의 왕복 ─────────────────────────────────────────────
# 실물 `reset` ①″ 가 내는 문장 그대로 ＋ 셸이 싫어하는 글자를 더 얹는다.
SQL_HARD='select count(*) from pg_stat_activity where datname in ('"'"'colab_platform'"'"','"'"'colab_ai'"'"') and state <> '"'"'idle'"'"' and pid <> pg_backend_pid(); -- $HOME `id` "큰따옴표"'
reset_logs
export FIXTURE_EXEC=1 FIXTURE_SQL_OUT="$TMP/sql.out" FIXTURE_DOCKER_STDOUT=0
rm -f "$TMP/sql.out"
if psql_master_query "$SQL_HARD" 0; then :; else
  note "ⓐ 따옴표가 든 SQL 로 psql_master_query 가 비영 종료했다 — 원격 셸이 문장을 쪼갰다"
fi
if [ -f "$TMP/sql.out" ]; then
  got="$(cat "$TMP/sql.out")"
  [ "$got" = "$SQL_HARD" ] || note "ⓐ′ psql 에 닿은 SQL 이 원본과 다르다:
       보낸 것 [$SQL_HARD]
       받은 것 [$got]"
else
  note "ⓐ″ psql 이 SQL 을 한 글자도 받지 못했다 — 전송로가 서지 않았다"
fi
# 원격 스크립트 본문에 SQL 원문이 **노출되지 않는다**(base64 로 실린다).
grep -q "colab_platform" "$FIXTURE_SSH_LOG" \
  && note "ⓐ‴ 원격 스크립트 본문에 SQL 원문이 그대로 실렸다 — 따옴표 결함이 되살아날 자리다"

# ── ⓒ 실패 한 건이 로그에 한 번만 ─────────────────────────────────────────
reset_logs
got="$(psql_master_run "$SQL_HARD")"
[ "$got" = 0 ] || note "기계 질의 stdout에 RUN 진단이 섞였다"
reset_logs
export FIXTURE_DOCKER_STDOUT=UNIQUE_REMOTE_PAYLOAD
got="$(psql_master_run "$SQL_HARD")"
reh_re payload '^UNIQUE_REMOTE_' "$got" >/dev/null 2>&1
[ "$(grep -c UNIQUE_REMOTE_PAYLOAD "$STAGE_LOG")" = 1 ] || note "리허설이 저장된 응답을 다시 로그에 썼다"
[ "$(grep -c 'RUN ssh <dev>' "$STAGE_LOG")" = 1 ] || note "리허설이 RUN 진단을 다시 로그에 썼다"
export FIXTURE_DOCKER_RC=7
got="$(psql_master_run "$SQL_HARD")"; rc=$?
[ "$rc" = 7 ] || note "capture가 원격 실패 종료코드를 잃었다"
unset FIXTURE_DOCKER_RC
export FIXTURE_DOCKER_STDOUT=0
for FIXTURE_DOCTOR_RC in 0 7; do
  reset_logs
  export FIXTURE_DOCTOR_RC FIXTURE_DOCTOR_FILE="$HERE/fixtures/doctor-15-15.txt"
  doctor_once >/dev/null 2>&1; rc=$?
  [ "$rc" = "$FIXTURE_DOCTOR_RC" ] || note "doctor 종료코드 $FIXTURE_DOCTOR_RC 를 $rc 로 바꿨다"
  [ "$(grep -c '항목 15 — ✓ 15 · ✗ 0 · ─ 0' "$STAGE_LOG")" = 1 ] || note "doctor 요약을 두 번 기록했다"
done
unset FIXTURE_DOCTOR_FILE FIXTURE_DOCTOR_RC
echo "로그/capture 경계 5 건"

reset_logs
export FIXTURE_DOCKER_RC=1 FIXTURE_DOCKER_STDOUT="" \
  FIXTURE_DOCKER_STDERR='ERROR:  column "colab_platform" does not exist'
psql_master_query "$SQL_HARD" 0 >/dev/null 2>&1
n="$(grep -c 'does not exist' "$STAGE_LOG")"
[ "$n" = 1 ] || note "ⓒ 같은 오류 줄이 단계 로그에 $n 번 있다(기대 1) — 이중 기록"
unset FIXTURE_DOCKER_RC FIXTURE_DOCKER_STDERR
export FIXTURE_DOCKER_STDOUT=0

# ── ⓑ 정지 뒤 실패 → 자동 재기동 ─────────────────────────────────────────
reset_logs
export FIXTURE_EXEC=0 FIXTURE_FAIL_MATCH='--phase schema'
COLAB_RESEED_OPERATOR=fixture stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓑ 스키마 걸음이 실패했는데 stage_reset 이 0 으로 끝났다"
order="$(grep -oE 'stop core-api|start core-api|phase schema' "$FIXTURE_SSH_LOG" | tr '\n' '>')"
case "$order" in
  'stop core-api>phase schema>start core-api>') : ;;
  *) note "ⓑ′ 정지·DROP·재기동의 순서가 [$order] 다(기대 stop>phase schema>start) — 실패 경로에 역연산이 없다" ;;
esac
[ -s "$RUN_DIR/recovery.jsonl" ] || note "ⓑ″ recovery.jsonl 이 없다 — 되살린 사실이 결과에 남지 않는다"
grep -q '"action": *"apps-start"' "$RUN_DIR/recovery.jsonl" 2>/dev/null \
  || note "ⓑ‴ recovery.jsonl 에 apps-start 기록이 없다"
# 정지는 **되돌릴 수 없는 걸음 직전**에만 내린다 — 읽기 전용 계수가 정지보다 먼저다.
first="$(grep -oE 'phase count|stop core-api' "$FIXTURE_SSH_LOG" | head -1)"
case "$first" in
  'phase count') : ;;
  *) note "ⓑ⁗ 읽기 전용 계수보다 앱 정지가 먼저다: ${first:-<없음>}" ;;
esac
unset FIXTURE_FAIL_MATCH

# 정지 전 active/idle-in-transaction(둘 다 count=1), 미측정, 질의 실패는 stop/schema 0회.
for tx_case in active idle-in-transaction missing query-failed; do
  reset_logs
  export FIXTURE_TX_REPLY=1 FIXTURE_TX_RC=0
  case "$tx_case" in
    missing) FIXTURE_TX_REPLY=invalid ;;
    query-failed) FIXTURE_TX_REPLY=0; FIXTURE_TX_RC=7 ;;
  esac
  stage_reset >/dev/null 2>&1; rc=$?
  [ "$rc" -ne 0 ] || note "정지 전 $tx_case 를 통과시켰다"
  grep -qE 'stop core-api|phase schema|start core-api' "$FIXTURE_SSH_LOG" \
    && note "정지 전 $tx_case 에 앱/스키마 변경을 실행했다"
done
unset FIXTURE_TX_REPLY FIXTURE_TX_RC
reset_logs
stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" = 0 ] || note "정상 idle 계수 0을 거절했다"
grep -q 'phase schema' "$FIXTURE_SSH_LOG" || note "정상 idle에서 schema 단계에 도달하지 않았다"
reset_logs
export FIXTURE_TX_SEQUENCE="$TMP/tx-sequence"
echo 0 > "$FIXTURE_TX_SEQUENCE"
stage_reset >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "정지 후 활성 트랜잭션을 통과시켰다"
order="$(grep -oE 'stop core-api|start core-api|phase schema' "$FIXTURE_SSH_LOG" | tr '\n' '>')"
[ "$order" = 'stop core-api>start core-api>' ] || note "정지 후 판정 실패 복구 순서 [$order]"
[ -s "$RUN_DIR/recovery.jsonl" ] || note "정지 후 판정 실패 복구 기록 없음"
unset FIXTURE_TX_SEQUENCE
echo "reset 트랜잭션 경계 6 건"

# ── ⓓ 리허설 dry-run 은 원격에 한 바이트도 내지 않는다 ────────────────────
reset_logs
DRY_RUN=1
stage_rehearse >/dev/null 2>&1; rc=$?
DRY_RUN=0
[ "$rc" -eq 0 ] || note "ⓓ --dry-run 리허설이 비영 종료했다(rc=$rc)"
[ -s "$FIXTURE_SSH_LOG" ] && note "ⓓ′ --dry-run 리허설이 원격에 나갔다 — 아무것도 건드리지 않아야 한다"

# ── ⓔ 응답이 기대와 어긋나면 이름을 대고 비영 ─────────────────────────────
reset_logs
export FIXTURE_EXEC=0 FIXTURE_BROWSER_TITLE='' FIXTURE_DOCKER_STDOUT='엉뚱한 값'
out="$(stage_rehearse 2>&1)"; rc=$?
[ "$rc" -ne 0 ] || note "ⓔ 원시동작 응답이 어긋났는데 리허설이 0 으로 끝났다 — fail-open"
printf '%s' "$out" | grep -qE '✗ [a-zA-Z0-9:_.-]+' \
  || note "ⓔ′ 어긋난 원시동작의 **이름**이 출력에 없다: $(printf '%s' "$out" | tail -3 | tr '\n' ' ')"
unset FIXTURE_BROWSER_TITLE
export FIXTURE_DOCKER_STDOUT=0

# ── ⓕ `='<값>'` 한 겹 적재가 0건 ──────────────────────────────────────────
bad="$(grep -nE "(export [A-Za-z_]+|-e [A-Za-z_]+)='\\\$" "$RESEED_DIR/stages.sh" || true)"
[ -z "$bad" ] || note "ⓕ 값을 작은따옴표 한 겹으로 싣는 자리가 남아 있다:
$(printf '%s' "$bad" | sed 's/^/       /')"

# ── ⓖ prelude ③ — 본문은 환경변수 · 비밀번호는 표준입력 한 줄 ─────────────
# 원격 스크립트는 argv 로 가고 표준입력이 「파이썬 본문 ＋ __PW__ ＋ 비밀번호」다. ssh 대역이 그
# 스크립트를 로컬 bash 로 실제로 돌리므로 원격 셸의 갈라내기·sudo 환경 전달·docker 표준입력이 재현된다.
reset_logs
CURRENT_STAGE=prelude; STAGE_LOG="$RUN_DIR/logs/prelude.log"; : > "$STAGE_LOG"
PW_HARD="pw'quote\"dq \$HOME \`id\` 12345"            # 10자 이상 · 셸이 싫어하는 글자 전부
OPERATOR_PASSWORD_FILE="$TMP/pw.txt"
printf '%s\n' "$PW_HARD" > "$OPERATOR_PASSWORD_FILE"; chmod 600 "$OPERATOR_PASSWORD_FILE"
export FIXTURE_EXEC_CMD=1 FIXTURE_PY_OUT="$TMP/py.out" FIXTURE_DOCKER_STDOUT='login_credential 1행'
rm -f "$TMP/py.out" "$TMP/py.out.stdin"
if prelude_login_credential >/dev/null 2>&1; then :; else
  note "ⓖ prelude_login_credential 이 비영 종료했다 — 원격 스크립트가 로컬 bash 에서 죽었다"
fi
if [ -f "$TMP/py.out" ]; then
  grep -q 'INSERT INTO account_admin.login_credential' "$TMP/py.out" \
    || note "ⓖ′ 컨테이너가 받은 파이썬 본문에 login_credential INSERT 가 없다"
  got_pw="$(cat "$TMP/py.out.stdin" 2>/dev/null)"
  [ "$got_pw" = "$PW_HARD" ] || note "ⓖ″ 컨테이너 표준입력의 비밀번호가 원본과 다르다:
       보낸 것 [$PW_HARD]
       받은 것 [$got_pw]"
else
  note "ⓖ‴ 컨테이너가 파이썬 본문을 받지 못했다 — RESEED_PY 가 docker 에 닿지 않았다"
fi
grep -qF "$PW_HARD" "$FIXTURE_SSH_LOG" && note "ⓖ⁗ 비밀번호가 원격 스크립트(argv)에 실렸다"
grep -qF "$PW_HARD" "$STAGE_LOG" && note "ⓖ⁗′ 비밀번호가 단계 로그에 남았다"
# 주석을 걷어낸 뒤 잰다 — 정적 대조가 주석을 코드로 읽는 오탐을 막는다(`CLAUDE.md §5-b`).
grep -vE '^[[:space:]]*#' "$RESEED_DIR/stages.sh" | grep -q 'docker cp' \
  && note "ⓖ⁗″ 컨테이너 안에 파일을 두는 자리(docker cp)가 stages.sh 에 남아 있다 — 소유자 결함이 되살아날 자리다"
# ── ⓗ 받은 본문을 실제로 실행한다 — 바인드 이름 ↔ `as_dict()` 키 ────────────
# `password.py` 는 실물을 경로로 싣는다(표준 라이브러리만 쓴다). `db_credentials.py` 는 `sqlalchemy.orm`
# 을 끌어와 여기서 못 싣으므로 `normalize_login_name` 만 실물 축자(`strip().lower()`)로 대역한다.
if [ -f "$TMP/py.out" ]; then
  cat > "$TMP/run_body.py" <<'PYRUN'
import sys, os, re, types, importlib.util, contextlib
body_path, password_py = sys.argv[1], sys.argv[2]
sa = types.ModuleType("sqlalchemy")
class _Text:
    def __init__(self, s): self.s = s
class _Conn:
    def execute(self, stmt, params=None):
        names = re.findall(r"(?<![:\w]):([A-Za-z_]\w*)", stmt.s)
        params = params or {}
        missing = [n for n in names if n not in params]
        if missing:
            raise RuntimeError("A value is required for bind parameter %r" % missing[0])
        if "INSERT INTO account_admin.login_credential" in stmt.s:
            cols = [c.strip() for c in re.search(r"\((.*?)\)\s*VALUES", stmt.s, re.S).group(1).split(",") if c.strip()]
            if len(cols) != len(names):
                raise RuntimeError("열 %d · 바인드 %d" % (len(cols), len(names)))
            for k in ("account_id", "login_name"):
                if not params[k]:
                    raise RuntimeError("빈 값 %s" % k)
            print("INSERT account_admin.login_credential ok · 열 %d · login_name=%s" % (len(cols), params["login_name"]))
        return types.SimpleNamespace(rowcount=1)
class _Engine:
    @contextlib.contextmanager
    def begin(self):
        yield _Conn()
sa.text = lambda s: _Text(s)
sa.create_engine = lambda url: _Engine()
sys.modules["sqlalchemy"] = sa
spec = importlib.util.spec_from_file_location("colab_core.kernel.password", password_py)
pw_mod = importlib.util.module_from_spec(spec)
sys.modules["colab_core.kernel.password"] = pw_mod   # dataclass 가 sys.modules[__module__] 을 본다
spec.loader.exec_module(pw_mod)
pkg = types.ModuleType("colab_core"); kern = types.ModuleType("colab_core.kernel")
dbc = types.ModuleType("colab_core.kernel.db_credentials")
dbc.normalize_login_name = lambda v: v.strip().lower()
sys.modules.update({"colab_core": pkg, "colab_core.kernel": kern,
                    "colab_core.kernel.password": pw_mod, "colab_core.kernel.db_credentials": dbc})
exec(compile(open(body_path).read(), "<reseed-body>", "exec"), {"__name__": "__main__"})
PYRUN
  printf 'postgresql+psycopg://x:y@db-dev.invalid/colab_platform\n' > "$TMP/url"
  if printf '%s\n' "$PW_HARD" \
      | RESEED_ACCOUNT_ID="$RESEED_ACCOUNT_ID" RESEED_ACCOUNT_EMAIL=' PI@Hymets.invalid ' \
        COLAB_CORE_ACCOUNT_ADMIN_DATABASE_URL_FILE="$TMP/url" \
        python3 "$TMP/run_body.py" "$TMP/py.out" \
        "$REPO_ROOT/services/core-api/src/colab_core/kernel/password.py" > "$TMP/body.out" 2>&1; then
    grep -q 'INSERT account_admin.login_credential ok · 열 8 · login_name=pi@hymets.invalid' "$TMP/body.out" \
      || note "ⓗ′ 본문이 login_credential INSERT 를 8열·정규화된 login_name 으로 내지 않았다: $(tail -1 "$TMP/body.out")"
  else
    note "ⓗ 컨테이너가 받은 파이썬 본문이 실행에서 죽었다: $(grep -E 'Error|error' "$TMP/body.out" | tail -1)"
  fi
fi

# 컨테이너가 비영이면 prelude ③ 도 비영이다(fail-closed).
export FIXTURE_DOCKER_RC=1
prelude_login_credential >/dev/null 2>&1 \
  && note "ⓖ⁗‴ 컨테이너 python 이 비영인데 prelude_login_credential 이 0 으로 끝났다 — fail-open"
unset FIXTURE_DOCKER_RC FIXTURE_EXEC_CMD FIXTURE_PY_OUT
export FIXTURE_DOCKER_STDOUT=0

# ── ⓘ prelude ②④ — psql 변수 값의 꼴은 SQL 파일이 정한다 ─────────────────
# `:'name'` 은 psql 이 따옴표를 씌우므로 **원문**을, 맨 `:name` 은 SQL 리터럴 자리라 **감싼 값**을 넘겨야 한다.
# stage_prelude 전체를 대역 위에서 돌리고(② 는 id 를 다르게 두어 돌린다) psql 대역이 적은 argv 를
# 실물 SQL 파일의 변수 꼴과 대조한다. 왜 = 4회차 재개 2(`20260914T023537Z`)가 ④ 에 감싼 값을 넘겨
# `'''<id>'''` 로 조회했고 `INSERT 0 0` 으로 멈췄다. 그 줄도 실모드로 돈 적이 없었다.
reset_logs
CURRENT_STAGE=prelude; STAGE_LOG="$RUN_DIR/logs/prelude.log"; : > "$STAGE_LOG"
DEV_REPO_DIR=/opt/colab-repo; PSQL_IMAGE=postgres:16-alpine
ACCOUNTS_FILE="$TMP/approved-profile.json"
cp "$RESEED_DIR/accounts-profile.example.json" "$ACCOUNTS_FILE"
chmod 600 "$ACCOUNTS_FILE"
export COLAB_RESEED_ACCOUNTS_PROFILE="$ACCOUNTS_FILE"
PROVISION_LAB_SQL="$REPO_ROOT/infra/staging/provision-lab.sql"
PROVISION_LAB_ACCOUNT_ID=000000000000000000HYMETSP9     # ≠ RESEED_ACCOUNT_ID → ② 가 돈다
export FIXTURE_EXEC=1 FIXTURE_EXEC_CMD=1 FIXTURE_PSQL_ARGS="$TMP/psql.args"
: > "$FIXTURE_PSQL_ARGS"
if stage_prelude >/dev/null 2>&1; then :; else
  note "ⓘ stage_prelude 가 대역 위에서 비영 종료했다: $(tail -2 "$STAGE_LOG" | tr '\n' ' ')"
fi
unset FIXTURE_EXEC_CMD FIXTURE_PSQL_ARGS
export FIXTURE_EXEC=0
cat > "$TMP/check_psql.py" <<'PYCHK'
import re, sys
args_path, repo, lab_id, account_id = sys.argv[1:5]
files = {"lab.sql": "infra/staging/provision-lab.sql",
         "acct.sql": "services/core-api/ops/provision-account.sql",
         "op.sql": "services/core-api/ops/provision-service-operator.sql"}
seen = set(); bad = []
for line in open(args_path, encoding="utf-8"):
    if not line.startswith("PSQL\t"): continue
    argv = line.rstrip("\n").split("\t")[1:]
    f = argv[argv.index("-f") + 1] if "-f" in argv else ""
    base = f.rsplit("/", 1)[-1]
    if base not in files: bad.append("알 수 없는 SQL 파일 %r" % f); continue
    seen.add(base)
    sql = open("%s/%s" % (repo, files[base]), encoding="utf-8").read()
    sql_code = "\n".join(l for l in sql.splitlines() if not l.lstrip().startswith("--"))
    pairs =[(argv[i + 1]) for i, a in enumerate(argv) if a == "-v" and i + 1 < len(argv)]
    for pair in pairs:
        name, _, value = pair.partition("=")
        if name == "ON_ERROR_STOP": continue
        quoted_style = re.search(r":'%s'" % re.escape(name), sql_code) is not None
        bare_style = re.search(r"(?<![:'\w]):%s\b" % re.escape(name), sql_code) is not None
        if quoted_style and value.startswith("'"):
            bad.append("%s :'%s' 는 psql 이 따옴표를 씌우는데 감싼 값 %r 을 넘겼다" % (base, name, value))
        if bare_style and not quoted_style and not (len(value) >= 2 and value[0] == "'" and value[-1] == "'"):
            bad.append("%s :%s 는 SQL 리터럴 자리인데 감싸지 않은 값 %r 을 넘겼다" % (base, name, value))
        if not quoted_style and not bare_style:
            bad.append("%s 에 없는 변수 %s 를 넘겼다" % (base, name))
    if base == "op.sql":
        c = argv[argv.index("-c") + 1] if "-c" in argv else ""
        if c != "SET app.current_lab = '%s'" % lab_id:
            bad.append("op.sql 의 경계 SET 이 기대와 다르다: %r" % c)
        acct = dict(p.partition("=")[::2] for p in pairs).get("account_id")
        if acct != account_id:
            bad.append("op.sql account_id 가 원문 %r 이 아니다: %r" % (account_id, acct))
    if base == "acct.sql":
        name_v = dict(p.partition("=")[::2] for p in pairs).get("name")
        if name_v != "'오''브라이언'":
            bad.append("acct.sql name 의 SQL 겹따옴표 규칙이 깨졌다: %r" % name_v)
for want in ("lab.sql", "acct.sql", "op.sql"):
    if want not in seen: bad.append("psql 호출에 %s 가 없다 — 그 걸음이 돌지 않았다" % want)
for b in bad: print("  ✗ ⓘ′ " + b)
sys.exit(1 if bad else 0)
PYCHK
if ! python3 "$TMP/check_psql.py" "$TMP/psql.args" "$REPO_ROOT" "$LAB_ID" "$RESEED_ACCOUNT_ID"; then
  fail=1
fi
unset PROVISION_LAB_ACCOUNT_ID

if [ "$fail" -eq 0 ]; then
  echo "remote-transport — green (따옴표 SQL 왕복 · 실패 후 자동 재기동 · 오류 1회 기록 · 리허설 dry-run 무접촉 · 리허설 fail-closed · 한겹 적재 0 · prelude ③ 환경변수·표준입력 왕복 · 본문 실행 바인드 대조 · ②④ psql 변수 꼴)"
  exit 0
fi
echo "remote-transport — red" >&2
exit 1
