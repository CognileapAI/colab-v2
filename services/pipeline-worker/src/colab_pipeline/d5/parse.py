"""헤더 파싱 = 자동 추출 (DATAMODEL §4.1 · DR-14).

포맷·변수·기간·좌표계·격자·용량을 **파일에서** 읽는다 — 사람이 타이핑하지 않는다.
PoC 의 archive-first(등재 시점에 파일을 안 여는) 구조는 계승하지 않는다.
못 읽은 값은 [미상]이다 — 추정으로 채우지 않는다.

**stage2 대기.** 이 모듈은 배포 단위·완료 정의에서 빠진다 — 파일은 지우지 않고
시험도 계속 CI 에서 돌린다(`〈71〉-㉰`). 근거: `dev-package/sessions/S1-PLAN.md` §5.2 행 7
(`〈75〉` 로 `grid.py` 만 부활, 나머지 6파일은 휴면 유지) · `PLAN-SoT.md §9 〈74〉〈75〉`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from .detect import DetectionResult
from .formats import UNKNOWN
from .hsr import HsrResult, parse_hsr

_COORD_VAR_NAMES = {"lat", "lon", "latitude", "longitude", "x", "y", "time",
                    "gk2a_imager_projection", "crs", "spatial_ref"}


@dataclass
class AutoMetadata:
    format: str
    variables: list[str] = field(default_factory=list)
    period: tuple[str, str] | str = UNKNOWN
    crs: str = UNKNOWN
    grid: tuple[int, int] | str = UNKNOWN
    size_bytes: int = 0
    crs_embedded: bool = False      # 파일 안에 좌표가 있는가 (기준 격자 필요 여부)
    notes: list[str] = field(default_factory=list)


class ParseError(Exception):
    pass


def _parse_netcdf(path: Path, meta: AutoMetadata) -> None:
    from netCDF4 import Dataset

    ds = Dataset(path, "r")
    try:
        all_vars = list(ds.variables)
        meta.variables = [v for v in all_vars if v.lower() not in _COORD_VAR_NAMES]
        has_latlon = any(v.lower() in ("lat", "latitude") for v in all_vars) and \
                     any(v.lower() in ("lon", "longitude") for v in all_vars)
        if has_latlon:
            meta.crs = "WGS84 (파일 내 좌표 변수)"
            meta.crs_embedded = True
        dims = {d: len(ds.dimensions[d]) for d in ds.dimensions}
        spatial = [n for n in dims if n.lower() in ("y", "x", "lat", "lon",
                                                    "latitude", "longitude",
                                                    "rows", "cols", "ydim", "xdim")]
        if len(spatial) >= 2:
            meta.grid = (dims[spatial[0]], dims[spatial[1]])
        elif meta.variables:
            shp = ds.variables[meta.variables[0]].shape
            if len(shp) >= 2:
                meta.grid = (int(shp[-2]), int(shp[-1]))
        if "time" in ds.variables:
            try:
                from netCDF4 import num2date
                t = ds.variables["time"]
                vals = t[:]
                d0 = num2date(vals.min(), t.units)
                d1 = num2date(vals.max(), t.units)
                meta.period = (str(d0), str(d1))
            except Exception:
                meta.notes.append("time 변수는 있으나 기간 해석 실패 — [미상]")
    finally:
        ds.close()


def _parse_hdf4(path: Path, meta: AutoMetadata) -> None:
    from pyhdf.SD import SD, SDC

    sd = SD(str(path), SDC.READ)
    try:
        infos = sd.datasets()
        meta.variables = list(infos.keys())
        shapes = [tuple(v[1]) for v in infos.values() if len(v[1]) >= 2]
        if shapes:
            meta.grid = (int(shapes[0][-2]), int(shapes[0][-1]))
        # MODIS Sinusoidal — 투영 격자. 위경도는 동봉 기준 격자가 필요하다.
        meta.crs_embedded = False
        attrs = sd.attributes()
        sm = attrs.get("StructMetadata.0", "")
        if "GCTP_SNSOID" in str(sm):
            meta.notes.append("투영 = Sinusoidal (StructMetadata) — 위경도는 기준 격자 필요")
    finally:
        sd.end()


def _parse_geotiff(path: Path, meta: AutoMetadata) -> None:
    import rasterio

    with rasterio.open(path) as src:
        meta.variables = [f"band{i}" for i in range(1, src.count + 1)]
        meta.grid = (src.height, src.width)
        if src.crs is not None:
            meta.crs = str(src.crs)
            meta.crs_embedded = True


def _parse_binary(path: Path, meta: AutoMetadata) -> HsrResult:
    r = parse_hsr(path)
    h = r.header
    meta.variables = [f"블록{i + 1}" for i in range(r.blocks_present)]
    meta.grid = (h.ny, h.nx)
    meta.period = (h.tm.isoformat(), h.tm.isoformat())
    # 헤더에 투영 파라미터가 **없다** — 36~63 B 가 실물에서 전부 0 이라 격자를 세울 수 없다.
    # (옛 문서는 「헤더가 직접 준다」였으나 근거가 명세 PDF 였다 — DATA-REFERENCE §0 M-8 · §1.1)
    # HSR 은 다섯 포맷 중 유일하게 기준 격자 파일이 필수인 포맷이다.
    meta.crs_embedded = False
    if r.block_count_mismatch:
        meta.notes.append(
            f"헤더 num_data={h.num_data} 인데 실재 블록 {r.blocks_present} — 배포본 축소")
    return r


def parse_metadata(path: Path, detection: DetectionResult) -> AutoMetadata:
    path = Path(path)
    if detection.format is None:
        raise ParseError(f"포맷 미상 — 파싱 불가: {detection.reason}")
    meta = AutoMetadata(format=detection.format, size_bytes=os.stat(path).st_size)
    if detection.format == "NetCDF":
        _parse_netcdf(path, meta)
    elif detection.format == "HDF4":
        _parse_hdf4(path, meta)
    elif detection.format == "GeoTIFF":
        _parse_geotiff(path, meta)
    elif detection.format == "Binary":
        _parse_binary(path, meta)
    else:
        raise ParseError(f"지원 목록 밖: {detection.format}")
    return meta
