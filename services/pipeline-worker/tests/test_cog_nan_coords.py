"""COG 재배치는 **좌표의 결측·퇴화를 값으로 판정한다** (코드리뷰 20260903 #13).

D5 `cog.py` 와 D7 `raster.py` 는 같은 최근접 재배치를 두 벌로 적은 쌍둥이인데 두 곳이
갈라져 있었다 —

  · **결측 좌표** — D5 는 `valid = np.isfinite(d)` 로 **값만** 봤다. 좌표 셀이 NaN 이면
    `np.rint(nan)` → `np.clip` → `.astype("i8")` 가 `INT64_MIN` 을 내고 그 인덱스가
    `out[rows[valid], cols[valid]]` 에서 `IndexError` 로 터진다. 사용자에게는
    「COG 변환 실패」한 줄만 남는다. D7 은 `isfinite(la) & isfinite(lo)` 로 함께 걸렀다.
  · **퇴화 범위** — D5 는 `lat_min == lat_max` 만 봤다. 경도가 한 값뿐인 격자
    (`lon_min == lon_max`)는 `lon_step = 0` → 0 나눗셈으로 전부 NaN 인덱스가 된다.
    D7 은 네 값을 다 본다.

**두 알고리즘의 통일은 이 회차 밖이다**(작업항목 초안 #9 — 등록 수용 기준이 바뀐다).
여기서 맞추는 것은 **거절 기준**뿐이다.
"""
from __future__ import annotations

import numpy as np
import pytest

from colab_pipeline.d5.cog import CogConversionError, regrid_curvilinear_nearest

pytestmark = pytest.mark.stage2

_N = 6


def _grid():
    lat = np.repeat(np.linspace(33.0, 39.0, _N)[:, None], _N, axis=1)
    lon = np.repeat(np.linspace(124.0, 132.0, _N)[None, :], _N, axis=0)
    data = np.arange(_N * _N, dtype="f4").reshape(_N, _N)
    return data, lat, lon


def test_좌표_셀이_NaN_이어도_터지지_않는다():
    data, lat, lon = _grid()
    lat[2, 3] = np.nan
    out, bounds = regrid_curvilinear_nearest(data, lat, lon)
    assert out.shape == (_N, _N)
    assert np.isfinite(bounds).all()


def test_좌표가_NaN_인_셀의_값은_버린다():
    """좌표를 모르는 값을 아무 자리에나 놓지 않는다 — 지어내지 않는 것과 같은 규칙이다."""
    data, lat, lon = _grid()
    data[:] = 0.0
    data[2, 3] = 777.0
    lon[2, 3] = np.nan
    out, _ = regrid_curvilinear_nearest(data, lat, lon)
    assert 777.0 not in set(out[np.isfinite(out)].tolist()), (
        "좌표가 결측인 값이 엉뚱한 화소에 찍혔다")


def test_경도_범위가_퇴화하면_거절한다():
    data, lat, lon = _grid()
    lon[:] = 127.0                      # 경도가 한 값뿐 — 재배치가 정의되지 않는다
    with pytest.raises(CogConversionError):
        regrid_curvilinear_nearest(data, lat, lon)


def test_위도_범위가_퇴화하면_거절한다():
    data, lat, lon = _grid()
    lat[:] = 36.0
    with pytest.raises(CogConversionError):
        regrid_curvilinear_nearest(data, lat, lon)


def test_좌표가_전부_결측이면_거절한다():
    data, lat, lon = _grid()
    lat[:] = np.nan
    with pytest.raises(CogConversionError):
        regrid_curvilinear_nearest(data, lat, lon)
