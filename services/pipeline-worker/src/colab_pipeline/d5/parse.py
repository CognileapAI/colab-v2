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
from .formats import SUPPORTED_FORMATS, UNKNOWN
from .hsr import HsrResult, parse_hsr
from .internal_grid import describe_internal_grid

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
    # 좌표 변수가 없어도 **투영 속성만으로 격자가 선다** — GK2A(`ko020lc`)가 그렇다.
    # 여기서 후주입을 강제하던 것이 운영 dry-run 39건 중 31건의 실패 원인이었다.
    # (근거 = DATA-REFERENCE §1.1 「NetCDF 는 파일 내부만으로 계산된다 ✅확인」 + 실물 재측정)
    if not meta.crs_embedded:
        note = describe_internal_grid(path, "NetCDF")
        if note:
            meta.crs = note
            meta.crs_embedded = True


def _parse_hdf4(path: Path, meta: AutoMetadata) -> None:
    from pyhdf.SD import SD, SDC

    sd = SD(str(path), SDC.READ)
    try:
        infos = sd.datasets()
        meta.variables = list(infos.keys())
        shapes = [tuple(v[1]) for v in infos.values() if len(v[1]) >= 2]
        if shapes:
            meta.grid = (int(shapes[0][-2]), int(shapes[0][-1]))
        attrs = sd.attributes()
        sm = str(attrs.get("StructMetadata.0", ""))
    finally:
        sd.end()
    # ⚠ 예전에는 여기서 `crs_embedded = False` 로 **고정**해 후주입을 강제했다 —
    # 운영 dry-run 39건 중 MODIS 8건의 실패 원인이 이 한 줄이었다. 정본(§1.1)은
    # 「HDF4 는 파일 내부만으로 계산된다 ✅확인(오차 7e-14°)」이었고, 실물로 다시
    # 재도 같았다(`sessions/D5-GRID.md §2`). 그래서 **세워 보고** 정한다 —
    # 속성이 있다고 믿는 것이 아니라 실제로 서는지를 본다 (`§0 M-8`).
    note = describe_internal_grid(path, "HDF4")
    if note:
        meta.crs = note
        meta.crs_embedded = True
    else:
        meta.crs_embedded = False
        if "GCTP_SNSOID" in sm:
            meta.notes.append("Sinusoidal 인데 격자를 세우지 못했다 — 기준 격자 필요")


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


def _parse_numpy(path: Path, meta: AutoMetadata) -> None:
    """`.npy` — **배열 하나뿐이다. 메타가 없다**(`〈77〉` Ted 판정 · `#58`).

    ⚠ **좌표를 지어내지 않는다.** `.npy` 에는 좌표계·기간·변수명 규약이 **없고**,
    다른 포맷의 규약을 빌려오면 그것이 곧 값을 지우는 일이다
    (`viz-render/readers._read_numpy` 가 같은 이유로 결측 규약을 빌리지 않는다).
    ⟹ `crs_embedded=False` — HSR 과 같은 자리에서 **기준 격자**를 받는다(`§E.4-⑶`).

    ⚠ **`allow_pickle` 을 켜지 않는다.** 켜면 헤더를 읽는 행위가 곧 임의 코드 실행이다.
    읽을 수 없는 `.npy` 는 **읽을 수 없다고 말한다** — 열어 보고 정한다(`§0 M-8`).
    """
    from numpy.lib import format as npformat

    with open(path, "rb") as f:
        version = npformat.read_magic(f)
        # 판별 함수는 판마다 다르다 — 사설 API 를 쓰지 않는다.
        reader = {(1, 0): npformat.read_array_header_1_0,
                  (2, 0): npformat.read_array_header_2_0}.get(version)
        if reader is None:
            raise ParseError(f"모르는 npy 판이다: v{version[0]}.{version[1]}")
        shape, fortran_order, dtype = reader(f)
    if dtype.hasobject:
        raise ParseError(
            f"`.npy` 가 object dtype 이다 — pickle 을 열지 않는다: {dtype}")
    meta.variables = [path.stem or "array"]
    if len(shape) >= 2:
        meta.grid = (int(shape[-2]), int(shape[-1]))
    else:
        meta.notes.append(f"2차원이 아니다 — shape={tuple(shape)}. 격자는 [미상]")
    meta.notes.append(
        f"npy v{version[0]}.{version[1]} · dtype={dtype.str} · shape={tuple(shape)}"
        f" · fortran_order={fortran_order}")
    # `.npy` 는 좌표를 담지 않는다 — 기준 격자가 필요하다(지어내지 않는다 · DR-9).
    meta.crs_embedded = False


def _parse_grib(path: Path, meta: AutoMetadata) -> None:
    """GRIB — **0절(section 0)만 읽는다. 디코더를 들이지 않는다.**

    이 포맷은 **지원하되 그릴 수 없다**(`〈134〉` 결정 2-3 — 「5종이어도 grib 은
    미리보기 대상이 아니다」). `〈134〉-㉰` 이 디코더를 들이지 않았다고 적었고
    이 회차도 들이지 않는다 — **범위를 늘리지 않는다.**

    ⟹ 읽는 것은 **판(edition) · 메시지 수 · 용량**뿐이고, **변수·격자·기간은
    [미상] 로 남긴다.** 없는 값을 채우면 그것이 곧 거짓 자동추출이다(`DR-9`).

    0절 배치 — GRIB1 = `GRIB` ＋ 전체 길이 3B ＋ 판 1B(offset 7),
    GRIB2 = `GRIB` ＋ 예약 2B ＋ 분야 1B ＋ 판 1B(offset 7) ＋ 전체 길이 8B(offset 8).
    """
    messages = 0
    edition: int | None = None
    with open(path, "rb") as f:
        while True:
            head = f.read(16)
            if len(head) < 8 or not head.startswith(b"GRIB"):
                break
            ed = head[7]
            if ed not in (1, 2):
                break
            if edition is None:
                edition = ed
            if ed == 1:
                total = int.from_bytes(head[4:7], "big")
            else:
                if len(head) < 16:
                    break
                total = int.from_bytes(head[8:16], "big")
            if total <= 0:
                break
            messages += 1
            start = f.tell() - len(head)
            f.seek(start + total)
    if edition is None:
        raise ParseError("GRIB 0절을 읽지 못했다 — 판(edition)이 1·2 가 아니다")
    meta.notes.append(
        f"GRIB 판 {edition} · 메시지 {messages}건 — **0절만 읽었다.** "
        "변수·격자·기간은 디코더 없이 읽지 않는다([미상] · DR-9).")
    meta.notes.append("미리보기 대상이 아니다 — 등록·다운로드·계보 확정은 막지 않는다.")
    meta.crs_embedded = False


#: **포맷 → 파서 분기표.** 목록이 아니라 표로 둔 것이 요점이다 —
#: `SUPPORTED_FORMATS` 와의 어긋남을 `tests/test_format_declaration_parity.py` 가
#: **기계로** 잡는다. `#58` 은 이 대조가 없어서 「선언 여섯 · 처리 넷」이 오래 살아남은 건이다.
PARSERS: dict[str, "object"] = {
    "NetCDF": _parse_netcdf,
    "HDF4": _parse_hdf4,
    "GeoTIFF": _parse_geotiff,
    "Binary": _parse_binary,
    "NumPy": _parse_numpy,
    "GRIB": _parse_grib,
}


def parse_metadata(path: Path, detection: DetectionResult) -> AutoMetadata:
    path = Path(path)
    if detection.format is None:
        raise ParseError(f"포맷 미상 — 파싱 불가: {detection.reason}")
    meta = AutoMetadata(format=detection.format, size_bytes=os.stat(path).st_size)
    parser = PARSERS.get(detection.format)
    if parser is None:
        # ⭑ **두 상태를 갈라 말한다** (`#58` · `PLAN-SoT §9 〈271〉-㉯`).
        #   종전에는 어느 쪽이든 「지원 목록 밖」이라 말했고, 그래서 **구현 결함이
        #   정책처럼 읽혔다.** 선언 안에 있는데 파서가 없으면 그것은 목록의 문제가
        #   아니라 **이 파일의 문제**다 — 그렇게 말해야 고치는 사람이 여기로 온다.
        if detection.format in SUPPORTED_FORMATS:
            raise ParseError(
                f"{detection.format} 은 지원 포맷인데 파서 구현이 없다 — "
                "지원 목록의 문제가 아니라 d5/parse.py 의 구현 결함이다")
        raise ParseError(f"지원 목록 밖: {detection.format}")
    parser(path, meta)
    return meta
