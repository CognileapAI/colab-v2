"""D6 Project — 프로젝트 · 데이터셋 N:N 연결."""
from __future__ import annotations

import dataclasses
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


#: 프로젝트 이름은 **연구실 단위 유니크**다 (결정 2-6 · `VAL-010` · `TC-E-004`).
#: 근거 — 결정 #11 로 빠른 생성이 전원에게 열렸으므로, **이름 중복 차단이 이름만 받는
#: 생성 경로의 유일한 방어선**이다. 데이터셋 이름은 중복 허용이라(2-1) 규칙이 갈리는데
#: **의도된 차이**다: 프로젝트는 여러 사람이 공유하는 묶음이라 이름이 식별자 역할을 하고,
#: 데이터셋은 개별 파일이라 업로더·파일명으로 구분된다.
#:
#: ⚠ **DB 유니크 제약이 아직 없다** — 넣으려면 마이그레이션이고 기존 행에 중복이 있으면
#: 실패한다. 지금은 응용 층이 지키고, **경계는 RLS 가 이미 걸어** 남의 연구실 이름은 안 보인다.
_NAME_TAKEN = text("""
    SELECT 1 FROM d6_project
     WHERE btrim(lower(name)) = btrim(lower(:name))
       AND (CAST(:exclude_id AS char(26)) IS NULL OR id <> CAST(:exclude_id AS char(26)))
     LIMIT 1
""")


class ProjectNameTaken(Exception):
    """같은 이름의 프로젝트가 이미 있다. 호출자가 409 로 바꾼다."""


def name_is_taken(session: Session, *, name: str, exclude_id: str | None = None) -> bool:
    """**대소문자·앞뒤 공백을 무시하고 본다.**

    `ERA5` 와 `era5 ` 를 다른 이름으로 두면 유니크가 이름값만 하고 실제로는 갈린다 —
    결정 2-10 이 원천 표기에서 든 근거와 같다.

    `exclude_id` = **자기 자신은 중복이 아니다.** 없으면 설명만 고치려는 사람이
    「이미 있어요」에 막힌다.
    """
    return session.execute(_NAME_TAKEN, {
        "name": name, "exclude_id": exclude_id}).first() is not None


#: 이 op 이 고칠 수 있는 칸 ↔ 열. **`type` 은 없다** — 「만든 뒤에는 바꾸지 않는다」
#: (`ProjectUpdate` 산문). `status` 도 없다 — 그쪽은 `setProjectStatus` 의 일이다.
_PROJECT_UPDATABLE = {
    "name": "name", "description": "description", "link": "link_url",
}


def update_project(session: Session, *, project_id: Ulid, changes: dict) -> None:
    """프로젝트 정보 부분 수정 (`〈150〉`). 보내지 않은 열쇠는 안 건드린다."""
    columns: dict[str, object] = {}
    for key, value in changes.items():
        if key in _PROJECT_UPDATABLE:
            columns[_PROJECT_UPDATABLE[key]] = value
    if "period" in changes:
        period = changes["period"]
        columns["period_start"] = None if period is None else period.get("start")
        columns["period_end"] = None if period is None else period.get("end")
    if not columns:
        return
    assignments = ", ".join(f"{c} = :{c}" for c in columns)
    session.execute(
        text(f"UPDATE d6_project SET {assignments} WHERE id = :project_id"),
        {**columns, "project_id": str(project_id)})


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


# ════════════════════════════════════════════════════════════════════════════
# S-02 목록 · S-02b 상세 · 연결 쓰기 (WU-P5)
#
# **여기 있는 질의는 전부 `d6_*` 뿐이다.** 데이터셋의 이름·조각 수·계보·접근 상태는
# D3·D4·D2 의 사실이라 이 파일이 읽지 않는다 — 조립은 `app/routes/project.py` 가 한다
# (`CLAUDE.md §3-1` · `ports/__init__.py` 머리말).
# ════════════════════════════════════════════════════════════════════════════

# 연구실 경계는 RLS 가 이미 걸었다 — 여기에 lab_id 조건을 다시 적지 않는다 (P-9·P-10).
_LIST = text("""
    SELECT p.id, p.type, p.name, p.description, p.status,
           p.period_start, p.period_end, p.link_url
      FROM d6_project p
     ORDER BY p.period_start DESC NULLS LAST, p.id
""")

_FIND = text("""
    SELECT p.id, p.type, p.name, p.description, p.status,
           p.period_start, p.period_end, p.link_url
      FROM d6_project p
     WHERE p.id = :project_id
""")

#: 한 프로젝트의 소속 데이터셋 **전부**. 자르지 않는다 (`Policy_프로젝트 §5` 표 범위).
#: 여기서 나오는 것은 **식별자와 의미 문장뿐**이다 — 나머지 열은 D3·D2·D4 가 말한다.
_DATASETS_OF = text("""
    SELECT pd.dataset_id, pd.usage_note
      FROM d6_project_dataset pd
     WHERE pd.project_id = :project_id
     ORDER BY pd.created_at, pd.dataset_id
""")

#: 목록 카드의 지표 타일이 쓰는 것 — 어느 프로젝트에 어느 데이터셋이 붙었는가.
#: **건수를 세어 내리지 않는다.** 승인·기록 없음은 D2·D4 의 사실이라 D6 이 셀 수 없고,
#: 데이터셋 수만 여기서 세면 세 칸이 서로 다른 곳에서 와 갈라진다.
_LINKS_ALL = text("""
    SELECT pd.project_id, pd.dataset_id
      FROM d6_project_dataset pd
""")

#: 멱등 PUT — 이미 있는 연결이면 의미 문장을 고친다 (계약 `linkProjectDataset` 산문).
#: `link_dataset`(등록 폼 경로)과 나눠 둔 이유는 그쪽이 `usage_note` 를 **적지 않기** 때문이다.
#: 한 문장으로 합치면 등록이 기존에 적어 둔 문장을 null 로 덮어쓴다.
_UPSERT_LINK = text("""
    INSERT INTO d6_project_dataset (id, lab_id, project_id, dataset_id, usage_note)
    VALUES (:id, current_lab_id(), :project_id, :dataset_id, :usage_note)
    ON CONFLICT (project_id, dataset_id) DO UPDATE SET usage_note = EXCLUDED.usage_note
""")


@dataclasses.dataclass(frozen=True)
class ProjectRecord:
    """프로젝트 한 건의 **D6 쪽 사실 전부**. 데이터셋 관련 값은 하나도 들어 있지 않다."""

    project_id: str
    type: str
    name: str
    description: str | None
    status: str
    period_start: object
    period_end: object
    link_url: str | None


def _record(r) -> ProjectRecord:
    return ProjectRecord(
        project_id=r["id"], type=r["type"], name=r["name"], description=r["description"],
        status=r["status"], period_start=r["period_start"], period_end=r["period_end"],
        link_url=r["link_url"],
    )


def list_projects(session: Session) -> list[ProjectRecord]:
    return [_record(r) for r in session.execute(_LIST).mappings()]


def find_project(session: Session, project_id: Ulid) -> ProjectRecord | None:
    """경계 밖이면 RLS 가 행을 지우므로 None 이고, 호출자는 404 를 낸다 (P-9·P-10)."""
    r = session.execute(_FIND, {"project_id": str(project_id)}).mappings().first()
    return None if r is None else _record(r)


def datasets_of(session: Session, project_id: Ulid) -> list[tuple[str, str | None]]:
    rows = session.execute(_DATASETS_OF, {"project_id": str(project_id)}).mappings()
    return [(r["dataset_id"], r["usage_note"]) for r in rows]


def dataset_ids_by_project(session: Session) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for r in session.execute(_LINKS_ALL).mappings():
        out.setdefault(r["project_id"], []).append(r["dataset_id"])
    return out


def upsert_link(session: Session, *, project_id: Ulid, dataset_id: Ulid,
                usage_note: str | None) -> None:
    session.execute(_UPSERT_LINK, {
        "id": str(Ulid.generate()), "project_id": str(project_id),
        "dataset_id": str(dataset_id), "usage_note": usage_note,
    })
