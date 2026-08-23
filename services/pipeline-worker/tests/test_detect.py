"""완료조건 ① — 감지는 매직바이트. 확장자는 힌트일 뿐이다 (DR-3)."""
from pathlib import Path

import pytest

from colab_pipeline.d5.detect import detect_format
from colab_pipeline.d5.formats import SUPPORTED_FORMATS

from fixture_builders import (
    make_cog_tiff,
    make_hdf4_magic_stub,
    make_hsr_bin_gz,
    make_netcdf,
    make_stripped_tiff,
)


def test_supported_formats_is_the_list_not_a_number():
    # 〈51〉 — 숫자가 아니라 목록. PoC 4포맷과 수만 같고 구성이 다르다.
    assert SUPPORTED_FORMATS == ["NetCDF", "Binary", "HDF4", "GeoTIFF"]


def test_hdf_extension_is_hdf4_by_magic(tmp_path: Path):
    p = make_hdf4_magic_stub(tmp_path / "sample.hdf")
    r = detect_format(p)
    assert r.format == "HDF4"


def test_extension_swap_is_corrected_by_magic(tmp_path: Path):
    # red fixture — 확장자만 .nc 로 바꾼 GeoTIFF 가 매직으로 바로잡힌다
    p = make_stripped_tiff(tmp_path / "liar.nc")
    r = detect_format(p)
    assert r.format == "GeoTIFF"
    assert r.extension_mismatch is True


def test_nc_that_is_hdf5_container(tmp_path: Path):
    # DR-3 — .nc 실체가 HDF5 컨테이너. try-open 으로 NetCDF 로 확정된다.
    p = make_netcdf(tmp_path / "gk2a.nc", fmt="NETCDF4")
    r = detect_format(p)
    assert r.format == "NetCDF"
    assert r.container == "HDF5"


def test_classic_netcdf(tmp_path: Path):
    p = make_netcdf(tmp_path / "classic.nc", fmt="NETCDF3_CLASSIC")
    assert detect_format(p).format == "NetCDF"


def test_gzip_hsr_binary(tmp_path: Path):
    p = make_hsr_bin_gz(tmp_path / "RDR_CMP_HSR_PUB_202508131000.bin.gz")
    r = detect_format(p)
    assert r.format == "Binary"
    assert r.container == "gzip"


def test_cog_tif_detects_as_geotiff(tmp_path: Path):
    p = make_cog_tiff(tmp_path / "hls.tif")
    assert detect_format(p).format == "GeoTIFF"


def test_unknown_bytes_fail_closed(tmp_path: Path):
    p = tmp_path / "junk.nc"
    p.write_bytes(b"\x00\x01\x02\x03garbage" * 10)
    r = detect_format(p)
    assert r.format is None       # 지어내지 않는다 — 미상은 미상이다
    assert r.reason
