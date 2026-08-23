"""결손 정정 — 결합축 `.nc` 격자가 **조용히 무시**되던 자리 (`〈66〉-ⓒ`).

`grid.py` 의 기준 격자 glob 이 `*.npy` 뿐이라, 한 파일에 `lat`·`lon` 을 다 담은 `.nc` 는
**실패하지도 않고 무시**됐다. 실패도 성공도 아닌 것이 가장 나쁘다 — `DATA-REFERENCE §0` 이
그 무늬로 쓰였다(일곱 중 여섯이 에러를 안 냈다).

정본은 이 파일을 실물로 갖고 있다 — `rdr_500m_latlon.nc`(HSR 정본 격자, `〈66〉`) ·
`gk2a_ko020lc_latlon.nc`.
"""
from __future__ import annotations

import numpy as np
import pytest

from colab_pipeline.d5.grid import GridUnavailableError, find_reference_grid


def _write_combined(path, n=8):
    h5py = pytest.importorskip("h5py")
    lat = np.repeat(np.linspace(30, 43, n)[:, None], n, axis=1).astype("f4")
    lon = np.repeat(np.linspace(118.8, 133.5, n)[None, :], n, axis=0).astype("f4")
    with h5py.File(path, "w") as f:
        f.create_dataset("lat", data=lat)
        f.create_dataset("lon", data=lon)
    return lat, lon


def test_combined_axis_nc_is_found_as_a_reference_grid(tmp_path):
    d = tmp_path / "04.Lat_Lon_info"
    d.mkdir()
    lat, lon = _write_combined(d / "rdr_500m_latlon.nc")
    grid = find_reference_grid(d, expect_shape=(8, 8))
    assert grid.shape == (8, 8)
    assert grid.axes == ("위도", "경도")
    assert np.allclose(np.asarray(grid.lat), lat)
    assert np.allclose(np.asarray(grid.lon), lon)
    assert grid.lat_path == grid.lon_path        # 한 파일이 둘 다 담는다 (`〈66〉`)


def test_combined_nc_wins_when_both_exist(tmp_path):
    """원천 `2_nc` 폴더는 같은 격자를 `.npy` 2건과 `.nc` 1건으로 **둘 다** 준다.

    **`〈69〉-⑵` 로 우선순위가 뒤집혔다** — 예전 이 시험은 `.npy` 가 이기는 것을
    단언했고, 그것이 `〈66〉`(정본 격자는 `.nc`)의 미이행 상태였다. 값이 실제로
    갈리는 것을 박는 시험은 `test_grid_canonical_nc.py` 다.
    """
    d = tmp_path / "04.Lat_Lon_info"
    d.mkdir()
    np.save(d / "Lat_x.npy", np.repeat(np.linspace(30, 43, 8)[:, None], 8, axis=1))
    np.save(d / "Lon_x.npy", np.repeat(np.linspace(118.8, 133.5, 8)[None, :], 8, axis=0))
    _write_combined(d / "combined.nc")
    grid = find_reference_grid(d)
    assert grid.lat_path.name == "combined.nc"


def test_nc_without_coordinate_variables_is_a_hard_failure(tmp_path):
    """무시하지 않는다 — 못 읽으면 실패다 (`DR-9`)."""
    h5py = pytest.importorskip("h5py")
    d = tmp_path / "04.Lat_Lon_info"
    d.mkdir()
    with h5py.File(d / "no_coords.nc", "w") as f:
        f.create_dataset("LST", data=np.zeros((8, 8), dtype="f4"))
    with pytest.raises(GridUnavailableError):
        find_reference_grid(d)
