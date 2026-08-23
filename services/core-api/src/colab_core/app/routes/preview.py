"""미리보기 렌더 **중계** 2 op (`〈63〉-㉮`) — `createPreviewRender` · `getPreviewRender`.

viz-render 는 내부 표면이라 FE 는 이 중계로만 렌더에 닿는다.

**중계만 한다.**
  · 요청/응답은 `core-viz.yaml#RenderRequest`/`RenderJob` 이고 **재선언하지 않는다.**
    같은 모양의 두 번째 선언은 갈라질 표면이다.
  · **타일 URL 을 중계하지 않는다** — 결과의 `tileUrlTemplate` 을 FE 가 직접 소비한다.
    `getRenderTile` 은 이 seam 에 없고, 여기에 대리 경로를 만들지 않는다.
  · **core-api 에 geo 라이브러리를 import 하지 않는다** (`CLAUDE.md §3-4`). 그리는 일은
    전부 viz-render 안이다 — 이 파일은 무엇을 그릴지도 해석하지 않는다.

core-api 가 하는 판정은 **경계 하나뿐**이다 — 대상(`datasetId`·`uploadId`)이 이 연구실의
것인가. 그 확인 없이 중계하면 남의 연구실 파일을 그려 준다.
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Request, Response
from sqlalchemy.orm import Session

from ...domains import d3_catalog, d5_ingestion
from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ..deps import current_subject, scoped_db
from ..relay import RelayUnavailable

router = APIRouter()

#: viz-render 에 닿지 못했을 때의 봉투 코드. `RenderFailureCode` 는 계약에 신설되지 않았고
#: (`NB-B` — Ted 답 대기) **계약을 고치지 않는다.** 기존 `ErrorEnvelope.code` 로 말한다.
RENDER_UNAVAILABLE = "RENDER_UNAVAILABLE"


def _target_in_lab(db: Session, target: dict) -> bool:
    """대상이 이 연구실 것인가. 경계는 RLS 가 이미 걸어 둔 위에서 확인한다."""
    dataset_ref, upload_ref = target.get("datasetId"), target.get("uploadId")
    if dataset_ref is not None:
        return Ulid.is_valid(dataset_ref) and d3_catalog.dataset_exists(db, Ulid(dataset_ref))
    if upload_ref is not None:
        if not Ulid.is_valid(upload_ref):
            return False
        return d5_ingestion.UploadLedgerAdapter(db).find(Ulid(upload_ref)) is not None
    return False


@router.post("/previews", name="createPreviewRender", status_code=202)
def create_preview_render(request: Request, response: Response, body: dict = Body(...),
                          subject: Subject = Depends(current_subject),
                          db: Session = Depends(scoped_db)) -> dict:
    """202 + `RenderJob`. 대상은 `datasetId` 또는 `uploadId` **정확히 하나**다 —
    등록하지 않은 업로드(S-08)도 대상이 된다."""
    target = body.get("target")
    if not isinstance(target, dict):
        raise errors.bad_request("target 이 없다.")
    has_dataset = target.get("datasetId") is not None
    has_upload = target.get("uploadId") is not None
    if has_dataset == has_upload:
        raise errors.bad_request("target 은 datasetId 또는 uploadId 정확히 하나다.")
    style = body.get("style")
    if not isinstance(style, dict) or not style.get("palette"):
        # `style.palette` 는 required 다. **값 집합은 viz-render 소유**라 여기서 만들지 않는다.
        raise errors.bad_request("style.palette 가 필요하다.")
    if not _target_in_lab(db, target):
        raise errors.not_found("그릴 대상이 없거나 연구실 경계 밖이다.")

    relay = request.app.state.previews
    if relay is None:
        raise errors.ApiError(503, RENDER_UNAVAILABLE,
                              "그리는 서버에 연결하지 못했다 — 미리보기 없이도 등록은 그대로 된다.")
    try:
        return relay.create(lab_id=str(subject.lab_id), account_id=str(subject.account_id),
                            request=body)
    except RelayUnavailable as e:
        # **그릴 수 없는 것과 등록할 수 없는 것은 다르다** — 여기서 실패해도 등록·다운로드·
        # 계보 확정은 그대로 된다. 가짜 성공을 만들지 않는다.
        raise errors.ApiError(503, RENDER_UNAVAILABLE,
                              f"그리는 서버에 연결하지 못했다: {e}") from None


@router.get("/previews/{renderId}", name="getPreviewRender")
def get_preview_render(request: Request, renderId: str,
                       subject: Subject = Depends(current_subject),
                       db: Session = Depends(scoped_db)) -> dict:
    """진행 단계·완료 결과·실패를 한 형태로 본다. **실패도 200 이고 `failure` 에 이유가 담긴다** —
    그 형태를 만드는 것은 viz-render 이고 여기서는 해석하지 않는다."""
    if not Ulid.is_valid(renderId):
        raise errors.bad_request("renderId 가 정규 ID 가 아니다.")
    relay = request.app.state.previews
    if relay is None:
        raise errors.ApiError(503, RENDER_UNAVAILABLE, "그리는 서버에 연결하지 못했다.")
    try:
        job = relay.get(lab_id=str(subject.lab_id), account_id=str(subject.account_id),
                        render_id=renderId)
    except RelayUnavailable as e:
        raise errors.ApiError(503, RENDER_UNAVAILABLE,
                              f"그리는 서버에 연결하지 못했다: {e}") from None
    if job is None:
        raise errors.not_found("그런 렌더 작업이 없다.")
    return job
