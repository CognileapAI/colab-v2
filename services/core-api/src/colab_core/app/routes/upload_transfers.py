"""프리사인드 전송 8 op — 브라우저→S3 직행 (동결 해제 8차 · `PLAN-SoT §9 〈174〉`).

컨트롤 플레인(계획·URL 발급·실측 검증·완결·중단)은 서버가, 데이터 플레인(바이트 PUT)은
브라우저가 프리사인드 URL 로 한다. **파트의 정본은 S3 ListParts 다** — 클라이언트의
자기 보고를 믿지 않는다. 완결(complete)되는 순간 같은 ULID 로 기존 원장(`d5_upload`)이
서고 `upload.accepted` 가 발행된다 — 그 뒤는 `routes/ingestion.py` 의 세계다.

**저장 모드 local 에서는 전부 501 이다** — 로컬 개발의 정문은 여전히 `createUpload`
(multipart/form-data)이고, FE 는 501 을 받으면 그쪽으로 폴백한다.

원장 접근은 `domains/d5_ingestion.UploadTransferAdapter` 하나를 지난다 (`〈63〉-㉱`).
"""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Body, Depends, Path, Request, Response
from sqlalchemy.orm import Session

from ...domains import d5_ingestion
from ...kernel import errors, storage_layout
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ...kernel.objectpath import normalize_relative_path
from ...kernel.s3 import Part, S3Client, S3Error
from ...ports.ingestion import TransferFileRecord, UploadFileRecord
from ..deps import current_subject, scoped_db
from .ingestion import _require_upload_edit, _ttl

router = APIRouter()

#: 이어올리기 창. 파이프라인 TTL(`upload_ttl_hours`)과 별개다 — 저것은 접수 **후**의
#: 수명이고 이것은 접수 **전**(전송 중) 상태의 수명이다. 금요일 밤에 끊겨도 월요일에 잇는다.
TRANSFER_TTL_HOURS = 72
URL_TTL_SECONDS = 900
MAX_FILES = 500
MAX_GRID_FILES = 2          # 〈58〉 — 기준 격자 파일 0~2건
MAX_PART_URL_BATCH = 16
MAX_URL_BATCH = 50

SINGLE_PUT_MAX = 16 * 1024 * 1024   # 이 미만은 단일 PUT — 재전송이 싸다
MIN_PART = 8 * 1024 * 1024
MAX_PARTS = 10_000                  # S3 하드 리밋


def choose_part_size(size: int) -> int:
    """8 MiB 에서 시작해 파트 수가 상한을 넘지 않을 때까지 배로 키운다."""
    part = MIN_PART
    while (size + part - 1) // part > MAX_PARTS:
        part *= 2
    return part


def part_count(size: int, part_size: int) -> int:
    return max(1, (size + part_size - 1) // part_size)


def _s3(request: Request) -> S3Client:
    """저장 모드가 s3 일 때만 선다 — local 이면 501 (FE 폴백 신호)."""
    settings = request.app.state.settings
    if getattr(settings, "storage_mode", "local") != "s3":
        raise errors.ApiError(
            501, "NOT_IMPLEMENTED",
            "프리사인드 전송은 저장 모드 s3 에서만 선다 — 로컬 개발은 createUpload 로 간다.")
    cached = getattr(request.app.state, "upload_transfer_s3", None)
    if cached is not None:
        return cached
    client = S3Client(bucket=settings.s3_bucket, region=settings.s3_region)
    request.app.state.upload_transfer_s3 = client
    return client


def _ledger(db: Session) -> d5_ingestion.UploadTransferAdapter:
    return d5_ingestion.UploadTransferAdapter(db)


def _accept_ledger(db: Session) -> d5_ingestion.UploadLedgerAdapter:
    return d5_ingestion.UploadLedgerAdapter(db)


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _iso(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _open_transfer(ledger: d5_ingestion.UploadTransferAdapter, transfer_id: str,
                   *, now: dt.datetime | None = None):
    if not Ulid.is_valid(transfer_id):
        raise errors.not_found("없는 전송이거나 이어올리기 창(72시간)이 지났다.")
    record = ledger.find(Ulid(transfer_id))
    if record is None or record.expires_at <= (now or _now()):
        raise errors.not_found("없는 전송이거나 이어올리기 창(72시간)이 지났다.")
    if record.completed_at is not None:
        raise errors.conflict("이미 완결된 전송이다 — 접수가 끝났다.")
    return record


def _reap_expired(s3: S3Client, ledger: d5_ingestion.UploadTransferAdapter) -> None:
    """만료된 미완결 전송의 지연 정리 — **원장이 아는 것만** 지운다 (버킷 루트 스캔 금지).

    S3 정리가 실패하면 행을 지우지 않는다 — 다음 기회에 다시 시도한다. 최후 백스톱은
    버킷 라이프사이클(abort-incomplete-multipart-7d)이다.
    """
    for transfer_id in ledger.expired_open():
        files = ledger.files(transfer_id)
        try:
            for f in files:
                if f.transfer_ref is not None and f.outcome != "올라감":
                    try:
                        s3.abort_multipart_upload(f.storage_key, f.transfer_ref)
                    except S3Error as e:
                        if e.code != "NoSuchUpload":  # 이미 소멸한 것은 성공과 같다
                            raise
            uploaded = [f.storage_key for f in files if f.outcome == "올라감"]
            if uploaded:
                s3.delete_objects(uploaded)
        except S3Error:
            continue
        ledger.delete(transfer_id)


def _file_of(ledger: d5_ingestion.UploadTransferAdapter, transfer_id: str,
             file_id: str) -> TransferFileRecord:
    files = ledger.files(transfer_id, [file_id])
    if not files:
        raise errors.not_found("이 전송에 없는 파일이다.")
    return files[0]


# ═════════════════════════ initiateUploadTransfer ═══════════════════════════
@router.post("/uploads/transfers", name="initiateUploadTransfer", status_code=201)
def initiate_upload_transfer(request: Request, body: dict = Body(...),
                             subject: Subject = Depends(current_subject),
                             db: Session = Depends(scoped_db)) -> dict:
    s3 = _s3(request)
    _require_upload_edit(db, subject)
    ledger = _ledger(db)
    _reap_expired(s3, ledger)  # 지연 정리 — 별도 크론 없이 여기서 치운다

    unknown = set(body) - {"sourceLabel", "files"}
    if unknown:
        raise errors.bad_request(f"계약에 없는 필드다: {sorted(unknown)}")
    raw_files = body.get("files")
    if not isinstance(raw_files, list) or not (1 <= len(raw_files) <= MAX_FILES):
        raise errors.bad_request(f"files 는 1~{MAX_FILES}개다.")
    source_label = body.get("sourceLabel") or ""
    if not isinstance(source_label, str) or len(source_label) > 255:
        raise errors.bad_request("sourceLabel 은 255자 이내 문자열이다.")

    transfer_id = Ulid.generate()
    planned: list[TransferFileRecord] = []
    rejected: list[dict] = []
    seen: set[str] = set()
    grid_count = 0
    for item in raw_files:
        if not isinstance(item, dict):
            raise errors.bad_request("files 항목 형태가 계약과 다르다.")
        name_raw = item.get("fileName")
        size = item.get("byteSize")
        if not isinstance(name_raw, str) or not isinstance(size, int) or size < 0:
            raise errors.bad_request("fileName(문자열)·byteSize(0 이상 정수)는 필수다.")
        kind = item.get("kind", "본체")
        if kind not in ("본체", "기준 격자 파일"):
            raise errors.bad_request("kind 는 ['본체', '기준 격자 파일'] 중 하나다.")
        rel_raw = item.get("relativePath")
        if rel_raw is not None and not isinstance(rel_raw, str):
            raise errors.bad_request("relativePath 는 문자열이다.")
        try:
            name = normalize_relative_path(name_raw)
            relative_path = None if rel_raw is None else normalize_relative_path(rel_raw)
        except ValueError:
            rejected.append({"fileName": name_raw, "reason": "이름을 정규화할 수 없다"})
            continue
        if "/" in name or len(name) > 255:
            rejected.append({"fileName": name_raw,
                             "reason": "fileName 은 경로 없는 1~255자다 — 경로는 relativePath 로"})
            continue
        if relative_path is not None and len(relative_path) > 1024:
            rejected.append({"fileName": name_raw, "reason": "relativePath 가 1024자를 넘는다"})
            continue
        identity = relative_path or name
        if identity in seen:
            rejected.append({"fileName": name_raw, "reason": "같은 파일이 요청에 두 번 있다"})
            continue
        if kind == "기준 격자 파일":
            grid_count += 1
            if grid_count > MAX_GRID_FILES:
                rejected.append({"fileName": name_raw,
                                 "reason": f"기준 격자 파일은 최대 {MAX_GRID_FILES}건이다 (〈58〉)"})
                continue
        file_id = str(Ulid.generate())
        try:
            # 저장 키는 세 배포 단위가 공유하는 규약 그대로 — 폴더 구조는 키가 아니라
            # relative_path 메타에 산다 (〈173〉 — layout.json 은 손대지 않는다).
            key = storage_layout.storage_key(str(transfer_id), file_id=file_id,
                                             kind=kind, file_name=name)
        except storage_layout.UnsafeFileName:
            rejected.append({"fileName": name_raw, "reason": "저장 키로 쓸 수 없는 이름이다"})
            continue
        seen.add(identity)
        part_size = None if size < SINGLE_PUT_MAX else choose_part_size(size)
        planned.append(TransferFileRecord(
            file_id=file_id, file_name=name, kind=kind, byte_size=size,
            storage_key=key, relative_path=relative_path,
            part_size=part_size, transfer_ref=None, outcome="대기"))
    if not planned:
        raise errors.bad_request("접수할 수 있는 파일이 없다.", {"rejected": rejected})

    expires_at = _now() + dt.timedelta(hours=TRANSFER_TTL_HOURS)
    ledger.open(transfer_id=transfer_id, uploader_account_id=subject.account_id,
                source_label=source_label or "(이름 없음)", expires_at=expires_at,
                files=planned)
    return {
        "uploadId": str(transfer_id),
        "expiresAt": _iso(expires_at),
        "files": [{
            "fileId": f.file_id, "fileName": f.file_name, "kind": f.kind,
            "byteSize": f.byte_size,
            **({"relativePath": f.relative_path} if f.relative_path else {}),
            "strategy": "단일" if f.part_size is None else "멀티파트",
            "partSize": f.part_size,
            "partCount": None if f.part_size is None else part_count(f.byte_size, f.part_size),
        } for f in planned],
        "rejected": rejected,
    }


# ═══════════════════════ listIncompleteUploadTransfers ══════════════════════
@router.get("/uploads/transfers/incomplete", name="listIncompleteUploadTransfers")
def list_incomplete_upload_transfers(request: Request,
                                     subject: Subject = Depends(current_subject),
                                     db: Session = Depends(scoped_db)) -> dict:
    s3 = _s3(request)
    ledger = _ledger(db)
    _reap_expired(s3, ledger)
    rows = ledger.incomplete_for(subject.account_id)
    return {"items": [{
        "uploadId": r["record"].transfer_id,
        "sourceLabel": r["record"].source_label,
        "uploadedFiles": r["uploaded_files"], "plannedFiles": r["planned_files"],
        "uploadedBytes": r["uploaded_bytes"], "plannedBytes": r["planned_bytes"],
        "createdAt": _iso(r["record"].created_at),
        "expiresAt": _iso(r["record"].expires_at),
    } for r in rows]}


# ═════════════════════════ getUploadTransfer (재개) ═════════════════════════
@router.get("/uploads/transfers/{uploadId}", name="getUploadTransfer")
def get_upload_transfer(request: Request, upload_id: str = Path(alias="uploadId"),
                        subject: Subject = Depends(current_subject),
                        db: Session = Depends(scoped_db)) -> dict:
    s3 = _s3(request)
    ledger = _ledger(db)
    record = _open_transfer(ledger, upload_id)
    files = []
    for f in ledger.files(upload_id):
        uploaded_parts = None
        if f.part_size is not None and f.outcome == "대기" and f.transfer_ref is not None:
            try:  # 파트의 정본은 S3 — DB 를 믿으면 이미 올린 파트를 다시 올린다
                uploaded_parts = [p.number for p in s3.list_parts(f.storage_key, f.transfer_ref)]
            except S3Error:
                uploaded_parts = None  # 재개 정보는 편의다 — 조회 자체를 죽이지 않는다
        files.append({
            "fileId": f.file_id, "fileName": f.file_name, "kind": f.kind,
            "byteSize": f.byte_size,
            **({"relativePath": f.relative_path} if f.relative_path else {}),
            "strategy": "단일" if f.part_size is None else "멀티파트",
            "partSize": f.part_size,
            "partCount": None if f.part_size is None else part_count(f.byte_size, f.part_size),
            "outcome": f.outcome,
            "uploadedParts": uploaded_parts,
        })
    return {"uploadId": upload_id, "expiresAt": _iso(record.expires_at), "files": files}


# ═══════════════════════════════ URL 발급 ═══════════════════════════════════
@router.post("/uploads/transfers/{uploadId}/put-urls", name="issueUploadUrls")
def issue_upload_urls(request: Request, upload_id: str = Path(alias="uploadId"),
                      body: dict = Body(...),
                      subject: Subject = Depends(current_subject),
                      db: Session = Depends(scoped_db)) -> dict:
    s3 = _s3(request)
    ledger = _ledger(db)
    _open_transfer(ledger, upload_id)
    file_ids = body.get("fileIds")
    if (not isinstance(file_ids, list) or not (1 <= len(file_ids) <= MAX_URL_BATCH)
            or not all(isinstance(v, str) for v in file_ids)):
        raise errors.bad_request(f"fileIds 는 1~{MAX_URL_BATCH}개다.")
    files = {f.file_id: f for f in ledger.files(upload_id, file_ids)}
    missing = [v for v in file_ids if v not in files]
    if missing:
        raise errors.bad_request("이 전송에 없는 파일이다.", {"fileIds": missing})
    wrong = [f.file_id for f in files.values() if f.part_size is not None]
    if wrong:
        raise errors.bad_request("전략이 `단일` 이 아닌 파일이 섞였다 — multipart 로 갈 것.",
                                 {"fileIds": wrong})
    now = _now()
    ttl = s3.url_ttl(URL_TTL_SECONDS, now)
    expires = _iso(now + dt.timedelta(seconds=ttl))
    return {"urls": [{
        "fileId": f.file_id,
        "url": s3.presign_put(f.storage_key, expires=ttl, now=now),
        "expiresAt": expires,
    } for f in (files[v] for v in file_ids)]}


@router.post("/uploads/transfers/{uploadId}/files/{fileId}/multipart",
             name="initUploadFileMultipart")
def init_upload_file_multipart(request: Request,
                               upload_id: str = Path(alias="uploadId"),
                               file_id: str = Path(alias="fileId"),
                               subject: Subject = Depends(current_subject),
                               db: Session = Depends(scoped_db)) -> dict:
    s3 = _s3(request)
    ledger = _ledger(db)
    _open_transfer(ledger, upload_id)
    f = _file_of(ledger, upload_id, file_id)
    if f.part_size is None:
        raise errors.bad_request("전략이 `멀티파트` 가 아니다 — put-urls 로 갈 것.")
    if f.transfer_ref is None:  # 멱등 — 이미 시작됐으면 같은 계획을 다시 돌려준다
        ref = s3.create_multipart_upload(f.storage_key)
        ledger.set_ref(file_id, ref)
    return {"partSize": f.part_size, "partCount": part_count(f.byte_size, f.part_size)}


@router.post("/uploads/transfers/{uploadId}/files/{fileId}/part-urls",
             name="issueUploadPartUrls")
def issue_upload_part_urls(request: Request,
                           upload_id: str = Path(alias="uploadId"),
                           file_id: str = Path(alias="fileId"),
                           body: dict = Body(...),
                           subject: Subject = Depends(current_subject),
                           db: Session = Depends(scoped_db)) -> dict:
    s3 = _s3(request)
    ledger = _ledger(db)
    _open_transfer(ledger, upload_id)
    f = _file_of(ledger, upload_id, file_id)
    if f.transfer_ref is None:
        raise errors.ApiError(409, "MULTIPART_NOT_STARTED",
                              "멀티파트가 시작되지 않았다 — multipart 먼저.")
    numbers = body.get("partNumbers")
    if (not isinstance(numbers, list) or not (1 <= len(numbers) <= MAX_PART_URL_BATCH)
            or not all(isinstance(n, int) and 1 <= n <= MAX_PARTS for n in numbers)):
        raise errors.bad_request(f"partNumbers 는 1~{MAX_PART_URL_BATCH}개의 1~{MAX_PARTS} 정수다.")
    now = _now()
    ttl = s3.url_ttl(URL_TTL_SECONDS, now)
    return {
        "urls": [{
            "partNumber": n,
            "url": s3.presign_put(f.storage_key,
                                  query={"partNumber": str(n), "uploadId": f.transfer_ref},
                                  expires=ttl, now=now),
        } for n in numbers],
        "expiresAt": _iso(now + dt.timedelta(seconds=ttl)),
    }


# ═══════════════════════════════ 실측 검증 ══════════════════════════════════
@router.post("/uploads/transfers/{uploadId}/files/{fileId}/complete",
             name="completeUploadFile")
def complete_upload_file(request: Request,
                         upload_id: str = Path(alias="uploadId"),
                         file_id: str = Path(alias="fileId"),
                         subject: Subject = Depends(current_subject),
                         db: Session = Depends(scoped_db)) -> dict:
    s3 = _s3(request)
    ledger = _ledger(db)
    _open_transfer(ledger, upload_id)
    f = _file_of(ledger, upload_id, file_id)
    if f.outcome == "올라감":  # 멱등 — 완료 보고가 두 번 와도 사실은 하나다
        return {"fileId": file_id, "outcome": "올라감", "detail": None}

    def fail(detail: str) -> dict:
        ledger.set_outcome(file_id, "실패")
        return {"fileId": file_id, "outcome": "실패", "detail": detail}

    try:
        if f.part_size is not None:
            if f.transfer_ref is None:
                return fail("멀티파트가 시작되지 않았다.")
            parts: list[Part] = s3.list_parts(f.storage_key, f.transfer_ref)
            if not parts:
                return fail("올라간 파트가 없다.")
            s3.complete_multipart_upload(f.storage_key, f.transfer_ref, parts)
        size, _etag = s3.head_object(f.storage_key)
    except S3Error as e:
        return fail(f"저장소 확인 실패 — {e}")
    if size != f.byte_size:
        return fail(f"크기 불일치 — 신고 {f.byte_size}B, 실제 {size}B. 다시 올릴 것.")
    ledger.set_outcome(file_id, "올라감")
    return {"fileId": file_id, "outcome": "올라감", "detail": None}


# ═══════════════════════════ 완결 = 접수 승계 ═══════════════════════════════
@router.post("/uploads/transfers/{uploadId}/complete", name="completeUploadTransfer",
             status_code=201)
def complete_upload_transfer(request: Request,
                             upload_id: str = Path(alias="uploadId"),
                             subject: Subject = Depends(current_subject),
                             db: Session = Depends(scoped_db)) -> dict:
    """모든 파일이 실측으로 확인된 뒤에만 — 이때 `d5_upload` 가 서고 `upload.accepted`
    가 발행된다. 응답은 `createUpload` 의 `UploadReceipt` 와 같은 모양이다: FE 는 이
    지점부터 두 경로의 구분 없이 같은 상태 조회(`getUploadStatus`)로 간다."""
    _s3(request)
    ledger = _ledger(db)
    _open_transfer(ledger, upload_id)
    files = ledger.files(upload_id)
    pending = [f.file_id for f in files if f.outcome != "올라감"]
    if pending:
        raise errors.ApiError(409, "TRANSFER_INCOMPLETE",
                              "실측으로 확인되지 않은 파일이 남아 있다.", {"fileIds": pending})
    if not ledger.complete(Ulid(upload_id)):
        raise errors.conflict("이미 완결된 전송이다.")

    accept = _accept_ledger(db)
    records = [UploadFileRecord(
        file_id=f.file_id, file_name=f.file_name, kind=f.kind, byte_size=f.byte_size,
        storage_key=f.storage_key, carries_lat=False, carries_lon=False,
        detected_format=None, relative_path=f.relative_path,
    ) for f in files]
    expires_at = _now() + _ttl(request)
    accept.accept(upload_id=Ulid(upload_id), uploader_account_id=subject.account_id,
                  expires_at=expires_at, files=records)
    accept.publish_accepted(upload_id=Ulid(upload_id),
                            actor_account_id=subject.account_id, files=records)
    return {"uploadId": upload_id,
            "files": [{"fileId": f.file_id, "fileName": f.file_name, "kind": f.kind,
                       "byteSize": f.byte_size} for f in files]}


# ═══════════════════════════════ 중단 ═══════════════════════════════════════
@router.delete("/uploads/transfers/{uploadId}", name="abortUploadTransfer",
               status_code=204)
def abort_upload_transfer(request: Request,
                          upload_id: str = Path(alias="uploadId"),
                          subject: Subject = Depends(current_subject),
                          db: Session = Depends(scoped_db)) -> Response:
    s3 = _s3(request)
    ledger = _ledger(db)
    record = ledger.find(Ulid(upload_id)) if Ulid.is_valid(upload_id) else None
    if record is None:
        raise errors.not_found("없는 전송이거나 이미 정리됐다.")
    if record.completed_at is not None:
        raise errors.conflict("이미 완결된 전송은 중단할 수 없다 — 접수가 끝났다.")
    files = ledger.files(upload_id)
    for f in files:
        if f.transfer_ref is not None and f.outcome != "올라감":
            try:
                s3.abort_multipart_upload(f.storage_key, f.transfer_ref)
            except S3Error as e:
                if e.code != "NoSuchUpload":
                    raise
    uploaded = [f.storage_key for f in files if f.outcome == "올라감"]
    if uploaded:
        s3.delete_objects(uploaded)
    ledger.delete(upload_id)
    return Response(status_code=204)
