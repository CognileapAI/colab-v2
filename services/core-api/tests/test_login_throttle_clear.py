"""운영자가 로그인 잠금을 푼다 — `clearLoginThrottle` (핫픽스 HF-B ②).

**엔드포인트가 유일한 길이다.** 시도 제한은 프로세스 메모리에 있고(`kernel/throttle.py`),
프로세스 밖의 스크립트·SQL 로는 그 dict 에 닿지 못한다. 종전에 잠긴 사람이 기다리는 것
말고 할 수 있는 일은 **웹 서버를 재시작하는 것**뿐이었고, 그것은 다른 모든 사용자의 셈까지
지우는 조치다.

여기서 재는 것 —
  ⓐ 운영자가 풀면 잠겼던 계정이 **곧바로** 로그인에 성공한다
  ⓑ 비운영자는 403 · 주체가 없으면 401 — 잠금 해제가 아무나 부를 수 있는 자리가 아니다
  ⓒ 없는 이메일도 **204** 다 — 응답으로 계정의 존재를 가르지 않는다
  ⓓ 한 사람의 해제가 **다른 사람의 셈을 지우지 않는다**
"""
from __future__ import annotations

import uuid

from conftest import TOKEN_PROF, TOKEN_RES, auth

SECRET = "test-session-secret-0123456789"
LAB_C = "0000000000000000000000000C"
PASSWORD = "시험용-초기암호-123"
WRONG = "틀린-비밀번호-999"
CLEAR = "/api/v1/admin/login-throttle/clear"


def _email(tag: str) -> str:
    """이메일은 회차마다 새로 짓는다 — 계정 행은 연구실 경계 밖이라 되돌리기가 훑지 않는다."""
    return f"{tag}-{uuid.uuid4().hex[:12]}@example.com"


def _make_account(client, email: str) -> None:
    made = client.post("/api/v1/admin/accounts", headers=auth(TOKEN_PROF), json={
        "email": email, "name": "잠금 시험 계정", "labId": LAB_C,
        "role": "연구원", "initialPassword": PASSWORD,
    })
    assert made.status_code == 201, made.text


def _login(client, email: str, password: str):
    return client.post("/api/v1/sessions",
                       json={"accountName": email, "password": password})


def _lock_out(client, email: str) -> None:
    for _ in range(5):
        assert _login(client, email, WRONG).status_code == 401
    assert _login(client, email, PASSWORD).status_code == 429, "잠기지 않았다 — 전제가 깨졌다."


# ═══════════════════ ⓐ 해제 뒤 곧바로 로그인이 선다 ═══════════════════════════
def test_an_operator_unlocks_a_locked_account(p2_client) -> None:
    client = p2_client(session_secret=SECRET, login_max_failures=5)
    EMAIL = _email("throttle-unlock")
    _make_account(client, EMAIL)
    _lock_out(client, EMAIL)
    cleared = client.post(CLEAR, headers=auth(TOKEN_PROF), json={"email": EMAIL})
    assert cleared.status_code == 204, cleared.text
    ok = _login(client, EMAIL, PASSWORD)
    assert ok.status_code == 201, f"해제했는데 여전히 막혀 있다: {ok.text}"


def test_the_email_is_normalised_the_same_way_login_normalises_it(p2_client) -> None:
    """**로그인이 세는 열쇠와 해제가 지우는 열쇠가 같은 함수로 만들어진다.**

    다르면 해제가 조용히 아무것도 안 지우고 204 만 낸다 — 가장 나쁜 실패 모양이다.
    """
    client = p2_client(session_secret=SECRET, login_max_failures=5)
    EMAIL = _email("throttle-normalise")
    _make_account(client, EMAIL)
    _lock_out(client, EMAIL)
    cleared = client.post(CLEAR, headers=auth(TOKEN_PROF),
                          json={"email": "  " + EMAIL.upper() + "  "})
    assert cleared.status_code == 204, cleared.text
    assert _login(client, EMAIL, PASSWORD).status_code == 201


# ═══════════════════ ⓑ 아무나 부르는 자리가 아니다 ════════════════════════════
def test_a_non_operator_is_refused(p2_client) -> None:
    client = p2_client(session_secret=SECRET, login_max_failures=5)
    EMAIL = _email("throttle-nonop")
    denied = client.post(CLEAR, headers=auth(TOKEN_RES), json={"email": EMAIL})
    assert denied.status_code == 403, denied.text


def test_an_anonymous_caller_is_refused(p2_client) -> None:
    client = p2_client(session_secret=SECRET, login_max_failures=5)
    assert client.post(CLEAR, json={"email": _email("throttle-anon")}).status_code == 401


def test_the_body_takes_nothing_but_an_email(p2_client) -> None:
    """**넓히지 않았음을 함께 잰다** — 지울 열쇠를 호출자가 지어내지 못한다."""
    client = p2_client(session_secret=SECRET, login_max_failures=5)
    extra = client.post(CLEAR, headers=auth(TOKEN_PROF),
                        json={"email": _email("throttle-extra"),
                              "clientKey": "client:203.0.113.9"})
    assert extra.status_code == 400, extra.text


# ═══════════════════ ⓒ 존재를 가르지 않는다 ═══════════════════════════════════
def test_an_unknown_email_answers_the_same_204(p2_client) -> None:
    client = p2_client(session_secret=SECRET, login_max_failures=5)
    unknown = client.post(CLEAR, headers=auth(TOKEN_PROF),
                          json={"email": _email("아무도-아닌")})
    assert unknown.status_code == 204, \
        "없는 계정을 다른 답으로 가르면 그 자리가 계정 열거 통로가 된다."


# ═══════════════════ ⓓ 남의 셈을 지우지 않는다 ════════════════════════════════
def test_clearing_one_account_leaves_the_others_counted(p2_client) -> None:
    client = p2_client(session_secret=SECRET, login_max_failures=5)
    EMAIL, OTHER = _email("throttle-one"), _email("throttle-other")
    _make_account(client, EMAIL)
    _make_account(client, OTHER)
    _lock_out(client, EMAIL)
    _lock_out(client, OTHER)
    assert client.post(CLEAR, headers=auth(TOKEN_PROF),
                       json={"email": EMAIL}).status_code == 204
    assert _login(client, EMAIL, PASSWORD).status_code == 201
    assert _login(client, OTHER, PASSWORD).status_code == 429, \
        "한 계정의 해제가 다른 계정의 셈까지 지웠다."
