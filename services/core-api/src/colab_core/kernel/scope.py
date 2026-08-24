"""스코프 커널 — 모든 조회에 연구실 경계를 **자동으로** 주입한다 (CLAUDE.md §3-5).

무엇을 하는가
  요청 하나가 트랜잭션 하나를 열고, 그 안에서 `app.current_lab`·`app.current_account` 를
  **트랜잭션 스코프로** 설정한 뒤(`set_config(..., is_local => true)` = `SET LOCAL`),
  요청이 끝나는 자리에서 commit 또는 rollback 한다.

왜 트랜잭션 스코프여야 하는가
  풀 커넥션에 비-LOCAL `SET` 을 쓰면 그 커넥션이 풀로 돌아간 뒤 **다음 요청이 앞 요청의 lab_id 를
  물려받는다.** 한 줄의 실수가 연구실 경계를 통째로 무너뜨리는 자리다 (NIGHT-20260823 §3).
  `SET LOCAL` 은 트랜잭션이 끝나는 순간 사라지므로, 커넥션이 풀로 돌아갈 때 GUC 도 같이 사라진다.

GUC 를 세팅하지 않은 접속이 보는 것
  `db/platform/schema.sql` 의 `current_lab_id()` 가 NULL 을 돌려주고, 모든 경계 정책이
  `lab_id = NULL` = false 가 되어 **한 행도 보이지 않는다.** 기본 거부다.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from .auth import Subject
from .ids import Ulid

GUC_LAB = "app.current_lab"
GUC_ACCOUNT = "app.current_account"

# is_local => true 가 `SET LOCAL` 이다. 값을 문자열 보간하지 않고 바인딩한다 —
# GUC 이름은 상수이고 값만 주체에서 온다.
_SET_LOCAL = text("SELECT set_config(:name, :value, true)")


def apply_scope(session: Session, subject: Subject) -> None:
    """열려 있는 트랜잭션에 경계를 심는다. 주체 밖의 값은 받지 않는다."""
    if not Ulid.is_valid(subject.lab_id) or not Ulid.is_valid(subject.account_id):
        raise ValueError("주체의 ID 가 정규 ID 가 아니다 — 경계를 심지 않는다.")
    session.execute(_SET_LOCAL, {"name": GUC_LAB, "value": str(subject.lab_id)})
    session.execute(_SET_LOCAL, {"name": GUC_ACCOUNT, "value": str(subject.account_id)})


# `SET TRANSACTION READ ONLY` — 검색 실행처럼 **읽기만 하는 자리**를 Postgres 가 지키게 한다.
# 문서로 「여기서는 안 쓴다」고 적는 대신 **쓰기를 거절당하게** 만든다.
_READ_ONLY = text("SET TRANSACTION READ ONLY")


@contextmanager
def read_only_scope(factory: sessionmaker[Session], subject: Subject) -> Iterator[Session]:
    """경계를 심은 **읽기 전용** 트랜잭션. 끝나면 언제나 rollback 한다.

    `scoped_session` 과 갈라 두는 이유 — 요청 트랜잭션은 쓰기를 해야 하는 자리가 있고,
    검색 질의는 **한 줄도 쓰지 않아야 한다.** 같은 트랜잭션에 얹으면 그 성질을 증명할 방법이
    사라진다 (`tests/test_search_execution.py::test_실행기는_읽기만_한다`).
    `READ ONLY` 는 트랜잭션이 열린 직후에만 세울 수 있으므로 경계 주입보다 먼저 온다.
    """
    session = factory()
    try:
        session.begin()
        session.execute(_READ_ONLY)
        apply_scope(session, subject)
        yield session
    finally:
        session.rollback()
        session.close()


@contextmanager
def scoped_session(factory: sessionmaker[Session], subject: Subject) -> Iterator[Session]:
    """요청 경계 = 트랜잭션 경계. 예외가 나면 rollback, 정상 종료면 commit."""
    session = factory()
    try:
        session.begin()
        apply_scope(session, subject)
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
