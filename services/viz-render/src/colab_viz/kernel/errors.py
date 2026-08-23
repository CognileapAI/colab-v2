"""오류 봉투 — 모든 4xx/5xx 가 한 형태다 (`contracts/schemas/common.json#/$defs/ErrorEnvelope`).

`ErrorEnvelope.code` 는 계약에서 **enum 없는 자유 문자열**이다. 그래서 정본 §9 의
실패 3종(그리는 서버 연결 불가·시간 초과·알 수 없는 오류)을 **계약 개정 없이** 코드로
가를 수 있다 — `RenderFailureCode` 신설(`NB-B`)이 없어도 seam 이 성립한다.
값 자체는 정본에 없으므로 `[정본 무근거]`이고 viz-render 소유다 (`domains/.../failures.py`).
"""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse

UNAUTHORIZED = "UNAUTHORIZED"
NOT_FOUND = "NOT_FOUND"
BAD_REQUEST = "BAD_REQUEST"
RENDER_TOO_LARGE = "RENDER_TOO_LARGE"
NOT_RENDERABLE = "NOT_RENDERABLE"
RENDER_NOT_READY = "RENDER_NOT_READY"
RENDER_EXPIRED = "RENDER_EXPIRED"


def envelope(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    return body


class ApiError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str,
                 details: dict[str, Any] | None = None) -> None:
        super().__init__(status_code=status_code, detail=envelope(code, message, details))


def unauthorized(message: str = "호출자 신원을 확인할 수 없다.") -> ApiError:
    return ApiError(401, UNAUTHORIZED, message)


def not_found(message: str = "없거나 경계 밖이다.") -> ApiError:
    return ApiError(404, NOT_FOUND, message)


def bad_request(message: str, details: dict[str, Any] | None = None) -> ApiError:
    return ApiError(400, BAD_REQUEST, message, details)


def error_response(exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(status_code=exc.status_code,
                        content=envelope(f"HTTP_{exc.status_code}", str(detail)))
