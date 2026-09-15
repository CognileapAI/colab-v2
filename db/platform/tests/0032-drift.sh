#!/usr/bin/env bash
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; CHAIN="$(cd "$HERE/.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"; IMAGE="${COLAB_PG_IMAGE:-postgres:16-alpine}"
red(){ echo "::error::0032-drift red — $*"; exit 1; }
ready(){ echo "::error::0032-drift red(준비) — $*"; exit 78; }
command -v docker >/dev/null || ready "docker가 없다"
command -v "$ALEMBIC" >/dev/null || [ -x "$ALEMBIC" ] || ready "alembic이 없다"
TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" colab-0032-XXXXXX)"; PGC=""
cleanup(){ [ -z "$PGC" ] || docker rm -f "$PGC" >/dev/null 2>&1; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM
export COLAB_PLATFORM_DB_URL=postgresql+psycopg://offline/offline
render(){ (cd "$CHAIN" && "$ALEMBIC" $1 --sql) >"$2" 2>"$TMP/err" || red "render $1"; }
render "upgrade 0032_labless_operator" "$TMP/head.sql"
render "upgrade 0031_search_evidence" "$TMP/prev.sql"
render "downgrade 0032_labless_operator:0031_search_evidence" "$TMP/down.sql"
docker image inspect "$IMAGE" >/dev/null 2>&1 || ready "postgres 이미지가 없다"
PGC="colab_0032_$$_${RANDOM}"
docker run -d --rm --name "$PGC" --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=x -e POSTGRES_HOST_AUTH_METHOD=trust "$IMAGE" >/dev/null || ready "postgres 기동 실패"
for _ in $(seq 1 60); do docker exec "$PGC" pg_isready -U postgres -q && break; sleep 1; done
apply(){ docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" <"$2"; }
for db in head prev down; do docker exec "$PGC" createdb -U postgres "$db" >/dev/null; done
apply head "$TMP/head.sql" || red "head 적용 실패"
apply head "$HERE/0032-assertions.sql" || red "head oracle 실패"
if apply head "$TMP/down.sql" >/dev/null 2>&1; then red "NULL 계정이 있는데 downgrade가 통과했다"; fi
docker exec "$PGC" psql -Atq -U postgres -d head -c \
  "SELECT count(*) FROM d1_account WHERE id='00000000000000000000000N32' AND lab_id IS NULL" \
  | grep -qx 1 || red "downgrade 거부 뒤 NULL 계정 데이터가 사라졌다"
apply prev "$TMP/prev.sql" || red "prev 적용 실패"
if apply prev "$HERE/0032-assertions.sql" >/dev/null 2>&1; then red "previous가 oracle을 통과했다"; fi
apply down "$TMP/head.sql" || red "down head 적용 실패"
apply down "$TMP/down.sql" || red "빈 DB downgrade 실패"
if apply down "$HERE/0032-assertions.sql" >/dev/null 2>&1; then red "downgrade가 oracle을 통과했다"; fi
echo "0032-drift green — nullable affiliation and downgrade boundary."
