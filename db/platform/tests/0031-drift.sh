#!/usr/bin/env bash
# 0031 오라클 — 파일 내용 리비전 ＋ 근거 붙은 검색 사실. 배치는 `0029-drift.sh` 와 같다
# (head/prev/down 세 DB). 형제가 없는 한 줄 회차라 두 순서 갈래는 없다 — 그 자리는
# `0030-drift.sh` 가 이미 재고 있고, 이 파일은 **이 회차가 무엇을 더하는가**를 잰다.
#
#   ㈎ head(0031) 적용 → 오라클 SQL 통과
#   ㈏ prev(0030 머지) 에서는 같은 오라클이 **실패해야** 한다 — 「되돌리면 red 가 나는가」
#   ㈐ downgrade 실물 동작 — 0030 shape 복원 ＋ 그 판에서 오라클이 실패
#   ㈑ 선언 정본(`db/platform/schema.sql`) = **체인 head** (schema-diff 가 보는 것과 같은 사실)
#
# ⚠ ㈑ 이 견주는 상대는 체인 head 이지 이 회차가 아니다 — `schema.sql` 은 체인 전체의 선언
#   정본이라, 뒤 회차가 서면 이 회차와는 반드시 갈린다. `db/ai/tests/0004-0005-drift.sh`(WU-C7)
#   ·`0006-drift.sh`(WU-C13) 가 같은 이유로 이미 head 를 견준다. 지금은 이 회차가 head 다.
#
# 원칙 (CLAUDE.md §4): 도커·alembic 이 없으면 **skip 이 아니라 red(준비 · 78)** 다.
# staging 을 건드리지 않는다 — 일회용 컨테이너는 호스트 포트를 하나도 열지 않는다.
#
# 환경변수
#   COLAB_ALEMBIC   alembic 실행 파일 (기본: PATH 의 alembic)
#   COLAB_PG_IMAGE  기본 postgres:16-alpine
set -uo pipefail
# 준비 판정만 재사용하며 컨테이너 생성·cleanup은 이 오라클이 소유한다.
. "$(dirname "${BASH_SOURCE[0]}")/../../../gates/tools/_pg.sh"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN="$(cd "$HERE/.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
IMAGE="${COLAB_PG_IMAGE:-postgres:16-alpine}"

REV="0031_search_evidence"
PREV_REV="0030_merge_audit_and_backoffice"

red(){ echo "::error::0031-drift red — $*"; exit 1; }
ready(){ echo "::error::0031-drift red(준비) — $*"; exit 78; }

command -v docker >/dev/null 2>&1 || ready "docker가 없다. DB가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || [ -x "$ALEMBIC" ] || ready "alembic을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다."

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" colab-0031-XXXXXX)"; PGC=""
cleanup(){ [ -z "$PGC" ] || docker rm -f "$PGC" >/dev/null 2>&1; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM

export COLAB_PLATFORM_DB_URL=postgresql+psycopg://offline/offline
render(){ (cd "$CHAIN" && "$ALEMBIC" $1 --sql) >"$2" 2>"$TMP/err" \
  || { sed 's/^/     /' "$TMP/err"; red "alembic 렌더 실패: $1"; }; }

render "upgrade $REV"             "$TMP/head.sql"
render "upgrade $PREV_REV"        "$TMP/prev.sql"
render "downgrade $REV:$PREV_REV" "$TMP/down.sql"
render "upgrade head"             "$TMP/chain_head.sql"

# 렌더 단계에서 먼저 막는다 — 이 회차가 더하는 것이 비면 아래 DB 판정은 볼 것이 없다.
for token in d3_search_evidence content_revision increment_d3_file_content_revision; do
  grep -q "$token" "$TMP/head.sql" || red "head 렌더에 $token 이 없다 — 받을 델타가 비었다."
done
echo "[0031-drift] 델타 = 내용 리비전 ＋ 검색 근거 표 → OK"

docker image inspect "$IMAGE" >/dev/null 2>&1 || docker pull -q "$IMAGE" >/dev/null 2>&1 \
  || ready "이미지 $IMAGE 를 확보하지 못했다."
PGC="colab_0031_$$_${RANDOM}"
docker run -d --rm --name "$PGC" --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=x -e POSTGRES_HOST_AUTH_METHOD=trust "$IMAGE" >/dev/null 2>&1 \
  || { PGC=""; ready "일회용 postgres 를 띄우지 못했다."; }
pg_wait_ready "$PGC" 60 || ready "postgres 실서버가 60초 안에 준비되지 않았다."

apply(){ docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" <"$2"; }
mkdb(){ docker exec "$PGC" createdb -U postgres "$1" >/dev/null; }
norm(){ docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$1" \
          | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' \
          | grep -v 'alembic_version_platform' > "$TMP/$1.norm"; }

FAILURES=()

# ── ㈎ head 적용 → 오라클 통과 ───────────────────────────────────────────────
mkdb head_db
apply head_db "$TMP/head.sql"        || red "$REV 적용 실패(㈎)."
apply head_db "$HERE/0031-assertions.sql" || red "㈎ head 에서 오라클이 실패했다 — 이 회차가 주장을 지키지 못한다."
echo "[0031-drift] ㈎ head 적용 ＋ 오라클 통과 → OK"

# ── ㈏ 이전 head 에서는 같은 오라클이 실패해야 한다 ──────────────────────────
# 여기가 green 이면 오라클은 이 회차에 대해 아무것도 말하지 않는다(0030 에서도 통과하므로).
mkdb prev_db
apply prev_db "$TMP/prev.sql" || red "$PREV_REV 적용 실패(㈏)."
if apply prev_db "$HERE/0031-assertions.sql" >/dev/null 2>&1; then
  echo "[0031-drift] ㈏ 0030 판이 오라클을 통과했다 — 오라클이 이 회차를 재지 않는다 ✗"
  FAILURES+=("㈏ 0030 에서 오라클 통과")
else
  echo "[0031-drift] ㈏ 0030 판에서 오라클 실패(기대) → OK"
fi

# ── ㈐ downgrade 실물 동작 ＋ 0030 shape 복원 ────────────────────────────────
mkdb down_db
apply down_db "$TMP/head.sql" || red "down 판 head 적용 실패(㈐)."
apply down_db "$TMP/down.sql" || red "downgrade 적용 실패(㈐) — 되돌릴 수 없는 회차다."
if apply down_db "$HERE/0031-assertions.sql" >/dev/null 2>&1; then
  echo "[0031-drift] ㈐ downgrade 판이 오라클을 통과했다 — 되돌려도 red 가 안 난다 ✗"
  FAILURES+=("㈐ downgrade 에서 오라클 통과")
fi
norm prev_db; norm down_db
if diff -u "$TMP/prev_db.norm" "$TMP/down_db.norm" > "$TMP/shape.diff"; then
  echo "[0031-drift] ㈐ downgrade 결과 = 0030 상태 (pg_dump 차이 0줄) → OK"
else
  echo "[0031-drift] ㈐ downgrade 결과가 0030 상태와 다르다 ✗"
  sed 's/^/           /' "$TMP/shape.diff" | head -60
  FAILURES+=("㈐ downgrade = 0030 동일성")
fi

# ── ㈑ 선언 정본 ↔ 체인 head (schema-diff 가 보는 것과 같은 사실) ────────────
mkdb chain_db
apply chain_db "$TMP/chain_head.sql" || red "체인 head 를 적용하지 못했다."
mkdb decl_db
apply decl_db "$CHAIN/schema.sql" || red "schema.sql 를 적용하지 못했다."
norm chain_db; norm decl_db
if diff -u "$TMP/decl_db.norm" "$TMP/chain_db.norm" > "$TMP/decl.diff"; then
  echo "[0031-drift] ㈑ 선언 정본 schema.sql = 체인 head → OK"
else
  echo "[0031-drift] ㈑ schema.sql 과 체인 head 가 갈렸다 ✗"
  sed 's/^/           /' "$TMP/decl.diff" | head -60
  FAILURES+=("㈑ schema.sql ↔ 체인 head")
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0031-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0031-drift green — head 오라클 통과 · 0030·downgrade 판에서 실패 · 0030 shape 복원 · 선언 = 체인 head."
