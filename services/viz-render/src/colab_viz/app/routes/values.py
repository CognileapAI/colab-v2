"""`lookupValue` — 계약 `core-viz.yaml` 그대로 (`V-2` · `PLAN-SoT §9 〈294〉` · 15차 해제).

**권한을 판정하지 않는다** — 완료 정의 권한 ⓑ 가 그 자리를 core-api 에 두었고
(`createScreenshot` 과 같은 선), 이 표면은 서비스 토큰 뒤에 선다.

**요청에 내용 키가 없다** — 자리 이름만으로 값을 내주는 길을 만들지 않는다. 자리는
`datasetId`＋`fileId` 로 연 파일에서 **다시 계산해** 얻는다(`value_lookup` 머리말).
"""
from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from ...domains.d7_visualization import value_lookup
from ...kernel import errors
from ...ports.source import TargetNotFound
from .. import deps
from ..deps import require_caller

router = APIRouter(tags=["render"], dependencies=[Depends(require_caller)])

_Ulid = Annotated[str, Field(pattern=r"^[0-9A-HJKMNP-TV-Z]{26}$")]


class LookupPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class ValueLookupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    #: **등록된 데이터셋만이다** — `uploadId` 자리를 두지 않는다(완료 정의 ⑺).
    datasetId: _Ulid
    fileId: _Ulid
    point: LookupPoint


#: **서버 단독 시간을 응답이 스스로 말한다** (`VL-1` ⑴ · `PLAN-SoT §9 〈310〉`).
#:
#: `〈304〉` 축자 — 「응답 헤더에 `Server-Timing: cfCacheStatus` 뿐이라 서버 처리 구간을
#: 가르는 재료가 없다 ⟹ **서버 측 p95 = `[미확인]`**」. 그 재료를 여기서 낸다.
#: ⚠ **계약 몸통은 한 글자도 늘지 않는다** — `Server-Timing` 은 표준 응답 헤더이고
#: `core-viz.yaml#ValueLookupResult` 밖의 관측 자리다(`/healthz` `tileBranch` 와 같은 선).
def _server_timing(spans: dict[str, float]) -> str:
    return ", ".join(f"{name};dur={ms:.3f}" for name, ms in spans.items())


@router.post("/value-lookups")
def lookup_value(body: ValueLookupRequest, request: Request, response: Response) -> dict:
    # **경계 헤더가 없으면 열지 않는다**(코드리뷰 #1). ⚠ 여기서 **대조는 하지 않는다** —
    # 이 op 은 `renderId` 가 아니라 `datasetId` 로 들어오고, 「그 데이터셋이 어느 연구실
    # 것인가」를 아는 표가 이 단위에 없다(저장 배치가 평평하다 — `layout.json`). 대조는
    # core-api 가 `require_body_access` 로 이미 하고(권한 ⓑ), 그 판정을 여기서 다시
    # 지어내면 **틀린 근거로 남의 것을 열어 주는 길**이 하나 더 생긴다.
    t_started = time.perf_counter()
    deps.tenant_scope(request)
    source = request.app.state.source
    try:
        resolved = source.resolve(dataset_id=body.datasetId, upload_id=None,
                                  file_ids=[body.fileId])
    except TargetNotFound as e:
        raise errors.not_found(str(e)) from None
    part = resolved.parts[0]
    t_resolved = time.perf_counter()
    outcome, spans = value_lookup.lookup_timed(
        request.app.state.settings.preview_dir, part.path,
        grid_dir=resolved.grid_dir, lat=body.point.lat, lon=body.point.lon)
    response.headers["Server-Timing"] = _server_timing({
        "vizResolve": (t_resolved - t_started) * 1000.0,
        "vizFindTile": spans["findTile"],
        "vizReadPoint": spans["readPoint"],
        "vizTotal": (time.perf_counter() - t_started) * 1000.0,
    })
    # **없는 것도 200 이다** — 사유가 실린다(완료 정의 ⑸ · 자리 없음은 500 이 아니다).
    return outcome.to_result()
