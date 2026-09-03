"""selftest 전용 red 픽스처 — **실패를 못 잡는 게이트는 게이트가 아니다.**

통과 1건을 함께 둔다. 「전건 실패」가 아니라 **한 건만 실패해도 red 여야** 하기 때문이다.
"""


def test_통과한다() -> None:
    assert 1 + 1 == 2


def test_일부러_실패한다() -> None:
    assert 1 + 1 == 3
