#!/usr/bin/env bash
# rls-coverage 게이트 (WU-D3) — allow-list 밖 테이블의 RLS 누락 검출.
#
# 이 프로젝트의 핵심 보험이다: CLAUDE.md §3-5 (모든 조회에 연구실 경계가 자동 주입된다) ·
# PLAN-SoT §9-㉖ / PERMISSION-PRINCIPLES P-34 (파일 본체 접근도 RLS 로 막는다).
#
# 판정 경로: db/<체인>/schema.sql 을 **일회용 postgres** 에 적용 → pg_class·pg_policies 를 조회해
#            사실(facts) TSV 를 만들고 → rls_coverage.py 가 allow-list 와 대조해 판정한다.
#   선언 스키마를 대상으로 보는 이유: RLS 는 스키마의 성질이고, 선언과 적용 DB 가 갈라졌는지는
#   schema-diff 의 일이다. 두 게이트가 같은 사실을 두 번 보지 않는다.
#   실제 postgres 엔진을 쓰는 이유: RLS 는 텍스트 grep 으로 판정할 수 없다
#   (ALTER … FORCE 가 뒤에서 다시 꺼질 수 있고, 정책 대상도 CREATE POLICY 문 하나로는 안 보인다).
#
# 원칙 (CLAUDE.md §4): 스키마가 없거나 postgres 를 못 띄우면 **red**. skip 없음.
#
# 환경변수
#   COLAB_DB_DIR · COLAB_RLS_ALLOWLIST · COLAB_PG_IMAGE · COLAB_PG_FORCE_UNAVAILABLE
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DB_DIR="${COLAB_DB_DIR:-$REPO_ROOT/db}"
ALLOWLIST="${COLAB_RLS_ALLOWLIST:-$REPO_ROOT/gates/config/rls-allowlist.toml}"
CHAINS=(platform ai)

red() { echo "::error::rls-coverage red — $*"; exit 1; }

[ -f "$ALLOWLIST" ] || red "allow-list 정본이 없다: ${ALLOWLIST#$REPO_ROOT/}"

MISSING=()
for c in "${CHAINS[@]}"; do
  [ -f "$DB_DIR/$c/schema.sql" ] || MISSING+=("db/$c/schema.sql")
done
if [ "${#MISSING[@]}" -gt 0 ]; then
  red "선언 스키마가 없다. 대상 0건은 통과가 아니다 — 'RLS 누락이 없다'와 '테이블이 없다'는 다른 사실이다.
   없는 것:
$(printf '     - %s\n' "${MISSING[@]}")
   P0 가 스키마를 놓을 때까지 red 다 (CLAUDE.md §4). v1 CI 가 DB 없이 RLS 테스트를 통과시킨 실패를 반복하지 않는다."
fi

# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_pg.sh"
pg_start rls-coverage || exit 1

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" rls-coverage-XXXXXX)"
trap 'rm -rf "$TMP"; pg_cleanup' EXIT INT TERM
FACTS="$TMP/facts.tsv"; : > "$FACTS"

for c in "${CHAINS[@]}"; do
  pg_apply "rlschk_$c" "$DB_DIR/$c/schema.sql" \
    || red "db/$c/schema.sql 를 빈 postgres 에 적용하지 못했다. 적용되지 않는 스키마는 검사할 수 없다."
  # 사용자 스키마의 **일반 테이블만** 본다 (뷰·파티션 부모·시스템 스키마 제외).
  pg_psql "rlschk_$c" -At -F$'\t' -c "
    SELECT '$c', c.relname,
           CASE WHEN c.relrowsecurity THEN 't' ELSE 'f' END,
           CASE WHEN c.relforcerowsecurity THEN 't' ELSE 'f' END,
           COALESCE((SELECT string_agg(p.polname, ',' ORDER BY p.polname)
                     FROM pg_policy p WHERE p.polrelid = c.oid), '')
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'r' AND n.nspname NOT IN ('pg_catalog','information_schema')
    ORDER BY c.relname;" >> "$FACTS" 2>"$TMP/err" \
    || red "카탈로그 조회 실패: $(cat "$TMP/err")"
done

echo "# 조사한 테이블 $(wc -l < "$FACTS")건 (db/platform · db/ai)"
# exec 하지 않는다 — exec 하면 trap 이 안 돌아 일회용 컨테이너가 남는다.
python3 "$REPO_ROOT/gates/tools/rls_coverage.py" "$FACTS"
exit $?
