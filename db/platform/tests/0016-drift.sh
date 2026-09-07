#!/usr/bin/env bash
# 0016 드리프트 시험 — **0016 을 되돌리면 red 가 난다**를 기계가 증명한다.
# 형태는 0015-drift.sh 와 같다(같은 실패를 두 번 배우지 않는다). 다른 것은 ㈑ 의 방향이다 —
# 0015 는 「backfill 을 안 했는가」를 쟀고, 0016 은 **「이관을 순서·대표까지 했는가」**를 잰다.
#
#   ㈎ head (0016 적용)        → 구조 오라클 green
#   ㈏ 0015 까지만             → 구조 오라클 red     ← 「되돌리면 red」
#   ㈐ head → downgrade 0015   → 구조 오라클 red + pg_dump 로 0015 형태 복원 확인
#   ㈑ 0015 에 기존 행을 심고 → 0015:0016 델타를 **소유자 롤(NOSUPERUSER NOBYPASSRLS)로**
#      적용 → **기존 행 오라클 green**
#      (3원소 → 3행 순서대로 · 첫 행만 대표 · 빈 배열 0행 · 원본 배열 무변 · 검색 무변).
#      그리고 **대표를 첫 행에서 떼어 놓은** DB 에서는 그 오라클이 red 다
#      (오라클이 오라클임의 증명 — 「옮겼다」와 「순서·대표까지 옮겼다」를 가른다)
#   ㈑-c 같은 소유자 롤에 **수정 전 델타**(원천 NO FORCE 구간 없음)를 적용 → 이관 0행 → red
#      (실배포 롤에서 이관이 0행이 되는 결함을 기계가 잰다. superuser 로 적용하면 RLS 를
#       무조건 우회해 이 대조군이 green 이 되고, 그때 ㈑ 는 수용 기준의 증거가 아니다)
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
HEAD_REV="0016_rb2_dataset_variable"
PREV_REV="0015_rb1_axes_category_type_lv"

red() { echo "::error::0016-drift red — $*"; exit 1; }

command -v docker >/dev/null 2>&1 || red "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || red "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다. 못 돈 시험은 통과가 아니다."
for f in 0016-assertions.sql 0016-existing-rows-seed.sql 0016-existing-rows-assertions.sql; do
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

# 표·색인·정책이 **한 리비전 안에** 있는가. 하나라도 빠지면 이름이 다르거나 체인이 갈린 것이다.
for token in d3_dataset_variable d3_dataset_variable_representative_idx lab_boundary; do
  grep -q "$token" "$TMP/delta.sql" \
    || red "렌더된 델타 SQL 에 $token 이 없다 — 0016 이 체인에 안 붙었거나 표·색인·정책이 갈렸다."
done

# **이관이 있다** — 이 회차의 알맹이다. 0015 와 방향이 반대라 여기서는 `INSERT … SELECT` 가
# 없으면 red 다(열만 세우고 기존 배열을 안 옮기면 이관이 없는 것이다).
# ⚠ `alembic_version_platform` 갱신 한 줄은 **장부 도장**이라 데이터가 아니다 — 빼고 센다.
MIGRATED="$(grep -iE '^[[:space:]]*INSERT[[:space:]]+INTO[[:space:]]+d3_dataset_variable' "$TMP/delta.sql")"
[ -n "$MIGRATED" ] \
  || red "0015→0016 델타에 d3_dataset_variable 로의 이관 INSERT 가 없다 — 표만 세우고 기존 배열을 안 옮겼다."

# **색인식을 안 건드렸다** — `M-10` 은 이 파일 밖이다(R-B-2 · WU-B7).
if grep -qiE 'search_vector' "$TMP/delta.sql"; then
  grep -inE 'search_vector' "$TMP/delta.sql" | sed 's/^/     /' | head -5
  red "0015→0016 델타가 search_vector 를 건드린다 — 색인 재정의는 M-10 소속이다."
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

# ── 소유자 롤 — **실배포의 마이그레이터와 같은 자격**이다 ──────────────────────────
# `infra/dev/db-bootstrap.sh` 의 `colab_owner` 가 NOSUPERUSER · NOBYPASSRLS 다. superuser
# `postgres` 로 델타를 적용하면 RLS 를 무조건 우회하므로 「FORCE 원천을 못 읽어 0행 이관」
# 결함이 시험에 안 잡힌다. 그래서 ㈑ 계열은 이 롤로 적용한다.
docker exec "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d postgres \
  -c "CREATE ROLE t_owner LOGIN NOSUPERUSER NOBYPASSRLS;" >/dev/null \
  || red "소유자 롤 t_owner 를 만들지 못했다."

# `REASSIGN OWNED BY postgres` 는 부트스트랩 superuser 라 거부된다 — public 스키마의
# 객체만 하나씩 넘긴다(표·시퀀스·뷰 · 함수 · 도메인/타입 ＋ 스키마 ＋ DB).
handover() {  # $1=DB — 그 DB 의 public 객체·DB 소유권을 t_owner 로 넘긴다
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
    echo "[0016-drift] $3 → $got OK"
    [ "$got" = "red" ] && echo "$out" | grep -m1 "0016 오라클 실패\|0016 기존 행 오라클 실패\|ERROR" | sed 's/^/           ↳ /'
  else
    echo "[0016-drift] $3 → $got (기대 $2) ✗"
    echo "$out" | sed 's/^/           /' | head -20
    FAILURES+=("$3")
  fi
  return 0
}

# ── ㈎ 0016 적용 ────────────────────────────────────────────────────────────
mkdb head_db;  psql_f head_db "$TMP/head.sql" || red "head 마이그레이션이 적용되지 않았다."
oracle head_db green "㈎ 0016 적용 후 — 구조 오라클" 0016-assertions.sql

# ── ㈏ 0015 까지만 (0016 없음) ──────────────────────────────────────────────
mkdb prev_db;  psql_f prev_db "$TMP/prev.sql" || red "0015 마이그레이션이 적용되지 않았다."
oracle prev_db red "㈏ 0016 없음 — 오라클이 red 를 내는가" 0016-assertions.sql

# ── ㈐ head → downgrade → 0015 ──────────────────────────────────────────────
mkdb down_db;  psql_f down_db "$TMP/head.sql" || red "head 적용 실패(㈐)."
psql_f down_db "$TMP/down.sql" || red "downgrade 가 실제로 돌지 않았다 — 되돌릴 수 없는 마이그레이션이다."
oracle down_db red "㈐ downgrade 후 — 오라클이 red 를 내는가" 0016-assertions.sql

# 「지웠다」와 「되돌렸다」는 다르다 — 0015 상태와 스키마가 같은가.
for db in down_db prev_db; do
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$db" \
    | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' > "$TMP/$db.norm"
done
if diff -u "$TMP/prev_db.norm" "$TMP/down_db.norm" > "$TMP/shape.diff"; then
  echo "[0016-drift] ㈐ downgrade 결과 = 0015 상태 (pg_dump 동일) → OK"
else
  echo "[0016-drift] ㈐ downgrade 결과가 0015 상태와 다르다 ✗"
  sed 's/^/           /' "$TMP/shape.diff" | head -40
  FAILURES+=("㈐ downgrade = 0015 동일성")
fi

# ── ㈑ 기존 행 — **적재된 배열 위에서 순서·대표까지 옮기는 것**이 이 회차의 알맹이다 ──
# 0015 상태에 기존 행을 심고, 그 위에 0015→0016 델타만 적용한다. 실제 배포와 같은 순서다.
mkdb keep_db;  psql_f keep_db "$TMP/prev.sql"          || red "0015 적용 실패(㈑)."
psql_f keep_db "$HERE/0016-existing-rows-seed.sql"     || red "기존 행 재료를 심지 못했다(㈑)."
handover keep_db
psql_owner keep_db "$TMP/delta.sql"                    || red "0015→0016 델타가 소유자 롤에서 돌지 않았다(㈑)."
oracle keep_db green "㈑ 기존 행(소유자 롤 적용) — 3원소가 순서대로 3행이 되고 첫 행이 대표인가" \
       0016-existing-rows-assertions.sql

# 오라클이 오라클임의 증명 — **대표를 첫 행에서 떼면 red** 여야 한다.
# 「옮겼다」만 재는 오라클이면 이 대조군도 green 이 되고, 그 순간 수용 기준의 「첫 행만
# 대표다」가 아무에게도 안 걸린다.
mkdb moved_db; psql_f moved_db "$TMP/prev.sql"         || red "0015 적용 실패(㈑-b)."
psql_f moved_db "$HERE/0016-existing-rows-seed.sql"    || red "기존 행 재료를 심지 못했다(㈑-b)."
handover moved_db
psql_owner moved_db "$TMP/delta.sql"                   || red "델타 적용 실패(㈑-b)."
docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d moved_db \
  -c "SET app.current_lab = '0000000000000000000000000T';
      UPDATE d3_dataset_variable SET is_representative = false
       WHERE dataset_id = '000000000000000000000DSV1A' AND ordinal = 1;
      UPDATE d3_dataset_variable SET is_representative = true
       WHERE dataset_id = '000000000000000000000DSV1A' AND ordinal = 2;" >/dev/null \
  || red "대표 이동 대조군을 만들지 못했다(㈑-b)."
oracle moved_db red "㈑-b 대표를 둘째 행으로 옮김 — 오라클이 red 를 내는가" \
       0016-existing-rows-assertions.sql

# ── ㈑-c 대조군 — **수정 전 델타**(원천 NO FORCE 구간 없음)를 같은 소유자 롤로 ──────────
# 델타에서 원천의 `NO FORCE` 한 줄만 지우면 수정 전 마이그레이션과 같은 자리가 된다.
# 그 상태의 소유자 롤은 `current_lab_id()` 가 NULL 이라 원천을 0행으로 읽고, INSERT 가
# **오류 없이 0행**으로 끝난다 → 기존 행 오라클 red. 이 대조군이 green 이 되면 시험이
# 결함을 못 재는 것이므로 그때는 ㈑ 도 증거가 아니다.
grep -v 'd3_dataset_autometa NO FORCE ROW LEVEL SECURITY' "$TMP/delta.sql" > "$TMP/delta-nofix.sql"
if diff -q "$TMP/delta.sql" "$TMP/delta-nofix.sql" >/dev/null; then
  red "델타에 원천 d3_dataset_autometa 의 NO FORCE 구간이 없다 — 마이그레이션이 FORCE 원천을 그대로 읽는다(실배포 0행 이관)."
fi
mkdb nofix_db; psql_f nofix_db "$TMP/prev.sql"         || red "0015 적용 실패(㈑-c)."
psql_f nofix_db "$HERE/0016-existing-rows-seed.sql"    || red "기존 행 재료를 심지 못했다(㈑-c)."
handover nofix_db
psql_owner nofix_db "$TMP/delta-nofix.sql"             || red "수정 전 델타가 돌지 않았다(㈑-c) — 대조군은 오류 없이 0행으로 끝나야 한다."
oracle nofix_db red "㈑-c 수정 전 델타(소유자 롤) — 이관 0행으로 오라클이 red 를 내는가" \
       0016-existing-rows-assertions.sql

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0016-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0016-drift green — ㈎ 적용 green · ㈏ 0016 없으면 red · ㈐ downgrade 실물 동작 + 0015 복원 · ㈑ 소유자 롤 이관 green(대조군 ㈑-b 대표 이동 red · ㈑-c 수정 전 델타 0행 red)."
