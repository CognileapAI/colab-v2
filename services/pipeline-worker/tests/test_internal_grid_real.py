"""파일 내부에서 격자·좌표계를 산출한다 — 위성 자료 두 종(GK-2A · MODIS).

**왜 이 시험이 있나.** 운영 이미지 dry-run 에서 본체 123 건 중 **39 건이 좌표계
단계에서 떨어졌다** — GK-2A(NetCDF) 31 · MODIS(HDF4) 8. 파싱은 123/123 성공했다.
떨어진 이유는 파일에 격자가 없어서가 아니라 **코드가 이 두 포맷에 기준 격자 파일
후주입을 강제**했기 때문이다.

**정본 근거** — `dev-package/DATA-REFERENCE.md §1.1`:
「HDF4·GeoTIFF·NetCDF 는 파일 내부만으로 계산된다 ✅확인 …
 이 셋에 후주입을 강제하는 규칙이 있다면 그것이 완화 대상이다.」

**오차 합격선도 그 표에서 가져온다 — 새로 만들지 않는다.**
  · HDF4 (MODIS Sinusoidal) = **7e-14°**
  · NetCDF (GK2A Lambert)   = **1.3e-5°** (float32 반올림 한계)

**좌표를 지어내지 않는다(DR-9).** 투영 정보가 실제로 없으면 이 경로는 서지 않고
기존의 `[미상]` + FAILURE 로 떨어진다 — 그 음성도 아래에서 단언한다.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest

from colab_pipeline.d5.pipeline import run_file

pytestmark = [pytest.mark.e2e, pytest.mark.stage2]

#: 합격선의 출처 = `dev-package/DATA-REFERENCE.md §1.1` 표. 여기서 새로 정하지 않는다.
TOL_HDF4_DEG = 7e-14
TOL_NETCDF_DEG = 1.3e-5

_ENV = "COLAB_REFERENCE_DATA"


def _root() -> Path:
    v = os.environ.get(_ENV)
    if not v or not Path(v).is_dir():
        pytest.fail(f"{_ENV} 가 원천 디렉터리를 가리키지 않는다 — E2E 는 skip 하지 않는다")
    return Path(v)


def _fmtdir(name: str) -> Path:
    d = _root() / "02.File-format" / name
    if not d.is_dir():
        pytest.fail(f"원천 폴더 없음: {d}")
    return d


def _files(pattern: str, d: Path) -> list[Path]:
    fs = sorted(p for p in d.glob(pattern) if p.name != "desktop.ini")
    if not fs:
        pytest.fail(f"{d} 에 {pattern} 없음")
    return fs


def test_gk2a_netcdf_grid_comes_from_the_file_alone(tmp_path: Path):
    """GK-2A 는 **기준 격자 파일 없이도** 좌표계가 서야 한다 (`grid_dir=None`)."""
    d = _fmtdir("file_format_2_nc")
    f = _files("gk2a_*.nc", d / "00.Data")[0]
    r = run_file(f, workdir=tmp_path, grid_dir=None)
    assert r.status == "SUCCESS", r.failures
    assert r.metadata.crs != "[미상]"
    assert r.metadata.crs_embedded is True, "파일 안에 투영이 있는데 후주입을 요구했다"


def test_modis_hdf4_grid_comes_from_the_file_alone(tmp_path: Path):
    """MODIS 는 **기준 격자 파일 없이도** 좌표계가 서야 한다 (`grid_dir=None`)."""
    d = _fmtdir("file_format_5_HDF5")   # 폴더명이 거짓말 — 실체 HDF4
    f = _files("*h27v05*.hdf", d / "00.Data")[0]
    r = run_file(f, workdir=tmp_path, grid_dir=None)
    assert r.status == "SUCCESS", r.failures
    assert r.metadata.crs != "[미상]"
    assert r.metadata.crs_embedded is True, "파일 안에 투영이 있는데 후주입을 요구했다"


def test_all_gk2a_and_modis_bodies_pass_the_coordinate_stage(tmp_path: Path):
    """**떨어지던 39 건을 그대로 센다** — 세는 단위 = 원천 본체 파일 1건.

    운영 dry-run 의 39 건(GK-2A 31 · MODIS 8)은 원천 본체의 부분집합이다.
    여기서는 원천에 실재하는 본체 전량(GK-2A `.nc` · MODIS `.hdf`)을 좌표계
    단계까지 돌려 **0 건 실패**를 요구한다 — 상위집합이므로 39 건을 덮는다.
    """
    nc = _files("gk2a_*.nc", _fmtdir("file_format_2_nc") / "00.Data")
    hdf = _files("*.hdf", _fmtdir("file_format_5_HDF5") / "00.Data")
    failed: list[str] = []
    for p in nc + hdf:
        r = run_file(p, workdir=tmp_path / p.stem, grid_dir=None)
        if r.status != "SUCCESS":
            failed.append(f"{p.name}: {r.failures}")
    assert not failed, (
        f"좌표계 단계 실패 {len(failed)}/{len(nc) + len(hdf)}건:\n" + "\n".join(failed[:10]))


def test_internal_grid_matches_the_shipped_reference_grid():
    """산출한 격자가 동봉 기준 격자와 **정본 합격선 안에서** 일치한다.

    합격선의 출처 = `DATA-REFERENCE.md §1.1`. 이 시험이 없으면 「성공했다」가
    「그럴듯한 좌표를 지어냈다」와 구분되지 않는다 (`§0` — 여덟 중 일곱이
    에러를 안 냈다).
    """
    from colab_pipeline.d5.internal_grid import internal_latlon

    nd = _fmtdir("file_format_2_nc")
    f = _files("gk2a_*.nc", nd / "00.Data")[0]
    lat, lon, _ = internal_latlon(f, "NetCDF")
    rlat = np.load(nd / "04.Lat_Lon_info" / "lat2d.npy")
    rlon = np.load(nd / "04.Lat_Lon_info" / "lon2d.npy")
    assert float(np.nanmax(np.abs(lat - rlat))) <= TOL_NETCDF_DEG
    assert float(np.nanmax(np.abs(lon - rlon))) <= TOL_NETCDF_DEG

    hd = _fmtdir("file_format_5_HDF5")
    g = _files("*h27v05*.hdf", hd / "00.Data")[0]
    lat, lon, _ = internal_latlon(g, "HDF4")
    rlat = np.load(hd / "04.Lat_Lon_info" / "lat2d_h27v05.npy")
    rlon = np.load(hd / "04.Lat_Lon_info" / "lon2d_h27v05.npy")
    assert float(np.nanmax(np.abs(lat - rlat))) <= TOL_HDF4_DEG
    assert float(np.nanmax(np.abs(lon - rlon))) <= TOL_HDF4_DEG


def test_no_projection_means_failure_not_a_made_up_grid(tmp_path: Path):
    """음성 — 투영이 없으면 **지어내지 않는다**. HSR 은 그대로 실패여야 한다(DR-9).

    완화가 「모든 포맷에 후주입 면제」로 번지지 않았음을 이 한 줄이 잡는다.
    """
    d = _fmtdir("file_format_3_bin")
    f = _files("RDR_CMP_HSR_*.bin.gz", d / "00.Data")[0]
    r = run_file(f, workdir=tmp_path, grid_dir=None)
    assert r.status == "FAILURE"
    assert r.metadata.crs == "[미상]"
