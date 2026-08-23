"""`d3_dataset.file_count` 드리프트 — 메타 층의 조각 수가 실제 조각 수와 어긋나면 red.

`PLAN-SoT §9-㊼` 이 조각 수를 본체 테이블 밖으로 옮기면서 치른 대가는 **비정규화된 값 하나**다.
비정규화의 유일한 위험은 조용한 어긋남이므로, 관례가 아니라 이 시험이 지킨다.

**세는 쪽도 정책을 받는다는 것이 이 파일의 어려운 지점이다.** 앱 롤로 잠긴 데이터셋의 `d3_file` 을
세면 0 이 나온다 — 그 0 이 바로 고치려던 결함이다. 그래서 실제 조각 수를 얻을 때는
같은 트랜잭션 안에서 **유효한 허용 줄을 넣어 본체를 정식으로 연다**(끝나면 rollback).
경계를 우회하지 않는다 — 정책이 열어 주는 문으로 들어간다.
"""
from __future__ import annotations

from sqlalchemy import text

from conftest import (ACC_A_PROF, ACC_B_PROF, DS_A2, LAB_A, LAB_B, scoped_ro)

_DATASETS = text("SELECT id, file_count FROM d3_dataset ORDER BY id")
_REAL = text("SELECT dataset_id, count(*) AS n FROM d3_file GROUP BY dataset_id")
_OPEN_ALL = text("""
    INSERT INTO d2_dataset_access_grant
      (id, lab_id, dataset_id, grantee_account_id, approver_account_id, approved_at, expires_at)
    SELECT 'GRANT' || substr(d.id, 6), d.lab_id, d.id, CAST(:me AS ulid), CAST(:me AS ulid),
           now() - interval '1 day', now() + interval '365 days'
      FROM d3_dataset d
     WHERE NOT EXISTS (SELECT 1 FROM d2_dataset_access_grant g
                        WHERE g.dataset_id = d.id AND g.grantee_account_id = CAST(:me AS ulid))
""")

SCOPES = [(ACC_A_PROF, LAB_A), (ACC_B_PROF, LAB_B)]


def _drift(db) -> list[tuple[str, int, int]]:
    """(데이터셋, 메타가 말하는 수, 실제 수) 중 어긋난 것만."""
    db.execute(_OPEN_ALL, {"me": db.execute(
        text("SELECT current_account_id()")).scalar_one()})
    real = {r[0]: r[1] for r in db.execute(_REAL).all()}
    return [(i, meta, real.get(i, 0))
            for i, meta in db.execute(_DATASETS).all() if meta != real.get(i, 0)]


def test_file_count_never_drifts_from_the_real_row_count(session_factory) -> None:
    """시드 전 행 — 메타의 조각 수 = 실제 조각 수.

    red 만드는 법 — 아무 데이터셋의 `file_count` 를 손으로 하나 올린다
    (아래 `test_a_hand_written_file_count_is_caught` 가 그 훼손을 실제로 만들어 본다).
    """
    for account, lab in SCOPES:
        with scoped_ro(session_factory, account, lab) as db:
            assert db.execute(_DATASETS).all(), "데이터셋이 0건이다 — 대상 0건은 통과가 아니다."
            assert _drift(db) == [], "조각 수가 실제 행수와 어긋났다."


def test_a_hand_written_file_count_is_caught(session_factory) -> None:
    """이 시험이 오라클인지 자기가 증명한다 — 값을 훼손하면 반드시 잡힌다."""
    with scoped_ro(session_factory, ACC_A_PROF, LAB_A) as db:
        assert _drift(db) == []
        db.execute(text("UPDATE d3_dataset SET file_count = file_count + 1 WHERE id = :d"),
                   {"d": DS_A2})
        assert [d[0] for d in _drift(db)] == [DS_A2], \
            "손으로 어긋내도 못 잡는다 — 이 시험은 오라클이 아니다."


def test_the_trigger_keeps_up_with_insert_delete_and_move(session_factory) -> None:
    """트리거가 세 경로 전부를 따라온다 — 넣기 · 지우기 · 다른 데이터셋으로 옮기기.

    한 문장이 여러 조각을 한꺼번에 건드리는 경우까지 본다 (문장 단위 트리거 + 전이 테이블).
    """
    with scoped_ro(session_factory, ACC_A_PROF, LAB_A) as db:
        db.execute(_OPEN_ALL, {"me": ACC_A_PROF})
        before = dict(db.execute(_DATASETS).all())

        db.execute(text("""
            INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key)
            SELECT 'ZZZZZZZZZZZZZZZZZZZZZZZZZ' || n, :lab, :d, '본체',
                   'drift-' || n || '.nc', 1, 'k/drift-' || n
              FROM generate_series(1, 3) AS n
        """), {"lab": LAB_A, "d": DS_A2})
        assert dict(db.execute(_DATASETS).all())[DS_A2] == before[DS_A2] + 3
        assert _drift(db) == []

        db.execute(text("UPDATE d3_file SET dataset_id = :to WHERE id LIKE 'ZZZZZZZZ%'"),
                   {"to": "0000000000000000000000DSA1"})
        assert _drift(db) == []

        db.execute(text("DELETE FROM d3_file WHERE id LIKE 'ZZZZZZZZ%'"))
        assert dict(db.execute(_DATASETS).all()) == before
