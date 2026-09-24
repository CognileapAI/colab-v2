#!/usr/bin/env bash
# 임시 운영자 **창(窓)** 픽스처 — 운영자 자격이 켜져 있는 구간을 판정한다.
#
# 무엇을 증명하는가 =
#   ⓐ `stage_seed` 가 `accounts` 국면을 마친 **직후** 임시 운영자를 내리고, 그 다음에야
#      `projects`·`datasets`·`verify`·`report` 국면을 돈다.
#   ⓐ′ 그 해제와 `projects` 사이에 **재로그인**이 있다. 자격이 바뀐 세션은 제품이 거절한다
#      (`kernel/session_token.py:59-61` · `kernel/login_sessions.py:192-206`) — 어떤 길로 내리든
#      열린 세션은 닫힌다. 2026-09-24 재개 1 이 이 자리에서 로그인 화면을 보고 멈췄다.
#   ⓑ `account_finalize` 가 `accounts.py finalize` 를 부르기 **전에** 자격을 되올린다.
#      되올리지 않으면 `accounts.py` 의 「final professor credential drift」 가 나서
#      교수 비밀번호를 초기값으로 되돌리지 못한다.
#   ⓒ 내리는 SQL 은 **그 계정 한 행만** 지우고, 한 트랜잭션(`-1`)으로 돌며,
#      운영자가 한 명도 남지 않으면 **거절**한다.
#   ⓓ 올리는 길은 `provision-service-operator.sql` 그대로다(문장을 두 벌 두지 않는다).
#
# 왜 필요한가 = 2026-09-24 재시드의 `seed` 가 첫 프로젝트 생성에서
#   「대상 연구실을 선택해 주세요.」(`app/target_scope.py:43`)로 멈췄다. 그 요구는
#   **주체가 운영자일 때만** 선다(`target_scope.py:31-34`). 러너는 그 칸을 채우지 않으므로
#   창을 `accounts` 국면으로 좁혀야 한다. 이 순서는 어느 검사에도 걸리지 않았다.
#
# dev·AWS 무접촉 = `ssh_script`·`run`·`python3` 를 전부 대역으로 가린다. 한 바이트도 나가지 않는다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
TRACE="$WORK/trace.txt"; : > "$TRACE"
BODIES="$WORK/bodies"; mkdir -p "$BODIES"

DRY_RUN=0
RUN_DIR="$WORK/run"
STAGE_LOG=/dev/null
mkdir -p "$RUN_DIR"
# shellcheck source=../lib.sh
. "$HERE/../lib.sh"
# shellcheck source=../stages.sh
. "$HERE/../stages.sh"

# ── 대역 ─────────────────────────────────────────────────────────────────
log() { :; }
warn() { :; }
run() { printf 'RUN %s\n' "$*" >> "$TRACE"; return 0; }
run_capture() { printf 'CAP %s\n' "$*" >> "$TRACE"; return 0; }
ssh_script() {
  local label="$1" body
  body="$(cat)"
  printf 'SSH %s\n' "$label" >> "$TRACE"
  printf '%s\n' "$body" > "$BODIES/$label.txt"
  return 0
}
# `account_finalize` 는 `accounts.py check-details` 를 되받는 자리에서 직접 부른다.
python3() {
  printf 'PY %s\n' "$*" >> "$TRACE"
  printf '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef\n'
  return 0
}

# ── 값 ───────────────────────────────────────────────────────────────────
REPO_ROOT="$HERE/../../../.."
RESEED_DIR="$HERE/.."
BUILD_PLAN_PY="$RESEED_DIR/build-plan.py"
SEED_WORK_DIR="$WORK/seed"
ACCOUNTS_WORK_DIR="$WORK/accounts"
ACCOUNTS_FILE="$WORK/accounts-profile.json"
DEV_URL="https://dev.invalid"
AB_SESSION="colab-dev"
RESEED_ACCOUNT_EMAIL="professor@example.invalid"
RESEED_ACCOUNT_ID="000000000000000000HYMETSP1"
LAB_ID="00000000000000000000HYMETS"
TARGET_SHA="0123456789ab"
EC2_SECRETS_DIR="/etc/colab/secrets"
DEV_REPO_DIR="/opt/colab-repo"
PSQL_IMAGE="postgres:16-alpine"
COLAB_DEV_SSH="dev@invalid"
COLAB_DEV_KEY_FILE="/dev/null"
mkdir -p "$SEED_WORK_DIR" "$ACCOUNTS_WORK_DIR"

fail=0
note() { echo "  ✗ $1"; fail=1; }
# 자취에서 그 줄이 몇 번째인지 — 없으면 빈 값.
idx() { grep -n -e "$1" "$TRACE" 2>/dev/null | head -1 | cut -d: -f1; }

# ── ⓐ seed 국면 순서 ─────────────────────────────────────────────────────
stage_seed >/dev/null 2>&1
i_check="$(idx 'check-created')"
i_revoke="$(idx 'seed:operator-revoke')"
i_projects="$(idx '\-\-phase projects')"
i_accounts="$(idx '\-\-phase accounts')"
[ -n "$i_accounts" ] || note 'ⓐ 자취에 accounts 국면이 없다'
[ -n "$i_check" ] || note 'ⓐ 자취에 check-created 가 없다'
[ -n "$i_projects" ] || note 'ⓐ 자취에 projects 국면이 없다'
[ -n "$i_revoke" ] || note 'ⓐ seed 국면이 임시 운영자를 내리지 않는다 — 대상 연구실 헤더 요구에 걸린다'
if [ -n "$i_revoke" ] && [ -n "$i_check" ] && [ -n "$i_projects" ]; then
  [ "$i_revoke" -gt "$i_check" ] \
    || note 'ⓐ accounts 국면보다 먼저 내렸다 — 무소속 운영자 넷을 만들 수 없다'
  [ "$i_revoke" -lt "$i_projects" ] \
    || note 'ⓐ projects 국면이 운영자 자격을 켠 채 돈다'
  # ⓐ′ 해제 **뒤** 첫 login 국면이 projects 앞에 와야 한다.
  i_relogin="$(grep -n -e '\-\-phase login' "$TRACE" | cut -d: -f1 \
               | awk -v r="$i_revoke" '$1 > r { print; exit }')"
  if [ -z "$i_relogin" ] || [ "$i_relogin" -gt "$i_projects" ]; then
    note "ⓐ′ 해제 뒤 재로그인이 없다 — 자격이 바뀐 세션은 거절되므로 projects 가 로그인 화면을 본다"
  fi
fi

# ── ⓑ 최종화 직전 되올림 ─────────────────────────────────────────────────
: > "$TRACE"
account_finalize >/dev/null 2>&1
i_grant="$(idx 'operator-grant')"
i_final="$(idx 'accounts.py finalize')"
[ -n "$i_grant" ] || note 'ⓑ 계정 최종화 전에 임시 운영자를 되올리지 않는다 — 교수 비밀번호를 되돌리지 못한다'
[ -n "$i_final" ] || note 'ⓑ 자취에 accounts.py finalize 가 없다'
if [ -n "$i_grant" ] && [ -n "$i_final" ]; then
  [ "$i_grant" -lt "$i_final" ] || note 'ⓑ 되올림이 accounts.py finalize 뒤에 온다'
fi

# ── ⓒ 내리는 SQL ─────────────────────────────────────────────────────────
body_revoke="$BODIES/seed:operator-revoke.txt"
if [ -f "$body_revoke" ]; then
  grep -q 'psql -1' "$body_revoke" \
    || note 'ⓒ 한 트랜잭션(-1)이 아니다 — 거절이 DELETE 를 되돌리지 못한다'
  # 값은 base64 로 실려 원격 셸에 따옴표·개행이 노출되지 않는다(`lib.sh` `remote_assign`).
  # 그러므로 **실린 것을 되돌려** 판정한다 — 원격 셸이 실제로 psql 에 넣는 본문이다.
  sql_revoke="$(sed -n 's/^REVOKE_SQL=$(printf %s \(.*\) | base64 -d)$/\1/p' "$body_revoke" | base64 -d 2>/dev/null)"
  if [ -z "$sql_revoke" ]; then
    note 'ⓒ 내리는 SQL 이 base64 대입문으로 실려 있지 않다 — 따옴표가 원격 셸에 노출된다'
  else
    printf '%s' "$sql_revoke" | grep -q 'account_admin.service_operator' \
      || note 'ⓒ 내리는 문장이 account_admin.service_operator 를 건드리지 않는다'
    printf '%s' "$sql_revoke" | grep -q "DELETE FROM account_admin.service_operator WHERE account_id=:'account_id'" \
      || note 'ⓒ 지우는 자리가 그 계정 한 행으로 좁혀져 있지 않다'
    printf '%s' "$sql_revoke" | grep -q 'NOT EXISTS (SELECT 1 FROM account_admin.service_operator)' \
      || note 'ⓒ 운영자가 한 명도 남지 않는 경우를 거절하지 않는다'
  fi
  if grep -q 'set_operator\|login_session' "$body_revoke"; then
    note 'ⓒ 제품 세션을 끊는 경로를 탄다 — 러너의 로그인이 그 자리에서 죽는다'
  fi
else
  note 'ⓒ 내리는 원격 본문이 없다'
fi

# ── ⓓ 올리는 길은 한 벌 ──────────────────────────────────────────────────
body_grant="$BODIES/verify:operator-grant.txt"
if [ -f "$body_grant" ]; then
  grep -q 'provision-service-operator.sql' "$body_grant" \
    || note 'ⓓ 되올림이 provision-service-operator.sql 을 쓰지 않는다 — 문장이 두 벌이 된다'
else
  note 'ⓓ 되올리는 원격 본문이 없다'
fi

if [ "$fail" -eq 0 ]; then
  echo "operator-window — green (accounts 뒤 해제 · projects 앞 · 최종화 전 복원 · 한 행·한 트랜잭션·마지막 한 명 거절)"
  exit 0
fi
echo "operator-window — red" >&2
exit 1
