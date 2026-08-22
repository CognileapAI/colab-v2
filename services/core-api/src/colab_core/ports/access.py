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


class DatasetAccessPort(Protocol):
    def dataset_access(self, dataset_ids: list[Ulid]) -> dict[str, DatasetAccess]: ...
