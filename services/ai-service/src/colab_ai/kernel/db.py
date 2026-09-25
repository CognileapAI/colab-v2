"""엔진 · 세션. 배포 단위 하나에 엔진 하나 (다른 단위와 같은 관례).

**이 단위가 붙는 저장소는 `db/ai` 하나다.** D9 사전 3종과 개념 그래프 두 표, 그리고 D10 의
모델 호출 실행 원장(`d10_model_call`)이 거기 살고, 그것이 자기 도메인이다.
`K4-a` 는 여기에 **플랫폼 DB(D3) 커넥션**도 함께 두었고 — 연구실 경계 주입(GUC)까지 이 파일이
했다 — 그것이 `CLAUDE.md §3-1` 위반이었다. 2026-08-25 판정 ㈎ 로 그 커넥션이 사라졌다.
**경계 주입 코드가 여기 없는 것이 지금은 옳다**: D9 다섯 표에 `lab_id` 가 없다 —
연구실 공통 지식이기 때문이다.

⚠ **⟨개정 2026-09-24 · D10 실행 원장⟩ 「이 단위는 읽기만 한다」가 더는 참이 아니다.**
사전·그래프 조회는 여전히 `READ ONLY` 트랜잭션으로 열리고(`app/dictionaries.py`), 거기에
한 글자도 쓰지 않는다. 쓰는 자리는 **`app/ledger.py` 한 곳뿐**이고 대상은 자기 표
`d10_model_call` 하나다. 그 표가 담는 것은 **호출 자체의 운영 메타데이터**이지 제안도
계보도 아니다 — 「AI 는 제안만 하고 기록하지 않는다」(`CLAUDE.md §3-2`)는 그대로다.
그 경계는 이제 `READ ONLY` 트랜잭션이 아니라 **게이트 `ai-no-lineage-write` 세 층**과
이 체인에 기록 도메인 표가 하나도 없다는 사실이 지킨다.

⚠ 원장 쓰기는 **자기 트랜잭션에서 나고 바로 닫힌다.** 조회 트랜잭션에 얹지 않는다 —
얹으면 원장 실패가 조회를 물들이고, 되돌릴 때 「호출은 실제로 일어났다」는 사실까지
함께 사라진다.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def make_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True, future=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
