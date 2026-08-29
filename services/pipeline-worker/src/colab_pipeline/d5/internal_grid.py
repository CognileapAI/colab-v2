"""파일 내부에서 격자·좌표계를 산출한다 — 후주입 없이 (DATA-REFERENCE §1.1).

**무엇을 고치는가.** 운영 dry-run 에서 본체 123 건 중 39 건이 좌표계 단계에서
떨어졌다(GK-2A 31 · MODIS 8). 파싱은 123/123 성공했다. 원인은 파일에 격자가
없어서가 아니라 **코드가 이 두 포맷에 기준 격자 파일 후주입을 강제**한 것이다.
`DATA-REFERENCE §1.1` 이 이미 실측으로 「HDF4·GeoTIFF·NetCDF 는 파일 내부만으로
계산된다 ✅확인 … 이 셋에 후주입을 강제하는 규칙이 있다면 그것이 완화 대상」
이라고 적어 두었고, 이 모듈이 그 완화다.

**정본을 근거로 바로 고치지 않았다 — 실물로 다시 쟀다** (`§0`: 「✅확인」도 마지막으로
적은 값이지 지금 잰 값이 아니다). 재측정 결과는 `sessions/D5-GRID.md §2`.

**합격선은 정본에서 가져온다 — 새로 만들지 않는다** (`§1.1` 표):
  · HDF4 (MODIS Sinusoidal) 7e-14° · NetCDF (GK2A Lambert) 1.3e-5°

⚠ **좌표를 지어내지 않는다 (DR-9).** 투영을 실제로 못 세우면 예외이고, 호출자는
기존대로 `[미상]` + FAILURE 로 간다. HSR 은 헤더의 투영 파라미터 자리가 전부 0
이므로 여기 해당하지 않는다 — **기준 격자 파일이 계속 필수다** (`§0 M-8`).

**stage2 대기.** 배포 단위·완료 정의에서 빠진다 — 파일·시험 유지(`〈71〉-㉰`).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np


class InternalGridUnavailable(Exception):
    """파일 내부만으로 격자를 세울 수 없다 — 지어내지 않고 호출자에게 넘긴다."""


# --------------------------------------------------------------------------
# HDF4 — MODIS Sinusoidal (StructMetadata.0)
# --------------------------------------------------------------------------
def _struct_metadata(path: Path) -> str:
    from pyhdf.SD import SD, SDC

    sd = SD(str(path), SDC.READ)
    try:
        return str(sd.attributes().get("StructMetadata.0", ""))
    finally:
        sd.end()


def hdf4_sinusoidal_grid(path: Path) -> tuple[np.ndarray, np.ndarray, str]:
    """MODIS 타일의 위경도를 `StructMetadata.0` 만으로 만든다.

    실물이 주는 값 — `Projection=GCTP_SNSOID` · `ProjParams=(6371007.181, 0…)` ·
    `UpperLeftPointMtrs` · `LowerRightMtrs` · `XDim`/`YDim`. 셀 중심을 쓴다.
    """
    sm = _struct_metadata(Path(path))
    if not sm:
        raise InternalGridUnavailable("StructMetadata.0 이 없다")
    if "GCTP_SNSOID" not in sm:
        raise InternalGridUnavailable("Sinusoidal 이 아닌 투영 — 이 경로로 세우지 않는다")

    def _pair(key: str) -> tuple[float, float]:
        m = re.search(rf"{key}=\(([^)]*)\)", sm)
        if not m:
            raise InternalGridUnavailable(f"{key} 가 없다")
        parts = [p.strip() for p in m.group(1).split(",")]
        if len(parts) < 2:
            raise InternalGridUnavailable(f"{key} 값이 좌표쌍이 아니다")
        return float(parts[0]), float(parts[1])

    def _dim(key: str) -> int:
        m = re.search(rf"\b{key}=(\d+)", sm)
        if not m:
            raise InternalGridUnavailable(f"{key} 가 없다")
        return int(m.group(1))

    m = re.search(r"ProjParams=\(([^)]*)\)", sm)
    if not m:
        raise InternalGridUnavailable("ProjParams 가 없다")
    radius = float(m.group(1).split(",")[0])
    if radius <= 0:
        raise InternalGridUnavailable(f"지구반경이 채워져 있지 않다: {radius}")

    ulx, uly = _pair("UpperLeftPointMtrs")
    lrx, lry = _pair("LowerRightMtrs")
    nx, ny = _dim("XDim"), _dim("YDim")

    dx = (lrx - ulx) / nx
    dy = (lry - uly) / ny
    xs = ulx + (np.arange(nx) + 0.5) * dx
    ys = uly + (np.arange(ny) + 0.5) * dy
    xg, yg = np.meshgrid(xs, ys)

    from pyproj import CRS, Transformer

    crs = CRS.from_proj4(f"+proj=sinu +R={radius} +units=m +no_defs")
    lon, lat = Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform(xg, yg)
    return np.asarray(lat), np.asarray(lon), f"Sinusoidal R={radius} → WGS84 (파일 내 StructMetadata)"


# --------------------------------------------------------------------------
# NetCDF — CF grid_mapping (GK2A: lambert_conformal_conic)
# --------------------------------------------------------------------------
#: ⚠ **타원체는 재서 골랐다 — 고르는 순간 좌표가 갈린다.** GK2A 는 `grid_mapping`
#: 변수에 타원체를 적지 않는다. 구(球) R=6371 km 로 세우면 동봉 격자와 위도 2.0e-2°
#: (약 2.2 km) 어긋나고, WGS84 타원체로 세우면 1.3e-5° 로 붙는다 — 정본 합격선
#: (`§1.1` 1.3e-5°)을 만족하는 것은 후자뿐이다. 측정은 `sessions/D5-GRID.md §2`.
_LCC_DEFAULT_ELLPS = "WGS84"


def netcdf_projection_grid(path: Path) -> tuple[np.ndarray, np.ndarray, str]:
    """CF `grid_mapping` 변수의 투영 속성만으로 위경도를 만든다.

    지금 실물로 확인된 것은 `lambert_conformal_conic`(GK2A `ko020lc`) 하나다.
    다른 `grid_mapping_name` 은 **여기서 세우지 않는다** — 못 세우는 것을
    세운 척하면 그게 `DR-9` 다.
    """
    from netCDF4 import Dataset

    ds = Dataset(str(path), "r")
    try:
        gm = None
        for name in ds.variables:
            if "grid_mapping_name" in ds.variables[name].ncattrs():
                gm = ds.variables[name]
                break
        if gm is None:
            raise InternalGridUnavailable("grid_mapping 변수가 없다")
        kind = str(gm.getncattr("grid_mapping_name"))
        if kind != "lambert_conformal_conic":
            raise InternalGridUnavailable(f"미지원 grid_mapping_name: {kind}")

        def _num(key: str) -> float:
            if key not in gm.ncattrs():
                raise InternalGridUnavailable(f"투영 속성 {key} 가 없다")
            return float(gm.getncattr(key))

        lat1, lat2 = _num("standard_parallel1"), _num("standard_parallel2")
        lat0, lon0 = _num("origin_latitude"), _num("central_meridian")
        fe, fn = _num("false_easting"), _num("false_northing")
        pixel = _num("pixel_size")
        width, height = int(_num("image_width")), int(_num("image_height"))
        ulx, uly = _num("upper_left_easting"), _num("upper_left_northing")
    finally:
        ds.close()

    if pixel <= 0 or width <= 0 or height <= 0:
        raise InternalGridUnavailable(
            f"격자 크기가 채워져 있지 않다: pixel={pixel} w={width} h={height}")

    xs = ulx + np.arange(width) * pixel
    ys = uly - np.arange(height) * pixel
    xg, yg = np.meshgrid(xs, ys)

    from pyproj import CRS, Transformer

    crs = CRS.from_proj4(
        f"+proj=lcc +lat_1={lat1} +lat_2={lat2} +lat_0={lat0} +lon_0={lon0} "
        f"+x_0={fe} +y_0={fn} +ellps={_LCC_DEFAULT_ELLPS} +units=m +no_defs")
    lon, lat = Transformer.from_crs(crs, "EPSG:4326", always_xy=True).transform(xg, yg)
    return (np.asarray(lat), np.asarray(lon),
            f"Lambert Conformal Conic ({lat1}/{lat2}, {lat0}/{lon0}) → WGS84 (파일 내 투영 속성)")


def internal_latlon(path: Path, fmt: str) -> tuple[np.ndarray, np.ndarray, str]:
    """포맷별 산출기 한 자리. 못 세우면 `InternalGridUnavailable`."""
    if fmt == "HDF4":
        return hdf4_sinusoidal_grid(Path(path))
    if fmt == "NetCDF":
        return netcdf_projection_grid(Path(path))
    raise InternalGridUnavailable(f"이 포맷에는 내부 산출 경로가 없다: {fmt}")


def describe_internal_grid(path: Path, fmt: str) -> str | None:
    """좌표계 문자열만 알아본다 — 배열은 만들지 않는다 (파싱 단계용).

    ⚠ 판정을 「속성이 있는가」로만 하지 않는다. `§0 M-8` 이 정확히 그 자리에서
    틀렸다 — **필드가 있는 것과 값이 채워져 있는 것은 다르다.** 그래서 실제로
    한 번 세워 보고, 서면 그 사실을 돌려준다.
    """
    try:
        _lat, _lon, note = internal_latlon(Path(path), fmt)
    except InternalGridUnavailable:
        return None
    except Exception:
        return None
    return note
