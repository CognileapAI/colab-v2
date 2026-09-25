"""요청 경계의 배선 — 주체 확인 → 트랜잭션 열기 → 스코프 주입 → commit/rollback."""
from __future__ import annotations

from collections.abc import Iterator

from fastapi import Header, Request
from sqlalchemy.orm import Session

from ..kernel import errors
from ..kernel.auth import Subject, bearer_token
from ..kernel.scope import apply_scope
from ..kernel.login_sessions import SessionStoreUnavailable

_REGISTRATION_CLEANUP = 'colab.registration_cleanup'


def defer_registration_cleanup(session, prepared):
    if session.in_nested_transaction() or not session.in_transaction():
        raise ValueError('registration cleanup requires the active root transaction')
    if _REGISTRATION_CLEANUP in session.info:
        raise ValueError('registration cleanup already reserved')
    session.info[_REGISTRATION_CLEANUP]=(session.get_transaction(),prepared)


async def registration_db(request: Request):
    """Only createDataset: commit before response, cleanup only after that root succeeds.

    ⭑ **⟨2026-09-18 develop 동기화⟩ 스코프 주입은 `scoped_db` 와 **한 벌**이어야 한다.**
      이 자리는 `scoped_session` 을 썼기 때문에 develop 이 더한 두 가지 —
      시스템 관리자의 전 연구실 읽기(`operator_read`)와 대상 연구실 선택
      (`prepare_target_scope` · `X-CoLAB-Target-Lab`) — 을 **조용히 건너뛰었다.**
      `createDataset` 은 `_CREATIONS` 라서 관리자는 대상 연구실을 반드시 고르는 자리인데,
      그 선택이 없으면 업로드가 경계 밖으로 보여 「없거나 수명이 다한 업로드다」가 된다.
      배선이 두 벌이면 한쪽만 늙는다 — 그래서 여기서도 같은 두 줄을 그대로 부른다.
    """
    import logging

    from .target_scope import prepare_target_scope

    subject = current_subject(request, request.headers.get('authorization'))
    session: Session = request.app.state.session_factory()
    pending = None
    try:
        session.begin()
        apply_scope(session, subject, operator_read=_operator_read(request, subject))
        await prepare_target_scope(request, session, subject)
        root = session.get_transaction()
        yield session
        pending = session.info.pop(_REGISTRATION_CLEANUP, None)
        if pending and (pending[0] is not root or session.get_transaction() is not root
                        or session.in_nested_transaction() or not root.is_active):
            raise ValueError('registration root transaction changed')
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.info.pop(_REGISTRATION_CLEANUP, None)
        session.close()
    # commit 이 끝난 뒤에만 원본을 치운다 — 실패 경로는 위에서 이미 빠져나갔다.
    if pending:
        try:
            pending[1].cleanup()
        except Exception:
            # Commit already succeeded; no credential/path/exception details in the warning.
            logging.getLogger(__name__).warning('registration_source_cleanup_deferred')


def current_subject(request: Request, authorization: str | None = Header(default=None)) -> Subject:
    """계약의 `sessionSubject` bearer 하나만 본다.

    인증 주체와 원소속은 변경하지 않는다. 관리자 대상 연구실은 별도 요청 스코프에서 검증한다.

    **인증 수단을 알지 못한다.** 판정은 `kernel/authn.py` 의 사슬이 하고, 여기는 그 결과만
    쓴다 (`PLAN-SoT §9 〈90〉-㉮`) — 수단이 늘어도 이 함수는 바뀌지 않는다.
    """
    token = bearer_token(authorization)
    if token is None:
        raise errors.unauthorized("Authorization: Bearer <토큰> 이 없다.")
    try:
        subject = request.app.state.authenticators.resolve(token)
    except SessionStoreUnavailable:
        raise errors.ApiError(503, "SESSION_STORE_UNAVAILABLE",
                              "세션 저장소에 연결할 수 없다.") from None
    if subject is None:
        raise errors.unauthorized("알 수 없는 주체다. 계정은 개발자가 심는다 (P-17).")
    if subject.must_change_password:
        raise errors.ApiError(403, "PASSWORD_CHANGE_REQUIRED",
                              "비밀번호를 변경해야 서비스를 사용할 수 있다.")
    return subject


def current_session_subject(request: Request,
                            authorization: str | None = Header(default=None)) -> Subject:
    token = bearer_token(authorization)
    if token is None:
        raise errors.unauthorized("Authorization: Bearer <토큰> 이 없다.")
    try:
        subject = request.app.state.authenticators.resolve(token)
    except SessionStoreUnavailable:
        raise errors.ApiError(503, "SESSION_STORE_UNAVAILABLE",
                              "세션 저장소에 연결할 수 없다.") from None
    if subject is None:
        raise errors.unauthorized("알 수 없는 주체다.")
    signer = getattr(request.app.state, "tracked_session_signer", None)
    request.state.session_claims = signer.verify_tracked(token) if signer else None
    return subject


def _operator_read(request: Request, subject: Subject) -> bool:
    """SELECT discovery for system admins; writes retain the selected lab boundary."""
    return subject.operator


def session_scoped_db(request: Request) -> Iterator[Session]:
    subject = current_session_subject(request, request.headers.get("authorization"))
    session: Session = request.app.state.session_factory()
    try:
        session.begin()
        apply_scope(session, subject, operator_read=_operator_read(request, subject))
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


async def scoped_db(request: Request):
    """요청 하나 = 트랜잭션 하나. `SET LOCAL` 이라 커넥션이 풀로 돌아갈 때 경계도 같이 사라진다."""
    subject = current_subject(request, request.headers.get("authorization"))
    session: Session = request.app.state.session_factory()
    try:
        session.begin()
        apply_scope(session, subject, operator_read=_operator_read(request, subject))
        from .target_scope import prepare_target_scope
        await prepare_target_scope(request, session, subject)
        yield session
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
