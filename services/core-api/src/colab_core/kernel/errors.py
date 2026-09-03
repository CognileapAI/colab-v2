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


def gone(message: str = "이 데이터는 지워졌어요.") -> ApiError:
    """410 — **자기 연구실의 묘비 하나에만** 쓴다 (Ted 판정 2026-09-03 · 17차 해제).

    404(「없거나 경계 밖」)와 갈라 쓰는 자리가 **한 칸뿐**인 이유는 누설 면적이다 —
    보는 사람이 이미 그 행을 보고 있던 연구실에서는 「지워졌다」가 새로 알리는 사실이
    없다. 남의 연구실 묘비·남의 연구실 생존·있었던 적 없는 id **셋은 그대로 404** 이고,
    셋을 가르는 순간 그 자체가 존재의 누설이 된다 (P-9·P-10).
    """
    return ApiError(410, "GONE", message)


def bad_request(message: str, details: dict[str, Any] | None = None) -> ApiError:
    return ApiError(400, "BAD_REQUEST", message, details)


def conflict(message: str, details: dict[str, Any] | None = None) -> ApiError:
    """409 — 「지금 상태에서는 그 일이 두 번 일어날 수 없다」.

    404(경계 밖)·400(요청이 틀림)과 갈라 쓴다. 등록 전환 두 번(`createDataset`) ·
    본체 파일 교체·삭제 시도(`〈59〉-③`) · 계보 순환이 여기로 온다.
    """
    return ApiError(409, "CONFLICT", message, details)


def too_many_attempts(message: str) -> ApiError:
    """429 — 창 안의 실패가 한계를 넘었다 (`PLAN-SoT §9 〈108〉-㉰`).

    401(자격이 틀림)과 갈라 쓴다. 같은 코드로 합치면 「막힌 것」과 「틀린 것」이 구분되지 않아
    사람이 자기 비밀번호를 계속 의심한다.
    """
    return ApiError(429, "TOO_MANY_ATTEMPTS", message)


class InputError(Exception):
    """**입력이 규칙에 맞지 않다** — 400 으로 나간다 (`CODE-REVIEW-20260903` #12).

    ⚠ **`ValueError` 를 통째로 400 에 매지 않는다.** `ValueError` 는 라이브러리·계산 실패도
    함께 던지는 넓은 형이고, 그것까지 400 으로 접으면 **서버 결함이 「네 요청이 틀렸다」로
    위장**한다 — 그 순간 결함은 감시에서 사라지고 사용자는 고칠 수 없는 값을 고치려 든다.
    그래서 형을 따로 세운다: 여기 걸리는 것은 **누군가가 입력 오류라고 판정한 것뿐**이다.

    `ApiError`(=`HTTPException`)와 갈라 두는 이유 — 이 형은 **커널·도메인이 던진다.**
    커널이 HTTP 를 알면 그 층은 더 이상 교체 가능하지 않다. 상태코드로 바꾸는 일은
    `app/main.py` 의 핸들러 한 자리가 한다.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


def input_error_response(exc: InputError) -> JSONResponse:
    return JSONResponse(status_code=400,
                        content=envelope("BAD_REQUEST", exc.message, exc.details))


#: `IntegrityError` 가 사용자에게 되는 말. **하나로 고정한다** — 화면이 분기하는 데는
#: 안정된 코드 하나면 충분하고, 그 이상은 전부 저장 내부의 누출이다.
INTEGRITY_MESSAGE = "요청한 값이 저장 규칙에 맞지 않아요. 값을 확인해 주세요."

#: CHECK 위반(`23514`)이 사용자에게 되는 말. 유니크 위반과 **문장을 가른다** —
#: 「이미 있어요」와 「그 값이 아니에요」는 사람이 할 일이 서로 다르다. 여기도 값·제약
#: 이름은 담지 않는다 (`INTEGRITY_MESSAGE` 와 같은 규칙).
INTEGRITY_INPUT_MESSAGE = "요청한 값이 허용된 값이 아니에요. 값을 확인해 주세요."


def integrity_error_response() -> JSONResponse:
    """유니크 위반(`23505`) → **409**. **SQL 도 제약 이름도 본문에 싣지 않는다.**

    드라이버의 예외 문자열에는 문장 전문·표 이름·열 이름·제약 이름·키 값이 들어 있다.
    그대로 실어 보내면 화면의 네트워크 탭에서 스키마가 읽힌다 — 사람에게는 아무 쓸모가
    없고 공격자에게만 쓸모가 있다. **사유는 서버 로그에 남고, 본문에는 코드만 간다.**
    """
    return JSONResponse(status_code=409, content=envelope("CONFLICT", INTEGRITY_MESSAGE))


def error_response(exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=envelope(f"HTTP_{exc.status_code}", str(detail)),
    )
