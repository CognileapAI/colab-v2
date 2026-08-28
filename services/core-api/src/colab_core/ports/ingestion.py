"""D5 업로드 원장 — **읽기 Port + 쓰기 Port** (`PLAN-SoT §9 〈63〉-㉱`).

왜 Port 인가
  `createUpload`·`getUploadStatus` 는 core-api 오퍼레이션인데 업로드 상태는 **D5 소유**다.
  불변규칙 1(`CLAUDE.md §3-1`) 때문에 core-api 의 조립 루트·D3·D4 는 `d5_*` 를 직접 만지지
  않는다. 이 파일이 그 표면이고, 유일한 구현은 `domains/d5_ingestion.py` 다.

왜 쓰기까지인가
  `createUpload` 는 **행 삽입도 outbox 기입도** 한다. 읽기만 세우면 반쪽 판정이 된다 —
  `〈63〉-㉱` 가 그 이유로 두 Port 를 함께 못 박았다.

패턴은 `ports/lineage.py` 를 승계한다 — dataclass 사실 + Protocol.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
from typing import Protocol

from ..kernel.ids import Ulid


@dataclasses.dataclass(frozen=True)
class UploadFileRecord:
    """업로드 안의 파일 하나. 계약 `UploadFileRef` 의 네 값 + 원장이 아는 사실.

    `file_id` 는 **등록 전환 뒤 `d3_file.id` 로 그대로 간다** (`NB-A` 동일성).
    변환 지점이 없다는 것이 그 승인의 코드 쪽 표현이다.
    """

    file_id: str
    file_name: str
    kind: str
    byte_size: int | None
    storage_key: str
    carries_lat: bool
    carries_lon: bool
    #: 매직바이트로 판정한 포맷. **core-api 는 절대 채우지 않는다** — 확장자를 믿지 않는다
    #: (`P2.md §2-10` · `DR-3`). 파이프라인이 `file.format-detected` 로 채운다.
    detected_format: str | None
    #: 폴더째 업로드에서 온 `폴더/이름` 상대 경로 (0008 · `〈173〉`). 낱개 파일은 None.
    relative_path: str | None = None


@dataclasses.dataclass(frozen=True)
class TransferFileRecord:
    """프리사인드 전송 중인 파일 하나 (`d5_upload_transfer_file` · `〈174〉`).

    `file_id` 는 전송 완결 시 `d5_upload_file.id`(본체) 혹은 워커가 세울 격자 행의
    id 로 **그대로** 간다 — `NB-A` 동일성이 전송 단계까지 소급된 형태다.
    파트 번호·크기는 여기 없다 — **파트의 정본은 S3 ListParts 다.**
    """

    file_id: str
    file_name: str
    kind: str
    byte_size: int
    storage_key: str
    relative_path: str | None
    part_size: int | None          #: None = 단일 PUT
    transfer_ref: str | None       #: S3 멀티파트 UploadId (단일 PUT 은 None)
    outcome: str                   #: 대기 | 올라감 | 실패 — 서버 실측 결과만


@dataclasses.dataclass(frozen=True)
class TransferRecord:
    """전송 1건 (`d5_upload_transfer`). 완결되면 같은 ULID 로 `d5_upload` 가 선다."""

    transfer_id: str
    uploader_account_id: str
    source_label: str
    created_at: dt.datetime
    expires_at: dt.datetime
    completed_at: dt.datetime | None


@dataclasses.dataclass(frozen=True)
class UploadRecord:
    """업로드 1건. 이벤트 ②~⑦ 의 **결과**만 담는다 — 새 사실을 만들지 않는다."""

    upload_id: str
    uploader_account_id: str
    created_at: dt.datetime
    expires_at: dt.datetime
    ready: bool
    renderable: bool | None
    metadata_complete: bool | None
    failure_reason: str | None
    registered_at: dt.datetime | None
    #: 파이프라인이 아직 일하는 중인가. **시계가 처리를 앞지르지 않는다** — 만료 판정과
    #: reaper 가 둘 다 이 값을 본다 (`NB-2` 개정 규칙 ②).
    processing: bool


@dataclasses.dataclass(frozen=True)
class HeldAutoMetadata:
    """**아직 장부에 반영되지 않은 채 보류된 사건들**이 나르는 자동 정보.

    왜 「보류」인가 — 사건은 **등록 전**에 난다(`upload.ready` 축자 「저장된 것은 아무것도
    없다」 · `datasetId` 가 없다). 그런데 값이 사는 장부 행 `d3_dataset_autometa` 는
    **등록 전환 시점**에 생긴다. 그래서 소비자는 **대상 행이 아직 없는 사건**을 반드시 만난다.

    **보류된 사건이 어디 사는가 = `d5_pipeline_event` 행 그 자체다.**
    따로 큐를 만들지 않는다. 메모리에 들고 있으면 재기동에서 사라지고, 사라진 사실은
    「값이 원래 없었다」와 구분되지 않는다 — 그것이 지금 상태의 재현이다. 사건 행은
    이미 내구 저장이고(원장 표 · 업로드와 함께 `ON DELETE CASCADE`), 멱등 키가
    `<타입>:<uploadId>` 라 **타입당 한 건**이다. 그래서 「보류 목록」은 **질의**이지
    자료구조가 아니다 — 두 벌이 될 수 없다.

    반영 시점 = **등록 전환 트랜잭션**. 같은 트랜잭션이라 반쪽이 남지 않는다.
    """

    format: str | None
    variables: list[str] | None
    period_start: str | None
    period_end: str | None
    crs: str | None
    grid: str | None
    byte_size_total: int | None
    #: 읽은 사건의 종류들. **건수가 아니라 목록이다** — 유실 감지가 「무엇이 안 왔나」를
    #: 말할 수 있어야 하고, 0 건과 「읽었는데 값이 비었다」는 다른 사실이다.
    event_types: tuple[str, ...] = ()

    @property
    def carries_any_value(self) -> bool:
        return any(v not in (None, [], "") for v in (
            self.format, self.variables, self.period_start, self.period_end,
            self.crs, self.grid, self.byte_size_total))


class UploadLedgerReadPort(Protocol):
    def find(self, upload_id: Ulid) -> UploadRecord | None: ...

    def files(self, upload_id: Ulid) -> list[UploadFileRecord]: ...

    def held_auto_metadata(self, upload_id: Ulid) -> HeldAutoMetadata: ...


class UploadLedgerWritePort(Protocol):
    def accept(self, *, upload_id: Ulid, uploader_account_id: Ulid,
               expires_at: dt.datetime, files: list[UploadFileRecord]) -> None: ...

    def publish_accepted(self, *, upload_id: Ulid, actor_account_id: Ulid,
                         files: list[UploadFileRecord]) -> bool: ...

    def mark_registered(self, upload_id: Ulid) -> bool: ...

    def reap_expired(self, now: dt.datetime | None = None) -> list[str]: ...
