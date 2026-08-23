"""호출자 신원 확인 — 서비스 자격 증명이지 사람의 세션이 아니다 (계약 `serviceToken`).

**검사 대상 0건을 통과로 세지 않는다** — 토큰이 설정되지 않은 앱은 뜨지 않는다
(`kernel/config.py`). 여기서 조용히 열어 두면 그것이 곧 green-by-skip 이다.
"""
from __future__ import annotations

from fastapi import Request

from ..kernel import errors, signing


def _require_configured(settings) -> None:
    """**배선이 없으면 열지 않는다.** 「없으니 통과」가 곧 green-by-skip 이다.

    타일 서명 비밀도 여기서 본다 — 비밀이 없으면 `createRender` 가 서명을 못 실어
    **쓸 수 없는 `tileUrlTemplate`** 을 발급하게 된다. 그 상태로 202 를 내면 FE 는
    「받았는데 타일이 전부 401」이라는, 이 결정이 막으려던 바로 그 자리에 다시 선다.
    """
    if not settings.service_token:
        raise errors.ApiError(503, "SERVICE_TOKEN_UNCONFIGURED",
                              "이 인스턴스에 서비스 자격 증명이 배선되지 않았다.")
    if not settings.tile_signing_secret:
        raise errors.ApiError(503, TILE_SIGNING_UNCONFIGURED,
                              "이 인스턴스에 타일 서명 비밀이 배선되지 않았다.")


TILE_SIGNING_UNCONFIGURED = "TILE_SIGNING_UNCONFIGURED"


def require_caller(request: Request) -> None:
    settings = request.app.state.settings
    _require_configured(settings)
    expected = settings.service_token
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise errors.unauthorized()
    if token != expected:
        raise errors.unauthorized("서비스 자격 증명이 맞지 않는다.")


def require_caller_or_tile_signature(request: Request) -> None:
    """**타일 경로 전용** (`〈68〉-ⓑ`) — 서비스 토큰 **또는** 이 렌더의 유효한 서명.

    나머지 렌더 표면은 `require_caller` 그대로다. 여기만 넓히는 근거는 계약이다 —
    타일만 core-api 를 통과하지 않고 CDN 뒤에 선다(`core-viz.yaml`).

    **작업 조회보다 먼저 선다.** 인증을 뒤에 두면 404/410 이 「그 렌더가 있느냐」를
    인증 없이 알려 주는 신탁(oracle)이 된다.
    """
    settings = request.app.state.settings
    _require_configured(settings)

    render_id = request.path_params.get("renderId", "")
    ok = signing.verify(settings.tile_signing_secret, render_id,
                        request.query_params.get(signing.EXP_PARAM),
                        request.query_params.get(signing.SIG_PARAM))
    if ok is True:
        return
    if ok is None:
        raise errors.unauthorized("타일 주소의 서명이 만료됐다. 미리보기를 다시 그려 주세요.")

    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() == "bearer" and token and token == settings.service_token:
        return
    raise errors.unauthorized("타일 주소의 서명이 없거나 맞지 않는다.")
