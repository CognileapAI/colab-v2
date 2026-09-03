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


# ── 경계 (`CODE-REVIEW-20260903` #1) ──────────────────────────────────────────
#: core-api `app/relay._scope_headers` 가 **모든 중계 호출에** 싣는 두 헤더의 이름.
#: ⚠ 이름을 여기서 새로 짓지 않는다 — 저쪽이 이미 쓰고 있는 값의 축자다.
LAB_HEADER = "X-CoLAB-Lab"
ACCOUNT_HEADER = "X-CoLAB-Account"


def tenant_scope(request: Request) -> tuple[str, str]:
    """**경계를 읽는 한 자리** — (연구실, 계정). 없으면 400 이고, 열어 주지 않는다.

    ⭑ ⟨2026-09-03 · 코드리뷰 #1⟩ 종전에는 이 seam 이 두 헤더를 **어디서도 읽지 않았다.**
    보내는 쪽(core-api)은 「경계는 중계에도 실린다」고 적어 두고 실제로 실어 보냈는데
    받는 쪽에 그것을 읽는 줄이 0 이었고, core-api 는 그 응답을 경계 확인으로 삼았다 —
    **양쪽 다 상대가 본다고 믿었다.**

    ⚠ **400 이지 401 이 아니다.** 자격 증명(`Authorization`)은 이미 통과한 상태이고
    (`require_caller` 가 라우터 의존으로 먼저 선다), 빠진 것은 **요청이 말했어야 할
    경계**다. 401 로 내면 부르는 쪽이 토큰을 의심하며 배선이 빠진 것을 못 찾는다.

    ⚠ **계정은 400 의 근거가 아니다** — 경계 판정에 쓰이는 것은 연구실 하나이고, 계정은
    「누가 불렀나」의 출처 표시다. 판정에 안 쓰는 값으로 문을 닫으면 닫히는 것 없이
    실패 경로만 하나 는다.
    """
    lab = (request.headers.get(LAB_HEADER) or "").strip()
    if not lab:
        raise errors.ApiError(
            400, errors.TENANT_SCOPE_MISSING,
            "경계를 말하지 않은 요청이다 — 어느 연구실의 것인지 없이 그리지 않는다.",
            {"header": LAB_HEADER})
    return lab, (request.headers.get(ACCOUNT_HEADER) or "").strip()


def same_lab_or_missing(job, lab: str):
    """**남의 것은 「없다」다.** 403 으로 내면 그 `renderId` 가 존재한다는 사실이 샌다.

    ⚠ 부르는 자리마다 문구를 다시 쓰지 않는다 — 「없다」와 「남의 것이다」가 **글자까지
    같아야** 응답 문구로도 갈리지 않는다.
    """
    if job is None or job.lab != lab:
        raise errors.not_found("그런 렌더 작업이 없다.")
    return job
