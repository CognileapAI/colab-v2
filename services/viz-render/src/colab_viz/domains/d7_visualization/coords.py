"""파일 **안**에서 격자를 계산한다 — `C-3` 과 그 이웃 (`DATA-PIPELINE-MEASUREMENT §1.1`).

넷 중 **셋은 파일이 격자를 준다.** 실측 오차 —

| 포맷 | 근거 | 오차 |
|---|---|---|
| GeoTIFF | affine + CRS (rasterio 가 이미 한다) | 2.8e-14° |
| HDF4 (MODIS) | 꼬리 `StructMetadata.0` 코너좌표 · Sinusoidal · **R = 6371007.181** | **7e-14°** |
| NetCDF (GK2A) | CF 투영 속성 18종 (LCC + 좌상단 좌표 + `pixel_size`) | **1.3e-5°** (= 1.45 m, float32 한계) |

**HSR 만 다르다** — 헤더의 투영 파라미터 자리(36~63 B)가 실물에서 전부 0 이라 **재현 불가**
(명세 기재값으로 재구성해도 0.053° ≈ 5.9 km 틀린다). 그것은 격자 파일을 받는다(`§5`).

⚠ **여기서 좌표를 지어내지 않는다.** 파일이 값을 안 주면 `None` 을 돌려주고, 호출자는
「지도형 보류」로 간다. `linspace` 합성은 이 모듈에 없다(`DR-9`).
"""
from __future__ import annotations

import re

import numpy as np

#: MODIS Sinusoidal 의 지구 반지름은 **파일이 말해 준다**(`ProjParams[0]`). 여기 상수로
#: 박지 않는다 — 박으면 다른 값을 담은 파일에서 조용히 틀린다.
_SINU_TEMPLATE = "+proj=sinu +R={radius} +lon_0=0 +x_0=0 +y_0=0 +units=m +no_defs"

#: GK2A 는 CF 속성에 **지구 모양을 안 싣는다.** CF 규약이 그 경우를 WGS84 로 읽으라
#: 했고, 실측 대조(동봉 격자 대비 1.3e-5°)가 그 읽기를 뒷받침한다 — **관례가 아니라
#: 대조로 고른 값**이다(`tests/test_e2e_real.py` 가 매번 다시 대조한다).
_LCC_TEMPLATE = ("+proj=lcc +lat_1={sp1} +lat_2={sp2} +lat_0={lat0} +lon_0={lon0} "
                 "+x_0={x0} +y_0={y0} +datum=WGS84 +units=m +no_defs")


def _to_lonlat(proj4: str, xs: np.ndarray, ys: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    from rasterio.warp import transform

    lon, lat = transform(proj4, "EPSG:4326", list(xs.ravel()), list(ys.ravel()))
    shape = xs.shape
    return (np.asarray(lat, dtype="f8").reshape(shape),
            np.asarray(lon, dtype="f8").reshape(shape))


def _centers(ul: float, lr: float, n: int) -> np.ndarray:
    """픽셀 **중심** 좌표. MODIS `PixelRegistration=HDFE_CENTER` 가 그렇게 적혀 있다."""
    step = (lr - ul) / n
    return ul + (np.arange(n) + 0.5) * step


def from_struct_metadata(text: str) -> tuple[np.ndarray, np.ndarray] | None:
    """HDF4-EOS `StructMetadata.0` → (위도, 경도) 2차원. 못 읽으면 `None`."""
    def _num(pattern: str):
        m = re.search(pattern, text)
        return m.group(1) if m else None

    xdim, ydim = _num(r"XDim=(\d+)"), _num(r"YDim=(\d+)")
    ul = re.search(r"UpperLeftPointMtrs=\(([-\d.]+),([-\d.]+)\)", text)
    lr = re.search(r"LowerRightMtrs=\(([-\d.]+),([-\d.]+)\)", text)
    params = re.search(r"ProjParams=\(([-\d.]+)", text)
    if not (xdim and ydim and ul and lr and params):
        return None
    if "GCTP_SNSOID" not in text:
        # 다른 투영을 만나면 **넘겨짚지 않는다** — 실측이 있는 것은 Sinusoidal 뿐이다.
        return None

    nx, ny = int(xdim), int(ydim)
    ulx, uly = float(ul.group(1)), float(ul.group(2))
    lrx, lry = float(lr.group(1)), float(lr.group(2))
    radius = float(params.group(1))
    xs = np.repeat(_centers(ulx, lrx, nx)[None, :], ny, axis=0)
    ys = np.repeat(_centers(uly, lry, ny)[:, None], nx, axis=1)
    return _to_lonlat(_SINU_TEMPLATE.format(radius=radius), xs, ys)


def from_cf_projection(attrs: dict, shape: tuple[int, int]
                       ) -> tuple[np.ndarray, np.ndarray] | None:
    """CF 투영 속성(LCC) → (위도, 경도) 2차원. 못 읽으면 `None`.

    **`upper_left_easting` 과 `pixel_size` 가 필수다**(`PREVIEW-IMPLEMENTATION §4`) —
    둘 중 하나라도 없으면 격자를 세울 수 없고, 그러면 세우지 않는다.
    """
    if str(attrs.get("grid_mapping_name", "")).lower() != "lambert_conformal_conic":
        return None
    need = ("standard_parallel1", "standard_parallel2", "origin_latitude",
            "central_meridian", "upper_left_easting", "upper_left_northing", "pixel_size")
    if any(k not in attrs for k in need):
        return None

    # ⚠ **MODIS 와 등록 방식이 다르다.** MODIS 는 코너 좌표가 바깥 모서리라 픽셀 중심을
    # 계산해야 하고(`HDFE_CENTER`), GK2A 의 `upper_left_easting` 은 **첫 픽셀 자신의
    # 좌표**다. 반 픽셀(1 km)이 여기서 갈린다 — 실측 대조로 확인했다: 중심을 잡으면
    # 오차가 1.1e-2°(≈1.2 km), 그대로 쓰면 **1.3e-5°** 로 정본 값과 일치한다.
    ny, nx = shape
    size = float(attrs["pixel_size"])
    ulx = float(attrs["upper_left_easting"])
    uly = float(attrs["upper_left_northing"])
    xs = np.repeat((ulx + np.arange(nx) * size)[None, :], ny, axis=0)
    ys = np.repeat((uly - np.arange(ny) * size)[:, None], nx, axis=1)
    proj4 = _LCC_TEMPLATE.format(
        sp1=float(attrs["standard_parallel1"]), sp2=float(attrs["standard_parallel2"]),
        lat0=float(attrs["origin_latitude"]), lon0=float(attrs["central_meridian"]),
        x0=float(attrs.get("false_easting", 0.0)), y0=float(attrs.get("false_northing", 0.0)))
    return _to_lonlat(proj4, xs, ys)
