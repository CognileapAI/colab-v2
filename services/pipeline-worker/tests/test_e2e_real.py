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

pytestmark = [pytest.mark.e2e, pytest.mark.stage2]

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


def test_e2e_grib_is_detected_and_is_deliberately_not_renderable(tmp_path: Path):
    """**GRIB — 지원하되 그리지 않는다** (`〈134〉`, Ted 판정 ㈎ · 2026-08-26).

    다른 E2E 와 달리 **COG 를 요구하지 않는다.** 정본이 미리보기 대상을
    `bin·nc·tif·HDF` 로 못 박았기 때문이다(결정 2-3). 여기서 요구하는 것은
    **감지되고, 그릴 수 없다고 정직하게 말하는 것** 둘이다.

    ⭑ **디코더가 필요 없다.** 정본 POLICY 핵심규칙 1 이 자동 추출을 **포맷·용량뿐**으로
    줄였고 GRIB 은 미리보기 대상도 아니다. 따라서 `eccodes`·`cfgrib` 없이 매직바이트만
    으로 충분하다 — `〈51〉` 이 걱정한 「아무도 안 쓸 포맷을 위해 디코더를 짜게 된다」가
    **구조적으로 사라졌다.**

    ⚠ **원파일이 아직 0 건이다.** `file_format_1_grib/` 에 `00.Data` 가 없다(실측).
    Ted 가 넣기로 했고(2026-08-26 「레퍼런슨데 데이터에 넣어줄게 기달」), 넣을 자리는
    `02.File-format/file_format_1_grib/00.Data/` 다. **그때까지 이 시험은 fail 로
    선다 — skip 이 아니다.** 완료 조건이 아직 안 닫혔다는 사실이 보여야 한다.
    """
    from colab_pipeline.d5.renderable import is_renderable

    d = _fmtdir("file_format_1_grib")
    f = _first("*.gr*b*", d / "00.Data")
    r = detect_format(f)
    assert r.format == "GRIB", f"{f.name} 이 GRIB 으로 감지되지 않았다: {r.reason}"
    assert is_renderable(r.format) is False, (
        "GRIB 은 미리보기 대상이 아니다 — 그릴 수 있다고 말하면 화면이 거짓이 된다.")


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
