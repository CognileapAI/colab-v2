"""XYZ 타일 한 장 — 웹 메르카토르 `z/x/y` → PNG.

**빈 타일(값 없음)도 200 + 투명 PNG 다.** 404 로 두면 지도 위젯이 재시도를 반복한다
(계약 `getRenderTile` 산문).

`morecantile`·`titiler` 를 끌어오지 않는다. 필요한 것은 웹 메르카토르 역변환 공식
하나뿐이고, **v2 에 타일링 선례가 없어**(PoC 는 `titiler` 를 설치하고 import 0건 ·
프론트는 단일 PNG `ImageOverlay` 였다 — `DATA-REFERENCE §5`) 물려받을 구조도 없다.
"""
from __future__ import annotations

import io
import math

import numpy as np
from PIL import Image

from .raster import Rendered

TILE_SIZE = 256
MAX_ZOOM = 22

_EMPTY_PNG: bytes | None = None


def _tile_lat(y_merc: np.ndarray) -> np.ndarray:
    """웹 메르카토르 y(0~1) → 위도."""
    return np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * y_merc))))


def empty_tile() -> bytes:
    global _EMPTY_PNG
    if _EMPTY_PNG is None:
        buf = io.BytesIO()
        Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0)).save(buf, format="PNG")
        _EMPTY_PNG = buf.getvalue()
    return _EMPTY_PNG


def _colors_rgba(rendered: Rendered) -> np.ndarray:
    out = np.zeros((len(rendered.colors), 4), dtype="u1")
    for i, c in enumerate(rendered.colors):
        out[i] = (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), 255)
    return out


def render_tile(rendered: Rendered, z: int, x: int, y: int) -> bytes:
    """타일 한 장. 데이터 밖이면 투명 PNG 를 돌려준다 (200 이다)."""
    n_tiles = 2 ** z
    if not (0 <= x < n_tiles and 0 <= y < n_tiles):
        return empty_tile()

    # 타일 픽셀 중심의 경위도
    px = (x + (np.arange(TILE_SIZE) + 0.5) / TILE_SIZE) / n_tiles
    py = (y + (np.arange(TILE_SIZE) + 0.5) / TILE_SIZE) / n_tiles
    lons = px * 360.0 - 180.0
    lats = _tile_lat(py)

    west, south, east, north = rendered.bounds
    if lons.max() < west or lons.min() > east or lats.max() < south or lats.min() > north:
        return empty_tile()

    ny, nx = rendered.values.shape
    rows = np.clip(((north - lats) / max(north - south, 1e-12) * (ny - 1)
                    ).round().astype("i8"), 0, ny - 1)
    cols = np.clip(((lons - west) / max(east - west, 1e-12) * (nx - 1)
                    ).round().astype("i8"), 0, nx - 1)
    inside = ((lats[:, None] <= north) & (lats[:, None] >= south)
              & (lons[None, :] >= west) & (lons[None, :] <= east))

    sampled = rendered.values[np.ix_(rows, cols)]
    valid = inside & np.isfinite(sampled)
    if not valid.any():
        return empty_tile()

    lo = rendered.breaks[0][0]
    hi = rendered.breaks[-1][1]
    count = len(rendered.breaks)
    # NaN 자리를 캐스트에 넣지 않는다 — 캐스트 경고를 끄는 것이 아니라 값을 넣지 않는다.
    safe = np.where(valid, sampled, lo)
    idx = np.clip(((safe - lo) / max(hi - lo, 1e-12) * count).astype("i8"), 0, count - 1)

    rgba = np.zeros((TILE_SIZE, TILE_SIZE, 4), dtype="u1")
    table = _colors_rgba(rendered)
    rgba[valid] = table[idx[valid]]

    buf = io.BytesIO()
    Image.fromarray(rgba, mode="RGBA").save(buf, format="PNG")
    return buf.getvalue()
