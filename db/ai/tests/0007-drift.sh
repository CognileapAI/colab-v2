#!/usr/bin/env bash
# 0007 드리프트 시험 — **두 순서가 같은 스키마로 수렴한다**를 기계가 증명한다.
# 형태는 db/ai/tests/0006-drift.sh 와 같다 (같은 실패를 두 번 배우지 않는다).
# 다른 것은 판정 대상이다 — 이 회차는 **차분이 0** 이라 「무엇이 바뀌었나」를 잴 것이 없고,
# 대신 **갈래를 어느 순서로 올려도 같은 곳에 닿는가**가 이 리비전이 성립하는 조건이다.
#
#   ㈎ dev 순서   0005 → 0006_topic_vocab_six      → head  → pg_dump
#   ㈏ staging 순서 0005 → 0006_rc7_synonym_category → head  → pg_dump
#   ㈐ ㈎ = ㈏  (두 순서 수렴 — 이것이 머지 리비전의 성립 조건이다)
#   ㈑ 선언 정본(`db/ai/schema.sql`) = ㈎ = ㈏  (schema-diff 가 보는 것과 같은 사실)
#   ㈒ 행 수준 수렴 — 동의어 13행의 `category` 가 양쪽 다 NULL 이고 이관 3쌍이 양쪽 다 산다
#
# ⚠ **dev 는 `0006_topic_vocab_six` 를 이미 적용했다.** 그래서 dev 가 받을 것은 ㈏ 가 아니라
#   「rc7 ＋ 0007」이고, 그 최종 상태가 ㈎ 와 같아야 한다 — ㈐ 가 그것을 잰다.
#
# 원칙 (CLAUDE.md §4): 도커·alembic 이 없으면 **skip 이 아니라 red** 다.
# staging 을 건드리지 않는다 — 일회용 컨테이너는 `k1bdb_` 접두사이고 호스트 포트를 하나도 열지 않는다.
#
# 환경변수
#   COLAB_ALEMBIC   alembic 실행 파일 (기본: PATH 의 alembic)
#   COLAB_PG_IMAGE  기본 postgres:16-alpine
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN_DIR="$(cd "$HERE/.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
PG_IMAGE="${COLAB_PG_IMAGE:-postgres:16-alpine}"
HEAD_REV="0007_merge_vocab_and_category"
SIB_VOCAB="0006_topic_vocab_six"
SIB_CATEG="0006_rc7_synonym_category"
PREV_REV="0005_k2b_concept_graph_seed"

red() { echo "::error::0007-drift red — $*"; exit 1; }

command -v docker >/dev/null 2>&1 || red "docker 가 없다. DB 가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || red "alembic 을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다. 못 돈 시험은 통과가 아니다."

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" k1bdb-drift7-XXXXXX)"
PGC=""
cleanup() { [ -n "$PGC" ] && docker rm -f "$PGC" >/dev/null 2>&1; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM

export COLAB_AI_DB_URL="postgresql+psycopg://offline/offline"
render() {
  ( cd "$CHAIN_DIR" && "$ALEMBIC" $1 --sql ) > "$2" 2>"$TMP/err" \
    || { sed 's/^/     /' "$TMP/err"; red "alembic 렌더 실패: $1"; }
}

# ── 0. 머지 리비전이 **차분을 만들지 않는다** ────────────────────────────────
# 스키마 변경이 여기 들어오면 그것은 머지가 아니라 새 회차다 (`0014_merge_ra1_and_topic_vocab`
# 와 같은 규율). ⛔ 이것을 `alembic upgrade <형제>:<head> --sql` 로 재지 않는다 — 그 렌더에는
# **반대편 갈래가 통째로 섞여 들어온다**(그것이 dev 가 받을 델타이고, 아래 ㈎-2 가 그 자리다).
# 그래서 여기서는 **리비전 파일의 `upgrade()` 본문이 비었는가**를 `ast` 로 정적 판정한다.
MERGE_FILE="$CHAIN_DIR/versions/0007_merge_topic_vocab_and_rc7_category.py"
[ -f "$MERGE_FILE" ] || red "머지 리비전 파일이 없다: $MERGE_FILE"
python3 - "$MERGE_FILE" <<'PYEOF' || red "머지 리비전의 upgrade() 가 비어 있지 않다 — 머지가 아니라 새 회차다."
import ast, sys
tree = ast.parse(open(sys.argv[1], encoding="utf-8").read())
fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "upgrade"), None)
if fn is None:
    print("upgrade() 가 없다"); raise SystemExit(1)
body = [n for n in fn.body
        if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str))
        and not isinstance(n, ast.Pass)]
if body:
    print(f"upgrade() 본문에 문장 {len(body)}개가 있다 (docstring·pass 제외)"); raise SystemExit(1)
dr = next((n for n in tree.body if isinstance(n, ast.Assign)
           and any(getattr(t, "id", "") == "down_revision" for t in n.targets)), None)
parents = tuple(e.value for e in dr.value.elts) if isinstance(dr.value, ast.Tuple) else None
if parents != ("0006_topic_vocab_six", "0006_rc7_synonym_category"):
    print(f"down_revision 이 두 형제 튜플이 아니다: {parents}"); raise SystemExit(1)
print("[0007-drift] 머지 리비전 upgrade() 본문 0문장 · down_revision = 두 형제 튜플 → OK")
PYEOF

# ── 두 순서를 각각 두 단계로 렌더한다 (한 번에 head 로 가면 순서를 못 고정한다) ──
render "upgrade $PREV_REV"              "$TMP/prev.sql"
render "upgrade $PREV_REV:$SIB_VOCAB"   "$TMP/a1.sql"   # ㈎-1 dev 가 이미 적용한 것
render "upgrade $PREV_REV:$SIB_CATEG"   "$TMP/b1.sql"   # ㈏-1 staging 이 먼저 적용한 것
# 2단계는 **나머지 갈래 ＋ 머지**다. alembic 이 남은 갈래를 알아서 끼워 넣는다.
render "upgrade $SIB_VOCAB:$HEAD_REV"   "$TMP/a2.sql"
render "upgrade $SIB_CATEG:$HEAD_REV"   "$TMP/b2.sql"
grep -q 'ADD COLUMN category' "$TMP/a2.sql" \
  || red "㈎ 2단계에 rc7 의 'ADD COLUMN category' 가 없다 — dev 가 받을 델타가 비었다."
grep -q '가뭄' "$TMP/b2.sql" \
  || red "㈏ 2단계에 창 9 의 주제 6값이 없다 — staging 이 받을 델타가 비었다."
echo "[0007-drift] dev 델타 = rc7 ＋ 머지 · staging 델타 = 어휘 6값 ＋ 머지 → OK"

docker image inspect "$PG_IMAGE" >/dev/null 2>&1 || docker pull -q "$PG_IMAGE" >/dev/null 2>&1 \
  || red "이미지 $PG_IMAGE 를 확보하지 못했다. skip 아님."
PGC="k1bdb_drift7_$$_${RANDOM}"
docker run -d --rm --name "$PGC" \
  --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=k1bdb -e POSTGRES_HOST_AUTH_METHOD=trust \
  "$PG_IMAGE" >/dev/null 2>&1 || { PGC=""; red "일회용 postgres 를 띄우지 못했다."; }
for _ in $(seq 1 60); do docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 && break; sleep 1; done
docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 || red "postgres 가 60초 안에 뜨지 않았다."

psql_f() { docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" < "$2"; }
mkdb()   { docker exec "$PGC" createdb -U postgres "$1" >/dev/null; }
norm()   { docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$1" \
             | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' \
             | grep -v 'alembic_version_ai' > "$TMP/$1.norm"; }

FAILURES=()

# ㈎ dev 순서 — 어휘 6값 먼저.
mkdb dev_db
psql_f dev_db "$TMP/prev.sql" || red "0005 적용 실패(㈎)."
psql_f dev_db "$TMP/a1.sql"   || red "$SIB_VOCAB 적용 실패(㈎-1)."
psql_f dev_db "$TMP/a2.sql"   || red "$SIB_CATEG ＋ 머지 적용 실패(㈎-2) — dev 가 받을 델타가 안 돈다."
echo "[0007-drift] ㈎ dev 순서(어휘 6값 → 분류 → 머지) 적용 → OK"

# ㈏ staging 순서 — 분류 먼저.
mkdb stg_db
psql_f stg_db "$TMP/prev.sql" || red "0005 적용 실패(㈏)."
psql_f stg_db "$TMP/b1.sql"   || red "$SIB_CATEG 적용 실패(㈏-1)."
psql_f stg_db "$TMP/b2.sql"   || red "$SIB_VOCAB ＋ 머지 적용 실패(㈏-2) — staging 이 받을 델타가 안 돈다."
echo "[0007-drift] ㈏ staging 순서(분류 → 어휘 6값 → 머지) 적용 → OK"

# ㈐ 두 순서 수렴 — 이것이 머지 리비전의 성립 조건이다.
norm dev_db; norm stg_db
if diff -u "$TMP/dev_db.norm" "$TMP/stg_db.norm" > "$TMP/order.diff"; then
  echo "[0007-drift] ㈐ 두 순서 수렴 (pg_dump 동일) → OK"
else
  echo "[0007-drift] ㈐ 두 순서가 다른 스키마에 닿는다 — 머지가 아니다 ✗"
  sed 's/^/           /' "$TMP/order.diff" | head -60
  FAILURES+=("㈐ 두 순서 수렴")
fi

# ㈑ 선언 정본 ↔ 적용 결과 (schema-diff 가 보는 것과 같은 사실).
mkdb decl_db; psql_f decl_db "$CHAIN_DIR/schema.sql" || red "schema.sql 를 적용하지 못했다."
norm decl_db
for db in dev_db stg_db; do
  if diff -u "$TMP/decl_db.norm" "$TMP/$db.norm" > "$TMP/decl-$db.diff"; then
    echo "[0007-drift] ㈑ 선언 정본 schema.sql = $db → OK"
  else
    echo "[0007-drift] ㈑ schema.sql 과 $db 가 갈렸다 ✗"
    sed 's/^/           /' "$TMP/decl-$db.diff" | head -60
    FAILURES+=("㈑ schema.sql ↔ $db")
  fi
done

# ㈒ **행 수준 수렴** — 스키마가 같아도 값이 갈리면 순서가 결과를 바꾼 것이다.
#    창 9 의 13행은 rc7 의 UPDATE 대상(강우·강수·식생·NDVI·토지피복·LULC)이 아니라
#    어느 순서에서도 category = NULL 이고, 이관 3쌍은 양쪽 다 산다.
ROWS_SQL="$TMP/rows.sql"
cat > "$ROWS_SQL" <<'SQL'
SELECT synonym, topic, coalesce(category, '<NULL>') FROM d9_topic_synonym ORDER BY synonym;
SQL
for db in dev_db stg_db; do
  docker exec -i "$PGC" psql -q -At -F '|' -v ON_ERROR_STOP=1 -U postgres -d "$db" \
    < "$ROWS_SQL" > "$TMP/$db.rows" || red "행 대조 질의가 실패했다($db)."
done
if diff -u "$TMP/dev_db.rows" "$TMP/stg_db.rows" > "$TMP/rows.diff"; then
  echo "[0007-drift] ㈒ 행 수준 수렴 (d9_topic_synonym $(wc -l < "$TMP/dev_db.rows")행 동일) → OK"
else
  echo "[0007-drift] ㈒ 같은 스키마인데 행이 갈린다 — 순서가 값을 바꿨다 ✗"
  sed 's/^/           /' "$TMP/rows.diff" | head -40
  FAILURES+=("㈒ 행 수준 수렴")
fi
# 새 13행이 category 를 얻으면 그것은 지어낸 분류다 — PRD-01 이 그 둘을 짚은 적이 없다.
if grep -E '^(가뭄|가뭄지수|SPI|SPEI|drought|grib|netcdf|nc|bin|tif|geotiff|hdf5|hdf)\|' "$TMP/dev_db.rows" \
     | grep -qv '|<NULL>$'; then
  echo "[0007-drift] ㈒ 창 9 의 새 동의어 행에 분류가 채워졌다 — PRD-01 무근거 값이다 ✗"
  FAILURES+=("㈒ 새 13행 category NULL")
else
  echo "[0007-drift] ㈒ 창 9 새 13행 category = NULL ([미상] 그대로) → OK"
fi
# 이관 3쌍은 양쪽 다 산다 (머지가 rc7 의 값을 지우지 않았다).
for pair in '강우·강수|기상·기후 인자' '식생·NDVI|식생·탄소 인자' '토지피복·LULC|사회·경제 인자'; do
  t="${pair%%|*}"; want="${pair#*|}"
  if ! grep -q "|$t|$want\$" "$TMP/dev_db.rows"; then
    echo "[0007-drift] ㈒ 이관 쌍 '$t → $want' 가 dev 순서에서 사라졌다 ✗"
    FAILURES+=("㈒ 이관 3쌍 보존 ($t)")
  fi
done
# 주제 6값이 실제로 통과한다 — 정의문만 보지 않고 넣어 본다.
docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d dev_db >/dev/null 2>&1 <<'SQL' \
  || FAILURES+=("㈒ 6값 CHECK 실통과")
BEGIN;
INSERT INTO d9_topic_synonym (synonym, topic, source_note) VALUES
  ('_t7_a', '가뭄', '오라클 임시 행'), ('_t7_b', '파일 포맷 예제', '오라클 임시 행');
ROLLBACK;
SQL
docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d dev_db >/dev/null 2>&1 <<'SQL' \
  && FAILURES+=("㈒ 6값 밖이 안 막힌다")
BEGIN;
INSERT INTO d9_topic_synonym (synonym, topic, source_note) VALUES ('_t7_c', '유출·수문', '오라클 임시 행');
ROLLBACK;
SQL
echo "[0007-drift] ㈒ 6값 실통과 · 6값 밖 실거절 → 판정 완료"

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0007-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0007-drift green — 머지 차분 0 · 두 순서(dev·staging) 스키마·행 수렴 · 선언 = 적용 · 6값 실통과/실거절."
