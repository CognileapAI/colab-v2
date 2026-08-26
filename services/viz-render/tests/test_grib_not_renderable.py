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
from colab_viz.domains.d7_visualization.readers import detect_format


def _grib1(path: Path) -> Path:
    path.write_bytes(b"GRIB" + (200).to_bytes(3, "big") + bytes([1]) + b"\x00" * 120)
    return path


def _grib2(path: Path) -> Path:
    path.write_bytes(b"GRIB" + b"\x00\x00" + bytes([0]) + bytes([2])
                     + (400).to_bytes(8, "big") + b"\x00" * 120)
    return path


def test_grib_is_not_renderable(tmp_path: Path):
    """지원 포맷이지만 그리지 않는다 — 415 로 가는 것 자체는 맞다."""
    with pytest.raises(NotRenderableError):
        detect_format(_grib1(tmp_path / "surface.grib"))


def test_the_reason_names_grib_instead_of_claiming_unknown_magic(tmp_path: Path):
    """**사유가 참이어야 한다.** 우리는 그것이 GRIB 임을 안다."""
    for maker, name in ((_grib1, "a.grib"), (_grib2, "b.grb2")):
        with pytest.raises(NotRenderableError) as caught:
            detect_format(maker(tmp_path / name))
        reason = str(caught.value)
        assert "GRIB" in reason, f"사유가 GRIB 을 지목하지 않는다: {reason}"
        assert "알려진 매직바이트가 없다" not in reason, (
            "지원하는 포맷을 「모르는 파일」로 말하면 사용자는 자기 파일이 깨진 줄 안다.")


def test_grib_makes_retry_pointless_but_a_read_failure_does_not(tmp_path: Path):
    """**재시도가 무의미한 것과 다시 해 볼 만한 것을 가른다** (결정 2-3 · 결정 #8).

    결정 #8 이 「못 그렸어요 ＋ **다시 그리기**」 상태를 만들라고 했으므로, 그 버튼을
    **언제 감출지**가 정해져 있어야 한다. 안 그러면 GRIB 에도 「다시 그리기」가 뜨고
    누르면 영원히 같은 실패가 돌아온다.
    """
    with pytest.raises(NotRenderableError) as caught:
        detect_format(_grib1(tmp_path / "surface.grib"))
    assert is_retry_pointless(caught.value) is True, (
        "이 형식은 원래 안 그려진다 — 다시 그려도 결과가 같다.")

    unknown = tmp_path / "mystery.dat"
    unknown.write_bytes(b"\x00" * 200)
    with pytest.raises(NotRenderableError) as caught_unknown:
        detect_format(unknown)
    assert is_retry_pointless(caught_unknown.value) is True, (
        "매직을 모르는 파일도 다시 그린다고 알려지지 않는다 — 같은 영구 실패다.")


def test_the_four_renderable_formats_are_untouched(tmp_path: Path):
    """갈라진 것은 GRIB 하나뿐이다 — 나머지를 같이 떨어뜨리지 않는다."""
    hdf4 = tmp_path / "x.hdf"
    hdf4.write_bytes(b"\x0e\x03\x13\x01" + b"\x00" * 120)
    assert detect_format(hdf4) == "HDF4"

    tif = tmp_path / "x.tif"
    tif.write_bytes(b"II*\x00" + b"\x00" * 120)
    assert detect_format(tif) == "GeoTIFF"
