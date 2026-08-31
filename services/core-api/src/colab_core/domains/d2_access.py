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


# ════════════════════════════════════════════════════════════════════════════
# 승인 처리 (WU-P6) — 접근 요청 · Verified 두 갈래
#
# **이 구역은 자기 표 넷만 만진다** — `d2_dataset_access_request` ·
# `d2_verification_request` · `d2_dataset_access_grant` · `d2_verified`.
# 데이터셋의 이름도 요청자의 이름도 여기서 읽지 않는다. 그건 D3·D1 의 사실이고,
# 조립은 `routes/access.py` 가 한다 (CLAUDE.md §3-1 · `routes/project.py` 와 같은 무늬).
#
# **처리 권한은 두 갈래가 다르다** (정본 §1.2 §6).
#   · 접근 요청  = 교수 + `승인 위임` 연구원   → `can_decide_access`
#   · Verified   = 교수만, 위임 불가 (P-22)   → `can_decide_verification`
# 그 판정을 라우트가 각자 다시 쓰지 않게 여기서 한 번만 정의한다.
# ════════════════════════════════════════════════════════════════════════════

_INSERT_ACCESS_REQUEST = text("""
    INSERT INTO d2_dataset_access_request
      (id, lab_id, dataset_id, requester_account_id, reason)
    VALUES (:id, current_lab_id(), :dataset_id, :requester, :reason)
    RETURNING id, dataset_id, requester_account_id, requested_at, reason
""")

#: 검토 대기가 이미 있는가. 부분 유니크가 DB 층에서 막지만, 409 를 **예외가 아니라 판정으로**
#: 내기 위해 미리 본다. 제약 위반을 잡아 409 로 바꾸면 다른 원인의 위반까지 409 가 된다.
_PENDING_ACCESS_OF = text("""
    SELECT id FROM d2_dataset_access_request
     WHERE dataset_id = :dataset_id AND requester_account_id = :requester
       AND state = '검토 대기'
""")

#: 보는 사람의 검토 대기 — 상세의 `accessRequestPending` 한 칸이 쓴다.
_PENDING_ACCESS_FOR_VIEWER = text("""
    SELECT dataset_id FROM d2_dataset_access_request
     WHERE requester_account_id = current_account_id()
       AND state = '검토 대기'
       AND dataset_id = ANY(CAST(:ids AS char(26)[]))
""")

#: 할 일 함 — **오래된 순**이다 (정본 §1.3 「방치를 막기 위해서다」).
#: 경계는 RLS 가 이미 걸었다 — 여기에 `lab_id` 조건을 또 쓰지 않는다.
_PENDING_ACCESS_LIST = text("""
    SELECT id, dataset_id, requester_account_id, requested_at, reason
      FROM d2_dataset_access_request
     WHERE state = '검토 대기'
     ORDER BY requested_at, id
""")

_ACCESS_REQUEST_ROW = text("""
    SELECT id, dataset_id, requester_account_id, requested_at, reason, state
      FROM d2_dataset_access_request WHERE id = :id
""")

#: 검토 대기 한 줄을 처리로 옮긴다. **`state = '검토 대기'` 를 WHERE 에 둔 것이 핵심이다** —
#: 이미 처리된 줄은 0행이 갱신되고, 라우트는 그 0 을 409 로 읽는다. 두 사람이 동시에
#: 눌러도 한 줄만 이긴다 (읽고 나서 쓰는 사이의 틈을 없앤다).
_DECIDE_ACCESS_REQUEST = text("""
    UPDATE d2_dataset_access_request
       SET state = :state, decided_by_account_id = :decider, decided_at = now(),
           rejection_reason = :rejection_reason
     WHERE id = :id AND state = '검토 대기'
    RETURNING dataset_id, requester_account_id
""")

#: 허용 목록 한 줄. **만료일 = 승인일 + 6개월** (정본 §1.3-6 · P-25).
#: 그 값을 애플리케이션이 계산하지 않는다 — 승인 시각과 만료 시각이 **같은 문장에서** 나와야
#: 둘이 어긋날 자리가 없다. `approved_at` 은 기본값(now())을 쓴다.
_INSERT_GRANT = text("""
    INSERT INTO d2_dataset_access_grant
      (id, lab_id, dataset_id, grantee_account_id, approver_account_id, expires_at)
    VALUES (:id, current_lab_id(), :dataset_id, :grantee, :approver,
            now() + interval '6 months')
    RETURNING approved_at, expires_at
""")

_INSERT_VERIFICATION_REQUEST = text("""
    INSERT INTO d2_verification_request
      (id, lab_id, dataset_id, requester_account_id)
    VALUES (:id, current_lab_id(), :dataset_id, :requester)
    RETURNING dataset_id, requester_account_id, requested_at
""")

_PENDING_VERIFICATION_OF = text("""
    SELECT id FROM d2_verification_request
     WHERE dataset_id = :dataset_id AND state = '검토 대기'
""")

_PENDING_VERIFICATION_LIST = text("""
    SELECT dataset_id, requester_account_id, requested_at
      FROM d2_verification_request
     WHERE state = '검토 대기'
     ORDER BY requested_at, id
""")

_CLOSE_VERIFICATION_REQUEST = text("""
    UPDATE d2_verification_request
       SET state = '승인됨', decided_by_account_id = :decider, decided_at = now()
     WHERE dataset_id = :dataset_id AND state = '검토 대기'
""")

#: 배지를 붙인다. 취소 흔적은 지운다 — 다시 승인된 것이지 취소된 채로 승인된 것이 아니다.
_APPROVE_VERIFIED = text("""
    INSERT INTO d2_verified
      (dataset_id, lab_id, verified, approver_account_id, approved_at)
    VALUES (:dataset_id, current_lab_id(), true, :approver, now())
    ON CONFLICT (dataset_id) DO UPDATE
       SET verified = true, approver_account_id = EXCLUDED.approver_account_id,
           approved_at = EXCLUDED.approved_at,
           cancelled_by_account_id = NULL, cancelled_at = NULL, cancellation_reason = NULL
""")

#: 취소 — **데이터와 계보는 남고 배지만 사라진다** (정본 §1.3-9).
#: 승인자·승인 시각을 지우지 않는다: 「누가 한때 보증했는가」는 취소해도 남는 사실이다.
_CANCEL_VERIFIED = text("""
    UPDATE d2_verified
       SET verified = false, cancelled_by_account_id = :actor, cancelled_at = now(),
           cancellation_reason = :reason
     WHERE dataset_id = :dataset_id AND verified
""")

_VERIFIED_STATE = text("SELECT verified FROM d2_verified WHERE dataset_id = :dataset_id")


def can_decide_access(session: Session, account_id: Ulid) -> bool:
    """접근 요청을 처리할 수 있는가 — **교수 + `승인 위임` 연구원** (정본 §1.2 §6).

    역할로 유도하지 않는다. 교수는 `permissions_of` 가 네 스위치를 켜서 주므로(P-5),
    스위치 하나만 보면 두 경우가 한 판정으로 닫힌다.
    """
    role = role_of(session, account_id)
    return bool(permissions_of(session, account_id, role).get("승인 위임", False))


def can_decide_verification(session: Session, account_id: Ulid) -> bool:
    """Verified 를 처리할 수 있는가 — **교수만이고 위임되지 않는다** (정본 §1.2 · P-22).

    `승인 위임` 스위치를 보지 않는 것이 이 함수의 요점이다. 위의 것과 같은 판정으로
    묶으면 위임 연구원에게 배지 권한이 새고, 그건 화면에서 조용하다.
    """
    return role_of(session, account_id) == "교수"


def pending_access_request_of(session: Session, dataset_id: Ulid, requester_id: Ulid) -> str | None:
    return session.execute(_PENDING_ACCESS_OF, {
        "dataset_id": str(dataset_id), "requester": str(requester_id)}).scalar_one_or_none()


def create_access_request(session: Session, *, dataset_id: Ulid, requester_id: Ulid,
                          reason: str | None):
    row = session.execute(_INSERT_ACCESS_REQUEST, {
        "id": str(Ulid.generate()), "dataset_id": str(dataset_id),
        "requester": str(requester_id), "reason": reason,
    }).mappings().one()
    return row


def pending_access_requests(session: Session) -> list:
    return session.execute(_PENDING_ACCESS_LIST).mappings().all()


def access_request_row(session: Session, request_id: str):
    return session.execute(_ACCESS_REQUEST_ROW, {"id": request_id}).mappings().one_or_none()


def datasets_with_pending_request(session: Session, dataset_ids: list[Ulid]) -> set[str]:
    """보는 사람이 검토 대기를 걸어 둔 데이터셋. 상세의 `accessRequestPending` 이 쓴다."""
    if not dataset_ids:
        return set()
    rows = session.execute(_PENDING_ACCESS_FOR_VIEWER, {"ids": [str(i) for i in dataset_ids]})
    return {r.dataset_id.strip() for r in rows}


def decide_access_request(session: Session, *, request_id: str, decider_id: Ulid,
                          approve: bool, rejection_reason: str | None):
    """검토 대기 → 승인됨/거절됨. **이미 처리된 줄이면 `None`** 을 돌려준다 (정본 §9).

    승인이면 같은 트랜잭션에서 허용 목록 한 줄을 함께 쓴다 — 상태만 바뀌고 허용 줄이
    없는 상태가 생기면 요청자는 「승인됐다」고 듣고 본체는 계속 닫혀 있다.
    """
    decided = session.execute(_DECIDE_ACCESS_REQUEST, {
        "id": request_id, "state": "승인됨" if approve else "거절됨",
        "decider": str(decider_id), "rejection_reason": None if approve else rejection_reason,
    }).mappings().one_or_none()
    if decided is None:
        return None
    if not approve:
        return {"dataset_id": decided["dataset_id"], "grantee": decided["requester_account_id"]}
    grant = session.execute(_INSERT_GRANT, {
        "id": str(Ulid.generate()), "dataset_id": decided["dataset_id"],
        "grantee": decided["requester_account_id"], "approver": str(decider_id),
    }).mappings().one()
    return {
        "dataset_id": decided["dataset_id"], "grantee": decided["requester_account_id"],
        "approved_at": grant["approved_at"], "expires_at": grant["expires_at"],
    }


def verified_state(session: Session, dataset_id: Ulid) -> bool | None:
    return session.execute(_VERIFIED_STATE, {"dataset_id": str(dataset_id)}).scalar_one_or_none()


def pending_verification_of(session: Session, dataset_id: Ulid) -> str | None:
    return session.execute(_PENDING_VERIFICATION_OF,
                           {"dataset_id": str(dataset_id)}).scalar_one_or_none()


def create_verification_request(session: Session, *, dataset_id: Ulid, requester_id: Ulid):
    return session.execute(_INSERT_VERIFICATION_REQUEST, {
        "id": str(Ulid.generate()), "dataset_id": str(dataset_id),
        "requester": str(requester_id),
    }).mappings().one()


def pending_verification_requests(session: Session) -> list:
    return session.execute(_PENDING_VERIFICATION_LIST).mappings().all()


def approve_verification(session: Session, *, dataset_id: Ulid, approver_id: Ulid) -> None:
    """배지를 붙이고 **검토 대기가 있었으면 같은 트랜잭션에서 닫는다.**

    검토 대기 없이도 승인할 수 있다 — 정본 §8 헤더 행은 ② 를 「검토 대기 + 교수」로
    적지만, 요청이 없던 데이터를 교수가 직접 승인하는 것을 금지한 조항은 없다.
    `_CLOSE_VERIFICATION_REQUEST` 가 0행을 갱신할 뿐이고 그것이 정상이다.
    """
    session.execute(_APPROVE_VERIFIED, {
        "dataset_id": str(dataset_id), "approver": str(approver_id)})
    session.execute(_CLOSE_VERIFICATION_REQUEST, {
        "dataset_id": str(dataset_id), "decider": str(approver_id)})


def cancel_verification(session: Session, *, dataset_id: Ulid, actor_id: Ulid,
                        reason: str | None) -> bool:
    """배지를 뗀다. 승인된 상태가 아니었으면 `False` — 지어낸 취소 기록을 남기지 않는다."""
    result = session.execute(_CANCEL_VERIFIED, {
        "dataset_id": str(dataset_id), "actor": str(actor_id), "reason": reason})
    return result.rowcount > 0
