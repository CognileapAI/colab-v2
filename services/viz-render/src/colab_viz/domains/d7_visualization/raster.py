"""값 + 실측 좌표 → **규칙 WGS84 격자** + 범례.

경계는 `Bounds`(WGS84 경위도 고정)로만 나간다 — 요청·응답 어디에도 좌표계 인자가 없고,
원본 좌표계 해석은 이 단위 안에서 끝난다 (계약 `Bounds` 산문 · `CLAUDE.md §3-4`).

**곡선(불규칙) 격자는 실측 좌표 배열로 최근접 재배치한다.** 좌표가 없으면 여기 오기
전에 이미 실패다 — 이 모듈에서 격자를 합성하지 않는다 (`DR-9`).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import palettes
from .failures import RenderError, RenderFailure
from .readers import Field

_CHUNK_ROWS = 512


@dataclass
class Rendered:
    """그려진 층 하나. 타일은 이 배열에서 잘라 낸다."""
    values: np.ndarray                        # 2D f4 · row 0 = 북쪽 · NaN = 값 없음
    bounds: tuple[float, float, float, float]  # (west, south, east, north)
    breaks: list[tuple[float, float]]
    colors: list[str]
    palette: str
    variable: str
    unit: str | None

    def legend(self) -> dict:
        legend: dict = {
            "palette": self.palette,
            "classes": [{"color": c, "min": lo, "max": hi}
                        for c, (lo, hi) in zip(self.colors, self.breaks)],
        }
        if self.variable:
            legend["variable"] = self.variable
        if self.unit:                 # 파일에 없으면 생략한다 — 지어내지 않는다
            legend["unit"] = self.unit
        return legend

    def bounds_dict(self) -> dict:
        w, s, e, n = self.bounds
        return {"west": w, "south": s, "east": e, "north": n}


def regrid_nearest(values: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                   ) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    """실측 곡선 격자 → 규칙 위경도 격자 최근접 재배치. **좌표는 받은 배열만 쓴다.**"""
    if values.shape != lat.shape or lat.shape != lon.shape:
        raise RenderError(RenderFailure.UNKNOWN,
                          f"값과 좌표의 형상이 다르다: {values.shape} / {lat.shape}")
    ny, nx = values.shape
    lat_min, lat_max = float(np.nanmin(lat)), float(np.nanmax(lat))
    lon_min, lon_max = float(np.nanmin(lon)), float(np.nanmax(lon))
    if not np.isfinite([lat_min, lat_max, lon_min, lon_max]).all() \
            or lat_min == lat_max or lon_min == lon_max:
        raise RenderError(RenderFailure.UNKNOWN, "격자 좌표 범위가 퇴화했다 — 재배치 불가")

    out = np.full((ny, nx), np.nan, dtype="f4")
    lat_step = (lat_max - lat_min) / max(ny - 1, 1)
    lon_step = (lon_max - lon_min) / max(nx - 1, 1)
    for r0 in range(0, ny, _CHUNK_ROWS):
        la = np.asarray(lat[r0:r0 + _CHUNK_ROWS], dtype="f8")
        lo = np.asarray(lon[r0:r0 + _CHUNK_ROWS], dtype="f8")
        d = np.asarray(values[r0:r0 + _CHUNK_ROWS], dtype="f4")
        rows = np.clip(np.rint((lat_max - la) / lat_step), 0, ny - 1).astype("i8")
        cols = np.clip(np.rint((lo - lon_min) / lon_step), 0, nx - 1).astype("i8")
        ok = np.isfinite(d) & np.isfinite(la) & np.isfinite(lo)
        out[rows[ok], cols[ok]] = d[ok]
    return out, (lon_min, lat_min, lon_max, lat_max)


def _classify(values: np.ndarray, count: int,
              value_range: tuple[float, float] | None = None) -> list[tuple[float, float]]:
    """구간 경계. **범위가 주어지면 그것을 쓴다 — 프레임에서 다시 잡지 않는다**(`V-2`).

    ⚠ 프레임별로 잡으면 값이 아니라 **분포**를 그리게 된다. 실측 — nc LST 5프레임에서
    개별 스트레치와 공통 범위가 최대 42 DN 어긋나고 p98 이 50분에 4.4 K 이동한다
    (`PREVIEW-IMPLEMENTATION §6.2`). **HSR 에서 차이가 작다고 규칙을 완화하지 마라.**
    """
    if value_range is not None:
        vmin, vmax = (float(v) for v in value_range)
        if vmax <= vmin:
            vmax = vmin + 1.0
        edges = [vmin + (vmax - vmin) * i / count for i in range(count + 1)]
        return [(edges[i], edges[i + 1]) for i in range(count)]
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        raise RenderError(RenderFailure.UNKNOWN, "그릴 값이 하나도 없다 — 전부 결측이다")
    vmin, vmax = float(finite.min()), float(finite.max())
    if vmin == vmax:
        # 값이 하나뿐이어도 구간 수는 정본이 준 값을 지킨다. 폭 0 구간을 만들지 않도록
        # 한 단위만 벌린다 — **값을 바꾸는 것이 아니라 구간 경계를 정하는 것**이다.
        vmax = vmin + 1.0
    edges = [vmin + (vmax - vmin) * i / count for i in range(count + 1)]
    return [(edges[i], edges[i + 1]) for i in range(count)]


def legend_from_range(*, palette_key: str, class_count: int,
                      value_range: tuple[float, float],
                      variable: str, unit: str | None) -> dict:
    """**좌표 없이 세우는 범례** — ②비지도형(`〈85〉`)이 쓰는 자리다.

    `Rendered` 는 경계를 요구하는 자료형이라 좌표가 없으면 만들 수 없다. 그런데 ②도
    같은 공통 색 범위로 칠해진 그림이므로 **범례는 있다.** 구간은 여기서 새로 잡지
    않고 넘겨받은 범위를 그대로 나눈다 — 프레임에서 다시 잡으면 `§10-7` 이 금지한
    그것이 된다(`_classify` 와 같은 계산이다).
    """
    palette = palettes.get(palette_key)
    breaks = _classify(np.empty(0, dtype="f4"), class_count, value_range)
    legend: dict = {
        "palette": palette.key,
        "classes": [{"color": c, "min": lo, "max": hi}
                    for c, (lo, hi) in zip(palettes.ramp(palette, class_count), breaks)],
    }
    if variable:
        legend["variable"] = variable
    if unit:
        legend["unit"] = unit
    return legend


def build(field: Field, *, palette_key: str, class_count: int,
          reference: tuple[np.ndarray, np.ndarray] | None,
          value_range: tuple[float, float] | None = None) -> Rendered:
    """값 하나를 규칙 격자로 놓고 구간·색을 정한다."""
    if field.bounds is not None:
        values, bounds = field.values, field.bounds
    elif field.lat is not None and field.lon is not None:
        values, bounds = regrid_nearest(field.values, field.lat, field.lon)
    elif reference is not None:
        lat, lon = reference
        values, bounds = regrid_nearest(field.values, lat, lon)
    else:
        # 여기 오면 안 된다 — 호출자가 이미 `기준 격자 없음`으로 실패시켰어야 한다.
        raise RenderError(RenderFailure.NO_REFERENCE_GRID, "좌표가 없다")

    palette = palettes.get(palette_key)
    breaks = _classify(values, class_count, value_range)
    return Rendered(values=values, bounds=bounds, breaks=breaks,
                    colors=palettes.ramp(palette, class_count),
                    palette=palette.key, variable=field.variable, unit=field.unit)


def merge(rendereds: list[Rendered],
          value_range: tuple[float, float] | None = None) -> Rendered:
    """조각 여러 개를 한 층으로 합친다 — 읽힌 조각만 들어온다.

    합칠 때 **좌표를 다시 만들지 않는다.** 공통 경계를 잡고 각 조각을 자기 경계에 맞춰
    다시 표본화한다. 겹치는 자리는 나중 조각이 이긴다(조각은 시각별로 잘려 오므로
    같은 자리에 두 값이 오는 것은 드물고, 왔다면 마지막 것이 최신이다).
    """
    if len(rendereds) == 1:
        return rendereds[0]
    w = min(r.bounds[0] for r in rendereds)
    s = min(r.bounds[1] for r in rendereds)
    e = max(r.bounds[2] for r in rendereds)
    n = max(r.bounds[3] for r in rendereds)
    ny = max(r.values.shape[0] for r in rendereds)
    nx = max(r.values.shape[1] for r in rendereds)
    out = np.full((ny, nx), np.nan, dtype="f4")

    rows = np.linspace(n, s, ny)
    cols = np.linspace(w, e, nx)
    grid_lon, grid_lat = np.meshgrid(cols, rows)
    for r in rendereds:
        rw, rs, re_, rn = r.bounds
        sy = np.clip(((rn - grid_lat) / max(rn - rs, 1e-12) * (r.values.shape[0] - 1)
                      ).round().astype("i8"), 0, r.values.shape[0] - 1)
        sx = np.clip(((grid_lon - rw) / max(re_ - rw, 1e-12) * (r.values.shape[1] - 1)
                      ).round().astype("i8"), 0, r.values.shape[1] - 1)
        inside = (grid_lat <= rn) & (grid_lat >= rs) & (grid_lon >= rw) & (grid_lon <= re_)
        sampled = r.values[sy, sx]
        take = inside & np.isfinite(sampled)
        out[take] = sampled[take]

    first = rendereds[0]
    breaks = _classify(out, len(first.breaks), value_range)
    return Rendered(values=out, bounds=(w, s, e, n), breaks=breaks, colors=first.colors,
                    palette=first.palette, variable=first.variable, unit=first.unit)
