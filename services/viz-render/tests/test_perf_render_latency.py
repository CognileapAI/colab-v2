"""미리보기 최초 표시 — **합격선 집행부** (`PLAN-SoT §9 〈233〉` · 정본 `Policy_데이터셋_상세` v2.6 §8).

재는 것 = **렌더 작업 하나가 3층 산출물까지 끝나는 벽시계 시간**이다.
`test_e2e_real.py` 와 **같은 원천 파일·같은 배선**을 쓰고, 포맷마다 여러 번 돌려 표본을 만든다.

⚠ **이 시험이 재지 않는 것을 적어 둔다** — ⓐ core-api 중계의 왕복 ⓑ 화면의 조회 주기
(`usePreviewRender` 의 `pollMs` 기본 1,000 ms) ⓒ 그림 내려받기 ⓓ 브라우저 그리기.
합격선이 렌더 시간보다 넉넉한 이유가 이 넷이다. **재지 않은 것을 잰 것처럼 적지 않는다**
(`DATA-REFERENCE §0`).

판정은 여기서 하지 않는다 — 초를 junit 속성 `렌더초` 로 내보내고 **게이트
`render-latency` 가 판정한다.** 기준값이 두 곳에 있으면 갈라지기 때문이다
(정본 = `gates/config/render-latency.toml`).

원천 마운트(`COLAB_REFERENCE_DATA`)가 없으면 **skip 이 아니라 fail** 이다 (`CLAUDE.md §4`).
"""
from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import pytest

from colab_viz.kernel import storage_layout
from conftest import AUTH

pytestmark = pytest.mark.perf

_ENV = "COLAB_REFERENCE_DATA"
_STYLE = {"palette": "단색-파랑"}

#: 포맷 하나를 몇 번 도는가. 표본 수가 곧 p95 의 분해능이다 —
#: 포맷 5 × 반복 5 = 25 표본이면 p95 는 위에서 둘째 값이다.
REPEAT = int(os.environ.get("COLAB_RENDER_LATENCY_REPEAT", "5"))


def _root() -> Path:
    v = os.environ.get(_ENV)
    if not v or not Path(v).is_dir():
        pytest.fail(f"{_ENV} 가 원천 디렉터리를 가리키지 않는다 — 성능 시험은 skip 하지 않는다")
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


def _veg() -> Path:
    d = _root() / "01.level-data" / "02.vegetation" / "02.vegetation"
    if not d.is_dir():
        pytest.fail(f"원천 폴더 없음: {d}")
    return d


def _case(fmt: str):
    """(본체 파일, 동봉 격자 파일 목록) — `test_e2e_real.py` 의 짝과 같은 것을 쓴다."""
    if fmt == "GeoTIFF":
        return _first("HLS.S30.*.tif", _fmtdir("file_format_4_tif") / "00.Data"), []
    if fmt == "NetCDF":
        d = _fmtdir("file_format_2_nc")
        return (_first("gk2a_*.nc", d / "00.Data"),
                [d / "04.Lat_Lon_info" / "lat2d.npy", d / "04.Lat_Lon_info" / "lon2d.npy"])
    if fmt == "Binary":
        d = _fmtdir("file_format_3_bin")
        return (_first("RDR_CMP_HSR_*.bin.gz", d / "00.Data"),
                [d / "04.Lat_Lon_info" / "rdr_500m_latlon.nc"])
    if fmt == "HDF4":
        d = _fmtdir("file_format_5_HDF5")   # 폴더명이 거짓말 — 실체는 HDF4 (`DR-3`)
        return (_first("*h27v05*.hdf", d / "00.Data"),
                [d / "04.Lat_Lon_info" / "lat2d_h27v05.npy",
                 d / "04.Lat_Lon_info" / "lon2d_h27v05.npy"])
    if fmt == "NumPy":
        veg = _veg()
        return (_first("Prediction_*.npy", veg / "Lv.2"),
                [veg / "#metadata" / "LAT_crop.npy", veg / "#metadata" / "LON_crop.npy"])
    raise AssertionError(f"짝이 없는 포맷: {fmt}")


FORMATS = ["GeoTIFF", "NetCDF", "Binary", "HDF4", "NumPy"]


@pytest.mark.parametrize("fmt", FORMATS)
@pytest.mark.parametrize("회차", list(range(REPEAT)))
def test_미리보기_최초_표시_시간을_잰다(fmt, 회차, source_root, client, put_target,
                                       record_property):
    src, grids = _case(fmt)
    tid = put_target(copy_from=[src])
    if grids:
        g = storage_layout.grid_dir(source_root, tid)
        g.mkdir(parents=True, exist_ok=True)
        for gp in grids:
            shutil.copy(gp, g / gp.name)

    t0 = time.perf_counter()
    r = client.post("/viz/v1/renders",
                    json={"target": {"uploadId": tid}, "style": _STYLE},
                    headers=AUTH)
    assert r.status_code == 202, r.text
    rid = r.json()["renderId"]
    job = client.get(f"/viz/v1/renders/{rid}",
                     headers=AUTH).json()
    초 = time.perf_counter() - t0

    # **그리지 못한 것을 빠르다고 세지 않는다.** 실패는 시간이 짧다.
    assert job["status"] == "완료", f"{fmt} 실패: {job.get('failure')}"
    assert job["result"]["imageUrl"]

    record_property("렌더포맷", fmt)
    record_property("렌더초", f"{초:.4f}")
    record_property("렌더바이트", str(src.stat().st_size))
