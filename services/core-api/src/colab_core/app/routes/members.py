"""D1 · D2 조립 — `listLabMembers` · `saveLabMemberPermissions`.

`연구실 설정 > 구성원 · 권한` 은 **권한 값을 고치는 유일한 자리**다 (P-18).
읽을 화면만 세우는 P1 에서 이 하나만 쓰기 화면으로 여는 이유가 그것이다 — 값의 원천이라
여기가 없으면 다른 화면의 권한 판정이 전부 시드에 기댄다.

여기서 서버가 강제하는 것 셋 —
  · **교수 행 고정** (P-5) — 교수는 네 스위치가 켜진 것으로 취급하고 아무도 못 고친다
  · **재위임 금지** (P-31) — `연구실 설정` 위임자는 `업로드·편집`·`프로젝트 생성` 두 열만 고친다
  · **화면에서 숨긴 것을 서버도 막는다** (P-11) — 격자의 편집 불가 칸은 403 이다
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from ...domains import d1_identity, d2_access
from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ..deps import current_subject, scoped_db

router = APIRouter()

#: 위임자가 고칠 수 있는 두 열. 나머지 둘(`승인 위임`·`연구실 설정`)은 교수만이다 (P-31).
DELEGABLE_SWITCHES = ("업로드·편집", "프로젝트 생성")


def _editable_permissions(*, viewer_is_professor: bool, row_role: str | None) -> list[str]:
    """이 요청자가 이 행에서 고칠 수 있는 열 — 재위임 금지의 계약 쪽 표현이다 (P-31).

    나머지 열은 **값은 보이되 편집 불가**로 그린다. 열을 지우면 표 구조가 깨져
    무엇을 못 만지는지조차 안 보이므로 여기서는 `P-12`(숨김)를 적용하지 않는다.
    """
    if row_role == "교수":
        return []                              # 교수 행은 고정이다 (P-5)
    if viewer_is_professor:
        return list(d2_access.SWITCHES)
    return list(DELEGABLE_SWITCHES)


def _require_lab_settings(db: Session, subject: Subject) -> bool:
    """`연구실 설정` 이 없으면 이 화면 자체가 없다 (P-18 · P-11). 반환값은 「교수인가」."""
    role = d2_access.role_of(db, subject.account_id)
    permissions = d2_access.permissions_of(db, subject.account_id, role)
    if not permissions.get("연구실 설정", False):
        raise errors.forbidden("`연구실 설정` 권한이 없다 — 구성원·권한은 그 자리 하나다 (P-18).")
    return role == "교수"


def _grid(db: Session, *, viewer_is_professor: bool) -> dict:
    """구성원 = 행, 권한 4종 = 열. 격자 관계라 표가 맞다 (E-01 §3)."""
    permissions = d2_access.member_permissions(db)
    items = []
    for account in d1_identity.list_members(db):
        account_id = account["id"].strip()
        row = permissions.get(account_id)
        items.append({
            "accountId": account_id,
            "name": account["name"],
            "email": account["email"],
            "role": None if row is None else row.role,
            "permissions": ({s: False for s in d2_access.SWITCHES} if row is None
                            else dict(row.switches)),
            "editablePermissions": _editable_permissions(
                viewer_is_professor=viewer_is_professor,
                row_role=None if row is None else row.role,
            ),
        })
    return {"items": items, "totalCount": len(items), "nextCursor": None}


@router.get("/lab/members", name="listLabMembers")
def list_lab_members(subject: Subject = Depends(current_subject),
                     db: Session = Depends(scoped_db)) -> dict:
    return _grid(db, viewer_is_professor=_require_lab_settings(db, subject))


@router.put("/lab/members/permissions", name="saveLabMemberPermissions")
def save_lab_member_permissions(subject: Subject = Depends(current_subject),
                                db: Session = Depends(scoped_db),
                                body: dict = Body(...)) -> dict:
    """확인 모달 한 번 = 요청 한 번 (P-19). 스위치 하나가 이력 한 줄이 된다 (P-33).

    **검사를 전부 마친 뒤에 쓴다.** 한 요청에 허용 칸과 금지 칸이 섞이면 통째로 거부한다 —
    절반만 저장하면 사용자가 방금 확인한 격자와 저장된 격자가 갈라진다.
    """
    viewer_is_professor = _require_lab_settings(db, subject)

    items = body.get("items")
    if not isinstance(items, list) or not items:
        raise errors.bad_request("바꾼 칸이 없다 — `items` 는 한 건 이상이다.")

    permissions = d2_access.member_permissions(db)
    planned: list[tuple[Ulid, str, bool]] = []
    for item in items:
        if not isinstance(item, dict):
            raise errors.bad_request("items 의 원소가 객체가 아니다.")
        account_id = item.get("accountId")
        changes = item.get("changes")
        if not isinstance(account_id, str) or not Ulid.is_valid(account_id):
            raise errors.bad_request("accountId 가 정규 ID 가 아니다.")
        if not isinstance(changes, dict) or not changes:
            raise errors.bad_request("`changes` 는 바꾼 칸 한 개 이상이다.")
        target = Ulid(account_id)
        # 경계 밖·없는 계정은 존재를 알리지 않는다 (P-9·P-10).
        if not d1_identity.member_exists(db, target):
            raise errors.not_found()
        row = permissions.get(account_id)
        editable = set(_editable_permissions(
            viewer_is_professor=viewer_is_professor,
            row_role=None if row is None else row.role,
        ))
        for switch, enabled in changes.items():
            if switch not in d2_access.SWITCHES:
                raise errors.bad_request(
                    "권한 스위치는 정확히 넷이다 — 다섯 번째를 만들지 않는다.",
                    {"switch": switch})
            if not isinstance(enabled, bool):
                raise errors.bad_request("스위치 값은 켜짐/꺼짐이다.")
            if switch not in editable:
                # 화면에서 편집 불가로 그린 칸이다. 서버도 같은 기준으로 막는다 (P-11 · P-31).
                raise errors.forbidden(
                    "이 칸은 고칠 수 없다 — 교수 행은 고정이고(P-5), 위임은 재위임되지 않는다(P-31).")
            planned.append((target, switch, enabled))

    for target, switch, enabled in planned:
        d2_access.apply_switch(db, actor_id=subject.account_id, target_id=target,
                               switch=switch, enabled=enabled)

    db.flush()
    return _grid(db, viewer_is_professor=viewer_is_professor)
