"""D1 Identity & Lab — 연구실(테넌트 루트) · 계정. shared kernel 이라 다른 도메인이 읽어도 된다.

**이 도메인은 위층을 모른다** (`importlinter.ini` 계약 4). 여기서 D2~D8 을 import 하면
'모두가 읽는 커널'이 '모두와 얽힌 커널'이 된다.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid

_ACCOUNT = text("""
    SELECT a.id, a.name, a.email, a.lab_id, l.name AS lab_name
      FROM d1_account a
      JOIN d1_lab l ON l.id = a.lab_id
     WHERE a.id = :account_id
""")

# d1_lab 은 테넌트 **루트**라 RLS 정책이 없다 (schema.sql §7 — 경계의 기준이 되는 테이블이다).
# 그래서 여기서는 경계를 조건으로 직접 적는다. 나머지 테이블은 RLS 가 대신 적는다.
_LAB = text("""
    SELECT l.id, l.name, l.opened_at,
           p.university, p.department, p.principal_investigator,
           p.research_field, p.introduction, p.default_visibility
      FROM d1_lab l
      LEFT JOIN d1_lab_profile p ON p.lab_id = l.id
     WHERE l.id = current_lab_id()
""")

_MEMBER_COUNT = text("SELECT count(*) FROM d1_account")

# 구성원·권한 격자의 행 순서. 이름순으로 세운다 — 정본이 순서를 주지 않으므로
# 화면이 매번 다른 순서를 보지 않게 하는 최소 규칙만 둔다.
_MEMBERS = text("""
    SELECT a.id, a.name, a.email
      FROM d1_account a
     ORDER BY a.name, a.id
""")


def find_account(session: Session, account_id: Ulid) -> dict | None:
    row = session.execute(_ACCOUNT, {"account_id": str(account_id)}).mappings().first()
    return dict(row) if row else None


def find_lab(session: Session) -> dict | None:
    row = session.execute(_LAB).mappings().first()
    return dict(row) if row else None


def list_members(session: Session) -> list[dict]:
    """연구실 구성원 전원. 경계는 RLS 가 이미 걸었다 — lab_id 조건을 다시 적지 않는다."""
    return [dict(r) for r in session.execute(_MEMBERS).mappings().all()]


def member_exists(session: Session, account_id: Ulid) -> bool:
    """경계 밖이면 RLS 가 행을 지우므로 False 가 되고, 호출자는 404 를 낸다 (P-9·P-10)."""
    return session.execute(
        text("SELECT 1 FROM d1_account WHERE id = :account_id"),
        {"account_id": str(account_id)},
    ).first() is not None


def member_count(session: Session) -> int:
    """RLS 가 이미 경계를 걸어 둔 위에서 센다 — 여기에 lab_id 조건을 다시 적지 않는다."""
    return int(session.execute(_MEMBER_COUNT).scalar_one())
