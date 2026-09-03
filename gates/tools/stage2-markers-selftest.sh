#!/usr/bin/env bash
# stage2-markers 가 red fixture 로 fail-closed 임을 증명한다.
#
# 케이스 3종 — 셋 다 red 를 내야 한다:
#   ⓐ 마커 시험 0 건 (선택자가 아무것도 못 잡음)
#   ⓑ 마커 시험이 skip 됨 (green-by-skip — v1 의 실패 형태)
#   ⓒ 마커 시험이 fail 함
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/stage2-markers.sh"
rc=0

# 판정 갈래(green·red·ready·미선언)의 정본 = `_expect.sh` 하나.
# ⭑ ⟨2026-09-03 코드리뷰 #6 의 형제⟩ 종전의 `expect_red` 는 **0 이 아니면 전부 red** 로 셌다.
#   그런데 `stage2-markers` 는 pipeline-worker venv 가 없으면 **78(준비 실패)** 로 나간다 —
#   venv 없는 체크아웃에서 이 셀프테스트는 세 케이스 전부를 「✓ red」로 찍으면서 **게이트를
#   한 번도 판정하지 않은 채 green** 이었다. 리뷰가 센 12개 밖의 같은 모양이다.
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

expect_red() { # $1 = 케이스 이름, 나머지 = 환경변수 주입
  local name="$1"; shift
  local out ec
  # `set -e` 아래서 실패한 명령 치환은 그 자리에서 스크립트를 죽인다 — 종료코드를 봐야 하는
  # 자리라 잠시 끈다. 종전 판이 `if env …; then` 이었던 것도 같은 이유였다.
  set +e
  out="$(env "$@" "$GATE" 2>&1)"; ec=$?
  set -e
  if expect_intercept_readiness "$ec" "$out" "$name" red; then return; fi
  if [ "$ec" -eq 0 ]; then
    echo "::error::stage2-markers-selftest red — 케이스 $name 이 green 을 냈다 (fail-open)."
    rc=1
  else
    echo "  ✓ $name — red"
  fi
}

# ⓐ 0 건
expect_red "ⓐ 마커 0 건" COLAB_STAGE2_SELECT="stage2 and not stage2"

# ⓑ skip / ⓒ fail — 임시 시험 파일을 주입해 선택자로 그것만 잡는다.
trap 'rm -f "$REPO_ROOT/services/pipeline-worker/tests/test_zz_stage2_selftest_fixture.py"' EXIT
cat > "$REPO_ROOT/services/pipeline-worker/tests/test_zz_stage2_selftest_fixture.py" <<'PYFIX'
# selftest 전용 red fixture — stage2-markers-selftest.sh 가 만들고 지운다.
import pytest


@pytest.mark.stage2
@pytest.mark.skip(reason="green-by-skip 재현")
def test_skipped_fixture():
    assert True


@pytest.mark.stage2
def test_failing_fixture():
    assert False
PYFIX

expect_red "ⓑ skip" COLAB_STAGE2_K="test_skipped_fixture"
expect_red "ⓒ fail" COLAB_STAGE2_K="test_failing_fixture"

[ "$rc" -eq 0 ] || exit "$rc"
# 판정 결함이 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다** (`_expect.sh`).
expect_readiness_verdict stage2-markers-selftest "pipeline-worker venv(파이썬 실행 파일)"
echo "stage2-markers-selftest green — 0건 · skip · fail 셋 다 red 다 (fail-closed 증명)."
exit 0
