#!/usr/bin/env bash
# 0030 오라클 — **두 순서가 같은 스키마로 수렴한다**를 기계가 증명한다.
# 형태는 db/ai/tests/0007-drift.sh 와 같다 (같은 실패를 두 번 배우지 않는다).
# 이 회차는 머지라 **차분이 0** 이고, 그래서 「무엇이 바뀌었나」가 아니라
# **갈래를 어느 순서로 올려도 같은 곳에 닿는가**가 리비전 성립 조건이다.
#
#   ㈎ 순서 A  0026 → 0027_operator_audit → (백오피스 갈래 ＋ 머지) → pg_dump
#   ㈏ 순서 B  0026 → 0028_account_status → 0029_operator_read_policy
#                   → (0027_operator_audit ＋ 머지)                  → pg_dump
#   ㈐ ㈎ = ㈏  (두 순서 수렴 — 머지 리비전의 성립 조건)
#   ㈑ 선언 정본(`db/platform/schema.sql`) = ㈎ = ㈏ (schema-diff 가 보는 것과 같은 사실)
#   ㈒ 머지 리비전의 `upgrade()` 본문이 비었고 `down_revision` 이 두 형제 튜플이다
#
# ⚠ **어느 갈래도 아직 dev 에 적용되지 않았다.** 그래서 이 오라클이 재는 것은
#   「이미 적용된 쪽이 무엇을 더 받는가」가 아니라 두 순서의 수렴 하나다.
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

MERGE_REV="0030_merge_audit_and_backoffice"
SIB_AUDIT="0027_operator_audit"
SIB_BACKOFFICE="0029_operator_read_policy"
PREV_REV="0026_login_sessions"

red(){ echo "::error::0030-drift red — $*"; exit 1; }
ready(){ echo "::error::0030-drift red(준비) — $*"; exit 78; }

command -v docker >/dev/null 2>&1 || ready "docker가 없다. DB가 필요한 시험을 DB 없이 green 으로 세지 않는다."
command -v "$ALEMBIC" >/dev/null 2>&1 || [ -x "$ALEMBIC" ] || ready "alembic을 찾지 못했다($ALEMBIC). COLAB_ALEMBIC 로 지정한다."

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" colab-0030-XXXXXX)"; PGC=""
cleanup(){ [ -z "$PGC" ] || docker rm -f "$PGC" >/dev/null 2>&1; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM

export COLAB_PLATFORM_DB_URL=postgresql+psycopg://offline/offline
render(){ (cd "$CHAIN" && "$ALEMBIC" $1 --sql) >"$2" 2>"$TMP/err" \
  || { sed 's/^/     /' "$TMP/err"; red "alembic 렌더 실패: $1"; }; }

# ── ㈒ 머지 리비전이 **차분을 만들지 않는다** ────────────────────────────────
# 스키마 변경이 여기 들어오면 그것은 머지가 아니라 새 회차다.
# ⛔ 이것을 `alembic upgrade <형제>:<merge> --sql` 로 재지 않는다 — 그 렌더에는
#    반대편 갈래가 통째로 섞여 들어온다(그것이 아래 2단계가 재는 것이다).
MERGE_FILE="$CHAIN/versions/0030_merge_operator_audit_and_backoffice.py"
[ -f "$MERGE_FILE" ] || red "머지 리비전 파일이 없다: $MERGE_FILE"
python3 - "$MERGE_FILE" "$SIB_AUDIT" "$SIB_BACKOFFICE" <<'PYEOF' || red "머지 리비전 정적 판정 실패 — 머지가 아니라 새 회차다."
import ast, sys
path, want_a, want_b = sys.argv[1], sys.argv[2], sys.argv[3]
tree = ast.parse(open(path, encoding="utf-8").read())
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
parents = tuple(e.value for e in dr.value.elts) if dr and isinstance(dr.value, ast.Tuple) else None
if parents != (want_a, want_b):
    print(f"down_revision 이 두 형제 튜플이 아니다: {parents}"); raise SystemExit(1)
rev = next((n.value.value for n in tree.body if isinstance(n, ast.Assign)
            and any(getattr(t, "id", "") == "revision" for t in n.targets)), None)
if rev is None or len(rev) > 32:
    print(f"revision id 가 없거나 32자를 넘는다: {rev!r}"); raise SystemExit(1)
print(f"[0030-drift] ㈒ upgrade() 본문 0문장 · down_revision = {parents} · id {len(rev)}자 → OK")
PYEOF

# ── 두 순서를 각각 두 단계로 렌더한다 (한 번에 head 로 가면 순서를 못 고정한다) ──
render "upgrade $PREV_REV"                  "$TMP/prev.sql"
render "upgrade $PREV_REV:$SIB_AUDIT"       "$TMP/a1.sql"
render "upgrade $PREV_REV:$SIB_BACKOFFICE"  "$TMP/b1.sql"
# 2단계는 **나머지 갈래 ＋ 머지**다. alembic 이 남은 갈래를 알아서 끼워 넣는다.
render "upgrade $SIB_AUDIT:$MERGE_REV"      "$TMP/a2.sql"
render "upgrade $SIB_BACKOFFICE:$MERGE_REV" "$TMP/b2.sql"
grep -q 'is_operator_read' "$TMP/a2.sql" \
  || red "㈎ 2단계에 백오피스 갈래의 is_operator_read() 가 없다 — 받을 델타가 비었다."
grep -q 'd2_operator_audit' "$TMP/b2.sql" \
  || red "㈏ 2단계에 감사 갈래의 d2_operator_audit 가 없다 — 받을 델타가 비었다."
echo "[0030-drift] 순서 A 델타 = 백오피스 ＋ 머지 · 순서 B 델타 = 감사 ＋ 머지 → OK"

docker image inspect "$IMAGE" >/dev/null 2>&1 || docker pull -q "$IMAGE" >/dev/null 2>&1 \
  || ready "이미지 $IMAGE 를 확보하지 못했다."
PGC="colab_0030_$$_${RANDOM}"
docker run -d --rm --name "$PGC" --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=x -e POSTGRES_HOST_AUTH_METHOD=trust "$IMAGE" >/dev/null 2>&1 \
  || { PGC=""; ready "일회용 postgres 를 띄우지 못했다."; }
for _ in $(seq 1 60); do docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 && break; sleep 1; done
docker exec "$PGC" pg_isready -U postgres -q >/dev/null 2>&1 || ready "postgres 가 60초 안에 뜨지 않았다."

apply(){ docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$1" <"$2"; }
mkdb(){ docker exec "$PGC" createdb -U postgres "$1" >/dev/null; }
norm(){ docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$1" \
          | grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' \
          | grep -v 'alembic_version_platform' > "$TMP/$1.norm"; }

FAILURES=()

# ㈎ 순서 A — 감사 갈래 먼저.
mkdb order_a
apply order_a "$TMP/prev.sql" || red "$PREV_REV 적용 실패(㈎)."
apply order_a "$TMP/a1.sql"   || red "$SIB_AUDIT 적용 실패(㈎-1)."
apply order_a "$TMP/a2.sql"   || red "백오피스 갈래 ＋ 머지 적용 실패(㈎-2)."
echo "[0030-drift] ㈎ 순서 A(감사 → 백오피스 → 머지) 적용 → OK"

# ㈏ 순서 B — 백오피스 갈래 먼저.
mkdb order_b
apply order_b "$TMP/prev.sql" || red "$PREV_REV 적용 실패(㈏)."
apply order_b "$TMP/b1.sql"   || red "$SIB_BACKOFFICE 적용 실패(㈏-1)."
apply order_b "$TMP/b2.sql"   || red "감사 갈래 ＋ 머지 적용 실패(㈏-2)."
echo "[0030-drift] ㈏ 순서 B(백오피스 → 감사 → 머지) 적용 → OK"

# ㈐ 두 순서 수렴 — 이것이 머지 리비전의 성립 조건이다.
norm order_a; norm order_b
if diff -u "$TMP/order_a.norm" "$TMP/order_b.norm" > "$TMP/order.diff"; then
  echo "[0030-drift] ㈐ 두 순서 수렴 (pg_dump 차이 0줄) → OK"
else
  echo "[0030-drift] ㈐ 두 순서가 다른 스키마에 닿는다 — 머지가 아니다 ✗"
  sed 's/^/           /' "$TMP/order.diff" | head -60
  FAILURES+=("㈐ 두 순서 수렴")
fi

# ㈑ 선언 정본 ↔ 적용 결과 (schema-diff 가 보는 것과 같은 사실).
mkdb decl_db
apply decl_db "$CHAIN/schema.sql" || red "schema.sql 를 적용하지 못했다."
norm decl_db
for db in order_a order_b; do
  if diff -u "$TMP/decl_db.norm" "$TMP/$db.norm" > "$TMP/decl-$db.diff"; then
    echo "[0030-drift] ㈑ 선언 정본 schema.sql = $db → OK"
  else
    echo "[0030-drift] ㈑ schema.sql 과 $db 가 갈렸다 ✗"
    sed 's/^/           /' "$TMP/decl-$db.diff" | head -60
    FAILURES+=("㈑ schema.sql ↔ $db")
  fi
done

if [ "${#FAILURES[@]}" -gt 0 ]; then
  printf '::error::0030-drift red — 실패 %d건:\n' "${#FAILURES[@]}"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "0030-drift green — 머지 차분 0 · 두 순서 스키마 수렴(차이 0줄) · 선언 = 적용."
