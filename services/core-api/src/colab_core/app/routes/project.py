"""D6 조립 — `createProject` · `listProjects`(S-02) · `getProject`(S-02b) · `linkProjectDataset`.

권한 판정(D2)과 저장(D6)의 조립은 이 자리에서만 한다.

**D6 → D3 을 어떻게 건너는가** (`CLAUDE.md §3-1`). 프로젝트 카드의 지표 타일 세 칸과
소속 데이터셋 표의 열들은 **D6 의 사실이 아니다** — 이름·조각 수는 D3, 계보는 D4,
접근·Verified 는 D2 다. `d6_project.py` 는 이 값을 하나도 읽지 않고 **자기 표의 식별자와
의미 문장만** 내놓는다. 그 식별자를 열로 채우는 일은 **이 조립 루트**가 하고, 각 도메인의
사실은 이미 있는 Port 어댑터(`DatasetAccessPort` · `LineageSummaryPort`)와 D3 자신의
모듈 함수로 받는다. `routes/catalog.py` 가 반대 방향(D3 이 D6 의 프로젝트 열을 받는 쪽)에서
쓰는 것과 **같은 무늬**다 — 새 Port 를 세우지 않아도 되는 이유가 이것이다.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Any

from fastapi import APIRouter, Body, Depends, Query, Response
from sqlalchemy.orm import Session

from ...domains import d2_access, d3_catalog, d4_lineage, d6_project
from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ..deps import current_subject, scoped_db

router = APIRouter()

_YEAR_MONTH = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")
_TYPES = ("국가과제", "논문")
_STATUSES = ("진행 중", "닫힘")

#: 목록 정렬 네 값 — 표기는 `Policy_프로젝트 §5` 목록 정렬 행 그대로다.
#: **기간 정렬의 기준은 시작일이다**(§5). 종료 정렬만 종료일을 본다.
_SORTS = ("최근 시작 순", "먼저 시작한 순", "최근 종료 순", "데이터셋 많은 순")
#: 목록 화면이 「전체」로 조건을 지울 때 쓰는 표기. 계약은 비우기(파라미터 생략)를 정본으로
#: 삼지만, 화면의 상태 셀렉트에는 `전체` 값이 있다(§5 목록 필터) — 둘 다 「거르지 않는다」다.
_ALL = "전체"


def _period(value: object) -> tuple[dt.date | None, dt.date | None]:
    """기간은 **연·월까지**다 (Policy_프로젝트 §5). 일자는 계약에 없으므로 1일로 저장한다."""
    if value is None:
        return None, None
    if not isinstance(value, dict):
        raise errors.bad_request("period 형태가 계약과 다르다.")
    out: list[dt.date | None] = []
    for key in ("start", "end"):
        v = value.get(key)
        if v is None:
            out.append(None)
            continue
        if not isinstance(v, str) or not _YEAR_MONTH.match(v):
            raise errors.bad_request(f"period.{key} 는 YYYY-MM 이어야 한다.")
        out.append(dt.date(int(v[:4]), int(v[5:7]), 1))
    return out[0], out[1]


def _year_month(value: dt.date | None) -> str | None:
    return None if value is None else f"{value.year:04d}-{value.month:02d}"


@router.post("/projects", name="createProject", status_code=201)
def create_project(response: Response, body: dict = Body(...),
                   subject: Subject = Depends(current_subject),
                   db: Session = Depends(scoped_db)) -> dict:
    role = d2_access.role_of(db, subject.account_id)
    permissions = d2_access.permissions_of(db, subject.account_id, role)
    if not permissions.get("프로젝트 생성"):
        # 화면에서 숨긴 것을 서버가 같은 기준으로 막는다 (P-11·P-12).
        raise errors.forbidden("`프로젝트 생성` 스위치가 꺼져 있다.")

    unknown = set(body) - {"type", "name", "description", "period", "link"}
    if unknown:
        raise errors.bad_request(f"계약에 없는 필드다: {sorted(unknown)}")
    type_ = body.get("type")
    name = body.get("name")
    if type_ not in _TYPES:
        raise errors.bad_request(f"type 은 {list(_TYPES)} 중 하나다.")
    if not isinstance(name, str) or not (1 <= len(name) <= 100):
        raise errors.bad_request("name 은 1~100자다.")
    start, end = _period(body.get("period"))

    row = d6_project.create_project(
        db, type_=type_, name=name, description=body.get("description"),
        period_start=start, period_end=end, link_url=body.get("link"),
    )
    return {
        "projectId": row["id"],
        "name": row["name"],
        "type": row["type"],
        "status": row["status"],
        "period": (None if row["period_start"] is None and row["period_end"] is None
                   else {"start": _year_month(row["period_start"]),
                         "end": _year_month(row["period_end"])}),
        "description": row["description"],
        "link": row["link_url"],
        "datasets": [],   # 담는 동작은 이 seam 에 없다 — 업로드 화면(E-04)이 맡는다
        "canManage": True,
    }


# ════════════════════════════════════════════════════════════════════════════
# S-02 목록 · S-02b 상세 · 연결 (WU-P5)
# ════════════════════════════════════════════════════════════════════════════

#: 커서 문법은 **한 벌만 둔다.** 카탈로그와 다른 문법을 세우면 같은 봉투(`ListEnvelope`)가
#: 자리에 따라 다른 커서를 뜻하게 된다. 그래서 여기서 다시 짜지 않고 그것을 쓴다.
from .catalog import PAGE_SIZE, _decode_cursor, _encode_cursor  # noqa: E402


def _can_manage(db: Session, subject: Subject) -> bool:
    """`프로젝트 생성` 스위치 하나가 이 화면의 **모든 쓰기 동작**을 가른다 (§6 · P-6).

    역할로 유도하지 않는다 — 교수는 `permissions_of` 가 이미 판정해 켜서 준다 (P-5).
    """
    role = d2_access.role_of(db, subject.account_id)
    return bool(d2_access.permissions_of(db, subject.account_id, role).get("프로젝트 생성"))


def _period_out(record) -> dict | None:
    if record.period_start is None and record.period_end is None:
        return None
    return {"start": _year_month(record.period_start), "end": _year_month(record.period_end)}


def _data_period(value: tuple | None) -> dict | None:
    """데이터가 다루는 시간 범위. **프로젝트 기간과 축이 다르다** (`DataModel §4.1`)."""
    if value is None:
        return None
    start, end = value
    def iso(v: Any) -> Any:
        return v.astimezone(dt.timezone.utc).isoformat() if isinstance(v, dt.datetime) else v
    return {"start": iso(start), "end": iso(end)}


def _dataset_facts(db: Session, dataset_ids: list[str]) -> dict[str, dict]:
    """식별자 → 소속 데이터셋 표 한 행에 필요한 **네 도메인의 사실**.

    D6 은 여기 오는 식별자를 줄 뿐이고, 값은 각자의 주인에게서 온다.
    **경계 밖·묘비 식별자는 결과에서 빠진다** — RLS 가 이미 행을 지웠고 지어내지 않는다.
    """
    if not dataset_ids:
        return {}
    ids = [Ulid(i) for i in dataset_ids]
    cores = {c.dataset_id: c for c in d3_catalog.list_dataset_cores(db)}
    periods = d3_catalog.periods_of(db, ids)
    summaries = d4_lineage.LineageSummaryAdapter(db).summaries(ids)
    access = d2_access.DatasetAccessAdapter(db).dataset_access(ids)

    out: dict[str, dict] = {}
    for dataset_id in dataset_ids:
        core = cores.get(dataset_id)
        if core is None:
            continue
        summary = summaries.get(dataset_id)
        acc = access.get(dataset_id)
        out[dataset_id] = {
            "datasetId": dataset_id,
            # **잠겼다고 이름을 지우지 않는다** — 이름·요약까지는 보이고 그 자리가
            # 접근 요청이 된다 (P-13). 숨기면 E-06 흐름 자체가 사라진다.
            "name": core.name,
            # 조각 수는 메타 열이다 — 본체를 세지 않는다 (㊼). 잠긴 행에서 0 이 되는 것을 막는다.
            "fileCount": core.file_count,
            "processingLevel": d3_catalog.processing_level(summary),
            "period": _data_period(periods.get(dataset_id)),
            "lineageState": d3_catalog.lineage_state(core, summary),
            "verified": False if acc is None else acc.verified,
            "accessState": "열림" if acc is None else acc.access_state,
            # 닫히는 것은 본체뿐이다 (P-34). 화면은 이 값으로 잠김 자리를 그린다.
            "bodyAccessible": False if acc is None else acc.body_accessible,
        }
    return out


@router.get("/projects", name="listProjects")
def list_projects(subject: Subject = Depends(current_subject),
                  db: Session = Depends(scoped_db),
                  cursor: str | None = Query(default=None),
                  status: str | None = Query(default=None),
                  type: str | None = Query(default=None),
                  sort: str | None = Query(default=None)) -> dict:
    """S-02 — 카드/표 두 보기가 **같은 거른 결과**를 그린다 (`Policy_프로젝트 §5`).

    기본값(상태 `진행 중`)은 **화면이 건다** — 서버가 걸면 「전체」를 부를 길이 없어진다
    (계약 `listProjects` 산문). 숨은 닫힘 건수도 같은 조건에 상태만 바꿔 부른 `totalCount` 로
    읽는다. 봉투에 필드를 더하지 않는다.
    """
    if status is not None and status not in _STATUSES and status != _ALL:
        raise errors.bad_request(f"status 는 {list(_STATUSES)} 중 하나다.")
    if type is not None and type not in _TYPES and type != _ALL:
        raise errors.bad_request(f"type 은 {list(_TYPES)} 중 하나다.")
    if sort is not None and sort not in _SORTS:
        raise errors.bad_request(f"sort 는 {list(_SORTS)} 중 하나다.")

    records = d6_project.list_projects(db)
    if status not in (None, _ALL):
        records = [r for r in records if r.status == status]
    if type not in (None, _ALL):
        records = [r for r in records if r.type == type]

    by_project = d6_project.dataset_ids_by_project(db)
    facts = _dataset_facts(db, sorted({i for r in records
                                       for i in by_project.get(r.project_id, [])}))

    rows: list[dict] = []
    for record in records:
        linked = [facts[i] for i in by_project.get(record.project_id, []) if i in facts]
        rows.append({
            "projectId": record.project_id,
            "name": record.name,
            "type": record.type,
            "status": record.status,
            "period": _period_out(record),
            "description": record.description,
            # 지표 타일 세 칸. **0 이어도 칸을 비우지 않는다** — 값이 0 이라는 사실을 내린다 (§5).
            "datasetCount": len(linked),
            "verifiedCount": sum(1 for d in linked if d["verified"]),
            "unknownLineageCount": sum(1 for d in linked if d["lineageState"] == "기록 없음"),
            "_start": record.period_start,
            "_end": record.period_end,
        })

    _sort_rows(rows, sort or "최근 시작 순")

    total = len(rows)
    offset = _decode_cursor(cursor)
    page = rows[offset:offset + PAGE_SIZE]
    next_cursor = _encode_cursor(offset + PAGE_SIZE) if offset + PAGE_SIZE < total else None
    for row in page:
        row.pop("_start", None)
        row.pop("_end", None)
    return {"items": page, "totalCount": total, "nextCursor": next_cursor}


def _sort_rows(rows: list[dict], sort: str) -> None:
    """**빈 기간은 언제나 뒤로 간다.** 없는 값을 최댓값·최솟값으로 취급하면 정렬을 바꿀 때마다
    같은 프로젝트가 맨 앞과 맨 뒤를 오간다."""
    key = {"최근 시작 순": "_start", "먼저 시작한 순": "_start", "최근 종료 순": "_end"}.get(sort)
    if key is None:                                 # 데이터셋 많은 순
        rows.sort(key=lambda r: (-r["datasetCount"], r["name"]))
        return
    ascending = sort == "먼저 시작한 순"
    dated = [r for r in rows if r[key] is not None]
    undated = [r for r in rows if r[key] is None]
    dated.sort(key=lambda r: r[key], reverse=not ascending)
    rows[:] = dated + sorted(undated, key=lambda r: r["name"])


@router.get("/projects/{projectId}", name="getProject")
def get_project(projectId: str, subject: Subject = Depends(current_subject),
                db: Session = Depends(scoped_db)) -> dict:
    """S-02b — 개요 · 연결 주소 · **소속 데이터셋 전부**. 자르지 않는다 (§5 표 범위).

    조회에는 권한 차이가 없다 (§6) — `프로젝트 생성` 이 꺼진 사람도 목록·상세를 본다.
    그 스위치는 `canManage` 로 내려가 화면이 쓰기 버튼을 **숨기는** 데만 쓰인다 (P-12).
    """
    if not Ulid.is_valid(projectId):
        raise errors.bad_request("projectId 가 정규 ID 가 아니다.")
    record = d6_project.find_project(db, Ulid(projectId))
    if record is None:
        # 경계 밖이면 RLS 가 이미 행을 지웠다 → 존재를 알리지 않는 404 다 (P-9·P-10).
        raise errors.not_found()

    links = d6_project.datasets_of(db, Ulid(projectId))
    facts = _dataset_facts(db, [dataset_id for dataset_id, _ in links])
    datasets = [{**facts[dataset_id], "usageNote": note}
                for dataset_id, note in links if dataset_id in facts]

    return {
        "projectId": record.project_id,
        "name": record.name,
        "type": record.type,
        "status": record.status,
        "period": _period_out(record),
        "description": record.description,
        # 연결 주소는 설명·기간과 **다른 묶음**이다 (§1.2). 값을 고쳐 보여주지 않는다 (§8).
        "link": record.link_url,
        "datasets": datasets,
        "canManage": _can_manage(db, subject),
    }


@router.put("/projects/{projectId}/datasets/{datasetId}", name="linkProjectDataset",
            status_code=204)
def link_project_dataset(projectId: str, datasetId: str, body: dict = Body(...),
                         subject: Subject = Depends(current_subject),
                         db: Session = Depends(scoped_db)) -> Response:
    """연결 한 건 — **활용 의미 문장을 쓰는 유일한 수단**이다 (계약 산문 · `DataModel §5`).

    이미 있는 연결이면 문장을 고친다(멱등 PUT). 등록 시점의 연결은 `createDataset.projectIds`
    가 만들고 이 op 은 등록 후 연결·문장 편집이다.
    """
    if not Ulid.is_valid(projectId):
        raise errors.bad_request("projectId 가 정규 ID 가 아니다.")
    if not Ulid.is_valid(datasetId):
        raise errors.bad_request("datasetId 가 정규 ID 가 아니다.")

    project_id, dataset_id = Ulid(projectId), Ulid(datasetId)
    # **경계가 권한보다 먼저다** (P-10) — 남의 연구실 프로젝트는 스위치와 무관하게 404 다.
    if not d6_project.project_exists(db, project_id):
        raise errors.not_found()
    if not _can_manage(db, subject):
        # 화면에서 숨긴 것을 서버가 같은 기준으로 막는다 (P-11·P-12 · §6).
        raise errors.forbidden("`프로젝트 생성` 스위치가 꺼져 있다.")

    unknown = sorted(set(body) - {"usageNote"})
    if unknown:
        raise errors.bad_request(f"계약에 없는 필드다: {unknown}")
    if "usageNote" not in body:
        # required 다 — 아직 못 적었으면 **null 로 명시**한다. 빠뜨린 요청과 구분하기 위해서다.
        raise errors.bad_request("usageNote 는 required 다 — 없으면 null 로 적는다.")
    usage_note = body["usageNote"]
    if usage_note is not None and not isinstance(usage_note, str):
        raise errors.bad_request("usageNote 는 문자열이거나 null 이다.")

    # `dataset_id` 는 bare 컬럼이라 없는 데이터셋도 DB 는 받는다 — **존재 확인은 부르는 쪽**이다.
    # 경계 밖 데이터셋도 여기서 False 가 되어 유령 연결이 쌓이지 않는다.
    if not d3_catalog.dataset_exists(db, dataset_id):
        raise errors.bad_request("그런 데이터셋이 없다.")

    d6_project.upsert_link(db, project_id=project_id, dataset_id=dataset_id,
                           usage_note=usage_note)
    # commit 은 `scoped_db` 가 한다 — 요청 하나 = 트랜잭션 하나 (`app/deps.py`).
    return Response(status_code=204)
