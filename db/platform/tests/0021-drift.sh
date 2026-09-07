#!/usr/bin/env bash
# 0021 드리프트 시험 — **이관 빈틈 보정이 실제로 그 한 행만 옮긴다**를 기계가 증명한다.
# 형태는 0019-drift.sh 의 ㈑ 계열과 같다. 다른 것은 **스키마 차분이 0** 이라는 점이다 —
# 0021 은 데이터 마이그레이션이라 빈 DB 의 구조 오라클이 없다. 재는 것은 전부 **행**이다.
#
#   ㈎ 0020 ＋ 픽스처 3종 → 0020:0021 델타를 **소유자 롤**로 적용 → 기존 행 오라클 green
#      (첫 것만 `지정 공개` · 나머지 둘 무변 · 상태 행 3건 그대로 · 불변식 0건)
#      그리고 **이동 행 수 1 이 출력에 보인다**(수용 기준 축자).
#   ㈏ 보정 구간(`RC7 GAP`)을 **도려낸** 델타 → 오라클 red  ← 「되돌리면 red」
#   ㈐ ㈎ 뒤에 downgrade 0020 → 되돌림 오라클 green (DS1 이 NULL 로 · grant 무손실)
#   ㈑ **NO FORCE 를 지운** 델타(수정 전 자리) → 0행 이관 → 오라클 red
#      (실배포 롤에서 UPDATE 가 오류 없이 0행이 되는 결함을 기계가 잰다)
#   ㈒ 델타에 스키마 변경 문장이 **0개**다 — 데이터 마이그레이션이 몰래 구조를 바꾸지 않는다.
#
# 원칙 (CLAUDE.md §4): 도커·alembic 이 없으면 **skip 이 아니라 red** 다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN_DIR="$(cd "$HERE/.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
PG_IMAGE="${COLAB_PG_IMAGE:-postgres:16-alpine}"
HEAD_REV="0021_rc7_access_state_gap"
PREV_REV="0020_rc7_project_name_unique"

red() { echo "::error::0021-drift red — $*"; exit 1; }

command -v docker >/dev/null 2>&1 || red "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || red "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다. 못 돈 시험은 통과가 아니다."
for f in 0021-assertions.sql 0021-existing-rows-seed.sql 0021-existing-rows-assertions.sql; do
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
render "upgrade $PREV_REV" "$TMP/prev.sql"
render "upgrade $PREV_REV:$HEAD_REV" "$TMP/delta.sql"
render "downgrade $HEAD_REV:$PREV_REV" "$TMP/down.sql"

for token in 'RC7 GAP BEGIN' 'RC7 GAP END' '지정 공개'; do
  grep -q "$token" "$TMP/delta.sql" || red "렌더된 델타 SQL 에 '$token' 이 없다 — 0021 이 체인에 안 붙었거나 갈렸다."
done
# ㈒ **스키마 변경 0** — 데이터 마이그레이션이다. `NO FORCE`/`FORCE` 는 RLS 스위치라 셈에서 뺀다.
SCHEMA_STMTS="$(grep -icE '^[[:space:]]*(CREATE|DROP)[[:space:]]|^[[:space:]]*ALTER[[:space:]]+TABLE[[:space:]]+[a-z0-9_]+[[:space:]]+(ADD|DROP|RENAME|ALTER)' "$TMP/delta.sql")"
if [ "$SCHEMA_STMTS" = "0" ]; then
  echo "[0021-drift] ㈒ 델타의 스키마 변경 문장 0개 → OK"
else
  echo "[0021-drift] ㈒ 델타에 스키마 변경 문장이 ${SCHEMA_STMTS}개 있다 ✗ — 0021 은 데이터 마이그레이션이다"
  grep -inE '^[[:space:]]*(CREATE|DROP)[[:space:]]' "$TMP/delta.sql" | sed 's/^/           /' | head -10
fi

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
oracle() {   # $1=DB $2=기대 $3=라벨 $4=오라클 파일
  local out rc got
  out="$(docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" \
          < "$HERE/$4" 2>&1)"; rc=$?
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$2" ]; then
    echo "[0021-drift] $3 → $got OK"
    [ "$got" = "red" ] && echo "$out" | grep -m1 "0021 .*오라클 실패\|ERROR" | sed 's/^/           ↳ /'
  else
    echo "[0021-drift] $3 → $got (기대 $2) ✗"
    echo "$out" | sed 's/^/           /' | head -20
    FAILURES+=("$3")
  fi
  return 0
}

seeded() {   # $1=DB — 0020 상태 ＋ 픽스처 3종 ＋ 소유권 이관
  mkdb "$1"; psql_f "$1" "$TMP/prev.sql"                    || red "0020 적용 실패($1)."
  psql_f "$1" "$HERE/0021-existing-rows-seed.sql"           || red "픽스처 3종을 심지 못했다($1)."
  handover "$1"
}

# ── ㈎ 보정 적용 ────────────────────────────────────────────────────────────
seeded gap_db
psql_owner gap_db "$TMP/delta.sql" > "$TMP/gap.out" 2>&1 \
  || { sed 's/^/           /' "$TMP/gap.out" | tail -10; red "0020→0021 델타가 소유자 롤에서 돌지 않았다(㈎)."; }
oracle gap_db green "㈎ 픽스처 3종 — 첫 것만 지정 공개인가" 0021-existing-rows-assertions.sql

# **이동 행 수가 출력에 보인다** — 「이동 행 수 1 이 출력에 보인다」가 수용 기준의 문장이다.
if grep -qE '\[0021\].*1행 이동' "$TMP/gap.out"; then
  echo "[0021-drift] ㈎ 이동 행 수 1 이 출력에 보인다 → OK"
  grep -m1 '\[0021\]' "$TMP/gap.out" | sed 's/^/           ↳ /'
else
  echo "[0021-drift] ㈎ 출력에 「1행 이동」이 없다 ✗ — 배포 창이 읽을 숫자가 없다"
  grep -m3 '\[0021\]' "$TMP/gap.out" | sed 's/^/           /'
  FAILURES+=("㈎ 이동 행 수 출력")
fi

# ── ㈏ 보정 구간을 도려낸 델타 → red ───────────────────────────────────────
awk '/RC7 GAP BEGIN/{skip=1} skip!=1{print} /RC7 GAP END/{skip=0}' "$TMP/delta.sql" > "$TMP/delta-nogap.sql"
if diff -q "$TMP/delta.sql" "$TMP/delta-nogap.sql" >/dev/null; then
  red "보정 구간을 도려내지 못했다 — 대조군을 만들 수 없다(RC7 GAP 표식 확인)."
fi
seeded nogap_db
psql_owner nogap_db "$TMP/delta-nogap.sql" >/dev/null 2>&1 || red "보정 없는 델타가 돌지 않았다(㈏)."
oracle nogap_db red "㈏ 보정을 뺀 델타 — 오라클이 red 를 내는가" 0021-existing-rows-assertions.sql

# ── ㈐ downgrade — 옮긴 그 행만 NULL 로 ────────────────────────────────────
seeded down_db
psql_owner down_db "$TMP/delta.sql" >/dev/null 2>&1 || red "델타 적용 실패(㈐)."
psql_owner down_db "$TMP/down.sql"  >/dev/null 2>&1 || red "downgrade 가 실제로 돌지 않았다 — 되돌릴 수 없는 마이그레이션이다."
oracle down_db green "㈐ downgrade 후 — 옮긴 행만 NULL 로 돌아왔는가(값 소실 0)" 0021-assertions.sql

# ── ㈑ NO FORCE 를 지운 델타(수정 전 자리) → 0행 이관 → red ────────────────
grep -v 'NO FORCE ROW LEVEL SECURITY' "$TMP/delta.sql" > "$TMP/delta-nofix.sql"
if diff -q "$TMP/delta.sql" "$TMP/delta-nofix.sql" >/dev/null; then
  red "델타에 NO FORCE 구간이 없다 — 실배포 롤에서 UPDATE 가 0행이 된다."
fi
seeded nofix_db
psql_owner nofix_db "$TMP/delta-nofix.sql" > "$TMP/nofix.out" 2>&1 \
  || { sed 's/^/           /' "$TMP/nofix.out" | tail -5; red "수정 전 델타가 돌지 않았다(㈑) — 대조군은 오류 없이 0행으로 끝나야 한다."; }
oracle nofix_db red "㈑ 수정 전 델타(소유자 롤) — 0행 이관으로 오라클이 red 를 내는가" \
       0021-existing-rows-assertions.sql

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0021-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0021-drift green — ㈎ 픽스처 3종 중 첫 것만 이동(1행 · 출력에 보임) · ㈏ 보정 빼면 red · ㈐ downgrade 가 옮긴 행만 NULL 로(값 소실 0) · ㈑ 수정 전 델타 0행 red · ㈒ 스키마 변경 0."
