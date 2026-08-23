"""기준 격자 축 판별 — `〈63〉-㉰` 채택 조건 ⓐ~ⓓ + `〈65〉` 유권해석 + `〈66〉` 출력 모양.

규칙의 정본은 `sessions/P2-W0-1-measurement.md §4.2` 와 `PLAN-SoT §9 〈65〉` 다.

  ㉠ 컨테이너가 축을 직접 말하면(`.nc` 내부 변수 lat/lon) 그것을 쓰고 값으로 교차검증한다
  ㉡ **값 범위 — max > 90 또는 min < -90 이면 위도일 수 없다 → 경도. 이 배제는 단독으로 성립한다**
     (`〈65〉` 유권해석. ⓑ 를 문면대로 읽으면 이미 확정된 8건을 쌍 정합으로 내려보낸다)
  ㉢ `[-90, 90]` 안이면 모호하다 → **쌍 정합**(형상 같은 격자 정확히 2건 → max 큰 쪽이 경도)
  ㉣ 이방성(축별 단조성)은 **교차검증 전용** — 단독 14/16 이고 MODIS 경도 2건을 조용히 뒤집는다
  ㉤ 파일명은 **보조 전용** — 단독으로 아무것도 확정하지 않는다
  ㉥ 어느 단계도 확정 못 하면 판별 실패이고, 그 파일은 **거절**된다(`〈66〉`).
     축이 빈 행을 넣지 않는다. 등록 자체는 막지 않는다(`〈63〉-ⓒ`)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from colab_pipeline.d5.axis import (
    AxisDetection,
    AxisUndeterminedError,
    detect_axes,
    detect_axes_for_upload,
)


def _npy(path: Path, arr: np.ndarray) -> Path:
    np.save(path, arr)
    return path


def _grid(lat0: float, lat1: float, lon0: float, lon1: float, n: int = 8):
    lat = np.repeat(np.linspace(lat0, lat1, n)[:, None], n, axis=1)
    lon = np.repeat(np.linspace(lon0, lon1, n)[None, :], n, axis=0)
    return lat, lon


# ── ㉡ 물리적 불가에 의한 배제는 단독으로 선다 (〈65〉) ────────────────────────
def test_max_over_90_is_longitude_alone(tmp_path):
    _, lon = _grid(30, 43, 118.8, 133.5)
    d = detect_axes(_npy(tmp_path / "grid_a.npy", lon))
    assert (d.carries_lat, d.carries_lon) == (False, True)
    assert d.method == "값 범위(물리적 불가)"
    # 쌍 정합으로 내려가지 않았다 — 〈65〉 가 막으려던 바로 그 자리다
    assert "쌍 정합" not in " ".join(d.evidence)


def test_min_under_minus_90_is_longitude_alone(tmp_path):
    lon = np.repeat(np.linspace(-130.0, -100.0, 8)[None, :], 8, axis=0)
    d = detect_axes(_npy(tmp_path / "grid_b.npy", lon))
    assert (d.carries_lat, d.carries_lon) == (False, True)
    assert d.method == "값 범위(물리적 불가)"


# ── ㉢ [-90,90] 안은 모호하다. 단독으로는 확정하지 않는다 ────────────────────
def test_inside_lat_range_alone_is_undetermined(tmp_path):
    lat, _ = _grid(30, 43, 60, 80)
    with pytest.raises(AxisUndeterminedError):
        detect_axes(_npy(tmp_path / "grid_c.npy", lat))


def test_pair_matching_resolves_the_ambiguous_pair(tmp_path):
    """경도 0~90 함정 — 둘 다 [-90,90] 안이라 값 범위로는 안 갈린다."""
    lat, lon = _grid(30, 43, 60, 80)
    a = _npy(tmp_path / "grid_1.npy", lat)
    b = _npy(tmp_path / "grid_2.npy", lon)
    res = detect_axes_for_upload([a, b])
    assert res.rejected == {}
    assert (res.resolved[a].carries_lat, res.resolved[a].carries_lon) == (True, False)
    assert (res.resolved[b].carries_lat, res.resolved[b].carries_lon) == (False, True)
    assert res.resolved[a].method == "쌍 정합"


def test_pair_matching_needs_exactly_two_same_shape(tmp_path):
    """형상 같은 격자가 4건이면 짝짓기가 미정의다 — 지어내지 않고 거절한다 (R-3 실측)."""
    lat, lon = _grid(30, 43, 60, 80)
    paths = [
        _npy(tmp_path / "g1.npy", lat), _npy(tmp_path / "g2.npy", lon),
        _npy(tmp_path / "g3.npy", lat), _npy(tmp_path / "g4.npy", lon),
    ]
    res = detect_axes_for_upload(paths)
    assert res.resolved == {}
    assert set(res.rejected) == set(paths)


# ── ㉤ 파일명은 단독으로 아무것도 정하지 않는다 ─────────────────────────────
def test_filename_never_decides_alone(tmp_path):
    """이름이 `lat_` 이어도 값이 모호하면 확정되지 않는다."""
    lat, _ = _grid(30, 43, 60, 80)
    with pytest.raises(AxisUndeterminedError):
        detect_axes(_npy(tmp_path / "lat_seoul.npy", lat))
    with pytest.raises(AxisUndeterminedError):
        detect_axes(_npy(tmp_path / "lon_seoul.npy", lat))


def test_values_beat_the_filename_and_the_mismatch_is_recorded(tmp_path):
    """이름은 위도라는데 값이 133 이다 — 값을 따르고 불일치를 기록한다 (측정 §4.2-5)."""
    _, lon = _grid(30, 43, 118.8, 133.5)
    d = detect_axes(_npy(tmp_path / "Lat_HSR_ish.npy", lon))
    assert (d.carries_lat, d.carries_lon) == (False, True)
    assert any("파일명" in w for w in d.warnings)


# ── ㉣ 이방성은 교차검증 전용 ───────────────────────────────────────────────
def test_anisotropy_alone_never_decides(tmp_path):
    """행 방향으로만 변하는 [-90,90] 배열 — 이방성 단독이면 「위도」라 부를 자리다."""
    lat, _ = _grid(30, 43, 60, 80)
    with pytest.raises(AxisUndeterminedError):
        detect_axes(_npy(tmp_path / "aniso.npy", lat))


# ── 〈66〉 출력 모양 = 두 불리언. 한 파일이 둘 다 담을 수 있다 ────────────────
def test_combined_axis_netcdf_carries_both(tmp_path):
    h5py = pytest.importorskip("h5py")
    lat, lon = _grid(30, 43, 118.8, 133.5)
    p = tmp_path / "rdr_500m_latlon_ish.nc"
    with h5py.File(p, "w") as f:
        f.create_dataset("lat", data=lat.astype("f4"))
        f.create_dataset("lon", data=lon.astype("f4"))
    d = detect_axes(p)
    assert (d.carries_lat, d.carries_lon) == (True, True)
    assert d.method == "컨테이너 내부 변수명"


def test_rejected_file_yields_no_row(tmp_path):
    """〈66〉 유권해석 — 판별 실패는 축이 빈 행을 만들지 않는다. 예외이지 빈 값이 아니다."""
    lat, _ = _grid(30, 43, 60, 80)
    p = _npy(tmp_path / "x.npy", lat)
    try:
        detect_axes(p)
    except AxisUndeterminedError as e:
        assert not hasattr(e, "carries_lat")
    else:  # pragma: no cover
        pytest.fail("확정되면 안 되는 파일이 확정됐다")


def test_detection_is_a_pair_of_booleans_not_a_string():
    d = AxisDetection(carries_lat=True, carries_lon=False, method="x", evidence=[], warnings=[])
    assert isinstance(d.carries_lat, bool) and isinstance(d.carries_lon, bool)
    assert not hasattr(d, "grid_axis")
