"""D2 Access & Policy — 역할 · 권한 스위치 4종 · 접근 상태 · Verified.

승인 흐름(접근 요청·Verified 승인)의 규칙 본체는 P6 이다 — 여기서는 그 자리를 읽기만 한다.
**쓰는 것은 권한 스위치 하나뿐이고**(P-18: 고치는 자리는 `연구실 설정 > 구성원 · 권한` 한 곳),
그 쓰기는 언제나 append-only 이력 한 줄을 함께 남긴다 (P-33).
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid
from ..ports.access import DatasetAccess, DatasetVerification, MemberPermissions

#: 권한 스위치는 정확히 넷이고 다섯 번째를 만들지 않는다 (common.json#/$defs/PermissionSwitch).
SWITCHES = ("업로드·편집", "프로젝트 생성", "승인 위임", "연구실 설정")

_ROLE = text("SELECT role FROM d2_member_role WHERE account_id = :account_id")
_SWITCHES = text("SELECT switch, enabled FROM d2_permission_switch WHERE account_id = :account_id")

_ACCESS = text("""
    SELECT d.dataset_id,
           COALESCE(a.state, p.default_visibility, '열림')      AS state,
           COALESCE(v.verified, false)                          AS verified,
           EXISTS (
             SELECT 1 FROM d2_dataset_access_grant g
              WHERE g.dataset_id = d.dataset_id
                AND g.grantee_account_id = current_account_id()
                AND g.expires_at > now()
           )                                                    AS granted
      FROM unnest(CAST(:ids AS char(26)[])) AS d(dataset_id)
      LEFT JOIN d2_dataset_access a ON a.dataset_id = d.dataset_id
      LEFT JOIN d2_verified       v ON v.dataset_id = d.dataset_id
      LEFT JOIN d1_lab_profile    p ON p.lab_id = current_lab_id()
""")


_VERIFICATION = text("""
    SELECT d.dataset_id,
           COALESCE(v.verified, false) AS verified,
           v.approver_account_id, ap.name AS approver_name, v.approved_at,
           v.cancelled_by_account_id, cb.name AS cancelled_by_name, v.cancelled_at,
           v.cancellation_reason
      FROM unnest(CAST(:ids AS char(26)[])) AS d(dataset_id)
      LEFT JOIN d2_verified v  ON v.dataset_id = d.dataset_id
      LEFT JOIN d1_account  ap ON ap.id = v.approver_account_id
      LEFT JOIN d1_account  cb ON cb.id = v.cancelled_by_account_id
""")

# 역할 · 스위치를 계정별로 한 번에 읽는다. 교수 판정(P-5)은 저장이 아니라 계산이라
# 여기서는 **저장된 것만** 돌려주고, 판정은 `permissions_of` 와 조립 루트가 한다.
_ROLES = text("SELECT account_id, role FROM d2_member_role")
_ALL_SWITCHES = text("SELECT account_id, switch, enabled FROM d2_permission_switch")

# 스위치 저장 — 계정 1:1 이라 갱신이지 이력이 아니다. 이력은 아래 append-only 표가 맡는다 (P-33).
_UPSERT_SWITCH = text("""
    INSERT INTO d2_permission_switch (account_id, lab_id, switch, enabled)
    VALUES (:account_id, current_lab_id(), :switch, :enabled)
    ON CONFLICT (account_id, switch)
    DO UPDATE SET enabled = EXCLUDED.enabled, updated_at = now()
""")

# 권한 변경 이력 — **append-only, 스위치 하나당 한 줄** (P-33).
# 수정·삭제 경로를 만들지 않는다. DB 트리거가 UPDATE·DELETE 를 거부한다.
_APPEND_CHANGE = text("""
    INSERT INTO d2_permission_change
      (id, lab_id, actor_account_id, target_account_id, switch, direction)
    VALUES (:id, current_lab_id(), :actor, :target, :switch, :direction)
""")


def role_of(session: Session, account_id: Ulid) -> str | None:
    return session.execute(_ROLE, {"account_id": str(account_id)}).scalar_one_or_none()


def permissions_of(session: Session, account_id: Ulid, role: str | None) -> dict[str, bool]:
    """교수는 네 스위치가 항상 켜진 것으로 내려간다 — 화면이 역할로 다시 판정하지 않는다 (P-5·P-6)."""
    if role == "교수":
        return {s: True for s in SWITCHES}
    stored = {r.switch: r.enabled for r in
              session.execute(_SWITCHES, {"account_id": str(account_id)})}
    return {s: bool(stored.get(s, False)) for s in SWITCHES}


class DatasetAccessAdapter:
    """`ports.DatasetAccessPort` 의 D2 쪽 구현. 조립은 app 이 한다."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def verification(self, dataset_ids: list[Ulid]) -> dict[str, DatasetVerification]:
        if not dataset_ids:
            return {}
        rows = self._session.execute(_VERIFICATION, {"ids": [str(i) for i in dataset_ids]})
        return {
            r["dataset_id"]: DatasetVerification(
                verified=bool(r["verified"]),
                approver_id=r["approver_account_id"],
                approver_name=r["approver_name"],
                approved_at=r["approved_at"],
                cancelled_by_id=r["cancelled_by_account_id"],
                cancelled_by_name=r["cancelled_by_name"],
                cancelled_at=r["cancelled_at"],
                cancellation_reason=r["cancellation_reason"],
            )
            for r in rows.mappings()
        }

    def dataset_access(self, dataset_ids: list[Ulid]) -> dict[str, DatasetAccess]:
        if not dataset_ids:
            return {}
        rows = self._session.execute(_ACCESS, {"ids": [str(i) for i in dataset_ids]}).mappings()
        out: dict[str, DatasetAccess] = {}
        for r in rows:
            open_ = r["state"] == "열림"
            out[r["dataset_id"]] = DatasetAccess(
                access_state=r["state"],
                verified=bool(r["verified"]),
                # 잠겨 있어도 허용 목록에 있으면 본체에 닿는다 (P-25 만료 포함).
                body_accessible=bool(open_ or r["granted"]),
            )
        return out


def roles_of_all(session: Session) -> dict[str, str]:
    """연구실 전원의 역할. 경계는 RLS 가 이미 걸었다."""
    return {r.account_id.strip(): r.role for r in session.execute(_ROLES)}


def member_permissions(session: Session) -> dict[str, MemberPermissions]:
    """격자 표 한 행의 D2 쪽 사실 — 역할 + 스위치 4종.

    **교수는 네 스위치가 항상 켜진 것으로 내려간다** (P-5·P-6). 화면이 역할로 다시
    판정하지 않게 하려면 판정이 끝난 값을 내려야 한다.
    """
    roles = roles_of_all(session)
    stored: dict[str, dict[str, bool]] = {}
    for r in session.execute(_ALL_SWITCHES):
        stored.setdefault(r.account_id.strip(), {})[r.switch] = r.enabled
    out: dict[str, MemberPermissions] = {}
    for account_id, role in roles.items():
        if role == "교수":
            switches = {s: True for s in SWITCHES}
        else:
            saved = stored.get(account_id, {})
            switches = {s: bool(saved.get(s, False)) for s in SWITCHES}
        out[account_id] = MemberPermissions(role=role, switches=switches)
    return out


def apply_switch(session: Session, *, actor_id: Ulid, target_id: Ulid,
                 switch: str, enabled: bool) -> None:
    """스위치 한 칸을 저장하고 **같은 트랜잭션에서** 이력 한 줄을 남긴다 (P-33).

    두 쓰기를 한 트랜잭션에 묶는 이유 — 값만 바뀌고 이력이 없는 상태가 생기면
    감사 기록이 「대체로 맞는 기록」이 된다. 그건 기록이 아니다.
    """
    session.execute(_UPSERT_SWITCH, {
        "account_id": str(target_id), "switch": switch, "enabled": enabled,
    })
    session.execute(_APPEND_CHANGE, {
        "id": str(Ulid.generate()), "actor": str(actor_id), "target": str(target_id),
        "switch": switch, "direction": "켬" if enabled else "끔",
    })
