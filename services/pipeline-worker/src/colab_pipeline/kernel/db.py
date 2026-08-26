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


def clear_scope(session: Session) -> None:
    """스코프 **해제**. 빈 값은 `current_lab_id()` 의 정규식을 통과하지 못해 NULL 이 되고,
    모든 경계 정책이 `lab_id = NULL` = false 로 닫힌다 — **기본 거부로 되돌아간다.**

    `apply_scope` 가 `SET LOCAL` 이라 트랜잭션이 끝나면 어차피 사라지지만, **워커가 한 바퀴에
    연구실 여럿을 도는 뒤로는 그 암묵을 믿지 않는다**(Ted 판정 2026-08-26 ㈑ — 워커는 한 번에
    하나의 연구실 스코프만 갖는다). 해제를 눈에 보이는 한 줄로 둔다.
    """
    session.execute(_SET_LOCAL, {"name": GUC_LAB, "value": ""})
    session.execute(_SET_LOCAL, {"name": GUC_ACCOUNT, "value": ""})


def scoped_labs(session: Session) -> list[str]:
    """처리 대상 연구실 목록. **스코프 없이 읽는 유일한 표가 `d1_lab` 이다.**

    `d1_lab` 은 테넌트 루트 그 자체라 RLS 대상이 아니다 —
    `gates/config/rls-allowlist.toml` `[platform].allow_no_rls` 가 그 근거이고, 그것이
    이 배선에 **BYPASSRLS 롤도 이벤트 표 면제도 마이그레이션도 필요 없는** 이유다.
    이 목록은 이름표일 뿐이고, 연구실의 **자료**는 스코프를 세운 뒤에만 보인다.
    """
    return [str(v) for v in session.execute(text("SELECT id FROM d1_lab ORDER BY id"))
            .scalars().all()]
