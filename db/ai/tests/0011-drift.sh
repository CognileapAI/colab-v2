#!/usr/bin/env bash
# 0011 드리프트 시험 — **원장 표를 되돌리면 오라클이 red 를 낸다**를 기계가 증명한다.
# ⭑ ⟨재번호 2026-09-25⟩ 처음에는 0008(부모 0007)이었다 — AI 검색 갈래(0008~0010)와 합치며 0011(부모 0010)로 옮겼다.
# 형태는 db/ai/tests/0006-drift.sh 와 같다 (같은 실패를 두 번 배우지 않는다).
#
#   ㈎ head (0011 적용)        → 오라클 green (닫힌 어휘가 실제로 거절 · 정상 행 통과 · 조회 캐시율)
#   ㈏ 0010 까지만             → 오라클 red     ← 「되돌리면 red」
#   ㈐ head → downgrade 0010   → 오라클 red + pg_dump 로 0010 형태 복원 확인
#   ㈑ 선언 정본(`db/ai/schema.sql`) = 마이그레이션 결과 (schema-diff 가 보는 것과 같은 사실)
#   ㈒ **델타가 담지 않기로 한 것을 담지 않는다** — 리전·캐시율·질의/검색어 칸이 없다
#
# ⚠ **㈒ 를 따로 두는 이유.** ㈎ 는 「표가 제 일을 하는가」를 보고, ㈑ 는 「두 쪽이 같은가」를
#   본다. **둘 다 green 인 채로 칸이 하나 늘어날 수 있다** — 선언과 리비전을 같이 고치면
#   그만이다. 이 회차 판정의 절반은 「무엇을 넣지 않기로 했는가」이고(리전 칸 철회 ·
#   질의 원문 비저장 · 캐시율 비저장), 그 절반은 **렌더된 델타에서 직접 재야** 지켜진다.
#
# 원칙 (CLAUDE.md §4): 도커·alembic 이 없으면 **skip 이 아니라 red** 다.
# staging 을 건드리지 않는다 — 일회용 컨테이너는 `k1bdb_` 접두사이고 호스트 포트를 하나도 열지 않는다.
#
# 환경변수
#   COLAB_ALEMBIC   alembic 실행 파일 (기본: PATH 의 alembic)
#   COLAB_PG_IMAGE  기본 postgres:16-alpine
set -uo pipefail
# 준비 판정만 재사용하며 컨테이너 생성·cleanup은 이 오라클이 소유한다.
. "$(dirname "${BASH_SOURCE[0]}")/../../../gates/tools/_pg.sh"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN_DIR="$(cd "$HERE/.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
PG_IMAGE="${COLAB_PG_IMAGE:-postgres:16-alpine}"
HEAD_REV="0011_d10_model_call_ledger"
PREV_REV="0010_practitioner_concept"

red() { echo "::error::0011-drift red — $*"; exit 1; }
ready() { echo "::error::0011-drift red(준비) — $*"; exit 78; }

command -v docker >/dev/null 2>&1 || ready "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || ready "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다. 못 돈 시험은 통과가 아니다."
[ -f "$HERE/0011-assertions.sql" ] || red "오라클 파일(0011-assertions.sql)이 없다."

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" k1bdb-drift11-XXXXXX)"
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

# ── ㈒-1 델타가 실제로 이 표를 만든다 ──────────────────────────────────────
for token in 'CREATE TABLE d10_model_call' 'd10_model_call_called_at_idx' \
             'd10_model_call_site_time_idx' "'empty_by_model'" "'not_called'"; do
  grep -q "$token" "$TMP/delta.sql" || red "렌더된 델타 SQL 에 '$token' 이 없다 — 0011 이 체인에 안 붙었거나 갈렸다."
done

# ── ㈒-2 **담지 않기로 한 것이 델타에 없다** ───────────────────────────────
# ⛔ 리전 — ㊷ 근거③의 「처리 리전을 필수 필드로 기록」은 2026-09-24 Ted 판정으로 철회됐다.
grep -qiE '(^|[^a-z_])region' "$TMP/delta.sql" \
  && red "델타에 리전 칸이 있다 — 철회된 기록 의무를 되살렸다(PLAN-SoT ㊷ 추기 ②)."
# ⛔ 캐시율 — 파생값은 조회 때 계산한다. 저장하면 토큰 둘과 비율 하나가 갈릴 자리가 생긴다.
grep -qiE 'cache_hit_ratio|cache_rate|GENERATED[[:space:]]+ALWAYS' "$TMP/delta.sql" \
  && red "델타에 파생 캐시율 칸이 있다 — 이 회차는 비율을 저장하지 않는다."
# ⛔ 질의 원문·검색어·데이터셋 이름 — 원장이 사용자 질의 로그가 되는 문이다.
grep -qiE '(^|[^a-z_])(query_text|raw_query|terms|search_terms|dataset_name|rationale|api_key)' \
  "$TMP/delta.sql" \
  && red "델타에 담지 않기로 한 칸이 있다 — 판정 기록 「넣지 않는 것」 위반."
# ⛔ 이 회차는 **표 하나만** 만든다. 사전·그래프 표를 건드리면 그것은 다른 회차다.
grep -qiE 'ALTER[[:space:]]+TABLE[[:space:]]+d9_|DROP[[:space:]]+TABLE' "$TMP/delta.sql" \
  && red "델타가 기존 표를 건드린다 — 이 회차는 표 하나를 **옆에** 세울 뿐이다."
echo "[0011-drift] ㈒ 델타 = 표 1 ＋ 색인 2 · 리전·캐시율·질의 칸 0 · 기존 표 무접촉 → OK"

docker image inspect "$PG_IMAGE" >/dev/null 2>&1 || docker pull -q "$PG_IMAGE" >/dev/null 2>&1 \
  || ready "이미지 $PG_IMAGE 를 확보하지 못했다. skip 아님."
PGC="k1bdb_drift11_$$_${RANDOM}"
docker run -d --rm --name "$PGC" \
  --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=k1bdb -e POSTGRES_HOST_AUTH_METHOD=trust \
  "$PG_IMAGE" >/dev/null 2>&1 || { PGC=""; ready "일회용 postgres 를 띄우지 못했다."; }
pg_wait_ready "$PGC" 60 || ready "postgres 실서버가 60초 안에 준비되지 않았다."

psql_f() { docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" < "$2"; }
mkdb()   { docker exec "$PGC" createdb -U postgres "$1" >/dev/null; }

FAILURES=()
oracle() {   # $1=DB $2=기대 $3=라벨
  local out rc got
  out="$(docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" \
          < "$HERE/0011-assertions.sql" 2>&1)"; rc=$?
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$2" ]; then
    echo "[0011-drift] $3 → $got OK"
    [ "$got" = "red" ] && echo "$out" | grep -m1 "0011 오라클 실패\|ERROR" | sed 's/^/           ↳ /'
  else
    echo "[0011-drift] $3 → $got (기대 $2) ✗"
    echo "$out" | sed 's/^/           /' | head -20
    FAILURES+=("$3")
  fi
  return 0
}

mkdb head_db; psql_f head_db "$TMP/head.sql" || red "head 마이그레이션이 적용되지 않았다."
oracle head_db green "㈎ 0011 적용 후 — 닫힌 어휘가 실제로 거절하고 정상 행이 통과하는가"

mkdb prev_db; psql_f prev_db "$TMP/prev.sql" || red "0010 마이그레이션이 적용되지 않았다."
oracle prev_db red "㈏ 0011 없음 — 오라클이 red 를 내는가"

mkdb down_db; psql_f down_db "$TMP/head.sql" || red "head 적용 실패(㈐)."
psql_f down_db "$TMP/down.sql" || red "downgrade 가 실제로 돌지 않았다 — 되돌릴 수 없는 마이그레이션이다."
oracle down_db red "㈐ downgrade 후 — 오라클이 red 를 내는가"

# 「지웠다」와 「되돌렸다」는 다르다 — 0010 상태와 스키마가 같은가.
for db in down_db prev_db; do
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$db" \
    | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' > "$TMP/$db.norm"
done
if diff -u "$TMP/prev_db.norm" "$TMP/down_db.norm" > "$TMP/shape.diff"; then
  echo "[0011-drift] ㈐ downgrade 결과 = 0010 상태 (pg_dump 동일) → OK"
else
  echo "[0011-drift] ㈐ downgrade 결과가 0010 상태와 다르다 ✗"
  sed 's/^/           /' "$TMP/shape.diff" | head -40
  FAILURES+=("㈐ downgrade = 0010 동일성")
fi

# ㈑ 선언 정본(schema.sql) ↔ 마이그레이션 결과 (schema-diff 가 보는 것과 같은 사실).
# 견주는 상대는 **체인 head** 다 — 이 회차가 그 head 이지만, 그 사실을 여기서 가정하지 않는다
# (`0006-drift.sh` 가 갈래 하나가 되면서 배운 자리다).
render "upgrade head" "$TMP/chain_head.sql"
mkdb chain_db; psql_f chain_db "$TMP/chain_head.sql" || red "체인 head 를 적용하지 못했다."
mkdb decl_db;  psql_f decl_db "$CHAIN_DIR/schema.sql" || red "schema.sql 를 적용하지 못했다."
for db in chain_db decl_db; do
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$db" \
    | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' \
    | grep -v 'alembic_version_ai' > "$TMP/$db.decl"
done
if diff -u "$TMP/decl_db.decl" "$TMP/chain_db.decl" > "$TMP/decl.diff"; then
  echo "[0011-drift] ㈑ 선언 정본 schema.sql = 마이그레이션 결과 → OK"
else
  echo "[0011-drift] ㈑ schema.sql 과 마이그레이션 결과가 갈렸다 ✗"
  sed 's/^/           /' "$TMP/decl.diff" | head -60
  FAILURES+=("㈑ schema.sql ↔ 마이그레이션 동일성")
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0011-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0011-drift green — ㈎ 닫힌 어휘 실거절 ＋ 정상 행 통과 · ㈏㈐ 되돌리면 red · downgrade 실물 동작 · 선언 = 적용 · 리전·캐시율·질의 칸 0."
