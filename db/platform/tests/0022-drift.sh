#!/usr/bin/env bash
# 0022 드리프트 시험 — **미러 트리거를 문장 단위로 내린 것을 되돌리면 red 가 난다**를 기계가 증명한다.
# 형태는 0020-drift.sh 와 같다(같은 실패를 두 번 배우지 않는다).
#
#   ㈎ head (0022 적용)        → 오라클 green (문장 단위 트리거 3 ＋ 전이 표 ＋ 미러 값 회귀)
#   ㈏ 0021 까지만             → 오라클 red     ← 「되돌리면 red」(행 단위 한 벌이 남아 있다)
#   ㈐ head → downgrade 0021   → 오라클 red + pg_dump 로 0021 형태 복원 확인
#
# ⚠ **「N행에 1회」의 나머지 반쪽은 여기가 아니다** — 쓰기 쪽이 INSERT 를 한 문장으로 보내는지는
#   `services/core-api/tests/test_variable_rows.py` 가 잰다. 트리거만 문장 단위로 두고 쓰기가
#   N 문장이면 여전히 N 번 뛴다.
#
# 원칙 (CLAUDE.md §4): 도커·alembic 이 없으면 **skip 이 아니라 red** 다.
#
# 환경변수
#   COLAB_ALEMBIC   alembic 실행 파일 (기본: PATH 의 alembic)
#   COLAB_PG_IMAGE  기본 postgres:16-alpine
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN_DIR="$(cd "$HERE/.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
PG_IMAGE="${COLAB_PG_IMAGE:-postgres:16-alpine}"
HEAD_REV="0022_rc7_variable_mirror_stmt"
PREV_REV="0021_rc7_access_state_gap"

red() { echo "::error::0022-drift red — $*"; exit 1; }

command -v docker >/dev/null 2>&1 || red "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || red "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다. 못 돈 시험은 통과가 아니다."
for f in 0022-assertions.sql; do
  [ -f "$HERE/$f" ] || red "오라클 파일($f)이 없다."
done

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" s1db-drift-XXXXXX)"
PGC=""
cleanup() { [ -n "$PGC" ] && docker rm -f "$PGC" >/dev/null 2>&1; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM

export COLAB_PLATFORM_DB_URL="postgresql+psycopg://offline/offline"
render() {
  ( cd "$CHAIN_DIR" && "$ALEMBIC" $1 --sql ) > "$2" 2>"$TMP/err" \
    || { sed 's/^/     /' "$TMP/err"; red "alembic 렌더 실패: $1"; }
}
render "upgrade $HEAD_REV" "$TMP/head.sql"
render "upgrade $PREV_REV" "$TMP/prev.sql"
render "downgrade $HEAD_REV:$PREV_REV" "$TMP/down.sql"
render "upgrade $PREV_REV:$HEAD_REV" "$TMP/delta.sql"

# 문장 단위 트리거 셋이 **한 리비전 안에** 있는가.
for token in d3_dataset_variable_mirror_ins d3_dataset_variable_mirror_upd \
             d3_dataset_variable_mirror_del 'FOR EACH STATEMENT' REFERENCING; do
  grep -q "$token" "$TMP/delta.sql" || red "렌더된 델타 SQL 에 '$token' 이 없다 — 0022 가 체인에 안 붙었거나 갈렸다."
done
# ⛔ **열을 지우지 않는다** — 미러 배열(`variables`)은 되돌림 경로다(라운드 ㉴).
grep -qiE 'DROP[[:space:]]+COLUMN' "$TMP/delta.sql" \
  && red "델타에 DROP COLUMN 이 있다 — 이 회차는 트리거만 바꾼다."
echo "[0022-drift] 델타에 DROP COLUMN 0개 → OK"

docker image inspect "$PG_IMAGE" >/dev/null 2>&1 || docker pull -q "$PG_IMAGE" >/dev/null 2>&1 \
  || red "이미지 $PG_IMAGE 를 확보하지 못했다. skip 아님."
PGC="s1db_drift_$$_${RANDOM}"
docker run -d --rm --name "$PGC" \
  --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=s1db -e POSTGRES_HOST_AUTH_METHOD=trust \
  "$PG_IMAGE" >/dev/null 2>&1 || { PGC=""; red "일회용 postgres 를 띄우지 못했다."; }
for _ in $(seq 1 60); do docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 && break; sleep 1; done
docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 || red "postgres 가 60초 안에 뜨지 않았다."

psql_f() { docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" < "$2"; }
mkdb()   { docker exec "$PGC" createdb -U postgres "$1" >/dev/null; }

# ── 소유자 롤 — **실배포의 마이그레이터와 같은 자격**이다 (0019-drift.sh 와 같은 이유) ──
docker exec "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d postgres \
  -c "CREATE ROLE t_owner LOGIN NOSUPERUSER NOBYPASSRLS;" >/dev/null \
  || red "소유자 롤 t_owner 를 만들지 못했다."
handover() {
  docker exec "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" -c "
    DO \$hand\$
    DECLARE r record;
    BEGIN
      FOR r IN SELECT c.oid::regclass::text AS n FROM pg_class c
                 JOIN pg_namespace ns ON ns.oid = c.relnamespace
                WHERE ns.nspname = 'public' AND c.relkind IN ('r','p','S','v','m')
      LOOP EXECUTE format('ALTER TABLE %s OWNER TO t_owner', r.n); END LOOP;
      FOR r IN SELECT p.oid::regprocedure::text AS n FROM pg_proc p
                 JOIN pg_namespace ns ON ns.oid = p.pronamespace
                WHERE ns.nspname = 'public'
      LOOP EXECUTE format('ALTER FUNCTION %s OWNER TO t_owner', r.n); END LOOP;
      FOR r IN SELECT t.oid::regtype::text AS n FROM pg_type t
                 JOIN pg_namespace ns ON ns.oid = t.typnamespace
                WHERE ns.nspname = 'public' AND t.typtype = 'd'
      LOOP EXECUTE format('ALTER DOMAIN %s OWNER TO t_owner', r.n); END LOOP;
    END
    \$hand\$;
    ALTER SCHEMA public OWNER TO t_owner;" >/dev/null \
    && docker exec "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d postgres \
    -c "ALTER DATABASE $1 OWNER TO t_owner;" >/dev/null \
    || red "소유권을 t_owner 로 넘기지 못했다($1)."
}
psql_owner() { docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U t_owner -d "$1" < "$2"; }

FAILURES=()
oracle() {   # $1=DB $2=기대(green|red) $3=라벨 $4=오라클 파일
  local out rc got
  out="$(docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" \
          < "$HERE/$4" 2>&1)"; rc=$?
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$2" ]; then
    echo "[0022-drift] $3 → $got OK"
    [ "$got" = "red" ] && echo "$out" | grep -m1 "0022 오라클 실패\|ERROR" | sed 's/^/           ↳ /'
  else
    echo "[0022-drift] $3 → $got (기대 $2) ✗"
    echo "$out" | sed 's/^/           /' | head -20
    FAILURES+=("$3")
  fi
  return 0
}

# ── ㈎ 0022 적용 ────────────────────────────────────────────────────────────
mkdb head_db;  psql_f head_db "$TMP/head.sql" || red "head 마이그레이션이 적용되지 않았다."
oracle head_db green "㈎ 0022 적용 후 — 문장 단위 트리거와 미러 회귀" 0022-assertions.sql

# ── ㈏ 0021 까지만 (0022 없음) ──────────────────────────────────────────────
mkdb prev_db;  psql_f prev_db "$TMP/prev.sql" || red "0021 마이그레이션이 적용되지 않았다."
oracle prev_db red "㈏ 0022 없음(행 단위) — 오라클이 red 를 내는가" 0022-assertions.sql

# ── ㈐ head → downgrade → 0019 ──────────────────────────────────────────────
mkdb down_db;  psql_f down_db "$TMP/head.sql" || red "head 적용 실패(㈐)."
psql_f down_db "$TMP/down.sql" || red "downgrade 가 실제로 돌지 않았다 — 되돌릴 수 없는 마이그레이션이다."
oracle down_db red "㈐ downgrade 후 — 오라클이 red 를 내는가" 0022-assertions.sql

# 「지웠다」와 「되돌렸다」는 다르다 — 0021 상태와 스키마가 같은가.
for db in down_db prev_db; do
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$db" \
    | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' > "$TMP/$db.norm"
done
if diff -u "$TMP/prev_db.norm" "$TMP/down_db.norm" > "$TMP/shape.diff"; then
  echo "[0022-drift] ㈐ downgrade 결과 = 0021 상태 (pg_dump 동일) → OK"
else
  echo "[0022-drift] ㈐ downgrade 결과가 0021 상태와 다르다 ✗"
  sed 's/^/           /' "$TMP/shape.diff" | head -40
  FAILURES+=("㈐ downgrade = 0021 동일성")
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0022-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0022-drift green — ㈎ 문장 단위 트리거 3 + 미러 값 회귀 · ㈏ 되돌리면 red · ㈐ downgrade 실물 동작 + 0021 복원."
