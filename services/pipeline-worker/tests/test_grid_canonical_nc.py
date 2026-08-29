"""`〈69〉-⑵` — HSR 정본 격자는 `rdr_500m_latlon.nc` 다. 코드가 그것을 **쓴다**.

`〈66〉` 이 정본을 `.nc` 로 판정했으나 로더는 `.npy` 를 우선했다. 두 격자는
**행·열 각 1셀(500 m) 인덱스 off-by-one** 만큼 어긋난다 — 그림은 멀쩡하고 값만
한 칸 옆으로 붙는다(`DATA-REFERENCE §0` 「에러 없이 그럴듯한 값」).

**그래서 「어느 파일을 골랐나」로는 부족하다 — 좌표값을 박는다.**
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest

from depgate import require_dep

from colab_pipeline.d5.grid import GridUnavailableError, find_reference_grid

_ENV = "COLAB_REFERENCE_DATA"

#: 실측값 (`sessions/P2-W0-1-measurement.md §2` · `DATA-REFERENCE §1`).
#: 이 자리에서 두 격자가 갈린다 — 재유도하지 않고 측정 보고서에서 그대로 가져왔다.
HSR_SOUTH_NC = 30.107119
HSR_SOUTH_NPY = 30.102751


def _write_combined(path, lat, lon):
    h5py = require_dep("h5py")
    with h5py.File(path, "w") as f:
        f.create_dataset("lat", data=lat)
        f.create_dataset("lon", data=lon)


def test_canonical_nc_wins_when_both_grids_are_present(tmp_path: Path):
    """원천 `3_bin` 폴더는 `.npy` 쌍과 `.nc` 를 **둘 다** 준다. 정본은 `.nc` 다(`〈69〉-⑵`)."""
    d = tmp_path / "04.Lat_Lon_info"
    d.mkdir()
    npy_lat = np.repeat(np.linspace(30.102751, 43.0, 8)[:, None], 8, axis=1).astype("f4")
    npy_lon = np.repeat(np.linspace(118.8, 133.553513, 8)[None, :], 8, axis=0).astype("f4")
    np.save(d / "Lat_HSR.npy", npy_lat)
    np.save(d / "Lon_HSR.npy", npy_lon)
    nc_lat = np.repeat(np.linspace(30.107119, 43.0, 8)[:, None], 8, axis=1).astype("f4")
    nc_lon = np.repeat(np.linspace(118.8, 133.560669, 8)[None, :], 8, axis=0).astype("f4")
    _write_combined(d / "rdr_500m_latlon.nc", nc_lat, nc_lon)

    grid = find_reference_grid(d, expect_shape=(8, 8))
    assert grid.lat_path.name == "rdr_500m_latlon.nc"
    assert grid.lat_path == grid.lon_path
    # **파일 이름만으로는 부족하다** — 실제로 읽힌 좌표가 `.nc` 판이어야 한다.
    assert float(np.asarray(grid.lat).min()) == pytest.approx(HSR_SOUTH_NC, abs=1e-5)
    assert float(np.asarray(grid.lat).min()) != pytest.approx(HSR_SOUTH_NPY, abs=1e-5)


def test_npy_pair_is_still_used_when_no_container_is_present(tmp_path: Path):
    d = tmp_path / "04.Lat_Lon_info"
    d.mkdir()
    np.save(d / "Lat_x.npy", np.repeat(np.linspace(30, 43, 8)[:, None], 8, axis=1))
    np.save(d / "Lon_x.npy", np.repeat(np.linspace(118.8, 133.5, 8)[None, :], 8, axis=0))
    assert find_reference_grid(d).lat_path.name == "Lat_x.npy"


def test_an_unreadable_container_falls_back_to_the_npy_pair_and_says_so(tmp_path: Path):
    """컨테이너가 격자가 아니면 `.npy` 로 내려간다 — **조용히 무시하지는 않는다**."""
    h5py = require_dep("h5py")
    d = tmp_path / "04.Lat_Lon_info"
    d.mkdir()
    np.save(d / "Lat_x.npy", np.repeat(np.linspace(30, 43, 8)[:, None], 8, axis=1))
    np.save(d / "Lon_x.npy", np.repeat(np.linspace(118.8, 133.5, 8)[None, :], 8, axis=0))
    with h5py.File(d / "LST_product.nc", "w") as f:
        f.create_dataset("LST", data=np.zeros((8, 8), dtype="f4"))
    grid = find_reference_grid(d)
    assert grid.lat_path.name == "Lat_x.npy"
    assert any("LST_product.nc" in r for r in grid.container_rejections)


def test_no_grid_at_all_is_a_hard_failure(tmp_path: Path):
    d = tmp_path / "04.Lat_Lon_info"
    d.mkdir()
    with pytest.raises(GridUnavailableError):
        find_reference_grid(d)


# ── 실물 ────────────────────────────────────────────────────────────────────
@pytest.mark.e2e
def test_the_real_hsr_grid_that_the_code_picks_has_the_nc_southern_edge():
    """실물 `04.Lat_Lon_info` 에는 `.npy` 쌍과 `.nc` 가 함께 있다. 어느 값을 읽는가."""
    v = os.environ.get(_ENV)
    if not v or not Path(v).is_dir():
        pytest.fail(f"{_ENV} 가 원천 디렉터리를 가리키지 않는다 — skip 하지 않는다")
    d = Path(v) / "02.File-format" / "file_format_3_bin" / "04.Lat_Lon_info"
    assert (d / "Lat_HSR.npy").is_file() and (d / "rdr_500m_latlon.nc").is_file()

    grid = find_reference_grid(d, expect_shape=(2881, 2305))
    assert grid.lat_path.name == "rdr_500m_latlon.nc"
    south = float(np.asarray(grid.lat).min())
    assert south == pytest.approx(HSR_SOUTH_NC, abs=1e-6), \
        f"남단 {south!r} — `.npy` 판({HSR_SOUTH_NPY})을 읽고 있다면 한 셀(500 m) 밀린 값이다"
    assert float(np.asarray(grid.lon).max()) == pytest.approx(133.560669, abs=1e-6)
