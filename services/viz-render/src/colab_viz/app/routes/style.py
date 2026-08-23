"""`listPalettes` — `RenderStyle.palette` 값의 출처.

`D2c` C1 열린 항목 ① 이 여기서 닫힌다: 「`palette` 가 required 인데 그 값의 출처가
FE 표면에 없다」. **core·FE 는 하드코딩하지 않는다** — 이 목록을 받아 쓴다.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ...domains.d7_visualization import palettes
from ..deps import require_caller

router = APIRouter(tags=["style"], dependencies=[Depends(require_caller)])


@router.get("/palettes")
def list_palettes() -> dict:
    items = palettes.options()
    # ListEnvelope — `nextCursor` 가 null 이면 더 없음. 팔레트는 3종 고정이라 늘 null 이다.
    return {"items": items, "totalCount": len(items), "nextCursor": None}
