#!/usr/bin/env bash
# 0020 드리프트 시험 — **0020 을 되돌리면 red 가 난다**를 기계가 증명한다.
# 형태는 0019-drift.sh 와 같다(같은 실패를 두 번 배우지 않는다). 다른 것은 ㈑ 다 —
# 0019 는 「색인이 그 낱말을 찾는가」를 쟀고, 0020 은 **「중복이 있으면 마이그레이션이 멈추는가」**를 잰다.
#
#   ㈎ head (0020 적용)        → 구조·동작 오라클 green (제약 존재 ＋ 둘째가 튕김 ＋ 다른 연구실 성공)
#   ㈏ 0019 까지만             → 오라클 red     ← 「되돌리면 red」
#   ㈐ head → downgrade 0019   → 오라클 red + pg_dump 로 0019 형태 복원 확인
#   ㈑ 0019 에 **겹치는 행**을 심고 0019:0020 델타를 소유자 롤로 적용 → **적용이 실패**하고
#      메시지에 **건수**가 보인다 (라운드 ㉴ 「지우지 않는다 · 멈추고 건수 보고」).
#   ㈑-b 같은 자리에서 **사전 점검의 NO FORCE 를 지운** 델타 → 점검이 0행을 세고 조용히 지나가
#      **ALTER 가 대신 실패**한다 → 그때 건수 문면이 없다(대조군 · 점검이 점검임의 증명).
#
# 원칙 (CLAUDE.md §4): 도커·alembic 이 없으면 **skip 이 아니라 red** 다.
# staging 을 건드리지 않는다 — 일회용 컨테이너는 `s1db_` 접두사이고 호스트 포트를 하나도 열지 않는다.
#
# 환경변수
#   COLAB_ALEMBIC   alembic 실행 파일 (기본: PATH 의 alembic)
#   COLAB_PG_IMAGE  기본 postgres:16-alpine
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN_DIR="$(cd "$HERE/.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
PG_IMAGE="${COLAB_PG_IMAGE:-postgres:16-alpine}"
HEAD_REV="0020_rc7_project_name_unique"
PREV_REV="0019_rb7_search_index_m10"

red() { echo "::error::0020-drift red — $*"; exit 1; }

command -v docker >/dev/null 2>&1 || red "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || red "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다. 못 돈 시험은 통과가 아니다."
for f in 0020-assertions.sql 0020-existing-rows-seed.sql; do
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

# 제약과 사전 점검이 **한 리비전 안에** 있는가. 하나라도 빠지면 이름이 다르거나 체인이 갈린 것이다.
for token in d6_project_lab_name_unique 'RC7 DUPCHECK BEGIN' 'RC7 DUPCHECK END'; do
  grep -q "$token" "$TMP/delta.sql" || red "렌더된 델타 SQL 에 '$token' 이 없다 — 0020 이 체인에 안 붙었거나 갈렸다."
done
# ⛔ **지우거나 고치는 문장이 없다** (라운드 ㉴ · spec 우려 6 「중복 이름 자동 개명 금지」).
grep -qiE '(DELETE[[:space:]]+FROM|UPDATE)[[:space:]]+d6_project' "$TMP/delta.sql" \
  && red "델타가 d6_project 의 행을 지우거나 고친다 — 사람이 적은 이름을 자동으로 건드리지 않는다."
echo "[0020-drift] 델타에 d6_project 행 변경 문장 0개 → OK"

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
    echo "[0020-drift] $3 → $got OK"
    [ "$got" = "red" ] && echo "$out" | grep -m1 "0020 오라클 실패\|ERROR" | sed 's/^/           ↳ /'
  else
    echo "[0020-drift] $3 → $got (기대 $2) ✗"
    echo "$out" | sed 's/^/           /' | head -20
    FAILURES+=("$3")
  fi
  return 0
}

# ── ㈎ 0020 적용 ────────────────────────────────────────────────────────────
mkdb head_db;  psql_f head_db "$TMP/head.sql" || red "head 마이그레이션이 적용되지 않았다."
oracle head_db green "㈎ 0020 적용 후 — 제약이 실제로 거절하는가" 0020-assertions.sql

# ── ㈏ 0019 까지만 (0020 없음) ──────────────────────────────────────────────
mkdb prev_db;  psql_f prev_db "$TMP/prev.sql" || red "0019 마이그레이션이 적용되지 않았다."
oracle prev_db red "㈏ 0020 없음 — 오라클이 red 를 내는가" 0020-assertions.sql

# ── ㈐ head → downgrade → 0019 ──────────────────────────────────────────────
mkdb down_db;  psql_f down_db "$TMP/head.sql" || red "head 적용 실패(㈐)."
psql_f down_db "$TMP/down.sql" || red "downgrade 가 실제로 돌지 않았다 — 되돌릴 수 없는 마이그레이션이다."
oracle down_db red "㈐ downgrade 후 — 오라클이 red 를 내는가" 0020-assertions.sql

# 「지웠다」와 「되돌렸다」는 다르다 — 0019 상태와 스키마가 같은가.
for db in down_db prev_db; do
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$db" \
    | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' > "$TMP/$db.norm"
done
if diff -u "$TMP/prev_db.norm" "$TMP/down_db.norm" > "$TMP/shape.diff"; then
  echo "[0020-drift] ㈐ downgrade 결과 = 0019 상태 (pg_dump 동일) → OK"
else
  echo "[0020-drift] ㈐ downgrade 결과가 0019 상태와 다르다 ✗"
  sed 's/^/           /' "$TMP/shape.diff" | head -40
  FAILURES+=("㈐ downgrade = 0019 동일성")
fi

# ── ㈑ 겹치는 행이 있으면 **멈추고 건수를 적는다** ─────────────────────────
mkdb dup_db;  psql_f dup_db "$TMP/prev.sql"        || red "0019 적용 실패(㈑)."
psql_f dup_db "$HERE/0020-existing-rows-seed.sql"  || red "겹치는 행 재료를 심지 못했다(㈑)."
handover dup_db
if psql_owner dup_db "$TMP/delta.sql" > "$TMP/dup.out" 2>&1; then
  echo "[0020-drift] ㈑ 겹치는 행이 있는데 델타가 green 으로 끝났다 ✗"
  FAILURES+=("㈑ 중복 사전 점검")
else
  if grep -q '0020 중단' "$TMP/dup.out" && grep -qE '짝이 [0-9]+건' "$TMP/dup.out"; then
    echo "[0020-drift] ㈑ 겹치는 행 → 멈춤 ＋ 건수 보고 → OK"
    grep -m1 '0020 중단' "$TMP/dup.out" | sed 's/^/           ↳ /'
  else
    echo "[0020-drift] ㈑ 멈추긴 했으나 **건수 문면이 없다** ✗ (「멈추고 건수 보고」가 수용 기준이다)"
    sed 's/^/           /' "$TMP/dup.out" | tail -10
    FAILURES+=("㈑ 중단 메시지의 건수")
  fi
fi
# 지우지 않았다 — 겹치던 행이 그대로 있다.
LEFT="$(docker exec "$PGC" psql -tAq -U postgres -d dup_db -c "SELECT count(*) FROM d6_project" 2>/dev/null)"
if [ "$LEFT" = "3" ]; then
  echo "[0020-drift] ㈑ 겹치던 행 3건이 **그대로 남았다**(지우지 않는다) → OK"
else
  echo "[0020-drift] ㈑ 겹치던 행이 ${LEFT}건이다 (기대 3) — 마이그레이션이 행을 건드렸다 ✗"
  FAILURES+=("㈑ 행 무변")
fi

# ── ㈑-b 대조군 — 사전 점검의 NO FORCE 를 지우면 **건수 문면이 사라진다** ───
# 소유자 롤은 `current_lab_id()` 가 NULL 이라 FORCE 인 채로는 0행을 세고 조용히 지나간다.
# 그때 실패는 ALTER 가 내는 unique_violation 이고, 사람은 **몇 건인지 못 듣는다**.
awk '/RC7 DUPCHECK BEGIN/{blk=1} blk && /NO FORCE ROW LEVEL SECURITY/{next} /RC7 DUPCHECK END/{blk=0} {print}' \
  "$TMP/delta.sql" > "$TMP/delta-noforce.sql"
if diff -q "$TMP/delta.sql" "$TMP/delta-noforce.sql" >/dev/null; then
  red "델타의 사전 점검 구간에 NO FORCE 가 없다 — 실배포 롤에서 점검이 0행을 센다."
fi
mkdb dupb_db; psql_f dupb_db "$TMP/prev.sql"        || red "0019 적용 실패(㈑-b)."
psql_f dupb_db "$HERE/0020-existing-rows-seed.sql"  || red "겹치는 행 재료를 심지 못했다(㈑-b)."
handover dupb_db
if psql_owner dupb_db "$TMP/delta-noforce.sql" > "$TMP/dupb.out" 2>&1; then
  echo "[0020-drift] ㈑-b 대조군이 green 이다 ✗ — 시험이 결함을 못 잰다"
  FAILURES+=("㈑-b 대조군")
elif grep -q '0020 중단' "$TMP/dupb.out"; then
  echo "[0020-drift] ㈑-b 대조군이 여전히 건수를 말했다 ✗ — NO FORCE 가 점검의 조건이 아니다"
  FAILURES+=("㈑-b 대조군")
else
  echo "[0020-drift] ㈑-b NO FORCE 를 뺀 델타 → 건수 없이 실패(대조군) → OK"
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0020-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0020-drift green — ㈎ 제약이 실제로 거절 · ㈏ 0020 없으면 red · ㈐ downgrade 실물 동작 + 0019 복원 · ㈑ 중복이면 멈추고 건수 보고(행 무변 · 대조군 ㈑-b red)."
