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


@dataclasses.dataclass(frozen=True)
class ProjectUse:
    """상세의 활용 프로젝트 한 건. **의미 문장은 연결마다 따로다** (Policy_데이터셋_상세 §5).

    카탈로그의 `대표 1건 + 외 N` 과 달리 상세는 **여러 건 전부**를 나열하므로 형태가 다르다.
    """

    project_id: str
    name: str
    type: str
    period_start: object
    period_end: object
    usage_note: str | None


class ProjectLinkPort(Protocol):
    def projects_of(self, dataset_ids: list[Ulid]) -> dict[str, DatasetProjects]: ...

    def uses_of(self, dataset_id: Ulid) -> list[ProjectUse]: ...
