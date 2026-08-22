"""D2 Access & Policy — 역할 · 권한 스위치 4종 · 접근 상태 · Verified.

규칙 본체(승인 흐름)는 P6 이다. 여기서는 P0 이 만든 저장 자리를 읽기만 한다.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid
from ..ports.access import DatasetAccess

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
