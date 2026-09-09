#!/usr/bin/env bash
# 0023 드리프트 — head green, 0022와 downgrade는 red, downgrade shape는 0022와 동일.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN_DIR="$(cd "$HERE/.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
PG_IMAGE="${COLAB_PG_IMAGE:-postgres:16-alpine}"
HEAD_REV="0023_upv_image_grid"
PREV_REV="0022_rc7_variable_mirror_stmt"
red(){ echo "::error::0023-drift red — $*"; exit 1; }
unready(){ echo "::error::0023-drift red(준비) — $*"; exit 78; }
command -v docker >/dev/null 2>&1 || unready "docker가 없다"
command -v "$ALEMBIC" >/dev/null 2>&1 || [ -x "$ALEMBIC" ] || unready "alembic이 없다"
[ -f "$HERE/0023-assertions.sql" ] || unready "오라클 파일이 없다"
TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" colab-0023-XXXXXX)"; PGC=""
cleanup(){ [ -z "$PGC" ] || docker rm -f "$PGC" >/dev/null 2>&1; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM
export COLAB_PLATFORM_DB_URL="postgresql+psycopg://offline/offline"
render(){ (cd "$CHAIN_DIR" && "$ALEMBIC" $1 --sql) >"$2" 2>"$TMP/err" || red "alembic 렌더 실패: $1"; }
render "upgrade $HEAD_REV" "$TMP/head.sql"
render "upgrade $PREV_REV" "$TMP/prev.sql"
render "downgrade $HEAD_REV:$PREV_REV" "$TMP/down.sql"
render "upgrade $PREV_REV:$HEAD_REV" "$TMP/delta.sql"
for token in human_grid_description d3_dataset_representative_image d3_representative_image_cleanup 'FORCE ROW LEVEL SECURITY' 'ON DELETE CASCADE'; do
  grep -q "$token" "$TMP/delta.sql" || red "delta에 $token 이 없다"
done
docker image inspect "$PG_IMAGE" >/dev/null 2>&1 || docker pull -q "$PG_IMAGE" >/dev/null 2>&1 || unready "postgres 이미지가 없다"
PGC="colab_0023_$$_${RANDOM}"
docker run -d --rm --name "$PGC" --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
 -e POSTGRES_PASSWORD=x -e POSTGRES_HOST_AUTH_METHOD=trust "$PG_IMAGE" >/dev/null || unready "postgres 기동 실패"
for _ in $(seq 1 60); do docker exec "$PGC" pg_isready -U postgres -q && break; sleep 1; done
docker exec "$PGC" pg_isready -U postgres -q || unready "postgres 준비 실패"
mkdb(){ docker exec "$PGC" createdb -U postgres "$1" >/dev/null; }
apply(){ docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" <"$2"; }
oracle(){
  local db="$1" expected="$2" label="$3" rc=0
  docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$db" \
    <"$HERE/0023-assertions.sql" >"$TMP/oracle.out" 2>&1 || rc=$?
  if { [ "$expected" = green ] && [ "$rc" -ne 0 ]; } || { [ "$expected" = red ] && [ "$rc" -eq 0 ]; }; then
    sed 's/^/  /' "$TMP/oracle.out" | head -20; red "$label 결과가 $expected가 아니다"
  fi
  echo "[0023-drift] $label → $expected OK"
}
mkdb head_db; apply head_db "$TMP/head.sql" || red "head 적용 실패"; oracle head_db green "head"
mkdb prev_db; apply prev_db "$TMP/prev.sql" || red "prev 적용 실패"; oracle prev_db red "0022"
mkdb down_db; apply down_db "$TMP/head.sql" || red "down head 적용 실패"
apply down_db "$TMP/down.sql" || red "downgrade 실패"; oracle down_db red "downgrade"
for db in prev_db down_db; do
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$db" \
   | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' >"$TMP/$db.norm"
done
diff -u "$TMP/prev_db.norm" "$TMP/down_db.norm" >"$TMP/shape.diff" || {
  head -40 "$TMP/shape.diff"; red "downgrade가 0022 shape를 복원하지 못했다"; }
echo "0023-drift green — head/previous/downgrade 3갈래와 0022 shape 복원."
