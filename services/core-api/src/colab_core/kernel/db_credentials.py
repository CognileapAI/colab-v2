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
    """운영자 목록의 한 행. 여섯 열 ＋ 식별자 ＋ 운영자 표시다."""

    account_id: str
    email: str
    name: str
    lab_id: str
    lab_name: str
    role: str | None
    status: str
    last_login_at: dt.datetime | None
    operator: bool = False


class OperatorChangeRefused(RuntimeError):
    """운영자 해제를 거절한다. 거절 사유는 사용자에게 그대로 보인다 — 숨길 것이 아니다."""


#: 운영자 표를 만지는 동안 다른 요청이 같은 셈을 하지 못하게 하는 자문 잠금.
#: **셈과 삭제가 한 잠금 안에 있어야 한다** — 아니면 둘이 동시에 「나 말고도 있다」를 본다.
_OPERATOR_LOCK = "SELECT pg_advisory_xact_lock(1131379082)"


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

    def status_for_account(self, account_id: str) -> str | None:
        """계정에 **DB 자격 행이 있으면** 그 상태, 없으면 `None`.

        `None` 은 「활성」이 아니라 **의견 없음**이다 — 이 저장소가 모르는 계정(심어 둔 주체
        표에만 있는 도구 계정 등)까지 비활성으로 접는 순간, 백오피스가 한 번도 만진 적 없는
        자격이 조용히 끊긴다. 비활성화는 **계정에 거는 것**이고, 그 사실이 기록된 자리는
        여기 한 곳이다.
        """
        with self._factory() as db:
            row = db.execute(text("""
                SELECT status FROM account_admin.login_credential
                 WHERE account_id = :account_id
            """), {"account_id": str(account_id)}).first()
        return row[0] if row is not None else None

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
                       l.name AS lab_name, m.role, s.last_login_at,
                       (o.account_id IS NOT NULL) AS operator
                  FROM account_admin.login_credential c
                  JOIN d1_account a ON a.id = c.account_id
                  JOIN d1_lab l ON l.id = a.lab_id
                  LEFT JOIN d2_member_role m
                    ON m.account_id = a.id AND m.lab_id = a.lab_id
                  LEFT JOIN (SELECT account_id, max(issued_at) AS last_login_at
                               FROM account_admin.login_session GROUP BY account_id) s
                    ON s.account_id = c.account_id
                  LEFT JOIN account_admin.service_operator o ON o.account_id = c.account_id
                  {where}
                 ORDER BY l.name, c.login_name
            """), params).mappings().all()
        return [ServiceAccountRow(
            account_id=row["account_id"], email=row["login_name"], name=row["name"],
            lab_id=row["lab_id"], lab_name=row["lab_name"], role=row["role"],
            status=row["status"], last_login_at=row["last_login_at"],
            operator=row["operator"],
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

    def set_operator(self, account_id: str, operator: bool, *, actor_account_id: str) -> bool | None:
        """운영자 지정·해제. 없는 계정이면 `None`, 거절이면 `OperatorChangeRefused`.

        거절은 둘뿐이다 — ⑴ **자기 자신 해제** ⑵ **마지막 한 명 해제**. 둘 다 「되살릴 사람이
        없어진다」는 같은 이유이고, 그래서 둘 다 여기 한 트랜잭션 안에서 판정한다.

        ⚠ **셈은 잠금 아래에서 한다.** 잠금 없이 세면 두 해제 요청이 동시에 「나 말고도 있다」를
        보고 둘 다 통과해 운영자가 0명이 된다 — 백오피스로는 되돌릴 수 없는 상태다.

        지정·해제는 **권한 변경**이므로 그 계정의 자격 버전을 올리고 열린 세션을 닫는다.
        자격 행이 없는 계정(파일 자격·접속 코드만 있는 계정)도 세션은 닫는다.
        """
        with self._factory.begin() as db:
            db.execute(text(_OPERATOR_LOCK))
            exists = db.execute(text(
                "SELECT 1 FROM d1_account WHERE id=:id"), {"id": account_id}).first()
            if exists is None:
                return None
            now_operator = db.execute(text(
                "SELECT 1 FROM account_admin.service_operator WHERE account_id=:id"),
                {"id": account_id}).first() is not None
            if now_operator == operator:
                # 같은 상태를 다시 고르는 것은 변경이 아니다 — 남의 세션을 공짜로 끊지 않는다.
                return operator
            if not operator:
                if account_id == actor_account_id:
                    raise OperatorChangeRefused(
                        "자기 자신의 관리자 권한은 해제할 수 없다. 다른 관리자에게 요청한다.")
                total = db.execute(text(
                    "SELECT count(*) FROM account_admin.service_operator")).scalar_one()
                if total <= 1:
                    raise OperatorChangeRefused(
                        "마지막 관리자는 해제할 수 없다. 먼저 다른 관리자를 지정한다.")
                db.execute(text(
                    "DELETE FROM account_admin.service_operator WHERE account_id=:id"),
                    {"id": account_id})
            else:
                db.execute(text(
                    "INSERT INTO account_admin.service_operator(account_id) VALUES (:id)"
                    " ON CONFLICT (account_id) DO NOTHING"), {"id": account_id})
            db.execute(text("""
                UPDATE account_admin.login_credential
                   SET session_version=session_version+1, updated_at=now()
                 WHERE account_id=:id
            """), {"id": account_id})
            db.execute(text(REVOKE_ACCOUNT_SESSIONS), {"account_id": account_id})
        return operator

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
