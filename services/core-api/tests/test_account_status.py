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


# ── 다른 로그인 수단으로 도는 자리 ────────────────────────────────────────────
#
# ⚠ **비활성은 DB 자격 경로에만 걸려 있었다.** `login_sessions.issue_database` 하나가
# `status` 를 보고, 파일 자격(`TrackedPasswordIssuer`)·접속 코드(`TrackedPlantedCodeIssuer`)
# 는 그 열을 아예 열지 않는다. 같은 사람이 두 경로를 다 가지고 있으면 「비활성화했다」가
# 참이 아니게 된다 — 비활성화는 **계정**에 거는 것이지 자격 한 벌에 거는 것이 아니다.

def _plant_file(tmp_path, name: str, account_id: str, lab_id: str) -> str:
    """파일 자격 한 벌. **DB 자격과 이름이 다르고 계정은 같다** — 겹치는 실제 모양이다."""
    import json

    from colab_core.kernel.password import hash_password

    entry = {"accountId": account_id, "labId": lab_id}
    entry.update(hash_password(INITIAL, n=1024).as_dict())
    path = tmp_path / "legacy-credentials.json"
    path.write_text(json.dumps({name: entry}, ensure_ascii=False), encoding="utf-8")
    return str(path)


def test_inactive_account_cannot_log_in_through_the_legacy_file_credential(
    p2_client, admin_db_url: str, tmp_path,
) -> None:
    client = p2_client(session_secret=SECRET)
    account_id = _create(client, _email())
    legacy_name = "구자격-" + account_id[-6:]
    file_client = p2_client(
        session_secret=SECRET,
        credentials_file=_plant_file(tmp_path, legacy_name, account_id, LAB_C))

    assert file_client.post("/api/v1/sessions", json={
        "accountName": legacy_name, "password": INITIAL}).status_code == 201

    assert _status(admin_db_url, account_id, "inactive") == "inactive"
    denied = file_client.post("/api/v1/sessions", json={
        "accountName": legacy_name, "password": INITIAL})
    unknown = file_client.post("/api/v1/sessions", json={
        "accountName": _email(), "password": INITIAL})
    assert denied.status_code == 401, denied.text
    assert denied.json() == unknown.json(), "파일 자격의 비활성 거절이 미등록 응답과 갈린다."


def test_inactive_account_cannot_log_in_through_a_planted_access_code(
    p2_client, admin_db_url: str, tmp_path,
) -> None:
    import json

    client = p2_client(session_secret=SECRET)
    account_id = _create(client, _email())
    code = "planted-" + account_id[-8:]
    planted = tmp_path / "planted-subjects.json"
    planted.write_text(json.dumps(
        {code: {"accountId": account_id, "labId": LAB_C}}), encoding="utf-8")
    code_client = p2_client(session_secret=SECRET,
                            subjects_file_override=str(planted))

    assert code_client.post(
        "/api/v1/sessions", json={"accessCode": code}).status_code == 201

    assert _status(admin_db_url, account_id, "inactive") == "inactive"
    denied = code_client.post("/api/v1/sessions", json={"accessCode": code})
    unknown = code_client.post("/api/v1/sessions", json={"accessCode": "없는-코드"})
    assert denied.status_code == 401, denied.text
    assert denied.json() == unknown.json(), "접속 코드의 비활성 거절이 미등록 응답과 갈린다."
