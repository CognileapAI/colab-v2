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
                     instant: str | None = None,
                     grid_digest: str | None = None) -> str:
    """산출물 하나를 가리키는 키. **같은 입력이면 같은 문자열**이다.

    `grid_digest` 는 **좌표를 쓰는 산출물에만** 들어간다. 호출자가 실수로 넘겨도
    `crs` 가 `없음`이면 **여기서 떨군다** — 「지도형만 무효화」를 호출 규율이 아니라
    **키 자신**이 지키게 한다. 규율에 맡기면 언젠가 한 곳이 어긴다.
    """
    return _digest(_payload(
        source_digest=source_digest, long_side=long_side, downsample=downsample,
        fills=fills, palette=palette, crs=crs, selection=selection,
        color_range=color_range, instant=instant, grid_digest=grid_digest))


#: 변이 키가 **빼는** 입력. 지금은 팔레트 하나다 — 넓히는 것은 별도 판정이다.
_VARIANT_EXCLUDED = ("palette",)


def render_variant_key(**kwargs) -> str:
    """**「같은 그림, 색만 다름」의 서명** — 팔레트를 뺀 나머지 입력 전부로 짓는다(`V-1` ⑴).

    `render_cache_key` 와 **같은 payload 를 쓴다** — 규칙이 두 곳이 되면 언젠가 한 곳이
    어긋나고, 어긋난 쪽이 「지워도 되는 옛 벌」을 잘못 고른다. 그래서 빼는 열쇠 하나만
    다르고 나머지는 한 함수가 짓는다.

    쓰임은 하나다 — 팔레트만 바꾼 재렌더가 **무엇을 대체했는가**를 가른다(`〈259〉` ⑷).
    원본·선택 변수·시각·색범위·격자 중 **하나라도 다르면 변이 키가 갈리고**, 그 벌은
    「색만 바뀐 같은 그림」이 아니므로 회수 대상이 아니다.
    """
    payload = _payload(**kwargs)
    for k in _VARIANT_EXCLUDED:
        payload.pop(k)
    return _digest(payload)


def _digest(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _payload(*, source_digest: str, long_side: int, downsample: str,
             fills: tuple[float, ...] | list[float], palette: str,
             crs: str, selection: str | None, color_range: ColorRange,
             instant: str | None = None, grid_digest: str | None = None) -> dict:
    """키의 재료 — **여기 한 곳에서만 짓는다.**"""
    if crs == NO_CRS:
        grid_digest = None
    return {
        "source": source_digest,
        "longSide": int(long_side),
        "downsample": downsample,
        "fills": [float(f) for f in fills],
        "palette": palette,
        "crs": crs,
        "selection": selection,
        # ⭑ ⟨2026-09-03 · 코드리뷰 #3⟩ **시각이 키에 없었다.** 24시각 파일의 T1·T2 요청이
        # 같은 키·같은 PNG 를 받았고, 그래서 시각을 바꿔도 그림이 안 바뀌는 것이 캐시로
        # 굳었다. 선택(`selection`)이 「어느 변수」라면 이것은 「어느 시각」이고, 둘은
        # 같은 자격으로 산출물을 가른다.
        "instant": instant,
        # 값 **과** 단계 토큰을 함께 싣는다 — 둘 중 하나만으로는 승격을 못 막는다.
        "range": [color_range.vmin, color_range.vmax, color_range.token()],
        "grid": grid_digest,
    }
