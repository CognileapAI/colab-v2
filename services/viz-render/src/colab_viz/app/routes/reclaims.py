"""`reclaimPreviews` — 사용자가 지운 데이터셋의 미리보기 산출물 회수 (22차 해제 ㉯).

`core-viz.yaml#reclaimPreviews` 그대로다. 이 파일이 지키는 것 넷.

  ① **대상을 해석하지 않는다.** 부르는 시점에 데이터셋은 묘비이고 `d3_file` 행도 없다 —
     `targetId` 로 무엇을 되묻는 순간 그 조회는 항상 빈손이고, 그 빈손이 「지울 것이 없다」로
     위장한다. 판정 입력은 요청이 실어 온 `fileIds` 뿐이다.
  ② **규칙을 다시 적지 않는다.** 판정은 `invalidation.deletion_keep_reason`, 한 바퀴는
     `reclaim_on_delete.run` 하나다. 라우트는 자리(싱크·클라이언트·미리보기 루트)를
     건네주기만 한다 — 여기서 판정을 한 줄이라도 재선언하면 규칙이 둘이 된다.
  ③ **경계를 가장 먼저 읽는다** — `describeTarget`·`createRender` 와 같은 순서다.
  ④ **자리를 지어내지 않는다.** 싱크·S3 클라이언트는 **렌더 라우트가 쓰는 그 자리**
     (`app.state.preview_sink` · `app.state.s3_client`)이고, 저장 모드가 `local` 이면
     클라이언트는 `None` 이다(표식도 원격 삭제도 없다 — 로컬은 디렉터리가 곧 색인이다).
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field

from ...domains.d7_visualization import reclaim_on_delete
from .. import deps
from ..deps import require_caller

router = APIRouter(tags=["render"], dependencies=[Depends(require_caller)])

_Ulid = Annotated[str, Field(pattern=r"^[0-9A-HJKMNP-TV-Z]{26}$")]


class PreviewReclaimRequest(BaseModel):
    """계약 `PreviewReclaimRequest` — 모르는 칸은 받지 않는다(`extra="forbid"`).

    ⚠ **`fileIds` 의 `min_length=1` 이 안전장치다** — 빈 집합에 대해 「모든 원천이
    포함된다」가 참이 되어 전건이 회수 대상이 된다. 계약의 `minItems: 1` 과 같은 값이다.
    """

    model_config = ConfigDict(extra="forbid")
    targetId: _Ulid
    fileIds: list[_Ulid] = Field(min_length=1)


@router.post("/reclaims")
def reclaim_previews(body: PreviewReclaimRequest, request: Request) -> dict:
    """`PreviewReclaimResult` 한 벌 — `stale`·`kept`·`unindexed` ＋ 지운 이름.

    **멱등이다** — 두 번째 호출은 표식도 파일도 없어 `stale 0` 이다. core 가 삭제를
    재시도해도 같은 답이 나오고, 그래서 실패한 삭제를 사람이 다시 눌러도 된다.
    """
    deps.tenant_scope(request)
    settings = request.app.state.settings
    # 저장 모드가 `s3` 일 때만 표식을 되묻는다 — 로컬은 `ownership.scan` 이 같은 일을 한다.
    client = (getattr(request.app.state, "s3_client", None)
              if settings.preview_sink == "s3" else None)
    result = reclaim_on_delete.run(
        client=client,
        sink=request.app.state.preview_sink,
        previews_root=settings.preview_dir,
        target_id=body.targetId,
        file_ids=body.fileIds,
        previews_prefix=settings.preview_s3_prefix)
    return {"targetId": body.targetId, "stale": result.stale, "kept": result.kept,
            "unindexed": result.unindexed, "orphanIndex": result.orphan_index,
            "removed": list(result.removed)}
