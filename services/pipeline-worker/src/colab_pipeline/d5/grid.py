"""기준 격자 파일 읽기 — `04.Lat_Lon_info` (DATA-REFERENCE §1 · 〈57〉·〈58〉).

축 타입이 있다 — 위도·경도 한 쌍, 데이터셋당 0~2건.
**좌표를 지어내지 않는다 (DR-9).** PoC 는 4곳에서 임의 격자를 합성하고 「성공」을
반환했다 — 이 모듈에는 그 경로가 존재하지 않는다. 못 읽으면 예외이고,
호출자는 `[미상]` + FAILURE 로 처리한다.

메모리 — np.load(mmap_mode="r") 로 필요한 창만 올린다 (DR-11).
후주입 경로 자체(계약·화면)는 P2/D2c 소관 — 여기는 읽기·검증만 한다.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


class GridUnavailableError(Exception):
    """기준 격자를 읽을 수 없다 — [미상]이고 실패다. 합성 격자로 대체하지 않는다."""


@dataclass
class ReferenceGrid:
    lat: np.ndarray
    lon: np.ndarray
    axes: tuple[str, str]
    lat_path: Path
    lon_path: Path

    @property
    def shape(self) -> tuple[int, ...]:
        return tuple(self.lat.shape)


def _load_axis(path: Path, axis: str) -> np.ndarray:
    if not path.is_file():
        raise GridUnavailableError(f"{axis} 격자 파일이 없다: {path.name}")
    try:
        arr = np.load(path, mmap_mode="r", allow_pickle=False)
    except Exception as e:
        raise GridUnavailableError(f"{axis} 격자 판독 실패({path.name}): {e}") from e
    if arr.ndim != 2:
        raise GridUnavailableError(f"{axis} 격자가 2차원이 아니다: shape={arr.shape}")
    return arr


def load_reference_grid(*, lat_path: Path, lon_path: Path) -> ReferenceGrid:
    lat = _load_axis(Path(lat_path), "위도")
    lon = _load_axis(Path(lon_path), "경도")
    if lat.shape != lon.shape:
        raise GridUnavailableError(
            f"위도/경도 형상 불일치: {lat.shape} vs {lon.shape}")
    return ReferenceGrid(lat=lat, lon=lon, axes=("위도", "경도"),
                         lat_path=Path(lat_path), lon_path=Path(lon_path))


def load_combined_grid(path: Path) -> ReferenceGrid:
    """한 파일이 `lat`·`lon` 을 **둘 다** 담는 격자 (`〈66〉` · 실물 `rdr_500m_latlon.nc`).

    `.npy` 쌍과 달리 축이 분리돼 있지 않다. 실물 16건 중 2건이 이 모양이다 —
    드문 예외가 아니라 12.5% 다 (`sessions/P2-W0-1-measurement.md §2.2`).
    """
    import h5py

    path = Path(path)
    found: dict[str, np.ndarray] = {}
    try:
        with h5py.File(path, "r") as f:
            def _visit(name, obj):
                if isinstance(obj, h5py.Dataset) and obj.ndim == 2:
                    base = name.rsplit("/", 1)[-1].lower()
                    if base in ("lat", "latitude"):
                        found["lat"] = np.asarray(obj[:])
                    elif base in ("lon", "longitude"):
                        found["lon"] = np.asarray(obj[:])
            f.visititems(_visit)
    except OSError as e:
        raise GridUnavailableError(f"격자 컨테이너를 열 수 없다({path.name}): {e}") from e
    if "lat" not in found or "lon" not in found:
        raise GridUnavailableError(
            f"컨테이너에 2차원 lat·lon 이 둘 다 있지 않다({path.name}): {sorted(found)}")
    if found["lat"].shape != found["lon"].shape:
        raise GridUnavailableError(
            f"위도/경도 형상 불일치: {found['lat'].shape} vs {found['lon'].shape}")
    return ReferenceGrid(lat=found["lat"], lon=found["lon"], axes=("위도", "경도"),
                         lat_path=path, lon_path=path)


def find_reference_grid(grid_dir: Path | None, *, expect_shape: tuple[int, int] | None = None,
                        ) -> ReferenceGrid:
    """디렉터리에서 기준 격자를 찾는다. 못 찾으면 예외 — 지어내지 않는다.

    ⚠ **결손 정정(`〈66〉-ⓒ`)** — 예전에는 `*.npy` 만 훑어서 결합축 `.nc` 격자가
    **실패하지도 않고 조용히 무시**됐다. 이제 `.npy` 쌍이 없으면 컨테이너를 본다.
    """
    if grid_dir is None:
        raise GridUnavailableError("기준 격자 디렉터리가 지정되지 않았다")
    grid_dir = Path(grid_dir)
    if not grid_dir.is_dir():
        raise GridUnavailableError(f"기준 격자 디렉터리가 없다: {grid_dir}")
    lats = sorted(p for p in grid_dir.glob("*.npy") if p.name.lower().startswith("lat"))
    lons = sorted(p for p in grid_dir.glob("*.npy") if p.name.lower().startswith("lon"))
    if not lats or not lons:
        combined = sorted(p for p in grid_dir.iterdir()
                          if p.is_file() and p.suffix.lower() in (".nc", ".h5", ".hdf5"))
        if not combined:
            raise GridUnavailableError(
                f"기준 격자를 찾지 못했다 (lat npy {len(lats)} · lon npy {len(lons)} · "
                f"컨테이너 0): {grid_dir}")
        reasons = []
        for c in combined:
            try:
                grid = load_combined_grid(c)
            except GridUnavailableError as e:
                reasons.append(str(e))
                continue
            if expect_shape is not None and grid.shape != tuple(expect_shape):
                reasons.append(f"{c.name}: 형상 {grid.shape} ≠ 데이터 {tuple(expect_shape)}")
                continue
            return grid
        raise GridUnavailableError(
            "결합축 격자 후보를 열었으나 쓸 수 있는 것이 없다: " + " | ".join(reasons))
    grid = load_reference_grid(lat_path=lats[0], lon_path=lons[0])
    if expect_shape is not None and grid.shape != tuple(expect_shape):
        raise GridUnavailableError(
            f"격자 형상이 데이터와 안 맞는다: 격자 {grid.shape} vs 데이터 {tuple(expect_shape)}")
    return grid
