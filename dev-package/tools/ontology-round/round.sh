#!/usr/bin/env bash
# 온톨로지 회차 실행기. 절차 정본 = dev-package/tools/ontology-round/PROCEDURE.md
#
#   bash dev-package/tools/ontology-round/round.sh init [--all | --since ISO] [--database-url URL]
#       준비 점검 → 지난 회차 이후 자료 수집(기본 dev · 읽기 전용) → 분석 → summary.md. 회차 폴더 경로를 출력한다.
#   bash dev-package/tools/ontology-round/round.sh page <회차 폴더>
#       <회차 폴더>/decisions.json(에이전트가 쓴다) → decision-page.html
#   bash dev-package/tools/ontology-round/round.sh measure <회차 폴더> <payload.json>
#       일회용 postgres 에서 초안 사실 기여·역전 측정(eval/k4-search/measure_draft_contribution.py) — DEV·운영 DB 무접촉
#
# 회차 폴더 기본 자리 = ${COLAB_ONTOLOGY_ROUND_HOME:-~/.local/state/colab/ontology-rounds}/<YYYYMMDD-N>
#   (레포 밖 — dev 자료 설명 원문이 들어 있다. PR 에는 PROCEDURE.md 가 정한 파일만 옮긴다.)
# 종료코드: 0 · 1 판정 실패 · 78 준비 실패
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
HOME_DIR="${COLAB_ONTOLOGY_ROUND_HOME:-$HOME/.local/state/colab/ontology-rounds}"
PY="$ROOT/services/core-api/.venv/bin/python"
cmd="${1:-}"; shift || true

latest_state() { ls -1d "$HOME_DIR"/*/ 2>/dev/null | sort | while read -r d; do [ -f "$d/state.json" ] && echo "$d"; done | tail -1; }

case "$cmd" in
  init)
    bash "$HERE/setup.sh" --check >/dev/null || { bash "$HERE/setup.sh" --check; echo "준비 실패 — setup.sh 를 먼저 돌린다"; exit 78; }
    since=""; src=(--source dev); all=0
    while [ $# -gt 0 ]; do case "$1" in
      --all) all=1; shift;; --since) since="$2"; shift 2;;
      --database-url) src=(--database-url "$2"); shift 2;;
      *) echo "알 수 없는 인자: $1"; exit 1;; esac; done
    if [ -z "$since" ] && [ "$all" = 0 ]; then
      prev="$(latest_state)"; [ -n "$prev" ] && since="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["collectedAt"])' "$prev/state.json")"
    fi
    day="$(date +%Y%m%d)"; n=1; while [ -e "$HOME_DIR/$day-$n" ]; do n=$((n+1)); done
    R="$HOME_DIR/$day-$n"; mkdir -p "$R" && chmod 700 "$R"
    args=("${src[@]}" --out "$R/datasets.json"); [ -n "$since" ] && args+=(--since "$since")
    python3 "$HERE/collect.py" "${args[@]}" || { rc=$?; echo "수집 실패(rc=$rc) — 회차 폴더 $R"; exit $rc; }
    "$PY" "$HERE/analyze.py" "$R/datasets.json" --out "$R/analysis.json" --md "$R/summary.md" || exit $?
    python3 -c 'import json,sys;d=json.load(open(sys.argv[1]));json.dump({"schema":"colab-ontology-round-state/1","collectedAt":d["collectedAt"],"since":d["since"],"source":d["source"],"datasets":len(d["datasets"])},open(sys.argv[2],"w"),ensure_ascii=False,indent=2)' "$R/datasets.json" "$R/state.json"
    echo "회차 폴더: $R"; echo "다음: summary.md·analysis.json 을 읽고 PROCEDURE.md 3단계(에이전트 판단)로 decisions.json 을 쓴다" ;;
  page)
    R="${1:?회차 폴더}"; python3 "$HERE/page.py" "$R/decisions.json" --out "$R/decision-page.html" ;;
  measure)
    R="${1:?회차 폴더}"; PAYLOAD="${2:?payload.json}"
    C="orr_$$"
    docker run -d --rm --name "$C" -e POSTGRES_PASSWORD=x -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=colab_platform postgres:16-alpine >/dev/null || { echo "준비 실패: 컨테이너"; exit 78; }
    trap 'docker rm -f "$C" >/dev/null 2>&1' EXIT
    for _ in $(seq 1 60); do docker exec "$C" pg_isready -U postgres -d colab_platform -q && break; sleep 1; done; sleep 2
    URL="$(CONTAINER="$C" DB=colab_platform bash "$ROOT/services/core-api/tests/fixtures/setup-db.sh" | tail -1 | cut -f1)"
    [ -n "$URL" ] || { echo "준비 실패: setup-db"; exit 78; }
    (cd "$ROOT" && "$PY" eval/k4-search/measure_draft_contribution.py "$URL" --i-know-this-is-disposable \
       --seed-dev-like --payload "$PAYLOAD" --round "$(basename "$R")" --output "$R/measurement") ;;
  *) sed -n '2,15p' "$0"; exit 1 ;;
esac
