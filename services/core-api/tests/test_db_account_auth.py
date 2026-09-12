from __future__ import annotations

from dataclasses import replace

from colab_core.kernel.auth import Subject
from colab_core.kernel.authn import DatabasePasswordIssuer, IssuerChain, LoginAttempt
from colab_core.kernel.db_credentials import DatabaseCredential
from colab_core.kernel.ids import Ulid
from colab_core.kernel.password import hash_password
from colab_core.kernel.session_token import DatabaseSessionSigner, SessionSigner


ACCOUNT = Ulid("000000000000000000000000A1")
LAB = Ulid("0000000000000000000000000A")
GOOD = "시험용-초기-비밀번호"


class Store:
    def __init__(self, record: DatabaseCredential | None):
        self.record = record

    def find(self, login_name: str):
        return self.record if login_name == "person@example.com" else None

    def dummy_verify(self, _password: str) -> None:
        pass


class Legacy:
    name = "legacy"

    def __init__(self):
        self.called = False

    def issue(self, _attempt):
        self.called = True
        return None


def record() -> DatabaseCredential:
    return DatabaseCredential(
        subject=Subject(ACCOUNT, LAB),
        login_name="person@example.com",
        password=hash_password(GOOD, n=1024),
        must_change_password=True,
        session_version=1,
    )


def test_db가_소유한_이메일의_암호실패는_legacy로_넘기지_않는다() -> None:
    legacy = Legacy()
    issuer = DatabasePasswordIssuer(Store(record()), DatabaseSessionSigner("secret", ttl_minutes=5))
    chain = IssuerChain((issuer, legacy))
    assert chain.issue(LoginAttempt(account_name=" Person@Example.com ", password="wrong")) is None
    assert legacy.called is False


def test_db에_없는_로그인이면_legacy가_받는다() -> None:
    legacy = Legacy()
    issuer = DatabasePasswordIssuer(Store(None), DatabaseSessionSigner("secret", ttl_minutes=5))
    IssuerChain((issuer, legacy)).issue(LoginAttempt(account_name="legacy", password="wrong"))
    assert legacy.called is True


def test_db_login_variants_share_one_rate_limit_bucket() -> None:
    chain = IssuerChain((DatabasePasswordIssuer(
        Store(record()), DatabaseSessionSigner("secret", ttl_minutes=5)),))
    keys = {chain.rate_limit_key(LoginAttempt(account_name=value, password="wrong"))
            for value in ("person@example.com", "Person@Example.com", " person@example.com ")}
    assert keys == {"name:person@example.com"}


def test_db_토큰은_목적과_version을_싣고_legacy_v1과_구분된다() -> None:
    signer = DatabaseSessionSigner("secret", ttl_minutes=5)
    issued = signer.issue(record())
    assert issued.token.startswith("db1.")
    claims = signer.verify(issued.token)
    assert claims is not None
    assert claims.must_change_password is True
    assert claims.session_version == 1
    assert signer.verify(issued.token.replace("db1.", "v1.", 1)) is None
    legacy = SessionSigner("secret", ttl_minutes=5)
    assert legacy.verify(issued.token.replace("db1.", "v1.", 1)) is None


def test_version이_바뀐_자격은_옛_토큰을_거부할_수_있다() -> None:
    signer = DatabaseSessionSigner("secret", ttl_minutes=5)
    old = signer.issue(record()).token
    claims = signer.verify(old)
    assert claims is not None
    assert claims.session_version != replace(record(), session_version=2).session_version
