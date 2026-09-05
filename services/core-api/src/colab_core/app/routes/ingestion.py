"""업로드·등록 전환·파일 조작 — P2 가 501 에서 꺼내 오는 6 op + AI 제안 중계 1.

**이 WU 가 처음 되돌릴 수 없는 것을 만든다.** 표시 오류는 뒤에서 고칠 수 있지만 계보
오염은 그렇지 않다 (`P2.md §8-A`). 그래서 이 파일의 규칙은 대부분 「무엇을 안 하는가」다.

안 하는 것
  · **`createUpload` 는 D3 에 행을 만들지 않는다** (`〈64〉-ⓐ`). 등록은 사람이 누른다.
  · **`getUploadStatus` 는 새 사실을 만들지 않는다** — 이벤트 ②~⑦ 의 결과를 읽기만 한다.
  · **확장자로 포맷을 정하지 않는다** (`P2.md §2-10` · `DR-3` — `.nc` 가 HDF5, `.hdf` 가 HDF4).
    core-api 는 `detected_format` 을 한 번도 쓰지 않는다.
  · **격자 파일의 축을 추측하지 않는다** (`〈66〉`). 축은 파일을 읽는 쪽이 정한다.
  · **AI 제안을 저장하지 않는다** — 사람이 확인해 `createDataset` 에 실어 보낸 것만 저장된다
    (`CLAUDE.md §3-2`).
"""
from __future__ import annotations

import datetime as dt
import pathlib
import tempfile
from typing import Any

from fastapi import APIRouter, Body, Depends, File, Form, Query, Request, Response, UploadFile
from sqlalchemy.orm import Session

from ...domains import (d1_identity, d2_access, d3_catalog, d4_lineage, d5_ingestion,
                        d6_project, d8_insight)
from ...kernel import errors, storage_layout
from ...kernel.auth import Subject
from ...kernel.objectpath import normalize_relative_path
from ...kernel.s3 import S3Client
from ...kernel.storage_backends import LocalFilesystemStorage, S3UploadStorage
from ...ports.storage import UploadStoragePort
from ...kernel.ids import Ulid
from ...ports.ingestion import UploadFileRecord
from ..deps import current_subject, scoped_db
from .catalog import dataset_detail, validate_human_metadata

router = APIRouter()

#: 파일 종류 2값 (`common.json#FileKind`). 여기서 값 집합을 늘리지 않는다.
FILE_KINDS = ("본체", "기준 격자 파일")
BODY = "본체"
GRID = "기준 격자 파일"

#: 계약 `UploadFileRef.fileName` 의 상한과 같은 값. DB CHECK 도 255 다.
MAX_FILE_NAME = 255
#: 한 접수의 파일 수 상한 — 계약 `createUpload.files.maxItems` · `UploadTransferDraft.files.maxItems`
#: 와 **한 값**이다 (`〈339〉`). 프리사인드 라우트(`routes/upload_transfers.MAX_FILES`)가 이것을
#: import 한다 — 두 입구가 다른 상한을 갖지 않는다.
MAX_UPLOAD_FILES = 500
#: 계약 `relativePath` 의 상한 — DB CHECK(`d5_upload_file`·`d3_file`)도 1024 다.
MAX_RELATIVE_PATH = 1024


def _relative_path(raw: str | None) -> str | None:
    """`relativePath` 한 칸의 정규화 — **프리사인드 경로와 같은 함수·같은 상한** (`〈337〉`·`〈339〉-(나)`).

    빈 문자열은 「경로 없음」이다 — multipart 배열은 null 을 싣지 못한다(계약 산문).
    정규화 뒤 세그먼트가 남지 않는 값(`..` · `/` 뿐)은 400. `..` 세그먼트 자체는 정규화가
    **떨어뜨린다**(`kernel/objectpath`) — 그 규칙은 FE `normalizeName.ts` 와 한 글자도 다르면 안 되므로
    여기서 더 엄격한 규칙을 만들지 않는다.
    """
    if raw is None or raw == "":
        return None
    try:
        path = normalize_relative_path(raw)
    except ValueError:
        raise errors.bad_request(f"relativePath 를 정규화할 수 없다 — 남는 세그먼트가 없다: {raw!r}")
    if len(path) > MAX_RELATIVE_PATH:
        raise errors.bad_request(f"relativePath 가 {MAX_RELATIVE_PATH}자를 넘는다.")
    return path

#: 한 번에 옮기는 바이트. **메모리는 이 값에 묶인다** — 파일 크기가 아니라
#: (`kernel/file_store.STREAM_CHUNK` 이 내려받기 쪽에 적은 것과 같은 규칙).
_STREAM_CHUNK = 1 << 20


# ── 저장 ────────────────────────────────────────────────────────────────────
# ⭑ 병합(창 8-a) — 종전 `main` 의 `_storage_root`/`_store`/`_discard`(로컬 디스크 직접 조작)는
#   아래 저장 Port 가 대신한다. 그 셋이 지키던 것 둘은 Port 안에 그대로 있다:
#     · **바이트를 흘려 보낸다**(`CODE-REVIEW-20260903` #10) — `put_stream` 이 청크로 쓴다.
#       종전 `await upload_file.read()` 전량 적재가 5GB 업로드 하나로 프로세스를 멈췄다.
#     · **쓴 바이트 수를 저장한 쪽이 센다** — `Content-Length` 를 믿지 않는다.
#   ⚠ 라우트는 `main`(`9aed645`)의 판정대로 **`def`** 로 남는다 — `async def` 로 두면 동기
#     SQLAlchemy 와 디스크 쓰기가 이벤트 루프에서 돈다.
# 바이트를 만지는 자리는 전부 저장 Port(`ports/storage.py`) 경유다 — 로컬 디스크와
# S3 가 여기서 갈린다 (`〈337〉`). **저장 키가 곧 배치**라는 규칙은 그대로다: 키는
# `kernel/storage_layout`(정본 `contracts/storage/layout.json`)이 만들고, 세 단위가
# 같은 생성물을 쓴다 — 키 규칙이 두 곳에 적혀 갈라졌던 실패(`03-HANDOFF §4 #20`)의 봉인.
def _storage(request: Request) -> UploadStoragePort:
    """설정이 정한 저장 백엔드. 앱마다 한 번 만들어 재사용한다.

    local 모드에서 `upload_storage_dir` 이 없으면 프로세스마다 한 번 만드는 임시
    디렉터리를 쓴다 — **바이트를 버리고 201 을 내리지 않기 위해서다.**
    """
    cached = getattr(request.app.state, "upload_storage", None)
    if cached is not None:
        return cached
    settings = request.app.state.settings
    if getattr(settings, "storage_mode", "local") == "s3":
        client = S3Client(bucket=settings.s3_bucket, region=settings.s3_region)
        storage: UploadStoragePort = S3UploadStorage(client)
    else:
        configured = getattr(settings, "upload_storage_dir", None)
        root = pathlib.Path(configured) if configured \
            else pathlib.Path(tempfile.mkdtemp(prefix="colab-uploads-"))
        storage = LocalFilesystemStorage(root)
    request.app.state.upload_storage = storage
    return storage


def _dataset_keys(dataset_id: str, files) -> dict[str, str]:
    """그 파일들이 **데이터셋의 자리**에서 가질 저장 키. 계산은 규약 함수 하나뿐이다."""
    return {f.file_id: storage_layout.storage_key(dataset_id, file_id=f.file_id,
                                                  kind=f.kind, file_name=f.file_name)
            for f in files}


# ── 권한 ────────────────────────────────────────────────────────────────────
def _require_upload_edit(db: Session, subject: Subject) -> None:
    """판정은 언제나 `업로드·편집` 스위치가 한다 (`〈59〉-②` · `P-6`).

    **소유자는 별도 관문이 아니다** — 「소유권 있는 사람이 조정하는 것」은 격자 파일의
    성격 서술이지 판정 축이 아니다 (`P2.md §2-23`).
    """
    role = d2_access.role_of(db, subject.account_id)
    permissions = d2_access.permissions_of(db, subject.account_id, role)
    if not permissions.get("업로드·편집"):
        raise errors.forbidden("`업로드·편집` 스위치가 꺼져 있다.")


def _ledger(db: Session) -> d5_ingestion.UploadLedgerAdapter:
    """`d5_*` 로 가는 **유일한 문**. 라우트가 그 표를 직접 알지 않는다 (`〈63〉-㉱`)."""
    return d5_ingestion.UploadLedgerAdapter(db)


def _ttl(request: Request) -> dt.timedelta:
    """수명은 **운영 설정**이다 (`〈67〉-ⓐ`) — 정본은 숫자를 갖지 않는다."""
    return dt.timedelta(hours=request.app.state.settings.upload_ttl_hours)


def _live_upload(db: Session, upload_id: Ulid, *, now: dt.datetime | None = None):
    """살아 있는 업로드만 돌려준다. 아니면 **404** — 「만료 뒤에는 없는 것으로 답한다」
    (`〈67〉-ⓐ` 규칙 ③).

    **시계가 처리를 앞지르지 않는다**(규칙 ②) — 만료 시각을 지났어도 파이프라인이 아직
    일하고 있으면 살아 있다. 이 한 줄이 없으면 ㉳(만료 404)이 green 인 채로 정상 처리 중인
    업로드를 404 로 지운다.
    """
    record = _ledger(db).find(upload_id, now=now)
    if record is None:
        return None
    reference = now or dt.datetime.now(dt.timezone.utc)
    if record.expires_at <= reference and not record.processing:
        return None
    return record


def _file_records(upload_files) -> list[dict[str, Any]]:
    """계약 `UploadFileRef`. 원장이 아는 다른 열은 FE 표면에 내리지 않는다.

    ⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 7⟩ **`gridAxis` 가 붙었다** — 기준 격자
    파일이고 축이 확정된 경우에만. 등록 뒤의 `DatasetFile.gridAxis` 와 **같은 모양**이다.
    화면이 뒤집기 버튼을 그리려면 지금 배정이 무엇인지 알아야 하는데, 등록 **전** 세계에는
    그 값을 말할 자리가 없었다(스윕 `B-2`).

    ⚠ **본체에는 붙이지 않는다.** 축이 붙은 본체는 `0004` 의 CHECK 가 애초에 만들지 않으므로
    거기 `false/false` 를 실으면 **없는 사실**을 말하는 것이 된다.

    `relativePath` 는 **있을 때만** 싣는다 (`〈339〉-(나)`) — 낱개 파일에 빈 키를 만들지 않는다.
    """
    out: list[dict[str, Any]] = []
    for f in upload_files:
        row: dict[str, Any] = {
            "fileId": f.file_id, "fileName": f.file_name, "kind": f.kind,
            "byteSize": 0 if f.byte_size is None else f.byte_size}
        if f.relative_path:
            row["relativePath"] = f.relative_path
        if f.kind == GRID and (f.carries_lat or f.carries_lon):
            row["gridAxis"] = {"carriesLat": bool(f.carries_lat),
                               "carriesLon": bool(f.carries_lon)}
        out.append(row)
    return out


# ═══════════════════════════════ createUpload ═══════════════════════════════
@router.post("/uploads", name="createUpload", status_code=201)
def create_upload(request: Request, response: Response,
                  files: list[UploadFile] = File(...),
                  fileKinds: list[str] | None = Form(default=None),
                  relativePaths: list[str] | None = Form(default=None),
                  subject: Subject = Depends(current_subject),
                  db: Session = Depends(scoped_db)) -> dict:
    """**`upload.accepted` 를 발행하는 유일한 자리다.**

    ⚠ **`def` 다 — `async def` 가 아니다** (`CODE-REVIEW-20260903` #10). 이 라우트는
    바이트를 디스크에 쓰고 **동기 SQLAlchemy** 로 원장을 세운다. `async def` 로 두면
    그 둘이 이벤트 루프에서 돌아 업로드 하나가 프로세스의 모든 요청을 멈춘다. `def` 는
    스레드풀에서 돈다 — 형제 라우트가 전부 그렇게 서 있다.

    봉투가 타입마다 `source` 를 const 로 못 박았고(`envelope.json`), 그 능력을 행사하는
    HTTP 입구가 이 op 이다. `UploadReceipt` 가 `uploadId`·`fileId` 를 **FE 표면에 처음** 내린다
    (`SEAM-AUDIT` I-01·I-06 — 소비만 있고 생산이 없던 두 식별자).

    **D3 에 행을 만들지 않는다.**

    폴더 경로(`relativePaths`)는 원장 메타로만 보존한다 (`〈337〉`·`〈339〉-(나)`) — 저장 키는
    그대로 평평하다. 바이트는 `put_stream` 으로 흘려보낸다 — 본문을 통째로 메모리에 올리지 않는다.
    """
    _require_upload_edit(db, subject)
    if not files:
        raise errors.bad_request("files 가 비었다 — 파일 없이 업로드를 접수하지 않는다.")
    if len(files) > MAX_UPLOAD_FILES:
        raise errors.bad_request(f"files 는 1~{MAX_UPLOAD_FILES}개다.")

    kinds = list(fileKinds or [])
    if not kinds:
        kinds = [BODY] * len(files)          # 생략하면 전부 `본체` (계약 산문)
    if len(kinds) != len(files):
        raise errors.bad_request("fileKinds 는 files 와 같은 순서·같은 개수여야 한다.")
    unknown = sorted(set(kinds) - set(FILE_KINDS))
    if unknown:
        raise errors.bad_request(f"파일 종류가 2값 밖이다: {unknown}")
    paths_raw = list(relativePaths or [])
    if not paths_raw:
        paths: list[str | None] = [None] * len(files)   # 생략하면 전부 경로 없음 (계약 산문)
    elif len(paths_raw) != len(files):
        raise errors.bad_request("relativePaths 는 files 와 같은 순서·같은 개수여야 한다.")
    else:
        paths = [_relative_path(p) for p in paths_raw]
    # ⚠ **여기서 「본체 1건 이상」을 요구하지 않는다.** 그 불변식은 **데이터셋의 성질**이고
    # (`DataModel §4.3`), 접수는 D3 에 아무것도 만들지 않는다 (`〈64〉-ⓐ`). 그래서 판정은
    # 등록 전환(`createDataset`)이 한다 — 아래 그 자리에 있다.
    # **격자만 든 묶음이 접수돼야 격자 후주입이 성립한다**(Ted 2026-08-25 판정 · 사용자
    # 관점 우선 — 「격자를 나중에 붙이는 행위」 = 파일 업로드). 그 묶음의 소비처는
    # `attachUploadGridFiles` 이고, 등록 전환은 여전히 본체를 요구한다.

    upload_id = Ulid.generate()
    records: list[UploadFileRecord] = []
    for upload_file, kind, relative_path in zip(files, kinds, paths):
        name = (upload_file.filename or "").strip()
        if not name or len(name) > MAX_FILE_NAME:
            raise errors.bad_request("파일 이름은 1~255자다.")
        file_id = Ulid.generate()
        key = storage_layout.storage_key(str(upload_id), file_id=str(file_id),
                                         kind=kind, file_name=name)
        # 크기는 **저장한 쪽이 센 값**이다 — `Content-Length` 도 클라이언트 신고도 믿지 않는다.
        upload_file.file.seek(0)
        byte_size = _storage(request).put_stream(key=key, stream=upload_file.file)
        records.append(UploadFileRecord(
            file_id=str(file_id), file_name=name, kind=kind, byte_size=byte_size,
            storage_key=key,
            # **축을 추측하지 않는다** — 격자 파일의 축은 파일을 읽는 쪽이 정한다 (`〈66〉`).
            carries_lat=False, carries_lon=False,
            # **확장자로 포맷을 정하지 않는다** — 매직바이트 판정은 파이프라인의 일이다.
            detected_format=None,
            relative_path=relative_path,
        ))

    ledger = _ledger(db)
    ledger.accept(upload_id=upload_id, uploader_account_id=subject.account_id,
                  expires_at=dt.datetime.now(dt.timezone.utc) + _ttl(request),
                  files=records)
    ledger.publish_accepted(upload_id=upload_id, actor_account_id=subject.account_id,
                            files=records)
    return {"uploadId": str(upload_id), "files": _file_records(records)}


# ══════════════════════════════ getUploadStatus ═════════════════════════════
@router.get("/uploads/{uploadId}", name="getUploadStatus")
def get_upload_status(uploadId: str,
                      subject: Subject = Depends(current_subject),
                      db: Session = Depends(scoped_db)) -> dict:
    """이벤트 ②~⑦ 의 결과를 읽는다. **새 사실을 만들지 않는다.**"""
    if not Ulid.is_valid(uploadId):
        raise errors.bad_request("uploadId 가 정규 ID 가 아니다.")
    upload_id = Ulid(uploadId)
    record = _live_upload(db, upload_id)
    if record is None:
        # 없는 업로드 · 경계 밖 · 수명이 다한 것을 **같은 404** 로 낸다.
        raise errors.not_found("없거나 수명이 다한 업로드다.")
    ledger = _ledger(db)
    files = ledger.files(upload_id)
    return {
        "uploadId": record.upload_id,
        "files": _file_records(files),
        # **거절된 격자는 `files` 에 못 선다** — 행이 없기 때문이다. 사라진 이유를
        # 말하는 자리가 이것이다 (`〈88〉` 묶음 7 · 스윕 `B-2`).
        "gridRejections": ledger.grid_rejections(upload_id),
        "ready": record.ready,
        "renderable": record.renderable,
        "metadataComplete": record.metadata_complete,
        "expiresAt": record.expires_at.astimezone(dt.timezone.utc).isoformat(),
        # **등록됐는가** — 도장의 유무만 말한다. 어느 데이터셋인지는 말하지 않는다(원장은 D3 를
        # 가리키지 않는다 · `d5_ingestion.py` 머리말). 이 값이 없으면 화면이 브라우저 기억에만
        # 기대게 되고, 등록 직후 탭이 죽으면 **이미 끝낸 것을 「등록만 남았어요」라고 말한다**.
        "registered": record.registered_at is not None,
        "failure": None if record.failure_reason is None else {"reason": record.failure_reason},
    }


# ─────────────────────────── AI 제안에 넘길 파일 메타 ────────────────────────
def _uploaded_file_meta(ledger, upload_id: Ulid) -> dict[str, Any]:
    """계약 `core-ai.yaml#UploadedFileMeta` 를 **원장에서 읽은 값으로만** 조립한다.

    ⭑ **⟨신설 2026-08-30⟩ 이 자리가 비어 있어서 중계가 계약과 다른 모양을 보내고 있었다.**
    ai-service 는 업로드 원장도 파일 바이트도 읽지 못한다(`DOMAINS §4`) — 그래서 계약이
    「이미 읽은 값」을 본문에 실으라고 적었고, 읽는 쪽은 D5 의 주인인 core-api 다.

    두 규칙을 지킨다.
      ① **헤더를 못 읽은 항목은 열쇠 자체를 만들지 않는다.** 빈 문자열·빈 배열로 채우면
         「못 읽음」과 「값 없음」이 갈리지 않는다 (계약 `UploadedFileMeta` 산문).
      ② **지어내지 않는다.** `format` 은 감지 이벤트가 말한 값이고, 판정이 없으면 생략한다.
    """
    files = ledger.files(upload_id)
    held = ledger.held_auto_metadata(upload_id)
    # 묶음 이름 = 본체 우선. `_FILES` 가 `kind DESC` 로 본체를 앞세운다.
    head = files[0] if files else None
    meta: dict[str, Any] = {
        "fileName": (head.file_name if head else "") or "이름 없는 업로드",
        "kind": head.kind if head else BODY,
    }
    fmt = held.format or getattr(head, "detected_format", None)
    if fmt:
        meta["format"] = fmt
    if held.variables:
        meta["variables"] = [v for v in held.variables if isinstance(v, str) and v]
        if not meta["variables"]:
            del meta["variables"]
    if held.crs:
        meta["crs"] = held.crs
    if held.grid:
        meta["gridDescription"] = held.grid
    if held.period_start:
        meta["periodStart"] = held.period_start
    if held.period_end:
        meta["periodEnd"] = held.period_end
    if len(files) > 1:
        meta["partCount"] = len(files)
    return meta


# ═══════════════════ listUploadLineageSuggestions (중계) ════════════════════
@router.get("/uploads/{uploadId}/lineage-suggestions", name="listUploadLineageSuggestions")
def list_upload_lineage_suggestions(
        request: Request, uploadId: str,
        datasetNameDraft: str | None = Query(default=None),
        subject_q: str | None = Query(default=None, alias="subject"),
        subject: Subject = Depends(current_subject),
        db: Session = Depends(scoped_db)) -> dict:
    """AI 계보 제안 조회 — **중계만** 한다. 확정 오퍼레이션이 아니다.

    `ai-service` 가 아직 비어 있으므로 지금 이 op 이 낼 수 있는 참인 답은 **0건**이다.
    그것을 200 + `degraded: true` + 빈 배열로 말한다 — **억지 제안을 만들지 않는다**
    (`CLAUDE.md §3` · `P2.md §2-8`). 5xx 로 끝내지 않는 이유는 **AI 없이도 v2 가
    완결된 제품**이기 때문이다.
    """
    if not Ulid.is_valid(uploadId):
        raise errors.bad_request("uploadId 가 정규 ID 가 아니다.")
    if _live_upload(db, Ulid(uploadId)) is None:
        raise errors.not_found("없거나 수명이 다한 업로드다.")
    lab = d1_identity.find_lab(db)
    searched = d3_catalog.count_datasets(db)
    # **계약이 요구하는 것은 식별자가 아니라 읽은 값이다** — `_uploaded_file_meta` 참조.
    return request.app.state.suggestions.suggest(
        lab_id=str(subject.lab_id), lab_name=("" if lab is None else lab["name"]) or "연구실",
        account_id=str(subject.account_id),
        file_meta=_uploaded_file_meta(_ledger(db), Ulid(uploadId)),
        searched_count=searched, dataset_name_draft=datasetNameDraft, subject=subject_q,
    )


# ═══════════════════════════════ createDataset ══════════════════════════════
#: ⭑ **2026-09-02 · `#62`** — `variables`·`crs`·`period` 를 **넣었다.** 계약 `DatasetCreate`
#: 는 `〈138〉`(정본 `VAL-006` 「변수·기간·좌표계는 자유 입력」) 이래 셋을 선언하고 있었는데
#: 서버는 UPDATE 절반만 세웠다 — 실어 보내면 400 이었다. 계약 변경 0 · 마이그레이션 0
#: (열은 `d3_dataset_autometa` 에 이미 있다).
_ALLOWED_CREATE_FIELDS = {"uploadId", "name", "topic", "summary", "sourceLabel",
                          "lineageParents", "projectIds",
                          "variables", "crs", "period"}

#: 등록 요청이 실어 오는 **사람이 적는 자유 입력 칸.** 저장은 `updateDataset` 이 쓰는
#: 그 경로 하나를 그대로 쓴다 (`d3_catalog.update_dataset`).
_HUMAN_METADATA_FIELDS = ("variables", "crs", "period")


def _human_metadata(body: dict) -> dict:
    """**폼 기본값 통과 ≠ 사람이 적었다.**

    빈 배열·빈 문자열·`null` 을 값으로 저장하면 `_APPLY_AUTOMETA` 의 「빈 칸만 채운다」가
    영영 막혀 그 칸이 **영구 공란**이 된다 (`〈140〉`-㉱ 와 같은 실패형). 그래서 빈 값은
    **안 보낸 것으로 다룬다** — 지우는 뜻의 `null` 은 등록 시점에 존재할 수 없다
    (지울 값이 아직 없다).
    """
    picked: dict = {}
    for key in _HUMAN_METADATA_FIELDS:
        value = body.get(key)
        if value is None or value == "" or value == []:
            continue
        picked[key] = value
    return picked
_ALLOWED_PARENT_FIELDS = {"parentDatasetId", "parentRole", "method", "origin",
                          "confirmedMethodText"}


def _parse_parents(raw: Any) -> list[dict]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise errors.bad_request("lineageParents 는 배열이다.")
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            raise errors.bad_request("lineageParents 항목이 객체가 아니다.")
        unknown = set(item) - _ALLOWED_PARENT_FIELDS
        if unknown:
            raise errors.bad_request(f"계약에 없는 필드다: {sorted(unknown)}")
        parent_id = item.get("parentDatasetId")
        if not Ulid.is_valid(parent_id):
            raise errors.bad_request("parentDatasetId 가 정규 ID 가 아니다.")
        origin = item.get("origin")
        if origin not in ("ai", "manual"):
            # **필수다.** 업로드 화면엔 두 경로가 다 있어 요청이 실어야 서버가 안다.
            # `processed`(가공으로 자동 생성)는 **여기서 받지 않는다** — 사람이 올리는 경로가
            # 만들 수 있는 값이 아니다. 생산 경로는 아직 없다 (`PLAN-SoT §9 〈205〉`).
            raise errors.bad_request("origin 은 `ai` 또는 `manual` 이다.")
        role = item.get("parentRole") or "주입력"    # 생략하면 기본값 (`Policy §5`)
        if role not in ("주입력", "보조입력"):
            raise errors.bad_request("parentRole 은 `주입력` 또는 `보조입력` 이다.")
        method, confirmed = item.get("method"), item.get("confirmedMethodText")
        if method is not None and confirmed is not None:
            # 계약이 「둘 다 오면 400」이라 적었다 — 같은 자리로 접히는 값이다.
            raise errors.bad_request("method 와 confirmedMethodText 를 함께 보내지 않는다.")
        out.append({"parent_id": Ulid(parent_id), "role": role,
                    "method": method if method is not None else confirmed, "origin": origin})
    return out


@router.post("/datasets", name="createDataset", status_code=201)
def create_dataset(request: Request, body: dict = None,
                   subject: Subject = Depends(current_subject),
                   db: Session = Depends(scoped_db)) -> dict:
    """**등록 전환**이다 — 「새 데이터셋을 만든다」가 아니다.

    한 요청 = 한 트랜잭션이라 **전환 + 파일 + 계보 + 프로젝트가 통째로 서거나 통째로 없다**
    (음성 시험 ㉰ 등록 원자성). 중간에 하나라도 실패하면 D3 에 반쪽 행이 남지 않는다.

    **`fileId` 동일성** — 업로드가 발급한 ULID 가 `d3_file.id` 로 그대로 간다. FK 가 없어
    (불변규칙 1) DB 는 새 ULID 를 넣어도 아무 말 안 한다 — 지키는 것은 이 코드와
    `tests/test_dataset_registration.py` 의 단언뿐이다 (`NB-A`).
    """
    _require_upload_edit(db, subject)
    if not isinstance(body, dict):
        raise errors.bad_request("요청 본문이 객체가 아니다.")
    unknown = set(body) - _ALLOWED_CREATE_FIELDS
    if unknown:
        raise errors.bad_request(f"계약에 없는 필드다: {sorted(unknown)}")

    upload_ref = body.get("uploadId")
    if not Ulid.is_valid(upload_ref):
        raise errors.bad_request("uploadId 가 정규 ID 가 아니다.")
    upload_id = Ulid(upload_ref)
    name = body.get("name")
    if not isinstance(name, str) or not name.strip():
        raise errors.bad_request("name 은 1자 이상이다.")
    source_label = body.get("sourceLabel")
    if source_label is not None and (not isinstance(source_label, str) or len(source_label) > 60):
        raise errors.bad_request("sourceLabel 은 60자 이하다.")
    # 세 자유 입력 칸의 형상 — **수정 경로와 같은 함수다.** 두 벌을 두지 않는다 (`#62`).
    human_metadata = _human_metadata(body)
    validate_human_metadata(human_metadata)
    parents = _parse_parents(body.get("lineageParents"))
    project_ids = body.get("projectIds") or []
    if not isinstance(project_ids, list) or any(not Ulid.is_valid(p) for p in project_ids):
        raise errors.bad_request("projectIds 는 정규 ID 배열이다.")

    ledger = _ledger(db)
    record = _live_upload(db, upload_id)
    if record is None:
        raise errors.not_found("없거나 수명이 다한 업로드다.")
    if record.registered_at is not None:
        raise errors.conflict("이미 등록 전환된 업로드다 — 같은 업로드로 데이터셋을 두 번 만들지 않는다.")
    files = ledger.files(upload_id)
    if not files:
        raise errors.bad_request("접수된 파일이 없다.")
    if not any(f.kind == BODY for f in files):
        # **본체 1건 이상** (`DataModel §4.3`). 격자만 올린 묶음은 데이터가 아니라 좌표다.
        # 판정이 접수가 아니라 **여기** 있는 이유 — 격자만 든 업로드는 후주입의 재료로
        # 정상 상태이고(`attachUploadGridFiles`), 데이터셋이 되는 것만 막으면 된다.
        raise errors.bad_request(
            "본체 파일이 최소 1건 있어야 한다 — 기준 격자 파일만 든 묶음은 "
            "데이터셋이 아니라 좌표다. 이미 있는 데이터셋에 붙이려면 "
            "`/datasets/{datasetId}/grid-files` 로 반영한다.")

    # ① 원장 도장을 **먼저** 찍는다. 두 요청이 동시에 오면 UPDATE 의 행 잠금이 하나를
    #    떨어뜨리고, 떨어진 쪽은 409 가 된다 — 데이터셋이 둘 생기지 않는다.
    if not ledger.mark_registered(upload_id):
        raise errors.conflict("이미 등록 전환된 업로드다.")

    dataset_id = Ulid.generate()
    body_files = [f for f in files if f.kind == BODY]
    formats = {f.detected_format for f in files if f.detected_format}
    d3_catalog.register_dataset(
        db, dataset_id=dataset_id, owner_id=subject.account_id,
        uploader_id=subject.account_id, name=name.strip(), topic=body.get("topic"),
        summary=body.get("summary"), source_label=source_label,
        # 포맷은 **파이프라인이 판정한 값**만 옮긴다. 조각마다 다르면 아직 모르는 것이다.
        detected_format=(formats.pop() if len(formats) == 1 else None),
        bundle_file_name=(body_files[0].file_name if body_files else None),
        # **합계를 손으로 넣지 않는다.** 0 으로 세우면 아래 ② 의 파일 INSERT 가 트리거
        # (`0009` `sync_dataset_total_size`)로 합계를 더한다. 여기서 sum 을 쓰면 **두 번 센다** —
        # 시드가 그렇게 200 == 100 red 를 냈다 (`tests/test_dataset_detail.py`).
        total_size_bytes=0,
    )

    # ①-a **사람이 적은 값을 먼저 쓴다** (`#62` · 정본 `VAL-006` · `〈138〉`).
    #
    # **순서가 곧 규칙이다.** 바로 아래 `apply_autometa` 는 「빈 칸만 채운다」(`COALESCE`)라,
    # 사람 값이 **먼저** 들어가 있으면 헤더 파싱 사건이 그것을 덮지 못한다. 뒤집으면
    # 사용자의 입력이 화면에 아무 말도 남기지 않고 사라진다.
    if human_metadata:
        d3_catalog.update_dataset(db, dataset_id=dataset_id, changes=human_metadata)

    # ①-b **보류된 사건을 반영한다** (`〈190〉` 사건 경유 되쓰기 · 반영 시점 = 여기).
    #
    # 사건은 **등록 전**에 났고(`upload.ready` 축자 「저장된 것은 아무것도 없다」) 값이 사는
    # 장부 행은 **바로 위에서** 생겼다. 그 사이 사건은 `d5_pipeline_event` 에 **보류**돼 있었다 —
    # 큐도 메모리도 아니다. 재기동을 건너도 남는 이유가 그것이고, 「버린다」를 고르지 않은
    # 이유도 그것이다(버리면 값이 영영 안 들어간다 = 지금 상태의 재현).
    #
    # **같은 트랜잭션이다** — 데이터셋이 생겼는데 값만 안 들어간 반쪽이 남지 않는다.
    # 판정은 하지 않는다: 사건이 말한 것을 옮길 뿐이고(`core-api` 는 파일을 못 읽는다),
    # 사람이 이미 고친 칸은 덮지 않는다(`apply_autometa` 의 `COALESCE`).
    held = ledger.held_auto_metadata(upload_id)
    d3_catalog.apply_autometa(
        db, dataset_id=dataset_id, format=held.format, crs=held.crs, grid=held.grid,
        period_start=held.period_start, period_end=held.period_end,
        variables=held.variables, total_size_bytes=held.byte_size_total)

    # ② 파일 — **업로드가 발급한 `fileId` 그대로.** 저장 키는 **데이터셋의 자리**다
    #    (`_relocate` 주석 — 승계하면 등록된 데이터셋 전체가 렌더 404 다).
    #    폴더 경로(`relative_path`)는 원장에서 그대로 승계한다 (`0009` · `〈339〉-(나)`).
    new_keys = _dataset_keys(str(dataset_id), files)
    for f in files:
        d3_catalog.insert_file(
            db, file_id=f.file_id, dataset_id=dataset_id, kind=f.kind,
            file_name=f.file_name, size_bytes=f.byte_size,
            storage_key=new_keys[f.file_id],
            carries_lat=f.carries_lat, carries_lon=f.carries_lon,
            relative_path=f.relative_path)

    # ③ 계보 — **사람이 확인한 것만** 온다. 비어 있으면 `기록 없음` 이고 등록은 막지 않는다.
    if parents:
        for p in parents:
            if not d3_catalog.dataset_exists(db, p["parent_id"]):
                raise errors.bad_request("부모 데이터셋이 없거나 연구실 경계 밖이다.")
            try:
                d4_lineage.add_parent(
                    db, child_id=dataset_id, parent_id=p["parent_id"],
                    parent_role=p["role"], method=p["method"], origin=p["origin"],
                    confirmed_by=subject.account_id)
            except d4_lineage.LineageCycle as e:
                raise errors.conflict(str(e)) from None
        d3_catalog.confirm_lineage(db, dataset_id)
    else:
        d4_lineage.mark_unknown(db, dataset_id=dataset_id, actor_id=subject.account_id)

    # ④ 프로젝트 — 등록 폼이 한 번에 제출한다.
    for project_id in project_ids:
        pid = Ulid(project_id)
        if not d6_project.project_exists(db, pid):
            raise errors.bad_request("프로젝트가 없거나 연구실 경계 밖이다.")
        d6_project.link_dataset(db, project_id=pid, dataset_id=dataset_id)

    # ⑤ 바이트 — **판정이 다 끝난 뒤에** 옮긴다. 앞에서 실패하면 바이트는 그대로다.
    _storage(request).relocate(files=files, new_keys=new_keys)
    # ⑥ **올린 일이 최근 활동을 만든다** (계약 `listActivities` 산문 · WU-P7).
    #    등록이 다 끝난 뒤에 적는다 — 위에서 떨어진 요청은 데이터셋을 만들지 않았으므로
    #    활동도 없다(활동만 남으면 목록이 없는 데이터셋을 가리킨다).
    d8_insight.record_activity(db, actor_id=subject.account_id,
                               action=d8_insight.ACTION_DATASET_ADDED,
                               target_kind="데이터셋", target_id=dataset_id)
    return dataset_detail(db, subject, dataset_id)


# ═════════════════════ addDatasetFile · 교체 · 삭제 (〈60〉) ═════════════════
#: `〈339〉-(라)` — 본체 파일 추가·교체·삭제의 활동 문자열. **`[정본 무근거]`** (`〈341〉-⑦-⑾` Ted 판정 대기).
#: 정본 §6.1 은 값 집합을 안 닫았고 `〈60〉` 은 격자 것(`d8_insight.ACTION_GRID_CHANGED`)만 고정했다.
#: 격자와 **다른** 문자열인 이유 — 바뀐 것이 좌표를 읽을 수단이 아니라 과학 데이터 자체라, 활동
#: 화면에서 두 사건이 갈려 보여야 한다. 상수가 여기(라우트) 사는 것은 D8 표면을 늘리지 않기 위해서다 —
#: `record_activity(action=…)` 는 자유 문자열이고 DB CHECK 는 비어 있지 않음만 본다.
ACTION_BODY_CHANGED = "본체 파일 변경"


def _record_grid_activity(db: Session, *, subject: Subject, dataset_id: Ulid) -> None:
    """`〈60〉` — 후주입·교체·삭제는 **계보를 접지 않고 이력에 남긴다.**

    ① `마지막 수정` 을 건드리지 않는다 → 파생인 `계보 상태` 가 `확정` → `확인 필요` 로
       접히지 않는다. 경보가 잦으면 사람이 경보를 끈다.
    ② `자동으로 읽은 정보`(좌표계·격자)는 재계산한다 — 그 값이 이 파일에서 나온다.
    ③ `d8_activity` 에 `좌표계·격자 변경` 한 행.
    """
    d3_catalog.recompute_grid_metadata(db, dataset_id)
    d8_insight.record_activity(
        db, actor_id=subject.account_id, action=d8_insight.ACTION_GRID_CHANGED,
        target_kind="데이터셋", target_id=dataset_id)


def _record_body_activity(db: Session, *, subject: Subject, dataset_id: Ulid) -> None:
    """`〈339〉-(라)` — 본체 추가·교체·삭제. **격자(`_record_grid_activity`)와 셋 다 반대다.**

    ① `마지막 수정` 을 **민다** (`〈339〉` 권고 · Ted 판정 대기 `〈341〉-⑦-⑷`). `〈60〉-①` 이 격자에서
       그 열을 안 건드린 이유는 「바뀐 것이 과학 데이터가 아니라 좌표를 읽을 수단」이어서였다 —
       본체는 **과학 데이터 자체**라 파생 관계를 다시 봐야 하고, 파생인 `계보 상태` 가 `확정` 에서
       `확인 필요` 로 접히는 것이 맞다. 사람이 확인하러 가면 실제로 바뀐 것이 있다.
    ② `crs/grid` 를 **건드리지 않는다** — `recompute_grid_metadata`(`_CLEAR_GRID_META`)는 사람이
       `updateDataset` 으로 적은 `crs`(`_UPDATABLE`)를 NULL 로 지운다. 본체가 바뀌었다고 사람이 적은
       좌표계가 틀려지는 것이 아니다 — 「모른다」와 「지웠다」는 다르다.
    ③ `d8_activity` 에 `본체 파일 변경` 한 행 — 격자 문자열과 갈라 둔다.
    `total_size_bytes` 는 여기서도 손대지 않는다 — `0009` 트리거가 `d3_file` 차분으로 옮긴다.
    """
    d3_catalog.touch_last_modified(db, dataset_id)
    d8_insight.record_activity(
        db, actor_id=subject.account_id, action=ACTION_BODY_CHANGED,
        target_kind="데이터셋", target_id=dataset_id)


@router.post("/datasets/{datasetId}/files", name="addDatasetFile", status_code=201)
def add_dataset_file(request: Request, datasetId: str,
                     file: UploadFile = File(...),
                     kind: str = Form(...),
                     relativePath: str | None = Form(default=None),
                     subject: Subject = Depends(current_subject),
                     db: Session = Depends(scoped_db)) -> dict:
    """후주입 — **본체는 여기서**, 기준 격자 파일은 `attachUploadGridFiles` 로.

    본체 후주입은 `〈59〉-③` 이 막았던 조작이고 `〈339〉-(라)` 가 번복했다 — 계약이 막지 않고
    사람이 판단한다. 격자 0건은 정상 상태다 (`P2.md §2-21`). 그릴 수 없는 것과 등록할 수 없는
    것은 다르다. 폴더 경로는 `relativePath` 로 받아 `d3_file.relative_path` 에 남긴다 (`〈339〉-(나)`).

    본체의 뒷정리는 교체·삭제와 **같은 규칙**(`_record_body_activity`)이다 — `마지막 수정` 이동 ·
    `crs/grid` 무변경 · `본체 파일 변경` 한 행. ⚠ 이 경로가 `_record_grid_activity` 를 불렀던 동안은
    본체를 하나 더할 때마다 사람이 적은 `crs` 가 지워지고 있었다(실측 — `〈339〉` 집행 전).
    """
    if not Ulid.is_valid(datasetId):
        raise errors.bad_request("datasetId 가 정규 ID 가 아니다.")
    dataset_id = Ulid(datasetId)
    _require_upload_edit(db, subject)
    if not d3_catalog.dataset_exists(db, dataset_id):
        raise errors.not_found()
    if kind not in FILE_KINDS:
        raise errors.bad_request(f"파일 종류가 2값 밖이다: {kind!r}")
    name = (file.filename or "").strip()
    if not name or len(name) > MAX_FILE_NAME:
        raise errors.bad_request("파일 이름은 1~255자다.")
    relative_path = _relative_path(relativePath)
    if kind == GRID:
        # 축을 모르는 채로는 `d3_file` 의 CHECK 를 통과하지 못한다 — 그리고 통과시키려고
        # 축을 지어내지 않는다 (`〈66〉`). 축 판별은 파일을 읽는 쪽의 일이다.
        # **격자의 자리는 `attachUploadGridFiles` 다** — 거절하면서 갈 곳을 말한다.
        #
        # ⚠ **거절이 저장 앞에 온다** (`CODE-REVIEW-20260903` 부록). 종전에는 `_store` 가
        # 이 검사 앞에 있어 거절한 격자 파일이 `uploads/{id}/grid/` 에 그대로 남았다.
        # 격자를 읽는 쪽(viz-render)에는 원장이 없어 **폴더가 곧 사실**이다 — 거절했다면서
        # 그 파일로 그리거나, 짝이 셋이 되어 멀쩡한 격자까지 통째로 거절된다.
        # 판정이 저장보다 **앞**이다 — 거절할 바이트를 디스크에 놓고 나서 거절하지 않는다.
        raise errors.bad_request(
            "기준 격자 파일의 축(위도·경도)은 서버가 파일에서 판별한다 — "
            "이 op 은 그 판별을 태우지 않는다. 격자는 업로드로 올려 판별을 마친 뒤 "
            "`/datasets/{datasetId}/grid-files` 로 반영한다.")

    file_id = Ulid.generate()
    key = storage_layout.storage_key(datasetId, file_id=str(file_id),
                                     kind=kind, file_name=name)
    file.file.seek(0)
    byte_size = _storage(request).put_stream(key=key, stream=file.file)
    row = d3_catalog.insert_file(db, file_id=str(file_id), dataset_id=dataset_id, kind=kind,
                                 file_name=name, size_bytes=byte_size, storage_key=key,
                                 carries_lat=False, carries_lon=False,
                                 relative_path=relative_path)
    # 여기 오는 것은 본체뿐이다 — 격자는 위에서 400 으로 갈 곳을 말하고 끝났다.
    _record_body_activity(db, subject=subject, dataset_id=dataset_id)
    return d3_catalog.file_ref(row)


_ALLOWED_ATTACH_FIELDS = {"uploadId"}


@router.post("/datasets/{datasetId}/grid-files", name="attachUploadGridFiles", status_code=201)
def attach_upload_grid_files(request: Request, datasetId: str, body: dict = Body(default=None),
                             subject: Subject = Depends(current_subject),
                             db: Session = Depends(scoped_db)) -> dict:
    """격자 후주입 **확정** — 판별이 끝난 업로드를 이 데이터셋에 반영한다.

    **사람에게 이 조작은 업로드다** (Ted 2026-08-25 판정 · 사용자 관점 우선). 그래서 새 개념을
    만들지 않고 기존 업로드 흐름을 그대로 쓴다 — `createUpload` 가 격자를 접수하고, 워커가
    축을 확정해 `d5_upload_file` 행을 세우고(`〈79〉-㈎`), 이 op 이 그 행을 `d3_file` 로 옮긴다.

    **짝(데이터셋 ↔ 업로드)을 저장하지 않는다** — 화면이 들고 있다가 이 요청에 동봉한다.
    `d5_upload` 는 `datasetId` 를 의도적으로 갖지 않는다(불변규칙 1). 등록 전환이 성립하는
    이유와 같은 이유로 이 op 도 성립한다: **`datasetId` 와 격자 파일이 한 트랜잭션 안에 있다.**

    안 하는 것
      · **축을 지어내지 않는다** — 원장에 축이 있는 행만 옮긴다 (`〈66〉`).
      · **저장 키를 승계하지 않는다** — 바이트는 데이터셋 자리로 온다(`_relocate`).
        등록 전환과 같은 규칙이고, 승계가 렌더 404 의 원인이었다.
      · **본체를 받지 않는다** — 본체가 든 묶음은 등록 전환의 대상이다. 본체 후주입의 자리는
        `addDatasetFile` 이다 (`〈339〉-(라)` 가 `〈59〉-③` 을 번복한 뒤에도 이 op 은 격자 전용이다).
      · **마이그레이션·이벤트 계약을 건드리지 않는다.**
    """
    if not Ulid.is_valid(datasetId):
        raise errors.bad_request("datasetId 가 정규 ID 가 아니다.")
    dataset_id = Ulid(datasetId)
    _require_upload_edit(db, subject)
    if not d3_catalog.dataset_exists(db, dataset_id):
        # 없는 데이터셋과 경계 밖을 **같은 404** 로 낸다.
        raise errors.not_found()

    if not isinstance(body, dict):
        raise errors.bad_request("요청 본문이 객체가 아니다.")
    unknown = set(body) - _ALLOWED_ATTACH_FIELDS
    if unknown:
        raise errors.bad_request(f"계약에 없는 필드다: {sorted(unknown)}")
    upload_ref = body.get("uploadId")
    if not Ulid.is_valid(upload_ref):
        raise errors.bad_request("uploadId 가 정규 ID 가 아니다.")
    upload_id = Ulid(upload_ref)

    ledger = _ledger(db)
    record = _live_upload(db, upload_id)
    if record is None:
        # 수명은 **일반 업로드와 같다** (`〈67〉-ⓐ` 규칙 ③) — 후주입 전용 수명을 만들지 않는다.
        raise errors.not_found("없거나 수명이 다한 업로드다.")
    if record.registered_at is not None:
        raise errors.conflict("이미 소비된 업로드다 — 같은 업로드를 두 번 반영하지 않는다.")

    files = ledger.files(upload_id)
    if any(f.kind == BODY for f in files):
        raise errors.bad_request(
            "본체 파일이 든 업로드다 — 본체가 든 묶음은 등록 전환의 대상이지 "
            "후주입의 대상이 아니다.")
    grids = [f for f in files if f.kind == GRID]
    if not grids:
        # 판별에 실패했거나 형상이 어긋난 격자는 **행 자체가 없다** (`〈66〉`).
        # 사유는 `getUploadStatus` 의 `gridRejections` 가 말한다 — 여기서 어휘를 새로 만들지 않는다.
        raise errors.bad_request(
            "축이 확정된 기준 격자 파일이 없다 — 판별 결과는 업로드 상태 조회의 "
            "`gridRejections` 가 말한다.")

    # `〈58〉` — 데이터셋당 기준 격자 파일 0~2 건이고 **축마다 하나**다. 집행 장치는
    # `0004` 의 축별 부분 유니크이고, 여기서는 그 위반을 **409 로 먼저** 말한다 —
    # IntegrityError 를 500 으로 흘리면 사람은 무엇이 겹쳤는지 못 읽는다.
    taken_lat = any(g.carries_lat for g in d3_catalog.grid_files(db, dataset_id))
    taken_lon = any(g.carries_lon for g in d3_catalog.grid_files(db, dataset_id))
    for g in grids:
        if (g.carries_lat and taken_lat) or (g.carries_lon and taken_lon):
            raise errors.conflict(
                "이미 그 축을 쓰는 기준 격자 파일이 있다 — 데이터셋당 축마다 한 건이다. "
                "바꾸려면 교체(`replaceDatasetGridFile`)를 쓴다.")
        taken_lat = taken_lat or g.carries_lat
        taken_lon = taken_lon or g.carries_lon

    # 원장 도장을 **먼저** 찍는다 — 등록 전환과 같은 도장이고 같은 행 잠금이다.
    # 두 요청이 동시에 오면 하나만 통과하고, 같은 업로드가 두 데이터셋에 반영되지 않는다.
    if not ledger.mark_registered(upload_id):
        raise errors.conflict("이미 소비된 업로드다.")

    out: list[dict[str, Any]] = []
    new_keys = _dataset_keys(datasetId, grids)
    for g in grids:
        # **`fileId` 동일성** — 업로드가 발급한 ULID 가 `d3_file.id` 로 그대로 간다 (`NB-A`).
        # **저장 키는 데이터셋의 자리다** — 등록 전환과 같은 규칙이고, 본체와 격자가 한
        # 디렉터리에 모여야 D7 이 짝을 본다(그쪽에는 원장이 없다).
        row = d3_catalog.insert_file(
            db, file_id=g.file_id, dataset_id=dataset_id, kind=g.kind,
            file_name=g.file_name, size_bytes=g.byte_size,
            storage_key=new_keys[g.file_id],
            carries_lat=g.carries_lat, carries_lon=g.carries_lon,
            relative_path=g.relative_path)
        out.append(d3_catalog.file_ref(row))

    # `〈60〉` — 계보를 접지 않고 이력에 남긴다. 좌표계·격자는 재계산한다.
    _record_grid_activity(db, subject=subject, dataset_id=dataset_id)
    _storage(request).relocate(files=grids, new_keys=new_keys)
    return {"items": out}


@router.put("/datasets/{datasetId}/files/{fileId}", name="replaceDatasetGridFile")
def replace_dataset_grid_file(request: Request, datasetId: str, fileId: str,
                              file: UploadFile | None = File(default=None),
                              flipAxes: bool | None = Form(default=None),
                              subject: Subject = Depends(current_subject),
                              db: Session = Depends(scoped_db)) -> dict:
    """교체는 **정상 동작**이다 (`〈59〉-①`) — **본체도, 격자도.**

    **⟨`〈339〉-(라)` · `〈59〉-③` 번복⟩** 「본체를 갈아 끼우는 것은 다른 데이터다」는 판단을 **사람이
    한다** — 계약이 막지 않는다(계약 산문 · `GridFileReplacement`). `operationId` 는 그대로다.
    본체 교체의 뒷정리는 격자와 반대다 — `_record_body_activity` 주석. `flipAxes` 만은 여전히
    **격자 사이의 조작**이라 본체에 요청하면 409 다(계약 409-②).

    **⟨동결 1회 해제 · `〈80〉-㉯ 3`(`K-3`)⟩ 축 뒤집기가 이 op 안에 든다.**
    뒤집기 = **같은 두 파일의 축 배정을 맞바꾸는 것**이고, 그것이 정확히 `〈59〉` 가 말한
    「잘못 붙인 격자를 바로잡는」 정상 동작이다. **파일을 다시 올리지 않는다.**
    새 op(`flipGridAxes`)을 만들지 않은 이유는 501 이 24 → 25 가 되고 **축을 바꾸는 길이 둘이 되어
    어느 것이 정본 경로인지 흐려지기** 때문이다.

    요청은 **택일**이다 — `file` 이거나 `flipAxes: true` 이거나. 둘 다이거나 둘 다 아니면 400.
    """
    row, dataset_id, file_ref = _file_target(db, subject, datasetId, fileId)
    if flipAxes is not None and file is not None:
        raise errors.bad_request(
            "`file` 과 `flipAxes` 는 택일이다 — 함께 보내면 어느 쪽을 했는지 응답이 말할 수 없다.")
    if flipAxes is not None:
        if not flipAxes:
            raise errors.bad_request("`flipAxes: false` 는 아무것도 요청하지 않는다.")
        if row.kind == BODY:
            # 본체에는 축이 없다(`0004` CHECK ㈏) — 뒤집을 배정 자체가 없다. 짝 수를 세기 전에 가른다.
            raise errors.conflict(
                "대상이 본체 파일이다 — `flipAxes` 는 기준 격자 파일 사이의 조작이고 본체에는 축이 없다.")
        return _flip_grid_axes(db, subject=subject, dataset_id=dataset_id, file_ref=file_ref)
    if file is None:
        raise errors.bad_request("`file` 이거나 `flipAxes: true` 여야 한다.")
    name = (file.filename or "").strip()
    if not name or len(name) > MAX_FILE_NAME:
        raise errors.bad_request("파일 이름은 1~255자다.")
    key = storage_layout.storage_key(datasetId, file_id=str(file_ref),
                                     kind=row.kind, file_name=name)
    file.file.seek(0)
    byte_size = _storage(request).put_stream(key=key, stream=file.file)
    # **옛 바이트를 남기지 않는다.**
    #   · 격자는 이름으로 자리가 정해지므로(`layout.json`) 이름이 바뀐 교체는 옛 파일을 그 자리에
    #     그대로 둔다 — 그러면 격자 폴더에 위도가 두 장 남고 짝짓기가 「짝이 아니다」로 죽는다.
    #     교체했는데 안 그려지는 실물이 이것이다.
    #   · 본체는 키가 `{datasetId}/{fileId}` 라 **키 불변**이다 — `put_stream` 이 그 자리에 덮어썼고
    #     `keep` 이 같은 키를 막아 이 줄은 아무것도 안 한다. 원장 키가 규약 밖인 행(시드·이관분)만
    #     옛 자리가 지워진다 — 그 바이트는 이제 아무도 가리키지 않는다.
    _storage(request).discard(key=row.storage_key, keep=key)
    updated = d3_catalog.replace_file(db, file_id=file_ref, file_name=name,
                                      size_bytes=byte_size, storage_key=key)
    if row.kind == BODY:
        d3_catalog.sync_bundle_file_name(db, dataset_id, was=row.file_name)
        _record_body_activity(db, subject=subject, dataset_id=dataset_id)
    else:
        _record_grid_activity(db, subject=subject, dataset_id=dataset_id)
    return d3_catalog.file_ref(updated)


@router.delete("/datasets/{datasetId}/files/{fileId}", name="deleteDatasetGridFile",
               status_code=204)
def delete_dataset_grid_file(request: Request, datasetId: str, fileId: str,
                             subject: Subject = Depends(current_subject),
                             db: Session = Depends(scoped_db)) -> Response:
    """삭제도 정상 동작이다 — **본체도.** 남는 불변식은 **본체 ≥ 1** 하나다 (`DataModel §4.3` ·
    `〈339〉-(라)` — `〈59〉-③` 의 「본체는 409」 번복). 그래서 409 의 뜻이 「본체다」에서
    「**마지막** 본체다」로 바뀌었다. 격자는 0건이 정상이라 그 409 가 없다.

    대표 조각(`d3_dataset.representative_file_id`)은 **FK `ON DELETE SET NULL`** 이 되돌린다
    (`schema.sql` `d3_dataset_representative_file_fk`). 그 열의 `NULL` 은 「없음」이 아니라 **「자동」**
    (파일명 자연 정렬의 첫 조각을 그때그때 고른다 — 열 주석 · 결정 2-4·2-8)이고, 값이 있으면 **사람이
    지정한 것**이다. 그래서 앱 코드가 남은 본체를 골라 써 넣지 않는다 — 써 넣으면 「사람이
    지정했다」는 없는 사실이 된다. 「남은 본체 중 가장 오래된 것으로 갱신」하는 규칙은 그 이유로
    기각했다 (`〈339〉` 집행 보고 · Ted 판정 대기).
    `bundle_file_name` 은 FK 가 없어 `sync_bundle_file_name` 이 따라간다 (`[정본 무근거]`).
    """
    row, dataset_id, file_ref = _file_target(db, subject, datasetId, fileId)
    if row.kind == BODY:
        # 세고 나서 지운다 — 그래서 **데이터셋 행을 먼저 잠근다.** 잠그지 않으면 마지막 둘을 동시에
        # 지우는 두 요청이 각자 「2건」을 보고 둘 다 통과해 본체 0건이 된다. 에러 없이 깨지는 불변식이다.
        if not d3_catalog.lock_dataset(db, dataset_id):
            raise errors.not_found()      # 관문 뒤에 묘비가 됐다 — 없는 것으로 답한다
        if d3_catalog.body_file_count(db, dataset_id) <= 1:
            raise errors.conflict(
                "마지막 본체 파일은 지울 수 없다 — 본체 없는 데이터셋은 데이터가 아니라 좌표다"
                "(본체 ≥ 1). 데이터를 없애려면 파일이 아니라 데이터셋을 지운다.")
    d3_catalog.delete_file(db, file_ref)
    _storage(request).discard(key=row.storage_key)
    if row.kind == BODY:
        d3_catalog.sync_bundle_file_name(db, dataset_id, was=row.file_name)
        _record_body_activity(db, subject=subject, dataset_id=dataset_id)
    else:
        _record_grid_activity(db, subject=subject, dataset_id=dataset_id)
    return Response(status_code=204)


def _flip_grid_axes(db: Session, *, subject: Subject, dataset_id: Ulid, file_ref: Ulid) -> dict:
    """`K-3` — 두 격자 파일의 축 배정을 맞바꾼다. **짝이 없으면 409.**

    「격자가 2건이 아니면 바꿀 배정이 없다」가 409 의 뜻이다. 결합축 1건(위도·경도가 한 파일)을
    뒤집는 것은 **같은 것**이라 조작 자체가 성립하지 않는다.
    """
    grids = d3_catalog.grid_files(db, dataset_id)
    if len(grids) != 2:
        raise errors.conflict(
            f"기준 격자 파일이 {len(grids)}건이라 축을 맞바꿀 짝이 없다 — 뒤집기는 두 파일 사이의 조작이다.")
    d3_catalog.swap_grid_axes(db, dataset_id)
    _record_grid_activity(db, subject=subject, dataset_id=dataset_id)
    updated = next(g for g in d3_catalog.grid_files(db, dataset_id) if g.file_id == str(file_ref))
    return d3_catalog.file_ref(updated)


def _file_target(db: Session, subject: Subject, datasetId: str, fileId: str):
    """교체·삭제가 공유하는 관문 — 400 · 403 · 404 를 한 자리에서 가른다.

    ⟨`〈339〉-(라)`⟩ 예전 이름은 `_grid_target` 이었고 여기서 본체를 409 로 막았다(`〈59〉-③`).
    번복으로 본체도 대상이다 — 종류별 검사(`flipAxes` 는 격자만 · 마지막 본체는 못 지운다)는
    **각 op 안에** 있다. 없는 파일과 경계 밖은 **같은 404** 다 (P-9·P-10).
    """
    if not Ulid.is_valid(datasetId) or not Ulid.is_valid(fileId):
        raise errors.bad_request("정규 ID 가 아니다.")
    dataset_id, file_id = Ulid(datasetId), Ulid(fileId)
    _require_upload_edit(db, subject)
    if not d3_catalog.dataset_exists(db, dataset_id):
        raise errors.not_found()
    row = d3_catalog.find_file(db, dataset_id=dataset_id, file_id=file_id)
    if row is None:
        raise errors.not_found()
    return row, dataset_id, file_id
