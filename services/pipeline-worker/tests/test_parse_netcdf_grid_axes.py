"""NetCDF 격자는 **차원 선언 순서가 아니라 축 역할**로 읽는다 (코드리뷰 20260903 #13).

`_parse_netcdf` 가 `meta.grid = (dims[spatial[0]], dims[spatial[1]])` 로 **`ds.dimensions`
의 선언 순서**를 따르고 있어, 경도 차원을 먼저 선언한 파일이 `(nx, ny)` 로 전치돼 나왔다.
그 값의 소비처가 둘이라 실패도 둘이다 —

  ① `pipeline.run_file` 이 `expect_shape` 로 `grid.find_reference_grid` 에 넘긴다.
     전치되면 **맞는 격자가 있어도** 「형상 불일치」로 거절되고 `좌표/격자 없음` 이 된다.
  ② `d5_ingestion` 이 `grid_text`(`"{rows}x{cols}"`)로 사람에게 그대로 보여 준다.

형제 핸들러 셋은 전부 `(rows, cols)` 다 — GeoTIFF `(height, width)` · HDF4 `shape[-2:]` ·
HSR `(ny, nx)`. NetCDF 만 갈라져 있었다.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from colab_pipeline.d5.detect import detect_format
from colab_pipeline.d5.parse import parse_metadata

pytestmark = pytest.mark.stage2

_ROWS, _COLS = 4, 5


def _nc_lon_first(path: Path) -> Path:
    """경도 차원을 **먼저** 선언한 NetCDF — 값 자체는 `(lat, lon)` 배열이다."""
    import numpy as np
    from netCDF4 import Dataset

    ds = Dataset(path, "w", format="NETCDF4")
    ds.createDimension("lon", _COLS)          # ← 선언 순서가 경도 먼저다
    ds.createDimension("lat", _ROWS)
    v = ds.createVariable("LST", "f4", ("lat", "lon"))
    v[:] = np.arange(_ROWS * _COLS, dtype="f4").reshape(_ROWS, _COLS)
    lat = ds.createVariable("lat", "f4", ("lat", "lon"))
    lon = ds.createVariable("lon", "f4", ("lat", "lon"))
    lat[:] = np.linspace(33, 39, _ROWS * _COLS).reshape(_ROWS, _COLS)
    lon[:] = np.linspace(124, 130, _ROWS * _COLS).reshape(_ROWS, _COLS)
    ds.close()
    return path


def test_경도_차원을_먼저_선언해도_격자는_행_열_이다(tmp_path):
    p = _nc_lon_first(tmp_path / "lon_first.nc")
    meta = parse_metadata(p, detect_format(p))
    assert meta.grid == (_ROWS, _COLS), (
        f"차원 선언 순서를 따라 전치됐다: {meta.grid} — 축 역할로 읽어야 한다")


def test_격자_문구도_전치되지_않는다(tmp_path):
    """사용자가 보는 `grid_text` 는 `d5_ingestion` 이 `meta.grid` 로 만든다."""
    p = _nc_lon_first(tmp_path / "lon_first_text.nc")
    meta = parse_metadata(p, detect_format(p))
    assert f"{meta.grid[0]}x{meta.grid[1]}" == f"{_ROWS}x{_COLS}"


def test_위도_차원을_먼저_선언한_파일은_그대로다(tmp_path):
    """회귀 방지 — 종전 순서(위도 먼저)에서 값이 바뀌지 않는다."""
    import numpy as np
    from netCDF4 import Dataset

    p = tmp_path / "lat_first.nc"
    ds = Dataset(p, "w", format="NETCDF4")
    ds.createDimension("lat", _ROWS)
    ds.createDimension("lon", _COLS)
    v = ds.createVariable("LST", "f4", ("lat", "lon"))
    v[:] = np.arange(_ROWS * _COLS, dtype="f4").reshape(_ROWS, _COLS)
    ds.close()
    meta = parse_metadata(p, detect_format(p))
    assert meta.grid == (_ROWS, _COLS)
