#!/usr/bin/env bash
# 0009 오라클 — 실무자 사례 어휘 13행. 배치는 `db/platform/tests/0031-drift.sh` 와 같다
# (같은 실패를 두 번 배우지 않는다). 한 줄 회차라 두 순서 갈래는 없다 — 그 자리는
# `0007-drift.sh` 가 이미 재고 있고, 이 파일은 **이 회차가 무엇을 더하는가**를 잰다.
#
#   ⓪ 델타 정적 판정 — 이 회차의 렌더에 **DDL 이 없고** 개념 그래프를 건드리지 않는다
#   ㈎ head(0009) 적용 → 오라클 SQL 통과
#   ㈏ prev(0008) 판에서는 같은 오라클이 **실패해야** 한다 — 「되돌리면 red 가 나는가」
#   ㈐ downgrade 실물 동작 — 0008 shape·행 복원 ＋ 그 판에서 오라클이 실패
#   ㈑ 선언 정본(`db/ai/schema.sql`) = **체인 head** (schema-diff 가 보는 것과 같은 사실)
#
# ⚠ ㈑ 이 견주는 상대는 체인 head 이지 이 회차가 아니다 — `schema.sql` 은 체인 전체의 선언
#   정본이다(`0006-drift.sh` · `0007-drift.sh` ㈑ 와 같은 배치). 지금은 이 회차가 head 다.
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

REV="0009_practitioner_lexicon"
PREV_REV="0008_dataset_knowledge"

red(){ echo "::error::0009-drift red — $*"; exit 1; }
ready(){ echo "::error::0009-drift red(준비) — $*"; exit 78; }

command -v docker >/dev/null 2>&1 || ready "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || [ -x "$ALEMBIC" ] || ready "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다."

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" k1bdb-drift9-XXXXXX)"; PGC=""
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
# 이 회차가 더하는 것이 비면 아래 DB 판정은 볼 것이 없다.
for token in 강수량 precipitation 한반도 충청권; do
  grep -q "$token" "$TMP/delta.sql" || red "델타에 «$token» 이 없다 — 받을 것이 비었다."
done
# 스키마 무변경이 이 회차의 승인 범위다(intent §영향 범위). DDL 이 섞이면 새 회차다.
if grep -qiE '^[[:space:]]*(CREATE|ALTER|DROP)[[:space:]]+(TABLE|INDEX|SCHEMA|DOMAIN|POLICY|TYPE|CONSTRAINT)' "$TMP/delta.sql"; then
  grep -inE '^[[:space:]]*(CREATE|ALTER|DROP)[[:space:]]+(TABLE|INDEX|SCHEMA|DOMAIN|POLICY|TYPE|CONSTRAINT)' "$TMP/delta.sql" | sed 's/^/     /' | head -10
  red "델타에 DDL 이 있다 — 이 회차의 승인 범위는 **스키마 무변경**이다."
fi
# 결정 4·5 는 보류다. 개념 그래프로 가는 글자가 델타에 나타나면 그 보류가 깨진 것이다.
if grep -qE 'd9_concept' "$TMP/delta.sql"; then
  red "델타가 d9_concept* 를 건드린다 — 결정 4·5 는 보류 상태다."
fi
echo "[0009-drift] ⓪ 델타 = 동의어 9 ＋ 별칭 4 · DDL 0 · 개념 그래프 무변경 → OK"

docker image inspect "$IMAGE" >/dev/null 2>&1 || docker pull -q "$IMAGE" >/dev/null 2>&1 \
  || ready "이미지 $IMAGE 를 확보하지 못했다."
PGC="k1bdb_0009_$$_${RANDOM}"
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
          -c "SELECT 'syn', synonym, topic FROM d9_topic_synonym
              UNION ALL SELECT 'plc', alias, place_name FROM d9_place_alias ORDER BY 1,2" \
          > "$TMP/$1.rows"; }

FAILURES=()

# ── ㈎ head 적용 → 오라클 통과 ───────────────────────────────────────────────
mkdb head_db
apply head_db "$TMP/head.sql"             || red "$REV 적용 실패(㈎)."
apply head_db "$HERE/0009-assertions.sql" || red "㈎ head 에서 오라클이 실패했다 — 이 회차가 주장을 지키지 못한다."
echo "[0009-drift] ㈎ head 적용 ＋ 오라클 통과 → OK"

# ── ㈏ 이전 head 에서는 같은 오라클이 **실패해야** 한다 ──────────────────────
# 여기가 통과하면 오라클은 이 회차에 대해 아무것도 말하지 않는다(0008 에서도 통과하므로).
mkdb prev_db
apply prev_db "$TMP/prev.sql" || red "$PREV_REV 적용 실패(㈏)."
if apply prev_db "$HERE/0009-assertions.sql" >/dev/null 2>&1; then
  echo "[0009-drift] ㈏ 0008 판이 오라클을 통과했다 — 오라클이 이 회차를 재지 않는다 ✗"
  FAILURES+=("㈏ 0008 에서 오라클 통과")
else
  echo "[0009-drift] ㈏ 0008 판에서 오라클 실패(기대) → OK"
fi

# ── ㈐ downgrade 실물 동작 ＋ 0008 복원 ──────────────────────────────────────
mkdb down_db
apply down_db "$TMP/head.sql" || red "down 판 head 적용 실패(㈐)."
apply down_db "$TMP/down.sql" || red "downgrade 적용 실패(㈐) — 되돌릴 수 없는 회차다."
if apply down_db "$HERE/0009-assertions.sql" >/dev/null 2>&1; then
  echo "[0009-drift] ㈐ downgrade 판이 오라클을 통과했다 — 되돌려도 red 가 안 난다 ✗"
  FAILURES+=("㈐ downgrade 에서 오라클 통과")
fi
norm prev_db; norm down_db
if diff -u "$TMP/prev_db.norm" "$TMP/down_db.norm" > "$TMP/shape.diff"; then
  echo "[0009-drift] ㈐ downgrade 결과 = 0008 shape (pg_dump 차이 0줄) → OK"
else
  echo "[0009-drift] ㈐ downgrade 결과가 0008 shape 와 다르다 ✗"
  sed 's/^/           /' "$TMP/shape.diff" | head -60
  FAILURES+=("㈐ downgrade = 0008 shape")
fi
# 이 회차는 **행**을 넣는 회차다. shape 만 보면 downgrade 가 아무것도 안 해도 통과한다.
rows prev_db; rows down_db
if diff -u "$TMP/prev_db.rows" "$TMP/down_db.rows" > "$TMP/rows.diff"; then
  echo "[0009-drift] ㈐ downgrade 결과 = 0008 행 집합 ($(wc -l < "$TMP/prev_db.rows")행 동일) → OK"
else
  echo "[0009-drift] ㈐ downgrade 뒤에도 이 회차의 행이 남았다 ✗"
  sed 's/^/           /' "$TMP/rows.diff" | head -40
  FAILURES+=("㈐ downgrade = 0008 행 집합")
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
  echo "[0009-drift] ㈑ 선언 정본 schema.sql = 체인 head($CHAIN_HEAD_REV) → OK"
else
  echo "[0009-drift] ㈑ schema.sql 과 체인 head 가 갈렸다 ✗"
  sed 's/^/           /' "$TMP/decl.diff" | head -60
  FAILURES+=("㈑ schema.sql ↔ 체인 head")
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0009-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0009-drift green — 델타 DDL 0 · head 오라클 통과 · 0008·downgrade 판에서 실패 · 행 복원 · 선언 = 체인 head."
