"""Stage 3 서비스 계정의 DB 자격 저장 경계."""
from __future__ import annotations

import dataclasses
import datetime as dt

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from .auth import Subject
from .ids import Ulid
from .login_sessions import REVOKE_ACCOUNT_SESSIONS
from .password import PasswordHash, hash_password, verify_password

#: 계정이 가질 수 있는 상태. 세 번째 값을 코드에서 지어내지 않는다 — DB CHECK 과 같은 두 값이다.
ACCOUNT_STATUSES = ("active", "inactive")


def normalize_login_name(value: str) -> str:
    return value.strip().lower()


@dataclasses.dataclass(frozen=True)
class DatabaseCredential:
    subject: Subject
    login_name: str
    password: PasswordHash
    must_change_password: bool
    session_version: int
    status: str = "active"


@dataclasses.dataclass(frozen=True)
class ServiceAccountRow:
    """운영자 목록의 한 행. 여섯 열 ＋ 식별자다."""

    account_id: str
    email: str
    name: str
    lab_id: str
    lab_name: str
    role: str | None
    status: str
    last_login_at: dt.datetime | None


class DatabaseCredentialStore:
    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory
        self._dummy = hash_password("존재하지-않는-DB-자격")

    def find(self, login_name: str) -> DatabaseCredential | None:
        with self._factory() as db:
            row = db.execute(text("""
                SELECT c.account_id, a.lab_id, c.login_name, c.kdf, c.salt, c.password_hash,
                       n, r, p, must_change_password, session_version, status
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
            status=row["status"],
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

    # ── 운영자 백오피스 ─────────────────────────────────────────────────────
    # 전 기기 종료의 기계는 **새로 만들지 않는다** — `session_version` 을 올리면 그 계정의
    # 모든 서명 세션이 다음 요청에서 거절되고(`login_sessions.authenticate`), 같은
    # 트랜잭션에서 원장 행의 `revoked_at` 까지 채워 열린 세션을 남기지 않는다.

    def list_accounts(self, *, lab_id: str | None = None, status: str | None = None,
                      role: str | None = None, email: str | None = None,
                      ) -> list[ServiceAccountRow]:
        """전 연구실 한 벌. **이 경로에는 연구실 경계를 걸지 않는다**(운영자 전용 · 등재된 예외).

        최근 로그인은 `login_session` 의 집계다 — 새 열을 만들지 않는다.
        """
        clauses, params = [], {}
        if lab_id is not None:
            clauses.append("a.lab_id = :lab_id")
            params["lab_id"] = lab_id
        if status is not None:
            clauses.append("c.status = :status")
            params["status"] = status
        if role is not None:
            clauses.append("m.role = :role")
            params["role"] = role
        if email:
            clauses.append("c.login_name LIKE '%' || :email || '%'")
            params["email"] = normalize_login_name(email)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._factory() as db:
            rows = db.execute(text(f"""
                SELECT c.account_id, c.login_name, c.status, a.name, a.lab_id,
                       l.name AS lab_name, m.role, s.last_login_at
                  FROM account_admin.login_credential c
                  JOIN d1_account a ON a.id = c.account_id
                  JOIN d1_lab l ON l.id = a.lab_id
                  LEFT JOIN d2_member_role m
                    ON m.account_id = a.id AND m.lab_id = a.lab_id
                  LEFT JOIN (SELECT account_id, max(issued_at) AS last_login_at
                               FROM account_admin.login_session GROUP BY account_id) s
                    ON s.account_id = c.account_id
                  {where}
                 ORDER BY l.name, c.login_name
            """), params).mappings().all()
        return [ServiceAccountRow(
            account_id=row["account_id"], email=row["login_name"], name=row["name"],
            lab_id=row["lab_id"], lab_name=row["lab_name"], role=row["role"],
            status=row["status"], last_login_at=row["last_login_at"],
        ) for row in rows]

    def reset_password(self, account_id: str, new: str) -> int | None:
        """운영자가 새 초기 비밀번호를 심는다. 첫 로그인 변경이 다시 강제되고 전 기기가 끊긴다.

        **원문은 어디에도 남기지 않는다** — 해시만 저장하고 돌려주는 것은 새 자격 버전뿐이다.
        """
        made = hash_password(new)
        with self._factory.begin() as db:
            found = db.execute(text("""
                SELECT 1 FROM account_admin.login_credential
                 WHERE account_id=:account_id FOR UPDATE
            """), {"account_id": account_id}).first()
            if found is None:
                return None
            changed = db.execute(text("""
                UPDATE account_admin.login_credential
                   SET kdf=:kdf, salt=:salt, password_hash=:digest, n=:n, r=:r, p=:p,
                       must_change_password=true, session_version=session_version+1,
                       updated_at=now()
                 WHERE account_id=:account_id
             RETURNING session_version
            """), {**made.as_dict(), "digest": made.digest,
                     "account_id": account_id}).mappings().one()
            db.execute(text(REVOKE_ACCOUNT_SESSIONS), {"account_id": account_id})
        return changed["session_version"]

    def set_status(self, account_id: str, status: str) -> str | None:
        """비활성화/재활성화. **행을 지우지 않는다** — 데이터·소유권은 그대로 남는다."""
        if status not in ACCOUNT_STATUSES:
            raise ValueError(f"허용하지 않는 계정 상태다: {status}")
        with self._factory.begin() as db:
            row = db.execute(text("""
                SELECT status FROM account_admin.login_credential
                 WHERE account_id=:account_id FOR UPDATE
            """), {"account_id": account_id}).mappings().first()
            if row is None:
                return None
            # 같은 상태를 다시 고르는 것은 변경이 아니다 — 남의 세션을 공짜로 끊지 않는다.
            if row["status"] == status:
                return status
            changed = db.execute(text("""
                UPDATE account_admin.login_credential
                   SET status=:status, session_version=session_version+1, updated_at=now()
                 WHERE account_id=:account_id
             RETURNING status
            """), {"status": status, "account_id": account_id}).mappings().one()
            db.execute(text(REVOKE_ACCOUNT_SESSIONS), {"account_id": account_id})
        return changed["status"]
