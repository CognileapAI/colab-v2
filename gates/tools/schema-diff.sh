#!/usr/bin/env bash
# schema-diff 게이트 (WU-D3) — 선언 스키마 ↔ 적용 DB 드리프트.
#
# 강제하는 것: db/README.md "선언 스키마 ↔ 적용 DB diff 게이트".
#   선언 = db/<체인>/schema.sql (SoT). 적용 = 실제로 마이그레이션이 돌아간 DB.
#   둘이 갈라지면 "문서상 스키마"가 생긴다 — v1 에서 허용값이 마이그레이션 docstring 에만 있던 것과 같은 종류의 붕괴.
#
# 판정: 선언 schema.sql 을 **일회용 postgres** 에 적용해 pg_dump 하고,
#       적용 DB($COLAB_APPLIED_DB_URL)를 같은 방식으로 pg_dump 해 정규화 후 diff. 차이가 있으면 red.
#
# 원칙 (CLAUDE.md §4): **DB 가 없으면 red.** skip 하면 그게 정확히 v1 의 실패다.
#   지금 db/ 에는 README 밖에 없으므로 이 게이트는 red 이고, red 인 것이 정상이다.
#
# 환경변수
#   COLAB_DB_DIR           db 루트 (기본: db/)
#   COLAB_APPLIED_DB_URL   적용 DB 접속 URL. 없으면 red (skip 아님)
#   COLAB_PG_IMAGE · COLAB_PG_FORCE_UNAVAILABLE  → _pg.sh
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DB_DIR="${COLAB_DB_DIR:-$REPO_ROOT/db}"
CHAINS=(platform ai)

red() { echo "::error::schema-diff red — $*"; exit 1; }

# ── 1. 선언 스키마가 있는가 (대상 0건 = red) ────────────────────────────────
MISSING=()
for c in "${CHAINS[@]}"; do
  [ -f "$DB_DIR/$c/schema.sql" ] || MISSING+=("db/$c/schema.sql")
  ls "$DB_DIR/$c/versions/"*.py >/dev/null 2>&1 || MISSING+=("db/$c/versions/*.py")
done
if [ "${#MISSING[@]}" -gt 0 ]; then
  red "선언 스키마·마이그레이션이 없다. 대상 0건은 통과가 아니다.
   없는 것:
$(printf '     - %s\n' "${MISSING[@]}")
   P0 가 db/<체인>/schema.sql(선언 SoT)과 versions/ 를 놓는다. 그때까지 red 다 (CLAUDE.md §4)."
fi

# ── 2. 적용 DB 가 있는가 (없으면 red — 여기서 skip 하면 v1 을 반복한다) ─────
APPLIED="${COLAB_APPLIED_DB_URL:-}"
[ -n "$APPLIED" ] || red "적용 DB 가 지정되지 않았다 (COLAB_APPLIED_DB_URL).
   **DB 가 없을 때 skip 하는 것이 v1 CI 의 실패였다.** 없으면 red 다.
   CI 설계: postgres 서비스 컨테이너를 띄우고 → db/<체인>/versions 를 alembic 으로 upgrade head →
   그 DB 의 URL 을 COLAB_APPLIED_DB_URL 로 넘긴다. 상세는 dev-package/sessions/D3-db.md §3."

# ── 3. 일회용 postgres 확보 ─────────────────────────────────────────────────
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_pg.sh"
pg_start schema-diff || exit 1

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" schema-diff-XXXXXX)"
trap 'rm -rf "$TMP"; pg_cleanup' EXIT INT TERM

# pg_dump 정규화 — 스키마와 무관한 줄만 걷어낸다. 그 밖엔 손대지 않는다
# (정규화를 늘릴수록 검사 대상이 줄어든다 = 게이트를 무디게 만드는 짓이다).
#   \restrict·\unrestrict = pg_dump 가 매번 새로 뽑는 난수 토큰. 스키마가 아니다.
normalize() {
  grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' "$1"
}

RC=0
for c in "${CHAINS[@]}"; do
  echo "── db/$c ────────────────────────────────────────────"
  pg_apply "declared_$c" "$DB_DIR/$c/schema.sql" \
    || red "db/$c/schema.sql 를 빈 postgres 에 적용하지 못했다. 선언 스키마 자체가 깨져 있다."
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges \
    -d "declared_$c" > "$TMP/declared_$c.sql" 2>"$TMP/err" \
    || red "선언 스키마 덤프 실패: $(cat "$TMP/err")"
  docker exec "$PGC" pg_dump --schema-only --no-owner --no-privileges \
    -d "$APPLIED" > "$TMP/applied_$c.sql" 2>"$TMP/err" \
    || red "적용 DB 덤프 실패(접속 불가도 red 다): $(cat "$TMP/err")"

  normalize "$TMP/declared_$c.sql" > "$TMP/d.norm"
  normalize "$TMP/applied_$c.sql"  > "$TMP/a.norm"
  if ! diff -u "$TMP/d.norm" "$TMP/a.norm" > "$TMP/diff_$c" ; then
    echo "::error::schema-diff red — db/$c 선언 스키마와 적용 DB 가 갈라졌다:"
    sed 's/^/     /' "$TMP/diff_$c" | head -80
    RC=1
  else
    echo "db/$c green — 드리프트 없음."
  fi
done

[ $RC -eq 0 ] || exit 1
echo "schema-diff green — 두 체인 모두 선언 = 적용."
