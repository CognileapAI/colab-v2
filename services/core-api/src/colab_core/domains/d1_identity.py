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

# ⭑ ⟨0028⟩ 경계를 **여기에도 직접 적는다.** 위 `_LAB` 과 같은 이유가 아니다 —
#   `d1_account` 에는 RLS 가 있다. 다만 운영자 읽기 스코프(`operator_read`)가 열리면
#   그 정책이 전 연구실을 통과시키고, 그러면 **연구실 행은 `current_lab_id()` 로 고정인데
#   구성원만 전 연구실**이 된다: 내 연구실 이름 아래 남의 연구실 사람들이 서는 화면이다.
#   한 화면의 두 값이 서로 다른 범위를 말하지 않게 이 두 질의는 연구실에 못 박는다.
#   (운영자가 남의 연구실 구성원을 보는 길은 이 화면이 아니라 백오피스 계정 목록이다.)
_MEMBER_COUNT = text("SELECT count(*) FROM d1_account WHERE lab_id = current_lab_id()")

# 구성원·권한 격자의 행 순서. 이름순으로 세운다 — 정본이 순서를 주지 않으므로
# 화면이 매번 다른 순서를 보지 않게 하는 최소 규칙만 둔다.
_MEMBERS = text("""
    SELECT a.id, a.name, a.email
      FROM d1_account a
     WHERE a.lab_id = current_lab_id()
     ORDER BY a.name, a.id
""")


def find_account(session: Session, account_id: Ulid) -> dict | None:
    row = session.execute(_ACCOUNT, {"account_id": str(account_id)}).mappings().first()
    return dict(row) if row else None


def find_lab(session: Session) -> dict | None:
    row = session.execute(_LAB).mappings().first()
    return dict(row) if row else None


#: 연구실 편집이 닿는 칸 ↔ 그 값이 사는 표. **계약(`LabUpdate`)이 정본이고** 여기는
#: 그것을 SQL 자리로 옮긴 표다. `openedAt` 은 여기 없다 — **개설일은 고치는 값이 아니다.**
_LAB_UPDATABLE = {
    "name": ("d1_lab", "name"),
    "university": ("d1_lab_profile", "university"),
    "department": ("d1_lab_profile", "department"),
    "principalInvestigator": ("d1_lab_profile", "principal_investigator"),
    "researchField": ("d1_lab_profile", "research_field"),
    "introduction": ("d1_lab_profile", "introduction"),
    "defaultVisibility": ("d1_lab_profile", "default_visibility"),
}


def update_lab(session: Session, changes: dict) -> None:
    """연구실 정보 부분 수정 (`〈150〉` · 계약 `LabUpdate`).

    **두 표에 걸쳐 있다** — 이름은 `d1_lab`, 나머지는 `d1_lab_profile` 이다. 정본이
    「연구실을 정의하는 유일한 자리」로 프로필을 따로 둔 결과이고(§2), 표를 합치는 것은
    마이그레이션이라 하지 않는다.

    **프로필 행이 없을 수 있다** — 그래서 `INSERT ... ON CONFLICT DO UPDATE` 로 쓴다.
    없는 행에 `UPDATE` 를 날리면 0행이 갱신되고 **조용히 아무 일도 안 일어난다.**

    경계는 `current_lab_id()` 가 넣는다 — 요청에서 `labId` 를 받지 않는다.
    """
    by_table: dict[str, dict[str, object]] = {}
    for key, value in changes.items():
        table, column = _LAB_UPDATABLE[key]
        by_table.setdefault(table, {})[column] = value

    lab = by_table.get("d1_lab")
    if lab:
        assignments = ", ".join(f"{c} = :{c}" for c in lab)
        session.execute(text(f"UPDATE d1_lab SET {assignments} WHERE id = current_lab_id()"),
                        lab)

    profile = by_table.get("d1_lab_profile")
    if profile:
        columns = ", ".join(profile)
        binds = ", ".join(f":{c}" for c in profile)
        updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in profile)
        session.execute(text(
            f"INSERT INTO d1_lab_profile (lab_id, {columns}) "
            f"VALUES (current_lab_id(), {binds}) "
            f"ON CONFLICT (lab_id) DO UPDATE SET {updates}"), profile)


def list_members(session: Session) -> list[dict]:
    """연구실 구성원 전원. 질의가 연구실을 직접 고른다(위 `_MEMBERS` 주석 — 0028)."""
    return [dict(r) for r in session.execute(_MEMBERS).mappings().all()]


def member_exists(session: Session, account_id: Ulid) -> bool:
    """경계 밖이면 RLS 가 행을 지우므로 False 가 되고, 호출자는 404 를 낸다 (P-9·P-10)."""
    return session.execute(
        text("SELECT 1 FROM d1_account WHERE id = :account_id"),
        {"account_id": str(account_id)},
    ).first() is not None


def member_count(session: Session) -> int:
    """연구실 구성원 수. 질의가 연구실을 직접 고른다(위 `_MEMBER_COUNT` 주석 — 0028)."""
    return int(session.execute(_MEMBER_COUNT).scalar_one())


def list_operator_labs(session: Session) -> list[dict]:
    """Reporter role에서 일일 보고 대상 연구실 전체를 반환한다."""
    return [dict(row) for row in session.execute(
        text("SELECT id, name FROM d1_lab ORDER BY id")
    ).mappings()]


def list_operator_accounts(session: Session) -> list[dict]:
    """Only display names in the explicitly scoped lab; never account email."""
    from ..kernel.scope import require_lab_scope
    require_lab_scope(session)
    return [dict(row) for row in session.execute(
        text("SELECT id,lab_id,name FROM d1_account ORDER BY id")
    ).mappings()]


def require_operator_actor(cursor, actor_id: str) -> None:
    cursor.execute("SELECT id FROM d1_account WHERE id=%s AND lab_id=current_lab_id()", (actor_id,))
    if cursor.fetchone() is None:
        raise ValueError("operator actor must belong to the scoped lab")
