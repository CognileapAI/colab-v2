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


class UploadLedgerReadPort(Protocol):
    def find(self, upload_id: Ulid) -> UploadRecord | None: ...

    def files(self, upload_id: Ulid) -> list[UploadFileRecord]: ...


class UploadLedgerWritePort(Protocol):
    def accept(self, *, upload_id: Ulid, uploader_account_id: Ulid,
               expires_at: dt.datetime, files: list[UploadFileRecord]) -> None: ...

    def publish_accepted(self, *, upload_id: Ulid, actor_account_id: Ulid,
                         files: list[UploadFileRecord]) -> bool: ...

    def mark_registered(self, upload_id: Ulid) -> bool: ...

    def reap_expired(self, now: dt.datetime | None = None) -> list[str]: ...
