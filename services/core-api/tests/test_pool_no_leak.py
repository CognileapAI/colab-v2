"""`SET LOCAL` 이 풀 커넥션을 타고 새지 않는다 — 요청 A(연구실 1) → 요청 B(무설정/연구실 2).

A1 이 이렇게 지었다는 사실만으로는 부족하다. **같은 커넥션이 재사용됨을 확인한 뒤**,
그 커넥션이 앞 요청의 lab_id 를 물려받지 않는 것을 본다.

이 파일에는 **탐지기 자신에 대한 시험**이 하나 있다 —
같은 순서를 비-LOCAL `set_config(..., false)` 로 돌리면 실제로 샌다는 것을 보여
「샌 것을 잡을 수 있는 시험」임을 증명한다. 그게 없으면 이 green 은 아무 말도 하지 않는다.
"""
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from conftest import (ACC_A_PROF, ACC_B_PROF, DS_A1, DS_A2, DS_B1, LAB_A, LAB_B,
                      scoped_ro)


def _single_connection_factory(url: str):
    """커넥션 **하나**만 쓰는 풀. 요청 A 와 B 가 반드시 같은 커넥션을 잡게 만든다."""
    engine = create_engine(url, poolclass=QueuePool, pool_size=1, max_overflow=0, future=True)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True), engine


def test_set_local_does_not_bleed_into_the_next_request(app_db_url: str) -> None:
    factory, engine = _single_connection_factory(app_db_url)
    try:
        # 요청 A — 연구실 A
        with scoped_ro(factory, ACC_A_PROF, LAB_A) as db:
            pid_a = db.execute(text("SELECT pg_backend_pid()")).scalar_one()
            assert {r[0] for r in db.execute(text("SELECT id FROM d3_dataset"))} == {DS_A1, DS_A2}

        # 요청 B-1 — 스코프를 아예 심지 않은 경로 (미스코프)
        session = factory()
        try:
            assert session.execute(text("SELECT pg_backend_pid()")).scalar_one() == pid_a, \
                "커넥션이 재사용되지 않았다 — 이 테스트가 증명하려는 상황이 아니다."
            assert session.execute(text("SELECT current_lab_id()")).scalar_one() is None
            assert session.execute(text("SELECT count(*) FROM d3_dataset")).scalar_one() == 0, \
                "앞 요청의 lab_id 가 남았다 — SET LOCAL 이 아니라 SET 을 쓴 것이다."
        finally:
            session.close()

        # 요청 B-2 — 다른 연구실
        with scoped_ro(factory, ACC_B_PROF, LAB_B) as db:
            assert db.execute(text("SELECT pg_backend_pid()")).scalar_one() == pid_a
            assert {r[0] for r in db.execute(text("SELECT id FROM d3_dataset"))} == {DS_B1}
    finally:
        engine.dispose()


def test_the_leak_detector_actually_detects_a_leak(app_db_url: str) -> None:
    """탐지기 시험 — 비-LOCAL `set_config` 를 쓰면 위 테스트가 **잡아내는** 형태로 샌다.

    여기서 새지 않는다면 위의 green 은 아무것도 증명하지 못한다. (`red 만드는 법` 의 실행형)
    """
    factory, engine = _single_connection_factory(app_db_url)
    try:
        session = factory()
        try:
            session.begin()
            # is_local => false. scope.py 가 쓰지 않는 형태다.
            session.execute(text("SELECT set_config('app.current_lab', :v, false)"), {"v": LAB_A})
            pid = session.execute(text("SELECT pg_backend_pid()")).scalar_one()
            session.commit()
        finally:
            session.close()

        leaked = factory()
        try:
            assert leaked.execute(text("SELECT pg_backend_pid()")).scalar_one() == pid
            assert leaked.execute(text("SELECT current_lab_id()")).scalar_one() == LAB_A
            assert leaked.execute(text("SELECT count(*) FROM d3_dataset")).scalar_one() == 2, \
                "비-LOCAL SET 인데도 새지 않았다 — 위 테스트의 green 이 무의미하다는 뜻이다."
        finally:
            leaked.close()
    finally:
        engine.dispose()


def test_no_bleed_across_http_requests_on_one_connection(app_db_url: str, subjects_file: str) -> None:
    """HTTP 층 — 커넥션 하나짜리 앱에 요청 A → 요청 B 를 연달아 보낸다."""
    from fastapi.testclient import TestClient

    from colab_core.app.main import API_PREFIX, create_app
    from colab_core.kernel.config import Settings

    app = create_app(Settings(database_url=app_db_url, subjects_file=subjects_file),
                     test_static_subjects=True)
    factory, engine = _single_connection_factory(app_db_url)
    app.state.session_factory = factory
    try:
        with TestClient(app) as client:
            a = client.get(f"{API_PREFIX}/datasets", headers={"Authorization": "Bearer a1-prof-token"})
            b = client.get(f"{API_PREFIX}/datasets", headers={"Authorization": "Bearer b1-prof-token"})
            a2 = client.get(f"{API_PREFIX}/lab", headers={"Authorization": "Bearer a1-prof-token"})
        assert {r["datasetId"] for r in a.json()["items"]} == {DS_A1, DS_A2}
        assert {r["datasetId"] for r in b.json()["items"]} == {DS_B1}, \
            "두 번째 요청이 첫 요청의 연구실을 물려받았다."
        assert a2.json()["labId"] == LAB_A
        # 인증 실패로 트랜잭션이 안 열린 요청 뒤에도 다음 요청이 온전해야 한다.
        with TestClient(app) as client:
            assert client.get(f"{API_PREFIX}/datasets").status_code == 401
            again = client.get(f"{API_PREFIX}/datasets", headers={"Authorization": "Bearer b1-prof-token"})
        assert {r["datasetId"] for r in again.json()["items"]} == {DS_B1}
    finally:
        engine.dispose()


# ═══════════════ 풀 **크기** — 누수가 아니라 「모자람」 쪽의 시험 ═══════════════
# 위의 시험들이 「한 커넥션을 돌려 써도 새지 않는다」를 본다면, 아래 둘은 **그 커넥션이
# 충분히 있는가**를 본다. 2026-09-17 운영 장애가 이 자리였다 — `make_engine` 이 크기를
# 적지 않아 SQLAlchemy 기본값 5＋10=15 로 섰고, 동기 라우트를 실어 나르는 스레드 40 개가
# 동시에 커넥션을 달라고 하자 25 개가 `pool_timeout` 30 초를 기다리다 죽었다
# (`QueuePool limit of size 5 overflow 10 reached` · 운영 API 4 분 전면 정지).
# ⚠ **새 파일로 두지 않는다** — 서비스 시험은 `-n 4 --dist loadfile` 로 **파일을** 워커에
#    나눠 담으므로(gates/tools/service-tests.sh:93) 파일이 하나 늘면 배분이 통째로 바뀌고,
#    워커별 DB 를 공유하는 상대가 달라진다. 풀을 다루는 시험이니 이 파일이 제자리이기도 하다.


def test_engine_declares_its_pool_capacity() -> None:
    """기본값에 기대지 않고 **적어 둔 값**으로 선다. DB 는 열지 않는다(지연 연결)."""
    from colab_core.kernel.db import MAX_OVERFLOW, POOL_SIZE, make_engine

    engine = make_engine("postgresql+psycopg://user:pw@127.0.0.1:1/never-opened")
    try:
        assert isinstance(engine.pool, QueuePool)
        assert engine.pool.size() == POOL_SIZE
        # 공개 접근자가 없다 — 풀이 실제로 쥔 값을 본다(SQLAlchemy 2.x).
        assert engine.pool._max_overflow == MAX_OVERFLOW
    finally:
        engine.dispose()


def test_pool_capacity_covers_the_sync_request_concurrency() -> None:
    """라우트가 전부 동기(`def`)라 **요청 하나 = 스레드 하나**다.

    그 상한만큼 커넥션이 있어야 남는 요청이 대기열에서 죽지 않는다. 이 시험이 red 면
    풀을 키우거나 스레드 상한을 함께 내려야 한다 — 한쪽만 바꾸면 그때 그 장애다.
    """
    import anyio
    import anyio.to_thread

    from colab_core.kernel.db import MAX_OVERFLOW, POOL_SIZE

    async def limit() -> int:
        return anyio.to_thread.current_default_thread_limiter().total_tokens

    threads = anyio.run(limit)
    assert POOL_SIZE + MAX_OVERFLOW >= threads, (
        f"동시 실행 {threads} 인데 커넥션은 {POOL_SIZE + MAX_OVERFLOW} 뿐이다 — "
        "남는 요청은 pool_timeout 을 기다리다 죽는다."
    )
