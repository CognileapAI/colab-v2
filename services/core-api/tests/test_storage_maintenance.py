"""R-S1-STORAGE: real DB ownership/retention; only S3 transport is a test double."""
from __future__ import annotations

import datetime as dt
import json
import threading

import pytest
from sqlalchemy import text

from conftest import ACC_A_RES, LAB_A
from colab_core.app.storage_maintenance import (
    maintain_storage,
    parse_storage_reclaim_approval,
    run_storage_maintenance,
)
from colab_core.kernel.auth import Subject
from colab_core.kernel.ids import Ulid
from colab_core.kernel.scope import apply_scope

NOW = dt.datetime(2030, 1, 10, tzinfo=dt.timezone.utc)
SUBJECT = Subject(account_id=Ulid(ACC_A_RES), lab_id=Ulid(LAB_A))


@pytest.fixture
def db(session_factory):
    session = session_factory()
    session.begin()
    apply_scope(session, SUBJECT)
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def expired_upload(db, *, registered=False):
    uid, fid = str(Ulid.generate()), str(Ulid.generate())
    key = f"uploads/{uid}/{fid}"
    db.execute(text("""INSERT INTO d5_upload
        (id,lab_id,uploader_account_id,created_at,expires_at,registered_at,ready)
        VALUES (:u,current_lab_id(),current_account_id(),:born,:expires,:reg,true)"""),
        {"u": uid, "born": NOW-dt.timedelta(days=3),
         "expires": NOW-dt.timedelta(days=2), "reg": NOW if registered else None})
    db.execute(text("""INSERT INTO d5_upload_file
        (id,lab_id,upload_id,kind,file_name,storage_key)
        VALUES (:f,current_lab_id(),:u,'본체','sample.nc',:k)"""),
        {"u": uid, "f": fid, "k": key})
    db.execute(text("""INSERT INTO d5_pipeline_event
        (id,lab_id,actor_account_id,upload_id,event_type,schema_version,source,idempotency_key,payload)
        VALUES (:e,current_lab_id(),current_account_id(),:u,'upload.accepted','1.0',
        'core-api',:ik,CAST(:payload AS jsonb))"""),
        {"e": str(Ulid.generate()), "u": uid, "ik": f"upload.accepted:{uid}",
         "payload": json.dumps({"files": [{"fileId":fid,"kind":"본체","fileName":"sample.nc","byteSize":1}]})})
    return uid, fid, key


def exists(db, uid):
    return db.execute(text("SELECT EXISTS(SELECT 1 FROM d5_upload WHERE id=:u)"), {"u":uid}).scalar_one()


class FakeS3:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.deleted: list[str] = []
        self.aborted: list[tuple[str, str]] = []

    def delete_objects(self, keys):
        self.deleted.extend(keys)
        if self.fail:
            from colab_core.kernel.s3 import S3Error
            raise S3Error(500, "InternalError", "partial")

    def abort_multipart_upload(self, key, transfer_ref):
        self.aborted.append((key, transfer_ref))


def maintain(db, s3, *, mode="apply"):
    if mode == "observe":
        return maintain_storage(db, s3=s3, mode=mode, now=NOW, lab_id=LAB_A)
    observed = maintain_storage(
        db, s3=FakeS3(), mode="observe", now=NOW, lab_id=LAB_A)
    approval = parse_storage_reclaim_approval(
        json.dumps(observed.approval_plan), expected_lab_id=LAB_A,
        expected_sha256=observed.plan_sha256)
    return maintain_storage(
        db, s3=s3, mode=mode, now=NOW, lab_id=LAB_A, approval=approval)


def make_all_d3_visible(db):
    """성공 경로는 현재 주체가 연구실 D3 파일 전건을 볼 수 있을 때만 열린다."""
    db.execute(text("UPDATE d2_dataset_access SET state='열림'"))
    db.execute(text("UPDATE d1_lab_profile SET default_visibility='열림' "
                    "WHERE lab_id=current_lab_id()"))


def test_uncoordinated_legacy_reaper_preserves_source_ownership(db):
    """Deleting D5 before source cleanup must fail this test."""
    from colab_core.domains.d5_ingestion import UploadLedgerAdapter
    uid, _, _ = expired_upload(db)
    assert UploadLedgerAdapter(db).reap_expired(NOW) == []
    assert exists(db, uid)


def test_observe_is_the_safe_default_and_changes_nothing(db):
    uid, _, key = expired_upload(db)
    s3 = FakeS3()
    report = maintain(db, s3, mode="observe")
    # 전체 서비스 묶음에서는 앞선 회귀 시험이 남긴 만료 후보도 같은 스코프에 있을 수 있다.
    assert report.candidates >= 1
    assert report.reclaimed_uploads == 0
    assert report.mode == "observe"
    assert s3.deleted == []
    assert exists(db, uid)


def test_apply_deletes_exact_accepted_keys_then_the_locked_ledger(db):
    uid, _, key = expired_upload(db)
    make_all_d3_visible(db)
    s3 = FakeS3()
    report = maintain(db, s3)
    assert report.reclaimed_uploads == 1
    assert s3.deleted == [key]
    assert not exists(db, uid)


def test_axis_unresolved_grid_is_reclaimed_from_the_accepted_event(db):
    uid, _, body_key = expired_upload(db)
    make_all_d3_visible(db)
    grid_id = str(Ulid.generate())
    grid_key = f"uploads/{uid}/grid/lat.nc"
    db.execute(text("""UPDATE d5_pipeline_event
        SET payload = payload || CAST(:grid AS jsonb)
        WHERE upload_id=:u AND event_type='upload.accepted'"""), {
        "u": uid,
        "grid": json.dumps({"files": [
            {"fileId": db.execute(text("SELECT id FROM d5_upload_file WHERE upload_id=:u"),
                                  {"u": uid}).scalar_one(),
             "kind": "본체", "fileName": "sample.nc", "byteSize": 1},
            {"fileId": grid_id, "kind": "기준 격자 파일", "fileName": "lat.nc",
             "byteSize": 1},
        ]}),
    })
    s3 = FakeS3()
    maintain(db, s3)
    assert s3.deleted == [body_key, grid_key]
    assert not exists(db, uid)


@pytest.mark.parametrize("damage", ["missing-event", "empty-event", "wrong-key", "open-transfer"])
def test_unknown_or_inconsistent_ownership_preserves_source(db, damage):
    uid, _, key = expired_upload(db)
    if damage == "missing-event":
        db.execute(text("DELETE FROM d5_pipeline_event WHERE upload_id=:u"), {"u": uid})
    elif damage == "empty-event":
        db.execute(text("UPDATE d5_pipeline_event SET payload='{" + '"files":[]' + "}'::jsonb "
                             "WHERE upload_id=:u"), {"u": uid})
    elif damage == "wrong-key":
        db.execute(text("UPDATE d5_upload_file SET storage_key='uploads/wrong/key' WHERE upload_id=:u"),
                   {"u": uid})
    else:
        db.execute(text("""INSERT INTO d5_upload_transfer
            (id,lab_id,uploader_account_id,source_label,created_at,expires_at)
            VALUES (:u,current_lab_id(),current_account_id(),'open',:born,:expires)"""),
                   {"u": uid, "born": NOW-dt.timedelta(hours=1),
                    "expires": NOW+dt.timedelta(hours=1)})
    s3 = FakeS3()
    report = maintain(db, s3)
    assert report.reclaimed_uploads == 0
    assert s3.deleted == []
    assert exists(db, uid)
    assert report.preserved


def test_any_inaccessible_dataset_makes_d3_ownership_unknown_even_when_empty(db):
    uid, _, _ = expired_upload(db)
    dataset_id = str(Ulid.generate())
    db.execute(text("""INSERT INTO d3_dataset
        (id,lab_id,owner_account_id,uploader_account_id)
        VALUES (:d,current_lab_id(),current_account_id(),current_account_id())"""), {"d": dataset_id})
    db.execute(text("""INSERT INTO d2_dataset_access(dataset_id,lab_id,state)
        VALUES (:d,current_lab_id(),'잠김')"""), {"d": dataset_id})
    s3 = FakeS3()
    report = maintain(db, s3)
    assert report.reclaimed_uploads == 0
    assert s3.deleted == []
    assert exists(db, uid)
    assert report.preserved.get("d3-ownership-unknown") == 1


@pytest.mark.parametrize("collision", ["file-id", "storage-key", "target-id"])
def test_any_d3_identity_collision_preserves_source(db, collision):
    uid, fid, key = expired_upload(db)
    make_all_d3_visible(db)
    dataset_id = uid if collision == "target-id" else str(Ulid.generate())
    db.execute(text("""INSERT INTO d3_dataset
        (id,lab_id,owner_account_id,uploader_account_id)
        VALUES (:d,current_lab_id(),current_account_id(),current_account_id())"""), {"d": dataset_id})
    if collision != "target-id":
        db.execute(text("""INSERT INTO d3_file
            (id,lab_id,dataset_id,kind,file_name,storage_key)
            VALUES (:f,current_lab_id(),:d,'본체','owned.nc',:k)"""), {
            "f": fid if collision == "file-id" else str(Ulid.generate()),
            "d": dataset_id,
            "k": key if collision == "storage-key" else f"uploads/{dataset_id}/other",
        })
    s3 = FakeS3()
    report = maintain(db, s3)
    assert report.reclaimed_uploads == 0
    assert s3.deleted == []
    assert exists(db, uid)
    assert report.preserved.get("d3-owned") == 1


def test_d3_visible_count_mismatch_preserves_source(db):
    uid, _, _ = expired_upload(db)
    dataset_id = str(Ulid.generate())
    db.execute(text("""INSERT INTO d3_dataset
        (id,lab_id,owner_account_id,uploader_account_id,file_count)
        VALUES (:d,current_lab_id(),current_account_id(),current_account_id(),1)"""), {"d": dataset_id})
    s3 = FakeS3()
    report = maintain(db, s3)
    assert report.reclaimed_uploads == 0
    assert exists(db, uid)
    assert report.preserved.get("d3-ownership-unknown") == 1


def test_partial_s3_failure_preserves_ledger_for_idempotent_retry(db):
    uid, _, key = expired_upload(db)
    make_all_d3_visible(db)
    failed = FakeS3(fail=True)
    first = maintain(db, failed)
    assert first.reclaimed_uploads == 0 and exists(db, uid)
    assert first.preserved.get("s3-delete-failed") == 1
    retry = FakeS3()
    second = maintain(db, retry)
    assert second.reclaimed_uploads == 1
    assert retry.deleted == [key]
    assert not exists(db, uid)


def test_db_rollback_after_s3_delete_retries_the_same_exact_key(db):
    uid, _, key = expired_upload(db)
    make_all_d3_visible(db)
    first_s3 = FakeS3()
    savepoint = db.begin_nested()
    first = maintain(db, first_s3)
    assert first.reclaimed_uploads == 1 and not exists(db, uid)
    savepoint.rollback()  # S3는 되돌아오지 않지만 D5 원장은 돌아온다.
    assert exists(db, uid)
    second_s3 = FakeS3()
    second = maintain(db, second_s3)
    assert second.reclaimed_uploads == 1
    assert first_s3.deleted == second_s3.deleted == [key]


def test_registered_and_processing_uploads_never_become_candidates(db):
    registered, _, registered_key = expired_upload(db, registered=True)
    processing, _, processing_key = expired_upload(db)
    db.execute(text("UPDATE d5_upload SET ready=false WHERE id=:u"), {"u": processing})
    db.execute(text("""INSERT INTO d5_pipeline_event
        (id,lab_id,actor_account_id,upload_id,event_type,schema_version,source,
         occurred_at,idempotency_key,payload)
        VALUES (:e,current_lab_id(),current_account_id(),:u,'file.header-parsed','1.0',
        'pipeline-worker',:at,:ik,'{}'::jsonb)"""), {
        "e": str(Ulid.generate()), "u": processing, "at": NOW-dt.timedelta(hours=1),
        "ik": f"file.header-parsed:{processing}",
    })
    make_all_d3_visible(db)
    s3 = FakeS3()
    maintain(db, s3)
    assert registered_key not in s3.deleted and processing_key not in s3.deleted
    assert exists(db, registered) and exists(db, processing)


def test_missing_scope_observes_no_candidate(session_factory):
    session = session_factory()
    try:
        session.begin()
        report = maintain_storage(session, s3=FakeS3(), mode="observe", now=NOW)
        assert report.candidates == 0
        assert report.reclaimed_uploads == 0
    finally:
        session.rollback()
        session.close()


def test_reclaim_lock_wins_registration_race_and_registration_fails_closed(session_factory):
    """S3 삭제 동안 잡은 D5 행 잠금이 등록 전환과 원장 삭제를 직렬화한다."""
    subject_b = Subject(
        account_id=Ulid("00000000000000000000000BP1"),
        lab_id=Ulid("0000000000000000000000000B"),
    )
    setup = session_factory()
    try:
        setup.begin()
        apply_scope(setup, subject_b)
        uid, _, key = expired_upload(setup)
        observed = maintain_storage(
            setup, s3=FakeS3(), mode="observe", now=NOW,
            lab_id=str(subject_b.lab_id))
        approval = parse_storage_reclaim_approval(
            json.dumps(observed.approval_plan), expected_lab_id=str(subject_b.lab_id),
            expected_sha256=observed.plan_sha256)
        setup.commit()
    finally:
        setup.close()

    class BlockingS3(FakeS3):
        def __init__(self):
            super().__init__()
            self.entered = threading.Event()
            self.release = threading.Event()

        def delete_objects(self, keys):
            self.deleted.extend(keys)
            self.entered.set()
            assert self.release.wait(5), "등록 경쟁 시험의 S3 release가 오지 않았다"

    s3 = BlockingS3()
    reclaim_result: dict = {}
    register_result: dict = {}

    def reclaim():
        try:
                reclaim_result["report"] = run_storage_maintenance(
                    session_factory, subject_b, s3=s3, mode="apply", now=NOW,
                    approval=approval)
        except BaseException as exc:  # 스레드 예외를 본 시험으로 가져온다.
            reclaim_result["error"] = exc

    def register():
        from colab_core.domains.d5_ingestion import UploadLedgerAdapter

        session = session_factory()
        try:
            session.begin()
            apply_scope(session, subject_b)
            register_result["marked"] = UploadLedgerAdapter(session).mark_registered(Ulid(uid))
            session.commit()
        except BaseException as exc:
            session.rollback()
            register_result["error"] = exc
        finally:
            session.close()

    reclaim_thread = threading.Thread(target=reclaim)
    reclaim_thread.start()
    assert s3.entered.wait(5), "회수기가 S3 삭제/행 잠금 지점에 도달하지 않았다"
    register_thread = threading.Thread(target=register)
    register_thread.start()
    register_thread.join(timeout=0.2)
    assert register_thread.is_alive(), "등록이 회수 행 잠금을 건너뛰었다"
    s3.release.set()
    reclaim_thread.join(timeout=5)
    register_thread.join(timeout=5)
    assert not reclaim_thread.is_alive() and not register_thread.is_alive()
    assert reclaim_result.get("error") is None and register_result.get("error") is None
    # 전체 서비스 묶음에서는 같은 lab의 앞선 시험 후보도 함께 잠기고 회수될 수 있다.
    assert reclaim_result["report"].reclaimed_uploads >= 1
    assert register_result["marked"] is False
    assert key in s3.deleted


def test_completed_transfer_metadata_is_pruned_only_after_seven_days_in_apply(db):
    old, edge, fresh = (str(Ulid.generate()) for _ in range(3))
    for transfer_id, completed in (
        (old, NOW-dt.timedelta(days=7, seconds=1)),
        (edge, NOW-dt.timedelta(days=7)),
        (fresh, NOW-dt.timedelta(days=6, seconds=86399)),
    ):
        db.execute(text("""INSERT INTO d5_upload_transfer
            (id,lab_id,uploader_account_id,source_label,created_at,expires_at,completed_at)
            VALUES (:u,current_lab_id(),current_account_id(),'done',:born,:expires,:done)"""), {
            "u": transfer_id, "born": completed-dt.timedelta(days=1),
            "expires": completed+dt.timedelta(days=3), "done": completed,
        })
        db.execute(text("""INSERT INTO d5_upload_transfer_file
            (id,lab_id,transfer_id,kind,file_name,byte_size,storage_key,outcome)
            VALUES (:f,current_lab_id(),:u,'본체','done.nc',1,:k,'올라감')"""), {
            "f": str(Ulid.generate()), "u": transfer_id, "k": f"uploads/{transfer_id}/file",
        })
    observe = maintain(db, FakeS3(), mode="observe")
    assert observe.eligible_completed_transfers == 2
    assert observe.pruned_completed_transfers == 0
    applied = maintain(db, FakeS3(), mode="apply")
    assert applied.pruned_completed_transfers == 2
    remaining = set(db.execute(text("SELECT id FROM d5_upload_transfer")).scalars())
    assert old not in remaining and edge not in remaining and fresh in remaining


def test_observe_never_reaps_an_expired_open_transfer(db):
    """Regression: observe used to abort multipart state and delete its ledger row."""
    transfer_id, file_id = str(Ulid.generate()), str(Ulid.generate())
    db.execute(text("""INSERT INTO d5_upload_transfer
        (id,lab_id,uploader_account_id,source_label,created_at,expires_at)
        VALUES (:u,current_lab_id(),current_account_id(),'paused',:born,:expires)"""), {
        "u": transfer_id, "born": NOW-dt.timedelta(days=4),
        "expires": NOW-dt.timedelta(days=1),
    })
    db.execute(text("""INSERT INTO d5_upload_transfer_file
        (id,lab_id,transfer_id,kind,file_name,byte_size,storage_key,outcome,
         part_size,transfer_ref)
        VALUES (:f,current_lab_id(),:u,'본체','paused.nc',99,:k,'대기',8,:ref)"""), {
        "f": file_id, "u": transfer_id,
        "k": f"uploads/{transfer_id}/{file_id}", "ref": "multipart-ref",
    })
    s3 = FakeS3()

    report = maintain_storage(
        db, s3=s3, mode="observe", now=NOW, include_open_transfers=True)

    assert report.reaped_open_transfers == 0
    assert report.expired_open_transfers == 1
    assert s3.aborted == [] and s3.deleted == []
    assert db.execute(text(
        "SELECT EXISTS(SELECT 1 FROM d5_upload_transfer WHERE id=:id)"),
        {"id": transfer_id}).scalar_one()


def test_apply_requires_the_exact_scoped_plan_before_any_delete(db):
    """Regression: setting mode=apply alone used to authorize every current candidate."""
    uid, _, _ = expired_upload(db)
    make_all_d3_visible(db)
    s3 = FakeS3()

    with pytest.raises(ValueError, match="승인 계획"):
        maintain_storage(db, s3=s3, mode="apply", now=NOW, lab_id=LAB_A)

    assert s3.deleted == [] and exists(db, uid)


def test_plan_is_stable_and_apply_rejects_wrong_scope_or_changed_targets(db):
    """The approved semantic list, not a timestamp or mode flag, binds deletion."""
    module = __import__("colab_core.app.storage_maintenance", fromlist=["x"])
    uid, _, key = expired_upload(db)
    make_all_d3_visible(db)
    first = maintain_storage(db, s3=FakeS3(), mode="observe", now=NOW, lab_id=LAB_A)
    second = maintain_storage(
        db, s3=FakeS3(), mode="observe", now=NOW+dt.timedelta(minutes=1), lab_id=LAB_A)
    assert first.plan_sha256 == second.plan_sha256
    assert first.approval_plan == {
        "schema": "colab-storage-reclaim-plan/1",
        "scope": {"labId": LAB_A},
        "uploads": [{"uploadId": uid, "keys": [key]}],
        "completedTransferIds": [],
    }

    wrong_scope = json.dumps({**first.approval_plan, "scope": {"labId": "0000000000000000000000000B"}})
    with pytest.raises(ValueError, match="연구실"):
        module.parse_storage_reclaim_approval(
            wrong_scope, expected_lab_id=LAB_A, expected_sha256=first.plan_sha256)
    duplicate = json.dumps(first.approval_plan)[:-1] + ',"uploads":[]}'
    with pytest.raises(ValueError, match="중복"):
        module.parse_storage_reclaim_approval(
            duplicate, expected_lab_id=LAB_A, expected_sha256=first.plan_sha256)

    with pytest.raises(ValueError, match="SHA-256"):
        module.parse_storage_reclaim_approval(
            json.dumps(first.approval_plan), expected_lab_id=LAB_A,
            expected_sha256="0" * 64)
    wrong_key = json.loads(json.dumps(first.approval_plan))
    wrong_key["uploads"][0]["keys"] = ["uploads/another-scope/file"]
    with pytest.raises(ValueError, match="upload scope"):
        module.parse_storage_reclaim_approval(
            json.dumps(wrong_key), expected_lab_id=LAB_A,
            expected_sha256=first.plan_sha256)

    approval = module.parse_storage_reclaim_approval(
        json.dumps(first.approval_plan), expected_lab_id=LAB_A,
        expected_sha256=first.plan_sha256)
    other_uid, _, _ = expired_upload(db)
    with pytest.raises(ValueError, match="현재 대상"):
        maintain_storage(
            db, s3=FakeS3(), mode="apply", now=NOW, lab_id=LAB_A,
            approval=approval)
    assert exists(db, uid) and exists(db, other_uid)
