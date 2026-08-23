"""완료 판정 — 지원 4종 각각 최소 1건이 **실제로 그려진다.**

`GeoTIFF 를 가장 먼저 돌린다` (`P2-EXEC §4 W2·P2-viz` 완료 판정 · `P2.md §6-2 양성 ④`) —
PoC 선례가 가장 얇은 경로라 여기서 나올 실패가 예측 목록에 없다.

원천 위치는 환경변수 `COLAB_REFERENCE_DATA` 로 받는다 (문서 절대경로 금지와 같은 이유).
미지정·미마운트면 **skip 이 아니라 fail** — green-by-skip 을 금지한다 (`CLAUDE.md §4`).
마운트 없이 단위 시험만 돌릴 때는 `-m "not e2e"` 로 명시적으로 뺀다.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import numpy as np
import pytest

from conftest import AUTH

pytestmark = pytest.mark.e2e

_ENV = "COLAB_REFERENCE_DATA"
_STYLE = {"palette": "단색-파랑"}


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


def _render(client, tid: str, **kw) -> dict:
    body = {"target": {"uploadId": tid}, "style": _STYLE}
    body.update(kw)
    r = client.post("/viz/v1/renders", json=body, headers=AUTH)
    assert r.status_code == 202, r.text
    rid = r.json()["renderId"]
    job = client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()
    job["_renderId"] = rid
    return job


def _value_range(job: dict) -> tuple[float, float]:
    """범례가 말하는 값의 하한·상한. **자릿수를 보는 유일한 창**이다."""
    classes = job["result"]["legend"]["classes"]
    return classes[0]["min"], classes[-1]["max"]


def _assert_drawn(client, job: dict, fmt: str) -> int:
    """「그려졌다」의 판정 — 200 + PNG 매직만으로는 **투명 타일도 통과한다.**

    그래서 경계 중심을 덮는 타일을 골라 **불투명 픽셀이 실제로 있는지**까지 본다.
    (`M-4` 의 무늬 — 부분 검증이 통과하면 전체가 통과한 것으로 착각한다.)
    """
    import math
    from PIL import Image

    assert job["status"] == "완료", f"{fmt} 실패: {job.get('failure')}"
    res = job["result"]
    b = res["bounds"]
    assert -180 <= b["west"] < b["east"] <= 180
    assert -90 <= b["south"] < b["north"] <= 90
    assert 3 <= len(res["legend"]["classes"]) <= 9

    lat = (b["south"] + b["north"]) / 2
    lon = (b["west"] + b["east"]) / 2
    z = 6
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    tile = client.get(f"/viz/v1/renders/{job['_renderId']}/tiles/{z}/{x}/{y}.png",
                      headers=AUTH)
    assert tile.status_code == 200 and tile.content[:8] == b"\x89PNG\r\n\x1a\n"
    alpha = np.asarray(Image.open(__import__("io").BytesIO(tile.content)).convert("RGBA"))[..., 3]
    opaque = int((alpha > 0).sum())
    assert opaque > 0, f"{fmt}: 타일 z{z}/{x}/{y} 가 통째로 투명하다 — 그려진 것이 아니다"
    return opaque


# ── ① GeoTIFF 를 가장 먼저 돌린다 ────────────────────────────────────────────
def test_e2e_1_geotiff(client, put_target):
    d = _fmtdir("file_format_4_tif")
    src = _first("HLS.S30.*.tif", d / "00.Data")
    tid = put_target(copy_from=[src])
    job = _render(client, tid)
    _assert_drawn(client, job, "GeoTIFF")


def test_e2e_2_netcdf(client, put_target, source_root):
    d = _fmtdir("file_format_2_nc")
    src = _first("gk2a_*.nc", d / "00.Data")
    tid = put_target(copy_from=[src])
    g = source_root / tid / "grid"
    g.mkdir(parents=True, exist_ok=True)
    for axis in ("lat2d.npy", "lon2d.npy"):
        shutil.copy(d / "04.Lat_Lon_info" / axis, g / axis)
    job = _render(client, tid)
    _assert_drawn(client, job, "NetCDF")


def test_e2e_3_binary_hsr(client, put_target, source_root):
    d = _fmtdir("file_format_3_bin")
    src = _first("RDR_CMP_HSR_*.bin.gz", d / "00.Data")
    tid = put_target(copy_from=[src])
    g = source_root / tid / "grid"
    g.mkdir(parents=True, exist_ok=True)
    # 〈66〉 — HSR 정본 격자는 `rdr_500m_latlon.nc`(한 파일에 lat·lon 둘 다)다.
    shutil.copy(d / "04.Lat_Lon_info" / "rdr_500m_latlon.nc", g / "rdr_500m_latlon.nc")
    job = _render(client, tid)
    _assert_drawn(client, job, "Binary")

    # ── 값 범위 — 불투명 픽셀 세기로는 **100배 틀린 값**을 못 잡는다 (`§7-ⓒ` 의 무늬).
    # 반사도는 `값/100` 이다(`DATA-REFERENCE §2`·`§2.2`). 스케일을 빠뜨리면 상한이
    # 58.09 가 아니라 5,809 로 뛴다 — 그래도 픽셀은 멀쩡히 그려진다.
    lo, hi = _value_range(job)
    assert hi <= 100, ("dBZ 상한이 물리 범위를 넘는다 — 스케일(/100)이 빠졌을 수 있다", lo, hi)
    # ⚠ **하한은 단언하지 않는다.** 이 실파일의 하한은 −296.87 dBZ 이고, 그 원인인
    # 미문서화 음수 코드값 2,073종은 `§7-ⓑ` 로 상신된 열린 질문이다. 여기서 하한을
    # 박으면 레인이 값 집합의 정의를 관례로 정하는 것이 된다(`㊴-②`).

    # ── 남단 경계 — `〈66〉` 이 고른 정본 격자(`.nc`)를 실제로 쓰고 있는가.
    # `.npy` 판은 `30.102751` 이라 두 격자가 여기서 갈린다 (`DATA-REFERENCE §1`).
    assert job["result"]["bounds"]["south"] == pytest.approx(30.107119, abs=1e-6), \
        "남단이 정본 격자(.nc)의 lat min 과 다르다 — .npy 판을 읽고 있을 수 있다"


def test_e2e_4_hdf4(client, put_target, source_root):
    d = _fmtdir("file_format_5_HDF5")      # 폴더명이 거짓말 — 실체는 HDF4 (`DR-3`·`M-1`)
    src = _first("*h27v05*.hdf", d / "00.Data")
    tid = put_target(copy_from=[src])
    g = source_root / tid / "grid"
    g.mkdir(parents=True, exist_ok=True)
    # h27v05 타일 격자만 붙인다 — 다른 타일 격자를 붙이면 그것이 오배정이다
    for axis in ("lat2d_h27v05.npy", "lon2d_h27v05.npy"):
        shutil.copy(d / "04.Lat_Lon_info" / axis, g / axis)
    job = _render(client, tid)
    _assert_drawn(client, job, "HDF4")

    # ── 값 범위 — FPAR 는 흡수 **비율**이라 0~1 이다
    # (`DATA-REFERENCE §6` cmap 정본 `Fpar_500m` vmin 0 / vmax 1 · 실측도 0.0~1.0).
    # 스케일 인자(0.01)를 빠뜨리면 0~100 이 되고, **픽셀은 그대로 그려진다.**
    lo, hi = _value_range(job)
    assert 0 <= lo <= hi <= 1, ("Fpar 가 0~1 밖이다 — 스케일 인자를 놓쳤을 수 있다", lo, hi)


def test_e2e_5_HSR_격자_없으면_실패다(client, put_target):
    """음성 — 같은 실파일에서 격자만 빼면 「완료」가 아니라 실패다 (`DR-9`)."""
    from colab_viz.domains.d7_visualization.failures import RenderFailure

    d = _fmtdir("file_format_3_bin")
    src = _first("RDR_CMP_HSR_*.bin.gz", d / "00.Data")
    tid = put_target(copy_from=[src])
    job = _render(client, tid)
    assert job["status"] == "실패"
    assert job["failure"]["code"] == RenderFailure.NO_REFERENCE_GRID


def test_e2e_6_변수를_생략하면_viz_render_가_고른다(client, put_target, source_root):
    """core 가 파일의 변수 목록을 해석해 고르지 않는다 (계약 `RenderRequest.variable`)."""
    d = _fmtdir("file_format_2_nc")
    src = _first("gk2a_*.nc", d / "00.Data")
    tid = put_target(copy_from=[src])
    g = source_root / tid / "grid"
    g.mkdir(parents=True, exist_ok=True)
    for axis in ("lat2d.npy", "lon2d.npy"):
        shutil.copy(d / "04.Lat_Lon_info" / axis, g / axis)
    job = _render(client, tid)                    # variable 없음
    assert job["status"] == "완료", job.get("failure")
    legend = job["result"]["legend"]
    assert legend["variable"]                     # 무엇을 그렸는지는 밝힌다
    # 품질 플래그(`DQF_LST`)가 아니라 값(`LST`)을 고른다 — 플래그는 값에 대한 메타데이터다
    assert legend["variable"] == "LST"
    # ⚠ 회귀 — netCDF4 자동 스케일 위에 스케일을 또 걸면 **에러 없이** 276 K 가 2.76 이 된다.
    # 자릿수를 단언한다: 지표면 온도가 켈빈이면 200~400 사이다.
    assert legend["unit"] == "K"
    lo, hi = legend["classes"][0]["min"], legend["classes"][-1]["max"]
    assert 200 < lo < hi < 400, (lo, hi)
