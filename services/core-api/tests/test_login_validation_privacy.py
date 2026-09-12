"""로그인 입력 오류가 자격 원문을 응답이나 로그에 남기지 않는지 검증한다."""
from __future__ import annotations

import logging
import json

import pytest
from conftest import TOKEN_RES


SECRET = "test-login-validation-secret"
MARKER = "반사되면-안되는-자격-" + ("x" * 520)


class CountingIssuer:
    """실제 발급기를 감싸 입력 거절이 발급 경계를 넘는지만 센다."""

    def __init__(self, delegate) -> None:
        self.delegate = delegate
        self.calls = 0

    def rate_limit_key(self, attempt):
        return self.delegate.rate_limit_key(attempt)

    def issue(self, attempt):
        self.calls += 1
        return self.delegate.issue(attempt)


@pytest.fixture()
def client(p2_client):
    return p2_client(session_secret=SECRET)


@pytest.mark.parametrize(
    "request_kwargs",
    [
        {"json": {"accessCode": MARKER}},
        {"json": {"accountName": {"value": MARKER}, "password": "시험암호"}},
        {"json": {"accountName": "시험계정", "password": {"value": MARKER}}},
        {"json": {"accessCode": TOKEN_RES, "unexpected": MARKER}},
        {"content": '{"accessCode":"' + MARKER},
    ],
)
def test_로그인_validation_오류는_입력값을_응답과_로그에_반사하지_않는다(
    client, caplog, request_kwargs,
) -> None:
    caplog.set_level(logging.DEBUG)

    response = client.post("/api/v1/sessions", **request_kwargs)

    assert response.status_code == 400
    assert MARKER not in response.text
    assert MARKER not in caplog.text
    raw_errors = response.json()["details"]["errors"]
    assert isinstance(raw_errors, str)
    errors = json.loads(raw_errors)
    assert errors
    assert all(set(error) == {"type"} for error in errors)


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"accountName": "시험계정"},
        {"password": "시험암호"},
        {"accountName": "", "password": "시험암호"},
        {"accountName": "시험계정", "password": ""},
        {"accessCode": ""},
        {"accountName": "시험계정", "accessCode": TOKEN_RES},
        {"password": "시험암호", "accessCode": TOKEN_RES},
        {"accountName": "시험계정", "password": "시험암호", "accessCode": TOKEN_RES},
    ],
)
def test_완전하지_않거나_혼합된_로그인_형식은_인증_전에_400이다(
    p2_client, body,
) -> None:
    client = p2_client(session_secret=SECRET, login_max_failures=1)
    issuer = CountingIssuer(client.app.state.session_issuer)
    client.app.state.session_issuer = issuer

    assert client.post("/api/v1/sessions", json=body).status_code == 400
    assert issuer.calls == 0
    assert client.post(
        "/api/v1/sessions", json={"accessCode": "틀린-접속-코드"},
        headers={"x-forwarded-for": "198.51.100.11"},
    ).status_code == 401
    assert issuer.calls == 1


def test_선택하지_않은_로그인_필드의_null은_미지정으로_처리한다(client) -> None:
    by_code = client.post("/api/v1/sessions", json={
        "accessCode": TOKEN_RES, "accountName": None, "password": None,
    })

    assert by_code.status_code == 201


def test_비밀번호_로그인에서도_선택하지_않은_null은_미지정이다(
    p2_client, tmp_path,
) -> None:
    account_name = "null-field@example.com"
    password = "시험용-null-비밀번호"
    from colab_core.kernel.password import hash_password
    import json
    from conftest import ACC_A_RES, LAB_A

    entry = {"accountId": ACC_A_RES, "labId": LAB_A}
    entry.update(hash_password(password, n=1024).as_dict())
    path = tmp_path / "null-field-credentials.json"
    path.write_text(json.dumps({account_name: entry}), encoding="utf-8")

    response = p2_client(
        session_secret=SECRET, credentials_file=str(path),
    ).post("/api/v1/sessions", json={
        "accountName": account_name, "password": password, "accessCode": None,
    })

    assert response.status_code == 201, response.text


def test_accountName은_320자까지_인증기로_전달하고_321자는_400이다(client) -> None:
    name_320 = "a" * 308 + "@example.com"

    assert len(name_320) == 320
    assert client.post("/api/v1/sessions", json={
        "accountName": name_320, "password": "시험암호",
    }).status_code == 401
    assert client.post("/api/v1/sessions", json={
        "accountName": name_320 + "a", "password": "시험암호",
    }).status_code == 400
