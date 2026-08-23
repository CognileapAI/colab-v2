"""D2 가 내주는 접근 상태 · Verified 읽기 Port."""
from __future__ import annotations

import dataclasses
from typing import Protocol

from ..kernel.ids import Ulid


@dataclasses.dataclass(frozen=True)
class DatasetAccess:
    access_state: str          # '열림' | '잠김'
    verified: bool
    body_accessible: bool      # 본체(파일)에 닿을 수 있는가 (P-13·P-34)


@dataclasses.dataclass(frozen=True)
class DatasetVerification:
    """Verified 기록 (`DataModel §4.1`) — 승인자·승인 시각·취소자·취소 시각·사유.

    배지는 **표시 전용**이다. 이 Port 는 상태를 말할 뿐 누를 자리를 만들지 않는다.
    """

    verified: bool
    approver_id: str | None
    approver_name: str | None
    approved_at: object
    cancelled_by_id: str | None
    cancelled_by_name: str | None
    cancelled_at: object
    cancellation_reason: str | None


@dataclasses.dataclass(frozen=True)
class MemberPermissions:
    """구성원 한 명의 역할 + 스위치 4종. 격자 표 한 행의 D2 쪽 사실이다."""

    role: str | None
    switches: dict[str, bool]


class DatasetAccessPort(Protocol):
    def dataset_access(self, dataset_ids: list[Ulid]) -> dict[str, DatasetAccess]: ...

    def verification(self, dataset_ids: list[Ulid]) -> dict[str, DatasetVerification]: ...
