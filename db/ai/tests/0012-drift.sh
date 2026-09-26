#!/usr/bin/env bash
# 0012 오라클 — Ted 판정 2026-09-26 「자료 지역 확정」 1 의 남한 노드·포함 엣지·별칭 4행.
# 배치는 `0012-drift.sh` 와 같다(같은 실패를 두 번 배우지 않는다).
#
#   ⓪ 델타 정적 판정 — 이 회차의 렌더에 **DDL 이 없고** 그래프·별칭을 **실제로 건드린다**
#   ㈎ head(0012) 적용 → 오라클 SQL 통과
#   ㈏ prev(0011) 판에서는 같은 오라클이 **실패해야** 한다 — 「되돌리면 red 가 나는가」
#   ㈐ downgrade 실물 동작 — 0011 shape·행(그래프 ＋ 지명 별칭) 복원 ＋ 그 판에서 오라클이 실패
#   ㈑ 선언 정본(`db/ai/schema.sql`) = **체인 head** (schema-diff 가 보는 것과 같은 사실)
#
# 원칙 (CLAUDE.md §4): 도커·alembic 이 없으면 **skip 이 아니라 red(준비 · 78)** 다.
# staging 을 건드리지 않는다 — 일회용 컨테이너는 호스트 포트를 하나도 열지 않는다.
#
# 환경변수
#   COLAB_ALEMBIC   alembic 실행 파일 (기본: PATH 의 alembic)
#   COLAB_PG_IMAGE  기본 postgres:16-alpine
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN="$(cd "$HERE/.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
IMAGE="${COLAB_PG_IMAGE:-postgres:16-alpine}"

REV="0012_region_south_korea"
PREV_REV="0011_d10_model_call_ledger"

red(){ echo "::error::0012-drift red — $*"; exit 1; }
ready(){ echo "::error::0012-drift red(준비) — $*"; exit 78; }

command -v docker >/dev/null 2>&1 || ready "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || [ -x "$ALEMBIC" ] || ready "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다."

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" k1bdb-drift12-XXXXXX)"; PGC=""
cleanup(){ [ -z "$PGC" ] || docker rm -f "$PGC" >/dev/null 2>&1; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM

export COLAB_AI_DB_URL="postgresql+psycopg://offline/offline"
render(){ ( cd "$CHAIN" && "$ALEMBIC" $1 --sql ) >"$2" 2>"$TMP/err" \
  || { sed 's/^/     /' "$TMP/err"; red "alembic 렌더 실패: $1"; }; }

render "upgrade $REV"             "$TMP/head.sql"
render "upgrade $PREV_REV"        "$TMP/prev.sql"
render "downgrade $REV:$PREV_REV" "$TMP/down.sql"
render "upgrade $PREV_REV:$REV"   "$TMP/delta.sql"
render "upgrade head"             "$TMP/chain_head.sql"

# ── ⓪ 델타 정적 판정 — 렌더 단계에서 먼저 막는다 ────────────────────────────
# ⚠ **주석을 먼저 떼고 본다.** 적재물의 머리 주석이 금지 어휘(「~이 제공한다」 등)를 **설명하려고**
#   글자로 담고 있어서, 그것을 그대로 grep 하면 설명이 위반으로 읽힌다. 아래 판정은 전부
#   주석을 뗀 `delta.code` 를 본다 — 재는 대상은 실행되는 SQL 이지 산문이 아니다.
sed -e 's/--.*$//' "$TMP/delta.sql" > "$TMP/delta.code"

for token in p-south-korea p-korea-peninsula 남한 대한민국 '안에 있다'; do
  grep -q "$token" "$TMP/delta.code" || red "델타에 «$token» 이 없다 — 받을 것이 비었다."
done
# 이 회차의 승인 범위는 **행 추가**다. DDL 이 섞이면 새 회차다(intent §영향 범위 — (i) 무변경).
if grep -qiE '^[[:space:]]*(CREATE|ALTER|DROP)[[:space:]]+(TABLE|INDEX|SCHEMA|DOMAIN|POLICY|TYPE|CONSTRAINT)' "$TMP/delta.sql"; then
  grep -inE '^[[:space:]]*(CREATE|ALTER|DROP)[[:space:]]+(TABLE|INDEX|SCHEMA|DOMAIN|POLICY|TYPE|CONSTRAINT)' "$TMP/delta.sql" | sed 's/^/     /' | head -10
  red "델타에 DDL 이 있다 — 이 회차의 승인 범위는 **스키마 무변경**이다."
fi
grep -q 'd9_place_alias' "$TMP/delta.code" || red "델타가 d9_place_alias 를 건드리지 않는다 — 별칭 남한·대한민국이 빠졌다."
grep -q 'd9_concept_edge' "$TMP/delta.code" || red "델타가 d9_concept_edge 를 건드리지 않는다 — 남한⊂한반도 엣지가 빠졌다."
# relation CHECK 3값은 그대로다(2026-09-18 결정 8). 새 관계값이 델타에 나타나면 그 판정이 깨진 것이다.
for banned in '~이 제공한다' '~을 관측한다' '~에서 가공되었다' '~을 보정한다'; do
  if grep -q "$banned" "$TMP/delta.code"; then
    red "델타에 «$banned» 가 있다 — relation CHECK 는 열리지 않았다."
  fi
done
echo "[0012-drift] ⓪ 델타 = 노드 1 ＋ 엣지 1 ＋ 별칭 2 · DDL 0 · 새 relation 0 → OK"

docker image inspect "$IMAGE" >/dev/null 2>&1 || docker pull -q "$IMAGE" >/dev/null 2>&1 \
  || ready "이미지 $IMAGE 를 확보하지 못했다."
PGC="k1bdb_0012_$$_${RANDOM}"
docker run -d --rm --name "$PGC" --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=x -e POSTGRES_HOST_AUTH_METHOD=trust "$IMAGE" >/dev/null 2>&1 \
  || { PGC=""; ready "일회용 postgres 를 띄우지 못했다."; }
for _ in $(seq 1 60); do docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 && break; sleep 1; done
docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 || ready "postgres 가 60초 안에 뜨지 않았다."

apply(){ docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" <"$2"; }
mkdb(){ docker exec "$PGC" createdb -U postgres "$1" >/dev/null; }
norm(){ docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$1" \
          | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' \
          | grep -v 'alembic_version_ai' > "$TMP/$1.norm"; }
rows(){ docker exec "$PGC" psql -q -At -F '|' -v ON_ERROR_STOP=1 -U postgres -d "$1" \
          -c "SELECT 'node', concept_id, kind, label, source_grade::text FROM d9_concept
              UNION ALL SELECT 'edge', src, relation, dst, source_grade::text FROM d9_concept_edge
              UNION ALL SELECT 'alias', alias, place_name, '', '' FROM d9_place_alias
              ORDER BY 1,2,3,4" > "$TMP/$1.rows"; }

FAILURES=()

# ── ㈎ head 적용 → 오라클 통과 ───────────────────────────────────────────────
mkdb head_db
apply head_db "$TMP/head.sql"             || red "$REV 적용 실패(㈎)."
apply head_db "$HERE/0012-assertions.sql" || red "㈎ head 에서 오라클이 실패했다 — 이 회차가 주장을 지키지 못한다."
echo "[0012-drift] ㈎ head 적용 ＋ 오라클 통과 → OK"

# ── ㈏ 이전 head 에서는 같은 오라클이 **실패해야** 한다 ──────────────────────
mkdb prev_db
apply prev_db "$TMP/prev.sql" || red "$PREV_REV 적용 실패(㈏)."
if apply prev_db "$HERE/0012-assertions.sql" >/dev/null 2>&1; then
  echo "[0012-drift] ㈏ 0011 판이 오라클을 통과했다 — 오라클이 이 회차를 재지 않는다 ✗"
  FAILURES+=("㈏ 0011 에서 오라클 통과")
else
  echo "[0012-drift] ㈏ 0011 판에서 오라클 실패(기대) → OK"
fi

# ── ㈐ downgrade 실물 동작 ＋ 0011 복원 ──────────────────────────────────────
mkdb down_db
apply down_db "$TMP/head.sql" || red "down 판 head 적용 실패(㈐)."
apply down_db "$TMP/down.sql" || red "downgrade 적용 실패(㈐) — 되돌릴 수 없는 회차다."
if apply down_db "$HERE/0012-assertions.sql" >/dev/null 2>&1; then
  echo "[0012-drift] ㈐ downgrade 판이 오라클을 통과했다 — 되돌려도 red 가 안 난다 ✗"
  FAILURES+=("㈐ downgrade 에서 오라클 통과")
fi
norm prev_db; norm down_db
if diff -u "$TMP/prev_db.norm" "$TMP/down_db.norm" > "$TMP/shape.diff"; then
  echo "[0012-drift] ㈐ downgrade 결과 = 0011 shape (pg_dump 차이 0줄) → OK"
else
  echo "[0012-drift] ㈐ downgrade 결과가 0011 shape 와 다르다 ✗"
  sed 's/^/           /' "$TMP/shape.diff" | head -60
  FAILURES+=("㈐ downgrade = 0011 shape")
fi
# 이 회차는 **행**을 넣는 회차다. shape 만 보면 downgrade 가 아무것도 안 해도 통과한다.
rows prev_db; rows down_db
if diff -u "$TMP/prev_db.rows" "$TMP/down_db.rows" > "$TMP/rows.diff"; then
  echo "[0012-drift] ㈐ downgrade 결과 = 0011 그래프·별칭 행 집합 ($(wc -l < "$TMP/prev_db.rows")행 동일) → OK"
else
  echo "[0012-drift] ㈐ downgrade 뒤에도 이 회차의 행이 남았다 ✗"
  sed 's/^/           /' "$TMP/rows.diff" | head -40
  FAILURES+=("㈐ downgrade = 0011 그래프·별칭 행 집합")
fi

# ── ㈑ 선언 정본 ↔ 체인 head ────────────────────────────────────────────────
HEADS="$( cd "$CHAIN" && "$ALEMBIC" heads 2>"$TMP/heads.err" )" \
  || { sed 's/^/     /' "$TMP/heads.err"; red "alembic heads 를 읽지 못했다."; }
HEAD_COUNT="$(printf '%s\n' "$HEADS" | grep -c '[^[:space:]]')"
[ "$HEAD_COUNT" = "1" ] || red "체인 head 가 $HEAD_COUNT 개다 — 머지 리비전이 필요하다:
$HEADS"
CHAIN_HEAD_REV="$(printf '%s\n' "$HEADS" | awk 'NF{print $1; exit}')"
grep -q "$CHAIN_HEAD_REV" "$TMP/chain_head.sql" \
  || red "체인 head 렌더에 head 리비전($CHAIN_HEAD_REV)이 없다 — 렌더가 도중에 멈췄다."

mkdb chain_db; apply chain_db "$TMP/chain_head.sql" || red "체인 head 를 적용하지 못했다."
mkdb decl_db;  apply decl_db "$CHAIN/schema.sql"    || red "schema.sql 를 적용하지 못했다."
norm chain_db; norm decl_db
if diff -u "$TMP/decl_db.norm" "$TMP/chain_db.norm" > "$TMP/decl.diff"; then
  echo "[0012-drift] ㈑ 선언 정본 schema.sql = 체인 head($CHAIN_HEAD_REV) → OK"
else
  echo "[0012-drift] ㈑ schema.sql 과 체인 head 가 갈렸다 ✗"
  sed 's/^/           /' "$TMP/decl.diff" | head -60
  FAILURES+=("㈑ schema.sql ↔ 체인 head")
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0012-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0012-drift green — 델타 DDL 0 · head 오라클 통과 · 0011·downgrade 판에서 실패 · 그래프·별칭 행 복원 · 선언 = 체인 head."
