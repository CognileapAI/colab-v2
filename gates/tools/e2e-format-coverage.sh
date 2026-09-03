#!/usr/bin/env bash
# 실데이터 포맷 완주 커버리지 — 지원 목록의 **각 포맷이 실파일로 실제 그려지는가**.
#
# 근거: `WORK-UNITS §7` `S3` 행 축자 — 「**4종 각각 최소 1건**이 **시각화 화면에 그려지고** …
#       실패 파일은 목록으로 남긴다(**조용히 건너뛰지 않는다**)」. 판정 목록은 같은 행의
#       「⚠ 다만 지원 포맷 목록은 `〈77〉` 로 … `NumPy` 가 된다 — S3 이 열릴 때 그 목록으로
#       판정한다」를 따른다. **목록의 정본은 `gates/config/e2e-format-coverage.toml` 하나다.**
#
# ⚠ **이 게이트는 `S3` 를 닫지 않는다.** `S3` 의 완료 정의에는 계보 확정 상태와
#   staging 배포 green 이 함께 붙어 있고 그 둘은 여기서 재지 않는다. 여기서 재는 것은
#   **「각 포맷이 최소 1건 그려진다」 한 줄**이고, 그 한 줄이 조용히 0 이 되는 것을 막는다.
#
# fail-closed (CLAUDE.md §4 green-by-skip 금지):
#   · 원천 마운트(`COLAB_REFERENCE_DATA`) 미선언·미마운트 → **준비 red**. skip 이 아니다
#   · viz-render 파이썬 실행 파일 부재 → 준비 red
#   · 포맷 표식이 붙은 케이스 **0건 → red**  ← 이 자리의 자연스러운 대상 수는 0 이다
#   · 필수 포맷의 통과 케이스 0건 → red (면제 선언에 **이름으로** 적히면 건수를 드러낸 채 통과)
#   · 실패·건너뜀 케이스는 **이름으로 찍는다** — 목록으로 남긴다는 조항이 그 뜻이다
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
SVC="${COLAB_E2E_COVERAGE_SVC:-$REPO_ROOT/services/viz-render}"
CONFIG="${COLAB_E2E_COVERAGE_CONFIG:-$REPO_ROOT/gates/config/e2e-format-coverage.toml}"
JUDGE="$REPO_ROOT/gates/tools/e2e_format_coverage.py"

# 준비 실패(readiness)와 판정 실패를 가른다 — 표식·종료코드는 다른 DB 게이트의 것과 같다.
# ⚠ 준비 실패도 여전히 red 다. 건너뛰지 않는다.
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_pg.sh"

REF="${COLAB_REFERENCE_DATA:-}"
if [ -z "$REF" ] || [ ! -d "$REF" ]; then
  pg_readiness_report e2e-format-coverage "원천 데이터 마운트(COLAB_REFERENCE_DATA)" "대기 없음" "0초" \
    "COLAB_REFERENCE_DATA 가 원천 디렉터리를 가리키게 하고 재실행한다. 원천이 없으면 이 검사는 돌 수 없고, 못 돈 것은 통과가 아니다."
  exit "$PG_READINESS_EXIT"
fi

PY="${COLAB_E2E_COVERAGE_PY:-$SVC/.venv/bin/python}"
if [ ! -x "$PY" ]; then
  pg_readiness_report e2e-format-coverage "viz-render 파이썬 실행 파일($PY)" "대기 없음" "0초" \
    "venv 가 이 체크아웃에 없다. services/viz-render 에 venv 를 만들고 requirements.txt 를 설치한 뒤 재실행한다."
  exit "$PG_READINESS_EXIT"
fi

XML="$(mktemp -t e2e-format-coverage-XXXXXX.xml)"
trap 'rm -f "$XML"' EXIT

# `--strict-markers` — 표식 오타가 조용히 무시되면 대상이 0 이 되고, 0 은 여기서 red 다.
#   그래도 오타를 red 로 **바로** 잡는 편이 원인이 한 겹 가깝다.
# `junit_family=xunit1` — xunit2 는 `record_property` 를 버린다(리포트에 속성이 안 남는다).
#   기본값을 그대로 쓰면 표식이 붙어 있는데도 관측 0건이 되어, red 의 원인이 거짓이 된다.
(cd "$SVC" && "$PY" -m pytest -q --strict-markers -p no:cacheprovider \
   -m e2e -o junit_family=xunit1 --junitxml="$XML")
rc=$?
[ "$rc" -ne 0 ] && echo "e2e-format-coverage — pytest 종료 코드 $rc (실패 케이스는 아래 목록에 이름으로 나온다)"

exec python3 "$JUDGE" --junit "$XML" --config "$CONFIG"
