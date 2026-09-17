#!/usr/bin/env bash
# In-place 0032 -> 0033 -> 0032, using populated data and the real non-owner app role.
set -uo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../../../gates/tools/_pg.sh"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN="$(cd "$HERE/.." && pwd)"
ROOT="$(cd "$CHAIN/../.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
red(){ echo "::error::0033-drift red — $*"; exit 1; }
ready(){ echo "::error::0033-drift red(준비) — $*"; exit 78; }
command -v "$ALEMBIC" >/dev/null || [ -x "$ALEMBIC" ] || ready "alembic이 없다"
TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" colab-0033-XXXXXX)"
cleanup(){ pg_cleanup; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM
export COLAB_PLATFORM_DB_URL=postgresql+psycopg://offline/offline
render(){ (cd "$CHAIN" && "$ALEMBIC" $1 --sql) >"$2" 2>"$TMP/err" || red "render $1"; }
render 'upgrade 0032_labless_operator' "$TMP/prev.sql"
render 'upgrade 0032_labless_operator:0033_admin_body_access' "$TMP/up.sql"
render 'downgrade 0033_admin_body_access:0032_labless_operator' "$TMP/down.sql"
pg_start 0033-drift || exit 78
# pg_start installs its own trap; keep both the shared PG cleanup and this scratch directory.
trap cleanup EXIT INT TERM
docker exec "$PGC" createdb -U postgres migration0033 >/dev/null || red "DB 생성 실패"
su_psql(){ docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d migration0033 "$@"; }
app_psql(){ docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U colab_app -d migration0033 "$@"; }
su_psql < "$TMP/prev.sql" >"$TMP/err" 2>&1 || red "0032 적용 실패"
su_psql -v owner=postgres -v app=colab_app -v app_password=gateapp \
  < "$ROOT/services/core-api/ops/app-role.sql" >"$TMP/err" 2>&1 || red "앱 롤 준비 실패"
su_psql < "$ROOT/services/core-api/tests/fixtures/seed.sql" >"$TMP/err" 2>&1 || red "기존 자료 시드 실패"
snapshot(){
  docker exec "$PGC" pg_dump -U postgres -d migration0033 --data-only --no-owner --no-privileges \
    --exclude-table-data=alembic_version_platform >"$TMP/raw" 2>"$TMP/err" || return 1
  sed '/^\\restrict /d; /^\\unrestrict /d' "$TMP/raw" >"$1"
}
check(){ app_psql -v manager_expected="$1" < "$HERE/0033-assertions.sql" >"$TMP/oracle" 2>&1; }
snapshot "$TMP/before" || red "기존 자료 snapshot 실패"
check 0 || red "0032 기존 일반/교수 경계 실패"
if check 1; then red "0032에서 새 관리자 예외 oracle이 통과했다"; fi
su_psql < "$TMP/up.sql" >"$TMP/err" 2>&1 || red "0033 증분 upgrade 실패"
check 1 || { cat "$TMP/oracle"; red "0033 관리자 본체 read/write 또는 일반 경계 실패"; }
snapshot "$TMP/up-data" || red "upgrade 자료 snapshot 실패"
cmp -s "$TMP/before" "$TMP/up-data" || red "upgrade가 기존 자료를 바꿨다"
su_psql < "$TMP/down.sql" >"$TMP/err" 2>&1 || red "0032 downgrade 실패"
check 0 || red "downgrade 후 기존 경계가 복원되지 않았다"
if check 1; then red "downgrade 후 새 관리자 예외가 남았다"; fi
snapshot "$TMP/down-data" || red "downgrade 자료 snapshot 실패"
cmp -s "$TMP/before" "$TMP/down-data" || red "downgrade가 기존 자료를 바꿨다"
echo '0033-drift green — populated 0032→0033→0032; all stored data unchanged; professor/system read+write, ordinary/foreign boundaries and previous/down negative controls.'
