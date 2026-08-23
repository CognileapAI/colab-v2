"""기준 격자 파일 읽기 — `04.Lat_Lon_info` 계열 (`DATA-REFERENCE §1` · `〈57〉`·`〈58〉`·`〈66〉`).

**좌표를 지어내지 않는다.** PoC 구세대는 HSR 위경도를 dummy `linspace` 로 합성하고
「성공」을 반환했다(4곳, `DR-9`) — 진짜 좌표가 옆에 있었는데도. **이 모듈에는 그 경로가
없다.** 못 읽으면 예외이고 호출자는 실패로 끝낸다.

⚠ **한 파일이 두 축을 다 담는 경우가 실물 16건 중 2건이다**(`〈66〉`). `.npy` 쌍만 찾는
glob 은 그 파일을 **실패시키지도 않고 조용히 무시한다** — `〈66〉-ⓒ` 가 `d5/grid.py` 의
결손으로 등재한 그 자리다. 여기서는 `.nc` 결합축을 **먼저** 본다.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


class GridUnavailableError(Exception):
    """기준 격자를 읽을 수 없다 — `[미상]` 이고 실패다. 합성 격자로 대체하지 않는다."""


@dataclass(frozen=True)
class ReferenceGrid:
    lat: np.ndarray
    lon: np.ndarray
    source: str          # 어느 파일에서 왔는지 — 화면·로그가 근거를 말할 수 있게

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(self.lat.shape)


_LAT_NAMES = ("lat", "latitude")
_LON_NAMES = ("lon", "longitude")


def _check_pair(lat: np.ndarray, lon: np.ndarray, source: str) -> ReferenceGrid:
    if lat.ndim != 2 or lon.ndim != 2:
        raise GridUnavailableError(f"격자가 2차원이 아니다({source}): {lat.shape} / {lon.shape}")
    if lat.shape != lon.shape:
        raise GridUnavailableError(f"위도/경도 형상 불일치({source}): {lat.shape} vs {lon.shape}")
    return ReferenceGrid(lat=lat, lon=lon, source=source)


def _from_netcdf(path: Path) -> ReferenceGrid:
    """`rdr_500m_latlon.nc` 처럼 **한 파일에 lat·lon 을 다 담는** 격자 (`〈66〉`)."""
    from netCDF4 import Dataset

    ds = Dataset(str(path), "r")
    try:
        names = {n.lower(): n for n in ds.variables}
        lat_name = next((names[n] for n in _LAT_NAMES if n in names), None)
        lon_name = next((names[n] for n in _LON_NAMES if n in names), None)
        if lat_name is None or lon_name is None:
            raise GridUnavailableError(
                f"{path.name} 에 lat/lon 변수가 없다: {sorted(ds.variables)}")
        lat = np.asarray(ds.variables[lat_name][:], dtype="f8")
        lon = np.asarray(ds.variables[lon_name][:], dtype="f8")
    finally:
        ds.close()
    return _check_pair(lat, lon, path.name)


def _from_npy_pair(lat_path: Path, lon_path: Path) -> ReferenceGrid:
    def _load(p: Path, axis: str) -> np.ndarray:
        try:
            return np.load(p, mmap_mode="r", allow_pickle=False)   # 필요한 창만 (`DR-11`)
        except Exception as e:
            raise GridUnavailableError(f"{axis} 격자 판독 실패({p.name}): {e}") from e

    return _check_pair(np.asarray(_load(lat_path, "위도")),
                       np.asarray(_load(lon_path, "경도")),
                       f"{lat_path.name} + {lon_path.name}")


def find_reference_grid(grid_dir: Path | None, *,
                        expect_shape: tuple[int, int] | None = None) -> ReferenceGrid:
    """격자 폴더에서 좌표를 찾는다. 못 찾으면 예외 — **지어내지 않는다.**"""
    if grid_dir is None:
        raise GridUnavailableError("기준 격자 디렉터리가 지정되지 않았다")
    grid_dir = Path(grid_dir)
    if not grid_dir.is_dir():
        raise GridUnavailableError(f"기준 격자 디렉터리가 없다: {grid_dir.name}")

    errors: list[str] = []
    candidates: list[ReferenceGrid] = []

    # ① 결합축 `.nc` 를 먼저 본다 (`〈66〉` — `.npy` 전용 glob 이 이것을 조용히 버렸다)
    for nc in sorted(grid_dir.glob("*.nc")):
        try:
            candidates.append(_from_netcdf(nc))
        except GridUnavailableError as e:
            errors.append(str(e))

    # ② `.npy` 축 쌍
    lats = sorted(p for p in grid_dir.glob("*.npy") if p.name.lower().startswith("lat"))
    lons = sorted(p for p in grid_dir.glob("*.npy") if p.name.lower().startswith("lon"))
    for lat_p, lon_p in zip(lats, lons):
        try:
            candidates.append(_from_npy_pair(lat_p, lon_p))
        except GridUnavailableError as e:
            errors.append(str(e))

    if not candidates:
        raise GridUnavailableError(
            f"기준 격자를 찾지 못했다({grid_dir.name}): " + ("; ".join(errors) or "후보 0건"))

    if expect_shape is None:
        return candidates[0]

    for g in candidates:
        if g.shape == tuple(expect_shape):
            return g
    shapes = ", ".join(str(g.shape) for g in candidates)
    raise GridUnavailableError(
        f"격자 형상이 데이터와 안 맞는다: 데이터 {tuple(expect_shape)} vs 격자 {shapes}")
