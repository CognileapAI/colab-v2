"""계보 쓰기의 TOCTOU — **검사와 삽입 사이가 비어 있었다** (부차 결함 `D-B`).

`would_create_cycle` 의 SELECT 와 `_INSERT_EDGE` 사이에 **락이 0건**이고 트랜잭션은
READ COMMITTED 다(`app/deps.py` — 요청 하나 = 트랜잭션 하나). 그래서 두 요청이
동시에 오면 **둘 다 순환 검사를 통과하고 둘 다 삽입해 순환이 생긴다.**

`A → B` 와 `B → A` 를 각각 다른 커넥션이 같은 순간에 붙이는 경우다. 어느 쪽도 혼자서는
순환이 아니고, 상대가 아직 커밋 전이라 서로를 못 본다.

**왜 그냥 두면 안 되는가.** 순환이 한 번 들어가면 `_SUMMARY` 의 재귀가 그 위를 돌고,
`deleteDataset` 이 501 이라 **지울 수단이 없다.** `〈133〉` 이 깊이를 접어 무한 재귀는
막았지만 **순환 자체를 막는 것은 이 락뿐이다.**

⚠ **오라클에 슬립을 쓰지 않는다.** 계획서가 그 이유를 적었다 — 시험이 공유 DB 를 쓰므로
슬립 기반 인터리빙은 **간헐 red** 를 낳는다. 대신 **락이 실제로 잡혔는지를 직접 묻는다**:
다른 커넥션에서 같은 열쇠로 `pg_try_advisory_xact_lock` 을 걸어 보고 **거절당하면**
락이 살아 있다는 뜻이다. 결정적이고, 기다리지 않는다.
"""
from __future__ import annotations

from sqlalchemy import text

from conftest import ACC_A_RES, LAB_A, scoped_ro

from colab_core.domains import d4_lineage
from colab_core.kernel.ids import Ulid


def _lock_key(session) -> int:
    """구현이 쓰는 것과 **같은 식**으로 열쇠를 만든다. 값을 시험이 지어내지 않는다."""
    return int(session.execute(
        text("SELECT hashtext(current_lab_id()::text)")).scalar_one())


def test_the_lab_lock_is_held_while_a_lineage_edge_is_written(session_factory) -> None:
    """**검사와 삽입이 같은 락 아래 있다.**

    쓰기 트랜잭션이 열려 있는 동안 다른 커넥션이 같은 열쇠를 못 잡으면, 두 요청이
    이 구간을 동시에 지날 수 없다는 뜻이다 — TOCTOU 창이 닫힌다.
    """
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as writer:
        d4_lineage.lock_lab_for_lineage_write(writer)
        key = _lock_key(writer)

        with scoped_ro(session_factory, ACC_A_RES, LAB_A) as observer:
            got = observer.execute(
                text("SELECT pg_try_advisory_xact_lock(:k)"), {"k": key}).scalar_one()
            assert got is False, (
                "다른 커넥션이 같은 열쇠를 잡았다 — 락이 실제로 걸리지 않았다")


def test_the_lock_is_released_when_the_transaction_ends(session_factory) -> None:
    """**트랜잭션 락이다** — 세션 락이 아니다.

    `pg_advisory_xact_lock` 이 아니라 세션 단위로 잡으면 커넥션이 풀로 돌아가도 락이
    남아, 다음 요청이 남의 락에 걸린다. 「요청 하나 = 트랜잭션 하나」와 수명이 같아야 한다.
    """
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as writer:
        d4_lineage.lock_lab_for_lineage_write(writer)
        key = _lock_key(writer)
    # 위 블록이 rollback 으로 끝났다 — 락도 함께 풀려야 한다.
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as after:
        assert after.execute(
            text("SELECT pg_try_advisory_xact_lock(:k)"), {"k": key}).scalar_one() is True, \
            "트랜잭션이 끝났는데 락이 남아 있다 — 커넥션 풀에 락이 새어 나간다"


def test_add_parent_takes_the_lock_before_it_checks_for_a_cycle(session_factory) -> None:
    """**락이 검사보다 먼저다.**

    검사 뒤에 잡으면 창이 그대로 남는다 — 두 요청이 나란히 검사를 통과한 다음
    차례로 락을 잡고 차례로 삽입한다. 순서가 곧 이 수정의 전부다.
    """
    import inspect

    source = inspect.getsource(d4_lineage.add_parent)
    lock_at = source.find("lock_lab_for_lineage_write")
    check_at = source.find("would_create_cycle")
    insert_at = source.find("_INSERT_EDGE")
    assert lock_at != -1, "add_parent 가 락을 잡지 않는다"
    assert lock_at < check_at < insert_at, (
        "락 → 검사 → 삽입 순서가 아니다 — 검사 뒤에 잡으면 창이 남는다")


def test_the_lock_is_scoped_to_the_lab_not_the_whole_table(session_factory) -> None:
    """**연구실 단위다.** 전역 락이면 한 연구실의 계보 쓰기가 남의 연구실을 멈춘다.

    열쇠가 `current_lab_id()` 에서 나오므로 다른 경계에서는 다른 값이 된다.
    """
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as a:
        key_a = _lock_key(a)
    from conftest import ACC_B_PROF, LAB_B
    with scoped_ro(session_factory, ACC_B_PROF, LAB_B) as b:
        key_b = _lock_key(b)
    assert key_a != key_b, "두 연구실이 같은 락을 나눠 쓴다 — 남의 쓰기를 막는다"


def test_a_self_parent_is_still_refused(session_factory) -> None:
    """락을 넣어도 **기존 규칙이 그대로 산다** — 회귀 방지."""
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        from conftest import DS_A1
        assert d4_lineage.would_create_cycle(
            session, child_id=Ulid(DS_A1), parent_id=Ulid(DS_A1)) is True
