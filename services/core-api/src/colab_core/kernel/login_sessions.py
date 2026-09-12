"""회수 가능한 브라우저 세션의 account-admin 저장 경계."""
from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import secrets
from collections.abc import Callable

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .auth import Subject
from .ids import Ulid
from .password import PasswordHash, hash_password, verify_password
from .session_token import IssuedSession, SessionSigner, TrackedSessionClaims


class SessionStoreUnavailable(RuntimeError):
    pass


FIXED_BROWSER_SESSION_TTL_MINUTES = 12 * 60


@dataclasses.dataclass(frozen=True)
class IssuedBrowserSession:
    token: str
    expires_at: dt.datetime
    session_id: Ulid
    revocation_token: str


@dataclasses.dataclass(frozen=True)
class RotatedBrowserSession:
    token: str
    expires_at: dt.datetime
    session_id: Ulid


class LoginSessionStore:
    def __init__(
        self, factory: sessionmaker[Session], signer: SessionSigner, *, ttl_minutes: int,
        clock: Callable[[], dt.datetime] | None = None,
    ) -> None:
        self._factory = factory
        self._signer = signer
        self._ttl = dt.timedelta(minutes=ttl_minutes)
        self._clock = clock or (lambda: dt.datetime.now(dt.timezone.utc))
        self._dummy = hash_password("존재하지-않는-세션-자격")

    @staticmethod
    def _digest(capability: str) -> str:
        return hashlib.sha256(capability.encode("ascii")).hexdigest()

    def issue(
        self,
        subject: Subject,
        *,
        credential_kind: str,
        credential_version: int | None,
        purpose: str,
        now: dt.datetime | None = None,
    ) -> IssuedBrowserSession:
        now = (now or self._clock()).replace(microsecond=0)
        expires_at = now + self._ttl
        session_id = Ulid.generate()
        capability = secrets.token_urlsafe(32)
        try:
            with self._factory.begin() as db:
                db.execute(text("""
                    INSERT INTO account_admin.login_session
                      (id,account_id,lab_id,issued_at,expires_at,generation,
                       credential_kind,purpose,credential_version,revoke_digest)
                    VALUES (:id,:account,:lab,:issued,:expires,1,:kind,:purpose,:version,:digest)
                """), {
                    "id": str(session_id), "account": str(subject.account_id),
                    "lab": str(subject.lab_id), "issued": now, "expires": expires_at,
                    "kind": credential_kind, "purpose": purpose,
                    "version": credential_version, "digest": self._digest(capability),
                })
        except SQLAlchemyError as exc:
            raise SessionStoreUnavailable from exc
        issued = self._signer.issue_tracked(
            subject, session_id=session_id, generation=1,
            credential_kind=credential_kind, purpose=purpose,
            credential_version=credential_version, expires_at=expires_at,
        )
        return IssuedBrowserSession(
            issued.token, issued.expires_at, session_id, capability
        )

    def issue_database(
        self, login_name: str, password: str, *, now: dt.datetime | None = None
    ) -> IssuedBrowserSession | None:
        now = (now or self._clock()).replace(microsecond=0)
        expires_at = now + self._ttl
        session_id = Ulid.generate()
        capability = secrets.token_urlsafe(32)
        try:
            with self._factory.begin() as db:
                row = db.execute(text("""
                    SELECT c.account_id,a.lab_id,c.kdf,c.salt,c.password_hash,c.n,c.r,c.p,
                           c.must_change_password,c.session_version
                      FROM account_admin.login_credential c
                      JOIN d1_account a ON a.id=c.account_id
                     WHERE c.login_name=:login_name FOR UPDATE OF c
                """), {"login_name": login_name}).mappings().first()
                if row is None:
                    verify_password(password, self._dummy)
                    return None
                stored = PasswordHash(
                    row["kdf"], row["salt"], row["password_hash"],
                    row["n"], row["r"], row["p"],
                )
                if not verify_password(password, stored):
                    return None
                subject = Subject(Ulid(row["account_id"]), Ulid(row["lab_id"]))
                purpose = "password-change" if row["must_change_password"] else "normal"
                db.execute(text("""
                    INSERT INTO account_admin.login_session
                      (id,account_id,lab_id,issued_at,expires_at,generation,
                       credential_kind,purpose,credential_version,revoke_digest)
                    VALUES (:id,:account,:lab,:issued,:expires,1,'database',:purpose,:version,:digest)
                """), {
                    "id": str(session_id), "account": str(subject.account_id),
                    "lab": str(subject.lab_id), "issued": now, "expires": expires_at,
                    "purpose": purpose, "version": row["session_version"],
                    "digest": self._digest(capability),
                })
        except SQLAlchemyError as exc:
            raise SessionStoreUnavailable from exc
        issued = self._signer.issue_tracked(
            subject, session_id=session_id, generation=1,
            credential_kind="database", purpose=purpose,
            credential_version=row["session_version"], expires_at=expires_at,
        )
        return IssuedBrowserSession(issued.token, expires_at, session_id, capability)

    def authenticate(
        self, token: str, *, now: dt.datetime | None = None
    ) -> Subject | None:
        now = now or self._clock()
        claims = self._signer.verify_tracked(token, now=now)
        if claims is None:
            return None
        try:
            with self._factory() as db:
                row = db.execute(text("""
                    SELECT s.account_id,s.lab_id,s.expires_at,s.revoked_at,s.generation,
                           s.credential_kind,s.purpose,s.credential_version,
                           c.session_version,c.must_change_password,a.lab_id AS current_lab_id
                      FROM account_admin.login_session s
                      JOIN d1_account a ON a.id=s.account_id
                      LEFT JOIN account_admin.login_credential c
                        ON c.account_id=s.account_id AND s.credential_kind='database'
                     WHERE s.id=:id
                """), {"id": str(claims.session_id)}).mappings().first()
        except SQLAlchemyError as exc:
            raise SessionStoreUnavailable from exc
        if row is None or row["revoked_at"] is not None or row["expires_at"] <= now:
            return None
        if any((
            str(row["account_id"]) != str(claims.subject.account_id),
            str(row["lab_id"]) != str(claims.subject.lab_id),
            str(row["current_lab_id"]) != str(claims.subject.lab_id),
            row["expires_at"] != claims.expires_at,
            row["generation"] != claims.generation,
            row["credential_kind"] != claims.credential_kind,
            row["purpose"] != claims.purpose,
            row["credential_version"] != claims.credential_version,
        )):
            return None
        must_change = claims.purpose == "password-change"
        if claims.credential_kind == "database":
            if (row["session_version"] != claims.credential_version
                    or row["must_change_password"] != must_change):
                return None
        return Subject(
            claims.subject.account_id, claims.subject.lab_id,
            must_change_password=must_change,
            credential_version=claims.credential_version,
        )

    def revoke(self, session_id: Ulid, *, now: dt.datetime | None = None) -> None:
        now = now or self._clock()
        try:
            with self._factory.begin() as db:
                db.execute(text("""
                    UPDATE account_admin.login_session
                       SET revoked_at=COALESCE(revoked_at,:now)
                     WHERE id=:id
                """), {"id": str(session_id), "now": now})
        except SQLAlchemyError as exc:
            raise SessionStoreUnavailable from exc

    def revoke_by_capability(
        self, capability: str, *, now: dt.datetime | None = None
    ) -> None:
        now = now or self._clock()
        try:
            digest = self._digest(capability)
        except (UnicodeEncodeError, AttributeError) as exc:
            raise ValueError("malformed revocation capability") from exc
        try:
            with self._factory.begin() as db:
                db.execute(text("""
                    UPDATE account_admin.login_session
                       SET revoked_at=COALESCE(revoked_at,:now)
                     WHERE revoke_digest=:digest
                """), {"digest": digest, "now": now})
        except SQLAlchemyError as exc:
            raise SessionStoreUnavailable from exc

    def change_initial_password(
        self, claims: TrackedSessionClaims, new_password: str,
        *, now: dt.datetime | None = None,
    ) -> RotatedBrowserSession | None:
        requested_now = now
        if claims.credential_kind != "database" or claims.purpose != "password-change":
            return None
        made = hash_password(new_password)
        try:
            with self._factory.begin() as db:
                credential = db.execute(text("""
                    SELECT login_name,kdf,salt,password_hash,n,r,p,
                           must_change_password,session_version
                      FROM account_admin.login_credential
                     WHERE account_id=:account FOR UPDATE
                """), {"account": str(claims.subject.account_id)}).mappings().first()
                session = db.execute(text("""
                    SELECT account_id,lab_id,expires_at,revoked_at,generation,
                           credential_kind,purpose,credential_version
                      FROM account_admin.login_session
                     WHERE id=:id FOR UPDATE
                """), {"id": str(claims.session_id)}).mappings().first()
                # 잠금 대기 중 만료될 수 있다. 잠금을 얻은 뒤 현재 시각을 다시 읽는다.
                checked_now = requested_now or self._clock()
                if credential is None or session is None:
                    return None
                if (session["revoked_at"] is not None or session["expires_at"] <= checked_now
                        or str(session["account_id"]) != str(claims.subject.account_id)
                        or str(session["lab_id"]) != str(claims.subject.lab_id)
                        or session["generation"] != claims.generation
                        or session["credential_kind"] != "database"
                        or session["purpose"] != "password-change"
                        or session["credential_version"] != claims.credential_version
                        or not credential["must_change_password"]
                        or credential["session_version"] != claims.credential_version):
                    return None
                stored = PasswordHash(
                    credential["kdf"], credential["salt"], credential["password_hash"],
                    credential["n"], credential["r"], credential["p"],
                )
                if verify_password(new_password, stored):
                    raise ValueError("initial password reuse")
                changed = db.execute(text("""
                    UPDATE account_admin.login_credential
                       SET kdf=:kdf,salt=:salt,password_hash=:digest,n=:n,r=:r,p=:p,
                           must_change_password=false,session_version=session_version+1,
                           updated_at=:now
                     WHERE account_id=:account
                 RETURNING session_version
                """), {
                    **made.as_dict(), "digest": made.digest, "now": checked_now,
                    "account": str(claims.subject.account_id),
                }).mappings().one()
                rotated = db.execute(text("""
                    UPDATE account_admin.login_session
                       SET generation=generation+1,purpose='normal',
                           credential_version=:version
                     WHERE id=:id
                 RETURNING expires_at,generation
                """), {
                    "id": str(claims.session_id),
                    "version": changed["session_version"],
                }).mappings().one()
        except SQLAlchemyError as exc:
            raise SessionStoreUnavailable from exc
        issued: IssuedSession = self._signer.issue_tracked(
            claims.subject, session_id=claims.session_id,
            generation=rotated["generation"], credential_kind="database",
            purpose="normal", credential_version=changed["session_version"],
            expires_at=rotated["expires_at"],
        )
        return RotatedBrowserSession(issued.token, issued.expires_at, claims.session_id)
