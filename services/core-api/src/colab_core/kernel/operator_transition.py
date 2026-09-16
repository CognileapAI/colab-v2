"""Reviewed, fixed-list professor/operator transition. No data or password migration."""
from __future__ import annotations

import hashlib
import hmac
import json

from sqlalchemy import text

from .db_credentials import _OPERATOR_LOCK, OperatorChangeRefused
from .login_sessions import REVOKE_ACCOUNT_SESSIONS


class TransitionRefused(OperatorChangeRefused):
    """Safe, non-secret explanation suitable for the local operator CLI."""


def plan_sha256(plan: dict) -> str:
    return hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _selection(value: dict) -> dict:
    if not isinstance(value, dict) or set(value) != {"actorId", "keep", "revoke"}:
        raise TransitionRefused("선택 목록에는 actorId, keep, revoke만 지정하세요.")
    if not isinstance(value["actorId"], str) or not value["actorId"].strip():
        raise TransitionRefused("실행자의 계정 ID가 필요해요.")
    result = {"actorId": value["actorId"]}
    seen = set()
    for kind in ("keep", "revoke"):
        rows = value[kind]
        if not isinstance(rows, list):
            raise TransitionRefused("유지·회수 목록은 배열이어야 해요.")
        for row in rows:
            if (not isinstance(row, dict) or set(row) != {"accountId", "reason"}
                    or not all(isinstance(row[key], str) and row[key].strip()
                               for key in ("accountId", "reason"))):
                raise TransitionRefused("각 계정에는 계정 ID와 분류 사유가 필요해요.")
            if row["accountId"] in seen:
                raise TransitionRefused("유지·회수 목록에 중복되거나 겹치는 계정이 있어요.")
            seen.add(row["accountId"])
        result[kind] = sorted((dict(row) for row in rows), key=lambda row: row["accountId"])
    if not result["keep"]:
        raise TransitionRefused("마지막 시스템 관리자는 회수할 수 없어요.")
    if result["actorId"] not in {row["accountId"] for row in result["keep"]}:
        raise TransitionRefused("실행자는 유지할 시스템 관리자여야 해요. 자기 권한은 회수할 수 없어요.")
    return result


def _operators(db) -> list[str]:
    return list(db.execute(text(
        "SELECT account_id FROM account_admin.service_operator ORDER BY account_id")).scalars())


def _lock(db) -> None:
    # Account creation can also insert service_operator. Match its existing lock first,
    # then the designation lock; do not import app routes into the credential kernel.
    db.execute(text("SELECT pg_advisory_xact_lock(1131379081)"))
    db.execute(text(_OPERATOR_LOCK))


def _snapshot(db, ids: list[str]) -> list[dict]:
    rows = db.execute(text("""
        SELECT a.id, a.lab_id, m.role, c.status
          FROM d1_account a
          LEFT JOIN d2_member_role m ON m.account_id=a.id AND m.lab_id=a.lab_id
          LEFT JOIN account_admin.login_credential c ON c.account_id=a.id
         WHERE a.id::text = ANY(:ids) ORDER BY a.id
    """), {"ids": ids}).mappings()
    return [{"accountId": row["id"], "labId": row["lab_id"],
             "role": row["role"], "status": row["status"]} for row in rows]


def _plan(selection: dict, snapshot: list[dict]) -> dict:
    before = sorted(row["accountId"] for kind in ("keep", "revoke") for row in selection[kind])
    rows = {row["accountId"]: row for row in snapshot}
    if sorted(rows) != before:
        raise TransitionRefused("목록에 존재하지 않는 계정이 있어요.")
    if rows[selection["actorId"]]["status"] != "active":
        raise TransitionRefused("실행자는 로그인 가능한 활성 시스템 관리자여야 해요.")
    for item in selection["revoke"]:
        row = rows[item["accountId"]]
        if row["labId"] is None or row["role"] != "교수":
            raise TransitionRefused("회수 목록은 연구실에 소속된 교수 계정만 허용해요.")
    return {"version": 1, "selection": selection, "accounts": snapshot,
            "beforeOperatorIds": before,
            "afterOperatorIds": sorted(row["accountId"] for row in selection["keep"])}


class OperatorTransition:
    def __init__(self, factory):
        self._factory = factory

    def inventory(self) -> list[dict]:
        with self._factory.begin() as db:
            _lock(db)
            return _snapshot(db, _operators(db))

    def prepare(self, selection: dict) -> dict:
        selected = _selection(selection)
        with self._factory.begin() as db:
            _lock(db)
            current = _operators(db)
            plan = _plan(selected, _snapshot(db, current))
            if plan["beforeOperatorIds"] != current:
                raise TransitionRefused("현재 시스템 관리자 전체를 유지·회수 목록에 정확히 한 번씩 분류하세요.")
            return plan

    def apply(self, plan: dict, expected_sha256: str) -> dict:
        if not isinstance(expected_sha256, str) or not hmac.compare_digest(plan_sha256(plan), expected_sha256):
            raise TransitionRefused("검토한 계획의 SHA256과 일치하지 않아요.")
        if not isinstance(plan, dict) or set(plan) != {
                "version", "selection", "accounts", "beforeOperatorIds", "afterOperatorIds"}:
            raise TransitionRefused("지원하지 않는 전환 계획이에요. prepare로 다시 준비하세요.")
        selected = _selection(plan["selection"])
        with self._factory.begin() as db:
            _lock(db)
            # Existing set_status/reset_password also lock credential rows. Public account/role
            # tables have no UPDATE grant here; do not broaden privileges to lock display rows.
            ids = sorted(row["accountId"] for kind in ("keep", "revoke") for row in selected[kind])
            db.execute(text("""SELECT account_id FROM account_admin.login_credential
                WHERE account_id::text = ANY(:ids) ORDER BY account_id FOR UPDATE"""), {"ids": ids}).all()
            current = _operators(db)
            checked = _plan(selected, _snapshot(db, ids))
            if checked != plan:
                raise TransitionRefused("계획 이후 소속·역할·상태가 바뀌었어요. 목록을 다시 검토하세요.")
            if current == plan["afterOperatorIds"]:
                return {"changed": 0, "alreadyApplied": True}
            if current != plan["beforeOperatorIds"]:
                raise TransitionRefused("계획 이후 시스템 관리자 목록이 바뀌었어요. 목록을 다시 검토하세요.")
            for row in selected["revoke"]:
                account_id = row["accountId"]
                db.execute(text("DELETE FROM account_admin.service_operator WHERE account_id=:id"), {"id": account_id})
                db.execute(text("""UPDATE account_admin.login_credential
                    SET session_version=session_version+1, updated_at=now() WHERE account_id=:id"""), {"id": account_id})
                db.execute(text(REVOKE_ACCOUNT_SESSIONS), {"account_id": account_id})
            return {"changed": len(selected["revoke"]), "alreadyApplied": False}
