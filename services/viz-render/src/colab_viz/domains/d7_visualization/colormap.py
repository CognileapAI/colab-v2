"""연속 컬러맵 — **11앵커에서 보간한 256엔트리 LUT** (`PREVIEW-IMPLEMENTATION §6.3`).

`matplotlib` 을 끌어오지 않는다(`palettes.py` 와 같은 이유 — 런타임 의존을 하나 줄인다).
필요한 것은 앵커 열한 개와 선형 보간뿐이다.

**결측은 알파 0 이다.** 컬러맵의 색 하나를 결측에 배정하지 마라 — 그 색이 유효값과
구분되지 않는다(`§6.1`).

⚠ **구간 색(`palettes.ramp`)과 다른 물건이다.** `ramp` 는 **범례**가 쓰는 3~9 구간이고
(`RenderStyle.classCount` — `§6.3` 「범례에만 적용된다」), 이 LUT 는 **미리보기 PNG 자체**가
쓰는 연속 색이다. 둘을 한 함수로 합치면 「구간 수를 바꿨더니 그림의 색 해상도가 바뀌는」
동작이 생긴다.
"""
from __future__ import annotations

import numpy as np

LUT_SIZE = 256

#: viridis 11앵커 (`§2` 「viridis, 11앵커에서 뽑은 256엔트리 LUT」).
#: `t = 0.0, 0.1, … 1.0` 지점의 값이다.
VIRIDIS_ANCHORS: tuple[str, ...] = (
    "#440154", "#482475", "#414487", "#355f8d", "#2a788e", "#21918c",
    "#22a884", "#44bf70", "#7ad151", "#bddf26", "#fde725",
)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    return (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16))


def lut256(anchors: tuple[str, ...] | list[str]) -> np.ndarray:
    """앵커를 등간격으로 놓고 선형 보간한 `(256, 3) uint8` 표."""
    if len(anchors) < 2:
        raise ValueError("앵커가 둘 미만이면 보간할 것이 없다")
    src = np.array([_hex_to_rgb(a) for a in anchors], dtype="f8")
    xs = np.linspace(0.0, 1.0, len(anchors))
    ts = np.linspace(0.0, 1.0, LUT_SIZE)
    out = np.empty((LUT_SIZE, 3), dtype="u1")
    for c in range(3):
        out[:, c] = np.rint(np.interp(ts, xs, src[:, c])).astype("u1")
    return out


def to_rgba(values: np.ndarray, *, vmin: float, vmax: float,
            lut: np.ndarray) -> np.ndarray:
    """값 격자 → `(h, w, 4) uint8` RGBA. **NaN 은 알파 0 이고 색도 남기지 않는다.**

    범위 밖 값은 **자른다**(clip) — 잘린 값은 여전히 값이라 알파는 255 다. 범위 밖을
    결측처럼 지우면 공통 스케일이 바깥 값을 「없는 것」으로 만든다(`§6.2` 는 범위를
    **고정**하라 했지 바깥을 지우라 하지 않았다).
    """
    v = np.asarray(values, dtype="f4")
    valid = np.isfinite(v)
    span = float(vmax) - float(vmin)
    if span <= 0:
        span = 1.0                     # 값이 하나뿐인 층 — 폭 0 으로 나누지 않는다
    scaled = np.clip((np.where(valid, v, vmin) - float(vmin)) / span, 0.0, 1.0)
    idx = np.rint(scaled * (LUT_SIZE - 1)).astype("i4")

    rgba = np.zeros(v.shape + (4,), dtype="u1")
    rgba[..., :3][valid] = lut[idx[valid]]
    rgba[..., 3][valid] = 255
    return rgba
