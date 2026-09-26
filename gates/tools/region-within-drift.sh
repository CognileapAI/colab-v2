#!/usr/bin/env bash
# region-within-drift — 검색 계약 지역 포함 표(`contracts/search/semantics.json` `regionWithin`)가
# D9 그래프(`db/ai/seed/k2b-graph-standard.tsv` 의 지명 `안에 있다` 엣지·expandable · `db/ai/seed/*.sql`
# 의 `d9_place_alias`)와 같은가.
#
# 왜 게이트인가: 그래프 사실을 계약에 한 번 더 적는다(intent
#   `dev-package/intent/2026-09-26-region-containment-expansion.md` 결정 1 ㈎). 그래프를 개정하고
#   계약을 잊으면 조건 검색이 조용히 옛 포함 관계로 답한다. 이 대조가 그 이중 기재의 유일한 방어선이다.
# 판정부는 `region_within_drift.py` 하나다. 입력은 커밋된 파일뿐이다(DB·네트워크 0).
#   green 0 · red(판정) 1 · red(준비) 78 — 입력 부재·파싱 불가·`regionWithin` 미선언(입력미선언).
#   입력 자리는 COLAB_REGION_SEMANTICS · COLAB_REGION_GRAPH_TSV · COLAB_REGION_ALIAS_DIR 로 바꿀 수 있다
#   (셀프테스트가 사본을 물린다).
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v python3 >/dev/null 2>&1 || {
  echo "::gate-readiness-failure::gate=region-within-drift|detail=python3 이 없다"; exit 78; }
exec python3 "$HERE/region_within_drift.py"
