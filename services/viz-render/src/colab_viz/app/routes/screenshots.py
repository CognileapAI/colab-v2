"""`createScreenshot` — 계약 `core-viz.yaml` `/screenshots` 그대로.

**권한은 여기서 판정하지 않는다**(계약 산문) — `업로드·편집` 판정은 core-api 의 몫이고
이 seam 이 보는 것은 서비스 자격 증명 하나다. 타일과 달리 서명 우회로도 두지 않는다:
스크린샷은 CDN 뒤에 서지 않고 core-api 를 통과한다.

**계약에 없는 상태 코드를 지어내지 않는다** — `/screenshots` 의 응답은
200·400·401·404·409·503 이고 410 이 없다. 수명이 다한 렌더는 **없는 렌더**로 404 다.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...domains.d7_visualization import jobs, screenshot
from ...kernel import errors
from ..deps import require_caller

router = APIRouter(tags=["screenshot"], dependencies=[Depends(require_caller)])

_Ulid = Annotated[str, Field(pattern=r"^[0-9A-HJKMNP-TV-Z]{26}$")]


class ScreenshotLayer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    renderId: _Ulid
    #: 얹은 층의 기본은 0.55 다 — 아래층을 비춰 봐야 비교가 된다 (정본 §8 얹은 층).
    opacity: float = Field(default=0.55, ge=0, le=1)


class Bounds(BaseModel):
    model_config = ConfigDict(extra="forbid")
    west: float = Field(ge=-180, le=180)
    south: float = Field(ge=-90, le=90)
    east: float = Field(ge=-180, le=180)
    north: float = Field(ge=-90, le=90)

    @model_validator(mode="after")
    def _ordered(self):
        if self.east <= self.west or self.north <= self.south:
            raise ValueError("경계가 뒤집혔거나 폭이 0 이다")
        return self


class Viewport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    width: int = Field(ge=1, le=screenshot.MAX_SIDE)
    height: int = Field(ge=1, le=screenshot.MAX_SIDE)
    bounds: Bounds


class ScreenshotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    layers: list[ScreenshotLayer] = Field(min_length=1)
    viewport: Viewport


@router.post("/screenshots")
def create_screenshot(body: ScreenshotRequest, request: Request) -> Response:
    """지금 장면을 이미지로 뽑는다. **첫 항목이 맨 아래 층**이다."""
    store = request.app.state.jobs
    scene: list[tuple] = []
    for layer in body.layers:
        job = store.get(layer.renderId)
        if job is None or job.expired:
            # 「있었는데 지났다」와 「없다」를 화면에 가르지 않는다 — 계약에 410 이 없다.
            raise errors.not_found("그런 렌더 작업이 없다.")
        if job.status != jobs.STATUS_DONE or job.rendered is None:
            raise errors.ApiError(409, errors.RENDER_NOT_READY,
                                  "장면에 담긴 층 중 아직 완료되지 않은 것이 있다.",
                                  {"renderId": layer.renderId, "status": job.status})
        scene.append((job.rendered, layer.opacity))

    b = body.viewport.bounds
    png = screenshot.compose(scene, body.viewport.width, body.viewport.height,
                             (b.west, b.south, b.east, b.north))
    # 장면은 그때그때 다르다 — 캐시하지 않는다.
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "no-store"})
