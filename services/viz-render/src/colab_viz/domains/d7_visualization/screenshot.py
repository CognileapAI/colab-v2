"""장면 합성 — 여러 층을 한 장의 PNG 로 (`core-viz.yaml` `createScreenshot`).

**시각화 설정은 저장하지 않는다.** 남길 장면은 여기서 뽑고, 그래서 층 목록·순서·
불투명도·화면 크기가 요청에 실린다 (`Policy_데이터셋_상세 §8 스크린샷`).

**타일과 같은 표본화를 쓴다** — 타일이 `z/x/y` 로 자르는 것을 여기서는 뷰포트 경계로
자를 뿐이고, 색을 정하는 규칙(구간·팔레트·NaN 자리)은 `tiles.py` 와 한 벌이다.
두 벌로 두면 화면과 스크린샷이 다른 색을 낸다.

**값이 없는 자리는 투명이다** — 데이터 밖이면 빈 장면을 돌려주고 실패로 만들지 않는다.
없는 좌표를 지어내지 않는다 (`DATA-REFERENCE §0` · `DR-9`).
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image

from .raster import Rendered
from .tiles import _colors_rgba

#: 뷰포트 한 변의 상한 — 계약 `Viewport.width`·`height` 의 `maximum` 과 같은 값이다.
MAX_SIDE = 4096

#: 한 장면에 담을 수 있는 층의 개수. ⭑ ⟨2026-09-03 · 코드리뷰 #11⟩ **상한이 없었다.**
#:
#: **왜 상한이 필요한가 — 층 하나가 뷰포트 한 판을 통째로 훑는다.** 최대 뷰포트
#: (4096×4096)에서 층 하나가 지나는 전이 할당은 `_sample_rgba` 의 RGBA(u1, 67 MB) ·
#: 표본값(f4, 67 MB) · 색인(i8, 134 MB) 과 `_over` 의 f4 중간판들(≈340 MB)이라 **층당
#: 수백 MB** 다. 요청 하나가 층 수를 자유롭게 실으면 그 배수가 그대로 한 프로세스에
#: 들어오고, 스레드풀(기본 40)이 그것을 동시에 여러 개 통과시킨다.
#:
#: **왜 8 인가 — `[정본 무근거]`.** 정본 `Policy_데이터셋_상세 §8` 은 「이 데이터」 층
#: 하나에 **얹은 층**을 겹쳐 비교한다고만 적고 개수를 말하지 않는다. 8 은 그 화면이
#: 실제로 비교하는 층 수(밑판 1 + 얹은 층 7)를 넉넉히 덮으면서, 위 계산으로 한 요청의
#: 작업량을 예측 가능한 범위에 묶는 값이다. **계약에는 `maxItems` 가 없다** —
#: 계약 델타 초안으로만 남기고(`CODE-REVIEW-20260903-C.md`) 이 레인은 계약을 안 고친다.
MAX_LAYERS = 8


def _sample_rgba(rendered: Rendered, width: int, height: int,
                 bounds: tuple[float, float, float, float]) -> np.ndarray:
    """뷰포트 격자 위에 층 하나를 최근접 표본화한다. 밖은 알파 0 이다."""
    vw, vs, ve, vn = bounds
    lons = vw + (np.arange(width) + 0.5) / width * (ve - vw)
    lats = vn - (np.arange(height) + 0.5) / height * (vn - vs)

    rgba = np.zeros((height, width, 4), dtype="u1")
    west, south, east, north = rendered.bounds
    if lons.max() < west or lons.min() > east or lats.max() < south or lats.min() > north:
        return rgba

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
        return rgba

    lo = rendered.breaks[0][0]
    hi = rendered.breaks[-1][1]
    count = len(rendered.breaks)
    # NaN 자리를 캐스트에 넣지 않는다 — 값을 넣지 않는 것이지 경고를 끄는 것이 아니다.
    safe = np.where(valid, sampled, lo)
    idx = np.clip(((safe - lo) / max(hi - lo, 1e-12) * count).astype("i8"), 0, count - 1)
    rgba[valid] = _colors_rgba(rendered)[idx[valid]]
    return rgba


def _over(base: np.ndarray, top: np.ndarray) -> np.ndarray:
    """알파 합성 — 위층이 아래층을 덮는다(straight alpha, `over` 연산)."""
    ta = top[..., 3:4].astype("f4") / 255.0
    ba = base[..., 3:4].astype("f4") / 255.0
    out_a = ta + ba * (1.0 - ta)
    out_rgb = (top[..., :3].astype("f4") * ta
               + base[..., :3].astype("f4") * ba * (1.0 - ta))
    with np.errstate(invalid="ignore", divide="ignore"):
        out_rgb = np.where(out_a > 0, out_rgb / np.where(out_a > 0, out_a, 1.0), 0.0)
    out = np.zeros_like(base)
    out[..., :3] = np.clip(out_rgb.round(), 0, 255).astype("u1")
    out[..., 3] = np.clip((out_a[..., 0] * 255.0).round(), 0, 255).astype("u1")
    return out


def compose(layers: list[tuple[Rendered, float]], width: int, height: int,
            bounds: tuple[float, float, float, float]) -> bytes:
    """장면 한 장. **첫 항목이 맨 아래 층**이다 (계약 `ScreenshotRequest` 산문)."""
    scene = np.zeros((height, width, 4), dtype="u1")
    for rendered, opacity in layers:
        layer = _sample_rgba(rendered, width, height, bounds)
        if opacity < 1.0:
            layer = layer.copy()
            layer[..., 3] = (layer[..., 3].astype("f4") * opacity).round().astype("u1")
        scene = _over(scene, layer)

    buf = io.BytesIO()
    Image.fromarray(scene, mode="RGBA").save(buf, format="PNG")
    return buf.getvalue()
