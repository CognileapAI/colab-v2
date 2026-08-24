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

import gzip
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import coords, downsample
from .failures import NotRenderableError
from .hsr import decode_block, parse_hsr

SUPPORTED_FORMATS: list[str] = ["NetCDF", "Binary", "HDF4", "GeoTIFF"]

MAGIC_HDF4 = b"\x0e\x03\x13\x01"
MAGIC_HDF5 = b"\x89HDF\r\n\x1a\n"
MAGIC_TIFF_LE = b"II*\x00"
MAGIC_TIFF_BE = b"MM\x00*"
MAGIC_GZIP = b"\x1f\x8b"
MAGIC_CDF = (b"CDF\x01", b"CDF\x02", b"CDF\x05")

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
        try:                                   # try-open 이 필수다 — 매직만으로 못 가른다
            from netCDF4 import Dataset
            Dataset(str(path), "r").close()
            return "NetCDF"
        except Exception as e:
            raise NotRenderableError(f"HDF5 컨테이너인데 NetCDF 로 열리지 않는다: {e}") from e
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


def _apply_fill_exact(values: np.ndarray, fills: list[float]) -> np.ndarray:
    """**정확일치**로만 결측을 판정한다. 범위 비교를 쓰지 않는다 (`P2.md §2-26`)."""
    out = values.astype("f4", copy=True)
    for fill in fills:
        out[values == fill] = np.nan
    return out


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
        arr = var[:]
        raw = np.ma.filled(np.asarray(arr, dtype="f8"), np.nan) if np.ma.isMaskedArray(arr) \
            else np.asarray(arr, dtype="f8")
        while raw.ndim > 2:             # 시각/밴드 축 — 한 번에 값 하나만 그린다
            raw = raw[0]
        if raw.ndim != 2:
            raise NotRenderableError(f"{path.name}: {name} 이 2차원이 아니다")

        fills = []
        for attr in ("_FillValue", "missing_value"):
            if hasattr(var, attr):
                fills.extend(np.atleast_1d(getattr(var, attr)).astype("f8").tolist())
        values = _apply_fill_exact(raw, fills)
        if hasattr(var, "scale_factor"):
            values = values * float(var.scale_factor)
        if hasattr(var, "add_offset"):
            values = values + float(var.add_offset)
        unit = getattr(var, "units", None)

        lat = lon = None
        lower = {n.lower(): n for n in names}
        lat_n = next((lower[k] for k in ("lat", "latitude") if k in lower), None)
        lon_n = next((lower[k] for k in ("lon", "longitude") if k in lower), None)
        if lat_n and lon_n:
            la = np.asarray(ds.variables[lat_n][:], dtype="f8")
            lo = np.asarray(ds.variables[lon_n][:], dtype="f8")
            if la.ndim == 1 and lo.ndim == 1:
                lo, la = np.meshgrid(lo, la)
            if la.shape == raw.shape:
                lat, lon = la, lo
        if lat is None:
            # 좌표 변수가 없으면 **투영 속성에서 계산한다**(`§4` — nc 는 파일이 격자를
            # 준다, 실측 오차 1.3e-5°). 못 세우면 `None` 이고 지도형은 보류다.
            for n in names:
                v = ds.variables[n]
                if "grid_mapping_name" in v.ncattrs():
                    computed = coords.from_cf_projection(
                        {a: getattr(v, a) for a in v.ncattrs()}, raw.shape)
                    if computed is not None:
                        lat, lon = computed
                    break
    finally:
        ds.close()

    native = (values.shape[0], values.shape[1])
    steps = _steps_for(native, max_side)
    values = _decimate(values, steps).astype("f4")
    if lat is not None:
        # ⚠ 좌표는 **평균하지 않는다** — `downsample.sample_centers` 주석 참조.
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
            raw = np.asarray(sds[:], dtype="f8")
            attrs = sds.attributes()
        finally:
            sds.endaccess()
        while raw.ndim > 2:
            raw = raw[0]

        fills = [float(attrs[k]) for k in ("_FillValue", "missing_value") if k in attrs]
        # MODIS 는 유효범위 밖 코드값(구름·물 등)을 값처럼 담는다 — **각각을 정확일치로**
        # 지운다. `valid_range` 로 범위 비교를 하면 그것이 곧 `>= 249` 버그의 재발이다.
        values = _apply_fill_exact(raw, fills)
        if "valid_range" in attrs:
            lo, hi = (float(v) for v in attrs["valid_range"])
            for code in np.unique(raw[~np.isnan(raw)]):
                if code < lo or code > hi:
                    values[raw == code] = np.nan
        if "scale_factor" in attrs:
            values = values * float(attrs["scale_factor"])
        if "add_offset" in attrs:
            values = values + float(attrs["add_offset"])
        unit = attrs.get("units")
        # **`C-3`** — 꼬리 `StructMetadata.0` 의 코너좌표 + Sinusoidal + R 로 격자를
        # 계산한다. 옛 코드는 이 경로를 막아 두고 「좌표는 밖에서 받아야 한다」고 적었는데,
        # 실측이 그것을 뒤집었다(동봉 격자 대비 오차 7e-14°).
        computed = None
        text = sd.attributes().get("StructMetadata.0")
        if text:
            computed = coords.from_struct_metadata(text)
    finally:
        sd.end()
    native = (values.shape[0], values.shape[1])
    steps = _steps_for(native, max_side)
    lat = lon = None
    if computed is not None and computed[0].shape == native:
        lat = downsample.sample_centers(computed[0], steps)
        lon = downsample.sample_centers(computed[1], steps)
    return Field(values=_decimate(values, steps).astype("f4"), variable=name, unit=unit,
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


def read_field(path: Path, *, variable: str | None = None, instant: str | None = None,
               max_side: int = 1024) -> tuple[str, Field]:
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
    except (NotRenderableError, FieldReadError):
        raise
    except Exception as e:                       # 포맷은 맞는데 이 파일이 깨졌다
        raise FieldReadError(f"{path.name}: {type(e).__name__}: {e}") from e
    raise NotRenderableError(f"지원 목록 밖: {fmt}")
