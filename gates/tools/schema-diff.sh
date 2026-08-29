#!/usr/bin/env bash
# schema-diff 게이트 (WU-D3) — 선언 스키마 ↔ 적용 DB 드리프트.
#
# 강제하는 것: db/README.md "선언 스키마 ↔ 적용 DB diff 게이트".
#   선언 = db/<체인>/schema.sql (SoT). 적용 = 실제로 마이그레이션이 돌아간 DB.
#   둘이 갈라지면 "문서상 스키마"가 생긴다 — v1 에서 허용값이 마이그레이션 docstring 에만 있던 것과 같은 종류의 붕괴.
#
# 판정: 선언 schema.sql 을 **일회용 postgres** 에 적용해 pg_dump 하고,
#       **그 체인의** 적용 DB 를 같은 방식으로 pg_dump 해 정규화 후 diff. 차이가 있으면 red.
#
# 체인은 둘이고 **서로 다른 DB** 다 (CLAUDE.md §3-3 — db/platform 과 db/ai 는 마이그레이션 체인이 분리된다).
#   그래서 적용 DB URL 도 체인마다 따로 받는다. 한 URL 로 두 체인을 비교하면
#   두 schema.sql 이 같아야만 green 이 되는데, 그건 체인 분리와 모순이다 (구 게이트의 결함).
#
# 원칙 (CLAUDE.md §4): **DB 가 없으면 red.** skip 하면 그게 정확히 v1 의 실패다.
#   지금 db/ 에는 README 밖에 없으므로 이 게이트는 red 이고, red 인 것이 정상이다.
#
# 환경변수
#   COLAB_DB_DIR           db 루트 (기본: db/)
#   COLAB_APPLIED_DB_URL_PLATFORM  db/platform 이 적용된 DB 접속 URL. 없으면 red (skip 아님)
#   COLAB_APPLIED_DB_URL_AI        db/ai 가 적용된 DB 접속 URL.       없으면 red (skip 아님)
#   COLAB_APPLIED_DB_URL           **구 변수. 단독으로 주면 red 다.**
#     근거: 이 변수 하나로는 "어느 체인의 DB 인가"를 알 수 없다. 아무 체인에나 갖다 붙이면
#     둘 중 한 체인만 실제로 검사되고 나머지는 우연히 통과/실패한다 — 조용히 검사 범위가 줄어든다.
#     검사를 무르게 만드느니 설정 오류로 red 를 내는 쪽이 옳다 (CLAUDE.md §4).
#     체인별 변수가 **둘 다** 있으면 구 변수는 무시하고 진행한다(마이그레이션 편의).
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

# ── 2. 체인별 적용 DB 가 있는가 (하나라도 없으면 red — skip 하면 v1 을 반복한다) ──
URL_PLATFORM="${COLAB_APPLIED_DB_URL_PLATFORM:-}"
URL_AI="${COLAB_APPLIED_DB_URL_AI:-}"
LEGACY="${COLAB_APPLIED_DB_URL:-}"

if [ -n "$LEGACY" ] && { [ -z "$URL_PLATFORM" ] || [ -z "$URL_AI" ]; }; then
  red "COLAB_APPLIED_DB_URL 은 더 이상 쓰지 않는다 — 어느 체인의 DB 인지 알 수 없다.
   db/platform 과 db/ai 는 마이그레이션 체인이 분리된 **서로 다른 DB** 다 (CLAUDE.md §3-3).
   한 URL 을 두 체인에 갖다 대면 한 체인만 실제로 검사된다 — 조용히 검사 범위가 줄어드는 게 최악이다.
   → COLAB_APPLIED_DB_URL_PLATFORM 과 COLAB_APPLIED_DB_URL_AI 를 **둘 다** 지정한다."
fi

MISSING_URL=()
[ -n "$URL_PLATFORM" ] || MISSING_URL+=("COLAB_APPLIED_DB_URL_PLATFORM (db/platform)")
[ -n "$URL_AI" ]       || MISSING_URL+=("COLAB_APPLIED_DB_URL_AI (db/ai)")
if [ "${#MISSING_URL[@]}" -gt 0 ]; then
  red "적용 DB 가 지정되지 않았다:
$(printf '     - %s\n' "${MISSING_URL[@]}")
   **DB 가 없을 때 skip 하는 것이 v1 CI 의 실패였다.** 한 체인이라도 없으면 red 다.
   CI 설계: 체인마다 DB 를 만들고 → db/<체인>/versions 를 alembic 으로 upgrade head →
   그 DB 의 URL 을 체인별 변수로 넘긴다. 상세는 dev-package/sessions/D3-db.md §3."
fi

applied_url() { case "$1" in platform) echo "$URL_PLATFORM";; ai) echo "$URL_AI";; esac; }

# ── 3. 일회용 postgres 확보 ─────────────────────────────────────────────────
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_pg.sh"
pg_start schema-diff || exit $?   # 준비 실패는 78 로 그대로 전달한다

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
  if ! pg_apply "declared_$c" "$DB_DIR/$c/schema.sql"; then
    # 형제 자리(rls-coverage)와 **같은 규율** — 서버 탓이면 준비 red, 스키마 탓이면 판정 red.
    if pg_is_readiness_error "$PG_APPLY_ERR"; then
      pg_readiness_report schema-diff "일회용 postgres 가 선언 스키마를 받을 수 있는 상태(db/$c 적용)" \
        "상한 없음" "-" "$PG_APPLY_ERR"
      exit "$PG_READINESS_EXIT"
    fi
    red "db/$c/schema.sql 를 빈 postgres 에 적용하지 못했다. 선언 스키마 자체가 깨져 있다.
   postgres 가 낸 말: ${PG_APPLY_ERR:-(출력 없음)}"
  fi
  docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges \
    -d "declared_$c" > "$TMP/declared_$c.sql" 2>"$TMP/err" \
    || red "선언 스키마 덤프 실패: $(cat "$TMP/err")"
  docker exec "$PGC" pg_dump --schema-only --no-owner --no-privileges \
    -d "$(applied_url "$c")" > "$TMP/applied_$c.sql" 2>"$TMP/err" \
    || red "db/$c 적용 DB 덤프 실패(접속 불가도 red 다): $(cat "$TMP/err")"

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
echo "schema-diff green — 두 체인 각각 선언 = 적용."
