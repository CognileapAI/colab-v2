#!/usr/bin/env bash
# 미리보기 렌더 성능 합격선 — **실원천으로 재고 눈금에 댄다**.
#
# 근거: `PLAN-SoT §9 〈233〉` (정본 `Policy_데이터셋_상세` v2.6 `§8` 「확대(줌)」 조건 ⑺).
#       눈금의 정본은 `gates/config/render-latency.toml` 하나다.
#
# ⚠ **이 게이트는 화면 왕복을 재지 않는다.** 재는 것은 viz-render 의 렌더 시간이고,
#   시험 머리말이 「재지 않은 넷」을 이름으로 적는다. 눈금이 실측보다 넉넉한 이유가 그것이다.
#
# fail-closed (CLAUDE.md §4 green-by-skip 금지):
#   · 원천 마운트(`COLAB_REFERENCE_DATA`) 미선언·미마운트 → **준비 red**. skip 이 아니다
#   · viz-render 파이썬 실행 파일 부재 → 준비 red
#   · `렌더초` 가 붙은 통과 케이스 **0건 → red**  ← 이 자리의 자연스러운 대상 수는 0 이다
#   · 실패·건너뛴 케이스 → red (그리지 못한 것은 시간이 짧다)
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
SVC="${COLAB_RENDER_LATENCY_SVC:-$REPO_ROOT/services/viz-render}"
CONFIG="${COLAB_RENDER_LATENCY_CONFIG:-$REPO_ROOT/gates/config/render-latency.toml}"
JUDGE="$REPO_ROOT/gates/tools/render_latency.py"

# 준비 실패(readiness)와 판정 실패를 가른다 — e2e-format-coverage 와 같은 관용구다.
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_pg.sh"

REF="${COLAB_REFERENCE_DATA:-}"
if [ -z "$REF" ] || [ ! -d "$REF" ]; then
  pg_readiness_report render-latency "원천 데이터 마운트(COLAB_REFERENCE_DATA)" "대기 없음" "0초" \
    "COLAB_REFERENCE_DATA 가 원천 디렉터리를 가리키게 하고 재실행한다. 원천이 없으면 이 검사는 돌 수 없고, 못 돈 것은 통과가 아니다."
  exit "$PG_READINESS_EXIT"
fi

PY="${COLAB_RENDER_LATENCY_PY:-$SVC/.venv/bin/python}"
if [ ! -x "$PY" ]; then
  pg_readiness_report render-latency "viz-render 파이썬 실행 파일($PY)" "대기 없음" "0초" \
    "venv 가 이 체크아웃에 없다. services/viz-render 에 venv 를 만들고 requirements.txt 를 설치한 뒤 재실행한다."
  exit "$PG_READINESS_EXIT"
fi

XML="$(mktemp -t render-latency-XXXXXX.xml)"
trap 'rm -f "$XML"' EXIT

# `--strict-markers` — 표식 오타가 조용히 무시되면 대상이 0 이 되고, 0 은 여기서 red 다.
# `junit_family=xunit1` — xunit2 는 `record_property` 를 버린다(초가 리포트에 안 남는다).
# `-p no:randomly` 같은 순서 개입은 걸지 않는다 — 시간은 순서에 의존하지 않아야 한다.
(cd "$SVC" && "$PY" -m pytest -q --strict-markers -p no:cacheprovider \
   -m perf -o junit_family=xunit1 --junitxml="$XML")
rc=$?
[ "$rc" -ne 0 ] && echo "render-latency — pytest 종료 코드 $rc (실패 케이스는 아래 목록에 이름으로 나온다)"

exec python3 "$JUDGE" --junit "$XML" --config "$CONFIG"
