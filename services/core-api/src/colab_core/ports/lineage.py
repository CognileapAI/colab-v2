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
#:
#: ⭑ **⟨개정 2026-09-07 · `WU-B5` · PRD-07·미결-7 ⓐ⟩ 값이 `2` → `3` 이다.**
#: ／ 종전 ~~`LV_CAP = 2`~~ — **위 원문은 지우지 않는다.** 그 다섯 줄은 rev1 정본
#: (`VAL-005`·`POL-020`·재검토 「Lv3 은 존재할 수 없는 값이다」)의 인용이고, 그 정본이
#: 2026-09-05 판정으로 **4단(`Lv0`~`Lv3`)** 이 됐다(미결-7 ⓐ · 마이그레이션 `0015` 의
#: `processing_level_user_set` CHECK 4값 · 계약 `_PROCESSING_LEVELS` 4값).
#: 상한이 `2` 로 남으면 두 자리가 깨진다 — ⑴ 파생 계산이 `Lv3` 을 만들 수 없어
#: 사람 값 `Lv3` 이 **언제나 불일치**로 읽히고 ⑵ `routes/catalog.py` 의 필터 검증이
#: 사람이 고른 `Lv3` 을 **400** 으로 되돌려 그 값으로 거를 방법이 없다.
#: ⚠ **접는 성질은 그대로다** — 상한을 넘는 깊은 사슬은 여전히 합법이고 값만 접힌다.
LV_CAP = 3


@dataclasses.dataclass(frozen=True)
class LineageSummary:
    """계보 상태·가공 단계 Lv 를 **계산하는 데 필요한 사실만** 담는다. 값 자체는 D3 이 계산한다."""

    parent_count: int
    max_primary_parent_level: int | None
    marked_unknown: bool


class LineageSummaryPort(Protocol):
    def summaries(self, dataset_ids: list[Ulid]) -> dict[str, LineageSummary]: ...
