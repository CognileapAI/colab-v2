#!/usr/bin/env bash
# 0004·0005 드리프트 시험 — **K1b·K2b 를 되돌리면 완료 오라클이 red 를 낸다**를 기계가 증명한다.
# 형태는 db/platform/tests/0005-drift.sh 와 같다 (같은 실패를 두 번 배우지 않는다).
# 다른 것은 체인(ai)과 오라클(k2b-graph-check.sh)뿐이다.
#
#   ㈎ head (0004+0005 적용)      → 오라클 green
#   ㈏ 0003 까지만                → 오라클 red     ← 「K1b 가 없으면 red」
#   ㈐ head → downgrade 0004      → 오라클 red     ← 「K2b 시드를 되돌리면 red」
#   ㈑ head → downgrade 0003      → 오라클 red + pg_dump 로 0003 형태 복원 확인
#
# **마이그레이션이 실제로 무엇을 했는지 증명하는 자리다.** 시험 없는 마이그레이션은 완료가 아니다
# (CLAUDE.md §4). 판정기 자체가 red 를 낼 수 있는지는 별개의 증명이다 —
# db/ai/tools/k2b-graph-selftest.sh (16 케이스, DB 없이 돈다).
#
# 원칙 (CLAUDE.md §4): 도커·alembic 이 없으면 **skip 이 아니라 red** 다.
# staging 을 건드리지 않는다 — 일회용 컨테이너는 `k1bdb_` 접두사이고 호스트 포트를 하나도 열지 않는다.
#
# 환경변수
#   COLAB_ALEMBIC   alembic 실행 파일 (기본: PATH 의 alembic)
#   COLAB_PG_IMAGE  기본 postgres:16-alpine
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN_DIR="$(cd "$HERE/.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
PG_IMAGE="${COLAB_PG_IMAGE:-postgres:16-alpine}"
HEAD_REV="0005_k2b_concept_graph_seed"
MID_REV="0004_k1b_concept_graph"
PREV_REV="0003_k2_ontology_seed"

red() { echo "::error::0004-0005-drift red — $*"; exit 1; }

command -v docker >/dev/null 2>&1 || red "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || red "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다. 못 돈 시험은 통과가 아니다."
[ -x "$CHAIN_DIR/tools/k2b-graph-check.sh" ] || red "완료 오라클(tools/k2b-graph-check.sh)이 없다."

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" k1bdb-drift-XXXXXX)"
PGC=""
cleanup() { [ -n "$PGC" ] && docker rm -f "$PGC" >/dev/null 2>&1; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM

export COLAB_AI_DB_URL="postgresql+psycopg://offline/offline"
render() {
  ( cd "$CHAIN_DIR" && "$ALEMBIC" $1 --sql ) > "$2" 2>"$TMP/err" \
    || { sed 's/^/     /' "$TMP/err"; red "alembic 렌더 실패: $1"; }
}
render "upgrade $HEAD_REV"              "$TMP/head.sql"
render "upgrade $MID_REV"               "$TMP/mid.sql"
render "upgrade $PREV_REV"              "$TMP/prev.sql"
render "downgrade $HEAD_REV:$MID_REV"   "$TMP/down_seed.sql"
render "downgrade $HEAD_REV:$PREV_REV"  "$TMP/down_all.sql"

grep -q "d9_concept_edge" "$TMP/head.sql" \
  || red "렌더된 head SQL 에 d9_concept_edge 가 없다 — 0004 가 체인에 안 붙었거나 리비전 이름이 다르다."
grep -q "m-cokriging" "$TMP/head.sql" \
  || red "렌더된 head SQL 에 시드 값이 없다 — 0005 가 seed SQL 을 읽지 못했다."
grep -q "Co-Kriging" "$TMP/head.sql" && grep -q $'m-cokriging\x27,\x27~의 한 가지다' "$TMP/head.sql" \
  && red "렌더된 head SQL 에 F-4d(Co-Kriging → 재격자화)가 들어 있다. Ted 가 ❌ 친 행이다."

docker image inspect "$PG_IMAGE" >/dev/null 2>&1 || docker pull -q "$PG_IMAGE" >/dev/null 2>&1 \
  || red "이미지 $PG_IMAGE 를 확보하지 못했다. skip 아님."
PGC="k1bdb_drift_$$_${RANDOM}"
docker run -d --rm --name "$PGC" \
  --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=k1bdb -e POSTGRES_HOST_AUTH_METHOD=trust \
  "$PG_IMAGE" >/dev/null 2>&1 || { PGC=""; red "일회용 postgres 를 띄우지 못했다."; }
for _ in $(seq 1 60); do docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 && break; sleep 1; done
docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 || red "postgres 가 60초 안에 뜨지 않았다."

psql_f() { docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" < "$2"; }
mkdb()   { docker exec "$PGC" createdb -U postgres "$1" >/dev/null; }

FAILURES=()
oracle() {   # $1=DB $2=기대(green|red) $3=라벨
  local out rc got
  out="$(COLAB_AI_DB_CONTAINER="$PGC" COLAB_AI_DB_NAME="$1" \
          bash "$CHAIN_DIR/tools/k2b-graph-check.sh" 2>&1)"; rc=$?
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$2" ]; then
    echo "[0004-0005-drift] $3 → $got OK"
    [ "$got" = "red" ] && echo "$out" | grep -m1 "::error::" | sed 's/^/           ↳ /'
  else
    echo "[0004-0005-drift] $3 → $got (기대 $2) ✗"
    echo "$out" | sed 's/^/           /' | head -20
    FAILURES+=("$3")
  fi
  return 0
}

# ── ㈎ head 적용 ────────────────────────────────────────────────────────────
mkdb head_db; psql_f head_db "$TMP/head.sql" || red "head 마이그레이션이 적용되지 않았다."
oracle head_db green "㈎ 0004+0005 적용 후 — 오라클"

# ── ㈏ 0003 까지만 (K1b 없음) ───────────────────────────────────────────────
mkdb prev_db; psql_f prev_db "$TMP/prev.sql" || red "0003 마이그레이션이 적용되지 않았다."
oracle prev_db red "㈏ K1b 없음 — 오라클이 red 를 내는가"

# ── ㈐ head → downgrade 0004 (표는 있고 시드만 없다) ────────────────────────
mkdb mid_db;  psql_f mid_db "$TMP/head.sql" || red "head 적용 실패(㈐)."
psql_f mid_db "$TMP/down_seed.sql" || red "0005 downgrade 가 실제로 돌지 않았다 — 되돌릴 수 없는 마이그레이션이다."
oracle mid_db red "㈐ K2b 시드만 되돌림 — 오라클이 red 를 내는가"

# ── ㈑ head → downgrade 0003 ────────────────────────────────────────────────
mkdb down_db; psql_f down_db "$TMP/head.sql" || red "head 적용 실패(㈑)."
psql_f down_db "$TMP/down_all.sql" || red "0004 downgrade 가 실제로 돌지 않았다."
oracle down_db red "㈑ 전부 되돌림 — 오라클이 red 를 내는가"

# 「지웠다」와 「되돌렸다」는 다르다 — 0003 상태와 스키마가 같은가.
for db in down_db prev_db; do
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$db" \
    | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' > "$TMP/$db.norm"
done
if diff -u "$TMP/prev_db.norm" "$TMP/down_db.norm" > "$TMP/shape.diff"; then
  echo "[0004-0005-drift] ㈑ downgrade 결과 = 0003 상태 (pg_dump 동일) → OK"
else
  echo "[0004-0005-drift] ㈑ downgrade 결과가 0003 상태와 다르다 ✗"
  sed 's/^/           /' "$TMP/shape.diff" | head -40
  FAILURES+=("㈑ downgrade = 0003 동일성")
fi

# 선언 정본(schema.sql) ↔ 마이그레이션 결과가 갈리지 않는가 (schema-diff 게이트가 보는 것과 같은 사실).
mkdb decl_db; psql_f decl_db "$CHAIN_DIR/schema.sql" || red "schema.sql 를 적용하지 못했다."
for db in head_db decl_db; do
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$db" \
    | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' \
    | grep -v 'alembic_version_ai' > "$TMP/$db.decl"
done
if diff -u "$TMP/decl_db.decl" "$TMP/head_db.decl" > "$TMP/decl.diff"; then
  echo "[0004-0005-drift] 선언 정본 schema.sql = 마이그레이션 결과 → OK"
else
  echo "[0004-0005-drift] schema.sql 과 마이그레이션 결과가 갈렸다 ✗"
  sed 's/^/           /' "$TMP/decl.diff" | head -60
  FAILURES+=("schema.sql ↔ 마이그레이션 동일성")
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0004-0005-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0004-0005-drift green — ㈎ green · ㈏㈐㈑ 되돌리면 red · downgrade 실물 동작 · 선언 = 적용."
