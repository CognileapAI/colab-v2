"""로그인·로그아웃 실동작 증명 (`PLAN-SoT §9 〈90〉` · WU-AUTH).

**red 를 먼저 봤다.** 이 파일이 붙은 시점에 `POST /api/v1/sessions` 는 라우트가 없었고,
`test_route_table.py` 도 「계약에 있는 오퍼레이션을 앱이 등록하지 않았다」로 red 였다.

여기서 증명하는 것 — 성공 · 실패 · 미인증 401 · 만료 · 로그아웃 뒤 401 ·
**cross-tenant 음성**(A 로 발급한 세션으로 B 자원 접근 불가) · **기존 주체 표 병존**.
"""
from __future__ import annotations

import datetime as dt

import pytest
from conftest import ACC_A_RES, DS_B1, LAB_A, TOKEN_RES, auth

from colab_core.kernel.auth import Subject
from colab_core.kernel.ids import Ulid
from colab_core.kernel.session_token import SessionSigner

SECRET = "test-session-secret-0123456789"


@pytest.fixture()
def client(p2_client):
    return p2_client(session_secret=SECRET)


def _login(client, code: str):
    return client.post("/api/v1/sessions", json={"accessCode": code})


# ── 발급 ────────────────────────────────────────────────────────────────────────

def test_로그인_성공은_201_과_토큰이다(client) -> None:
    res = _login(client, TOKEN_RES)
    assert res.status_code == 201, res.text
    body = res.json()
    assert set(body) == {"token", "expiresAt"}
    assert body["token"]
    # 만료 시각은 미래다 — 발급하자마자 죽은 세션을 내리지 않는다.
    assert dt.datetime.fromisoformat(body["expiresAt"]) > dt.datetime.now(dt.timezone.utc)


def test_모르는_접속코드는_401_이고_계정을_만들지_않는다(client) -> None:
    """**회원가입이 아니다** (P-17). 표에 없는 코드는 그냥 거절이다."""
    res = _login(client, "심어-두지-않은-코드")
    assert res.status_code == 401
    assert res.json()["code"] == "UNAUTHORIZED"


def test_빈_접속코드는_400_이다(client) -> None:
    res = _login(client, "")
    assert res.status_code == 400


def test_로그인은_주체_없이_부를_수_있다(client) -> None:
    """`security: []` — 이 seam 에서 유일한 예외다. 헤더 없이 201 이어야 로그인이 성립한다."""
    assert _login(client, TOKEN_RES).status_code == 201


# ── 발급한 세션으로 실제 op 을 부른다 ───────────────────────────────────────────

def test_발급한_세션으로_me_가_열린다(client) -> None:
    token = _login(client, TOKEN_RES).json()["token"]
    res = client.get("/api/v1/me", headers=auth(token))
    assert res.status_code == 200, res.text
    assert res.json()["accountId"] == ACC_A_RES


def test_기존_주체_표_토큰도_그대로_통한다(client) -> None:
    """병존 (`〈90〉-㉱`). 로그인을 세우면서 도구·시험의 경로를 끊지 않는다."""
    assert client.get("/api/v1/me", headers=auth(TOKEN_RES)).status_code == 200


def test_미인증은_401_이다(client) -> None:
    assert client.get("/api/v1/me").status_code == 401


def test_서명이_틀린_토큰은_401_이다(client) -> None:
    token = _login(client, TOKEN_RES).json()["token"]
    forged = token[:-1] + ("A" if token[-1] != "A" else "B")
    assert client.get("/api/v1/me", headers=auth(forged)).status_code == 401


def test_만료된_세션은_401_이다(client) -> None:
    """수명이 지난 서명은 **서명이 맞아도** 주체가 되지 않는다."""
    expired = SessionSigner(SECRET, ttl_minutes=1).issue(
        Subject(account_id=Ulid(ACC_A_RES), lab_id=Ulid(LAB_A)),
        now=dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2))
    assert client.get("/api/v1/me", headers=auth(expired.token)).status_code == 401


# ── 경계 ────────────────────────────────────────────────────────────────────────

def test_A_세션으로_B_연구실_자원에_닿지_않는다(client) -> None:
    """cross-tenant 음성. 경계는 **요청이 아니라 주체**에서 나온다 (`CLAUDE.md §3-5`)."""
    token = _login(client, TOKEN_RES).json()["token"]
    res = client.get(f"/api/v1/datasets/{DS_B1}", headers=auth(token))
    assert res.status_code == 404, "경계 밖은 403 이 아니라 404 다 (P-9·P-10)."


def test_세션_토큰에_lab_을_실어도_경계가_바뀌지_않는다(client) -> None:
    """다른 연구실 lab 을 담은 토큰은 **서명이 안 맞아** 통째로 거절된다."""
    from conftest import LAB_B
    forged = SessionSigner("다른-비밀값", ttl_minutes=60).issue(
        Subject(account_id=Ulid(ACC_A_RES), lab_id=Ulid(LAB_B)))
    assert client.get("/api/v1/me", headers=auth(forged.token)).status_code == 401


# ── 로그아웃 ────────────────────────────────────────────────────────────────────

def test_로그아웃은_204_다(client) -> None:
    token = _login(client, TOKEN_RES).json()["token"]
    assert client.delete("/api/v1/sessions/current", headers=auth(token)).status_code == 204


def test_로그아웃도_주체를_요구한다(client) -> None:
    assert client.delete("/api/v1/sessions/current").status_code == 401


def test_토큰을_버린_뒤에는_401_이다(client) -> None:
    """로그아웃의 실체 = 화면이 토큰을 버리는 것. 버린 뒤 요청은 미인증과 같다 (`〈90〉-㉳`)."""
    token = _login(client, TOKEN_RES).json()["token"]
    client.delete("/api/v1/sessions/current", headers=auth(token))
    assert client.get("/api/v1/me").status_code == 401


# ── 설정이 없을 때 ──────────────────────────────────────────────────────────────

def test_비밀값이_없으면_로그인이_정직하게_실패한다(p2_client) -> None:
    """서명 비밀값 없이 세션을 만들지 않는다. **200 으로 가짜 토큰을 내리지 않는다.**"""
    res = _login(p2_client(session_secret=None), TOKEN_RES)
    assert res.status_code == 500
    assert res.json()["code"] == "SESSION_UNAVAILABLE"


def test_비밀값이_없어도_기존_주체_표는_돈다(p2_client) -> None:
    client = p2_client(session_secret=None)
    assert client.get("/api/v1/me", headers=auth(TOKEN_RES)).status_code == 200
