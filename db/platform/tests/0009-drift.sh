#!/usr/bin/env bash
# 0009 드리프트 시험 — **0009 를 되돌리면 red 가 난다**를 기계가 증명한다.
# 형태는 0008-drift.sh 와 같다(같은 실패를 두 번 배우지 않는다). 다른 것은 대상 리비전과,
# 백필이 있는 판이라 0004 처럼 **㈑ 시드 위 적용** 한 경우가 더 붙은 것뿐이다.
#
#   ㈎ head (0009 적용)        → 오라클 green
#   ㈏ 0008 까지만             → 오라클 red     ← 「되돌리면 red」
#   ㈐ head → downgrade 0008   → 오라클 red + pg_dump 로 0008 형태 복원 확인
#   ㈑ 0008 + 낡은 합계 시드 → **소유자 롤(비superuser·NOBYPASSRLS)** 로 0008→0009 적용
#      → 백필이 합계를 실제로 고쳤는가(999→100 · NULL→0) + 오라클 green(⑥ 이 비어 있지 않다)
#      superuser 로 적용하면 FORCE RLS 창이 있으나 없으나 통과한다 — 창을 증명하려면 정책을
#      받는 롤로 적용해야 한다.
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
HEAD_REV="0009_file_management"
PREV_REV="0008_s3_upload_transfer"

red() { echo "::error::0009-drift red — $*"; exit 1; }

command -v docker >/dev/null 2>&1 || red "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || red "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다. 못 돈 시험은 통과가 아니다."
[ -f "$HERE/0009-assertions.sql" ] || red "오라클 파일(0009-assertions.sql)이 없다."

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
render "upgrade $PREV_REV:$HEAD_REV" "$TMP/step.sql"

grep -q "sync_dataset_total_size" "$TMP/head.sql" \
  || red "렌더된 head SQL 에 sync_dataset_total_size 가 없다 — 0009 가 체인에 안 붙었거나 리비전 이름이 다르다."

docker image inspect "$PG_IMAGE" >/dev/null 2>&1 || docker pull -q "$PG_IMAGE" >/dev/null 2>&1 \
  || red "이미지 $PG_IMAGE 를 확보하지 못했다. skip 아님."
PGC="s1db_drift_$$_${RANDOM}"
docker run -d --rm --name "$PGC" \
  --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=s1db -e POSTGRES_HOST_AUTH_METHOD=trust \
  "$PG_IMAGE" >/dev/null 2>&1 || { PGC=""; red "일회용 postgres 를 띄우지 못했다."; }
for _ in $(seq 1 60); do docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 && break; sleep 1; done
docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 || red "postgres 가 60초 안에 뜨지 않았다."

psql_f()  { docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" < "$2"; }
psql_as() { docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U "$1" -d "$2" < "$3"; }   # $1=롤
mkdb()    { docker exec "$PGC" createdb -U postgres "$@" >/dev/null; }

FAILURES=()
oracle() {   # $1=DB $2=기대(green|red) $3=라벨
  local out rc got
  out="$(docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" \
          < "$HERE/0009-assertions.sql" 2>&1)"; rc=$?
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$2" ]; then
    echo "[0009-drift] $3 → $got OK"
    [ "$got" = "red" ] && echo "$out" | grep -m1 "0009 오라클 실패\|ERROR" | sed 's/^/           ↳ /'
  else
    echo "[0009-drift] $3 → $got (기대 $2) ✗"
    echo "$out" | sed 's/^/           /' | head -20
    FAILURES+=("$3")
  fi
  return 0
}

# ── ㈎ 0009 적용 ────────────────────────────────────────────────────────────
mkdb head_db;  psql_f head_db "$TMP/head.sql" || red "head 마이그레이션이 적용되지 않았다."
oracle head_db green "㈎ 0009 적용 후 — 오라클"

# ── ㈏ 0008 까지만 (0009 없음) ──────────────────────────────────────────────
mkdb prev_db;  psql_f prev_db "$TMP/prev.sql" || red "0008 마이그레이션이 적용되지 않았다."
oracle prev_db red "㈏ 0009 없음 — 오라클이 red 를 내는가"

# ── ㈐ head → downgrade → 0008 ──────────────────────────────────────────────
mkdb down_db;  psql_f down_db "$TMP/head.sql" || red "head 적용 실패(㈐)."
psql_f down_db "$TMP/down.sql" || red "downgrade 가 실제로 돌지 않았다 — 되돌릴 수 없는 마이그레이션이다."
oracle down_db red "㈐ downgrade 후 — 오라클이 red 를 내는가"

# 「지웠다」와 「되돌렸다」는 다르다 — 0008 상태와 스키마가 같은가.
for db in down_db prev_db; do
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$db" \
    | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' > "$TMP/$db.norm"
done
if diff -u "$TMP/prev_db.norm" "$TMP/down_db.norm" > "$TMP/shape.diff"; then
  echo "[0009-drift] ㈐ downgrade 결과 = 0008 상태 (pg_dump 동일) → OK"
else
  echo "[0009-drift] ㈐ downgrade 결과가 0008 상태와 다르다 ✗"
  sed 's/^/           /' "$TMP/shape.diff" | head -40
  FAILURES+=("㈐ downgrade = 0008 동일성")
fi

# ── ㈑ 낡은 합계 위에 0009 를 **소유자 롤**로 적용 — 백필이 실제로 고치는가 ─────
# 0008 까지를 소유자 롤(비superuser·NOBYPASSRLS — ops/app-role.sql 의 colab_owner 와 같은 성질)로
# 세우고, superuser 로 낡은 값을 심은 뒤(FORCE RLS 아래에서는 소유자가 두 연구실을 못 심는다),
# 0008→0009 를 다시 소유자 롤로 적용한다. FORCE RLS 창이 없으면 소유자는 `current_lab_id()` 가
# NULL 이라 d3_file 을 한 행도 못 보고 **전부 0 으로 백필**한다 — 그 실패가 여기서 잡힌다.
docker exec "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d postgres \
  -c "CREATE ROLE s1db_owner LOGIN NOSUPERUSER NOBYPASSRLS" >/dev/null \
  || red "㈑ 소유자 롤을 만들지 못했다."
mkdb -O s1db_owner backfill_db
psql_as s1db_owner backfill_db "$TMP/prev.sql" || red "㈑ 0008 까지를 소유자 롤로 적용하지 못했다."
docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d backfill_db <<'SQL' || red "㈑ 낡은 합계 시드가 들어가지 않았다 — 시험 재료 문제."
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000S', 'S 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('00000000000000000000000SP1', '0000000000000000000000000S', 'S 교수', 'prof@s.example');
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id) VALUES
  ('0000000000000000000000DSS1', '0000000000000000000000000S', '00000000000000000000000SP1', '00000000000000000000000SP1'),
  ('0000000000000000000000DSS2', '0000000000000000000000000S', '00000000000000000000000SP1', '00000000000000000000000SP1');
-- DSS1: 손으로 적은 999 (실제 조각 50+50=100) · DSS2: NULL (조각 1건, size NULL → 0)
INSERT INTO d3_dataset_autometa (dataset_id, lab_id, total_size_bytes) VALUES
  ('0000000000000000000000DSS1', '0000000000000000000000000S', 999),
  ('0000000000000000000000DSS2', '0000000000000000000000000S', NULL);
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key, carries_lat, carries_lon) VALUES
  ('00000000000000000000000SF1', '0000000000000000000000000S', '0000000000000000000000DSS1', '본체',            's1.csv',  50,   'k/s1',  false, false),
  ('00000000000000000000000SF2', '0000000000000000000000000S', '0000000000000000000000DSS1', '기준 격자 파일', 's1g.nc',  50,   'k/s1g', true,  true),
  ('00000000000000000000000SF3', '0000000000000000000000000S', '0000000000000000000000DSS2', '본체',            's2.csv',  NULL, 'k/s2',  false, false);
SQL
out="$(psql_as s1db_owner backfill_db "$TMP/step.sql" 2>&1)"; rc=$?
if [ $rc -ne 0 ]; then
  echo "[0009-drift] ㈑ 소유자 롤로 0008→0009 적용 → red ✗"
  echo "$out" | sed 's/^/           /' | head -20
  FAILURES+=("㈑ 소유자 롤 적용")
else
  echo "$out" | grep -m1 "0009 백필" | sed 's/^/           ↳ /'
  AFTER="$(docker exec -i "$PGC" psql -tAq -U postgres -d backfill_db -c "
    SELECT string_agg(dataset_id || '=' || COALESCE(total_size_bytes::text, 'NULL'), ' ' ORDER BY dataset_id)
      FROM d3_dataset_autometa")"
  if [ "$AFTER" = "0000000000000000000000DSS1=100 0000000000000000000000DSS2=0" ]; then
    echo "[0009-drift] ㈑ 백필 전 999·NULL → 후 100·0 (소유자 롤 · FORCE RLS 창 실물) → OK"
  else
    echo "[0009-drift] ㈑ 백필 결과 '$AFTER' (기대 'DSS1=100 DSS2=0') ✗"
    FAILURES+=("㈑ 백필 값")
  fi
  oracle backfill_db green "㈑ 낡은 합계 위 0009 적용 후 — 오라클(⑥ 비어 있지 않음)"
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0009-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0009-drift green — ㈎ 적용 green · ㈏ 0009 없으면 red · ㈐ downgrade 실물 동작 + 0008 복원 · ㈑ 소유자 롤 백필 999→100·NULL→0."
