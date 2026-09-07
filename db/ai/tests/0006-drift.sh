#!/usr/bin/env bash
# 0006 드리프트 시험 — **분류 한 칸을 되돌리면 오라클이 red 를 낸다**를 기계가 증명한다.
# 형태는 db/ai/tests/0004-0005-drift.sh 와 같다 (같은 실패를 두 번 배우지 않는다).
# 다른 것은 오라클(0006-assertions.sql)과, **선언 정본 대조를 그대로 잇는다**는 점이다.
#
#   ㈎ head (0006 적용)        → 오라클 green (5값 CHECK 가 실제로 거절 · 이관 3쌍 · [미상] NULL)
#   ㈏ 0005 까지만             → 오라클 red     ← 「되돌리면 red」
#   ㈐ head → downgrade 0005   → 오라클 red + pg_dump 로 0005 형태 복원 확인
#   ㈑ 선언 정본(`db/ai/schema.sql`) = 마이그레이션 결과 (schema-diff 가 보는 것과 같은 사실)
#
# ⚠ 체인 머리가 라운드 파일의 전망(`0004`)과 다르다 — 실측 머리가 `0005_k2b_concept_graph_seed`
#   라 이 회차는 **`0006`** 이다. 번호를 맞추려고 남의 리비전을 밀어내지 않는다.
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
HEAD_REV="0006_rc7_synonym_category"
PREV_REV="0005_k2b_concept_graph_seed"

red() { echo "::error::0006-drift red — $*"; exit 1; }

command -v docker >/dev/null 2>&1 || red "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || red "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다. 못 돈 시험은 통과가 아니다."
[ -f "$HERE/0006-assertions.sql" ] || red "오라클 파일(0006-assertions.sql)이 없다."

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" k1bdb-drift-XXXXXX)"
PGC=""
cleanup() { [ -n "$PGC" ] && docker rm -f "$PGC" >/dev/null 2>&1; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM

export COLAB_AI_DB_URL="postgresql+psycopg://offline/offline"
render() {
  ( cd "$CHAIN_DIR" && "$ALEMBIC" $1 --sql ) > "$2" 2>"$TMP/err" \
    || { sed 's/^/     /' "$TMP/err"; red "alembic 렌더 실패: $1"; }
}
render "upgrade $HEAD_REV"             "$TMP/head.sql"
render "upgrade $PREV_REV"             "$TMP/prev.sql"
render "downgrade $HEAD_REV:$PREV_REV" "$TMP/down.sql"
render "upgrade $PREV_REV:$HEAD_REV"   "$TMP/delta.sql"

for token in 'ADD COLUMN category' 'RC7 SYNONYM MAP BEGIN' 'RC7 SYNONYM MAP END' '기상·기후 인자'; do
  grep -q "$token" "$TMP/delta.sql" || red "렌더된 델타 SQL 에 '$token' 이 없다 — 0006 이 체인에 안 붙었거나 갈렸다."
done
# ⛔ **`topic` 을 안 건드린다** — 주제 축과 분류 축은 다른 축이고, 갈아 끼우면 `0005` 의 오라클이 무너진다.
grep -qiE 'ALTER[[:space:]]+TABLE[[:space:]]+d9_topic_synonym[^;]*(DROP[[:space:]]+COLUMN[[:space:]]+topic|ALTER[[:space:]]+COLUMN[[:space:]]+topic)' "$TMP/delta.sql" \
  && red "델타가 topic 열을 건드린다 — 이 회차는 분류 한 칸을 **옆에** 세울 뿐이다."
grep -qiE 'UPDATE[[:space:]]+d9_topic_synonym[[:space:]]+SET[[:space:]]+topic' "$TMP/delta.sql" \
  && red "델타가 topic 값을 고친다 — 주제 축은 이 회차의 범위 밖이다."
# ⛔ **지형·DEM 을 어느 분류로도 옮기지 않는다** ([미상] · PRD-01 무근거).
grep -q '지형·DEM' "$TMP/delta.sql" \
  && red "델타가 지형·DEM 을 매핑한다 — PRD-01 어느 줄에서도 도출되지 않는 값을 지어냈다."
echo "[0006-drift] 델타가 topic 무접촉 · 지형·DEM 매핑 0 → OK"

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
oracle() {   # $1=DB $2=기대 $3=라벨
  local out rc got
  out="$(docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" \
          < "$HERE/0006-assertions.sql" 2>&1)"; rc=$?
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$2" ]; then
    echo "[0006-drift] $3 → $got OK"
    [ "$got" = "red" ] && echo "$out" | grep -m1 "0006 오라클 실패\|ERROR" | sed 's/^/           ↳ /'
  else
    echo "[0006-drift] $3 → $got (기대 $2) ✗"
    echo "$out" | sed 's/^/           /' | head -20
    FAILURES+=("$3")
  fi
  return 0
}

mkdb head_db; psql_f head_db "$TMP/head.sql" || red "head 마이그레이션이 적용되지 않았다."
oracle head_db green "㈎ 0006 적용 후 — 5값 CHECK 가 실제로 거절하고 3쌍이 옮겨졌는가"

mkdb prev_db; psql_f prev_db "$TMP/prev.sql" || red "0005 마이그레이션이 적용되지 않았다."
oracle prev_db red "㈏ 0006 없음 — 오라클이 red 를 내는가"

mkdb down_db; psql_f down_db "$TMP/head.sql" || red "head 적용 실패(㈐)."
psql_f down_db "$TMP/down.sql" || red "downgrade 가 실제로 돌지 않았다 — 되돌릴 수 없는 마이그레이션이다."
oracle down_db red "㈐ downgrade 후 — 오라클이 red 를 내는가"

# 「지웠다」와 「되돌렸다」는 다르다 — 0005 상태와 스키마가 같은가.
for db in down_db prev_db; do
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$db" \
    | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' > "$TMP/$db.norm"
done
if diff -u "$TMP/prev_db.norm" "$TMP/down_db.norm" > "$TMP/shape.diff"; then
  echo "[0006-drift] ㈐ downgrade 결과 = 0005 상태 (pg_dump 동일) → OK"
else
  echo "[0006-drift] ㈐ downgrade 결과가 0005 상태와 다르다 ✗"
  sed 's/^/           /' "$TMP/shape.diff" | head -40
  FAILURES+=("㈐ downgrade = 0005 동일성")
fi

# ㈑ 선언 정본(schema.sql) ↔ 마이그레이션 결과 (schema-diff 가 보는 것과 같은 사실).
mkdb decl_db; psql_f decl_db "$CHAIN_DIR/schema.sql" || red "schema.sql 를 적용하지 못했다."
for db in head_db decl_db; do
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$db" \
    | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' \
    | grep -v 'alembic_version_ai' > "$TMP/$db.decl"
done
if diff -u "$TMP/decl_db.decl" "$TMP/head_db.decl" > "$TMP/decl.diff"; then
  echo "[0006-drift] 선언 정본 schema.sql = 마이그레이션 결과 → OK"
else
  echo "[0006-drift] schema.sql 과 마이그레이션 결과가 갈렸다 ✗"
  sed 's/^/           /' "$TMP/decl.diff" | head -60
  FAILURES+=("schema.sql ↔ 마이그레이션 동일성")
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0006-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0006-drift green — ㈎ 5값 CHECK 실거절 ＋ 이관 3쌍 ＋ [미상] NULL · ㈏㈐ 되돌리면 red · downgrade 실물 동작 · 선언 = 적용."
