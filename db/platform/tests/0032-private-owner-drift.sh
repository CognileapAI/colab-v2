#!/usr/bin/env bash
# In-place 0033 -> 0032_private_owner_access -> 0033, populated data, real non-owner app role.
#
# 왜 있나 (2026-09-18 develop 동기화): `0032_private_owner_access` 는 두 브랜치의 head 가
# 갈렸을 때 **`0033_admin_body_access` 뒤로 옮겨 붙인** 리비전이다. 옮기면서 그 본문을
# 「관리자 갈래를 보존한 채 소유자 갈래를 덧붙이는 ALTER POLICY」로 다시 썼다. 그 재작성이
# 실제로 **관리자 갈래를 살려 두는지** 재는 자리가 없으면, 소유자 갈래를 넣으면서 관리자
# 갈래를 지우는 회귀가 조용히 지나간다 — `body_access` 는 정책 하나이기 때문이다.
#
# 판정: 소유자 read/write 가 0 → 1 로 열리고, 관리자·외랩·연구실 경계는 **두 상태 모두 불변**,
#       저장된 자료는 upgrade·downgrade 어느 쪽에서도 바뀌지 않는다.
set -uo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../../../gates/tools/_pg.sh"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN="$(cd "$HERE/.." && pwd)"
ROOT="$(cd "$CHAIN/../.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
red(){ echo "::error::0032-private-owner-drift red — $*"; exit 1; }
ready(){ echo "::error::0032-private-owner-drift red(준비) — $*"; exit 78; }
command -v "$ALEMBIC" >/dev/null || [ -x "$ALEMBIC" ] || ready "alembic이 없다"
TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" colab-0032po-XXXXXX)"
cleanup(){ pg_cleanup; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM
export COLAB_PLATFORM_DB_URL=postgresql+psycopg://offline/offline
render(){ (cd "$CHAIN" && "$ALEMBIC" $1 --sql) >"$2" 2>"$TMP/err" || red "render $1"; }
render 'upgrade 0033_admin_body_access' "$TMP/prev.sql"
render 'upgrade 0033_admin_body_access:0032_private_owner_access' "$TMP/up.sql"
render 'downgrade 0032_private_owner_access:0033_admin_body_access' "$TMP/down.sql"
pg_start 0032-private-owner-drift || exit 78
# pg_start installs its own trap; keep both the shared PG cleanup and this scratch directory.
trap cleanup EXIT INT TERM
docker exec "$PGC" createdb -U postgres migration0032po >/dev/null || red "DB 생성 실패"
su_psql(){ docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d migration0032po "$@"; }
app_psql(){ docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U colab_app -d migration0032po "$@"; }
su_psql < "$TMP/prev.sql" >"$TMP/err" 2>&1 || red "0033 적용 실패"
su_psql -v owner=postgres -v app=colab_app -v app_password=gateapp \
  < "$ROOT/services/core-api/ops/app-role.sql" >"$TMP/err" 2>&1 || red "앱 롤 준비 실패"
su_psql < "$ROOT/services/core-api/tests/fixtures/seed.sql" >"$TMP/err" 2>&1 || red "기존 자료 시드 실패"
su_psql < "$HERE/0032-private-owner-fixture.sql" >"$TMP/err" 2>&1 || red "소유자 판정용 자료 준비 실패"
snapshot(){
  docker exec "$PGC" pg_dump -U postgres -d migration0032po --data-only --no-owner --no-privileges \
    --exclude-table-data=alembic_version_platform >"$TMP/raw" 2>"$TMP/err" || return 1
  sed '/^\\restrict /d; /^\\unrestrict /d' "$TMP/raw" >"$1"
}
check(){ app_psql -v owner_expected="$1" < "$HERE/0032-private-owner-assertions.sql" >"$TMP/oracle" 2>&1; }
snapshot "$TMP/before" || red "기존 자료 snapshot 실패"
check 0 || { cat "$TMP/oracle"; red "0033 에서 소유자 음성·관리자 양성 전제가 서지 않는다"; }
if check 1; then red "0033 에서 소유자 예외 oracle 이 이미 통과했다 — 이 회차가 재는 것이 없다"; fi
su_psql < "$TMP/up.sql" >"$TMP/err" 2>&1 || red "0032_private_owner_access 증분 upgrade 실패"
check 1 || { cat "$TMP/oracle"; red "소유자 본체 read/write 또는 관리자·경계 불변이 깨졌다"; }
if check 0; then red "upgrade 뒤에도 소유자가 막혀 있다"; fi
snapshot "$TMP/up-data" || red "upgrade 자료 snapshot 실패"
cmp -s "$TMP/before" "$TMP/up-data" || red "upgrade 가 기존 자료를 바꿨다"
su_psql < "$TMP/down.sql" >"$TMP/err" 2>&1 || red "0033 downgrade 실패"
check 0 || { cat "$TMP/oracle"; red "downgrade 뒤 0033 상태가 복원되지 않았다"; }
if check 1; then red "downgrade 뒤에도 소유자 예외가 남았다"; fi
snapshot "$TMP/down-data" || red "downgrade 자료 snapshot 실패"
cmp -s "$TMP/before" "$TMP/down-data" || red "downgrade 가 기존 자료를 바꿨다"
echo '0032-private-owner-drift green — populated 0033 to 0032_private_owner_access and back; owner read/write opens and closes, manager/foreign/lab boundaries unchanged, stored data unchanged.'
