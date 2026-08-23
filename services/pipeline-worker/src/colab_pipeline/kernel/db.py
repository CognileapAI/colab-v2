"""엔진 · 세션 팩토리. 배포 단위 하나에 엔진 하나 (core-api `kernel/db.py` 와 같은 관례).

**세션에 연구실 경계를 심는 것은 호출자 몫이다** — `d5_*` 는 전 표에 RLS + FORCE 가 걸려
있고 GUC 를 안 세우면 `current_lab_id()` 가 NULL 이라 **한 행도 안 보인다.** 기본 거부다.
"""
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

GUC_LAB = "app.current_lab"
GUC_ACCOUNT = "app.current_account"

_SET_LOCAL = text("SELECT set_config(:name, :value, true)")


def make_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True, future=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def apply_scope(session: Session, *, lab_id: str, account_id: str) -> None:
    """트랜잭션 스코프(`SET LOCAL`). 풀로 돌아간 커넥션이 앞 작업의 lab_id 를 물려받지 않는다."""
    session.execute(_SET_LOCAL, {"name": GUC_LAB, "value": str(lab_id)})
    session.execute(_SET_LOCAL, {"name": GUC_ACCOUNT, "value": str(account_id)})
