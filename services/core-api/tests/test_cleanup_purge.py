"""시험 간 되돌리기(`conftest.purge_test_rows`)가 **시계에 기대지 않는다**는 오라클.

왜 있는가 (실측 2026-09-13 · `service-tests-core-api` 비결정 red):
호스트(WSL2)의 실시간 시계가 이따금 **뒤로 점프한다** — 한 pytest 프로세스 안에서 순번이
19 → 20 으로 늘어나는 동안 `time.time()` 이 151 ms 줄어든 것을 실측했고, 컨테이너 postgres 의
`now()` 도 같은 커널 시계라 함께 움직인다. 되돌리기가 「기준 시각 이후 행만 지운다」였을 때
그 점프 뒤에 만들어진 행은 기준 시각보다 **앞선** 시각을 달고 태어나 삭제 대상에서 빠졌다.
남은 `d4_lineage_edge` 한 줄이 `d3_dataset` DELETE 를 FK 로 막으면 되돌리기 트랜잭션 전체가
무효가 되어 **삭제도 시드 복구도 통째로 사라졌고**, 그 회차 이후의 모든 개수 오라클이
(`test_cross_tenant`·`test_scope_kernel`·`test_search_execution`·`test_storage_maintenance`)
연구실 A 의 데이터셋을 2 가 아닌 4~8 로 셌다.

그래서 오라클은 「시각을 뒤로 돌려도 되돌리기가 그 행을 지운다」다.
"""
from __future__ import annotations

from conftest import (
    ACC_A_PROF,
    DS_A1,
    LAB_A,
    _cleanup_scope,
    purge_test_rows,
    snapshot_test_rows,
)


def _count(sql, statement: str, params: dict | None = None) -> int:
    return sql(statement, params, account_id=ACC_A_PROF, lab_id=LAB_A)[0]["n"]


def test_purge_removes_rows_stamped_before_the_snapshot(session_factory, sql) -> None:
    """시계가 뒤로 간 뒤 태어난 행 — 시각은 기준점보다 **앞서** 있고, 그래도 지워져야 한다."""
    snapshot = None
    marker = session_factory()
    try:
        marker.begin()
        _cleanup_scope(marker)
        snapshot = snapshot_test_rows(marker)
    finally:
        marker.rollback()
        marker.close()

    # 시계가 1 초 뒤로 점프한 상황을 그대로 만든다 — 기준점보다 **1 초 앞선** 시각의 행.
    sql("""INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id,
                                   uploaded_at, last_modified_at)
             VALUES ('0000000000000000000000DSX1', current_lab_id(),
                     :acc, :acc, now() - interval '1 second', now() - interval '1 second')""",
        {"acc": ACC_A_PROF}, account_id=ACC_A_PROF, lab_id=LAB_A)
    sql("""INSERT INTO d4_lineage_edge (id, lab_id, child_dataset_id, parent_dataset_id,
                                        origin, confirmed_by_account_id, confirmed_at)
             VALUES ('0000000000000000000000EDX1', current_lab_id(),
                     '0000000000000000000000DSX1', :parent, 'manual', :acc,
                     now() - interval '1 second')""",
        {"acc": ACC_A_PROF, "parent": DS_A1}, account_id=ACC_A_PROF, lab_id=LAB_A)

    assert _count(sql, "SELECT count(*) AS n FROM d3_dataset") == 3

    session = session_factory()
    try:
        session.begin()
        _cleanup_scope(session)
        purge_test_rows(session, snapshot)
        session.commit()
    finally:
        session.close()

    assert _count(sql, "SELECT count(*) AS n FROM d4_lineage_edge"
                       " WHERE id = '0000000000000000000000EDX1'") == 0, \
        "기준점보다 앞선 시각의 계보 줄이 남았다 — 다음 `d3_dataset` DELETE 가 FK 로 막힌다."
    assert _count(sql, "SELECT count(*) AS n FROM d3_dataset") == 2, \
        "기준점보다 앞선 시각의 데이터셋이 남았다 — 이후 모든 개수 오라클이 틀어진다."


def test_purge_keeps_the_seed_rows_it_did_not_make(session_factory, sql) -> None:
    """되돌리기는 **시드를 지우지 않는다.** 남는 것이 없으면 오라클도 없다."""
    marker = session_factory()
    try:
        marker.begin()
        _cleanup_scope(marker)
        snapshot = snapshot_test_rows(marker)
    finally:
        marker.rollback()
        marker.close()

    session = session_factory()
    try:
        session.begin()
        _cleanup_scope(session)
        purge_test_rows(session, snapshot)
        session.commit()
    finally:
        session.close()

    assert _count(sql, "SELECT count(*) AS n FROM d3_dataset") == 2
    # `0032_private_owner_access` 이후 A 교수는 잠긴 DSA2의 소유자라 시드 FA3도 보인다.
    assert _count(sql, "SELECT count(*) AS n FROM d3_file") == 3
    assert _count(sql, "SELECT count(*) AS n FROM d6_project") == 1
    assert _count(sql, "SELECT count(*) AS n FROM d4_lineage_edge") == 1
