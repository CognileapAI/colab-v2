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

from collections.abc import Callable

from fastapi import APIRouter, Body, Depends, Request
from sqlalchemy.orm import Session

from ...domains import d1_identity, d2_access
from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ..deps import current_subject, scoped_db

router = APIRouter()

#: 위임자가 고칠 수 있는 두 열. 나머지 둘(`승인 위임`·`연구실 설정`)은 교수만이다 (P-31).
DELEGABLE_SWITCHES = ("업로드·편집", "프로젝트 생성")


#: 비활성 계정의 표기. 계정 관리 화면과 **같은 말**이라 두 화면이 같은 사람을 같게 부른다.
INACTIVE = "inactive"


def _status_reader(request: Request) -> Callable[[str], str | None] | None:
    """계정 상태를 읽는 자리. **앱 롤이 `account_admin` 을 읽지 않는다** (`CLAUDE.md §3` 규칙 1).

    상태의 원본은 앱 롤 접근이 차단된 스키마에 있고, 그것을 읽는 자격은 계정 자격 저장소가
    따로 쥐고 있다(`kernel/db_credentials.py` · 별도 접속 롤). 여기서는 **그 저장소의 기존
    조회를 그대로 빌려 쓴다** — 새 롤 권한도, 새 표도, 마이그레이션도 만들지 않는다.

    저장소가 서 있지 않은 배치(계정 관리 미구성)에서는 `None` 이고, 그러면 응답에 상태
    열쇠가 실리지 않는다 — 계약이 그 열쇠를 선택으로 둔 이유다.
    """
    store = getattr(request.app.state, "database_credentials", None)
    return None if store is None else store.status_for_account


def _editable_permissions(*, viewer_is_professor: bool, row_role: str | None,
                          account_status: str | None = None) -> list[str]:
    """이 요청자가 이 행에서 고칠 수 있는 열 — 재위임 금지의 계약 쪽 표현이다 (P-31).

    나머지 열은 **값은 보이되 편집 불가**로 그린다. 열을 지우면 표 구조가 깨져
    무엇을 못 만지는지조차 안 보이므로 여기서는 `P-12`(숨김)를 적용하지 않는다.

    ⭑ ⟨2026-09-13 · `D-4`⟩ **비활성 계정 행은 아무도 못 고친다.** 쓰이지 않는 계정의 권한을
    켜고 끄는 것은 아무 효과도 없으면서 표에는 효과가 있는 것처럼 보인다 — 교수 행 고정과
    같은 자리에서 같은 방식으로 접는다. 화면은 이 배열만 읽으므로(P-31) 여기가 정본이다.
    """
    if account_status == INACTIVE:
        return []
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


def _grid(db: Session, *, viewer_is_professor: bool,
          status_of: Callable[[str], str | None] | None = None) -> dict:
    """구성원 = 행, 권한 4종 = 열. 격자 관계라 표가 맞다 (E-01 §3)."""
    permissions = d2_access.member_permissions(db)
    items = []
    for account in d1_identity.list_members(db, status_of=status_of):
        account_id = account["id"].strip()
        row = permissions.get(account_id)
        status = account.get("account_status")
        item = {
            "accountId": account_id,
            "name": account["name"],
            "email": account["email"],
            "role": None if row is None else row.role,
            "permissions": ({s: False for s in d2_access.SWITCHES} if row is None
                            else dict(row.switches)),
            "editablePermissions": _editable_permissions(
                viewer_is_professor=viewer_is_professor,
                row_role=None if row is None else row.role,
                account_status=status,
            ),
        }
        # 모르는 상태는 **싣지 않는다** — 계약이 이 열쇠를 선택으로 둔 자리다.
        if status is not None:
            item["accountStatus"] = status
        items.append(item)
    return {"items": items, "totalCount": len(items), "nextCursor": None}


@router.get("/lab/members", name="listLabMembers")
def list_lab_members(request: Request,
                     subject: Subject = Depends(current_subject),
                     db: Session = Depends(scoped_db)) -> dict:
    return _grid(db, viewer_is_professor=_require_lab_settings(db, subject),
                 status_of=_status_reader(request))


@router.put("/lab/members/permissions", name="saveLabMemberPermissions")
def save_lab_member_permissions(request: Request,
                                subject: Subject = Depends(current_subject),
                                db: Session = Depends(scoped_db),
                                body: dict = Body(...)) -> dict:
    """확인 모달 한 번 = 요청 한 번 (P-19). 스위치 하나가 이력 한 줄이 된다 (P-33).

    **검사를 전부 마친 뒤에 쓴다.** 한 요청에 허용 칸과 금지 칸이 섞이면 통째로 거부한다 —
    절반만 저장하면 사용자가 방금 확인한 격자와 저장된 격자가 갈라진다.
    """
    viewer_is_professor = _require_lab_settings(db, subject)
    status_of = _status_reader(request)

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
        # 화면에서 잠근 줄이다. **서버도 같은 기준으로 막는다** — 화면만 막으면 요청으로
        # 우회된다 (P-11 · `D-4`). 없는 계정과 달리 존재는 이미 확인됐으므로 400 이다.
        status = None if status_of is None else status_of(account_id)
        if status == INACTIVE:
            raise errors.bad_request(
                "비활성 계정의 권한은 바꿀 수 없다 — 먼저 계정을 다시 활성으로 되돌린다.",
                {"accountId": account_id})
        row = permissions.get(account_id)
        editable = set(_editable_permissions(
            viewer_is_professor=viewer_is_professor,
            row_role=None if row is None else row.role,
            account_status=status,
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
    return _grid(db, viewer_is_professor=viewer_is_professor, status_of=status_of)
