"""`describeTarget` — 대상에서 **그릴 수 있는 변수와 시각**을 읽는다 (21차 해제 · 첨가 ⑴).

`core-viz.yaml#describeTarget` 그대로다. 이 파일이 지키는 것 셋.

  ① **읽기 전용이다.** 렌더 작업을 만들지도 조회하지도 않고, 미리보기·타일·캐시 키에
     한 글자도 닿지 않는다 (`lookupValue` 와 같은 자세 · 계약 산문 축자).
  ② **규칙을 다시 적지 않는다.** 그릴 수 있는 이름의 판정은 `readers.describe_field`
     하나이고 그것은 `read_field` 와 같은 상수·같은 줄을 쓴다 — 「고를 수 있다고 한
     이름」과 「실제로 그려지는 이름」이 갈릴 자리를 만들지 않는다.
  ③ **경계를 가장 먼저 읽는다** — `createRender` 와 같은 순서다. 대상을 해석한 뒤에
     읽으면 헤더 없는 요청이 「그 대상이 있느냐」를 404/200 으로 알려 주는 신탁이 된다.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...domains.d7_visualization.failures import (
    NOT_RENDERABLE_MESSAGE, TOO_LARGE_MESSAGE,
)
from ...domains.d7_visualization.readers import (
    SUPPORTED_FORMATS, FieldReadError, NotRenderableError, _pick_default, describe_field,
)
from ...kernel import errors
from ...ports.source import SizeMismatch, TargetNotFound, WorkspaceExceeded
from .. import deps
from ..deps import require_caller
from .renders import RenderTarget

router = APIRouter(tags=["render"], dependencies=[Depends(require_caller)])


@router.post("/target-descriptions")
def describe_target(body: RenderTarget, request: Request) -> dict:
    """`TargetDescription` 한 벌 — 변수 목록 ＋ 시각(건수·처음·마지막) ＋ 서버 기본값.

    **어느 조각을 보는가** — 읽을 수 있는 **첫 조각**이다. 조각마다 변수 이름이 다를 수
    있는데 합집합을 내면 「고를 수 있다」고 한 이름이 어떤 조각에도 없을 수 있고,
    교집합을 내면 그릴 수 있는 것을 못 그린다고 말하게 된다. 렌더도 조각을 이 순서로
    읽으므로(`jobs.py`) **같은 조각이 같은 답을 낸다** — 조각을 좁히려면 `fileIds` 다.
    """
    lab, account = deps.tenant_scope(request)
    settings = request.app.state.settings
    source = request.app.state.source
    try:
        target = source.resolve(dataset_id=body.datasetId, upload_id=body.uploadId,
                                file_ids=body.fileIds)
    except TargetNotFound as e:
        raise errors.not_found(str(e)) from e

    total = sum(p.size_bytes for p in target.parts)
    if total > settings.max_render_bytes:
        # `createRender` 와 **같은 판정·같은 코드**다 — 화면의 복구 경로가 같은 모양으로 선다.
        raise errors.ApiError(413, errors.RENDER_TOO_LARGE, TOO_LARGE_MESSAGE,
                              {"limitBytes": settings.max_render_bytes,
                               "targetBytes": total})
    try:
        target = source.materialize(target)
    except (SizeMismatch, WorkspaceExceeded) as e:
        raise errors.ApiError(413, errors.RENDER_TOO_LARGE, TOO_LARGE_MESSAGE,
                              {"limitBytes": settings.max_render_bytes, "reason": str(e)}) from e

    for part in target.parts:
        try:
            _fmt, variables, instants = describe_field(part.path)
        except (NotRenderableError, FieldReadError):
            continue
        if not variables:
            continue
        # **기본값은 지어내지 않는다** — 렌더가 생략을 만났을 때 부르는 바로 그 함수다.
        default_variable = _pick_default(variables)
        return {
            "variables": variables,
            # **빈 목록이 아니라 `null` 이다** — 「시각이 없는 데이터」와 「시각을 못 셌다」를
            # 같은 값으로 접지 않는다(계약 산문 축자).
            "instants": (None if not instants else
                         {"count": len(instants), "first": instants[0], "last": instants[-1]}),
            "default": {"variable": default_variable,
                        # 생략하면 **첫 시각**이다 — `_time_index(instant=None)` 과 같은 답.
                        "instant": instants[0] if instants else None},
        }

    # 어느 조각도 그릴 수 없다 — `createRender` 와 같은 415·같은 본문이다.
    raise errors.ApiError(415, errors.NOT_RENDERABLE, NOT_RENDERABLE_MESSAGE,
                          {"renderableFormats": list(SUPPORTED_FORMATS)})
