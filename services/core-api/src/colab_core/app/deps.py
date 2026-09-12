"""요청 경계의 배선 — 주체 확인 → 트랜잭션 열기 → 스코프 주입 → commit/rollback."""
from __future__ import annotations

from collections.abc import Iterator

from fastapi import Header, Request
from sqlalchemy.orm import Session

from ..kernel import errors
from ..kernel.auth import Subject, bearer_token
from ..kernel.scope import apply_scope
from ..kernel.login_sessions import SessionStoreUnavailable


def current_subject(request: Request, authorization: str | None = Header(default=None)) -> Subject:
    """계약의 `sessionSubject` bearer 하나만 본다.

    **labId 를 헤더·쿼리·바디 어디에서도 받지 않는다.** 경계는 주체에서만 나온다 (P-9·P-10).

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


#: 운영자 읽기 스코프를 켜는 **유일한 조건** — 읽기 메서드다. 목록에 없는 메서드는 쓰기로 본다.
_READ_METHODS = frozenset(("GET", "HEAD"))

#: 읽기 메서드인데도 스코프를 **열지 않는** 자리 — 경로의 마지막 칸이 이것이면 반출이다
#: (`routes/download.py` 의 `downloadDataset`·`downloadDatasetFile`). 두 op 은 GET 이지만
#: 하는 일은 「바이트를 가져갈 자격(티켓)을 발급하고 `d8_download` 에 한 줄 적는 것」이다.
#: **열람과 반출은 다른 일이다** — 승인 intent 가 연 것은 「모든 연구실을 **읽는다**」이고,
#: 남의 연구실 자료를 통째로 내려받는 것은 거기에 없다. 켜면 거절할 자리가 아예 사라진다 —
#: RLS 가 행을 보여 주므로 `_accessible_dataset` 의 404 가 서지 않고, 이력의 `lab_id` 는
#: `current_lab_id()`(＝운영자 자기 연구실)라 **자료 주인의 원장에는 아무 흔적도 안 남는다.**
_EXPORT_TAIL = "download"


def _operator_read(request: Request, subject: Subject) -> bool:
    """운영자의 **읽기 요청에만** 전 연구실 스코프를 연다 (승인 intent 2026-09-12).

    ⚠ 쓰기 요청에서는 켜지 않는다. 켜면 「남의 연구실 행을 읽어서 자기 연구실에 적어 넣는」
    경로가 열린다 — 예를 들어 남의 데이터셋을 자기 프로젝트에 붙이는 것은 `lab_boundary` 의
    WITH CHECK 을 통과해 버린다(적히는 행의 `lab_id` 는 자기 연구실이므로). RLS 가 막아 주는
    것은 **남의 연구실에 쓰는 것**이지 남의 것을 보고 자기 자리에 쓰는 것이 아니다.

    ⚠ **반출 경로에서도 켜지 않는다** — 위 `_EXPORT_TAIL` 주석이 이유다. 판정을 여기 한 자리에
    두는 이유: 라우트마다 「내 연구실인가」를 다시 적으면 새 반출 op 이 생길 때 그 줄이 빠진다.
    """
    if not (subject.operator and request.method.upper() in _READ_METHODS):
        return False
    return request.url.path.rstrip("/").rsplit("/", 1)[-1] != _EXPORT_TAIL


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


def scoped_db(request: Request) -> Iterator[Session]:
    """요청 하나 = 트랜잭션 하나. `SET LOCAL` 이라 커넥션이 풀로 돌아갈 때 경계도 같이 사라진다."""
    subject = current_subject(request, request.headers.get("authorization"))
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
