"""포맷 4종을 열어 **그릴 값 하나**를 꺼낸다 (`〈51〉` — NetCDF·Binary·HDF4·GeoTIFF).

세 가지를 규칙으로 못박는다.

1. **감지는 매직바이트로 한다. 확장자는 힌트다** (`DR-3` · `DATA-REFERENCE §3`).
   원천에서 세 번 다 확장자가 거짓말을 했다 — 폴더명 `HDF5` 인데 실체 HDF4 ·
   `.nc` 인데 HDF5 컨테이너 · `.tif` 인데 이미 COG. `\\x89HDF` 만으로는 NetCDF4 와
   순수 HDF5 를 못 가르므로 **try-open 이 필수**다.
2. **`variable` 을 생략하면 여기서 고른다.** core 가 파일의 변수 목록을 해석해 고르지
   않는다 (계약 `RenderRequest.variable` 산문).
3. **fill 은 정확일치로 판정한다.** `>=`·`<=` 범위 비교로 거르지 않는다 —
   그 비교가 진짜 관측값을 지운 출시 버그가 실재한다 (`P2.md §10-(가)`).
"""
from __future__ import annotations

import datetime as dt
import gzip
import itertools
import re
from urllib.parse import quote, unquote
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import coords, downsample
from .failures import NotRenderableError
from .hsr import decode_block, parse_hsr
from .native_io import serialized_netcdf

#: 이 단위가 **그릴 수 있는** 포맷 — `〈51〉`·`〈77〉`·`〈134〉`. **숫자가 아니라 목록이다.**
#:
#: ⚠ 같은 이름의 목록이 `pipeline-worker` 의 `d5/formats.py` 에도 있다 — **두 곳에
#: 적혀 있다는 사실 자체가 갈릴 자리다**(`§D.5b-⑵`).
#:
#: GRIB 판독과 렌더 경로가 구현되어 두 목록은 다시 같은 지원 범위를 말한다:
#:
#:   pipeline-worker `SUPPORTED_FORMATS` = 받아서 저장하는 것
#:   여기 `SUPPORTED_FORMATS`            = 그려 낼 수 있는 것
#:                                        = pipeline-worker 의 `RENDERABLE_FORMATS`
#:
SUPPORTED_FORMATS: list[str] = [
    "NetCDF", "Binary", "HDF4", "GeoTIFF", "NumPy", "GRIB", "HDF5"]

MAGIC_HDF4 = b"\x0e\x03\x13\x01"
MAGIC_HDF5 = b"\x89HDF\r\n\x1a\n"
MAGIC_TIFF_LE = b"II*\x00"
MAGIC_TIFF_BE = b"MM\x00*"
MAGIC_GZIP = b"\x1f\x8b"
MAGIC_CDF = (b"CDF\x01", b"CDF\x02", b"CDF\x05")
#: `.npy` — 매직 + 버전 2B + 길이 2B + ASCII 헤더 dict(`descr`·`fortran_order`·`shape`).
#: **확장자가 아니라 매직으로 감지한다**(`〈77〉-⑵`) — 저장 키에 확장자가 없는 자리가 있다.
MAGIC_NPY = b"\x93NUMPY"
#: GRIB — **여기서는 그리려고 보는 것이 아니라 「아는데 안 그린다」고 말하려고 본다**
#: (`〈135〉`). 판정 규칙은 `pipeline-worker` 의 `detect.py` 와 같다: 매직 ＋ **판**
#: (offset 7 이 1 또는 2). `GRIB` 은 인쇄 가능한 ASCII 라 산문과 우연히 겹친다.
MAGIC_GRIB = b"GRIB"
GRIB_EDITIONS = (1, 2)


def _is_grib(head: bytes) -> bool:
    if not head.startswith(MAGIC_GRIB) or len(head) < 8:
        return False
    return head[7] in GRIB_EDITIONS

_COORD_NAMES = {"lat", "lon", "latitude", "longitude", "x", "y", "time",
                "crs", "spatial_ref", "gk2a_imager_projection"}

#: 기본값을 고를 때 **뒤로 미루는** 이름 조각. `[정본 무근거]` — 정본은 「값 하나를
#: 그린다」까지만 말하고 *어느* 값이 기본인지 말하지 않는다.
#: 미루는 이유는 하나다 — 품질 플래그는 **값에 대한 메타데이터**이지 값이 아니다.
#: 실측으로 드러난 자리다: `gk2a_..._lst_ko_*.nc` 는 변수 순서상 `DQF_LST`(품질 플래그)가
#: `LST`(지표면 온도)보다 앞이라, 순서만 보면 미리보기가 품질 플래그를 그린다.
#: ⚠ **지우는 것이 아니라 미루는 것이다** — 플래그밖에 없으면 그것을 그린다.
_DEPRIORITIZED_NAME_PARTS = ("dqf", "qc", "qa", "flag", "quality", "mask", "err")


def _pick_default(names: list[str]) -> str:
    preferred = [n for n in names
                 if not any(part in n.lower() for part in _DEPRIORITIZED_NAME_PARTS)]
    return (preferred or names)[0]


class FieldReadError(Exception):
    """이 조각을 못 읽었다. 조각 묶음이면 부분 실패로, 하나뿐이면 전부 실패로 간다."""


@dataclass
class Field:
    """그릴 값 하나 + 그 값이 놓인 자리.

    자리를 말하는 방식이 둘이다 — 규칙 격자면 `bounds`, 곡선 격자면 `lat`/`lon` 배열.
    **둘 다 없으면 그릴 수 없다.** 근사 격자를 만들어 채우지 않는다 (`DR-9`).
    """
    values: np.ndarray                       # 2D float32 · NaN = 결측
    variable: str
    unit: str | None = None
    lat: np.ndarray | None = None            # 2D 실측 좌표
    lon: np.ndarray | None = None
    bounds: tuple[float, float, float, float] | None = None   # (w, s, e, n) WGS84
    #: 솎기 전 원래 형상과 솎은 간격. **기준 격자는 원래 형상으로 대조하고 같은 간격으로
    #: 솎는다** — 솎은 배열의 형상으로 격자를 찾으면 실물 격자가 「안 맞는다」로 튕긴다.
    native_shape: tuple[int, int] | None = None
    steps: tuple[int, int] = (1, 1)
    #: 이 파일에서 **정확일치로 지운** 결측값들. 캐시 키에 들어간다(`§7.2`) — 결측 판정이
    #: 바뀌면 그림이 바뀌므로 키도 바뀌어야 한다.
    fills: tuple[float, ...] = ()

    @property
    def has_position(self) -> bool:
        return self.bounds is not None or (self.lat is not None and self.lon is not None)


# ── 감지 ─────────────────────────────────────────────────────────────────────
def _head(path: Path) -> tuple[bytes, bool]:
    with open(path, "rb") as f:
        raw = f.read(64)
    if raw.startswith(MAGIC_GZIP):
        with gzip.open(path, "rb") as f:
            return f.read(64), True
    return raw, False


def _plausible_hsr(head: bytes) -> bool:
    """HSR 헤더 개연성 — 매직바이트가 없는 포맷이라 헤더 값의 합리성으로 본다."""
    import struct
    if len(head) < 64:
        return False
    yy, = struct.unpack_from("<h", head, 3)
    mm, dd, hh = head[5], head[6], head[7]
    nx, ny, nz, dxy = struct.unpack_from("<hhhh", head, 20)
    return (1990 <= yy <= 2100 and 1 <= mm <= 12 and 1 <= dd <= 31 and hh <= 23
            and nx > 0 and ny > 0 and nz > 0 and dxy > 0)


@serialized_netcdf
def detect_format(path: Path) -> str:
    """지원 4종 중 하나를 돌려준다. 아니면 `NotRenderableError` — 415 의 근거다."""
    path = Path(path)
    try:
        head, gz = _head(path)
    except OSError as e:
        raise FieldReadError(f"읽기 실패: {e}") from e

    if head.startswith(MAGIC_HDF4):
        return "HDF4"
    if head.startswith(MAGIC_CDF):
        return "NetCDF"
    if head.startswith((MAGIC_TIFF_LE, MAGIC_TIFF_BE)):
        return "GeoTIFF"
    if head.startswith(MAGIC_HDF5):
        if gz:
            raise NotRenderableError("gzip 안의 HDF5 컨테이너 — 지원 조합이 아니다")
        try:
            import h5py
            with h5py.File(path, "r") as h5:
                is_netcdf4 = "_NCProperties" in h5.attrs
            if is_netcdf4:
                from netCDF4 import Dataset
                Dataset(str(path), "r").close()
                return "NetCDF"
            return "HDF5"
        except Exception as e:
            raise NotRenderableError(f"HDF5 컨테이너를 열 수 없다: {e}") from e
    if head.startswith(MAGIC_NPY):
        return "NumPy"
    if _is_grib(head):
        return "GRIB"
    if _plausible_hsr(head):
        return "Binary"
    raise NotRenderableError("알려진 매직바이트가 없다")


# ── 포맷별 판독 ───────────────────────────────────────────────────────────────
def _steps_for(shape: tuple[int, int], max_side: int) -> tuple[int, int]:
    return downsample.steps_for(shape, max_side)


def _decimate(arr: np.ndarray, steps: tuple[int, int]) -> np.ndarray:
    """전체 적재를 피한 뒤에도 남는 크기를 상세 해상도로 줄인다 (`DR-11`).

    ⚠ **stride 가 아니라 블록평균이다** (`V-1` · `PREVIEW-IMPLEMENTATION §10-6`).
    stride 를 쓰면 점 형태 강수가 전역 5.79 % · 국지 16.9 % 사라진다 — 그 비용은
    「빠르다」로 갚아지지 않는다. 썸네일 128 px 에서만 stride 를 쓰고, 그 자리는
    `preview.build_value_layers` 다.

    좌표 배열도 같은 방식으로 줄인다 — 값은 평균인데 좌표만 모서리를 집으면 둘이
    반 블록 어긋난다. 측정된 좌표들의 평균은 그 블록의 중심이고, **지어낸 좌표가
    아니다**(`DR-9` 가 금지한 것은 없는 값을 만드는 것이다).
    """
    return downsample.block_average(np.asarray(arr), steps)


def _windowed_block_average(shape: tuple[int, int], steps: tuple[int, int],
                            read_window) -> np.ndarray:
    """원본 전체를 적재하지 않고 기존 블록 평균과 같은 결과를 만든다."""
    sy, sx = steps
    ny, nx = shape
    out = np.full((-(-ny // sy), -(-nx // sx)), np.nan, dtype="f4")
    for oy, y in enumerate(range(0, ny, sy)):
        strip = np.asarray(read_window(slice(y, min(y + sy, ny)), slice(0, nx)),
                           dtype="f4")
        out[oy:oy + 1] = downsample.block_average(strip, (sy, sx))
    return out


def _read_geotiff(path: Path, variable: str | None, max_side: int) -> Field:
    import rasterio
    from rasterio.warp import Resampling, calculate_default_transform, reproject

    with rasterio.open(path) as src:
        if src.crs is None:
            # 좌표계가 없으면 어디에 그릴지 모른다 — 지어내지 않는다 (`DR-9`)
            raise FieldReadError(f"{path.name}: GeoTIFF 에 좌표계(CRS)가 없다")
        bands = [f"band{i}" for i in range(1, src.count + 1)]
        band_index = 1
        if variable:
            if variable not in bands:
                raise FieldReadError(f"{path.name}: 그럴 값이 없다 — {variable} ∉ {bands}")
            band_index = bands.index(variable) + 1
        name = bands[band_index - 1]

        dst_transform, dst_w, dst_h = calculate_default_transform(
            src.crs, "EPSG:4326", src.width, src.height, *src.bounds)
        scale = max(1.0, max(dst_w, dst_h) / max_side)
        out_w, out_h = max(1, int(dst_w / scale)), max(1, int(dst_h / scale))
        dst_transform, dst_w, dst_h = calculate_default_transform(
            src.crs, "EPSG:4326", src.width, src.height, *src.bounds,
            dst_width=out_w, dst_height=out_h)

        dest = np.full((dst_h, dst_w), np.nan, dtype="f4")
        reproject(
            source=rasterio.band(src, band_index), destination=dest,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=dst_transform, dst_crs="EPSG:4326",
            src_nodata=src.nodata, dst_nodata=np.nan,
            # 연속형 기본값 — 축소 뷰에서 값이 튀지 않게 한다 (`DR-12`).
            resampling=Resampling.average,
        )
        west, north = dst_transform * (0, 0)
        east, south = dst_transform * (dst_w, dst_h)
        unit = None
        units = src.units[band_index - 1] if src.units else None
        if units:
            unit = units
        nodata = src.nodata
    return Field(values=dest, variable=name, unit=unit,
                 fills=() if nodata is None else (float(nodata),),
                 bounds=(float(west), float(south), float(east), float(north)))


def _grib_band_id(src, index: int) -> str:
    tags = src.tags(index)
    pieces = [
        tags.get("GRIB_ELEMENT") or tags.get("GRIB_SHORT_NAME") or f"band{index}",
        tags.get("GRIB_VALID_TIME", "time?"),
        tags.get("GRIB_SHORT_NAME", "level?"),
        tags.get("GRIB_COMMENT", "level?"),
        tags.get("GRIB_GRID_TYPE", src.tags().get("GRIB_GRID_TYPE", "grid?")),
    ]
    return f"grib:{index}:" + "|".join(str(p) for p in pieces)


def _grib_variables(path: Path) -> list[str]:
    import rasterio
    with rasterio.open(path) as src:
        return [_grib_band_id(src, i) for i in range(1, src.count + 1)]


def _read_grib(path: Path, variable: str | None, max_side: int) -> Field:
    import rasterio
    from rasterio.warp import Resampling, calculate_default_transform, reproject

    with rasterio.open(path) as src:
        names = [_grib_band_id(src, i) for i in range(1, src.count + 1)]
        if not names:
            raise NotRenderableError(f"{path.name}: GRIB 메시지가 없다")
        name = variable or _pick_default(names)
        if name not in names:
            raise FieldReadError(f"{path.name}: 그럴 값이 없다 — {name} ∉ {names}")
        index = names.index(name) + 1
        if src.crs is None:
            raw = src.read(index, masked=True).filled(np.nan).astype("f8")
            native = raw.shape
            steps = _steps_for(native, max_side)
            return Field(_decimate(raw, steps).astype("f4"), name,
                         unit=src.tags(index).get("GRIB_UNIT"), native_shape=native, steps=steps)
        transform, width, height = calculate_default_transform(
            src.crs, "EPSG:4326", src.width, src.height, *src.bounds)
        scale = max(1.0, max(width, height) / max_side)
        width, height = max(1, int(width / scale)), max(1, int(height / scale))
        transform, width, height = calculate_default_transform(
            src.crs, "EPSG:4326", src.width, src.height, *src.bounds,
            dst_width=width, dst_height=height)
        values = np.full((height, width), np.nan, dtype="f4")
        reproject(rasterio.band(src, index), values, src_transform=src.transform,
                  src_crs=src.crs, dst_transform=transform, dst_crs="EPSG:4326",
                  src_nodata=src.nodata, dst_nodata=np.nan, resampling=Resampling.average)
        west, north = transform * (0, 0)
        east, south = transform * (width, height)
        return Field(values, name, unit=src.tags(index).get("GRIB_UNIT"),
                     bounds=(max(-180.0, float(west)), max(-90.0, float(south)),
                             min(180.0, float(east)), min(90.0, float(north))))


_HDF5_SELECTION = re.compile(r"^hdf5:(?P<path>/[^\[]+?)(?:\[(?P<indices>\d+(?:,\d+)*)\])?$")
_HDF5_MAX_SELECTIONS = 4096


def _hdf5_variables(h5) -> list[str]:
    import h5py
    out: list[str] = []
    def visit(name, obj):
        if (not isinstance(obj, h5py.Dataset) or obj.ndim < 2
                or obj.dtype.kind not in "biuf"
                or name.lower().rsplit("/", 1)[-1] in _COORD_NAMES):
            return
        path = quote("/" + name, safe="/")
        if obj.ndim == 2:
            out.append("hdf5:" + path)
        else:
            count = int(np.prod(obj.shape[:-2], dtype="i8"))
            if count > _HDF5_MAX_SELECTIONS:
                raise NotRenderableError(
                    f"{path}: slice {count}개는 목록 상한 {_HDF5_MAX_SELECTIONS}개를 넘는다 — "
                    "선행 차원을 줄인 파일로 선택 범위를 명시해야 한다")
            for idx in itertools.product(*(range(n) for n in obj.shape[:-2])):
                out.append(f"hdf5:{path}[{','.join(map(str, idx))}]")
    h5.visititems(visit)
    return out


def _read_hdf5(path: Path, variable: str | None, max_side: int) -> Field:
    import h5py
    with h5py.File(path, "r") as h5:
        names = _hdf5_variables(h5)
        if not names:
            raise NotRenderableError(f"{path.name}: 수치형 2차원 이상 dataset이 없다")
        name = variable or _pick_default(names)
        if name not in names:
            raise FieldReadError(f"{path.name}: 그럴 값이 없다 — {name} ∉ {names}")
        match = _HDF5_SELECTION.fullmatch(name)
        if match is None:
            raise FieldReadError(f"{path.name}: HDF5 선택 표기가 잘못됐다 — {name}")
        ds = h5[unquote(match.group("path"))]
        indices = tuple(int(v) for v in match.group("indices").split(",")) \
            if match.group("indices") else ()
        raw = np.asarray(ds[indices + (slice(None), slice(None))], dtype="f8")
        fills: list[float] = []
        for attr in ("_FillValue", "missing_value"):
            if attr in ds.attrs:
                fills.extend(np.atleast_1d(ds.attrs[attr]).astype("f8").tolist())
        values = _apply_fill_exact(raw, fills)
        if "scale_factor" in ds.attrs:
            values *= float(ds.attrs["scale_factor"])
        if "add_offset" in ds.attrs:
            values += float(ds.attrs["add_offset"])
        if not np.isfinite(values).any():
            raise NotRenderableError(f"{path.name}: {name}은 전부 결측이다")
        unit_raw = ds.attrs.get("units")
        unit = unit_raw.decode() if isinstance(unit_raw, bytes) else unit_raw
        lat = lon = None
        def decoded_values(coord):
            raw_coord = np.asarray(coord, dtype="f8")
            coord_fills: list[float] = []
            for attr in ("_FillValue", "missing_value"):
                if attr in coord.attrs:
                    coord_fills.extend(np.atleast_1d(coord.attrs[attr]).astype("f8").tolist())
            out = _apply_fill_exact(raw_coord, coord_fills)
            if "scale_factor" in coord.attrs:
                out *= float(coord.attrs["scale_factor"])
            if "add_offset" in coord.attrs:
                out += float(coord.attrs["add_offset"])
            return out

        parent = ds.parent
        candidates = {k.lower(): k for k, obj in parent.items()
                      if isinstance(obj, h5py.Dataset)}
        coordinate_pairs = []
        for lat_name in ("lat", "latitude"):
            for lon_name in ("lon", "longitude"):
                if lat_name in candidates and lon_name in candidates:
                    la = decoded_values(parent[candidates[lat_name]])
                    lo = decoded_values(parent[candidates[lon_name]])
                    if la.shape == raw.shape and lo.shape == raw.shape:
                        coordinate_pairs.append((la.astype("f8"), lo.astype("f8")))
        if len(coordinate_pairs) == 1:
            lat, lon = coordinate_pairs[0]
        native = raw.shape
        steps = _steps_for(native, max_side)
        values = _decimate(values, steps).astype("f4")
        if lat is not None:
            lat = downsample.sample_centers(lat, steps)
            lon = downsample.sample_centers(lon, steps)
        return Field(values, name, unit=unit, lat=lat, lon=lon,
                     native_shape=native, steps=steps, fills=tuple(fills))


def _apply_fill_exact(values: np.ndarray, fills: list[float]) -> np.ndarray:
    """**정확일치**로만 결측을 판정한다. 범위 비교를 쓰지 않는다 (`P2.md §2-26`)."""
    out = values.astype("f4", copy=True)
    for fill in fills:
        out[values == fill] = np.nan
    return out


#: 시각 축으로 읽는 차원·변수 이름. **계약이 값을 주지 않았다** — `[정본 무근거]`.
#: CF 규약의 관행 이름이고, 못 찾으면 **첫 축을 시각 축으로 지어내지 않는다.**
_TIME_NAMES = ("time", "times", "t", "valid_time", "forecast_time")


def _parse_instant(raw: str) -> "dt.datetime":
    """계약 `Timestamp`(UTC ISO-8601) 하나를 **정확히** 읽는다.

    ⚠ **관대하게 받지 않는다.** 「비슷한 것」을 받아 주면 오타가 조용히 첫 시각으로
    떨어지고, 그것이 이 결함(`instant` 무시)이 아무도 모르게 살아 있던 모양이다.
    """
    text = raw.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    value = dt.datetime.fromisoformat(text)      # 형식이 아니면 ValueError
    return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)


def _instant_labels(var) -> list[str]:
    """시각 좌표를 계약 표기(UTC ISO-8601)로 편다 — **사유에 실물을 적으려고** 둔다."""
    from netCDF4 import num2date

    values = num2date(np.asarray(var[:]), units=getattr(var, "units", ""),
                      calendar=getattr(var, "calendar", "standard"),
                      only_use_cftime_datetimes=False,
                      only_use_python_datetimes=True)
    out = []
    for v in np.atleast_1d(values):
        stamp = v if v.tzinfo else v.replace(tzinfo=dt.timezone.utc)
        out.append(stamp.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"))
    return out


def _time_index(ds, var, instant: str | None, path: Path) -> tuple[int, int]:
    """`(고를 자리, 그 자리가 있는 축)`. **생략하면 첫 시각**(계약 축자).

    ⭑ ⟨2026-09-03 · 코드리뷰 #3⟩ 종전에는 이 함수가 없었고 `while raw.ndim > 2:
    raw = raw[0]` 이 **언제나 첫 시각**을 집었다 — `instant` 는 서명에만 있고 본문에서
    한 번도 쓰이지 않았다. 계약이 「층마다 시각을 따로 고른다」고 적은 값이 그렇게
    조용히 버려졌고, 캐시 키에도 없어서 **틀린 시각이 모든 시각에 대해 서빙**됐다.

    ⭑ ⟨2026-09-03 · 레인 C 수용 검토 #1⟩ **축 위치를 함께 돌려준다.** 종전에는 자리만
    돌려주고 `_read_netcdf` 가 `raw[t]` 로 **언제나 0축**을 잘랐다. `(time, lat, lon)`
    에서는 우연히 맞았지만 `(lat, lon, time)` 에서는 **위도 한 줄**을 골라 `(lon, time)`
    판을 그림으로 냈다 — 그것도 2차원이라 **예외 하나 없이 틀린 그림**이 나간다.
    축을 찾는 자리와 자르는 자리가 갈라져 있던 것이 원인이라, 찾은 쪽이 축을 말한다.

    ⚠ **정확 일치로만 고른다.** 가장 가까운 시각으로 바꿔 그리면 사용자는 자기가 다른
    시각을 보고 있다는 사실을 모른다 — `_apply_fill_exact` 와 같은 자세다.
    """
    dims = tuple(getattr(var, "dimensions", ()))
    time_dim = next((d for d in dims if d.lower() in _TIME_NAMES), None)
    # 시각 축이 몇 번째인가. **못 찾으면 0** — 남은 축을 첫 자리로 접는 종전 행동 그대로다
    # (밴드 축은 계약에 고르는 자리가 없다). 지어낸 값이 아니라 「모르니 앞에서부터」다.
    axis = dims.index(time_dim) if time_dim is not None else 0
    if instant is None:
        # 생략은 「첫 시각」이다 — **첫 축이 아니다.** 시각 축이 뒤에 있는 파일에서
        # 0축을 자르면 그것은 첫 위도이고, 계약이 적은 값과 다르다.
        return 0, axis
    try:
        wanted = _parse_instant(instant)
    except ValueError as e:
        raise FieldReadError(
            f"{path.name}: 시각 표기가 계약(UTC ISO-8601) 형태가 아니다 — {instant!r}") from e

    time_var = ds.variables.get(time_dim) if time_dim else None
    if time_var is None:
        # 시각 축이 없는 파일에 시각을 지정한 것이다. **조용히 무시하지 않는다** —
        # 무시하면 「지정했는데 안 바뀐다」가 그대로 돌아온다.
        raise FieldReadError(
            f"{path.name}: 이 값에는 시각 축이 없다 — {instant!r} 을 고를 자리가 없다")
    labels = _instant_labels(time_var)
    for i, label in enumerate(labels):
        if _parse_instant(label) == wanted:
            return i, axis
    # ⭑ ⟨2026-09-03 · 레인 C 수용 검토 #2⟩ **`NotRenderableError` 다.** 계획 레인 C 행이
    # 이 자리를 「기존 NOT_RENDERABLE 오류」로 못박았고, `failures.is_retry_pointless` 가
    # 바로 그 형으로 재시도 무의미를 판정한다 — 파일이 안 가진 시각은 몇 번을 다시
    # 눌러도 없다. 종전 `FieldReadError` 는 `RENDER_UNKNOWN_ERROR` 로 나가 「다시
    # 그리기」가 뜨고, 눌러도 영원히 같은 실패가 돌아왔다.
    #
    # ⚠ 사유에 **목록을 통째로 싣지 않는다** — 8760시각 파일에서 그 사유가 화면을 덮는다.
    # 개수 · 처음 · 마지막이면 「내가 요청한 것이 이 파일의 범위 밖인가」를 답할 수 있다.
    raise NotRenderableError(
        f"{path.name}: 그럴 시각이 없다 — {instant} ∉ "
        f"시각 {len(labels)}개"
        + (f"(처음 {labels[0]} · 마지막 {labels[-1]})" if labels else "(비어 있다)"))


@serialized_netcdf
def _read_netcdf(path: Path, variable: str | None, instant: str | None,
                 max_side: int) -> Field:
    from netCDF4 import Dataset

    ds = Dataset(str(path), "r")
    try:
        names = list(ds.variables)
        drawable = [n for n in names
                    if n.lower() not in _COORD_NAMES and ds.variables[n].ndim >= 2]
        if not drawable:
            raise NotRenderableError(f"{path.name}: 2차원 이상 값 변수가 없다")
        if variable:
            if variable not in drawable:
                raise FieldReadError(f"{path.name}: 그럴 값이 없다 — {variable} ∉ {drawable}")
            name = variable
        else:
            name = _pick_default(drawable)   # 생략하면 viz-render 가 고른다 (계약 산문)

        var = ds.variables[name]
        # ⚠ netCDF4 는 기본으로 `scale_factor`·`add_offset`·`_FillValue` 를 **자동 적용**한다.
        # 그대로 두면 ① 우리가 스케일을 한 번 더 걸어 값이 조용히 100배 틀리고
        # (실측: GK2A `LST` 가 276 K 가 아니라 2.76 으로 나왔다 — 에러 없이 그럴듯했다)
        # ② fill 판정이 **스케일된 실수**에서 일어나 「정확일치」가 부동소수 비교가 된다.
        # 그래서 자동 적용을 끄고 **원시값에서 정확일치로 fill 을 판정한 뒤** 스케일한다
        # (`P2.md §10-(가)` 의 순서 규칙 그대로).
        var.set_auto_maskandscale(False)
        # **시각을 먼저 고른다**(코드리뷰 #3) — 자르기 전에 고르지 않으면 고를 자리가 없다.
        t, t_axis = _time_index(ds, var, instant, path)
        selected_time_axis = t_axis if var.ndim > 2 else None
        remaining = [axis for axis in range(var.ndim) if axis != selected_time_axis]
        spatial_axes = remaining[-2:]
        if len(spatial_axes) != 2:
            raise NotRenderableError(f"{path.name}: {name} 이 2차원이 아니다")
        native = (int(var.shape[spatial_axes[0]]), int(var.shape[spatial_axes[1]]))
        steps = _steps_for(native, max_side)

        fills = []
        for attr in ("_FillValue", "missing_value"):
            if hasattr(var, attr):
                fills.extend(np.atleast_1d(getattr(var, attr)).astype("f8").tolist())
        def read_window(rows, cols):
            selection = []
            for axis in range(var.ndim):
                if axis == selected_time_axis:
                    selection.append(t)
                elif axis == spatial_axes[0]:
                    selection.append(rows)
                elif axis == spatial_axes[1]:
                    selection.append(cols)
                else:
                    selection.append(0)
            arr = var[tuple(selection)]
            raw_block = (np.ma.filled(np.asarray(arr, dtype="f8"), np.nan)
                         if np.ma.isMaskedArray(arr) else np.asarray(arr, dtype="f8"))
            block = _apply_fill_exact(raw_block, fills)
            if hasattr(var, "scale_factor"):
                block *= float(var.scale_factor)
            if hasattr(var, "add_offset"):
                block += float(var.add_offset)
            return block

        values = _windowed_block_average(native, steps, read_window)
        unit = getattr(var, "units", None)

        lat = lon = None
        lower = {n.lower(): n for n in names}
        lat_n = next((lower[k] for k in ("lat", "latitude") if k in lower), None)
        lon_n = next((lower[k] for k in ("lon", "longitude") if k in lower), None)
        row_idx = np.minimum(np.arange(values.shape[0]) * steps[0] + steps[0] // 2,
                             native[0] - 1)
        col_idx = np.minimum(np.arange(values.shape[1]) * steps[1] + steps[1] // 2,
                             native[1] - 1)
        row_idx[-1], col_idx[-1] = native[0] - 1, native[1] - 1
        if lat_n and lon_n:
            lat_var, lon_var = ds.variables[lat_n], ds.variables[lon_n]
            if lat_var.ndim == 1 and lon_var.ndim == 1:
                la = np.asarray(lat_var[row_idx], dtype="f8")
                lo = np.asarray(lon_var[col_idx], dtype="f8")
            else:
                # netCDF4 의 고급 인덱싱은 직교곱을 만들므로 미리보기 행만 읽는다.
                la = np.vstack([np.asarray(lat_var[int(row), col_idx], dtype="f8")
                                for row in row_idx])
                lo = np.vstack([np.asarray(lon_var[int(row), col_idx], dtype="f8")
                                for row in row_idx])
            if la.ndim == 1 and lo.ndim == 1:
                lo, la = np.meshgrid(lo, la)
            if la.shape == native or la.shape == values.shape:
                lat, lon = la, lo
        if lat is None:
            # 좌표 변수가 없으면 **투영 속성에서 계산한다**(`§4` — nc 는 파일이 격자를
            # 준다, 실측 오차 1.3e-5°). 못 세우면 `None` 이고 지도형은 보류다.
            for n in names:
                v = ds.variables[n]
                if "grid_mapping_name" in v.ncattrs():
                    computed = coords.from_cf_projection(
                        {a: getattr(v, a) for a in v.ncattrs()}, native,
                        row_indices=row_idx, col_indices=col_idx)
                    if computed is not None:
                        lat, lon = computed
                    break
    finally:
        ds.close()

    if lat is not None:
        # ⚠ 좌표는 **평균하지 않는다** — `downsample.sample_centers` 주석 참조.
        if lat.shape == native:
            lat = downsample.sample_centers(lat, steps)
            lon = downsample.sample_centers(lon, steps)
    return Field(values=values, variable=name, unit=unit, lat=lat, lon=lon,
                 native_shape=native, steps=steps, fills=tuple(float(f) for f in fills))


def _read_hdf4(path: Path, variable: str | None, max_side: int) -> Field:
    from pyhdf.SD import SD, SDC

    sd = SD(str(path), SDC.READ)
    try:
        infos = sd.datasets()
        drawable = [n for n, v in infos.items() if len(v[1]) >= 2]
        if not drawable:
            raise NotRenderableError(f"{path.name}: 2차원 이상 SDS 가 없다")
        if variable:
            if variable not in drawable:
                raise FieldReadError(f"{path.name}: 그럴 값이 없다 — {variable} ∉ {drawable}")
            name = variable
        else:
            name = _pick_default(drawable)
        sds = sd.select(name)
        try:
            attrs = sds.attributes()
            shape = tuple(int(v) for v in infos[name][1])
            native = (shape[-2], shape[-1])
            steps = _steps_for(native, max_side)
            fills = [float(attrs[k]) for k in ("_FillValue", "missing_value") if k in attrs]

            def read_window(rows, cols):
                start = [0] * len(shape)
                count = [1] * len(shape)
                start[-2:] = [rows.start, cols.start]
                count[-2:] = [rows.stop - rows.start, cols.stop - cols.start]
                raw_block = np.asarray(sds.get(start=start, count=count), dtype="f8").reshape(
                    rows.stop - rows.start, cols.stop - cols.start)
                block = _apply_fill_exact(raw_block, fills)
                if "valid_range" in attrs:
                    lo, hi = (float(v) for v in attrs["valid_range"])
                    block[(raw_block < lo) | (raw_block > hi)] = np.nan
                if "scale_factor" in attrs:
                    block *= float(attrs["scale_factor"])
                if "add_offset" in attrs:
                    block += float(attrs["add_offset"])
                return block

            values = _windowed_block_average(native, steps, read_window)
        finally:
            sds.endaccess()
        unit = attrs.get("units")
        # **`C-3`** — 꼬리 `StructMetadata.0` 의 코너좌표 + Sinusoidal + R 로 격자를
        # 계산한다. 옛 코드는 이 경로를 막아 두고 「좌표는 밖에서 받아야 한다」고 적었는데,
        # 실측이 그것을 뒤집었다(동봉 격자 대비 오차 7e-14°).
        computed = None
        text = sd.attributes().get("StructMetadata.0")
        if text:
            row_idx = np.minimum(np.arange(values.shape[0]) * steps[0] + steps[0] // 2,
                                 native[0] - 1)
            col_idx = np.minimum(np.arange(values.shape[1]) * steps[1] + steps[1] // 2,
                                 native[1] - 1)
            row_idx[-1], col_idx[-1] = native[0] - 1, native[1] - 1
            computed = coords.from_struct_metadata(
                text, row_indices=row_idx, col_indices=col_idx)
    finally:
        sd.end()
    lat = lon = None
    if computed is not None:
        lat, lon = computed
    return Field(values=values.astype("f4"), variable=name, unit=unit,
                 lat=lat, lon=lon,
                 native_shape=native, steps=steps, fills=tuple(float(f) for f in fills))


def _read_binary(path: Path, variable: str | None, max_side: int) -> Field:
    result = parse_hsr(path)
    labels = [result.block_label(i) for i in range(len(result.blocks))]
    index = 0
    if variable:
        if variable not in labels:
            raise FieldReadError(f"{path.name}: 그럴 값이 없다 — {variable} ∉ {labels}")
        index = labels.index(variable)
    values = decode_block(result.blocks[index])
    # 반사도 블록만 dBZ 다 — 고도(m)·지점정보는 값 그대로다 (`DATA-REFERENCE §2.2`).
    unit = "dBZ" if labels[index] == "에코" else None
    native = (values.shape[0], values.shape[1])
    steps = _steps_for(native, max_side)
    return Field(values=_decimate(values, steps).astype("f4"),
                 variable=labels[index], unit=unit,
                 # HSR 결측 3값 중 **둘만** 결측이다 — `−20000` 은 유효 하한이다(`§5.6`).
                 fills=(-25000.0, -30000.0),
                 native_shape=native, steps=steps)


def numpy_variable_name(path: Path, display_name: str | None) -> str:
    """`.npy` 의 변수 이름 — **describe 와 read 가 같은 답을 내는 유일한 자리**다.

    `.npy` 는 파일 안에 변수 이름이 없어 **파일 이름의 stem** 을 쓴다. 그런데 저장 배치가
    본체를 `fileId` 로 이름 붙이므로(`kernel/storage_layout`) 디스크의 stem 은 ULID 다 —
    화면의 변수 고르개에 `01J…` 26자가 서는 것이 그 때문이다.

    원래 이름은 원장(core-api)에만 있고, 그것을 여기서 읽으면 D7 이 남의 표에 닿는다
    (불변규칙 1). 그래서 `core-viz.yaml#RenderTarget.fileNames` 가 **식별자와 같은 자리에**
    이름을 실어 보내고, 이 함수가 그 하나를 받는다.

    ⚠ **이름이 없으면 종전 그대로다** — 선택 필드이고, 없을 때 답이 바뀌면 계약 파괴다.
    ⛔ **캐시 키에 닿지 않는다** — `source_digest` 는 디스크 이름을 그대로 쓴다.
    """
    return Path(display_name).stem if display_name else path.stem


def _read_numpy(path: Path, max_side: int, display_name: str | None = None) -> Field:
    """`.npy` — 배열 하나. **결측은 NaN 만이다**(`〈77〉` Ted 판정).

    네 포맷은 결측값이 실측으로 확정돼 있지만 `.npy` 에는 그런 규약이 **없다** —
    배열만 있고 메타가 없다. 그래서 `−9999` 도 `65535` 도 **여기서는 유효값**이다.
    다른 포맷의 규약을 빌려오면 그것이 곧 값을 지우는 일이다(`§6.1` 의 두 전례).

    **좌표를 말하지 않는다** — ③지도형은 HSR 과 같은 자리에서 격자를 받는다(`§E.4-⑶`).
    """
    arr = np.load(path, mmap_mode="r", allow_pickle=False)   # 헤더를 직접 파싱하지 않는다
    values = np.asarray(arr, dtype="f8")
    while values.ndim > 2:            # 시각·밴드 축 — 한 번에 값 하나만 그린다
        values = values[0]
    if values.ndim != 2:
        raise NotRenderableError(f"{path.name}: 2차원 배열이 아니다 — shape={arr.shape}")
    native = (values.shape[0], values.shape[1])
    steps = _steps_for(native, max_side)
    return Field(values=_decimate(values, steps).astype("f4"),
                 variable=numpy_variable_name(path, display_name),
                 unit=None, native_shape=native, steps=steps, fills=())


@serialized_netcdf
def describe_field(path: Path, *,
                   display_name: str | None = None) -> tuple[str, list[str], list[str]]:
    """`(포맷, 그릴 수 있는 이름들, 시각 표기들)` — **값을 읽지 않는다.**

    ⭑ ⟨21차 해제 · `core-viz.yaml#describeTarget`⟩ 화면의 변수 고르개·시각 고르개가
    값을 얻는 자리다. 종전에는 `RenderRequest.variable`·`instant` 가 고를 값을 열어
    두고도 **그 목록을 얻을 경로가 0건**이었다.

    ⚠ **`read_field` 의 규칙을 다시 적지 않는다** — 같은 상수(`_COORD_NAMES` ·
    `_TIME_NAMES`)와 같은 판정(2차원 이상 · `band1..N` · `block_label`)을 쓴다. 여기서
    한 벌 더 적으면 「고를 수 있다고 한 이름」과 「실제로 그려지는 이름」이 갈린다.

    ⚠ **배열을 만들지 않는다** — 격자를 재투영하지도 소수화하지도 않는다. 이 함수는
    렌더 부작용이 없고 캐시 키에 닿지 않는다(계약 산문 축자).

    ⚠ **시각은 기본 변수의 축이다.** 파일 안에서 변수마다 시각 축이 다를 수 있지만
    `_time_index` 도 **고른 변수의 dims** 에서 축을 찾는다 — 같은 자리를 본다.
    """
    path = Path(path)
    fmt = detect_format(path)
    try:
        if fmt == "GeoTIFF":
            import rasterio

            with rasterio.open(path) as src:
                # `_read_geotiff` 와 **같은 줄**이다 — 밴드 이름은 1부터다.
                bands = [f"band{i}" for i in range(1, src.count + 1)]
            if not bands:
                raise NotRenderableError(f"{path.name}: 밴드가 없다")
            # GeoTIFF 에는 계약이 고를 시각 축이 없다 — 빈 목록이지 「0개의 시각」이 아니다.
            return fmt, bands, []

        if fmt == "NetCDF":
            from netCDF4 import Dataset

            ds = Dataset(str(path), "r")
            try:
                drawable = [n for n in ds.variables
                            if n.lower() not in _COORD_NAMES and ds.variables[n].ndim >= 2]
                if not drawable:
                    raise NotRenderableError(f"{path.name}: 2차원 이상 값 변수가 없다")
                var = ds.variables[_pick_default(drawable)]
                dims = tuple(getattr(var, "dimensions", ()))
                time_dim = next((d for d in dims if d.lower() in _TIME_NAMES), None)
                time_var = ds.variables.get(time_dim) if time_dim else None
                labels = [] if time_var is None else _instant_labels(time_var)
                return fmt, drawable, labels
            finally:
                ds.close()

        if fmt == "HDF4":
            from pyhdf.SD import SD, SDC

            sd = SD(str(path), SDC.READ)
            try:
                drawable = [n for n, v in sd.datasets().items() if len(v[1]) >= 2]
            finally:
                sd.end()
            if not drawable:
                raise NotRenderableError(f"{path.name}: 2차원 이상 SDS 가 없다")
            return fmt, drawable, []

        if fmt == "Binary":
            result = parse_hsr(path)
            return fmt, [result.block_label(i) for i in range(len(result.blocks))], []

        if fmt == "NumPy":
            # `_read_numpy` 와 같다 — 배열 하나뿐이고 이름은 **같은 함수**가 고른다.
            return fmt, [numpy_variable_name(path, display_name)], []
        if fmt == "GRIB":
            return fmt, _grib_variables(path), []
        if fmt == "HDF5":
            import h5py
            with h5py.File(path, "r") as h5:
                drawable = _hdf5_variables(h5)
            if not drawable:
                raise NotRenderableError(f"{path.name}: 수치형 2차원 이상 dataset이 없다")
            return fmt, drawable, []
    except (NotRenderableError, FieldReadError):
        raise
    except Exception as e:                       # 포맷은 맞는데 이 파일이 깨졌다
        raise FieldReadError(f"{path.name}: {type(e).__name__}: {e}") from e
    raise NotRenderableError(f"지원 목록 밖: {fmt}")


def read_field(path: Path, *, variable: str | None = None, instant: str | None = None,
               max_side: int = 1024,
               display_name: str | None = None) -> tuple[str, Field]:
    """(포맷, 값 하나). 위치가 파일 안에 없으면 `Field.has_position` 이 False 다."""
    path = Path(path)
    fmt = detect_format(path)
    try:
        if fmt == "GeoTIFF":
            return fmt, _read_geotiff(path, variable, max_side)
        if fmt == "NetCDF":
            return fmt, _read_netcdf(path, variable, instant, max_side)
        if fmt == "HDF4":
            return fmt, _read_hdf4(path, variable, max_side)
        if fmt == "Binary":
            return fmt, _read_binary(path, variable, max_side)
        if fmt == "NumPy":
            return fmt, _read_numpy(path, max_side, display_name)
        if fmt == "GRIB":
            return fmt, _read_grib(path, variable, max_side)
        if fmt == "HDF5":
            return fmt, _read_hdf5(path, variable, max_side)
    except (NotRenderableError, FieldReadError):
        raise
    except Exception as e:                       # 포맷은 맞는데 이 파일이 깨졌다
        raise FieldReadError(f"{path.name}: {type(e).__name__}: {e}") from e
    raise NotRenderableError(f"지원 목록 밖: {fmt}")
