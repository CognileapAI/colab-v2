#!/usr/bin/env bash
# 0015 드리프트 시험 — **0015 를 되돌리면 red 가 난다**를 기계가 증명한다.
# 형태는 0013-drift.sh 와 같다(같은 실패를 두 번 배우지 않는다). 다른 것은 ㈑ 의 방향이다 —
# 0013 은 「백필이 채웠는가」를 재고, 0015 는 **「backfill 을 안 했는가」**를 잰다(미결-3 ⓐ).
#
#   ㈎ head (0015 적용)        → 오라클 green
#   ㈏ 0014 까지만             → 오라클 red     ← 「되돌리면 red」
#   ㈐ head → downgrade 0014   → 오라클 red + pg_dump 로 0014 형태 복원 확인
#   ㈑ 0014 에 기존 행을 심고 → 0014:0015 델타 적용 → **기존 행 오라클 green**
#      (전 행 NULL · topic 무변). 그리고 열을 세운 뒤 **backfill 을 흉내 낸** DB 에서는
#      그 오라클이 red 다 (오라클이 오라클임의 증명 — 대조군의 방향이 0013 과 반대다)
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
HEAD_REV="0015_rb1_axes_category_type_lv"
PREV_REV="0014_merge_ra1_and_topic_vocab"

red() { echo "::error::0015-drift red — $*"; exit 1; }

command -v docker >/dev/null 2>&1 || red "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || red "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다. 못 돈 시험은 통과가 아니다."
for f in 0015-assertions.sql 0015-existing-rows-seed.sql 0015-existing-rows-assertions.sql; do
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

# 세 변경이 **한 head 안에** 있는가. 하나라도 빠지면 리비전이 갈렸거나 이름이 다른 것이다.
for token in category data_type processing_level_user_set; do
  grep -q "$token" "$TMP/head.sql" \
    || red "렌더된 head SQL 에 $token 이 없다 — 0015 가 체인에 안 붙었거나 M-1·M-2·M-3 이 한 head 가 아니다."
done

# **backfill 이 0 이다** — 이 회차의 알맹이다(미결-3 ⓐ). 델타에 데이터 `UPDATE` 가 있으면
# 그 순간 자동 매핑이 생긴 것이고, 그것은 확정 판정을 뒤집는 변경이다.
# ⚠ `alembic_version_platform` 갱신 한 줄은 **장부 도장**이라 데이터가 아니다 — 빼고 센다.
BACKFILL="$(grep -iE '^[[:space:]]*UPDATE[[:space:]]' "$TMP/delta.sql" \
              | grep -v 'alembic_version_platform')"
if [ -n "$BACKFILL" ]; then
  echo "$BACKFILL" | sed 's/^/     /' | head -5
  red "0014→0015 델타에 데이터 UPDATE 가 있다 — 자동 매핑을 만들지 않는다(미결-3 ⓐ)."
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

FAILURES=()
oracle() {   # $1=DB $2=기대(green|red) $3=라벨 $4=오라클 파일
  local out rc got
  out="$(docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" \
          < "$HERE/$4" 2>&1)"; rc=$?
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$2" ]; then
    echo "[0015-drift] $3 → $got OK"
    [ "$got" = "red" ] && echo "$out" | grep -m1 "0015 오라클 실패\|0015 기존 행 오라클 실패\|ERROR" | sed 's/^/           ↳ /'
  else
    echo "[0015-drift] $3 → $got (기대 $2) ✗"
    echo "$out" | sed 's/^/           /' | head -20
    FAILURES+=("$3")
  fi
  return 0
}

# ── ㈎ 0015 적용 ────────────────────────────────────────────────────────────
mkdb head_db;  psql_f head_db "$TMP/head.sql" || red "head 마이그레이션이 적용되지 않았다."
oracle head_db green "㈎ 0015 적용 후 — 오라클" 0015-assertions.sql

# ── ㈏ 0014 까지만 (0015 없음) ──────────────────────────────────────────────
mkdb prev_db;  psql_f prev_db "$TMP/prev.sql" || red "0014 마이그레이션이 적용되지 않았다."
oracle prev_db red "㈏ 0015 없음 — 오라클이 red 를 내는가" 0015-assertions.sql

# ── ㈐ head → downgrade → 0014 ──────────────────────────────────────────────
mkdb down_db;  psql_f down_db "$TMP/head.sql" || red "head 적용 실패(㈐)."
psql_f down_db "$TMP/down.sql" || red "downgrade 가 실제로 돌지 않았다 — 되돌릴 수 없는 마이그레이션이다."
oracle down_db red "㈐ downgrade 후 — 오라클이 red 를 내는가" 0015-assertions.sql

# 「지웠다」와 「되돌렸다」는 다르다 — 0014 상태와 스키마가 같은가.
for db in down_db prev_db; do
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$db" \
    | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' > "$TMP/$db.norm"
done
if diff -u "$TMP/prev_db.norm" "$TMP/down_db.norm" > "$TMP/shape.diff"; then
  echo "[0015-drift] ㈐ downgrade 결과 = 0014 상태 (pg_dump 동일) → OK"
else
  echo "[0015-drift] ㈐ downgrade 결과가 0014 상태와 다르다 ✗"
  sed 's/^/           /' "$TMP/shape.diff" | head -40
  FAILURES+=("㈐ downgrade = 0014 동일성")
fi

# ── ㈑ 기존 행 — **적재된 데이터 위에서 아무것도 안 채우는** 것이 이 회차의 알맹이다 ──
# 0014 상태에 기존 행을 심고, 그 위에 0014→0015 델타만 적용한다. 실제 배포와 같은 순서다.
mkdb keep_db;  psql_f keep_db "$TMP/prev.sql"          || red "0014 적용 실패(㈑)."
psql_f keep_db "$HERE/0015-existing-rows-seed.sql"     || red "기존 행 재료를 심지 못했다(㈑)."
psql_f keep_db "$TMP/delta.sql"                        || red "0014→0015 델타가 적재 데이터 위에서 돌지 않았다(㈑)."
oracle keep_db green "㈑ 기존 행 — 전 행 NULL 이고 topic 이 그대로인가" 0015-existing-rows-assertions.sql

# 오라클이 오라클임의 증명 — **backfill 을 흉내 내면 red** 여야 한다.
# ⚠ 방향이 0013 과 반대다. 거기서는 「안 채우면 red」였고 여기서는 「채우면 red」다.
mkdb filled_db; psql_f filled_db "$TMP/prev.sql"       || red "0014 적용 실패(㈑-b)."
psql_f filled_db "$HERE/0015-existing-rows-seed.sql"   || red "기존 행 재료를 심지 못했다(㈑-b)."
psql_f filled_db "$TMP/delta.sql"                      || red "델타 적용 실패(㈑-b)."
docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d filled_db \
  -c "UPDATE d3_dataset_description SET category = '기상·기후 인자' WHERE topic = '강우·강수';" >/dev/null \
  || red "자동 매핑 대조군을 만들지 못했다(㈑-b)."
oracle filled_db red "㈑-b 자동 매핑을 흉내 냄 — 오라클이 red 를 내는가" 0015-existing-rows-assertions.sql

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0015-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0015-drift green — ㈎ 적용 green · ㈏ 0015 없으면 red · ㈐ downgrade 실물 동작 + 0014 복원 · ㈑ 기존 행 전 행 NULL(대조군 red)."
