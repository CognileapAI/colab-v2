"""엔진 · 세션 · **경계 주입**. 배포 단위 하나에 엔진 하나 (다른 단위와 같은 관례).

**세션에 연구실 경계를 심는 것이 이 파일의 존재 이유다.** GUC 를 안 세우면
`current_lab_id()` 가 NULL 이라 정책이 한 행도 안 보여 준다 — 기본 거부다.
`SET LOCAL` 이라 풀로 돌아간 커넥션이 앞 요청의 경계를 물려받지 않는다.

**그리고 이 단위는 읽기만 한다.** 트랜잭션을 `READ ONLY` 로 연다 — D10 이 기록 쪽 저장소에
쓰지 않는다는 것을 문서가 아니라 **Postgres 가** 거절로 증명한다 (`CLAUDE.md §3-2` 의
정신 · `ai-no-lineage-write` 게이트의 런타임 짝).
"""
from __future__ import annotations

import contextlib

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

GUC_LAB = "app.current_lab"
GUC_ACCOUNT = "app.current_account"

_SET_LOCAL = text("SELECT set_config(:name, :value, true)")
_READ_ONLY = text("SET TRANSACTION READ ONLY")


def make_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True, future=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


@contextlib.contextmanager
def read_only_scope(factory: sessionmaker[Session], *, lab_id: str, account_id: str):
    """경계를 심은 **읽기 전용** 트랜잭션. 끝나면 언제나 rollback 한다."""
    session = factory()
    try:
        session.begin()
        session.execute(_READ_ONLY)
        session.execute(_SET_LOCAL, {"name": GUC_LAB, "value": str(lab_id)})
        session.execute(_SET_LOCAL, {"name": GUC_ACCOUNT, "value": str(account_id)})
        yield session
    finally:
        session.rollback()
        session.close()
