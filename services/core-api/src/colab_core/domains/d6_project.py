"""D6 Project — 프로젝트 · 데이터셋 N:N 연결."""
from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid
from ..ports.project_link import DatasetProjects

_INSERT = text("""
    INSERT INTO d6_project (id, lab_id, type, name, description,
                            period_start, period_end, link_url, status)
    VALUES (:id, current_lab_id(), :type, :name, :description,
            :period_start, :period_end, :link_url, '진행 중')
    RETURNING id, type, name, status, description, period_start, period_end, link_url
""")

_LINKS = text("""
    SELECT pd.dataset_id, p.id AS project_id, p.name, pd.created_at
      FROM d6_project_dataset pd
      JOIN d6_project p ON p.id = pd.project_id
     WHERE pd.dataset_id = ANY(CAST(:ids AS char(26)[]))
     ORDER BY pd.dataset_id, pd.created_at, p.id
""")


def create_project(session: Session, *, type_: str, name: str, description: str | None,
                   period_start: date | None, period_end: date | None,
                   link_url: str | None) -> dict:
    """`lab_id` 를 요청에서 받지 않는다 — `current_lab_id()` 가 넣는다.

    경계 밖 lab_id 로 쓰려는 시도는 RLS 의 WITH CHECK 에서 거부된다.
    """
    new_id = Ulid.generate()
    row = session.execute(_INSERT, {
        "id": str(new_id), "type": type_, "name": name, "description": description,
        "period_start": period_start, "period_end": period_end, "link_url": link_url,
    }).mappings().one()
    return dict(row)


class ProjectLinkAdapter:
    """`ports.ProjectLinkPort` 의 D6 쪽 구현."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def projects_of(self, dataset_ids: list[Ulid]) -> dict[str, DatasetProjects]:
        if not dataset_ids:
            return {}
        grouped: dict[str, list[dict]] = {}
        for r in self._session.execute(_LINKS, {"ids": [str(i) for i in dataset_ids]}).mappings():
            grouped.setdefault(r["dataset_id"], []).append(dict(r))
        out: dict[str, DatasetProjects] = {}
        for ds_id, rows in grouped.items():
            first = rows[0]
            out[ds_id] = DatasetProjects(
                representative_id=first["project_id"],
                representative_name=first["name"],
                more_count=len(rows) - 1,
                names=[r["name"] for r in rows],
            )
        return out
