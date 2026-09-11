"""S3 원본 회수의 조립 경계 — D5 후보 + D2 가시성 + D3 소유권 + exact-key 삭제."""
from __future__ import annotations

import collections
import dataclasses
import datetime as dt
import hashlib
import json
from typing import Any

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
RECLAIM_PLAN_SCHEMA = "colab-storage-reclaim-plan/1"


@dataclasses.dataclass(frozen=True)
class StorageReclaimApproval:
    plan: dict[str, Any]
    sha256: str


def _canonical_plan(plan: dict[str, Any]) -> bytes:
    return json.dumps(
        plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def _plan_sha256(plan: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_plan(plan)).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"승인 계획 JSON에 중복 필드가 있다: {key}")
        result[key] = value
    return result


def parse_storage_reclaim_approval(
        raw: str, *, expected_lab_id: str,
        expected_sha256: str) -> StorageReclaimApproval:
    """엄격한 exact-target 승인 계획을 읽는다. 이 함수 호출 자체는 승인이 아니다."""
    try:
        plan = json.loads(raw, object_pairs_hook=_unique_object)
    except json.JSONDecodeError as exc:
        raise ValueError("승인 계획 JSON이 올바르지 않다") from exc
    if not isinstance(plan, dict) or set(plan) != {
            "schema", "scope", "uploads", "completedTransferIds"}:
        raise ValueError("승인 계획 최상위 필드가 정확하지 않다")
    if plan["schema"] != RECLAIM_PLAN_SCHEMA:
        raise ValueError("승인 계획 schema가 맞지 않다")
    scope = plan["scope"]
    if not isinstance(scope, dict) or set(scope) != {"labId"}:
        raise ValueError("승인 계획 연구실 scope가 정확하지 않다")
    if scope["labId"] != expected_lab_id:
        raise ValueError("승인 계획 연구실이 현재 주체와 다르다")
    if not Ulid.is_valid(expected_lab_id):
        raise ValueError("승인 계획 연구실 ID가 올바르지 않다")

    uploads = plan["uploads"]
    if not isinstance(uploads, list):
        raise ValueError("승인 계획 uploads는 목록이어야 한다")
    seen_uploads: set[str] = set()
    seen_keys: set[str] = set()
    previous_upload = ""
    normalized_uploads: list[dict[str, Any]] = []
    for target in uploads:
        if not isinstance(target, dict) or set(target) != {"uploadId", "keys"}:
            raise ValueError("승인 계획 upload 대상 필드가 정확하지 않다")
        upload_id, keys = target["uploadId"], target["keys"]
        if (not isinstance(upload_id, str) or not Ulid.is_valid(upload_id)
                or upload_id in seen_uploads or upload_id <= previous_upload):
            raise ValueError("승인 계획 uploadId가 중복·비정렬·비정규다")
        if (not isinstance(keys, list) or not keys
                or any(not isinstance(key, str) or not key for key in keys)
                or keys != sorted(keys) or len(keys) != len(set(keys))
                or seen_keys.intersection(keys)):
            raise ValueError("승인 계획 key가 비었거나 중복·비정렬이다")
        if any(not key.startswith(f"uploads/{upload_id}/") for key in keys):
            raise ValueError("승인 계획 key가 upload scope 밖을 가리킨다")
        seen_uploads.add(upload_id)
        seen_keys.update(keys)
        previous_upload = upload_id
        normalized_uploads.append({"uploadId": upload_id, "keys": keys})

    completed = plan["completedTransferIds"]
    if (not isinstance(completed, list)
            or any(not isinstance(item, str) or not Ulid.is_valid(item) for item in completed)
            or completed != sorted(completed) or len(completed) != len(set(completed))):
        raise ValueError("승인 계획 completedTransferIds가 중복·비정렬·비정규다")
    normalized = {
        "schema": RECLAIM_PLAN_SCHEMA,
        "scope": {"labId": expected_lab_id},
        "uploads": normalized_uploads,
        "completedTransferIds": completed,
    }
    actual_sha256 = _plan_sha256(normalized)
    if (len(expected_sha256) != 64
            or any(char not in "0123456789abcdef" for char in expected_sha256)
            or expected_sha256 != actual_sha256):
        raise ValueError("승인 계획 SHA-256이 정확한 대상 목록과 다르다")
    return StorageReclaimApproval(plan=normalized, sha256=actual_sha256)


@dataclasses.dataclass
class StorageMaintenanceReport:
    mode: str
    candidates: int = 0
    reclaimed_uploads: int = 0
    eligible_completed_transfers: int = 0
    pruned_completed_transfers: int = 0
    reaped_open_transfers: int = 0
    expired_open_transfers: int = 0
    preserved: dict[str, int] = dataclasses.field(default_factory=dict)
    approval_plan: dict[str, Any] | None = None
    plan_sha256: str | None = None

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


def maintain_storage(session: Session, *, s3, mode: str = "observe",
                     now: dt.datetime | None = None, limit: int = 50,
                     include_open_transfers: bool = False,
                     lab_id: str | None = None,
                     approval: StorageReclaimApproval | None = None,
                     ) -> StorageMaintenanceReport:
    """열린 트랜잭션 안에서 저장소 유지보수를 수행한다.

    호출자는 REPEATABLE READ와 연구실 scope를 먼저 세워야 한다. 테스트는 동일한 실DB
    트랜잭션에서 이 함수의 외부 동작을 검증한다.
    """
    if mode not in RECLAIM_MODES:
        raise ValueError(f"모르는 저장 회수 모드다: {mode!r}")
    report = StorageMaintenanceReport(mode=mode)
    if mode == "apply" and (approval is None or lab_id is None):
        raise ValueError("apply에는 현재 연구실의 exact-target 승인 계획이 필요하다")
    if approval is not None and (lab_id is None or approval.plan["scope"]["labId"] != lab_id):
        raise ValueError("승인 계획 연구실이 현재 scope와 다르다")

    ledger = d5_ingestion.UploadLedgerAdapter(session)
    transfers = d5_ingestion.UploadTransferAdapter(session)
    if include_open_transfers:
        report.expired_open_transfers = len(transfers.expired_open(now))
        if report.expired_open_transfers:
            report.preserved["open-transfer"] = report.expired_open_transfers
    candidates = ledger.reclaim_candidates(now, limit=limit)
    report.candidates = len(candidates)

    try:
        complete, dataset_ids, d3_file_ids, d3_keys = _d3_ownership(session)
    except Exception:
        complete, dataset_ids, d3_file_ids, d3_keys = False, set(), set(), set()

    eligible: list[tuple[dict, list[str]]] = []
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
        eligible.append((candidate, sorted(keys)))
        if mode == "observe":
            report.preserve("observe")

    completed = transfers.completed_for_prune(
        now, days=COMPLETED_TRANSFER_RETENTION_DAYS, limit=limit)
    report.eligible_completed_transfers = len(completed)
    if lab_id is not None:
        plan = {
            "schema": RECLAIM_PLAN_SCHEMA,
            "scope": {"labId": lab_id},
            "uploads": [
                {"uploadId": candidate["upload_id"], "keys": keys}
                for candidate, keys in sorted(eligible, key=lambda item: item[0]["upload_id"])
            ],
            "completedTransferIds": sorted(completed),
        }
        report.approval_plan = plan
        report.plan_sha256 = _plan_sha256(plan)

    if mode == "apply":
        assert approval is not None
        if approval.sha256 != report.plan_sha256 or approval.plan != report.approval_plan:
            raise ValueError("승인 계획과 현재 대상이 다르다 — 새 관측과 승인이 필요하다")
        for candidate, keys in eligible:
            try:
                s3.delete_objects(keys)
            except S3Error:
                report.preserve("s3-delete-failed")
                continue
            ledger.delete_reclaimed(candidate["upload_id"])
            report.reclaimed_uploads += 1
        for transfer_id in completed:
            transfers.delete(transfer_id)
        report.pruned_completed_transfers = len(completed)
    return report


def run_storage_maintenance(factory: sessionmaker[Session], subject: Subject, *, s3,
                            mode: str = "observe", now: dt.datetime | None = None,
                            approval: StorageReclaimApproval | None = None,
                            ) -> StorageMaintenanceReport:
    """요청과 독립된 REPEATABLE READ 트랜잭션에서 유지보수를 commit한다."""
    session = factory()
    try:
        session.begin()
        session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
        apply_scope(session, subject)
        report = maintain_storage(
            session, s3=s3, mode=mode, now=now, include_open_transfers=True,
            lab_id=str(subject.lab_id), approval=approval)
        session.commit()
        return report
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
