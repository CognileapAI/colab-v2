from __future__ import annotations

import datetime as dt
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from colab_core.kernel.auth import Subject
from colab_core.kernel.ids import Ulid
from colab_core.kernel.session_token import SessionSigner
from colab_core.kernel.login_sessions import LoginSessionStore, SessionStoreUnavailable
from colab_core.kernel.password import hash_password
from colab_core.kernel.db import make_session_factory


ACCOUNT = Ulid("000000000000000000000000A1")
LAB = Ulid("0000000000000000000000000A")
NOW = dt.datetime(2026, 9, 12, 0, 0, tzinfo=dt.timezone.utc)


def test_ss1_claims_bind_server_session_fields() -> None:
    signer = SessionSigner("secret", ttl_minutes=720)
    issued = signer.issue_tracked(
        Subject(ACCOUNT, LAB),
        session_id=Ulid("0000000000000000000000SES1"),
        generation=1,
        credential_kind="planted-code",
        purpose="normal",
        credential_version=None,
        expires_at=NOW + dt.timedelta(hours=12),
    )
    claims = signer.verify_tracked(issued.token, now=NOW)
    assert claims is not None
    assert claims.session_id == Ulid("0000000000000000000000SES1")
    assert claims.credential_kind == "planted-code"
    assert claims.purpose == "normal"
    assert claims.credential_version is None


def test_database_ss1_requires_credential_version() -> None:
    signer = SessionSigner("secret", ttl_minutes=720)
    with pytest.raises(ValueError):
        signer.issue_tracked(
            Subject(ACCOUNT, LAB),
            session_id=Ulid("0000000000000000000000SES2"),
            generation=1,
            credential_kind="database",
            purpose="password-change",
            credential_version=None,
            expires_at=NOW + dt.timedelta(hours=12),
        )


def test_old_stateless_tokens_are_not_tracked_browser_sessions() -> None:
    signer = SessionSigner("secret", ttl_minutes=720)
    old = signer.issue(Subject(ACCOUNT, LAB), now=NOW)
    assert signer.verify_tracked(old.token, now=NOW) is None


class BrokenFactory:
    def __call__(self):
        raise OperationalError("select", {}, RuntimeError("down"))

    def begin(self):
        raise OperationalError("insert", {}, RuntimeError("down"))


def test_store_failure_is_not_reported_as_bad_credentials() -> None:
    signer = SessionSigner("secret", ttl_minutes=720)
    store = LoginSessionStore(BrokenFactory(), signer, ttl_minutes=720)
    with pytest.raises(SessionStoreUnavailable):
        store.issue(
            Subject(ACCOUNT, LAB), credential_kind="planted-code",
            credential_version=None, purpose="normal", now=NOW,
        )
    token = signer.issue_tracked(
        Subject(ACCOUNT, LAB), session_id=Ulid("0000000000000000000000SES3"),
        generation=1, credential_kind="planted-code", purpose="normal",
        credential_version=None, expires_at=NOW + dt.timedelta(hours=12),
    ).token
    with pytest.raises(SessionStoreUnavailable):
        store.authenticate(token, now=NOW)
    with pytest.raises(SessionStoreUnavailable):
        store.revoke_by_capability("x" * 43, now=NOW)


def test_exact_expiry_and_current_lab_are_checked_against_database(admin_db_url: str) -> None:
    engine = create_engine(admin_db_url)
    factory = make_session_factory(engine)
    signer = SessionSigner("boundary-secret", ttl_minutes=720)
    store = LoginSessionStore(factory, signer, ttl_minutes=720)
    issued = store.issue(Subject(ACCOUNT, LAB), credential_kind="planted-code",
                         credential_version=None, purpose="normal", now=NOW)
    claims = signer.verify_tracked(issued.token, now=NOW)
    assert claims is not None
    boundary = NOW + dt.timedelta(hours=12)
    try:
        assert store.authenticate(issued.token, now=boundary - dt.timedelta(microseconds=1)) == Subject(ACCOUNT, LAB)
        assert store.authenticate(issued.token, now=boundary) is None
        other_lab = Ulid("0000000000000000000000000B")
        with engine.begin() as db:
            db.execute(text("UPDATE account_admin.login_session SET lab_id=:lab WHERE id=:id"),
                       {"lab": str(other_lab), "id": str(issued.session_id)})
        moved_claim = signer.issue_tracked(
            Subject(ACCOUNT, other_lab), session_id=issued.session_id, generation=1,
            credential_kind="planted-code", purpose="normal", credential_version=None,
            expires_at=boundary,
        )
        # 세션 행과 토큰을 함께 다른 lab으로 바꿔도 현재 d1_account 소속과 달라 거절한다.
        assert store.authenticate(moved_claim.token, now=NOW) is None
    finally:
        engine.dispose()


def test_password_change_rechecks_expiry_after_waiting_for_credential_lock(admin_db_url: str) -> None:
    engine = create_engine(admin_db_url)
    factory = make_session_factory(engine)
    signer = SessionSigner("lock-secret", ttl_minutes=720)
    clock = [NOW]
    store = LoginSessionStore(factory, signer, ttl_minutes=720, clock=lambda: clock[0])
    account = ACCOUNT
    password = "초기-잠금-비밀번호-123"
    made = hash_password(password, n=1024)
    with engine.begin() as db:
        db.execute(text("""INSERT INTO account_admin.login_credential
          (account_id,login_name,kdf,salt,password_hash,n,r,p)
          VALUES(:id,'lock-boundary@example.com',:kdf,:salt,:digest,:n,:r,:p)"""),
                   {"id": str(account), **made.as_dict(), "digest": made.digest})
    issued = store.issue_database("lock-boundary@example.com", password, now=NOW)
    assert issued is not None
    claims = signer.verify_tracked(issued.token, now=NOW)
    assert claims is not None
    blocker = engine.connect()
    tx = blocker.begin()
    blocker.execute(text("SELECT 1 FROM account_admin.login_credential WHERE account_id=:id FOR UPDATE"),
                    {"id": str(account)})
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(store.change_initial_password, claims, "새-잠금-비밀번호-456")
            time.sleep(0.15)
            clock[0] = issued.expires_at
            tx.commit()
            assert pending.result(timeout=5) is None
        clock[0] = NOW
        racing = store.issue_database("lock-boundary@example.com", password, now=NOW)
        assert racing is not None
        racing_claims = signer.verify_tracked(racing.token, now=NOW)
        assert racing_claims is not None
        with ThreadPoolExecutor(max_workers=2) as pool:
            changed = pool.submit(
                store.change_initial_password, racing_claims, "경합-새-비밀번호-789"
            )
            revoked = pool.submit(store.revoke, racing.session_id, now=NOW)
            changed_session = changed.result(timeout=5)
            revoked.result(timeout=5)
        assert store.authenticate(racing.token, now=NOW) is None
        if changed_session is not None:
            assert store.authenticate(changed_session.token, now=NOW) is None
    finally:
        blocker.close()
        engine.dispose()
