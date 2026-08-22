"""D6 — `createProject`. 권한 판정(D2)과 저장(D6)의 조립은 이 자리에서만 한다."""
from __future__ import annotations

import datetime as dt
import re

from fastapi import APIRouter, Body, Depends, Response
from sqlalchemy.orm import Session

from ...domains import d2_access, d6_project
from ...kernel import errors
from ...kernel.auth import Subject
from ..deps import current_subject, scoped_db

router = APIRouter()

_YEAR_MONTH = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")
_TYPES = ("국가과제", "논문")


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
