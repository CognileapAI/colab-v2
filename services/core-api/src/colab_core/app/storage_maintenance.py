"""S3 원본 회수의 조립 경계 — D5 후보 + D2 가시성 + D3 소유권 + exact-key 삭제."""
from __future__ import annotations

import collections
import dataclasses
import datetime as dt

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from ..domains import d2_access, d3_catalog, d5_ingestion
from ..kernel import storage_layout
from ..kernel.auth import Subject
from ..kernel.ids import Ulid
from ..kernel.s3 import S3Error
from ..kernel.scope import apply_scope

RECLAIM_MODES = ("observe", "apply")
COMPLETED_TRANSFER_RETENTION_DAYS = 7


@dataclasses.dataclass
class StorageMaintenanceReport:
    mode: str
    candidates: int = 0
    reclaimed_uploads: int = 0
    eligible_completed_transfers: int = 0
    pruned_completed_transfers: int = 0
    reaped_open_transfers: int = 0
    preserved: dict[str, int] = dataclasses.field(default_factory=dict)

    def preserve(self, reason: str) -> None:
        self.preserved[reason] = self.preserved.get(reason, 0) + 1


def _accepted_keys(candidate: dict) -> tuple[list[str] | None, str | None]:
    """D5 사건과 실원장이 일치할 때만 exact-key 목록을 만든다."""
    upload_id = candidate["upload_id"]
    accepted = candidate.get("accepted")
    raw_files = accepted.get("files") if isinstance(accepted, dict) else None
    if not isinstance(raw_files, list) or not raw_files:
        return None, "accepted-event-invalid"
    if candidate.get("open_transfer"):
        return None, "open-transfer"

    refs: dict[str, tuple[str, str, str]] = {}
    keys: list[str] = []
    seen_keys: set[str] = set()
    for raw in raw_files:
        if not isinstance(raw, dict):
            return None, "accepted-event-invalid"
        file_id, kind, file_name = raw.get("fileId"), raw.get("kind"), raw.get("fileName")
        if (not isinstance(file_id, str) or not Ulid.is_valid(file_id)
                or kind not in (storage_layout.BODY_KIND, storage_layout.GRID_KIND)
                or not isinstance(file_name, str) or not file_name.strip()
                or file_id in refs):
            return None, "accepted-event-invalid"
        try:
            key = storage_layout.storage_key(
                upload_id, file_id=file_id, kind=kind, file_name=file_name)
        except (TypeError, ValueError):
            return None, "accepted-event-invalid"
        if key in seen_keys:
            return None, "accepted-event-invalid"
        refs[file_id] = (kind, file_name, key)
        keys.append(key)
        seen_keys.add(key)

    actual = {row["id"]: row for row in candidate.get("files", [])}
    if set(actual) - set(refs):
        return None, "d5-ledger-mismatch"
    for file_id, (kind, file_name, key) in refs.items():
        row = actual.get(file_id)
        # 축 미확정 격자는 아직 d5_upload_file에 없을 수 있다. 본체는 접수 때 반드시 선다.
        if row is None:
            if kind == storage_layout.GRID_KIND:
                continue
            return None, "d5-ledger-mismatch"
        if (row["kind"] != kind or row["file_name"] != file_name
                or row["storage_key"] != key):
            return None, "d5-ledger-mismatch"
    return keys, None


def _d3_ownership(session: Session) -> tuple[bool, set[str], set[str], set[str]]:
    """D2/D3 전건이 보일 때만 충돌 집합을 돌려준다."""
    snapshot = d3_catalog.reclaim_ownership_snapshot(session)
    dataset_ids = list(snapshot.dataset_file_counts)
    try:
        access = d2_access.DatasetAccessAdapter(session).dataset_access(
            [Ulid(dataset_id) for dataset_id in dataset_ids])
    except Exception:  # DB/Port 실패는 소유권 없음이 아니라 unknown이다.
        return False, set(), set(), set()
    if len(access) != len(dataset_ids) or any(
            not access.get(dataset_id) or not access[dataset_id].body_accessible
            for dataset_id in dataset_ids):
        return False, set(), set(), set()

    visible = collections.Counter(dataset_id for _file_id, dataset_id, _key in snapshot.files)
    if any(visible[dataset_id] != expected
           for dataset_id, expected in snapshot.dataset_file_counts.items()):
        return False, set(), set(), set()
    return (
        True,
        set(dataset_ids),
        {file_id for file_id, _dataset_id, _key in snapshot.files},
        {key for _file_id, _dataset_id, key in snapshot.files},
    )


def _reap_expired_open_transfers(session: Session, s3, report: StorageMaintenanceReport,
                                 *, now: dt.datetime | None) -> None:
    ledger = d5_ingestion.UploadTransferAdapter(session)
    for transfer_id in ledger.expired_open(now):
        files = ledger.files(Ulid(transfer_id))
        try:
            for file in files:
                if file.transfer_ref is not None and file.outcome != "올라감":
                    try:
                        s3.abort_multipart_upload(file.storage_key, file.transfer_ref)
                    except S3Error as exc:
                        if exc.code != "NoSuchUpload":
                            raise
            keys = [file.storage_key for file in files if file.outcome == "올라감"]
            if keys:
                s3.delete_objects(keys)
        except S3Error:
            report.preserve("open-transfer-s3-failed")
            continue
        ledger.delete(transfer_id)
        report.reaped_open_transfers += 1


def maintain_storage(session: Session, *, s3, mode: str = "observe",
                     now: dt.datetime | None = None, limit: int = 50,
                     include_open_transfers: bool = False) -> StorageMaintenanceReport:
    """열린 트랜잭션 안에서 저장소 유지보수를 수행한다.

    호출자는 REPEATABLE READ와 연구실 scope를 먼저 세워야 한다. 테스트는 동일한 실DB
    트랜잭션에서 이 함수의 외부 동작을 검증한다.
    """
    if mode not in RECLAIM_MODES:
        raise ValueError(f"모르는 저장 회수 모드다: {mode!r}")
    report = StorageMaintenanceReport(mode=mode)
    if include_open_transfers:
        _reap_expired_open_transfers(session, s3, report, now=now)

    ledger = d5_ingestion.UploadLedgerAdapter(session)
    transfers = d5_ingestion.UploadTransferAdapter(session)
    candidates = ledger.reclaim_candidates(now, limit=limit)
    report.candidates = len(candidates)

    try:
        complete, dataset_ids, d3_file_ids, d3_keys = _d3_ownership(session)
    except Exception:
        complete, dataset_ids, d3_file_ids, d3_keys = False, set(), set(), set()

    for candidate in candidates:
        keys, invalid = _accepted_keys(candidate)
        if invalid is not None:
            report.preserve(invalid)
            continue
        assert keys is not None
        if not complete:
            report.preserve("d3-ownership-unknown")
            continue
        accepted_ids = {
            item["fileId"] for item in candidate["accepted"]["files"]
            if isinstance(item, dict) and isinstance(item.get("fileId"), str)
        }
        if (candidate["upload_id"] in dataset_ids
                or accepted_ids & d3_file_ids or set(keys) & d3_keys):
            report.preserve("d3-owned")
            continue
        if mode == "observe":
            report.preserve("observe")
            continue
        try:
            s3.delete_objects(keys)
        except S3Error:
            report.preserve("s3-delete-failed")
            continue
        ledger.delete_reclaimed(candidate["upload_id"])
        report.reclaimed_uploads += 1

    completed = transfers.completed_for_prune(
        now, days=COMPLETED_TRANSFER_RETENTION_DAYS, limit=limit)
    report.eligible_completed_transfers = len(completed)
    if mode == "apply":
        for transfer_id in completed:
            transfers.delete(transfer_id)
        report.pruned_completed_transfers = len(completed)
    return report


def run_storage_maintenance(factory: sessionmaker[Session], subject: Subject, *, s3,
                            mode: str = "observe", now: dt.datetime | None = None
                            ) -> StorageMaintenanceReport:
    """요청과 독립된 REPEATABLE READ 트랜잭션에서 유지보수를 commit한다."""
    session = factory()
    try:
        session.begin()
        session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
        apply_scope(session, subject)
        report = maintain_storage(
            session, s3=s3, mode=mode, now=now, include_open_transfers=True)
        session.commit()
        return report
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
