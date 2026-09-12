"""세션 두 오퍼레이션 — `createSession`(로그인) · `endSession`(로그아웃).

**수단을 알지 못한다.** 발급은 `kernel/authn.py` 의 `CredentialIssuer` 가 하고, 이 파일은
그 결과를 계약 모양으로 옮겨 적기만 한다 (`PLAN-SoT §9 〈90〉-㉮`). 구글 로그인이 인가되면
바뀌는 것은 그 어댑터뿐이고 이 파일은 그대로다.

**DB 를 열지 않는다.** 로그인은 아직 주체가 없는 자리라 `scoped_db` 를 걸 수 없다 —
경계를 심을 주체가 없기 때문이다. 계정의 실체 확인은 발급 직후 `GET /me` 가 한다.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.exc import SQLAlchemyError

from ...kernel import errors
from ...kernel.auth import Subject, bearer_token
from ...kernel.authn import LoginAttempt, client_key
from ...kernel.login_sessions import SessionStoreUnavailable
from ..deps import current_session_subject

router = APIRouter()


class SessionCredentials(BaseModel):
    """계약 `SessionCredentials` — 두 형태 중 **정확히 하나** (`〈107〉-㉮` · `〈108〉-㉮`).

    ㈎ `accountName` ＋ `password`  ㈏ `accessCode`
    """

    model_config = ConfigDict(extra="forbid")

    accountName: str | None = Field(default=None, min_length=1, max_length=320)
    password: str | None = Field(default=None, min_length=1, max_length=512)
    accessCode: str | None = Field(default=None, min_length=1, max_length=512)

    @model_validator(mode="after")
    def exactly_one_form(self) -> SessionCredentials:
        password_form = (
            self.accountName is not None
            and self.password is not None
            and self.accessCode is None
        )
        code_form = (
            self.accessCode is not None
            and self.accountName is None
            and self.password is None
        )
        if not (password_form or code_form):
            raise ValueError(
                "`accountName`＋`password` 또는 `accessCode` 중 정확히 하나를 보낸다."
            )
        return self

    def attempt(self) -> LoginAttempt:
        """**갈래를 여기서 판단하지 않는다** — 입력을 한 벌로 묶어 발급 사슬에 넘긴다."""
        return LoginAttempt(access_code=self.accessCode,
                            account_name=self.accountName, password=self.password)


class RevokeSession(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revocationToken: str = Field(min_length=32, max_length=256)


@router.post("/sessions", name="createSession", status_code=201)
def create_session(body: SessionCredentials, request: Request) -> dict:
    issuer = request.app.state.session_issuer
    if issuer is None:
        # 서명 비밀값이 없다. **가짜 토큰을 내리지 않는다** — 없는 것을 있는 척하는 순간
        # 화면은 로그인에 성공했다고 믿고, 다음 요청 전부가 401 로 흩어진다.
        raise errors.ApiError(
            500, "SESSION_UNAVAILABLE",
            "세션 서명 비밀값이 설정되지 않아 로그인을 세울 수 없다 "
            "(COLAB_CORE_SESSION_SECRET).")
    attempt = body.attempt()
    limiter = request.app.state.login_limiter
    # **버킷 둘을 함께 센다** (`CODE-REVIEW-20260903` #5) — ⑴ 로그인이 겨냥한 자격 ·
    # ⑵ 부른 클라이언트. 하나만 두면 각각 뚫린다: 자격만 세면 코드를 갈아 가며 하는 열거에
    # 브레이크가 없고, 클라이언트만 세면 여러 곳에서 한 계정을 두드리는 것을 못 센다.
    # 한도·창은 **같은 값**을 쓴다 — 두 숫자를 두면 어느 쪽이 걸렸는지 아무도 모른다.
    try:
        key_for = getattr(issuer, "rate_limit_key", None)
        buckets = [key_for(attempt) if key_for is not None else attempt.key]
        client = client_key(request.headers.get("x-forwarded-for"))
        if client:
            buckets.append(client)
    except SQLAlchemyError:
        raise errors.ApiError(503, "SESSION_STORE_UNAVAILABLE",
                              "세션 저장소에 연결할 수 없다.") from None
    if any(limiter.blocked(bucket) for bucket in buckets):
        # 사전 추측을 **느리게** 만드는 최소 보완이다 (`〈108〉-㉰`). 한계는 `kernel/throttle.py`.
        # **어느 버킷이 걸렸는지 말하지 않는다** — 말하면 열거 도구가 그 답으로 학습한다.
        raise errors.too_many_attempts(
            "로그인 시도가 너무 잦다. 잠시 뒤에 다시 시도한다.")
    try:
        issued = issuer.issue(attempt)
    except (SessionStoreUnavailable, SQLAlchemyError):
        raise errors.ApiError(503, "SESSION_STORE_UNAVAILABLE",
                              "세션 저장소에 연결할 수 없다.") from None
    if issued is None:
        # 「없는 계정」과 「틀린 비밀번호」를 가르지 않는다 — 가르는 순간 계정의 존재가 샌다.
        # ⚠ **입력값을 메시지에 담지 않는다** (Ted 2026-08-26 조건 1 — 로그·오류에 값 미출력).
        for bucket in buckets:
            limiter.record_failure(bucket)
        raise errors.unauthorized("심어 둔 계정이 아니다. 계정은 개발자가 심는다 (P-17).")
    for bucket in buckets:
        limiter.clear(bucket)
    result = {"token": issued.token,
              "expiresAt": issued.expires_at.isoformat().replace("+00:00", "Z")}
    if hasattr(issued, "session_id"):
        result.update(sessionId=str(issued.session_id),
                      revocationToken=issued.revocation_token)
    return result


@router.delete("/sessions/current", name="endSession", status_code=204,
               response_class=Response)
def end_session(request: Request,
                _subject: Subject = Depends(current_session_subject)) -> Response:
    claims = getattr(request.state, "session_claims", None)
    sessions = request.app.state.login_sessions
    if claims is None or sessions is None:
        raise errors.unauthorized("서버에 등록된 브라우저 세션이 아니다.")
    try:
        sessions.revoke(claims.session_id)
    except SessionStoreUnavailable:
        raise errors.ApiError(503, "SESSION_STORE_UNAVAILABLE",
                              "세션 저장소에 연결할 수 없다.") from None
    return Response(status_code=204)


@router.post("/sessions/revoke", name="revokeSession", status_code=204,
             response_class=Response)
def revoke_session(body: RevokeSession, request: Request) -> Response:
    sessions = request.app.state.login_sessions
    if sessions is None:
        raise errors.ApiError(503, "SESSION_STORE_UNAVAILABLE",
                              "세션 저장소가 설정되지 않았다.")
    try:
        sessions.revoke_by_capability(body.revocationToken)
    except ValueError:
        raise errors.bad_request("종료 자격 형식이 올바르지 않다.") from None
    except SessionStoreUnavailable:
        raise errors.ApiError(503, "SESSION_STORE_UNAVAILABLE",
                              "세션 저장소에 연결할 수 없다.") from None
    return Response(status_code=204)
