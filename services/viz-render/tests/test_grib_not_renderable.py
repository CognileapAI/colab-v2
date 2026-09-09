"""GRIB — **그리지 않는 것과 못 그리는 것은 다르다** (`C-5` · `〈135〉`).

결정 2-3 이 요구한 분리다 — 「미리보기 불가 상태 2종 분리: **못 그렸어요(재시도
가능)** vs **이 형식은 원래 안 그려져요(재시도 무의미)**」.

`〈134〉` 로 GRIB 이 지원 포맷이 됐다. 그런데 이 단위의 `detect_format` 은 GRIB 매직을
모르므로 **「알려진 매직바이트가 없다」로 떨어진다.** 분류(415·영구)는 맞지만
**사유가 거짓이다** — 우리는 그것이 GRIB 임을 안다. 정상적으로 지원하는 파일을
올렸는데 화면이 「매직바이트를 모르겠다」고 말하면 **사용자는 자기 파일이 깨진 줄 안다.**

⚠ **그릴 수 없는 것과 등록할 수 없는 것은 다르다** — 415 는 등록·다운로드·계보 확정을
막지 않는다(정본 §9 · 결정 #4 「저장은 받고 미리보기만 실패」).
"""
from pathlib import Path

import pytest

from colab_viz.domains.d7_visualization.failures import (
    NotRenderableError,
    is_retry_pointless,
)
from colab_viz.domains.d7_visualization.readers import SUPPORTED_FORMATS, detect_format


def _grib1(path: Path) -> Path:
    path.write_bytes(b"GRIB" + (200).to_bytes(3, "big") + bytes([1]) + b"\x00" * 120)
    return path


def _grib2(path: Path) -> Path:
    path.write_bytes(b"GRIB" + b"\x00\x00" + bytes([0]) + bytes([2])
                     + (400).to_bytes(8, "big") + b"\x00" * 120)
    return path


def test_grib_is_renderable_format(tmp_path: Path):
    assert detect_format(_grib1(tmp_path / "surface.grib")) == "GRIB"
    assert "GRIB" in SUPPORTED_FORMATS


def test_the_four_renderable_formats_are_untouched(tmp_path: Path):
    """갈라진 것은 GRIB 하나뿐이다 — 나머지를 같이 떨어뜨리지 않는다."""
    hdf4 = tmp_path / "x.hdf"
    hdf4.write_bytes(b"\x0e\x03\x13\x01" + b"\x00" * 120)
    assert detect_format(hdf4) == "HDF4"

    tif = tmp_path / "x.tif"
    tif.write_bytes(b"II*\x00" + b"\x00" * 120)
    assert detect_format(tif) == "GeoTIFF"
