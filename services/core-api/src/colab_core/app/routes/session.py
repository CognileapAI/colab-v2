"""세션 두 오퍼레이션 — `createSession`(로그인) · `endSession`(로그아웃).

**수단을 알지 못한다.** 발급은 `kernel/authn.py` 의 `CredentialIssuer` 가 하고, 이 파일은
그 결과를 계약 모양으로 옮겨 적기만 한다 (`PLAN-SoT §9 〈90〉-㉮`). 구글 로그인이 인가되면
바뀌는 것은 그 어댑터뿐이고 이 파일은 그대로다.

**DB 를 열지 않는다.** 로그인은 아직 주체가 없는 자리라 `scoped_db` 를 걸 수 없다 —
경계를 심을 주체가 없기 때문이다. 계정의 실체 확인은 발급 직후 `GET /me` 가 한다.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from ...kernel import errors
from ...kernel.auth import Subject
from ..deps import current_subject

router = APIRouter()


class SessionCredentials(BaseModel):
    """계약 `SessionCredentials` — 칸 하나뿐이다 (P-17 · `〈90〉-㉮`)."""

    accessCode: str = Field(min_length=1, max_length=512)


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
    issued = issuer.issue(body.accessCode)
    if issued is None:
        # 「없는 코드」와 「틀린 코드」를 가르지 않는다 — 가르는 순간 코드의 존재 여부가 샌다.
        raise errors.unauthorized("심어 둔 계정이 아니다. 계정은 개발자가 심는다 (P-17).")
    return {"token": issued.token,
            "expiresAt": issued.expires_at.isoformat().replace("+00:00", "Z")}


@router.delete("/sessions/current", name="endSession", status_code=204,
               response_class=Response)
def end_session(_subject: Subject = Depends(current_subject)) -> Response:
    """무상태 서명 세션이라 서버가 지울 것이 없다. 그 사실을 감추지 않는다 (`〈90〉-㉳`).

    그래도 **주체는 요구한다** — 인증 없이 도는 표면을 하나라도 늘리지 않는다.
    """
    return Response(status_code=204)
