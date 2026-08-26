"""D1 · D2 를 조립해 내리는 두 오퍼레이션 — `getCurrentAccount` · `getLab`."""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from ...domains import d1_identity, d2_access
from ...kernel import errors
from ...kernel.auth import Subject
from ..deps import current_subject, scoped_db

router = APIRouter()


@router.get("/me", name="getCurrentAccount")
def get_current_account(subject: Subject = Depends(current_subject),
                        db: Session = Depends(scoped_db)) -> dict:
    account = d1_identity.find_account(db, subject.account_id)
    if account is None:
        # 주체가 가리키는 계정이 이 연구실에 없다 — RLS 가 이미 지운 뒤다.
        raise errors.unauthorized("주체에 해당하는 계정이 경계 안에 없다.")
    role = d2_access.role_of(db, subject.account_id)
    if role is None:
        raise errors.unauthorized("역할이 배정되지 않은 계정이다.")
    return {
        "accountId": account["id"],
        "name": account["name"],
        "email": account["email"],
        "role": role,
        "permissions": d2_access.permissions_of(db, subject.account_id, role),
        "labId": account["lab_id"],
        "labName": account["lab_name"],
    }


#: `LabUpdate` 가 받는 열쇠. **계약이 정본이고** 런타임에 그것을 강제하는 것은 이 줄이다.
#: `openedAt` 은 없다 — **개설일은 고치는 값이 아니다.**
_LAB_UPDATE_FIELDS = ("name", "university", "department", "principalInvestigator",
                      "researchField", "introduction", "defaultVisibility")


@router.patch("/lab", name="updateLab")
def update_lab(body: dict | None = Body(default=None),
               subject: Subject = Depends(current_subject),
               db: Session = Depends(scoped_db)) -> dict:
    """연구실 정보 편집 (`PLAN-SoT §9 〈150〉` — `〈149〉-㉱` 가 남긴 결손 2건 중 하나).

    **이 op 이 없어서 이름을 잘못 적으면 고칠 수단이 없었다.** 그 이름은 연구실
    전환기와 업로드 모달 헤더가 읽으므로(`DataModel §2`) **틀리면 화면 여러 곳이
    함께 틀린다.** `〈127〉`·㈏ 가 데이터셋에서 연 「올린 뒤 고치는 길」의 연구실 판이다.

    **`연구실 설정` 스위치가 켜진 사람만**(`P-2` 행동표 · 계약 산문). 읽기는 전 구성원이다.
    """
    from .members import _require_lab_settings

    payload = body if isinstance(body, dict) else {}
    unknown = sorted(set(payload) - set(_LAB_UPDATE_FIELDS))
    if unknown:
        raise errors.bad_request(f"요청에 계약에 없는 필드가 있다: {unknown}",
                                 {"allowed": list(_LAB_UPDATE_FIELDS)})
    # **권한을 필드 검사보다 먼저 본다** — 권한 없는 사람에게 「어떤 필드가 있는지」를
    # 400 으로 알려 줄 이유가 없다. 다만 계약 밖 필드는 그 전에 거른다(형태 오류다).
    _require_lab_settings(db, subject)

    if "name" in payload:
        name = payload["name"]
        if not isinstance(name, str) or not name.strip():
            raise errors.bad_request("연구실 이름을 적어 주세요.")
    if "defaultVisibility" in payload and payload["defaultVisibility"] not in ("열림", "잠김"):
        raise errors.bad_request("데이터 공개 범위는 `열림`·`잠김` 이다.")

    if payload:
        d1_identity.update_lab(db, payload)
    return get_lab(db=db)


@router.get("/lab", name="getLab")
def get_lab(db: Session = Depends(scoped_db)) -> dict:
    """읽기는 전 구성원이다 — 편집 버튼만 권한자에게 보인다 (Policy_홈_대시보드 §6)."""
    lab = d1_identity.find_lab(db)
    if lab is None:
        raise errors.not_found("연구실을 찾지 못했다.")
    return {
        "labId": lab["id"],
        "name": lab["name"],
        "university": lab["university"],
        "department": lab["department"],
        "principalInvestigator": lab["principal_investigator"],
        "researchField": lab["research_field"],
        "introduction": lab["introduction"],
        "defaultVisibility": lab["default_visibility"] or "열림",
        "memberCount": d1_identity.member_count(db),
        "openedAt": lab["opened_at"],
    }
