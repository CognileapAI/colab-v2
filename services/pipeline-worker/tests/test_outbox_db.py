"""outbox 원장 실물 — `d5_*` 표에 **실제로** 쓴다 (W1 이 만든 표. 새로 만들지 않는다).

DB URL 은 `COLAB_PIPELINE_DB_URL` 로 받는다. **미지정이면 skip 이 아니라 fail** —
검사를 못 한 것을 통과로 세지 않는다(`CLAUDE.md §4`). 로컬에서 DB 없이 돌릴 때는
`-m "not dbint"` 로 **명시적으로** 뺀다.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from colab_pipeline.d5.events import EVENT_TYPES
from colab_pipeline.domains.d5_ingestion import (
    IngestionService,
    SqlLedger,
    UploadFileWork,
    UploadWork,
    reap_expired_uploads,
    relay_unpublished,
)
from fixture_builders import make_readable_geotiff

pytestmark = pytest.mark.dbint

_ENV = "COLAB_PIPELINE_DB_URL"
# 시드(`services/core-api/tests/fixtures/seed.sql`)의 A 연구실·계정. D1 은 shared kernel 이라
# `d5_*` 의 FK 가 이 값을 요구한다 — 지어낸 ID 를 넣으면 FK 가 죽는다.
_LAB = "0000000000000000000000000A"
_ACC = "000000000000000000000000A1"


@pytest.fixture()
def session():
    url = os.environ.get(_ENV)
    if not url:
        pytest.fail(f"{_ENV} 가 없다 — DB 시험을 DB 없이 green 으로 세지 않는다 (CLAUDE.md §4)")
    from sqlalchemy import text
    from sqlalchemy.orm import sessionmaker

    from colab_pipeline.kernel.db import make_engine

    engine = make_engine(url)
    factory = sessionmaker(bind=engine, future=True)
    s = factory()
    s.begin()
    # 스코프 커널과 같은 방식 — 트랜잭션 스코프 GUC. RLS 가 이 값으로 판정한다.
    s.execute(text("SELECT set_config('app.current_lab', :v, true)"), {"v": _LAB})
    s.execute(text("SELECT set_config('app.current_account', :v, true)"), {"v": _ACC})
    try:
        yield s
    finally:
        s.rollback()
        s.close()
        engine.dispose()


def _ulid(tail: str) -> str:
    return ("01JQ" + "0" * 22)[: 26 - len(tail)] + tail


def _accept(session, upload_id: str, *, ttl_hours: int = 24) -> None:
    from sqlalchemy import text
    session.execute(text("""
        INSERT INTO d5_upload (id, lab_id, uploader_account_id, expires_at)
        VALUES (:id, :lab, :acc, now() + (:h || ' hours')::interval)
    """), {"id": upload_id, "lab": _LAB, "acc": _ACC, "h": ttl_hours})
    # `upload.accepted` 는 core-api 가 내는 유일한 이벤트다 — 여기서는 접수 사실을 세운다.
    session.execute(text("""
        INSERT INTO d5_pipeline_event
          (id, lab_id, actor_account_id, upload_id, event_type, schema_version, source,
           idempotency_key, payload)
        VALUES (:eid, :lab, :acc, :uid, 'upload.accepted', '1.0', 'core-api',
                :key, '{"files": []}'::jsonb)
    """), {"eid": _ulid("ACC1"), "lab": _LAB, "acc": _ACC, "uid": upload_id,
           "key": f"upload.accepted:{upload_id}"})


def test_worker_writes_all_stage_events_into_the_w1_ledger(session, tmp_path):
    from sqlalchemy import text
    upload_id = _ulid("V001")
    _accept(session, upload_id)
    src = make_readable_geotiff(tmp_path / "ok.tif")
    fid = _ulid("F001")
    session.execute(text("""
        INSERT INTO d5_upload_file (id, lab_id, upload_id, kind, file_name, storage_key)
        VALUES (:id, :lab, :uid, '본체', :name, :key)
    """), {"id": fid, "lab": _LAB, "uid": upload_id, "name": src.name, "key": f"s3://{src.name}"})

    svc = IngestionService(SqlLedger(session))
    res = svc.process_upload(UploadWork(
        upload_id=upload_id, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "w",
        files=[UploadFileWork(file_id=fid, path=src, kind="본체", file_name=src.name)],
    ))
    assert [e["type"] for e in res.events][-1] == "upload.ready"

    rows = session.execute(text(
        "SELECT event_type, source, idempotency_key, published_at "
        "FROM d5_pipeline_event WHERE upload_id = :u ORDER BY occurred_at, event_type"
    ), {"u": upload_id}).all()
    types = {r[0] for r in rows}
    assert types == set(EVENT_TYPES) - {"upload.failed"}
    assert all(r[3] is None for r in rows)          # 아직 발행 전 — 릴레이가 채운다
    assert {r[1] for r in rows if r[0] == "upload.accepted"} == {"core-api"}
    assert {r[1] for r in rows if r[0] != "upload.accepted"} == {"pipeline-worker"}

    status = session.execute(text(
        "SELECT ready, renderable, metadata_complete FROM d5_upload WHERE id = :u"
    ), {"u": upload_id}).one()
    assert status[0] is True and status[1] is True


def test_redelivery_does_not_duplicate_rows(session, tmp_path):
    from sqlalchemy import text
    upload_id = _ulid("V002")
    _accept(session, upload_id)
    src = make_readable_geotiff(tmp_path / "ok.tif")
    fid = _ulid("F002")
    session.execute(text("""
        INSERT INTO d5_upload_file (id, lab_id, upload_id, kind, file_name, storage_key)
        VALUES (:id, :lab, :uid, '본체', :name, :key)
    """), {"id": fid, "lab": _LAB, "uid": upload_id, "name": src.name, "key": "s3://x"})
    work = UploadWork(
        upload_id=upload_id, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "w",
        files=[UploadFileWork(file_id=fid, path=src, kind="본체", file_name=src.name)],
    )
    svc = IngestionService(SqlLedger(session))
    svc.process_upload(work)
    n1 = session.execute(text("SELECT count(*) FROM d5_pipeline_event WHERE upload_id=:u"),
                         {"u": upload_id}).scalar_one()
    svc.process_upload(work)
    n2 = session.execute(text("SELECT count(*) FROM d5_pipeline_event WHERE upload_id=:u"),
                         {"u": upload_id}).scalar_one()
    assert n1 == n2


def test_relay_marks_published_and_is_the_only_thing_that_does(session, tmp_path):
    from sqlalchemy import text
    upload_id = _ulid("V003")
    _accept(session, upload_id)
    src = make_readable_geotiff(tmp_path / "ok.tif")
    fid = _ulid("F003")
    session.execute(text("""
        INSERT INTO d5_upload_file (id, lab_id, upload_id, kind, file_name, storage_key)
        VALUES (:id, :lab, :uid, '본체', :name, 's3://x')
    """), {"id": fid, "lab": _LAB, "uid": upload_id, "name": src.name})
    IngestionService(SqlLedger(session)).process_upload(UploadWork(
        upload_id=upload_id, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "w",
        files=[UploadFileWork(file_id=fid, path=src, kind="본체", file_name=src.name)],
    ))
    delivered: list[dict] = []
    n = relay_unpublished(SqlLedger(session), publish=delivered.append)
    assert n == len(delivered) >= 6
    left = session.execute(text(
        "SELECT count(*) FROM d5_pipeline_event WHERE upload_id=:u AND published_at IS NULL"
    ), {"u": upload_id}).scalar_one()
    assert left == 0
    assert relay_unpublished(SqlLedger(session), publish=delivered.append) == 0


def test_reaper_deletes_expired_unregistered_uploads(session):
    from sqlalchemy import text
    upload_id = _ulid("V004")
    # `CHECK (expires_at > created_at)` 때문에 만료된 행을 직접 넣을 수 없다 —
    # 표가 그것을 막는 것이 옳다. 그래서 **시각을 앞으로 돌려** 만료를 만든다.
    _accept(session, upload_id, ttl_hours=1)
    assert session.execute(text("SELECT count(*) FROM d5_upload WHERE id=:u"),
                           {"u": upload_id}).scalar_one() == 1
    later = datetime.now(timezone.utc) + timedelta(hours=2)
    gone = reap_expired_uploads(SqlLedger(session), now=later)
    assert upload_id in gone
    assert session.execute(text("SELECT count(*) FROM d5_upload WHERE id=:u"),
                           {"u": upload_id}).scalar_one() == 0
    # 이벤트도 함께 사라진다 (ON DELETE CASCADE) — 원장은 남지 않는다 (`〈64〉-ⓒ`)
    assert session.execute(text("SELECT count(*) FROM d5_pipeline_event WHERE upload_id=:u"),
                           {"u": upload_id}).scalar_one() == 0


def test_reaper_leaves_registered_uploads_alone(session):
    from sqlalchemy import text
    upload_id = _ulid("V005")
    _accept(session, upload_id, ttl_hours=1)
    session.execute(text("UPDATE d5_upload SET registered_at = now() WHERE id=:u"),
                    {"u": upload_id})
    later = datetime.now(timezone.utc) + timedelta(hours=2)
    assert upload_id not in reap_expired_uploads(SqlLedger(session), now=later)


def test_axis_row_is_two_booleans_and_empty_axis_is_refused_by_the_db(session, tmp_path):
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError
    upload_id = _ulid("V006")
    _accept(session, upload_id)
    import numpy as np
    lon = tmp_path / "grid_x.npy"
    np.save(lon, np.repeat(np.linspace(118.8, 133.5, 8)[None, :], 8, axis=0))
    fid = _ulid("F006")
    ledger = SqlLedger(session)
    ledger.record_file_axes_row(
        file_id=fid, lab_id=_LAB, upload_id=upload_id, file_name=lon.name,
        storage_key="s3://grid_x.npy", carries_lat=False, carries_lon=True,
    )
    row = session.execute(text(
        "SELECT kind, carries_lat, carries_lon FROM d5_upload_file WHERE id=:f"), {"f": fid}).one()
    assert row == ("기준 격자 파일", False, True)

    with pytest.raises(IntegrityError):
        session.execute(text("""
            INSERT INTO d5_upload_file (id, lab_id, upload_id, kind, file_name, storage_key,
                                        carries_lat, carries_lon)
            VALUES (:id, :lab, :uid, '기준 격자 파일', 'empty.npy', 's3://e', false, false)
        """), {"id": _ulid("F007"), "lab": _LAB, "uid": upload_id})
    session.rollback()
    session.begin()


# ════════════════════════════════════════════════════════════════════════════
# 후속 레인 — `〈69〉-⑴`(격자 행은 워커가 만든다) · `〈67〉`-㉠㉡(처리 중 제외)
# ════════════════════════════════════════════════════════════════════════════

def test_worker_creates_the_grid_file_row_that_acceptance_did_not(session, tmp_path):
    """`〈69〉-⑴` — 접수는 본체 행까지만. 격자 행은 워커가 축을 정한 뒤 **세운다**."""
    from sqlalchemy import text
    import numpy as np
    upload_id = _ulid("V008")
    _accept(session, upload_id)
    src = make_readable_geotiff(tmp_path / "ok.tif")
    fid, gid = _ulid("F008"), _ulid("G008")
    # 접수가 만드는 것은 본체 행뿐이다 (`core-api` 의 `_INSERT_FILE` 이 격자를 건너뛴다)
    session.execute(text("""
        INSERT INTO d5_upload_file (id, lab_id, upload_id, kind, file_name, storage_key)
        VALUES (:id, :lab, :uid, '본체', :name, 's3://ok.tif')
    """), {"id": fid, "lab": _LAB, "uid": upload_id, "name": src.name})
    assert session.execute(text(
        "SELECT count(*) FROM d5_upload_file WHERE upload_id=:u AND kind='기준 격자 파일'"
    ), {"u": upload_id}).scalar_one() == 0

    lon = tmp_path / "Lon_x.npy"
    np.save(lon, np.repeat(np.linspace(118.8, 133.5, 8)[None, :], 8, axis=0))
    res = IngestionService(SqlLedger(session)).process_upload(UploadWork(
        upload_id=upload_id, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "w",
        files=[UploadFileWork(file_id=fid, path=src, kind="본체", file_name=src.name),
               UploadFileWork(file_id=gid, path=lon, kind="기준 격자 파일",
                              file_name=lon.name, storage_key="s3://Lon_x.npy")],
    ))
    assert [e["type"] for e in res.events][-1] == "upload.ready"
    row = session.execute(text(
        "SELECT kind, carries_lat, carries_lon, storage_key FROM d5_upload_file WHERE id=:g"
    ), {"g": gid}).one()
    assert row == ("기준 격자 파일", False, True, "s3://Lon_x.npy")


def test_no_grid_row_is_created_when_the_axis_cannot_be_determined(session, tmp_path):
    """판별 실패 = 그 파일만 거절. **행이 안 생기고** 업로드는 완주한다(`〈63〉-ⓒ`)."""
    from sqlalchemy import text
    import numpy as np
    upload_id = _ulid("V009")
    _accept(session, upload_id)
    src = make_readable_geotiff(tmp_path / "ok.tif")
    fid, gid = _ulid("F009"), _ulid("G009")
    session.execute(text("""
        INSERT INTO d5_upload_file (id, lab_id, upload_id, kind, file_name, storage_key)
        VALUES (:id, :lab, :uid, '본체', :name, 's3://ok.tif')
    """), {"id": fid, "lab": _LAB, "uid": upload_id, "name": src.name})
    amb = tmp_path / "mystery.npy"
    np.save(amb, np.repeat(np.linspace(30, 43, 8)[:, None], 8, axis=1))
    res = IngestionService(SqlLedger(session)).process_upload(UploadWork(
        upload_id=upload_id, lab_id=_LAB, actor_account_id=_ACC, workdir=tmp_path / "w",
        files=[UploadFileWork(file_id=fid, path=src, kind="본체", file_name=src.name),
               UploadFileWork(file_id=gid, path=amb, kind="기준 격자 파일",
                              file_name=amb.name)],
    ))
    assert [e["type"] for e in res.events][-1] == "upload.ready"   # 등록은 막히지 않는다
    assert gid in res.rejected
    assert session.execute(text("SELECT count(*) FROM d5_upload_file WHERE id=:g"),
                           {"g": gid}).scalar_one() == 0


def test_reaper_leaves_an_upload_that_is_still_being_processed(session):
    """`〈67〉` 이행 제약 ㉡ — 처리 중인 업로드는 **만료 시각을 지나고도 살아남는다**."""
    from sqlalchemy import text
    upload_id = _ulid("V010")
    _accept(session, upload_id, ttl_hours=1)
    # 단계 이벤트가 만료 직전에 들어왔다 = 처리가 진행 중이다
    session.execute(text("""
        INSERT INTO d5_pipeline_event
          (id, lab_id, actor_account_id, upload_id, event_type, schema_version, source,
           occurred_at, idempotency_key, payload)
        VALUES (:eid, :lab, :acc, :uid, 'file.header-parsed', '1.0', 'pipeline-worker',
                now() + interval '110 minutes', :key, '{}'::jsonb)
    """), {"eid": _ulid("EV10"), "lab": _LAB, "acc": _ACC, "uid": upload_id,
           "key": f"file.header-parsed:{upload_id}"})
    later = datetime.now(timezone.utc) + timedelta(hours=2)
    assert upload_id not in reap_expired_uploads(SqlLedger(session), now=later)
    assert session.execute(text("SELECT count(*) FROM d5_upload WHERE id=:u"),
                           {"u": upload_id}).scalar_one() == 1
