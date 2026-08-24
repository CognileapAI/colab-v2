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


def _load_npy(path: Path) -> np.ndarray:
    try:
        # `np.load` 를 쓴다 — **헤더를 직접 파싱해 `reshape` 하지 않는다**(`§10-19`).
        # 식생 격자는 `fortran_order: True` 라 C-order 를 가정하면 전치된 격자를 얻는다.
        return np.asarray(np.load(path, mmap_mode="r", allow_pickle=False))
    except Exception as e:
        raise GridUnavailableError(f"격자 판독 실패({path.name}): {e}") from e


# ── 짝짓기 (`§5.4.1`) — 파일명으로 해도 되는 것은 **이것뿐**이다 ────────────────
_AXIS_TOKENS = ("lat", "lon")


def _pair_key(path: Path) -> str:
    """위경도 토큰을 **대소문자 무시하고** 지운 나머지 stem. 같으면 한 쌍이다(가-2).

    ⚠ 같은 배열이 트리마다 `Lat_HSR.npy`(첫 글자만 대문자)·`LAT_HSR.npy`(전부 대문자)로
    나온다 — **대소문자 구분 비교를 박으면 한쪽을 못 찾는다**(`§5.4.1`).
    """
    stem = path.stem.casefold()
    for token in _AXIS_TOKENS:
        stem = stem.replace(token, "")
    return stem.strip("_-. ")


def _abs_max(arr: np.ndarray) -> float:
    window = np.asarray(arr[:2048, :2048], dtype="f8")     # 통계는 창으로 (`DR-11`)
    finite = window[np.isfinite(window)]
    if finite.size == 0:
        raise GridUnavailableError("격자에 유한한 값이 없다")
    return float(np.abs(finite).max())


#: 위도는 90 을 넘을 수 없다. **물리적 불가에 의한 배제**라 단독으로 선다(`〈65〉`).
LAT_LIMIT = 90.0


def _order_axes(a: Path, b: Path) -> tuple[Path, Path]:
    """축 판별 사다리 (`§5.4.2`). 돌려주는 것은 (위도 파일, 경도 파일).

    ① 내장 좌표 — `.npy` 에는 없다(배열·dtype·shape 가 전부다).
    ② **값 범위 — 절댓값 최대 > 90 이면 위도일 수 없다 → 경도.** 실측 14/14.
    ③ 쌍 정합 — ②가 한 장을 세우면 나머지는 여집합이다.
    ④ 파일명 — **맨 아래다.** 외부 반입 파일에서 가장 먼저 깨진다(`§10-4`).

    **⚠ 쓰지 않는 규칙 — 축 변동 방향(이방성).** MODIS 경도 2건에서 뒤집힌다(12/14).
    사다리에 넣지 않는다.

    ⚠ 둘 다 90 이하면 **판별 실패다.** 사용자에게 「어느 쪽이 위도입니까」를 묻지 않고
    (`§10-16`), 파일명으로 넘겨짚지도 않으며, 그 쌍을 거절한다(`§E.2-⑦`).
    """
    a_max, b_max = _abs_max(_load_npy(a)), _abs_max(_load_npy(b))
    a_is_lon, b_is_lon = a_max > LAT_LIMIT, b_max > LAT_LIMIT
    if a_is_lon and not b_is_lon:
        return b, a
    if b_is_lon and not a_is_lon:
        return a, b
    if a_is_lon and b_is_lon:
        raise GridUnavailableError(
            f"축을 판별하지 못했다({a.name} / {b.name}): 두 배열 모두 |값| > 90 이라 "
            f"둘 다 위도일 수 없다")
    raise GridUnavailableError(
        f"축을 판별하지 못했다({a.name} / {b.name}): 두 배열 모두 값이 ±90 안에 있어 "
        f"위도와 경도를 구분할 수 없다 — 파일명으로 정하지 않는다")


def _npy_pairs(grid_dir: Path) -> tuple[list[ReferenceGrid], list[str]]:
    """`.npy` 쌍들. **stem 대응으로 짝을 짓고**(가-2·가-3) 형상으로 확정한다(가-4).

    ⚠ 옛 코드는 `sorted(...)[0]` 로 골랐다 — `LAT_HSR`·`LAT_RN15`·`LAT_crop` 이 한
    폴더에 공존하는데 정렬상 `LAT_HSR` 이 먼저 오는 것은 **우연이지 규칙이 아니다.**
    """
    groups: dict[str, list[Path]] = {}
    for path in sorted(grid_dir.glob("*.npy")):
        name = path.name.casefold()
        if not (name.startswith(("lat", "lon")) or "lat" in name or "lon" in name):
            continue
        groups.setdefault(_pair_key(path), []).append(path)

    grids: list[ReferenceGrid] = []
    errors: list[str] = []
    for key, members in sorted(groups.items()):
        if len(members) != 2:
            errors.append(f"짝이 아니다({key or '.'}): {[m.name for m in members]} — "
                          f"위도·경도 두 장이 필요하다")
            continue
        try:
            lat_p, lon_p = _order_axes(*members)
            grids.append(_check_pair(_load_npy(lat_p), _load_npy(lon_p),
                                     f"{lat_p.name} + {lon_p.name}"))
        except GridUnavailableError as e:
            errors.append(str(e))
    return grids, errors


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

    # ② `.npy` 축 쌍 — 짝짓기 규칙 + 축 판별 사다리
    pairs, pair_errors = _npy_pairs(grid_dir)
    candidates.extend(pairs)
    errors.extend(pair_errors)

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
        f"격자 형상이 데이터와 안 맞는다: 데이터 {tuple(expect_shape)} vs 격자 {shapes}"
        + (f" ({'; '.join(errors)})" if errors else ""))
