"""GRIB — **지원하되 그릴 수 없는 첫 포맷.**

정본이 `〈51〉`(GRIB 제외, 4종)을 뒤집었다 — `POLICY-20260825-001` 의 5종
(`nc · grib · tif · HDF · bin`)이 정본이고, 결정 2-3 이 「개발 정본 `〈51〉` 의 GRIB
제외 결정을 뒤집는다」고 명시했다. Ted 판정 = ㈎(수급한다) · 2026-08-26.

**그런데 5종이 아니라 6종이다.** 정본 목록에는 `NumPy` 가 없고 개발 판정 `〈77〉` 이
그것을 **독립 포맷**으로 이미 들여놨다(Ted — 「nc 랑은 다른 파일이다」). 두 목록은
**수가 같고 구성이 다르다.** 합집합으로 적는다 — **숫자가 아니라 목록이다.**

**그리고 GRIB 은 미리보기 대상이 아니다.** 결정 2-3 이 스스로 적었다 — 「5종이어도
grib 은 미리보기 대상이 아니다(미리보기는 bin·nc·tif·HDF)」. 그래서 이 포맷이
`SUPPORTED_FORMATS` 와 `RENDERABLE_FORMATS` 를 **처음으로 가른다.**
`renderable.py` 의 주석이 예고한 그 자리다 — 「갈라지는 날이 오면 여기 한 줄이 갈라진다」.

⚠ **그릴 수 없는 것과 등록할 수 없는 것은 다르다.** `renderable=false` 는 등록·
다운로드·계보 확정을 막지 않는다(정본 §9 · 결정 #4 「저장은 받고 미리보기만 실패」).
"""
from pathlib import Path

from colab_pipeline.d5.detect import detect_format
from colab_pipeline.d5.formats import SUPPORTED_FORMATS
from colab_pipeline.d5.renderable import RENDERABLE_FORMATS, is_renderable


def _grib1(path: Path) -> Path:
    """GRIB1 — `GRIB` ＋ 전체 길이 3B ＋ **판 1B = 1**(offset 7)."""
    body = b"GRIB" + (200).to_bytes(3, "big") + bytes([1]) + b"\x00" * 120
    path.write_bytes(body)
    return path


def _grib2(path: Path) -> Path:
    """GRIB2 — `GRIB` ＋ 예약 2B ＋ 분야 1B ＋ **판 1B = 2**(offset 7) ＋ 길이 8B."""
    body = (b"GRIB" + b"\x00\x00" + bytes([0]) + bytes([2])
            + (400).to_bytes(8, "big") + b"\x00" * 120)
    path.write_bytes(body)
    return path


# ═════════════════ ① 목록 — 숫자가 아니라 목록이다 ═════════════════
def test_supported_formats_is_the_union_of_both_canons():
    """정본 5종(grib 포함·npy 없음) ＋ 개발 `〈77〉`(npy) = **6종.**

    수를 적으면 또 틀린다 — 정본과 `〈77〉` 이 **둘 다 5종인데 구성이 달랐다.**
    """
    assert SUPPORTED_FORMATS == [
        "NetCDF", "Binary", "HDF4", "GeoTIFF", "NumPy", "GRIB"]


def test_grib_is_supported_but_not_renderable():
    """**두 목록이 여기서 처음 갈라진다.**"""
    assert "GRIB" in SUPPORTED_FORMATS, "정본이 grib 을 지원 포맷으로 되돌렸다."
    assert "GRIB" not in RENDERABLE_FORMATS, (
        "결정 2-3 — 「5종이어도 grib 은 미리보기 대상이 아니다」.")
    assert is_renderable("GRIB") is False
    assert RENDERABLE_FORMATS != SUPPORTED_FORMATS, (
        "지원 목록과 렌더 목록이 더는 같지 않다 — 파생 한 줄이 갈라진 것이다.")


def test_the_other_four_are_still_renderable():
    """갈라진 것은 grib 하나뿐이다 — 나머지를 같이 떨어뜨리지 않는다."""
    for fmt in ("NetCDF", "Binary", "HDF4", "GeoTIFF"):
        assert is_renderable(fmt) is True, f"{fmt} 은 미리보기 대상이다."


# ═════════════════ ② 감지 — 매직바이트가 정본, 확장자는 힌트 ═════════════════
def test_grib1_is_detected_by_magic(tmp_path: Path):
    r = detect_format(_grib1(tmp_path / "sample.grib"))
    assert r.format == "GRIB", r.reason


def test_grib2_is_detected_by_magic(tmp_path: Path):
    r = detect_format(_grib2(tmp_path / "sample.grb2"))
    assert r.format == "GRIB", r.reason


def test_grib_is_detected_without_any_extension(tmp_path: Path):
    """저장 키에는 확장자가 없다 — 매직으로만 감지돼야 한다(`〈77〉-⑵` 와 같은 이유)."""
    r = detect_format(_grib2(tmp_path / "01ARZ3NDEKTSV4RRFFQ69G5FAV"))
    assert r.format == "GRIB", r.reason


def test_grib_extension_on_a_non_grib_file_does_not_make_it_grib(tmp_path: Path):
    """**음성** — 확장자는 힌트일 뿐이다(DR-3). 세 번 다 확장자가 거짓말을 했다."""
    liar = tmp_path / "liar.grib"
    liar.write_bytes(b"\x89HDF\r\n\x1a\n" + b"\x00" * 120)
    r = detect_format(liar)
    assert r.format != "GRIB"


def test_a_file_that_merely_starts_with_the_word_grib_is_not_grib(tmp_path: Path):
    """**음성** — 매직만 보고 판을 안 보면 산문이 GRIB 으로 감지된다.

    판 바이트(offset 7)가 1 또는 2 여야 한다. 지어내지 않는다 — 못 읽으면 실패다.
    """
    prose = tmp_path / "notes.txt"
    prose.write_bytes(b"GRIB is a format used in meteorology." + b" " * 120)
    r = detect_format(prose)
    assert r.format != "GRIB", r.reason
