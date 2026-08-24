"""캐시 키 — **원본 해시 + 렌더 파라미터** (`PREVIEW-IMPLEMENTATION §7.2`).

무효화 규칙을 따로 코딩하지 않는다. **키가 하게 한다:**

| 사건 | 무효화 |
|---|---|
| 격자 교체·후주입 | **지도형만** — 격자 해시가 지도형 키에만 들어가므로 자동이다 |
| 공통 스케일 갱신 | 전 프레임·전 산출물 — 범위와 **단계 토큰**이 키에 들어간다 |
| 원본 교체 | 그 파일의 전 산출물 |

⚠ **범위는 값만 넣으면 안 된다.** 잠정과 확정이 우연히 같은 수를 내면 키가 같아져
**잠정 산출물이 확정으로 조용히 승격된다.** 그래서 `ColorRange.token()`(단계 + 대상)을
넣는다 — 이것이 `§D.4-⑶ⓒ` 가 요구한 자리다.
"""
from __future__ import annotations

import hashlib
import json

from .scale import ColorRange

#: 좌표계 「없음」 — 썸네일(①)·비지도형(②)이 쓰는 값이다.
NO_CRS = "none"
#: 지도형(③)의 좌표계. `PREVIEW-IMPLEMENTATION §3.3` — **고정이다.**
MAP_CRS = "EPSG:3857"


def render_cache_key(*, source_digest: str, long_side: int, downsample: str,
                     fills: tuple[float, ...] | list[float], palette: str,
                     crs: str, selection: str | None,
                     color_range: ColorRange,
                     grid_digest: str | None = None) -> str:
    """산출물 하나를 가리키는 키. **같은 입력이면 같은 문자열**이다.

    `grid_digest` 는 **좌표를 쓰는 산출물에만** 들어간다. 호출자가 실수로 넘겨도
    `crs` 가 `없음`이면 **여기서 떨군다** — 「지도형만 무효화」를 호출 규율이 아니라
    **키 자신**이 지키게 한다. 규율에 맡기면 언젠가 한 곳이 어긴다.
    """
    if crs == NO_CRS:
        grid_digest = None
    payload = {
        "source": source_digest,
        "longSide": int(long_side),
        "downsample": downsample,
        "fills": [float(f) for f in fills],
        "palette": palette,
        "crs": crs,
        "selection": selection,
        # 값 **과** 단계 토큰을 함께 싣는다 — 둘 중 하나만으로는 승격을 못 막는다.
        "range": [color_range.vmin, color_range.vmax, color_range.token()],
        "grid": grid_digest,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
