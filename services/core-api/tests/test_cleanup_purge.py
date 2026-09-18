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
    ACC_B_PROF,
    DS_A1,
    DS_B1,
    LAB_A,
    LAB_B,
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
    assert _count(sql, "SELECT count(*) AS n FROM d3_file") == 3
    assert _count(sql, "SELECT count(*) AS n FROM d6_project") == 1
    assert _count(sql, "SELECT count(*) AS n FROM d4_lineage_edge") == 1


#: 시험이 만드는 계정 한 벌. 역할·스위치까지 함께 넣는 이유는 아래 주석에 적었다.
_NEW_ACCOUNT = "0000000000000000000000ACX1"


def test_purge_removes_the_account_rows_a_test_made(session_factory, sql) -> None:
    """계정 계열도 **되돌리기가 줍는다** — 시험이 손으로 지우지 않는다.

    왜 있는가 (실측 2026-09-17 · 이슈 #47 · `service-tests-core-api` 비결정 red):
    `d1_account` 계열이 `_CLEANUP` 에 없어서 계정을 만드는 시험은 되돌리기를 `try/finally` 로
    직접 적었고(`test_lab_members.py` 의 `_purge_member`), 계정 생성이 중간에 실패하면 그
    `finally` 가 아예 서지 않아 A 연구실에 계정이 영구히 남았다. 남은 한 행은 곧바로
    `memberCount`(`d1_identity.py` 의 `count(*) FROM d1_account`) 를 세는 다음 파일의 오라클을
    틀리게 한다 — 내부 worker 수가 바뀌면 오염원과 피해자의 동거 여부가 바뀌어 판정이 흔들린다.

    양성·음성을 한 시험에서 함께 센다 — 되돌리기 **전 3**(시드 2 ＋ 시험 1) · **후 2**.
    「대상이 0 건이라 통과」 형태를 쓰지 않는다.
    """
    marker = session_factory()
    try:
        marker.begin()
        _cleanup_scope(marker)
        snapshot = snapshot_test_rows(marker)
    finally:
        marker.rollback()
        marker.close()

    # ⚠ 스위치 줄까지 넣는다. `d2_permission_switch` 는 `d1_account` 를 **CASCADE 없이**
    #   참조하므로(`db/platform/schema.sql` 앵커 `CREATE TABLE d2_permission_switch`), 이 표가
    #   되돌리기에서 빠지면 `d1_account` DELETE 가 FK 로 막히고 그 순간 되돌리기 **트랜잭션
    #   전체**가 무효가 된다 — 삭제도 `_RESTORE` 도 함께 사라진다(2026-09-13 에 겪은 형태다).
    sql("""INSERT INTO d1_account (id, lab_id, name, email)
             VALUES (:id, current_lab_id(), '되돌리기 시험 계정', 'purge-acx1@example.com')""",
        {"id": _NEW_ACCOUNT}, account_id=ACC_A_PROF, lab_id=LAB_A)
    sql("""INSERT INTO d2_member_role (account_id, lab_id, role)
             VALUES (:id, current_lab_id(), '연구원')""",
        {"id": _NEW_ACCOUNT}, account_id=ACC_A_PROF, lab_id=LAB_A)
    sql("""INSERT INTO d2_permission_switch (account_id, lab_id, switch, enabled)
             VALUES (:id, current_lab_id(), '승인 위임', true)""",
        {"id": _NEW_ACCOUNT}, account_id=ACC_A_PROF, lab_id=LAB_A)

    assert _count(sql, "SELECT count(*) AS n FROM d1_account") == 3, \
        "되돌리기 전에는 시드 2 ＋ 시험 1 이어야 한다 — 대상 0 건을 통과로 세지 않는다."
    assert _count(sql, "SELECT count(*) AS n FROM d2_member_role") == 3
    assert _count(sql, "SELECT count(*) AS n FROM d2_permission_switch") == 5

    session = session_factory()
    try:
        session.begin()
        _cleanup_scope(session)
        purge_test_rows(session, snapshot)
        session.commit()
    finally:
        session.close()

    assert _count(sql, "SELECT count(*) AS n FROM d1_account WHERE id = :id",
                  {"id": _NEW_ACCOUNT}) == 0, \
        "시험이 만든 계정이 남았다 — 다음 파일의 `memberCount` 오라클이 이 행을 함께 센다."
    assert _count(sql, "SELECT count(*) AS n FROM d1_account") == 2, \
        "A 연구실 계정 수가 시드 2 로 돌아오지 않았다."
    assert _count(sql, "SELECT count(*) AS n FROM d2_member_role") == 2, \
        "역할 줄이 남았다 — 계정 DELETE 가 FK 로 막히는 자리다."
    assert _count(sql, "SELECT count(*) AS n FROM d2_permission_switch") == 4, \
        "스위치 줄이 남았다 — 계정 DELETE 가 FK 로 막히는 자리다."
    # 시드는 지우지 않는다. 남는 것이 없으면 오라클도 없다(A 2건 ＋ 경계 밖 B 1건 = 시드 3건).
    assert sql("SELECT count(*) AS n FROM d1_account", None,
               account_id=ACC_B_PROF, lab_id=LAB_B)[0]["n"] == 1, \
        "되돌리기가 B 연구실 시드 계정을 지웠다."


# ═══════════ 되돌리기가 **다른 연구실** 행도 줍는다 (2026-09-18 · 이슈 #47) ═══════════
# 왜 있는가 (실측 2026-09-18 · `COLAB_SERVICE_TEST_JOBS=12` 간헐 red):
#   되돌리기가 앱 롤로 서던 때에는 경계가 A 연구실이라 RLS 가 다른 연구실 행을 숨겼다.
#   시험이 커밋한 LAB_B 행은(`test_admin_actor_visibility.py:38` 매개변수 2회 · `:62` — 한 회차에
#   LAB_B 데이터셋 3벌) 스냅숏에도 없고 DELETE 에도 안 걸려 **한 번도 회수되지 않았고**, 같은
#   xdist worker 의 다음 시험으로 새어 절대 집합 오라클을 틀리게 했다
#   (`test_pool_no_leak.py:48`·`:99`·`:106` 의 `{DS_B1}`).
#   그래서 되돌리기만 superuser(`conftest.purge_session_factory`)로 세웠다.
#
# 오라클은 둘이다 — ㈎ 시험이 만든 LAB_B 행은 사라지고 **시드 LAB_B 행은 남는다**,
#                  ㈏ 시험이 만든 LAB_C **계정**은 남는다(계정 계열 예외).

#: 이 파일이 만드는 다른 연구실 행 한 벌. 시드 ID 와 겹치지 않는 자리를 골랐다.
_NEW_LAB_B_DATASET = "0000000000000000000000DSY1"
_NEW_LAB_C_ACCOUNT = "0000000000000000000000ACY1"
#: 시드의 셋째 연구실(`tests/fixtures/seed.sql:15` — 계정 발급 시험 연구실).
#: `test_operator_designation.py:29` 가 쓰는 값과 같다.
_LAB_C = "0000000000000000000000000C"


def _snapshot_as_superuser(purge_session_factory) -> dict:
    session = purge_session_factory()
    try:
        session.begin()
        _cleanup_scope(session)
        return snapshot_test_rows(session)
    finally:
        session.rollback()
        session.close()


def _purge_as_superuser(purge_session_factory, snapshot: dict) -> dict:
    session = purge_session_factory()
    try:
        session.begin()
        _cleanup_scope(session)
        outside = purge_test_rows(session, snapshot)
        session.commit()
        return outside
    finally:
        session.close()


def _su(purge_session_factory, statement: str, params: dict | None = None) -> list:
    """되돌리기와 **같은 접속**으로 직접 쓰고 읽는다 — 경계 밖의 사실을 보는 유일한 자리."""
    from sqlalchemy import text

    session = purge_session_factory()
    try:
        session.begin()
        result = session.execute(text(statement), params or {})
        rows = [dict(r) for r in result.mappings()] if result.returns_rows else []
        session.commit()
        return rows
    finally:
        session.close()


def test_purge_removes_a_lab_b_row_a_test_made_and_keeps_the_lab_b_seed(
        purge_session_factory, sql) -> None:
    """시험이 커밋한 LAB_B 데이터셋은 회수되고, 시드 `DS_B1` 은 그대로다.

    양성·음성을 한 시험에서 함께 센다 — 되돌리기 **전 2**(시드 1 ＋ 시험 1) · **후 1**.
    「대상이 0건이라 통과」 형태를 쓰지 않는다.
    """
    snapshot = _snapshot_as_superuser(purge_session_factory)

    _su(purge_session_factory,
        """INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id,
                                   uploaded_at, last_modified_at)
             VALUES (:id, :lab, :acc, :acc, now(), now())""",
        {"id": _NEW_LAB_B_DATASET, "lab": LAB_B, "acc": ACC_B_PROF})

    before = {r["id"] for r in _su(purge_session_factory,
                                   "SELECT id FROM d3_dataset WHERE lab_id = :lab",
                                   {"lab": LAB_B})}
    assert before == {DS_B1, _NEW_LAB_B_DATASET}, \
        "시험이 만든 LAB_B 데이터셋이 애초에 없다 — 대상 0건을 통과로 세지 않는다."

    outside = _purge_as_superuser(purge_session_factory, snapshot)

    after = {r["id"] for r in _su(purge_session_factory,
                                  "SELECT id FROM d3_dataset WHERE lab_id = :lab",
                                  {"lab": LAB_B})}
    assert _NEW_LAB_B_DATASET not in after, \
        "시험이 만든 LAB_B 데이터셋이 남았다 — 다음 시험의 절대 집합이 이 행을 함께 센다."
    assert after == {DS_B1}, \
        "되돌리기가 LAB_B 시드 데이터셋까지 지웠다 — 남는 것이 없으면 오라클도 없다."
    assert outside.get("d3_dataset") == 1, \
        "A 연구실 밖에서 지운 건수를 기록하지 않았다 — 누출을 세는 자리가 사라진다."
    # A 연구실 시드는 그대로다(앱 롤로 다시 본다 — 경계 안쪽의 셈도 함께 지킨다).
    assert _count(sql, "SELECT count(*) AS n FROM d3_dataset") == 2


def test_purge_keeps_an_account_a_test_made_in_another_lab(purge_session_factory, sql) -> None:
    """계정 계열은 **A 연구실 안에서만** 지운다 — LAB_C 계정은 되돌리기가 건드리지 않는다.

    이유는 스키마에 있다: `d8_activity.actor_account_id` 가 `d1_account(id)` 를 ON DELETE 없이
    참조하고(`db/platform/versions/0001_p0_platform.py:387`) `d8_activity` 는 append-only
    트리거가 DELETE 를 거부한다(`:394-396`). 행위한 계정은 영영 못 지운다 — 지우려 들면
    되돌리기 **트랜잭션 전체**가 무효가 된다. 백오피스 시험 30여 건이 LAB_C 에 계정을
    일부러 남기므로(`test_admin_role_scope.py:13-14`) 그 자리는 매 회차 터졌을 것이다.
    """
    snapshot = _snapshot_as_superuser(purge_session_factory)

    _su(purge_session_factory,
        """INSERT INTO d1_account (id, lab_id, name, email)
             VALUES (:id, :lab, '다른 연구실 시험 계정', 'purge-acy1@example.com')""",
        {"id": _NEW_LAB_C_ACCOUNT, "lab": _LAB_C})
    try:
        _purge_as_superuser(purge_session_factory, snapshot)

        assert _su(purge_session_factory,
                   "SELECT count(*) AS n FROM d1_account WHERE id = :id",
                   {"id": _NEW_LAB_C_ACCOUNT})[0]["n"] == 1, \
            "되돌리기가 LAB_C 계정을 지웠다 — 행위 기록이 있는 계정이면 이 DELETE 가 FK 로 막혀 " \
            "되돌리기 트랜잭션 전체가 무효가 된다."
        # A 연구실 계정은 여전히 시드 2 로 돌아온다 — 예외가 삭제 자체를 끄지 않았다.
        assert _count(sql, "SELECT count(*) AS n FROM d1_account") == 2
    finally:
        # 이 파일이 만든 것은 이 파일이 치운다 — 되돌리기가 줍지 않는 자리라서다.
        _su(purge_session_factory, "DELETE FROM d1_account WHERE id = :id",
            {"id": _NEW_LAB_C_ACCOUNT})
