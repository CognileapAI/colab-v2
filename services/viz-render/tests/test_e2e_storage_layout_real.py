"""`S3` 완주의 **접합부** — 저장 배치가 실제로 놓는 이름으로도 5종이 그려지는가.

**왜 따로 재는가.** `test_e2e_real.py` 는 본체를 **원래 파일 이름**으로 놓는다
(`HLS.S30….tif` · `gk2a_….nc` …). 그런데 배치 정본은 그렇게 적지 않았다 —
`contracts/storage/layout.json` 의 `keys.본체` 는 **`{uploadsPrefix}/{targetId}/{fileId}`**
이고 `fileId` 는 ULID 다. **확장자가 없다.**

즉 실운영에서 그리는 쪽이 여는 파일에는 이름도 확장자도 남아 있지 않다.
포맷 판정을 확장자에 조금이라도 기대는 자리가 하나라도 있으면, **원래 이름으로 도는
E2E 는 전건 초록인데 실제 업로드는 한 장도 안 그려진다.** 이 레포에 이미 있던 무늬다 —
확장자로 역할을 갈랐다가 실파일 14건을 삼킨 `M-1`, 시험이 자기가 놓은 자리에서 읽어
배치를 아무도 안 본 `#20`. **부분 검증이 통과하면 전체가 통과한 것으로 착각한다**(`M-4`).

그래서 이 파일은 같은 실파일을 **배치 정본이 적은 이름(ULID · 확장자 없음)** 으로 놓고
다시 그린다. 격자는 배치가 이름을 보존하는 자리라(`keys.기준 격자 파일`) 그대로 둔다.

⚠ **포맷 커버리지 표식(`e2e_format`)을 붙이지 않는다** — 커버리지 계수는
`test_e2e_real.py` 다섯 건이 지는 것이고, 여기에 또 붙이면 같은 포맷을 두 번 세게 된다.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from test_e2e_real import _assert_drawn, _fmtdir, _first, _render, _root

from colab_viz.kernel.ids import new_ulid
from colab_viz.kernel import storage_layout

pytestmark = pytest.mark.e2e


def _source_and_grid(fmt: str) -> tuple[Path, list[Path]]:
    """포맷마다 **본체 하나와 격자 파일 목록**. 목록의 근거는 `DATA-REFERENCE §1`·`§1.1`.

    격자를 붙이는 기준은 확장자가 아니라 **그 포맷이 격자를 밖에서 받아야 하는가**다.
    `Binary`(HSR)만 진짜로 필요하고 나머지는 파일 안에서 계산되지만, 원천이 동봉 격자를
    주므로 `test_e2e_real.py` 와 **같은 조건**으로 맞춘다 — 조건이 달라지면 이 시험이
    보는 것이 「배치 이름」이 아니라 「격자 유무」가 된다.
    """
    if fmt == "GeoTIFF":
        d = _fmtdir("file_format_4_tif")
        return _first("HLS.S30.*.tif", d / "00.Data"), []
    if fmt == "NetCDF":
        d = _fmtdir("file_format_2_nc")
        return (_first("gk2a_*.nc", d / "00.Data"),
                [d / "04.Lat_Lon_info" / a for a in ("lat2d.npy", "lon2d.npy")])
    if fmt == "Binary":
        d = _fmtdir("file_format_3_bin")
        return (_first("RDR_CMP_HSR_*.bin.gz", d / "00.Data"),
                [d / "04.Lat_Lon_info" / "rdr_500m_latlon.nc"])
    if fmt == "HDF4":
        # 폴더명이 거짓말한다 — 실체는 HDF4 (`DR-3`·`M-1`)
        d = _fmtdir("file_format_5_HDF5")
        return (_first("*h27v05*.hdf", d / "00.Data"),
                [d / "04.Lat_Lon_info" / a
                 for a in ("lat2d_h27v05.npy", "lon2d_h27v05.npy")])
    if fmt == "NumPy":
        veg = _root() / "01.level-data" / "02.vegetation" / "02.vegetation"
        if not veg.is_dir():
            pytest.fail(f"원천 폴더 없음: {veg}")
        return (_first("Prediction_*.npy", veg / "Lv.2"),
                [veg / "#metadata" / a for a in ("LAT_crop.npy", "LON_crop.npy")])
    pytest.fail(f"자리 미작성 포맷: {fmt} — 목록이 늘었으면 여기도 늘린다")


@pytest.mark.parametrize(
    "fmt", ["GeoTIFF", "NetCDF", "Binary", "HDF4", "NumPy"])
def test_배치_정본이_적은_이름으로_놓아도_그려진다(source_root, client, fmt) -> None:
    """본체를 **ULID 한 개**로 놓는다 — 확장자도 원래 이름도 없다(`layout.json keys.본체`)."""
    src, grids = _source_and_grid(fmt)

    tid = new_ulid()
    d = storage_layout.target_dir(source_root, tid)
    d.mkdir(parents=True)
    file_id = new_ulid()
    assert "." not in file_id, "본체 키는 ULID 하나다 — 확장자가 붙으면 이 시험이 무의미하다"
    (d / file_id).write_bytes(src.read_bytes())

    if grids:
        g = storage_layout.grid_dir(source_root, tid)
        g.mkdir(parents=True, exist_ok=True)
        for path in grids:
            shutil.copy(path, g / path.name)      # 격자만 이름을 보존한다

    job = _render(client, tid)
    _assert_drawn(client, job, f"{fmt}(배치 이름)")
