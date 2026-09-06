#!/usr/bin/env bash
# k2-coverage — WU-K2 완료 오라클. 적재된 D9 시드가 커버리지 기준을 전부 덮는지 본다.
#
# 기준 = db/ai/seed/k2-coverage-standard.tsv   (03-HANDOFF §1 K2 행)
# 사실 = 실제 DB 의 d9_method_term · d9_topic_synonym · d9_place_alias
# 판정 = db/ai/tools/k2_coverage_check.py  (미커버 1건이라도 있으면 red)
#
# DB 를 못 붙으면 **red 다. skip 이 아니다** (CLAUDE.md §4 — 검사를 못 한 것은 통과가 아니다).
# 게이트가 아니라 db/ai 의 도구다. gates/ 는 이 밤 다른 레인이 만지고 있어 건드리지 않았다.
#
# 접속 두 가지 (하나는 있어야 한다)
#   ① COLAB_AI_DB_CONTAINER=<컨테이너> [COLAB_AI_DB_NAME=<db>]  → docker exec 로 컨테이너 안에서 psql
#      (일회용 postgres 검증용. 호스트 포트를 publish 하지 않아도 된다 — gates/tools/_pg.sh 와 같은 방식)
#   ② COLAB_AI_DB_URL=postgresql://…                            → 호스트의 psql
# 접속 URL 을 파일에 적지 않는다 (db/ai/env.py 와 같은 규율).
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STD="${COLAB_K2_STANDARD:-$HERE/../seed/k2-coverage-standard.tsv}"

red() { echo "::error::k2-coverage red — $*"; exit 1; }

SQL="
SELECT 'method', term       FROM d9_method_term
UNION ALL
SELECT 'topic',  topic      FROM d9_topic_synonym
UNION ALL
SELECT 'place',  place_name FROM d9_place_alias;
"

if [ -n "${COLAB_AI_DB_CONTAINER:-}" ]; then
  DB="${COLAB_AI_DB_NAME:-postgres}"
  FACTS="$(docker exec -i "$COLAB_AI_DB_CONTAINER" psql -U postgres -d "$DB" -At -F$'\t' \
             -v ON_ERROR_STOP=1 -c "$SQL" 2>&1)" \
    || red "컨테이너 $COLAB_AI_DB_CONTAINER 의 DB $DB 를 조회하지 못했다:
$FACTS"
elif [ -n "${COLAB_AI_DB_URL:-}" ]; then
  command -v psql >/dev/null 2>&1 || red "psql 이 없다. COLAB_AI_DB_CONTAINER 방식을 쓰거나 psql 을 설치한다."
  FACTS="$(psql "$COLAB_AI_DB_URL" -At -F$'\t' -v ON_ERROR_STOP=1 -c "$SQL" 2>&1)" \
    || red "COLAB_AI_DB_URL 로 조회하지 못했다:
$FACTS"
else
  red "DB 접속 정보가 없다. COLAB_AI_DB_CONTAINER 또는 COLAB_AI_DB_URL 을 준다.
   접속처 없음을 green 으로 세지 않는다."
fi

printf '%s\n' "$FACTS" | python3 "$HERE/k2_coverage_check.py" "$STD"
