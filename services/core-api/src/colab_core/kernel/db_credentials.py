"""Stage 3 서비스 계정의 DB 자격 저장 경계."""
from __future__ import annotations

import dataclasses

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from .auth import Subject
from .ids import Ulid
from .password import PasswordHash, hash_password, verify_password


def normalize_login_name(value: str) -> str:
    return value.strip().lower()


@dataclasses.dataclass(frozen=True)
class DatabaseCredential:
    subject: Subject
    login_name: str
    password: PasswordHash
    must_change_password: bool
    session_version: int


class DatabaseCredentialStore:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory
        self._dummy = hash_password("존재하지-않는-DB-자격")

    def find(self, login_name: str) -> DatabaseCredential | None:
        with self._factory() as db:
            row = db.execute(text("""
                SELECT c.account_id, a.lab_id, c.login_name, c.kdf, c.salt, c.password_hash,
                       n, r, p, must_change_password, session_version
                  FROM account_admin.login_credential c JOIN d1_account a ON a.id=c.account_id
                 WHERE c.login_name = :login_name
            """), {"login_name": normalize_login_name(login_name)}).mappings().first()
        if row is None:
            return None
        return DatabaseCredential(
            subject=Subject(Ulid(row["account_id"]), Ulid(row["lab_id"])),
            login_name=row["login_name"],
            password=PasswordHash(kdf=row["kdf"], salt=row["salt"],
                                  digest=row["password_hash"], n=row["n"],
                                  r=row["r"], p=row["p"]),
            must_change_password=row["must_change_password"],
            session_version=row["session_version"],
        )

    def dummy_verify(self, password: str) -> None:
        verify_password(password, self._dummy)

    def token_is_current(self, account_id: Ulid, lab_id: Ulid, version: int) -> DatabaseCredential | None:
        with self._factory() as db:
            row = db.execute(text("""
                SELECT c.login_name FROM account_admin.login_credential c
                  JOIN d1_account a ON a.id=c.account_id
                 WHERE c.account_id=:account_id AND a.lab_id=:lab_id AND c.session_version=:version
            """), {"account_id": str(account_id), "lab_id": str(lab_id),
                     "version": version}).first()
        return self.find(row.login_name) if row else None

    def change_password(self, account_id: Ulid, new: str, expected_version: int) -> DatabaseCredential | None:
        with self._factory.begin() as db:
            row = db.execute(text("""
                SELECT login_name, kdf, salt, password_hash, n, r, p,
                       must_change_password, session_version
                  FROM account_admin.login_credential
                 WHERE account_id=:account_id FOR UPDATE
            """), {"account_id": str(account_id)}).mappings().first()
            if row is None:
                return None
            if not row["must_change_password"] or row["session_version"] != expected_version:
                return None
            stored = PasswordHash(row["kdf"], row["salt"], row["password_hash"],
                                  row["n"], row["r"], row["p"])
            if verify_password(new, stored):
                raise ValueError("initial password reuse")
            made = hash_password(new)
            db.execute(text("""
                UPDATE account_admin.login_credential
                   SET kdf=:kdf, salt=:salt, password_hash=:digest, n=:n, r=:r, p=:p,
                       must_change_password=false, session_version=session_version+1,
                       updated_at=now()
                 WHERE account_id=:account_id
            """), {**made.as_dict(), "digest": made.digest,
                     "account_id": str(account_id)})
        return self.find(row["login_name"])
