"""D4 가 내주는 읽기 전용 계보 요약 (DATAMODEL-BASELINE §계보 상태 소유 — '권고: Port 하나 추가')."""
from __future__ import annotations

import dataclasses
from typing import Protocol

from ..kernel.ids import Ulid

#: 가공 단계 Lv 의 상한. **정본이 준 값이지 고른 값이 아니다** —
#: `VAL-005`(가공 단계 = `Lv0 · Lv1 · Lv2`, 상한 Lv2) · `POL-020`(「연결된 가공 전
#: 데이터 중 가장 높은 Lv + 1, **상한 Lv2**」) · 용어 정의(「Lv0 원자료 · Lv1 1차 가공 ·
#: Lv2 집계·분석용. 상한 Lv2」). 재검토 판정 = 「Lv3 은 존재할 수 없는 값이다」.
#:
#: **Lv 은 깊이가 아니라 종류다.** 5홉 떨어진 데이터도 여전히 「집계·분석용」이므로
#: Lv2 로 접어도 잃는 것이 없다 — 깊이는 계보 그래프에 그대로 남는다.
#:
#: D3(값 계산)과 D4(재귀 상한)가 **같은 값을 봐야 하므로** 두 도메인이 공유하는
#: 이 Port 에 둔다. 두 자리에 따로 적으면 갈라진다.
LV_CAP = 2


@dataclasses.dataclass(frozen=True)
class LineageSummary:
    """계보 상태·가공 단계 Lv 를 **계산하는 데 필요한 사실만** 담는다. 값 자체는 D3 이 계산한다."""

    parent_count: int
    max_primary_parent_level: int | None
    marked_unknown: bool


class LineageSummaryPort(Protocol):
    def summaries(self, dataset_ids: list[Ulid]) -> dict[str, LineageSummary]: ...
