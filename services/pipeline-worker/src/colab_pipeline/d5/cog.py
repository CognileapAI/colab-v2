"""COG 변환 — 오버뷰 리샘플링은 범주형/연속형으로 갈린다 (DR-12).

- PoC 는 rio-cogeo 기본값(nearest 단일)에 위임했다 — 연속형 축소 뷰가 튄다.
- 곡선(불규칙) 격자는 **실측 좌표 배열**을 써서 규칙 격자로 최근접 재배치한다.
  좌표가 없으면 이 모듈에 오기 전에 이미 실패다 (DR-9) — 여기서 합성하지 않는다.
- 메모리 — 행 청크로 처리한다 (DR-11). cog_translate 자체가 윈도우 IO 다.

**stage2 대기.** 배포 단위·완료 정의에서 빠진다 — 파일·시험 유지(`〈71〉-㉰`).
근거: `dev-package/sessions/S1-PLAN.md` §5.2 행 7 · `PLAN-SoT.md §9 〈74〉〈75〉`.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

#: DR-12 — 정본 분기. 범주형(토지피복·LULC)=nearest · 연속형(NDVI·강수·반사도)=average
OVERVIEW_RESAMPLING: dict[str, str] = {
    "categorical": "nearest",
    "continuous": "average",
}

_CHUNK_ROWS = 512


class CogConversionError(Exception):
    pass


def _cog_translate(src_path: Path, dst_path: Path, kind: str) -> Path:
    from rio_cogeo.cogeo import cog_translate
    from rio_cogeo.profiles import cog_profiles

    if kind not in OVERVIEW_RESAMPLING:
        raise CogConversionError(f"kind 는 categorical|continuous — 받은 값: {kind}")
    profile = cog_profiles.get("deflate")
    # 작은 이미지(한 타일에 다 드는)는 rio-cogeo 가 오버뷰 0단을 만든다.
    # 우리 산출물은 COG 판정 정본(타일 + IFD 2개 이상)을 항상 만족해야 하므로
    # 최소 1단을 강제한다 — 판정 규칙을 느슨하게 푸는 쪽은 택하지 않는다 (DR-2).
    import rasterio
    with rasterio.open(src_path) as s:
        overview_level = None if max(s.height, s.width) > 256 else 1
    cog_translate(
        str(src_path), str(dst_path), profile,
        overview_level=overview_level,
        overview_resampling=OVERVIEW_RESAMPLING[kind],
        in_memory=False,   # DR-11 — 임시본도 디스크로
        quiet=True,
    )
    return dst_path


def convert_tif_to_cog(src_tif: Path, dst_path: Path, *, kind: str) -> Path:
    """이미 GeoTIFF 인 입력(타일만/스트립)을 COG 로 변환한다."""
    return _cog_translate(Path(src_tif), Path(dst_path), kind)


def regrid_curvilinear_nearest(
    data: np.ndarray, lat: np.ndarray, lon: np.ndarray,
) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    """실측 곡선 격자 → 규칙 위경도 격자 최근접 재배치.

    좌표는 입력으로 받은 **실제 배열**만 쓴다 — 어떤 값도 합성하지 않는다.
    반환 = (재배치 배열, (west, south, east, north)).
    """
    ny, nx = data.shape
    lat_min, lat_max = float(np.nanmin(lat)), float(np.nanmax(lat))
    lon_min, lon_max = float(np.nanmin(lon)), float(np.nanmax(lon))
    if not (np.isfinite(lat_min) and np.isfinite(lon_min)) or lat_min == lat_max:
        raise CogConversionError("격자 좌표 범위가 퇴화했다 — 재배치 불가")

    out = np.full((ny, nx), np.nan, dtype="f4")
    lat_step = (lat_max - lat_min) / max(ny - 1, 1)
    lon_step = (lon_max - lon_min) / max(nx - 1, 1)
    for r0 in range(0, ny, _CHUNK_ROWS):
        la = np.asarray(lat[r0:r0 + _CHUNK_ROWS], dtype="f8")
        lo = np.asarray(lon[r0:r0 + _CHUNK_ROWS], dtype="f8")
        d = np.asarray(data[r0:r0 + _CHUNK_ROWS], dtype="f4")
        rows = np.clip(np.rint((lat_max - la) / lat_step), 0, ny - 1).astype("i8")
        cols = np.clip(np.rint((lo - lon_min) / lon_step), 0, nx - 1).astype("i8")
        valid = np.isfinite(d)
        out[rows[valid], cols[valid]] = d[valid]
    return out, (lon_min, lat_min, lon_max, lat_max)


def write_cog_from_grid(
    data: np.ndarray, lat: np.ndarray, lon: np.ndarray, dst_path: Path, *, kind: str,
) -> Path:
    """배열 + 실측 좌표 → GTiff 임시본 → COG."""
    import rasterio
    from rasterio.transform import from_bounds

    regridded, (w, s, e, n) = regrid_curvilinear_nearest(data, lat, lon)
    ny, nx = regridded.shape
    transform = from_bounds(w, s, e, n, nx, ny)
    dst_path = Path(dst_path)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".temp.tif", dir=dst_path.parent,
                                     delete=False) as tf:
        temp_path = Path(tf.name)
    try:
        with rasterio.open(
            temp_path, "w", driver="GTiff", height=ny, width=nx, count=1,
            dtype="float32", crs="EPSG:4326", transform=transform, nodata=np.nan,
            tiled=True, blockxsize=256, blockysize=256,
        ) as dst:
            for r0 in range(0, ny, _CHUNK_ROWS):
                r1 = min(r0 + _CHUNK_ROWS, ny)
                dst.write(regridded[r0:r1], 1,
                          window=rasterio.windows.Window(0, r0, nx, r1 - r0))
        return _cog_translate(temp_path, dst_path, kind)
    finally:
        temp_path.unlink(missing_ok=True)
