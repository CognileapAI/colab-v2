"""운영자 백오피스 — 계정 목록 · 비밀번호 재설정 · 비활성화/재활성화.

세 경로 전부 `account_admin.service_operator` 행이 있는 주체만 통과한다. 목록은 **전 연구실
한 벌**이며, 그것이 의도임을 여기서 못 박는다 — 다른 화면의 연구실 경계와 달리 이 경로는
등재된 예외다.

전 기기 종료는 새 저장 방식을 만들지 않는다. 기존 `session_version`(서명의
`credential_version`) 대조를 그대로 쓰고, 같은 트랜잭션에서 그 계정의 `login_session` 행에
`revoked_at` 을 채운다.
"""
from __future__ import annotations

import logging
import uuid

from conftest import ACC_A_PROF, LAB_A, TOKEN_PROF, TOKEN_RES, auth
from sqlalchemy import create_engine, text

SECRET = "test-account-backoffice-secret"
LAB_C = "0000000000000000000000000C"
INITIAL = "시험용-백오피스-초기암호-123"
RESET = "시험용-백오피스-재설정암호-456"


def _email(tag: str = "bo") -> str:
    return f"{tag}-{uuid.uuid4().hex[:12]}@example.com"


def _create(client, email: str, *, lab: str = LAB_C, role: str = "연구원") -> str:
    made = client.post("/api/v1/admin/accounts", headers=auth(TOKEN_PROF), json={
        "email": email, "name": "백오피스 시험", "labId": lab,
        "role": role, "initialPassword": INITIAL,
    })
    assert made.status_code == 201, made.text
    return made.json()["accountId"]


def _login(client, email: str, password: str = INITIAL):
    return client.post("/api/v1/sessions", json={"accountName": email, "password": password})


def _credential(admin_db_url: str, account_id: str) -> dict:
    engine = create_engine(admin_db_url)
    try:
        with engine.connect() as db:
            row = db.execute(text(
                "SELECT session_version, must_change_password, status"
                "  FROM account_admin.login_credential WHERE account_id=:id"),
                {"id": account_id}).mappings().first()
    finally:
        engine.dispose()
    assert row is not None
    return dict(row)


def _account_row_count(admin_db_url: str, account_id: str) -> int:
    engine = create_engine(admin_db_url)
    try:
        with engine.connect() as db:
            return db.execute(text("SELECT count(*) FROM d1_account WHERE id=:id"),
                              {"id": account_id}).scalar_one()
    finally:
        engine.dispose()


# ═════════════════════════════ 목록 ═════════════════════════════
# ⚠ **시험 계정을 `LAB_A`·`LAB_B` 에 만들지 않는다.** 두 연구실의 구성원 수를
# `test_live_endpoints.py::test_get_lab_is_scoped`(2·1)와 `test_lab_members.py` 가 세고 있어,
# 같은 worker DB 를 쓰는 직렬 실행에서 그 둘이 실제로 깨졌다. 발급 시험 연구실(`LAB_C`)만 쓴다.
def test_listServiceAccounts_is_not_scoped_to_the_operator_lab(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    signed_in = _email("listed")
    never = _email("never")
    _create(client, signed_in, role="연구원")
    _create(client, never, role="교수")
    _login(client, signed_in)

    listed = client.get("/api/v1/admin/accounts", headers=auth(TOKEN_PROF))
    assert listed.status_code == 200, listed.text
    rows = {row["email"]: row for row in listed.json()["accounts"]}
    # 운영자는 `LAB_A` 소속인데 `LAB_C` 계정이 목록에 있다 — 이 경로는 연구실 경계를 걸지 않는다.
    assert signed_in in rows and never in rows, "목록이 운영자 연구실로 좁혀졌다."
    assert set(rows[signed_in]) == {
        "accountId", "email", "name", "labId", "labName", "role", "status", "lastLoginAt",
        # 관리자 표시 — 목록 행이 토글의 현재 상태를 들고 온다 (intent 2026-09-12 운영자 지정).
        "operator",
    }
    assert rows[signed_in]["role"] == "연구원" and rows[never]["role"] == "교수"
    assert rows[signed_in]["labId"] == LAB_C
    assert rows[signed_in]["labName"] == "계정 발급 시험 연구실"
    assert rows[signed_in]["status"] == "active"
    assert rows[signed_in]["lastLoginAt"] is not None, "최근 로그인이 login_session 집계로 안 채워졌다."
    assert rows[never]["lastLoginAt"] is None

    other_lab = client.get("/api/v1/admin/accounts", headers=auth(TOKEN_PROF),
                           params={"labId": LAB_A})
    assert other_lab.status_code == 200
    assert signed_in not in {row["email"] for row in other_lab.json()["accounts"]}


def test_listServiceAccounts_filters_by_lab_status_role_and_email(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    researcher = _email("filter-res")
    professor = _email("filter-prof")
    researcher_id = _create(client, researcher, role="연구원")
    _create(client, professor, role="교수")
    assert client.post(f"/api/v1/admin/accounts/{researcher_id}/status",
                       headers=auth(TOKEN_PROF), json={"status": "inactive"}).status_code == 200

    def emails(**params) -> set[str]:
        got = client.get("/api/v1/admin/accounts", headers=auth(TOKEN_PROF), params=params)
        assert got.status_code == 200, got.text
        return {row["email"] for row in got.json()["accounts"]}

    assert {researcher, professor} <= emails(labId=LAB_C)
    assert researcher in emails(status="inactive") and professor not in emails(status="inactive")
    assert professor in emails(role="교수") and researcher not in emails(role="교수")
    assert emails(email=researcher.split("@")[0][:14]) == {researcher}


def test_backoffice_paths_are_operator_only(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    account_id = _create(client, _email("forbidden"))
    assert client.get("/api/v1/admin/accounts", headers=auth(TOKEN_RES)).status_code == 403
    assert client.post(f"/api/v1/admin/accounts/{account_id}/password-reset",
                       headers=auth(TOKEN_RES), json={"newPassword": RESET}).status_code == 403
    assert client.post(f"/api/v1/admin/accounts/{account_id}/status",
                       headers=auth(TOKEN_RES), json={"status": "inactive"}).status_code == 403


# ═════════════════════════════ 재설정 ═════════════════════════════
def test_resetServiceAccountPassword_forces_change_and_ends_every_session(
    p2_client, admin_db_url: str, caplog,
) -> None:
    client = p2_client(session_secret=SECRET)
    email = _email("reset")
    other_email = _email("bystander")
    account_id = _create(client, email)
    _create(client, other_email)

    first = _login(client, email)
    second = _login(client, email)
    assert first.status_code == second.status_code == 201
    bystander = _login(client, other_email)
    assert bystander.status_code == 201
    before = _credential(admin_db_url, account_id)

    with caplog.at_level(logging.DEBUG):
        reset = client.post(f"/api/v1/admin/accounts/{account_id}/password-reset",
                            headers=auth(TOKEN_PROF), json={"newPassword": RESET})
    assert reset.status_code == 200, reset.text
    assert RESET not in reset.text, "재설정 비밀번호가 응답 본문에 실렸다."
    assert RESET not in caplog.text, "재설정 비밀번호가 로그에 남았다."

    after = _credential(admin_db_url, account_id)
    assert after["session_version"] == before["session_version"] + 1
    assert after["must_change_password"] is True

    assert client.get("/api/v1/me", headers=auth(first.json()["token"])).status_code == 401
    assert client.get("/api/v1/me", headers=auth(second.json()["token"])).status_code == 401
    assert client.get("/api/v1/me", headers=auth(bystander.json()["token"])).status_code == 200

    assert _login(client, email, INITIAL).status_code == 401
    again = _login(client, email, RESET)
    assert again.status_code == 201, again.text
    me = client.get("/api/v1/me", headers=auth(again.json()["token"]))
    assert me.status_code == 200 and me.json()["mustChangePassword"] is True
    assert client.get("/api/v1/lab", headers=auth(again.json()["token"])).status_code == 403


def test_resetServiceAccountPassword_rejects_a_short_password(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    account_id = _create(client, _email("short"))
    assert client.post(f"/api/v1/admin/accounts/{account_id}/password-reset",
                       headers=auth(TOKEN_PROF), json={"newPassword": "짧다"}).status_code == 400


def test_resetServiceAccountPassword_rejects_a_bad_id_and_a_missing_credential(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    assert client.post("/api/v1/admin/accounts/정규-ID-아님/password-reset",
                       headers=auth(TOKEN_PROF), json={"newPassword": RESET}).status_code == 400
    assert client.post(f"/api/v1/admin/accounts/{ACC_A_PROF}/password-reset",
                       headers=auth(TOKEN_PROF), json={"newPassword": RESET}).status_code == 404


# ═════════════════════════════ 비활성화 ═════════════════════════════
def test_setServiceAccountStatus_blocks_login_ends_sessions_and_keeps_rows(
    p2_client, admin_db_url: str,
) -> None:
    client = p2_client(session_secret=SECRET)
    email = _email("deactivate")
    account_id = _create(client, email)
    session = _login(client, email)
    assert session.status_code == 201
    before = _credential(admin_db_url, account_id)

    off = client.post(f"/api/v1/admin/accounts/{account_id}/status",
                      headers=auth(TOKEN_PROF), json={"status": "inactive"})
    assert off.status_code == 200, off.text
    assert off.json()["status"] == "inactive"

    after = _credential(admin_db_url, account_id)
    assert after["status"] == "inactive"
    assert after["session_version"] == before["session_version"] + 1
    assert client.get("/api/v1/me", headers=auth(session.json()["token"])).status_code == 401
    assert _login(client, email).status_code == 401
    assert _account_row_count(admin_db_url, account_id) == 1, "비활성화가 계정 행을 지웠다."

    on = client.post(f"/api/v1/admin/accounts/{account_id}/status",
                     headers=auth(TOKEN_PROF), json={"status": "active"})
    assert on.status_code == 200 and on.json()["status"] == "active"
    assert _login(client, email).status_code == 201


def test_operator_cannot_deactivate_itself(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    refused = client.post(f"/api/v1/admin/accounts/{ACC_A_PROF}/status",
                          headers=auth(TOKEN_PROF), json={"status": "inactive"})
    assert refused.status_code == 400, refused.text


def test_setServiceAccountStatus_rejects_an_unknown_value(p2_client) -> None:
    client = p2_client(session_secret=SECRET)
    account_id = _create(client, _email("badstatus"))
    assert client.post(f"/api/v1/admin/accounts/{account_id}/status",
                       headers=auth(TOKEN_PROF), json={"status": "삭제됨"}).status_code == 400
