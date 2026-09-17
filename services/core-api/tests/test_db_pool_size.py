"""풀 크기는 **동시 실행 상한과 맞물린 값**이다 — 숫자만 지키지 말고 그 근거를 함께 지킨다.

2026-09-17 운영 장애의 재발 방지 시험이다. 그때 `make_engine` 이 풀 크기를 적지 않아
SQLAlchemy 기본값 15 로 돌았고, 동기 라우트를 실어 나르는 스레드 40 개가 동시에
커넥션을 달라고 하자 25 개가 `pool_timeout` 을 기다리다 죽었다
(`QueuePool limit of size 5 overflow 10 reached` · 운영 API 전면 정지 4 분).

DB 는 연결하지 않는다 — `create_engine` 은 지연 연결이라 풀 **설정**만 보면 된다.
"""
from __future__ import annotations

import anyio
import anyio.to_thread
from sqlalchemy.pool import QueuePool

from colab_core.kernel.db import MAX_OVERFLOW, POOL_SIZE, make_engine

# 실제로 열지 않는 주소. 여기서 보는 것은 풀 설정뿐이다.
UNUSED_URL = "postgresql+psycopg://user:pw@127.0.0.1:1/never-opened"


def test_engine_declares_its_pool_capacity() -> None:
    """기본값에 기대지 않고 **적어 둔 값**으로 선다."""
    engine = make_engine(UNUSED_URL)
    try:
        pool = engine.pool
        assert isinstance(pool, QueuePool)
        assert pool.size() == POOL_SIZE
        # 공개 접근자가 없다 — 풀이 실제로 쥔 값을 본다(SQLAlchemy 2.x).
        assert pool._max_overflow == MAX_OVERFLOW
    finally:
        engine.dispose()


def test_pool_capacity_covers_the_sync_request_concurrency() -> None:
    """라우트가 전부 동기(`def`)라 **요청 하나 = 스레드 하나**다.

    그 스레드 상한만큼 커넥션이 있어야 요청이 대기열에서 죽지 않는다.
    이 시험이 red 면 풀을 키우거나 스레드 상한을 함께 내려야 한다 — 한쪽만 바꾸면 그때 그 장애다.
    """

    async def limit() -> int:
        return anyio.to_thread.current_default_thread_limiter().total_tokens

    threads = anyio.run(limit)
    assert POOL_SIZE + MAX_OVERFLOW >= threads, (
        f"동시 실행 {threads} 인데 커넥션은 {POOL_SIZE + MAX_OVERFLOW} 뿐이다 — "
        "남는 요청은 pool_timeout 을 기다리다 죽는다."
    )
