"""`createRender` · `getRender` · `getRenderTile` — 계약 `core-viz.yaml` 그대로.

요청 모델에 **좌표계·격자·픽셀·밴드·NoData 가 없다.** 그런 값이 필요해지면 그것은
core 가 파일을 해석하고 있다는 뜻이고, 계약은 그때 멈추라고 적었다.
"""
from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Request, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...domains.d7_visualization import jobs, palettes, tiles
from ...domains.d7_visualization.failures import TOO_LARGE_MESSAGE
from ...kernel import errors
from ...kernel.ids import new_ulid
from ...ports.source import TargetNotFound
from .. import deps
from ..deps import require_caller, require_caller_or_tile_signature

router = APIRouter(tags=["render"], dependencies=[Depends(require_caller)])

#: **타일만 따로 선다** (`〈68〉-ⓑ`). 서비스 토큰 `Depends` 를 이 경로에도 걸면
#: 브라우저 지도 위젯이 도달할 수 없다 — 계약대로인데 실배포에서 전량 401 이 된다.
#: 라우터를 가르는 것은 「나머지 표면은 서비스 토큰 그대로」를 **기계가 지키게** 하려는 것이다.
tile_router = APIRouter(tags=["tile"],
                        dependencies=[Depends(require_caller_or_tile_signature)])

_Ulid = Annotated[str, Field(pattern=r"^[0-9A-HJKMNP-TV-Z]{26}$")]


class FileNameHint(BaseModel):
    """`fileId` 의 **표시용 원래 이름** (`core-viz.yaml#RenderTarget.fileNames`).

    원장은 core-api 가 소유하므로 D7 은 이름을 읽을 길이 없다(불변규칙 1) — 식별자와
    같은 자리에 이름도 실려 온다. **표시에만 쓴다** — 바이트·배치·캐시 키에 닿지 않는다.
    """
    model_config = ConfigDict(extra="forbid")
    fileId: _Ulid
    fileName: str = Field(min_length=1)


class RenderTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    datasetId: _Ulid | None = None
    uploadId: _Ulid | None = None
    fileIds: list[_Ulid] | None = Field(default=None, min_length=1)
    #: **선택**이다 — 없으면 종전 동작 그대로다(계약 산문 축자).
    fileNames: list[FileNameHint] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _exactly_one(self):
        if (self.datasetId is None) == (self.uploadId is None):
            raise ValueError("datasetId 와 uploadId 중 정확히 하나를 넣는다")
        return self

    def display_names(self) -> dict[str, str]:
        """`fileId → 표시 이름`. 힌트가 없으면 빈 map 이고, 그때 읽기는 디스크 이름을 쓴다."""
        return {h.fileId: h.fileName for h in (self.fileNames or [])}


class RenderStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    palette: str = Field(min_length=1)
    classCount: int = Field(default=palettes.DEFAULT_CLASS_COUNT,
                            ge=palettes.MIN_CLASS_COUNT, le=palettes.MAX_CLASS_COUNT)


class RenderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: RenderTarget
    variable: str | None = Field(default=None, min_length=1)
    instant: str | None = None
    style: RenderStyle
    withoutReferenceGrid: bool = False


@router.post("/renders", status_code=202)
def create_render(body: RenderRequest, request: Request) -> dict:
    # **경계를 가장 먼저 읽는다** — 대상을 해석한 뒤에 읽으면 헤더 없는 요청이 「그 대상이
    # 있느냐」를 404/200 으로 먼저 알려 주는 신탁이 된다.
    lab, account = deps.tenant_scope(request)
    settings = request.app.state.settings
    source = request.app.state.source
    try:
        target = source.resolve(dataset_id=body.target.datasetId,
                                upload_id=body.target.uploadId,
                                file_ids=body.target.fileIds)
    except TargetNotFound as e:
        raise errors.not_found(str(e)) from e

    total = sum(p.size_bytes for p in target.parts)
    if total > settings.max_render_bytes:
        target_key = "uploadId" if body.target.uploadId else "datasetId"
        jobs.log.warning(
            "render_rejected lab=%s account=%s %s=%s reason=declared_size "
            "limitBytes=%s targetBytes=%s", lab, account, target_key,
            body.target.uploadId or body.target.datasetId,
            settings.max_render_bytes, total)
        raise errors.ApiError(413, errors.RENDER_TOO_LARGE, TOO_LARGE_MESSAGE,
                              {"limitBytes": settings.max_render_bytes,
                               "targetBytes": total})

    if body.style.palette not in {p.key for p in palettes.PALETTES}:
        raise errors.bad_request(
            "모르는 팔레트다 — `listPalettes` 가 돌려준 값을 쓴다.",
            {"palette": body.style.palette})

    spec = jobs.RenderSpec(
        target=target, palette=body.style.palette, class_count=body.style.classCount,
        variable=body.variable, instant=body.instant,
        # **표시용 이름만 넘어간다** — 캐시 키(`source_digest`)는 디스크 이름 그대로다.
        display_names=body.target.display_names(),
        without_reference_grid=body.withoutReferenceGrid,
        max_preview_side=settings.max_preview_side,
        deadline_seconds=settings.render_deadline_seconds,
        max_render_bytes=settings.max_render_bytes,
        preview_dir=settings.preview_dir,
        preview_url_base=settings.preview_url_base,
        materialize=source.materialize,
        preview_sink=request.app.state.preview_sink,
    )
    try:
        job = request.app.state.jobs.submit(new_ulid(), spec,
                                            temporary=body.target.uploadId is not None,
                                            lab=lab, account=account)
    except jobs.QueueFull as e:
        raise errors.ApiError(503, errors.PREVIEW_QUEUE_FULL,
                              "미리보기 요청이 많아요. 잠시 뒤 다시 시도해 주세요.") from e
    return job.to_dict()


@router.get("/renders/{renderId}")
def get_render(renderId: _Ulid, request: Request) -> dict:
    """**실패도 200 이다.** 이유는 `failure` 에 담긴다 — 4xx 로 두면 「작업이 없다」와 섞인다.

    ⭑ ⟨2026-09-03 · 코드리뷰 #1⟩ **서명된 타일 주소가 나가는 문이 여기 하나뿐이다.**
    그래서 경계를 여기서 닫으면 타일도 함께 닫힌다 — 타일 경로 자신은 헤더를 못 받는
    자리(브라우저 직접 호출)라 서명만으로 남는다.
    """
    lab, _ = deps.tenant_scope(request)
    job = deps.same_lab_or_missing(request.app.state.jobs.get(renderId), lab)
    return job.to_dict()


@tile_router.get("/renders/{renderId}/tiles/{z}/{x}/{y}.png")
def get_render_tile(request: Request, renderId: _Ulid,
                    z: Annotated[int, Path(ge=0, le=tiles.MAX_ZOOM)],
                    x: Annotated[int, Path(ge=0)],
                    y: Annotated[int, Path(ge=0)]) -> Response:
    """**core-api 를 통과하지 않는 유일한 경로다** — 지도 위젯이 직접 부른다."""
    job = request.app.state.jobs.get(renderId)
    if job is None:
        raise errors.not_found("그런 렌더 작업이 없다.")
    if job.expired:
        raise errors.ApiError(410, errors.RENDER_EXPIRED,
                              "수명이 다한 미리보기예요. 다시 그려 주세요.")
    if job.status != jobs.STATUS_DONE or job.rendered is None:
        raise errors.ApiError(409, errors.RENDER_NOT_READY,
                              "아직 그리는 중이거나 실패한 작업이다. 상태는 조회로 확인한다.",
                              {"status": job.status})
    png = tiles.render_tile(job.rendered, z, x, y)
    # 빈 타일도 200 이다 — 404 로 두면 지도 위젯이 재시도를 반복한다.
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=300"})
