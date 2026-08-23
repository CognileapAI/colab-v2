"""축 판별 — 실물 16건 전건 (`.npy` 14 + `.nc` 2).

`sessions/P2-W0-1-measurement.md` 가 잰 그 16건을 **구현된 규칙으로 다시 판별**한다.
측정과 구현이 갈라지면 여기서 red 가 난다.

**업로드 구성은 시험이 명시한다** — 정본상 데이터셋당 격자는 0~2건이므로(`〈58〉`),
4파일이 한 폴더에 있는 `4_tif`·`5_HDF5` 는 **데이터셋 2개**로 갈려 올라오는 것이 정상이다
(측정 §3.3). 폴더를 그대로 업로드 하나로 보면 짝짓기가 미정의가 된다 — 그 사실도 시험한다.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from colab_pipeline.d5.axis import detect_axes, detect_axes_for_upload

pytestmark = pytest.mark.e2e

_ENV = "COLAB_REFERENCE_DATA"


def _root() -> Path:
    v = os.environ.get(_ENV)
    if not v or not Path(v).is_dir():
        pytest.fail(f"{_ENV} 가 원천 디렉터리를 가리키지 않는다 — E2E 는 skip 하지 않는다")
    return Path(v)


def _ll(folder: str) -> Path:
    d = _root() / "02.File-format" / folder / "04.Lat_Lon_info"
    if not d.is_dir():
        pytest.fail(f"원천 폴더 없음: {d}")
    return d


# 업로드(=데이터셋) 단위로 묶은 격자 쌍 7건 + 결합축 `.nc` 2건 = 파일 16건
_PAIRS = [
    ("file_format_1_grib", "lat2d.npy", "lon2d.npy"),
    ("file_format_2_nc", "lat2d.npy", "lon2d.npy"),
    ("file_format_3_bin", "Lat_HSR.npy", "Lon_HSR.npy"),
    ("file_format_4_tif", "HLS.S30.T51SYB.2025359T023019.v2.0_lat2d.npy",
     "HLS.S30.T51SYB.2025359T023019.v2.0_lon2d.npy"),
    ("file_format_4_tif", "HLS.S30.T52SCE.2025361T022121.v2.0_lat2d.npy",
     "HLS.S30.T52SCE.2025361T022121.v2.0_lon2d.npy"),
    ("file_format_5_HDF5", "lat2d_h27v05.npy", "lon2d_h27v05.npy"),
    ("file_format_5_HDF5", "lat2d_h28v05.npy", "lon2d_h28v05.npy"),
]

_COMBINED = [
    ("file_format_2_nc", "gk2a_ko020lc_latlon.nc"),
    ("file_format_3_bin", "rdr_500m_latlon.nc"),
]


def test_all_sixteen_real_grid_files_resolve():
    seen: list[Path] = []
    for folder, lat_name, lon_name in _PAIRS:
        d = _ll(folder)
        lat_p, lon_p = d / lat_name, d / lon_name
        for p in (lat_p, lon_p):
            if not p.is_file():
                pytest.fail(f"실물 없음: {p}")
        res = detect_axes_for_upload([lat_p, lon_p])
        assert res.rejected == {}, (folder, res.rejected)
        assert (res.resolved[lat_p].carries_lat, res.resolved[lat_p].carries_lon) == (True, False), lat_name
        assert (res.resolved[lon_p].carries_lat, res.resolved[lon_p].carries_lon) == (False, True), lon_name
        seen += [lat_p, lon_p]

    for folder, name in _COMBINED:
        p = _ll(folder) / name
        if not p.is_file():
            pytest.fail(f"실물 없음: {p}")
        d = detect_axes(p)
        assert (d.carries_lat, d.carries_lon) == (True, True), name
        assert d.method == "컨테이너 내부 변수명"
        seen.append(p)

    assert len(seen) == 16, [p.name for p in seen]


def test_every_real_longitude_npy_is_settled_by_value_range_alone():
    """〈65〉 유권해석의 실물 근거 — 경도 파일은 `max > 90` 한 단계로 끝난다."""
    settled = []
    for folder, _lat, lon_name in _PAIRS:
        p = _ll(folder) / lon_name
        d = detect_axes(p)
        assert (d.carries_lat, d.carries_lon) == (False, True), lon_name
        assert d.method == "값 범위(물리적 불가)", (lon_name, d.method)
        settled.append(p.name)
    assert len(settled) == len(_PAIRS)


def test_anisotropy_would_flip_the_two_modis_longitudes():
    """이방성 단독 규칙이 조용히 뒤집는 2건 — 구현은 뒤집지 않는다(교차검증 전용)."""
    import numpy as np
    for name in ("lon2d_h27v05.npy", "lon2d_h28v05.npy"):
        p = _ll("file_format_5_HDF5") / name
        a = np.load(p, mmap_mode="r")
        mad_down = float(np.abs(np.diff(np.asarray(a[:64, :64]), axis=0)).mean())
        mad_right = float(np.abs(np.diff(np.asarray(a[:64, :64]), axis=1)).mean())
        assert mad_down > mad_right, (name, mad_down, mad_right)   # 이방성 단독이면 「위도」
        d = detect_axes(p)
        assert (d.carries_lat, d.carries_lon) == (False, True), name
        assert any("이방성" in w for w in d.warnings), d.warnings


def test_real_combined_nc_grid_actually_drives_the_pipeline(tmp_path):
    """결손 정정의 실물 확인 — 예전 glob(`*.npy` 전용)이면 이 격자는 **조용히 무시**됐다.

    `〈66〉` 이 HSR 정본 격자로 판정한 `rdr_500m_latlon.nc` 를 **단독으로** 쥐여 준다.
    """
    from colab_pipeline.d5.grid import find_reference_grid
    from colab_pipeline.d5.pipeline import run_file

    d = _root() / "02.File-format" / "file_format_3_bin"
    nc = d / "04.Lat_Lon_info" / "rdr_500m_latlon.nc"
    if not nc.is_file():
        pytest.fail(f"실물 없음: {nc}")
    only_nc = tmp_path / "grid_nc"
    only_nc.mkdir()
    (only_nc / nc.name).symlink_to(nc)

    grid = find_reference_grid(only_nc, expect_shape=(2881, 2305))
    assert grid.shape == (2881, 2305)
    assert grid.lat_path == grid.lon_path

    bins = sorted((d / "00.Data").glob("RDR_CMP_HSR_*.bin.gz"))
    if not bins:
        pytest.fail(f"HSR 실파일이 없다: {d / '00.Data'}")
    r = run_file(bins[0], workdir=tmp_path / "out", grid_dir=only_nc)
    assert r.status == "SUCCESS", r.failures
    assert r.metadata.grid == (2881, 2305)
    assert r.artifact is not None and r.artifact.origin == "산출"


def test_four_same_shape_files_in_one_upload_are_rejected_not_guessed():
    """측정 R-3 — 폴더를 업로드 하나로 보면 짝짓기가 미정의다. 지어내지 않는다."""
    d = _ll("file_format_5_HDF5")
    lats = [d / "lat2d_h27v05.npy", d / "lat2d_h28v05.npy"]
    res = detect_axes_for_upload(lats + [d / "lon2d_h27v05.npy", d / "lon2d_h28v05.npy"])
    # 경도 2건은 값 범위 단독으로 서고, 위도 2건은 짝을 못 지어 거절된다
    assert set(res.rejected) == set(lats), (list(res.rejected), list(res.resolved))
