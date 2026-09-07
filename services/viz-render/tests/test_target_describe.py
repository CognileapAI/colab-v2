"""`describeTarget` — 대상 기술 조회 (21차 해제 · 첨가 6건 ⑴).

여기서 재는 것 (`R-C-1-contract-db.md §2 WU-C10` 수용 기준 축자)

  ⑴ NetCDF — `variables` 가 **`_pick_default` 와 같은 규칙·같은 순서**다:
     좌표 변수는 빠지고, 2차원 미만도 빠지고, 파일의 변수 순서가 남는다.
     그리고 `default.variable` 은 품질 플래그를 **미룬** 결과다(`DQF_*` ≠ 기본값).
  ⑵ GeoTIFF — `band1`~`bandN`.
  ⑶ 시각 — `count`·`first`·`last` 셋. **목록을 통째로 내리지 않는다.**
     시각 축이 없으면 `instants` 는 **`null`** 이고 빈 배열이 아니다.
  ⑷ **읽기 전용이다** — 렌더 작업이 서지 않고 미리보기 산출물이 생기지 않는다.
  ⑸ 인증·경계는 다른 op 과 같은 자리에서 걸린다.

⚠ 여기서 재지 않는 것 — core-api 중계는 `core-api/tests/test_preview_relay.py`.
"""
from __future__ import annotations

import warnings
from contextlib import contextmanager

import numpy as np
import pytest

from conftest import AUTH

pytest.importorskip("netCDF4")

_PATH = "/viz/v1/target-descriptions"


@contextmanager
def _quiet_netcdf_write():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*[Ss]hape.*")
        yield


@pytest.fixture
def nc_with_flag(tmp_path):
    """**품질 플래그가 값보다 앞에 있는** NetCDF — 실측으로 드러난 자리 그대로다
    (`readers._DEPRIORITIZED_NAME_PARTS` 주석 — GK2A `DQF_LST` 가 `LST` 보다 앞이다).

    순서만 보면 미리보기가 품질 플래그를 그린다. 그래서 `variables` 는 **파일 순서**이고
    `default.variable` 은 **미룬 결과**다 — 둘이 다르다는 사실이 이 픽스처의 요점이다.
    """
    from netCDF4 import Dataset

    path = tmp_path / "flagfirst.nc"
    ds = Dataset(str(path), "w", format="NETCDF4")
    ds.createDimension("time", 3)
    ds.createDimension("lat", 4)
    ds.createDimension("lon", 5)
    t = ds.createVariable("time", "f8", ("time",))
    t.units = "hours since 2026-06-01 00:00:00"
    t.calendar = "standard"
    t[:] = [0.0, 12.0, 24.0]
    la = ds.createVariable("lat", "f8", ("lat",))
    la[:] = np.linspace(38.0, 36.0, 4)
    lo = ds.createVariable("lon", "f8", ("lon",))
    lo[:] = np.linspace(126.0, 128.0, 5)
    # 1차원 값 변수 — **그릴 수 없다.** 목록에 들면 화면이 못 그릴 것을 고르게 된다.
    ds.createVariable("scan_quality", "f4", ("time",))
    with _quiet_netcdf_write():
        for name in ("DQF_LST", "LST"):
            ds.createVariable(name, "f4", ("time", "lat", "lon"))[:] = np.zeros((3, 4, 5), "f4")
    ds.close()
    return path


def _describe(client, target, headers=AUTH):
    return client.post(_PATH, json=target, headers=headers)


# ═══════════ ⑴ NetCDF — drawable 규칙과 같은 순서 ═══════════
def test_netcdf_변수_목록은_drawable_규칙_그대로다(client, put_target, nc_with_flag):
    body = _describe(client, {"datasetId": put_target(copy_from=[nc_with_flag])}).json()
    # 좌표 변수(`time`·`lat`·`lon`)와 1차원 `scan_quality` 가 빠지고 **파일 순서**가 남는다.
    assert body["variables"] == ["DQF_LST", "LST"]


def test_기본_변수는_품질_플래그를_미룬_결과다(client, put_target, nc_with_flag):
    """`_pick_default` 와 **같은 답**이다 — 순서상 첫 값이 아니다."""
    from colab_viz.domains.d7_visualization.readers import _pick_default

    body = _describe(client, {"datasetId": put_target(copy_from=[nc_with_flag])}).json()
    assert body["default"]["variable"] == "LST"
    assert body["default"]["variable"] == _pick_default(body["variables"])


# ═══════════ ⑵ GeoTIFF — band1..N ═══════════
def test_geotiff_는_band1부터_센다(client, put_target, tiny_geotiff):
    body = _describe(client, {"datasetId": put_target(copy_from=[tiny_geotiff])}).json()
    assert body["variables"] == ["band1"]
    assert body["default"]["variable"] == "band1"


# ═══════════ ⑶ 시각 — 건수·처음·마지막 ═══════════
def test_시각은_건수_처음_마지막_셋이다(client, put_target, nc_with_flag):
    body = _describe(client, {"datasetId": put_target(copy_from=[nc_with_flag])}).json()
    assert body["instants"] == {"count": 3,
                                "first": "2026-06-01T00:00:00Z",
                                "last": "2026-06-02T00:00:00Z"}
    # ⚠ 목록을 통째로 싣지 않는다 — 8760시각 파일에서 그것이 화면을 덮는다.
    assert set(body["instants"]) == {"count", "first", "last"}


def test_기본_시각은_첫_시각이다(client, put_target, nc_with_flag):
    """계약 축자 — `instant` 를 생략하면 첫 시각이다."""
    body = _describe(client, {"datasetId": put_target(copy_from=[nc_with_flag])}).json()
    assert body["default"]["instant"] == body["instants"]["first"]


def test_시각_축이_없으면_null_이고_빈_배열이_아니다(client, put_target, tiny_geotiff):
    """「시각이 없는 데이터」와 「시각을 못 셌다」를 같은 값으로 접지 않는다."""
    body = _describe(client, {"datasetId": put_target(copy_from=[tiny_geotiff])}).json()
    assert body["instants"] is None
    assert body["default"]["instant"] is None


# ═══════════ ⑷ 읽기 전용 ═══════════
def test_렌더_작업도_산출물도_만들지_않는다(client, put_target, tiny_geotiff, source_root):
    previews = source_root.parent / "previews"
    before = sorted(p.name for p in previews.rglob("*")) if previews.exists() else []
    r = _describe(client, {"datasetId": put_target(copy_from=[tiny_geotiff])})
    assert r.status_code == 200
    assert "renderId" not in r.json()
    after = sorted(p.name for p in previews.rglob("*")) if previews.exists() else []
    assert after == before


# ═══════════ ⑸ 경계·오류 ═══════════
def test_인증_없이는_401_이다(client, put_target, tiny_geotiff):
    assert _describe(client, {"datasetId": put_target(copy_from=[tiny_geotiff])},
                     headers={}).status_code == 401


def test_없는_대상은_404_다(client):
    assert _describe(client, {"datasetId": "01JQ0000000000000000000000"}).status_code == 404


def test_그릴_수_없는_조각뿐이면_415_다(client, put_target, tmp_path):
    broken = tmp_path / "broken.txt"
    broken.write_bytes(b"not a raster at all")
    r = _describe(client, {"datasetId": put_target(copy_from=[broken])})
    assert r.status_code == 415
    # 안 되는 것만 말하면 무엇을 올려야 하는지 모른 채 떠난다 — `createRender` 와 같은 본문.
    assert r.json()["details"]["renderableFormats"]


def test_대상은_datasetId_uploadId_정확히_하나다(client):
    assert _describe(client, {}).status_code == 400
