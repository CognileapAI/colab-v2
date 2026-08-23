"""D6 Project — 프로젝트 · 데이터셋 N:N 연결."""
from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid
from ..ports.project_link import DatasetProjects, ProjectUse

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


# 상세의 활용 프로젝트 — **여러 건 전부**를 나열한다 (Policy_데이터셋_상세 §5·§8).
# 의미 문장(`usage_note`)은 연결마다 따로다. 같은 데이터라도 과제마다 쓰임이 다르다.
_USES = text("""
    SELECT p.id AS project_id, p.name, p.type, p.period_start, p.period_end,
           pd.usage_note, pd.created_at
      FROM d6_project_dataset pd
      JOIN d6_project p ON p.id = pd.project_id
     WHERE pd.dataset_id = :dataset_id
     ORDER BY pd.created_at, p.id
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


# 등록 폼이 **한 번에** 제출하므로 등록 뒤 `linkProjectDataset` N 회가 아니라 여기서 붙인다
# (`DatasetCreate.projectIds` 산문). `usageNote` 는 이 자리에 없다 — 업로드 화면이 그 문장을
# 받는 자리가 정본 폼에 없어(`D2c` C1 Q2) 등록 후 `linkProjectDataset` 이 적는다(P5).
# `dataset_id` 는 bare 컬럼이라 없는 데이터셋도 DB 는 받는다 — **존재 확인은 부르는 쪽이**
# 하고, 없으면 400 이다. 그 확인이 없으면 유령 연결이 조용히 쌓인다.
_LINK = text("""
    INSERT INTO d6_project_dataset (id, lab_id, project_id, dataset_id)
    VALUES (:id, current_lab_id(), :project_id, :dataset_id)
    ON CONFLICT (project_id, dataset_id) DO NOTHING
""")

_PROJECT_EXISTS = text("SELECT 1 FROM d6_project WHERE id = :project_id")


def project_exists(session: Session, project_id: Ulid) -> bool:
    """경계 밖이면 RLS 가 행을 지우므로 False 다 — 남의 연구실 프로젝트에 붙지 않는다."""
    return session.execute(_PROJECT_EXISTS, {"project_id": str(project_id)}).first() is not None


def link_dataset(session: Session, *, project_id: Ulid, dataset_id: Ulid) -> None:
    session.execute(_LINK, {
        "id": str(Ulid.generate()), "project_id": str(project_id),
        "dataset_id": str(dataset_id),
    })


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

    def uses_of(self, dataset_id: Ulid) -> list[ProjectUse]:
        rows = self._session.execute(_USES, {"dataset_id": str(dataset_id)}).mappings().all()
        return [
            ProjectUse(
                project_id=r["project_id"], name=r["name"], type=r["type"],
                period_start=r["period_start"], period_end=r["period_end"],
                usage_note=r["usage_note"],
            )
            for r in rows
        ]
