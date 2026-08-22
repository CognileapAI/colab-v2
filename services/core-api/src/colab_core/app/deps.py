"""요청 경계의 배선 — 주체 확인 → 트랜잭션 열기 → 스코프 주입 → commit/rollback."""
from __future__ import annotations

from collections.abc import Iterator

from fastapi import Header, Request
from sqlalchemy.orm import Session

from ..kernel import errors
from ..kernel.auth import Subject, bearer_token
from ..kernel.scope import apply_scope


def current_subject(request: Request, authorization: str | None = Header(default=None)) -> Subject:
    """계약의 `sessionSubject` bearer 하나만 본다.

    **labId 를 헤더·쿼리·바디 어디에서도 받지 않는다.** 경계는 주체에서만 나온다 (P-9·P-10).
    """
    token = bearer_token(authorization)
    if token is None:
        raise errors.unauthorized("Authorization: Bearer <토큰> 이 없다.")
    subject = request.app.state.subjects.resolve(token)
    if subject is None:
        raise errors.unauthorized("알 수 없는 주체다. 계정은 개발자가 심는다 (P-17).")
    return subject


def scoped_db(request: Request) -> Iterator[Session]:
    """요청 하나 = 트랜잭션 하나. `SET LOCAL` 이라 커넥션이 풀로 돌아갈 때 경계도 같이 사라진다."""
    subject = current_subject(request, request.headers.get("authorization"))
    session: Session = request.app.state.session_factory()
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
