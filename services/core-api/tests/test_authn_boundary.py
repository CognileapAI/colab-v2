"""인증 경계 자체의 증명 — **교체 지점이 하나인가** (`PLAN-SoT §9 〈90〉-㉮`).

DB 를 쓰지 않는다. 여기서 보는 것은 「수단을 하나 더해도 요청 경계가 안 바뀐다」는 성질이다.
"""
from __future__ import annotations

import datetime as dt

import pytest

from colab_core.kernel import authn
from colab_core.kernel.auth import Subject, SubjectRegistry
from colab_core.kernel.ids import Ulid
from colab_core.kernel.session_token import SessionSigner

LAB = Ulid("0000000000000000000000000A")
ACC = Ulid("000000000000000000000000A1")
SUBJECT = Subject(account_id=ACC, lab_id=LAB)
REGISTRY = SubjectRegistry({"심어둔-코드": SUBJECT})


def signer() -> SessionSigner:
    return SessionSigner("비밀값-0123456789", ttl_minutes=60)


# ── 사슬 ────────────────────────────────────────────────────────────────────────

def test_비밀값이_없으면_어댑터가_하나다() -> None:
    chain, issuer = authn.build(registry=REGISTRY, signer=None)
    assert [a.name for a in chain.adapters] == ["planted-subject-table"]
    assert issuer is None


def test_비밀값이_있으면_두_수단이_병존한다() -> None:
    chain, issuer = authn.build(registry=REGISTRY, signer=signer())
    assert [a.name for a in chain.adapters] == ["planted-subject-table", "signed-session"]
    assert issuer is not None
    # 심어 둔 코드와 발급된 세션이 **같은 주체**로 판정된다.
    assert chain.resolve("심어둔-코드") == SUBJECT
    issued = issuer.issue(authn.LoginAttempt(access_code="심어둔-코드"))
    assert chain.resolve(issued.token) == SUBJECT


def test_빈_사슬은_모두_거부한다() -> None:
    """「검사할 것이 없으니 통과」를 만들지 않는다 (`CLAUDE.md §4`)."""
    assert authn.AuthenticatorChain(()).resolve("무엇이든") is None


def test_사슬은_수단을_더해도_같은_형태다() -> None:
    """다음 수단(구글 등)은 어댑터 하나로 들어온다 — 요청 경계는 안 바뀐다."""

    class 가짜IdP:
        name = "fake-idp"

        def authenticate(self, token: str) -> Subject | None:
            return SUBJECT if token == "idp-토큰" else None

    chain = authn.AuthenticatorChain((authn.StaticTokenAuthenticator(REGISTRY), 가짜IdP()))
    assert chain.resolve("idp-토큰") == SUBJECT
    assert chain.resolve("심어둔-코드") == SUBJECT
    assert chain.resolve("아무것도-아님") is None


def test_발급기는_표에_없는_코드로_계정을_만들지_않는다() -> None:
    _, issuer = authn.build(registry=REGISTRY, signer=signer())
    assert issuer.issue(authn.LoginAttempt(access_code="없는-코드")) is None


def test_시도_식별자에_비밀번호가_들어가지_않는다() -> None:
    """제한이 세는 키가 로그·메모리에 남아도 비밀번호는 새지 않는다 (`〈108〉-㉰`)."""
    attempt = authn.LoginAttempt(account_name="colab", password="비밀")
    assert "비밀" not in attempt.key


# ── 서명 토큰 ───────────────────────────────────────────────────────────────────

def test_서명이_다른_비밀값이면_거절한다() -> None:
    token = signer().issue(SUBJECT).token
    assert SessionSigner("다른-비밀값", ttl_minutes=60).verify(token) is None


def test_페이로드를_고치면_거절한다() -> None:
    token = signer().issue(SUBJECT).token
    head, payload, mac = token.split(".")
    tampered = f"{head}.{payload[:-1]}{'A' if payload[-1] != 'A' else 'B'}.{mac}"
    assert signer().verify(tampered) is None


def test_만료가_지나면_거절한다() -> None:
    s = signer()
    issued = s.issue(SUBJECT, now=dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=3))
    assert s.verify(issued.token) is None


def test_형식이_아니면_거절한다() -> None:
    s = signer()
    for bad in ("", "v1", "v1.a", "v2.a.b", "a.b.c", "심어둔-코드"):
        assert s.verify(bad) is None, bad


def test_토큰은_권한을_담지_않는다() -> None:
    """권한은 언제나 DB 에서 읽는다 (P-6·P-7). 토큰에 담기면 값이 두 곳으로 갈라진다."""
    import base64
    import json
    payload = signer().issue(SUBJECT).token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    assert set(claims) == {"sub", "lab", "exp"}


def test_비밀값이_비면_서명기를_만들지_못한다() -> None:
    with pytest.raises(ValueError):
        SessionSigner("", ttl_minutes=60)


def test_수명이_0_이하면_서명기를_만들지_못한다() -> None:
    with pytest.raises(ValueError):
        SessionSigner("비밀값", ttl_minutes=0)
