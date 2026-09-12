"""계정 상태 열(`account_admin.login_credential.status`)의 판정.

비활성 계정은 **로그인 거절**이고, 거절의 겉모습은 「비밀번호가 틀렸다」와 같다 —
응답으로 계정의 존재·상태가 갈리면 그 자리가 열거 통로가 된다 (`routes/session.py` 주석).

⚠ **옳은 비밀번호로 막힌 비활성 계정은 실패 제한 버킷을 쓰지 않는다.** 자격이 맞는데도
막힌 것은 추측이 아니기 때문이다. 비밀번호가 틀린 시도는 비활성이어도 그대로 센다 —
안 세면 「몇 번을 두드려도 429 가 안 온다」가 비활성 여부를 알려 준다.
"""
from __future__ import annotations

import uuid

import pytest
from conftest import TOKEN_PROF, auth
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

SECRET = "test-account-status-secret"
LAB_C = "0000000000000000000000000C"
INITIAL = "시험용-상태암호-123"
WRONG = "시험용-틀린암호-999"


def _email() -> str:
    return f"status-{uuid.uuid4().hex[:12]}@example.com"


def _create(client, email: str) -> str:
    made = client.post("/api/v1/admin/accounts", headers=auth(TOKEN_PROF), json={
        "email": email, "name": "상태 시험", "labId": LAB_C,
        "role": "연구원", "initialPassword": INITIAL,
    })
    assert made.status_code == 201, made.text
    return made.json()["accountId"]


def _status(admin_db_url: str, account_id: str, value: str | None = None) -> str:
    engine = create_engine(admin_db_url)
    try:
        with engine.begin() as db:
            if value is not None:
                db.execute(text(
                    "UPDATE account_admin.login_credential SET status=:s WHERE account_id=:id"),
                    {"s": value, "id": account_id})
            return db.execute(text(
                "SELECT status FROM account_admin.login_credential WHERE account_id=:id"),
                {"id": account_id}).scalar_one()
    finally:
        engine.dispose()


def test_new_credentials_start_active(p2_client, admin_db_url: str) -> None:
    client = p2_client(session_secret=SECRET)
    account_id = _create(client, _email())
    assert _status(admin_db_url, account_id) == "active"


def test_inactive_account_login_is_rejected_like_a_wrong_password(
    p2_client, admin_db_url: str,
) -> None:
    client = p2_client(session_secret=SECRET)
    email = _email()
    account_id = _create(client, email)
    assert client.post("/api/v1/sessions", json={
        "accountName": email, "password": INITIAL}).status_code == 201

    assert _status(admin_db_url, account_id, "inactive") == "inactive"
    denied = client.post("/api/v1/sessions", json={"accountName": email, "password": INITIAL})
    unknown = client.post("/api/v1/sessions", json={
        "accountName": _email(), "password": INITIAL})
    assert denied.status_code == 401, denied.text
    assert unknown.status_code == 401
    assert denied.json() == unknown.json(), "비활성 응답이 미등록 계정 응답과 갈린다 — 상태가 샌다."


def test_reactivation_restores_login(p2_client, admin_db_url: str) -> None:
    client = p2_client(session_secret=SECRET)
    email = _email()
    account_id = _create(client, email)
    _status(admin_db_url, account_id, "inactive")
    assert client.post("/api/v1/sessions", json={
        "accountName": email, "password": INITIAL}).status_code == 401
    _status(admin_db_url, account_id, "active")
    assert client.post("/api/v1/sessions", json={
        "accountName": email, "password": INITIAL}).status_code == 201


def test_inactive_rejection_does_not_consume_the_failure_bucket(
    p2_client, admin_db_url: str,
) -> None:
    client = p2_client(session_secret=SECRET, login_max_failures=1)
    email = _email()
    account_id = _create(client, email)
    _status(admin_db_url, account_id, "inactive")

    for _ in range(3):
        blocked = client.post("/api/v1/sessions", json={
            "accountName": email, "password": INITIAL})
        assert blocked.status_code == 401, blocked.text

    # 버킷 자체는 살아 있다 — 틀린 비밀번호 한 번이면 다음 시도가 429 다.
    assert client.post("/api/v1/sessions", json={
        "accountName": email, "password": WRONG}).status_code == 401
    assert client.post("/api/v1/sessions", json={
        "accountName": email, "password": INITIAL}).status_code == 429


def test_status_column_rejects_unknown_values(p2_client, admin_db_url: str) -> None:
    client = p2_client(session_secret=SECRET)
    account_id = _create(client, _email())
    with pytest.raises(IntegrityError):
        _status(admin_db_url, account_id, "삭제됨")
