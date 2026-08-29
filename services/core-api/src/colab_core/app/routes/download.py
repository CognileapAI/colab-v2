"""다운로드 집행 3 op — `downloadDataset`(묶음) · `downloadDatasetFile`(파일) · `getDownloadBytes`(바이트).

형태는 `PLAN-SoT §9 〈175〉-(다)` 가 정했다: **200 티켓 + 바이트 op**. 302 는 브라우저가
Bearer 를 못 실어 도달 불가라 기각됐다(계약 산문). 흐름은 셋으로 갈린다 —

  발급(두 op · Bearer 필수)
    주체 → 데이터셋 존재(404, 경계 밖 포함) → 본체 접근(`body_accessible` 아니면 403 — 상세는
    200 이지만 바이트를 주는 자리는 다르다, P-34) → 파일 단위면 그 데이터셋의 조각인가(404)
    → **이력 한 줄**(`d8_download`, 발급 시점) → 티켓 서명 → url 결정.
  url
    · 저장 모드 s3 + 파일 단위 = **프리사인드 GET 절대 URL** — 바이트가 core 를 안 거친다.
    · 그 밖(local 전부 · s3 묶음) = 이 seam 의 `getDownloadBytes` 상대 경로.
  바이트(`security: []`)
    티켓이 곧 자격이다. 서명 검증(틀리면 404 — 존재를 흘리지 않는다) → 만료(410) →
    **티켓의 주체로 경계를 다시 심고**(자기 세션 · `read_only_scope`) 파일 행을 다시 읽는다 —
    RLS `body_access` 가 재판정하므로 발급 뒤 잠기면 행이 안 보여 404 다. 그 뒤 스트리밍.

**서명 비밀값이 없으면 셋 다 500** (`DOWNLOAD_UNAVAILABLE`) — `createSession` 의
`SESSION_UNAVAILABLE` 과 같은 모양이다. 조용한 기본 키로 서명하는 순간 아무나 티켓을 위조한다.

묶음(zip)은 **탐색 불가 스트림 위에 `ZIP_STORED`·zip64** 로 쓴다 — 조각 하나를 다 읽지 않고
청크마다 `yield` 하므로 메모리는 청크 하나다. 압축하지 않는 이유: 과학 자료(NetCDF·GeoTIFF)는
이미 압축돼 있거나 커서, CPU 를 태워 얻는 것이 없고 스트리밍 크기를 미리 알 수도 없다.
"""
from __future__ import annotations

import datetime as dt
import io
import logging
import posixpath
import zipfile
from collections.abc import Callable, Iterator

from fastapi import APIRouter, Depends, Path, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...domains import d2_access, d3_catalog, d3_download, d8_insight
from ...domains.d3_catalog import FileRow
from ...kernel import errors, storage_layout
from ...kernel.auth import Subject
from ...kernel.download_ticket import (SCOPE_BUNDLE, SCOPE_FILE, TTL_SECONDS, DownloadClaims,
                                       DownloadTicketSigner, TicketExpired, TicketInvalid)
from ...kernel.ids import Ulid
from ...kernel.scope import read_only_scope
from ...kernel.storage_backends import content_disposition
from ...ports.storage import UploadStoragePort
from ..deps import current_subject, scoped_db
from .ingestion import _storage

router = APIRouter()

_log = logging.getLogger("colab_core.download")

#: 서명 비밀값이 없을 때의 봉투 코드 — `SESSION_UNAVAILABLE`(`routes/session.py`)과 같은 모양.
DOWNLOAD_UNAVAILABLE = "DOWNLOAD_UNAVAILABLE"

#: zip 엔트리를 밀어낼 때의 단위 — 저장 백엔드의 읽기 청크와 같은 급이면 된다.
ZIP_FLUSH = 1024 * 1024


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _iso(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _signer(request: Request) -> DownloadTicketSigner:
    signer = getattr(request.app.state, "download_tickets", None)
    if signer is None:
        # 비밀값이 없다. **기본 키로 서명하지 않는다** — 그 순간 티켓은 자격이 아니다.
        raise errors.ApiError(
            500, DOWNLOAD_UNAVAILABLE,
            "세션 서명 비밀값이 설정되지 않아 다운로드 티켓을 서명할 수 없다 "
            "(COLAB_CORE_SESSION_SECRET).")
    return signer


# ═══════════════════════════════ 발급 ═══════════════════════════════════════
def _accessible_dataset(db: Session, dataset_id: Ulid) -> d3_catalog.DatasetCore:
    """`listDatasetFiles` 와 **같은 판정**이다 — 존재(404)와 본체 접근(403)을 한 자리에서."""
    core = d3_catalog.find_dataset_core(db, dataset_id)
    if core is None:
        # 경계 밖이면 RLS 가 이미 행을 지웠고(P-9·P-10), 묘비면 상세 화면이 없다(§7).
        raise errors.not_found()
    access = d2_access.DatasetAccessAdapter(db).dataset_access([dataset_id]).get(str(dataset_id))
    if access is not None and not access.body_accessible:
        # 메타는 상세에서 보이지만 바이트는 본체 쪽이라 막힌다 (P-34). 그 자리가 `접근 요청` 이다.
        raise errors.forbidden("잠긴 데이터이고 허용 목록 밖이다.")
    return core


def _issue(request: Request, db: Session, subject: Subject, *, dataset_id: Ulid,
           row: FileRow | None, core: d3_catalog.DatasetCore) -> dict:
    """이력 → 서명 → url. 파일 단위면 `row` 가 그 조각, 묶음이면 None."""
    signer = _signer(request)
    file_id = None if row is None else Ulid(row.file_id)
    # **발급이 곧 이력이다** — 바이트 시점이 아니다 (계약 산문 · `DataModel §6.2`).
    d8_insight.record_download(db, account_id=subject.account_id, dataset_id=dataset_id,
                               file_id=file_id)
    now = _now()
    issued = signer.issue(dataset_id=dataset_id, file_id=file_id, subject=subject, now=now)
    expires_at = issued.expires_at
    if row is None:
        file_name = f"{core.name}.zip"
        byte_size = None      # zip 을 만들어 봐야 아는 값이다 — 지어내지 않는다 (계약 산문)
        url = _bytes_url(request, issued.ticket)
    else:
        file_name = row.file_name
        byte_size = row.size_bytes
        # s3 모드 = 프리사인드 GET 절대 URL. local 은 None 을 돌려주므로 아래로 떨어진다.
        presigned = _storage(request).presign_get(
            key=row.storage_key, file_name=file_name, expires_seconds=TTL_SECONDS, now=now)
        if presigned is not None:
            url, expires_at = presigned.url, presigned.expires_at
        else:
            url = _bytes_url(request, issued.ticket)
    return {
        "url": url,
        "expiresAt": _iso(expires_at),
        "fileName": file_name,
        "byteSize": byte_size,
        "scope": SCOPE_BUNDLE if row is None else SCOPE_FILE,
    }


def _bytes_url(request: Request, ticket: str) -> str:
    """이 seam 의 `getDownloadBytes` **상대 경로** — 접두(`/api/v1`)는 앱의 라우트 표가 안다.
    `main.API_PREFIX` 를 여기서 import 하면 순환이라, 이름으로 되짚는다."""
    return str(request.app.url_path_for("getDownloadBytes", ticket=ticket))


@router.get("/datasets/{datasetId}/download", name="downloadDataset")
def download_dataset(request: Request, dataset_ref: str = Path(alias="datasetId"),
                     subject: Subject = Depends(current_subject),
                     db: Session = Depends(scoped_db)) -> dict:
    """묶음 티켓 — 「부분 다운로드는 없고, 조각 묶음이면 묶어서 한 번에」는 그대로다."""
    if not Ulid.is_valid(dataset_ref):
        raise errors.bad_request("datasetId 가 정규 ID 가 아니다.")
    dataset_id = Ulid(dataset_ref)
    core = _accessible_dataset(db, dataset_id)
    return _issue(request, db, subject, dataset_id=dataset_id, row=None, core=core)


@router.get("/datasets/{datasetId}/files/{fileId}/download", name="downloadDatasetFile")
def download_dataset_file(request: Request, dataset_ref: str = Path(alias="datasetId"),
                          file_ref: str = Path(alias="fileId"),
                          subject: Subject = Depends(current_subject),
                          db: Session = Depends(scoped_db)) -> dict:
    """파일 단위 티켓 — 정본 「부분 다운로드 없음」의 개정 제안(회의 2026-08-23) 위에 선다."""
    if not Ulid.is_valid(dataset_ref) or not Ulid.is_valid(file_ref):
        raise errors.bad_request("정규 ID 가 아니다.")
    dataset_id, file_id = Ulid(dataset_ref), Ulid(file_ref)
    core = _accessible_dataset(db, dataset_id)
    row = d3_catalog.find_file(db, dataset_id=dataset_id, file_id=file_id)
    if row is None:
        # 다른 데이터셋의 조각이거나 없는 조각 — FK 는 이것을 못 막는다 (`file_belongs_to` 주석).
        raise errors.not_found()
    return _issue(request, db, subject, dataset_id=dataset_id, row=row, core=core)


# ═══════════════════════════════ 바이트 ═════════════════════════════════════
def _claims(request: Request, ticket: str) -> DownloadClaims:
    signer = _signer(request)
    try:
        return signer.verify(ticket, now=_now())
    except TicketExpired:
        raise errors.gone("수명이 지난 다운로드 티켓이다 — 다시 발급받는다.") from None
    except TicketInvalid:
        # 위조·훼손·형식 오류를 한 404 로 — 어느 쪽인지 말해 주는 것 자체가 정보다.
        raise errors.not_found() from None


@router.get("/downloads/{ticket}", name="getDownloadBytes")
def get_download_bytes(request: Request, ticket: str = Path(min_length=1, max_length=1024)
                       ) -> StreamingResponse:
    """`security: []` — `deps.scoped_db` 를 **쓸 수 없다**(헤더에 주체가 없다). 대신 티켓의
    주체로 자기 세션을 열어 경계를 심는다. 읽기 전용이고 행을 읽은 뒤 **트랜잭션을 닫고 나서**
    스트리밍한다 — 긴 다운로드가 커넥션을 붙들지 않는다."""
    claims = _claims(request, ticket)
    storage = _storage(request)
    with read_only_scope(request.app.state.session_factory, claims.subject) as db:
        core = d3_catalog.find_dataset_core(db, claims.dataset_id)
        if core is None:
            raise errors.not_found()
        if claims.file_id is not None:
            row = d3_catalog.find_file(db, dataset_id=claims.dataset_id, file_id=claims.file_id)
            rows = [] if row is None else [row]
        else:
            rows = d3_download.file_rows(db, claims.dataset_id)
    if not rows:
        # 발급 뒤 잠겼거나(`body_access` 가 행을 지웠다) 조각이 사라졌다 — 404, 존재를 흘리지 않는다.
        raise errors.not_found()

    if claims.file_id is not None:
        return _single(storage, rows[0])
    return _bundle(storage, rows, file_name=f"{core.name}.zip")


def _single(storage: UploadStoragePort, row: FileRow) -> StreamingResponse:
    try:
        stream = storage.open(key=row.storage_key)    # 없으면 **여기서** — 200 을 보내기 전에
    except FileNotFoundError:
        _log.error("event=download.bytes_missing fileId=%s key=%s", row.file_id, row.storage_key)
        raise errors.not_found("원장에는 있는데 바이트가 없다.") from None
    headers = {"Content-Disposition": content_disposition(row.file_name)}
    if row.size_bytes is not None:
        headers["Content-Length"] = str(row.size_bytes)
    return StreamingResponse(stream, media_type="application/octet-stream", headers=headers)


def _bundle(storage: UploadStoragePort, rows: list[FileRow], *, file_name: str) -> StreamingResponse:
    entries = [(name, row) for name, row in zip(entry_names(rows), rows)]

    def opener(row: FileRow) -> Callable[[], Iterator[bytes]]:
        return lambda: storage.open(key=row.storage_key)

    body = zip_stream([(name, opener(row), row.created_at) for name, row in entries])
    return StreamingResponse(body, media_type="application/zip",
                             headers={"Content-Disposition": content_disposition(file_name)})


def entry_names(rows: list[FileRow]) -> list[str]:
    """zip 안의 이름 — `relative_path`(없으면 `file_name`), 격자는 `grid/<file_name>`.

    겹치면 두 번째부터 `<stem>.<fileId 앞 8자>.<ext>` — 같은 이름의 본체 둘이 한 zip 에서
    한 조각으로 접히면 사용자는 그 사실을 모른다. 격자 디렉터리 이름은 저장 배치의 그것과 같다
    (`layout.json` `gridDirname`) — 풀었을 때의 모양이 서버의 자리와 같아야 한다.
    """
    out: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if row.kind == storage_layout.GRID_KIND:
            name = f"{storage_layout.GRID_DIRNAME}/{row.file_name}"
        else:
            name = row.relative_path or row.file_name
        if name in seen:
            head, base = posixpath.split(name)
            # 마지막 점 뒤를 **그대로** 뒤로 보낼 뿐이다 — 확장자를 읽거나 판정하지 않는다
            # (`DR-3` · `tests/test_uploads.py` 의 표 부재 시험이 확장자 함수 이름까지 금지한다).
            stem, dot, ext = base.rpartition(".")
            if not stem:                       # 점이 없거나 `.hidden` 처럼 점으로 시작한다
                stem, dot, ext = base, "", ""
            base = f"{stem}.{row.file_id[:8]}" + (f".{ext}" if dot else "")
            name = posixpath.join(head, base) if head else base
        seen.add(name)
        out.append(name)
    return out


class _Sink(io.RawIOBase):
    """`zipfile` 이 쓰는 **탐색 불가** 목적지 — 쓴 만큼 모아 두고 제너레이터가 비운다.

    `seekable()` 이 False 이므로 `zipfile` 은 데이터 디스크립터 방식으로 쓴다(크기·CRC 를
    엔트리 뒤에 적는다) — 그래서 조각의 크기를 미리 몰라도 되고, 한 조각을 다 읽어 들고
    있을 필요가 없다.
    """

    def __init__(self) -> None:
        self._buf = bytearray()

    def writable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return False

    def write(self, b) -> int:  # type: ignore[override]
        self._buf += b
        return len(b)

    def drain(self) -> bytes:
        out = bytes(self._buf)
        self._buf.clear()
        return out


def zip_stream(entries: list[tuple[str, Callable[[], Iterator[bytes]], dt.datetime]]
               ) -> Iterator[bytes]:
    """`ZIP_STORED`·zip64 스트리밍 zip. 엔트리마다 (이름, 열기, 시각).

    `force_zip64=True` — 탐색 불가 스트림에서는 크기를 미리 못 적으므로 4 GiB 를 넘는 조각이
    나중에 와도 헤더를 고칠 수 없다. 처음부터 zip64 로 적어야 한다.
    조각이 도중에 없으면(원장은 있는데 바이트가 없다) 스트림을 **끊는다** — 빠진 채 닫힌 zip 은
    「다 받았다」로 읽히고, 그것이 더 나쁘다. 로그가 어느 조각인지 말한다.
    """
    sink = _Sink()
    with zipfile.ZipFile(sink, mode="w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        for name, open_, created_at in entries:
            stamp = created_at.astimezone(dt.timezone.utc) if created_at.tzinfo else created_at
            info = zipfile.ZipInfo(name, date_time=(max(stamp.year, 1980), stamp.month, stamp.day,
                                                    stamp.hour, stamp.minute, stamp.second))
            info.compress_type = zipfile.ZIP_STORED
            try:
                source = open_()
            except FileNotFoundError:
                _log.error("event=download.bytes_missing entry=%s", name)
                raise
            with zf.open(info, mode="w", force_zip64=True) as dst:
                pending = 0
                for chunk in source:
                    dst.write(chunk)
                    pending += len(chunk)
                    if pending >= ZIP_FLUSH:
                        yield sink.drain()
                        pending = 0
            yield sink.drain()
    yield sink.drain()
