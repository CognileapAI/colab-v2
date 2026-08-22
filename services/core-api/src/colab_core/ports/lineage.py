"""D4 가 내주는 읽기 전용 계보 요약 (DATAMODEL-BASELINE §계보 상태 소유 — '권고: Port 하나 추가')."""
from __future__ import annotations

import dataclasses
from typing import Protocol

from ..kernel.ids import Ulid


@dataclasses.dataclass(frozen=True)
class LineageSummary:
    """계보 상태·가공 단계 Lv 를 **계산하는 데 필요한 사실만** 담는다. 값 자체는 D3 이 계산한다."""

    parent_count: int
    max_primary_parent_level: int | None
    marked_unknown: bool


class LineageSummaryPort(Protocol):
    def summaries(self, dataset_ids: list[Ulid]) -> dict[str, LineageSummary]: ...
