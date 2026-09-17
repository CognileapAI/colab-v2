"""엔진 · 세션 팩토리. 앱 전체에서 엔진은 하나다."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


# ⭑ **⟨2026-09-17⟩ 풀 크기는 동시 실행 상한과 같은 수다.**
# 라우트가 전부 동기(`def`)라 FastAPI 는 요청 하나를 스레드 하나에 실어 보낸다 — 그 스레드
# 상한이 anyio 기본 **40** 이다. 즉 커넥션을 동시에 달라는 요청이 최대 40 개다.
# 종전에는 이 값을 **적지 않아** SQLAlchemy 기본값(`pool_size=5` ＋ `max_overflow=10` = **15**)으로
# 돌았고, 나머지 25 개가 `pool_timeout` 30 초를 기다리다 죽었다 —
# `QueuePool limit of size 5 overflow 10 reached` · 운영 전면 정지 4 분(2026-09-17 21:09 KST).
# ⚠ **DB 한계가 아니었다** — 그때 RDS 는 `max_connections` 181 중 21 개만 쓰고 있었고 전부 idle 이었다.
#    앱이 스스로 15 로 묶은 것이 유일한 병목이다.
# ⛔ 40 보다 키우지 않는다 — 스레드가 40 이라 그 위는 쓰이지 않는 채 RDS 자리만 차지한다.
#    엔진은 둘(일반 · 계정관리)이라 최악이 80 이고, 그래도 181 안에 남는다.
POOL_SIZE = 20
MAX_OVERFLOW = 20


def make_engine(database_url: str) -> Engine:
    # future 스타일 · 커넥션 풀. 풀을 쓰기 때문에 스코프 주입이 반드시 트랜잭션 스코프여야 한다
    # (kernel/scope.py 의 주석 참조).
    return create_engine(database_url, pool_pre_ping=True, future=True,
                         pool_size=POOL_SIZE, max_overflow=MAX_OVERFLOW)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
