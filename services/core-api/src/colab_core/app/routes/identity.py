"""D1 · D2 를 조립해 내리는 두 오퍼레이션 — `getCurrentAccount` · `getLab`."""
from __future__ import annotations

from fastapi import APIRouter, Depends
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
