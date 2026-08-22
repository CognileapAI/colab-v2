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


def error_response(exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=envelope(f"HTTP_{exc.status_code}", str(detail)),
    )
