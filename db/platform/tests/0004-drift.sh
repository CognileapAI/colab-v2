#!/usr/bin/env bash
# 0004 드리프트 시험 — **0004 를 되돌리면 red 가 난다**를 기계가 증명한다 (P2-EXEC §4 W1 ⑶).
#
# 왜 이 모양인가
#   ① **실제 마이그레이션 파일을 태운다.** schema.sql 을 그대로 먹이면 「선언은 맞는데 마이그레이션이
#      틀린」 경우를 못 잡는다. 여기서는 alembic 오프라인 모드(`--sql`)로 versions/ 를 렌더해 쓴다.
#      오프라인이라 **DB 에 접속하지 않는다** — 렌더는 파일만 읽는다.
#   ② **양성과 음성을 같은 오라클로 판정한다.** 0004-assertions.sql 하나가 세 경우에 다 돈다.
#      「green 으로 시작하는 시험은 오라클이 아니다」(CLAUDE.md §4) 를 파일 두 개로 나누지 않고
#      한 파일 안에서 증명한다.
#   ③ **downgrade 를 말이 아니라 실물로 태운다.** upgrade 만 도는 마이그레이션은 되돌릴 수 없다.
#
# 세 경우
#   ㈎ head (0004 적용)        → 오라클 green 이어야 한다
#   ㈏ 0003 까지만             → 오라클 red 여야 한다   ← 「되돌리면 red」
#   ㈐ head → downgrade 0003   → 오라클 red + 0003 형태 복원 확인
#
# 원칙 (CLAUDE.md §4): 도커·alembic 이 없으면 **skip 이 아니라 red** 다.
# staging 을 건드리지 않는다 — 일회용 컨테이너는 `p2db_` 접두사이고 **호스트 포트를 하나도 열지 않는다.**
#
# 환경변수
#   COLAB_ALEMBIC   alembic 실행 파일 (기본: PATH 의 alembic)
#   COLAB_PG_IMAGE  기본 postgres:16-alpine
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN_DIR="$(cd "$HERE/.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
PG_IMAGE="${COLAB_PG_IMAGE:-postgres:16-alpine}"
HEAD_REV="0004_p2_grid_axis_and_d5"
PREV_REV="0003_p1_topic_check"

red() { echo "::error::0004-drift red — $*"; exit 1; }

command -v docker >/dev/null 2>&1 || red "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || red "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다. 못 돈 시험은 통과가 아니다."
[ -f "$HERE/0004-assertions.sql" ] || red "오라클 파일(0004-assertions.sql)이 없다."

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" p2db-drift-XXXXXX)"
PGC=""
cleanup() { [ -n "$PGC" ] && docker rm -f "$PGC" >/dev/null 2>&1; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM

# ── 1. 마이그레이션 렌더 (오프라인 — 접속하지 않는다) ────────────────────────
# URL 은 형식만 있으면 된다. 오프라인 모드는 이 주소로 접속하지 않는다.
export COLAB_PLATFORM_DB_URL="postgresql+psycopg://offline/offline"
render() { # $1=alembic 인자들 → $2 파일
  ( cd "$CHAIN_DIR" && "$ALEMBIC" $1 --sql ) > "$2" 2>"$TMP/err" \
    || { sed 's/^/     /' "$TMP/err"; red "alembic 렌더 실패: $1"; }
}
render "upgrade $HEAD_REV" "$TMP/head.sql"
render "upgrade $PREV_REV" "$TMP/prev.sql"
render "downgrade $HEAD_REV:$PREV_REV" "$TMP/down.sql"
render "upgrade $PREV_REV:$HEAD_REV" "$TMP/step.sql"

grep -q "carries_lat" "$TMP/head.sql" \
  || red "렌더된 head SQL 에 carries_lat 이 없다 — 0004 가 체인에 안 붙었거나 리비전 이름이 다르다."

# ── 2. 일회용 postgres — 포트를 열지 않는다 ─────────────────────────────────
docker image inspect "$PG_IMAGE" >/dev/null 2>&1 || docker pull -q "$PG_IMAGE" >/dev/null 2>&1 \
  || red "이미지 $PG_IMAGE 를 확보하지 못했다. skip 아님."
PGC="p2db_drift_$$_${RANDOM}"
docker run -d --rm --name "$PGC" \
  --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=p2db -e POSTGRES_HOST_AUTH_METHOD=trust \
  "$PG_IMAGE" >/dev/null 2>&1 || { PGC=""; red "일회용 postgres 를 띄우지 못했다."; }
for _ in $(seq 1 60); do docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 && break; sleep 1; done
docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 || red "postgres 가 60초 안에 뜨지 않았다."

psql_f() { docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" < "$2"; }
mkdb()   { docker exec "$PGC" createdb -U postgres "$1" >/dev/null; }

FAILURES=()
# $1=DB 이름 $2=기대(green|red) $3=라벨
oracle() {
  local out rc got
  out="$(docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" \
          < "$HERE/0004-assertions.sql" 2>&1)"; rc=$?
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$2" ]; then
    echo "[0004-drift] $3 → $got OK"
    [ "$got" = "red" ] && echo "$out" | grep -m1 "0004 오라클 실패\|ERROR" | sed 's/^/           ↳ /'
  else
    echo "[0004-drift] $3 → $got (기대 $2) ✗"
    echo "$out" | sed 's/^/           /' | head -20
    FAILURES+=("$3")
  fi
  return 0
}

# ── ㈎ 0004 적용 ────────────────────────────────────────────────────────────
mkdb head_db;  psql_f head_db "$TMP/head.sql" || red "head 마이그레이션이 적용되지 않았다."
oracle head_db green "㈎ 0004 적용 후 — 오라클"

# ── ㈏ 0003 까지만 (0004 없음) ──────────────────────────────────────────────
mkdb prev_db;  psql_f prev_db "$TMP/prev.sql" || red "0003 마이그레이션이 적용되지 않았다."
oracle prev_db red "㈏ 0004 없음 — 오라클이 red 를 내는가"

# ── ㈐ head → downgrade → 0003 ──────────────────────────────────────────────
mkdb down_db;  psql_f down_db "$TMP/head.sql" || red "head 적용 실패(㈐)."
psql_f down_db "$TMP/down.sql" || red "downgrade 가 실제로 돌지 않았다 — 되돌릴 수 없는 마이그레이션이다."
oracle down_db red "㈐ downgrade 후 — 오라클이 red 를 내는가"

# downgrade 가 **원래 모양**으로 되돌렸는가 (지우기만 한 게 아니라 옛 인덱스까지 복원)
SHAPE="$(docker exec -i "$PGC" psql -tAq -U postgres -d down_db -c "
  SELECT
    (SELECT count(*) FROM information_schema.columns
      WHERE table_name='d3_file' AND column_name IN ('carries_lat','carries_lon')) || '/' ||
    (SELECT count(*) FROM pg_indexes
      WHERE tablename='d3_file' AND indexname='d3_file_one_reference_grid_per_dataset') || '/' ||
    (SELECT count(*) FROM pg_class
      WHERE relnamespace='public'::regnamespace
        AND relname IN ('d5_upload','d5_upload_file','d5_pipeline_event'))")"
if [ "$SHAPE" = "0/1/0" ]; then
  echo "[0004-drift] ㈐ downgrade 형태 복원(축 열 0 · 옛 인덱스 1 · d5 표 0) → OK"
else
  echo "[0004-drift] ㈐ downgrade 형태 복원 → '$SHAPE' (기대 '0/1/0') ✗"
  FAILURES+=("㈐ downgrade 형태 복원")
fi

# downgrade 뒤의 스키마가 0003 상태와 **같은가** — 「지웠다」와 「되돌렸다」는 다르다.
docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d down_db \
  | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' > "$TMP/down.norm"
docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d prev_db \
  | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' > "$TMP/prev.norm"
if diff -u "$TMP/prev.norm" "$TMP/down.norm" > "$TMP/shape.diff"; then
  echo "[0004-drift] ㈐ downgrade 결과 = 0003 상태 (pg_dump 동일) → OK"
else
  echo "[0004-drift] ㈐ downgrade 결과가 0003 상태와 다르다 ✗"
  sed 's/^/           /' "$TMP/shape.diff" | head -40
  FAILURES+=("㈐ downgrade = 0003 동일성")
fi

# ── ㈑ 기존 격자 파일 1건 상태에서 0004 를 적용 — PRECOUNT 가아 apply 자체를 막는가 ──────
# 이 경우는 오라클(0004-assertions.sql)로 재지 않는다 — 적용이 되면 오라클을 돌릴 DB 도 없다.
# apply(head.sql) 그 자체의 성패와 메시지가 판정 대상이다.
mkdb seed_db; psql_f seed_db "$TMP/prev.sql" || red "0003 마이그레이션이 적용되지 않았다(㈑ 준비)."
docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d seed_db <<'SQL' || red "㈑ 시드 삽입이 실패했다 — 시험 재료 문제."
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000T', 'T 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('00000000000000000000000TP1', '0000000000000000000000000T', 'T 교수', 'prof@t.example');
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id,
                        uploaded_at, last_modified_at) VALUES
  ('0000000000000000000000DST1', '0000000000000000000000000T', '00000000000000000000000TP1',
   '00000000000000000000000TP1', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, storage_key) VALUES
  ('0000000000000000000000GRD1', '0000000000000000000000000T', '0000000000000000000000DST1',
   '기준 격자 파일', 'grid.dat', 'k/grid');
SQL
out="$(psql_f seed_db "$TMP/step.sql" 2>&1)"; rc=$?
if [ $rc -eq 0 ]; then
  FAILURES+=("㈑ 기존 격자 1건인데 0004 적용이 통과했다 — PRECOUNT 가드가 안 걸렸다")
  echo "[0004-drift] ㈑ 기존 격자 1건 → apply green (기대 red) ✗"
elif echo "$out" | grep -q "축(carries_lat·carries_lon)을 채울 근거가 없다"; then
  echo "[0004-drift] ㈑ 기존 격자 1건 → apply red, PRECOUNT 가드 발동 OK"
  echo "$out" | grep -m1 "축(carries_lat·carries_lon)을 채울 근거가 없다" | sed 's/^/           ↳ /'
else
  FAILURES+=("㈑ apply 가 실패했지만 PRECOUNT 가드 메시지가 아니다 — 엉뚱한 이유의 red")
  echo "[0004-drift] ㈑ apply red 이나 원인 불명 ✗"
  echo "$out" | sed 's/^/           /' | head -20
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0004-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0004-drift green — ㈎ 적용 green · ㈏ 0004 없으면 red · ㈐ downgrade 실물 동작 + 0003 복원 · ㈑ 기존 격자 1건이면 apply 자체가 가드로 막힌다."
