"""selftest 전용 red 픽스처 — 수집은 되는데 **전부 skip**.

수집 건수만 보면 0 이 아니라 통과처럼 보인다. 그러나 **실행된 것이 0 건**이면 검사한 것도
0 건이다 — 그것을 green 으로 세는 것이 green-by-skip 의 정확한 모양이다 (`CLAUDE.md §4`).
"""
import pytest


@pytest.mark.skip(reason="green-by-skip 재현 — 수집은 되고 실행은 0")
def test_건너뛴다() -> None:
    assert True


@pytest.mark.skip(reason="green-by-skip 재현 — 수집은 되고 실행은 0")
def test_이것도_건너뛴다() -> None:
    assert True
