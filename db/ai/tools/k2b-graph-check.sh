#!/usr/bin/env bash
# k2b-graph — WU-K2b 완료 오라클. 적재된 D9 그래프가 Ted 판정 기준과 완전일치하는지 본다.
#
# 기준 = db/ai/seed/k2b-graph-standard.tsv   (Ted 판정 2026-08-25 · PLAN-SoT §9)
# 사실 = 실제 DB 의 d9_concept · d9_concept_edge (+ 정합 대조용 d9_method_term · d9_topic_synonym)
# 판정 = db/ai/tools/k2b_graph_check.py  (기준과 한 행이라도 갈리면 red)
#
# DB 를 못 붙으면 **red 다. skip 이 아니다** (CLAUDE.md §4 — 검사를 못 한 것은 통과가 아니다).
# 이 스크립트가 fail-closed 임을 증명하는 red fixture 는 k2b-graph-selftest.sh 에 있다.
#
# 접속 두 가지 (하나는 있어야 한다) — k2-coverage-check.sh 와 같은 규약
#   ① COLAB_AI_DB_CONTAINER=<컨테이너> [COLAB_AI_DB_NAME=<db>]
#   ② COLAB_AI_DB_URL=postgresql://…
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STD="${COLAB_K2B_STANDARD:-$HERE/../seed/k2b-graph-standard.tsv}"

red() { echo "::error::k2b-graph red — $*"; exit 1; }

SQL="
SELECT 'node', concept_id, kind, label, source_grade::text,
       CASE WHEN expandable THEN 't' ELSE 'f' END FROM d9_concept
UNION ALL
SELECT 'edge', src, relation, dst, source_grade::text, '' FROM d9_concept_edge
UNION ALL
SELECT 'mterm', term, '', '', '', '' FROM d9_method_term
UNION ALL
SELECT 'topic', topic, '', '', '', '' FROM d9_topic_synonym;
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

printf '%s\n' "$FACTS" | python3 "$HERE/k2b_graph_check.py" "$STD"
