"""사용자 대표 그림의 D3 메타데이터와 바이트 표면."""
from __future__ import annotations

import io
import warnings

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from ...domains import d3_catalog
from ...kernel import errors, storage_layout
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ...kernel.scope import apply_scope
from ..deps import current_subject, scoped_db
from .catalog import require_body_access
from .ingestion import _require_upload_edit, _storage

router = APIRouter()
MAX_IMAGE_BYTES = 10 * 1024 * 1024
_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}
_PIL_TYPES = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}
# 압축된 10 MiB 그림도 해제 후 수십 GB가 될 수 있다. 대표 화면에 충분한 상한을 별도로 둔다.
MAX_IMAGE_PIXELS = 50_000_000


def _detected_content_type(payload: bytes) -> str | None:
    """Pillow가 구조 검증과 실제 픽셀 해제를 모두 끝낸 세 형식만 받는다."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(payload)) as opened:
                content_type = _PIL_TYPES.get(opened.format or "")
                width, height = opened.size
                if content_type is None or width <= 0 or height <= 0 \
                        or width * height > MAX_IMAGE_PIXELS:
                    return None
                opened.verify()
            # verify()는 디코더 구조를 훑고 이미지를 닫는다. 다시 열어 실제 픽셀까지 읽어
            # SOS 뒤 entropy가 없거나 WebP frame payload가 깨진 파일도 저장 전에 거절한다.
            with Image.open(io.BytesIO(payload)) as decoded:
                decoded.load()
            return content_type
    except (Image.DecompressionBombError, Image.DecompressionBombWarning,
            UnidentifiedImageError, OSError, SyntaxError, ValueError):
        return None


def _metadata(row: d3_catalog.RepresentativeImage | None) -> dict:
    return {"custom": row is not None,
            "fileName": None if row is None else row.file_name,
            "contentType": None if row is None else row.content_type,
            "sizeBytes": None if row is None else row.size_bytes}


def _dataset_id(raw: str) -> Ulid:
    if not Ulid.is_valid(raw):
        raise errors.bad_request("datasetId 가 정규 ID 가 아니다.")
    return Ulid(raw)


def _remember_failed_cleanup(
        db: Session, subject: Subject, dataset_id: Ulid, storage_key: str) -> None:
    """이미 500으로 끝날 작업에서도 orphan 키는 별도 transaction에 남긴다."""
    try:
        if not db.in_transaction():
            apply_scope(db, subject)
        d3_catalog.queue_representative_image_cleanup(db, dataset_id, storage_key)
        db.commit()
    except Exception:
        # 원래 저장/DB 오류를 cleanup 기록 오류로 가리지 않는다. 둘 다 실패하면 응답은 원래 500이고,
        # 이 함수는 가능한 마지막 추적 시도다.
        db.rollback()


def _discard_new_or_remember(
        storage, db: Session, subject: Subject, dataset_id: Ulid, storage_key: str) -> None:
    try:
        storage.discard(key=storage_key)
    except Exception:
        _remember_failed_cleanup(db, subject, dataset_id, storage_key)


def _drain_cleanups(storage, db: Session, subject: Subject, dataset_id: Ulid,
                    *, keep: str | None = None) -> None:
    """확정된 응답을 바꾸지 않는 best-effort drain. 실패한 키 행은 그대로 다음 mutation에 남긴다."""
    try:
        if not db.in_transaction():
            apply_scope(db, subject)
        for pending in d3_catalog.representative_image_cleanups(db, dataset_id):
            try:
                storage.discard(key=pending.storage_key, keep=keep)
            except Exception:
                continue
            d3_catalog.finish_representative_image_cleanup(db, pending.cleanup_id)
        db.commit()
    except Exception:
        # 참조 변경 transaction은 이미 commit됐다. cleanup 원장의 재시도 가능성을 보존한다.
        db.rollback()


@router.put("/datasets/{datasetId}/representative-image", name="putDatasetRepresentativeImage")
def put_representative_image(
        datasetId: str, request: Request, image: UploadFile = File(...),
        subject: Subject = Depends(current_subject), db: Session = Depends(scoped_db)) -> dict:
    dataset_id = _dataset_id(datasetId)
    _require_upload_edit(db, subject)
    require_body_access(db, dataset_id)
    file_name = (image.filename or "").strip()
    if not file_name or len(file_name) > 255:
        raise errors.bad_request("대표 그림 파일명은 1~255자다.")
    declared = (image.content_type or "").lower()
    if declared not in _CONTENT_TYPES:
        raise errors.ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "PNG·JPEG·WebP 그림만 올릴 수 있다.")
    payload = image.file.read(MAX_IMAGE_BYTES + 1)
    if len(payload) > MAX_IMAGE_BYTES:
        raise errors.payload_too_large("대표 그림은 10 MiB 이하여야 한다.")
    detected = _detected_content_type(payload)
    if detected is None or detected != declared:
        raise errors.ApiError(415, "UNSUPPORTED_MEDIA_TYPE",
                              "선언한 형식과 실제로 해석되는 PNG·JPEG·WebP가 같아야 한다.")

    d3_catalog.lock_dataset_for_representative_image(db, dataset_id)
    previous = d3_catalog.find_representative_image(db, dataset_id)
    image_id = Ulid.generate()
    key = storage_layout.representative_image_key(datasetId, str(image_id))
    storage = _storage(request)
    try:
        storage.put(key=key, payload=payload)
    except BaseException:
        _discard_new_or_remember(storage, db, subject, dataset_id, key)
        raise
    try:
        d3_catalog.upsert_representative_image(
            db, dataset_id=dataset_id, image_id=image_id, file_name=file_name,
            content_type=detected, size_bytes=len(payload), storage_key=key)
        if previous is not None:
            d3_catalog.queue_representative_image_cleanup(db, dataset_id, previous.storage_key)
        # 이전 바이트를 지우기 전에 새 참조를 확정한다. scoped_db의 마지막 commit은 재확인이다.
        db.commit()
    except BaseException:
        db.rollback()
        _discard_new_or_remember(storage, db, subject, dataset_id, key)
        raise
    _drain_cleanups(storage, db, subject, dataset_id, keep=key)
    return _metadata(d3_catalog.RepresentativeImage(
        dataset_id=datasetId, image_id=str(image_id), file_name=file_name,
        content_type=detected, size_bytes=len(payload), storage_key=key))


@router.get("/datasets/{datasetId}/representative-image", name="getDatasetRepresentativeImage")
def get_representative_image(datasetId: str, request: Request,
                             db: Session = Depends(scoped_db)) -> StreamingResponse:
    dataset_id = _dataset_id(datasetId)
    require_body_access(db, dataset_id)
    row = d3_catalog.find_representative_image(db, dataset_id)
    if row is None:
        raise errors.not_found("사용자 대표 그림이 없다.")
    try:
        chunks = _storage(request).open(key=row.storage_key)
    except FileNotFoundError:
        raise errors.not_found("대표 그림 바이트가 없다.") from None
    return StreamingResponse(chunks, media_type=row.content_type,
                             headers={"Content-Length": str(row.size_bytes)})


@router.delete("/datasets/{datasetId}/representative-image", name="deleteDatasetRepresentativeImage",
               status_code=204)
def delete_representative_image(datasetId: str, request: Request,
                                subject: Subject = Depends(current_subject),
                                db: Session = Depends(scoped_db)) -> Response:
    dataset_id = _dataset_id(datasetId)
    _require_upload_edit(db, subject)
    require_body_access(db, dataset_id)
    d3_catalog.lock_dataset_for_representative_image(db, dataset_id)
    removed = d3_catalog.delete_representative_image(db, dataset_id)
    if removed is not None:
        d3_catalog.queue_representative_image_cleanup(db, dataset_id, removed.storage_key)
    db.commit()
    _drain_cleanups(_storage(request), db, subject, dataset_id)
    return Response(status_code=204)
