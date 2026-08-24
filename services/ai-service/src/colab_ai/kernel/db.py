"""엔진 · 세션. 배포 단위 하나에 엔진 하나 (다른 단위와 같은 관례).

**이 단위가 붙는 저장소는 `db/ai` 하나다.** D9 사전 3종이 거기 살고, 그것이 자기 도메인이다.
`K4-a` 는 여기에 **플랫폼 DB(D3) 커넥션**도 함께 두었고 — 연구실 경계 주입(GUC)까지 이 파일이
했다 — 그것이 `CLAUDE.md §3-1` 위반이었다. 2026-08-25 판정 ㈎ 로 그 커넥션이 사라졌다.
**경계 주입 코드가 여기 없는 것이 지금은 옳다**: 경계를 심을 대상 테이블이 이 단위에 없다.
(`db/ai` 세 표에는 `lab_id` 가 없다 — 연구실 공통 지식이기 때문이다.)

그리고 이 단위는 **읽기만 한다.** 사전 조회는 `READ ONLY` 트랜잭션으로 열린다
(`app/dictionaries.py`) — D10 이 어느 저장소에도 쓰지 않는다는 것을 문서가 아니라
**Postgres 가** 거절로 증명한다 (`CLAUDE.md §3-2` 의 정신 · `ai-no-lineage-write` 의 런타임 짝).
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True, future=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
