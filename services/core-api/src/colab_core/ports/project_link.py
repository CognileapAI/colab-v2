"""D6 이 내주는 데이터셋↔프로젝트 연결 읽기 Port."""
from __future__ import annotations

import dataclasses
from typing import Protocol

from ..kernel.ids import Ulid


@dataclasses.dataclass(frozen=True)
class DatasetProjects:
    """대표 1건 + `외 N` (Policy_데이터_찾기 §5 프로젝트 열). 대표는 가장 먼저 연결된 것이다."""

    representative_id: str | None
    representative_name: str | None
    more_count: int
    names: list[str]


class ProjectLinkPort(Protocol):
    def projects_of(self, dataset_ids: list[Ulid]) -> dict[str, DatasetProjects]: ...
