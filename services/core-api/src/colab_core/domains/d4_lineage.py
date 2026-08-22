"""D4 Lineage — 관계(부모 여럿) · 확인 기록. **사람이 확인한 것만 저장된다.**

D10 이 이 도메인에 쓰는 경로는 존재하지 않는다 (CLAUDE.md §3-2). 여기에도 만들지 않는다.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid
from ..ports.lineage import LineageSummary

# 주입력 부모의 최대 Lv 를 재귀로 센다 — Lv 는 컬럼이 아니라 계산이다 (PLAN-SoT §9-⑳).
# 보조입력은 Lv 계산에서 빠진다 (common.json#/$defs/ParentRole).
_SUMMARY = text("""
    WITH RECURSIVE depth(dataset_id, level) AS (
        SELECT d.id, 0
          FROM d3_dataset d
         WHERE NOT EXISTS (
             SELECT 1 FROM d4_lineage_edge e
              WHERE e.child_dataset_id = d.id AND e.parent_role = '주입력'
         )
        UNION ALL
        SELECT e.child_dataset_id, p.level + 1
          FROM d4_lineage_edge e
          JOIN depth p ON p.dataset_id = e.parent_dataset_id
         WHERE e.parent_role = '주입력'
    )
    SELECT t.dataset_id,
           (SELECT count(*) FROM d4_lineage_edge e WHERE e.child_dataset_id = t.dataset_id)
               AS parent_count,
           (SELECT max(d.level) FROM depth d
             JOIN d4_lineage_edge e ON e.parent_dataset_id = d.dataset_id
            WHERE e.child_dataset_id = t.dataset_id AND e.parent_role = '주입력')
               AS max_primary_parent_level,
           EXISTS (SELECT 1 FROM d4_lineage_unknown u WHERE u.dataset_id = t.dataset_id)
               AS marked_unknown
      FROM unnest(CAST(:ids AS char(26)[])) AS t(dataset_id)
""")


class LineageSummaryAdapter:
    """`ports.LineageSummaryPort` 의 D4 쪽 구현 — **읽기 전용**이다."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def summaries(self, dataset_ids: list[Ulid]) -> dict[str, LineageSummary]:
        if not dataset_ids:
            return {}
        rows = self._session.execute(_SUMMARY, {"ids": [str(i) for i in dataset_ids]}).mappings()
        return {
            r["dataset_id"]: LineageSummary(
                parent_count=int(r["parent_count"]),
                max_primary_parent_level=(
                    None if r["max_primary_parent_level"] is None
                    else int(r["max_primary_parent_level"])
                ),
                marked_unknown=bool(r["marked_unknown"]),
            )
            for r in rows
        }
