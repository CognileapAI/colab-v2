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

expect_red() { # $1 = 케이스 이름, 나머지 = 환경변수 주입
  local name="$1"; shift
  if env "$@" "$GATE" >/dev/null 2>&1; then
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

exit $rc
