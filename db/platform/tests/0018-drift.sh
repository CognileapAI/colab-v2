#!/usr/bin/env bash
# 0018 드리프트 시험 — **0018 을 되돌리면 red 가 난다**를 기계가 증명한다.
# 형태는 0015-drift.sh 와 같다(같은 실패를 두 번 배우지 않는다). 0015 와 같은 부류인 이유 =
# **둘 다 열만 더하고 데이터를 한 줄도 안 옮긴다.** 다른 것은 ㈑ 의 방향이 아니라 **오라클이
# 재는 성질**이다 — 0015 는 「자동 매핑을 안 만들었는가」를 쟀고, 0018 은 거기에
# **「선택 입력인가 · Lv 로 갈리지 않는가」**를 더 잰다(PRD-19 의 폐기된 판정 회귀 방지).
#
#   ㈎ head (0018 적용)        → 구조 오라클 green
#   ㈏ 0017 까지만             → 구조 오라클 red     ← 「되돌리면 red」
#   ㈐ head → downgrade 0017   → 구조 오라클 red + pg_dump 로 0017 형태 복원 확인
#   ㈑ 0017 에 기존 행을 심고 → 0017:0018 델타를 **소유자 롤(NOSUPERUSER NOBYPASSRLS)로**
#      적용 → **기존 행 오라클 green** (두 칸 전 행 NULL · source_label 무변 · 수정 안 막힘)
#   ㈑-b 같은 DB 에 **백필을 흉내 냄**(source_label 을 source_url 로 옮김) → 오라클 red
#      (오라클이 오라클임의 증명 — 「열을 세웠다」와 「아무것도 안 옮겼다」를 가른다)
#
# ⭑ **`NO FORCE ROW LEVEL SECURITY` 구간이 없는 것이 정상이다.** `0017` 은 매핑 UPDATE 가
#   있어서 그 구간이 필요했고(FORCE 인 두 표를 NOBYPASSRLS 롤이 0행으로 읽는다), `0018` 은
#   **데이터 마이그레이션이 0** 이라 내릴 정책이 없다. 그래서 `0017-drift.sh` 의 ㈑-c
#   대조군(수정 전 델타 = NO FORCE 없음 → 매핑 0행)에 해당하는 자리가 이 파일에는 **없다.**
#   대신 ㈑ 를 **소유자 롤로** 적용해 「NOBYPASSRLS 마이그레이터가 이 델타를 끝까지 돌린다」를
#   실배포와 같은 자격으로 잰다 — 델타에 UPDATE 가 한 줄도 없음은 아래 BACKFILL 검사가 잰다.
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
HEAD_REV="0018_rb6_lv0_source"
PREV_REV="0017_rb4_access_state_3"

red() { echo "::error::0018-drift red — $*"; exit 1; }

command -v docker >/dev/null 2>&1 || red "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || red "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다. 못 돈 시험은 통과가 아니다."
for f in 0018-assertions.sql 0018-existing-rows-seed.sql 0018-existing-rows-assertions.sql; do
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

# **두 칸이 다 있는가.** 한쪽만 세우면 「어디서 언제」의 반쪽만 남는다.
for token in source_url source_downloaded_on; do
  grep -q "$token" "$TMP/delta.sql" \
    || red "렌더된 델타 SQL 에 $token 이 없다 — 0018 이 체인에 안 붙었거나 두 칸 중 한쪽만 세웠다."
done

# **CHECK 를 안 걸었다** — 두 칸은 선택 입력이다(PRD-19). 조건 제약을 세우는 순간
# 폐기된 완료 판정(「Lv0 이면 필수」·「Lv1 이상 400」)이 DB 층에 되살아난다.
if grep -iE 'source_url|source_downloaded_on' "$TMP/delta.sql" | grep -iqE 'CHECK|NOT NULL'; then
  grep -inE 'source_url|source_downloaded_on' "$TMP/delta.sql" | grep -iE 'CHECK|NOT NULL' \
    | sed 's/^/     /' | head -5
  red "0017→0018 델타가 출처 두 칸에 CHECK·NOT NULL 을 건다 — 두 칸은 선택 입력이다(PRD-19)."
fi

# **backfill 이 0 이다** — 이 회차의 알맹이다. `source_label` 은 출처의 이름이지 주소가
# 아니고, 내려받은 날은 어디에도 기록돼 있지 않다. 옮겨 적으면 거짓 출처가 박힌다.
# ⚠ `alembic_version_platform` 갱신 한 줄은 **장부 도장**이라 데이터가 아니다 — 빼고 센다.
BACKFILL="$(grep -iE '^[[:space:]]*UPDATE[[:space:]]' "$TMP/delta.sql" \
              | grep -v 'alembic_version_platform')"
if [ -n "$BACKFILL" ]; then
  echo "$BACKFILL" | sed 's/^/     /' | head -5
  red "0017→0018 델타에 데이터 UPDATE 가 있다 — 두 칸은 전 행 NULL 이다(PRD-19 「기존 데이터」)."
fi

# **`source_label` 과 그 색인을 안 건드렸다** — 원천 표기는 Lv 무관 상시 노출이다(미결-11 ⓐ).
if grep -qiE 'DROP +COLUMN +(IF +EXISTS +)?source_label|DROP +INDEX.*source_label' "$TMP/delta.sql"; then
  red "0017→0018 델타가 source_label 또는 그 색인을 지운다 — 원천 표기는 그대로 둔다."
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

# ── 소유자 롤 — **실배포의 마이그레이터와 같은 자격**이다 (0017-drift.sh 와 같은 장치) ────
# `infra/dev/db-bootstrap.sh` 의 `colab_owner` 가 NOSUPERUSER · NOBYPASSRLS 다. 이 회차는
# 옮길 행이 0 이라 RLS 에 막힐 UPDATE 자체가 없지만, **그 사실을 주장이 아니라 실행으로**
# 보이려면 델타를 그 자격으로 한 번 돌려 봐야 한다. superuser 로만 돌리면 「이 델타는
# NOBYPASSRLS 에서도 끝까지 간다」가 시험된 적이 없는 문장으로 남는다.
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
    echo "[0018-drift] $3 → $got OK"
    [ "$got" = "red" ] && echo "$out" | grep -m1 "0018 오라클 실패\|0018 기존 행 오라클 실패\|ERROR" | sed 's/^/           ↳ /'
  else
    echo "[0018-drift] $3 → $got (기대 $2) ✗"
    echo "$out" | sed 's/^/           /' | head -20
    FAILURES+=("$3")
  fi
  return 0
}

# ── ㈎ 0018 적용 ────────────────────────────────────────────────────────────
mkdb head_db;  psql_f head_db "$TMP/head.sql" || red "head 마이그레이션이 적용되지 않았다."
oracle head_db green "㈎ 0018 적용 후 — 구조 오라클" 0018-assertions.sql

# ── ㈏ 0017 까지만 (0018 없음) ──────────────────────────────────────────────
mkdb prev_db;  psql_f prev_db "$TMP/prev.sql" || red "0017 마이그레이션이 적용되지 않았다."
oracle prev_db red "㈏ 0018 없음 — 오라클이 red 를 내는가" 0018-assertions.sql

# ── ㈐ head → downgrade → 0017 ──────────────────────────────────────────────
mkdb down_db;  psql_f down_db "$TMP/head.sql" || red "head 적용 실패(㈐)."
psql_f down_db "$TMP/down.sql" || red "downgrade 가 실제로 돌지 않았다 — 되돌릴 수 없는 마이그레이션이다."
oracle down_db red "㈐ downgrade 후 — 오라클이 red 를 내는가" 0018-assertions.sql

# 「지웠다」와 「되돌렸다」는 다르다 — 0017 상태와 스키마가 같은가.
for db in down_db prev_db; do
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$db" \
    | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' > "$TMP/$db.norm"
done
if diff -u "$TMP/prev_db.norm" "$TMP/down_db.norm" > "$TMP/shape.diff"; then
  echo "[0018-drift] ㈐ downgrade 결과 = 0017 상태 (pg_dump 동일) → OK"
else
  echo "[0018-drift] ㈐ downgrade 결과가 0017 상태와 다르다 ✗"
  sed 's/^/           /' "$TMP/shape.diff" | head -40
  FAILURES+=("㈐ downgrade = 0017 동일성")
fi

# ── ㈑ 기존 행 — **적재된 데이터 위에서 아무것도 안 채우는** 것이 이 회차의 알맹이다 ──
# 0017 상태에 기존 행을 심고, 그 위에 0017→0018 델타만 **소유자 롤로** 적용한다.
mkdb keep_db;  psql_f keep_db "$TMP/prev.sql"          || red "0017 적용 실패(㈑)."
psql_f keep_db "$HERE/0018-existing-rows-seed.sql"     || red "기존 행 재료를 심지 못했다(㈑)."
handover keep_db
psql_owner keep_db "$TMP/delta.sql" \
  || red "0017→0018 델타가 소유자 롤(NOSUPERUSER NOBYPASSRLS)에서 돌지 않았다(㈑)."
oracle keep_db green "㈑ 기존 행(소유자 롤 적용) — 두 칸 전 행 NULL 이고 source_label 이 그대로인가" \
       0018-existing-rows-assertions.sql

# 오라클이 오라클임의 증명 — **백필을 흉내 내면 red** 여야 한다.
# `source_label`(출처의 **이름**)을 `source_url`(**주소**)로 옮기는 것이 가장 그럴듯한 오류다.
mkdb filled_db; psql_f filled_db "$TMP/prev.sql"       || red "0017 적용 실패(㈑-b)."
psql_f filled_db "$HERE/0018-existing-rows-seed.sql"   || red "기존 행 재료를 심지 못했다(㈑-b)."
handover filled_db
psql_owner filled_db "$TMP/delta.sql"                  || red "델타 적용 실패(㈑-b)."
docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d filled_db \
  -c "UPDATE d3_dataset SET source_url = source_label WHERE source_label IS NOT NULL;" >/dev/null \
  || red "백필 대조군을 만들지 못했다(㈑-b)."
oracle filled_db red "㈑-b 백필을 흉내 냄(원천 표기를 주소로 옮김) — 오라클이 red 를 내는가" \
       0018-existing-rows-assertions.sql

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0018-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0018-drift green — ㈎ 적용 green · ㈏ 0018 없으면 red · ㈐ downgrade 실물 동작 + 0017 복원 · ㈑ 소유자 롤 적용 뒤 두 칸 전 행 NULL(대조군 ㈑-b 백필 red)."
