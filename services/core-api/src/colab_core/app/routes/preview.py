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
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ...domains import d2_access, d3_catalog, d5_ingestion
from . import catalog
from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ..deps import current_subject, scoped_db
from ..relay import RelayRefused, RelayUnavailable

router = APIRouter()

#: viz-render 에 닿지 못했을 때의 봉투 코드. `RenderFailureCode` 는 계약에 신설되지 않았고
#: (`NB-B` — Ted 답 대기) **계약을 고치지 않는다.** 기존 `ErrorEnvelope.code` 로 말한다.
RENDER_UNAVAILABLE = "RENDER_UNAVAILABLE"
#: 저쪽이 거절했는데 **본문을 안 준** 드문 경우에만 쓰는 코드. 정상 경로에서는 viz 의 봉투가
#: 그대로 올라가므로 이 값이 화면에 닿지 않는다 — 상태코드는 사실이니 버리지 않을 뿐이다.
RENDER_REFUSED = "RENDER_REFUSED"


def _refused(exc: RelayRefused) -> JSONResponse:
    """저쪽이 낸 거절을 **해석하지 않고 그대로 올린다** (`CODE-REVIEW-20260903` #8).

    ⚠ **415 NOT_RENDERABLE 의 본문에는 `details.renderableFormats` 가 실려 있다** —
    그것이 사용자가 다음 수를 아는 유일한 길이다. 여기서 503 으로 접으면 화면은
    「서버 장애」만 말하고 사람은 그릴 수 없는 파일을 계속 재시도한다.

    **상태를 지어내지 않는다.** 본문이 없어도 상태는 저쪽이 낸 사실이라 그대로 쓴다.
    """
    body = exc.body if isinstance(exc.body, dict) else errors.envelope(
        RENDER_REFUSED, "그리는 서버가 이 요청을 받아들이지 않았다.")
    return JSONResponse(status_code=exc.status, content=body)


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


@router.get("/preview-palettes", name="listPalettes")
def list_palettes(request: Request,
                  subject: Subject = Depends(current_subject)) -> dict:
    """`RenderStyle.palette` 값의 **유일한 출처** — 중계만 한다 (`〈88〉` 묶음 4).

    ⚠ **이 op 이 없어서 실서버에서 미리보기 렌더가 단 한 번도 시작되지 않았다.**
    `RenderStyle.required` 가 `[palette]` 인데 FE 가 그 값을 얻을 계약 경로가 없었고,
    화면은 목록을 지어내는 대신(옳다) `createRender` 를 아예 안 불렀다
    (`sessions/S1-CONTRACT-GAP-SWEEP.md` `D-1`).

    **경계 판정이 없다** — 팔레트는 연구실에 딸린 값이 아니라 렌더러의 능력이다.
    인증은 건다: 경계 밖에 표면을 열지 않는다.
    """
    relay = request.app.state.previews
    if relay is None:
        raise errors.ApiError(503, RENDER_UNAVAILABLE,
                              "그리는 서버에 연결하지 못했다 — 미리보기 없이도 등록은 그대로 된다.")
    try:
        return relay.palettes(lab_id=str(subject.lab_id), account_id=str(subject.account_id))
    except RelayRefused as e:
        return _refused(e)
    except RelayUnavailable as e:
        # **빈 목록을 내지 않는다.** 0건은 「고를 것이 없다」는 답이고, 참인 것은
        # 「물어보지 못했다」이다 — `〈87〉-㉯` 가 검색에서 금지한 접기와 같은 모양이다.
        raise errors.ApiError(503, RENDER_UNAVAILABLE,
                              f"그리는 서버에 연결하지 못했다: {e}") from None


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
    except RelayRefused as e:
        # **그릴 수 없는 파일은 장애가 아니다** — 저쪽의 상태·봉투가 그대로 화면까지 간다.
        return _refused(e)
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


@router.post("/preview-screenshots", name="createPreviewScreenshot")
def create_preview_screenshot(request: Request, body: dict = Body(...),
                              subject: Subject = Depends(current_subject),
                              db: Session = Depends(scoped_db)) -> Response:
    """`createScreenshot` 중계 (`〈231〉` · **11차 동결 해제**).

    ⚠ **이 op 이 없어서 정본이 요구하는 컨트롤이 계약상 도달 불가였다** —
    서버(`core-viz.yaml#createScreenshot`)는 서 있는데 `fe-core.yaml` 에 중계가 0건이라
    화면이 닿을 길이 없었다. `listPalettes` 부재(`〈88〉` 묶음 4)와 같은 모양이다.

    **core-api 가 하는 판정은 둘뿐이다.**
      ⑴ **편집 권한** — 정본이 스크린샷을 편집 권한자 컨트롤로 둔다
        (`Policy_데이터셋_상세 §6`). `core-viz.yaml` 이 「권한 판정은 core-api 가 한다」로
        그 자리를 여기에 넘겼다. **화면에서 숨긴 것은 서버도 같은 기준으로 막는다**(`§3.3`).
      ⑵ **연구실 경계** — 장면에 담긴 렌더가 이 연구실 것인가. 확인 없이 중계하면
        남의 연구실 그림을 뽑아 준다.

    **그리는 일은 한 줄도 하지 않는다** (`CLAUDE.md §3-4`). 층 합성·픽셀은 viz-render 안이다.
    """
    layers = body.get("layers")
    if not isinstance(layers, list) or not layers:
        raise errors.bad_request("layers 가 없다 — 장면에는 층이 하나 이상 있어야 한다.")
    if not isinstance(body.get("viewport"), dict):
        raise errors.bad_request("viewport 가 없다.")

    render_ids: list[str] = []
    for layer in layers:
        if not isinstance(layer, dict):
            raise errors.bad_request("layers 의 항목이 층이 아니다.")
        render_ref = layer.get("renderId")
        if not isinstance(render_ref, str) or not Ulid.is_valid(render_ref):
            raise errors.bad_request("layers[].renderId 가 정규 ID 가 아니다.")
        render_ids.append(render_ref)

    role = d2_access.role_of(db, subject.account_id)
    permissions = d2_access.permissions_of(db, subject.account_id, role)
    if not permissions.get("업로드·편집"):
        raise errors.forbidden("`업로드·편집` 스위치가 꺼져 있다.")

    relay = request.app.state.previews
    if relay is None:
        raise errors.ApiError(503, RENDER_UNAVAILABLE,
                              "그리는 서버에 연결하지 못했다 — 장면을 뽑을 수 없다.")

    # **경계는 렌더 조회로 확인한다.** 렌더 작업은 viz-render 소유라 core-api 에 표가 없다 —
    # 그쪽에 경계 헤더를 실어 물어보는 것이 이 경계의 유일한 정직한 확인이다.
    for render_ref in render_ids:
        try:
            job = relay.get(lab_id=str(subject.lab_id), account_id=str(subject.account_id),
                            render_id=render_ref)
        except RelayUnavailable as e:
            raise errors.ApiError(503, RENDER_UNAVAILABLE,
                                  f"그리는 서버에 연결하지 못했다: {e}") from None
        if job is None:
            # **경계 밖은 존재를 알리지 않는다** — 403 이 아니라 404 다 (`fe-core.yaml` NotFound).
            raise errors.not_found("장면에 담긴 렌더가 없거나 연구실 경계 밖이다.")

    try:
        status, payload, content_type = relay.screenshot(
            lab_id=str(subject.lab_id), account_id=str(subject.account_id), request=body)
    except RelayUnavailable as e:
        # **빈 이미지를 만들지 않는다** — 0바이트 PNG 는 「장면이 비었다」로 읽힌다.
        raise errors.ApiError(503, RENDER_UNAVAILABLE,
                              f"그리는 서버에 연결하지 못했다: {e}") from None
    if status != 200:
        # 저쪽이 낸 상태·봉투를 **해석하지 않고** 그대로 올린다.
        return Response(content=payload, status_code=status,
                        media_type=content_type or "application/json")
    return Response(content=payload, status_code=200,
                    media_type=content_type or "image/png")


# ══════════════════════════════════════════════════════════════════════════════
# 값 조회 중계 (`V-2` · `PLAN-SoT §9 〈294〉` · 15차 동결 해제)
#
# **왜 `datasetId` 로 들어오나** — 완료 정의 `〈254〉` 권한 ⓑ 축자: 「자리 이름(내용 키)만으로
# 값을 내주는 길을 만들지 않는다. 키에 연구실이 없어(실측 `MAP_TILE_KEY_FIELDS`) 이름을
# 아는 것이 권한이 되면 경계가 무너진다. 값 조회는 **언제나 `datasetId` 로 들어와 경계
# 판정을 지난 뒤** 산출물에 닿는다」.
#
# **접근 판정을 새로 만들지 않는다** — `downloadDataset` 이 쓰는 `require_body_access` 를
# 그대로 부른다: ⑴ 경계 밖이면 404(존재를 알리지 않는다 · P-9·P-10) ⑵ `body_accessible`
# 이 거짓이면 403(P-34). **값은 메타가 아니라 본체다**(권한 ⓐ).
#
# **그리는 일도 읽는 일도 하지 않는다** (`CLAUDE.md §3-4`) — 조각을 원장에서 뽑아 넘길 뿐이다.
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/datasets/{datasetId}/value-lookup", name="lookupDatasetValue")
def lookup_dataset_value(request: Request, datasetId: str, body: dict = Body(...),
                         subject: Subject = Depends(current_subject),
                         db: Session = Depends(scoped_db)) -> dict:
    """한 점의 **그 칸 값**. 중계만 한다 — `core-viz.yaml#ValueLookupResult` 그대로 돌려준다."""
    if not Ulid.is_valid(datasetId):
        raise errors.bad_request("datasetId 가 정규 ID 가 아니다.")
    dataset_id = Ulid(datasetId)
    point = body.get("point")
    if not isinstance(point, dict):
        raise errors.bad_request("point.lat · point.lon 이 필요하다.")
    lat, lon = point.get("lat"), point.get("lon")
    # ⚠ **`bool` 을 먼저 뺀다** — `bool` 은 `int` 의 하위형이라 `isinstance(True, int)` 가
    # 참이고, 종전 검사는 `{"lat": true}` 를 그대로 통과시켰다 (`CODE-REVIEW-20260903` #8).
    if isinstance(lat, bool) or isinstance(lon, bool) \
            or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        raise errors.bad_request("point.lat · point.lon 이 필요하다.")
    # **범위를 여기서 본다.** 종전에는 타입만 봐서 `{"lat": 200}` 이 viz 의 pydantic(ge=-90)
    # 에서 422 가 되고 그 422 가 503 이 됐다 — **클라이언트 오류가 장애 계수에 섞였다.**
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise errors.bad_request("point.lat 은 -90~90, point.lon 은 -180~180 이다.")

    # ⑴ 404 · ⑵ 403 — 내려받기와 **같은 두 줄**이다.
    catalog.require_body_access(db, dataset_id)

    # **본체 조각은 원장이 안다** — 화면이 조각 식별자를 들고 다니지 않는다.
    pieces = [p for p in d3_catalog.files_for_download(db, dataset_id)
              if p["kind"] == "본체"]
    if not pieces:
        raise errors.not_found("값을 읽을 본체 조각이 없다.")

    relay = request.app.state.previews
    if relay is None:
        raise errors.ApiError(503, RENDER_UNAVAILABLE, "그리는 서버에 연결하지 못했다.")
    try:
        return relay.lookup_value(
            lab_id=str(subject.lab_id), account_id=str(subject.account_id),
            request={"datasetId": datasetId, "fileId": str(pieces[0]["id"]),
                     "point": {"lat": float(lat), "lon": float(lon)}})
    except RelayRefused as e:
        return _refused(e)
    except RelayUnavailable as e:
        # **값을 지어내지 않는다** — 0 도 null 도 「못 물어봤다」의 답이 아니다.
        raise errors.ApiError(503, RENDER_UNAVAILABLE,
                              f"그리는 서버에 연결하지 못했다: {e}") from None
