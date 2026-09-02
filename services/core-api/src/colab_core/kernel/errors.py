"""오류 봉투 — 모든 4xx/5xx 가 한 형태를 쓴다 (`contracts/schemas/common.json#/$defs/ErrorEnvelope`)."""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse

#: 미구현 두 종 (NIGHT-20260823 §3). 404 를 쓰지 않는다 — 404 는 「경계 밖」이다 (§9-㊱).
NOT_IMPLEMENTED_NO_STORE = "NOT_IMPLEMENTED_NO_STORE"
NOT_IMPLEMENTED_P1 = "NOT_IMPLEMENTED_P1"


def envelope(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    return body


class ApiError(HTTPException):
    """상태코드 + 봉투를 한 자리에서 묶는다."""

    def __init__(self, status_code: int, code: str, message: str,
                 details: dict[str, Any] | None = None) -> None:
        super().__init__(status_code=status_code, detail=envelope(code, message, details))


def unauthorized(message: str = "인증 주체가 없다.") -> ApiError:
    return ApiError(401, "UNAUTHORIZED", message)


def forbidden(message: str) -> ApiError:
    return ApiError(403, "FORBIDDEN", message)


def not_found(message: str = "없거나 연구실 경계 밖이다.") -> ApiError:
    return ApiError(404, "NOT_FOUND", message)


def bad_request(message: str, details: dict[str, Any] | None = None) -> ApiError:
    return ApiError(400, "BAD_REQUEST", message, details)


def conflict(message: str, details: dict[str, Any] | None = None) -> ApiError:
    """409 — 「지금 상태에서는 그 일이 두 번 일어날 수 없다」.

    404(경계 밖)·400(요청이 틀림)과 갈라 쓴다. 등록 전환 두 번(`createDataset`) ·
    본체 파일 교체·삭제 시도(`〈59〉-③`) · 계보 순환이 여기로 온다.
    """
    return ApiError(409, "CONFLICT", message, details)


def payload_too_large(message: str) -> ApiError:
    """413 — 본문이 저장 백엔드의 단일 쓰기 상한을 넘는다 (`〈278〉` — S3 단일 PUT 5 GiB).

    400 과 갈라 쓴다: 요청이 틀린 것이 아니라 **이 입구로는 못 받는 크기**다. 그 크기의
    정문은 프리사인드 전송(`〈277〉`)이고, 메시지가 그쪽을 가리킨다.
    """
    return ApiError(413, "PAYLOAD_TOO_LARGE", message)


def gone(message: str) -> ApiError:
    """410 — 「있었는데 창이 닫혔다 — 다시 발급받으라」 (`〈278〉-(다)` · `getDownloadBytes` 전용).

    404 와 갈라 쓴다: 404 는 「없거나 접근이 회수됐다」(존재를 흘리지 않는다), 410 은 서명은
    맞는데 수명이 지난 티켓이다. 둘을 접으면 화면이 「없다」와 「다시 받으면 된다」를 구분 못 한다.
    """
    return ApiError(410, "GONE", message)


def too_many_attempts(message: str) -> ApiError:
    """429 — 창 안의 실패가 한계를 넘었다 (`PLAN-SoT §9 〈108〉-㉰`).

    401(자격이 틀림)과 갈라 쓴다. 같은 코드로 합치면 「막힌 것」과 「틀린 것」이 구분되지 않아
    사람이 자기 비밀번호를 계속 의심한다.
    """
    return ApiError(429, "TOO_MANY_ATTEMPTS", message)


def error_response(exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=envelope(f"HTTP_{exc.status_code}", str(detail)),
    )
