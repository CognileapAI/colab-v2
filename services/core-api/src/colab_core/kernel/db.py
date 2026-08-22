"""엔진 · 세션 팩토리. 앱 전체에서 엔진은 하나다."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(database_url: str) -> Engine:
    # future 스타일 · 커넥션 풀. 풀을 쓰기 때문에 스코프 주입이 반드시 트랜잭션 스코프여야 한다
    # (kernel/scope.py 의 주석 참조).
    return create_engine(database_url, pool_pre_ping=True, future=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
