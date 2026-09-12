from __future__ import annotations

import datetime as dt
from conftest import LAB_A, TOKEN_PROF, TOKEN_RES, auth
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from concurrent.futures import ThreadPoolExecutor

SECRET = "test-stage3-session-secret"
EMAIL = "stage3-user@example.com"
LAB_C = "0000000000000000000000000C"
INITIAL = "시험용-초기암호-123"
NEW = "시험용-새암호-456"
LONG_EMAIL = ("a" * 125) + "@example.com"

@pytest.mark.parametrize("table", ["login_credential", "service_operator", "login_session"])
def test_ordinary_app_role_cannot_read_global_account_registry(
    app_db_url: str, table: str,
) -> None:
    engine = create_engine(app_db_url)
    try:
        with engine.connect() as connection:
            with pytest.raises(ProgrammingError) as denied:
                connection.execute(text(f"SELECT 1 FROM account_admin.{table}"))
            assert denied.value.orig.sqlstate == "42501"
    finally:
        engine.dispose()

def test_createServiceAccount_changeOwnPassword_getAccountOptions(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    assert client.get("/api/v1/admin/account-options", headers=auth(TOKEN_RES)).status_code == 403
    options = client.get("/api/v1/admin/account-options", headers=auth(TOKEN_PROF))
    assert options.status_code == 200
    assert LAB_C in {row["labId"] for row in options.json()["labs"]}

    made = client.post("/api/v1/admin/accounts", headers=auth(TOKEN_PROF), json={
        "email": EMAIL, "name": "Stage 3 사용자", "labId": LAB_C,
        "role": "연구원", "initialPassword": INITIAL,
    })
    assert made.status_code == 201, made.text
    assert "initialPassword" not in made.json()
    duplicate = client.post("/api/v1/admin/accounts", headers=auth(TOKEN_PROF), json={
        "email": EMAIL.upper(), "name": "중복", "labId": LAB_C,
        "role": "연구원", "initialPassword": INITIAL,
    })
    assert duplicate.status_code == 409
    invalid = client.post("/api/v1/admin/accounts", headers=auth(TOKEN_PROF), json={
        "email": "bad@@example.com", "name": "잘못된 이메일", "labId": LAB_C,
        "role": "연구원", "initialPassword": INITIAL,
    })
    assert invalid.status_code == 400

    assert len(LONG_EMAIL) == 137
    long_account = client.post("/api/v1/admin/accounts", headers=auth(TOKEN_PROF), json={
        "email": LONG_EMAIL, "name": "긴 이메일 사용자", "labId": LAB_C,
        "role": "연구원", "initialPassword": INITIAL,
    })
    assert long_account.status_code == 201, long_account.text
    long_login = client.post("/api/v1/sessions", json={
        "accountName": LONG_EMAIL, "password": INITIAL,
    })
    assert long_login.status_code == 201, long_login.text

    login = client.post("/api/v1/sessions", json={"accountName": EMAIL.upper(), "password": INITIAL})
    assert login.status_code == 201, login.text
    login_body = login.json()
    assert set(login_body) == {"token", "expiresAt", "sessionId", "revocationToken"}
    restricted = login_body["token"]
    assert client.get("/api/v1/lab", headers=auth(restricted)).status_code == 403
    me = client.get("/api/v1/me", headers=auth(restricted))
    assert me.status_code == 200 and me.json()["mustChangePassword"] is True
    same = client.put("/api/v1/me/password", headers=auth(restricted), json={
        "newPassword": INITIAL,
    })
    assert same.status_code == 400
    changed = client.put("/api/v1/me/password", headers=auth(restricted), json={
        "newPassword": NEW,
    })
    assert changed.status_code == 200, changed.text
    assert changed.json()["sessionId"] == login_body["sessionId"]
    assert changed.json()["expiresAt"] == login_body["expiresAt"]
    normal = changed.json()["token"]
    assert client.get("/api/v1/me", headers=auth(restricted)).status_code == 401
    assert client.get("/api/v1/lab", headers=auth(normal)).status_code == 200
    assert client.put("/api/v1/me/password", headers=auth(restricted), json={
        "newPassword": "다시-바꾸려는-비밀번호-789",
    }).status_code == 401
    assert client.put("/api/v1/me/password", headers=auth(normal), json={
        "newPassword": "다시-바꾸려는-비밀번호-789",
    }).status_code == 403
    assert client.post("/api/v1/sessions", json={"accountName": EMAIL, "password": INITIAL}).status_code == 401
    first = client.post("/api/v1/sessions", json={"accountName": EMAIL, "password": NEW})
    second = client.post("/api/v1/sessions", json={"accountName": EMAIL, "password": NEW})
    assert first.status_code == second.status_code == 201
    assert client.delete("/api/v1/sessions/current", headers=auth(first.json()["token"])).status_code == 204
    assert client.get("/api/v1/me", headers=auth(first.json()["token"])).status_code == 401
    assert client.get("/api/v1/me", headers=auth(second.json()["token"])).status_code == 200
    assert client.post("/api/v1/sessions/revoke", json={
        "revocationToken": second.json()["revocationToken"],
    }).status_code == 204
    assert client.get("/api/v1/me", headers=auth(second.json()["token"])).status_code == 401


def test_session_expiry_is_fixed_and_revocation_survives_app_restart(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    first = client.post("/api/v1/sessions", json={"accessCode": TOKEN_RES})
    assert first.status_code == 201
    issued = first.json()
    expires = dt.datetime.fromisoformat(issued["expiresAt"])
    assert dt.timedelta(hours=11, minutes=59) < expires - dt.datetime.now(dt.timezone.utc) <= dt.timedelta(hours=12)
    assert client.post("/api/v1/sessions/revoke", json={
        "revocationToken": issued["revocationToken"],
    }).status_code == 204
    restarted = p2_client(session_secret=SECRET)
    assert restarted.get("/api/v1/me", headers=auth(issued["token"])).status_code == 401


def test_two_initial_sessions_and_concurrent_change_allow_only_one(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    email = "stage3-concurrent@example.com"
    made = client.post("/api/v1/admin/accounts", headers=auth(TOKEN_PROF), json={
        "email": email, "name": "동시 변경", "labId": LAB_C,
        "role": "연구원", "initialPassword": INITIAL,
    })
    assert made.status_code == 201, made.text
    first = client.post("/api/v1/sessions", json={"accountName": email, "password": INITIAL})
    second = client.post("/api/v1/sessions", json={"accountName": email, "password": INITIAL})
    assert first.status_code == second.status_code == 201
    assert client.get("/api/v1/lab", headers=auth(first.json()["token"])).status_code == 403

    def change(token: str, suffix: str) -> int:
        return client.put("/api/v1/me/password", headers=auth(token), json={
            "newPassword": f"동시-새비밀번호-{suffix}-123",
        }).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted(pool.map(
            lambda pair: change(*pair),
            ((first.json()["token"], "A"), (second.json()["token"], "B")),
        ))
    assert statuses == [200, 401]
    assert client.get("/api/v1/me", headers=auth(first.json()["token"])).status_code == 401
    assert client.get("/api/v1/me", headers=auth(second.json()["token"])).status_code == 401

