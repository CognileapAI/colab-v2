"""DR-9 음성 시험(합성 격자 0건) + HSR 규칙 (P2 §2 행 25·26)."""
import struct
from pathlib import Path

import numpy as np
import pytest

from colab_pipeline.d5.grid import GridUnavailableError, load_reference_grid
from colab_pipeline.d5.hsr import FILL_NON_OBSERVED, FILL_OUT_OF_RADIUS, parse_hsr, decode_block

from fixture_builders import make_hsr_bin_gz, make_npy_2d


# ── DR-9 — 좌표를 지어내지 않는다 ───────────────────────────────────────

def test_missing_grid_raises_not_synthesizes(tmp_path: Path):
    with pytest.raises(GridUnavailableError):
        load_reference_grid(lat_path=tmp_path / "no_lat.npy", lon_path=tmp_path / "no_lon.npy")


def test_corrupt_grid_raises(tmp_path: Path):
    lat = tmp_path / "Lat.npy"
    lat.write_bytes(b"not an npy file at all")
    lon = make_npy_2d(tmp_path / "Lon.npy", 4, 5)
    with pytest.raises(GridUnavailableError):
        load_reference_grid(lat_path=lat, lon_path=lon)


def test_shape_mismatch_raises(tmp_path: Path):
    lat = make_npy_2d(tmp_path / "Lat.npy", 4, 5)
    lon = make_npy_2d(tmp_path / "Lon.npy", 5, 4)
    with pytest.raises(GridUnavailableError):
        load_reference_grid(lat_path=lat, lon_path=lon)


def test_good_grid_axis_typed(tmp_path: Path):
    lat = make_npy_2d(tmp_path / "Lat.npy", 4, 5, start=33.0)
    lon = make_npy_2d(tmp_path / "Lon.npy", 4, 5, start=124.0)
    g = load_reference_grid(lat_path=lat, lon_path=lon)
    assert g.shape == (4, 5)
    assert g.lat[0, 0] == pytest.approx(33.0)
    assert g.axes == ("위도", "경도")


def test_no_linspace_synthesis_anywhere():
    # DR-9 — PoC 는 4곳에서 좌표를 합성했다. 소스에 그 경로 자체가 없어야 한다.
    import colab_pipeline.d5 as pkg
    root = Path(pkg.__file__).parent
    hits = [
        p.name
        for p in root.glob("*.py")
        if "linspace" in p.read_text(encoding="utf-8")
    ]
    assert hits == []


# ── HSR ─────────────────────────────────────────────────────────────────

@pytest.mark.stage2
def test_hsr_reads_num_data_not_assumed(tmp_path: Path):
    nx, ny = 8, 6
    blocks = [[100] * 48, [200] * 48, [7] * 48]
    p = make_hsr_bin_gz(tmp_path / "hsr3.bin.gz", nx=nx, ny=ny, blocks=blocks)
    r = parse_hsr(p)
    assert r.header.num_data == 3
    assert r.blocks_present == 3
    assert len(r.blocks) == 3          # 뒤 블록을 조용히 버리지 않는다
    assert r.header.nx == nx and r.header.ny == ny


@pytest.mark.stage2
def test_hsr_header_declares_more_than_file_holds(tmp_path: Path):
    # 실측 실물: 원천 배포본이 헤더 num_data=3 인데 1블록만 담는다 — 정직하게 기록
    p = make_hsr_bin_gz(tmp_path / "hsr1.bin.gz", blocks=[[100] * 48], declared_num_data=3)
    r = parse_hsr(p)
    assert r.header.num_data == 3
    assert r.blocks_present == 1
    assert r.block_count_mismatch is True


@pytest.mark.stage2
def test_fill_values_exact_match_only():
    # 행 26 — -20000 은 유효 하한이다. 범위 비교 금지.
    raw = np.array([[-30000, -25000, -20000, 0, 100]], dtype="<i2")
    out = decode_block(raw)
    assert np.isnan(out[0, 0]) and np.isnan(out[0, 1])
    assert out[0, 2] == pytest.approx(-200.0)   # -20000/100 — 살아 있다
    assert out[0, 3] == pytest.approx(0.0)
    assert out[0, 4] == pytest.approx(1.0)
    assert FILL_NON_OBSERVED == -25000 and FILL_OUT_OF_RADIUS == -30000
