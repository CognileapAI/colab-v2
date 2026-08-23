"""완료조건 ④ — 실데이터 E2E: 4포맷 각 ≥1건 감지→파싱→좌표→COG.

원천 위치는 환경변수 `COLAB_REFERENCE_DATA` 로 받는다 (문서 절대경로 금지 규칙과
동일한 이유 — 마운트가 환경마다 다르다). 미지정·미마운트면 **skip 이 아니라 fail** —
green-by-skip 을 금지한다 (CLAUDE.md §4). 로컬에서 마운트 없이 단위 테스트만 돌릴
때는 `-m "not e2e"` 로 명시적으로 뺀다.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from colab_pipeline.d5.detect import detect_format
from colab_pipeline.d5.pipeline import run_file
from colab_pipeline.d5.tiff_probe import classify_tiff

pytestmark = pytest.mark.e2e

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


def _first(pattern: str, d: Path) -> Path:
    files = sorted(p for p in d.glob(pattern) if p.name != "desktop.ini")
    if not files:
        pytest.fail(f"{d} 에 {pattern} 없음")
    return files[0]


def test_e2e_netcdf(tmp_path: Path):
    d = _fmtdir("file_format_2_nc")
    f = _first("gk2a_*.nc", d / "00.Data")
    r = run_file(f, workdir=tmp_path, grid_dir=d / "04.Lat_Lon_info")
    assert r.status == "SUCCESS", r.failures
    assert r.metadata.format == "NetCDF"
    assert r.cog_path and classify_tiff(Path(r.cog_path)) == "cog"


def test_e2e_binary_hsr(tmp_path: Path):
    d = _fmtdir("file_format_3_bin")
    f = _first("RDR_CMP_HSR_*.bin.gz", d / "00.Data")
    r = run_file(f, workdir=tmp_path, grid_dir=d / "04.Lat_Lon_info")
    assert r.status == "SUCCESS", r.failures
    assert r.metadata.format == "Binary"
    assert r.metadata.grid == (2881, 2305)
    assert r.cog_path and classify_tiff(Path(r.cog_path)) == "cog"
    assert r.artifact is not None and r.artifact.origin == "산출"


def test_e2e_hdf4(tmp_path: Path):
    d = _fmtdir("file_format_5_HDF5")   # 폴더명이 거짓말 — 실체 HDF4 (F-2)
    f = _first("*h27v05*.hdf", d / "00.Data")
    det = detect_format(f)
    assert det.format == "HDF4" and det.extension_mismatch is False
    # h27v05 타일 격자만 골라 준다 — 타일이 다른 격자를 붙이면 그게 바로 오배정이다
    gd = tmp_path / "grid_h27v05"
    gd.mkdir()
    for axis in ("lat2d_h27v05.npy", "lon2d_h27v05.npy"):
        (gd / axis).symlink_to(d / "04.Lat_Lon_info" / axis)
    r = run_file(f, workdir=tmp_path, grid_dir=gd)
    assert r.status == "SUCCESS", r.failures
    assert r.metadata.format == "HDF4"
    assert r.cog_path and classify_tiff(Path(r.cog_path)) == "cog"


def test_e2e_geotiff_already_cog(tmp_path: Path):
    d = _fmtdir("file_format_4_tif")
    f = _first("HLS.S30.*.tif", d / "00.Data") if (d / "00.Data").is_dir() \
        else _first("HLS.S30.*.tif", d)
    r = run_file(f, workdir=tmp_path)
    assert r.status == "SUCCESS", r.failures
    assert r.metadata.format == "GeoTIFF"
    assert r.input_cog_class == "cog"     # SEED-DATA 실측 — 포맷견본 6건은 이미 COG
    assert r.artifact is None             # DR-2 — 사람이 올린 tif 는 산출물이 아니다


def test_e2e_geotiff_stripped_to_cog(tmp_path: Path):
    # KWRA Output 40건이 스트립 — 하나를 골라 실제 변환까지 간다
    kwra = sorted(_root().glob("3_KWRA_conference*/**/Output/**/*.tif"))
    if not kwra:
        pytest.fail("KWRA Output tif 를 찾지 못했다")
    src = kwra[0]
    assert classify_tiff(src) in ("stripped", "tiled-only")
    r = run_file(src, workdir=tmp_path)
    assert r.status == "SUCCESS", r.failures
    assert r.cog_path and classify_tiff(Path(r.cog_path)) == "cog"
    assert r.artifact is not None and str(r.artifact.path) != str(src)


def test_e2e_hsr_coords_missing_fails(tmp_path: Path):
    # DR-9 음성 — 같은 실파일에서 격자만 못 주면 성공이 아니라 실패다
    d = _fmtdir("file_format_3_bin")
    f = _first("RDR_CMP_HSR_*.bin.gz", d / "00.Data")
    r = run_file(f, workdir=tmp_path, grid_dir=None)
    assert r.status == "FAILURE"
    assert r.metadata.crs == "[미상]"
