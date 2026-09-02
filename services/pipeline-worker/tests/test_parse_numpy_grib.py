"""`#58` — **선언은 하는데 못 파싱하던 두 포맷**을 판다 (`PLAN-SoT §9 〈271〉-㉯`).

판정은 **줄이는 쪽(선언 6→4)이 아니라 채우는 쪽(처리 4→6)**이었다.

⚠ **두 포맷의 목표가 다르다.**
  · `NumPy` 는 **그릴 수 있는** 포맷이다 — 격자를 세워 COG 까지 간다.
  · `GRIB` 은 **지원하되 그릴 수 없다**(`〈134〉` 결정 2-3). 0절(section 0)만 읽고,
    변수·격자는 **디코더 없이 지어내지 않는다**(`DR-9`). 그리고 COG 를 만들지 않는 것이
    실패가 아니다 — 「그릴 수 없는 것과 등록할 수 없는 것은 다르다」.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from colab_pipeline.d5.detect import detect_format
from colab_pipeline.d5.formats import UNKNOWN
from colab_pipeline.d5.parse import parse_metadata
from colab_pipeline.d5.pipeline import run_file

pytestmark = pytest.mark.stage2


def _npy(path: Path, shape=(12, 20)) -> Path:
    np.save(path, np.arange(np.prod(shape), dtype="f4").reshape(shape))
    return path.with_suffix(".npy") if path.suffix != ".npy" else path


def _grib2(path: Path) -> Path:
    body = (b"GRIB" + b"\x00\x00" + bytes([0]) + bytes([2])
            + (136).to_bytes(8, "big") + b"\x00" * 120)
    path.write_bytes(body)
    return path


# ═════ NumPy ═════
def test_numpy_parses_instead_of_raising(tmp_path: Path):
    """**`#58` 의 before/after 그 자체** — 종전에는 `지원 목록 밖: NumPy` 였다."""
    p = _npy(tmp_path / "field")
    meta = parse_metadata(p, detect_format(p))
    assert meta.format == "NumPy"
    assert meta.grid == (12, 20)
    assert meta.size_bytes == p.stat().st_size


def test_numpy_says_it_has_no_coordinates(tmp_path: Path):
    """`.npy` 는 배열만 있고 메타가 없다 — 좌표를 지어내지 않는다(`〈77〉`·`DR-9`)."""
    p = _npy(tmp_path / "field")
    meta = parse_metadata(p, detect_format(p))
    assert meta.crs_embedded is False
    assert meta.crs == UNKNOWN


def test_numpy_higher_rank_reports_the_trailing_two_axes(tmp_path: Path):
    p = _npy(tmp_path / "cube", shape=(3, 12, 20))
    meta = parse_metadata(p, detect_format(p))
    assert meta.grid == (12, 20)


def test_numpy_one_dimensional_has_no_grid(tmp_path: Path):
    """**음성** — 2차원이 아니면 격자를 만들어 내지 않는다."""
    p = _npy(tmp_path / "line", shape=(7,))
    meta = parse_metadata(p, detect_format(p))
    assert meta.grid == UNKNOWN


def test_numpy_object_array_is_refused(tmp_path: Path):
    """**음성** — pickle 을 여는 `.npy` 는 받지 않는다(`allow_pickle` 을 켜지 않는다)."""
    p = tmp_path / "obj.npy"
    np.save(p, np.array([{"a": 1}], dtype=object), allow_pickle=True)
    from colab_pipeline.d5.parse import ParseError
    with pytest.raises(ParseError):
        parse_metadata(p, detect_format(p))


# ═════ GRIB ═════
def test_grib_parses_section0_only(tmp_path: Path):
    p = _grib2(tmp_path / "s.grib")
    meta = parse_metadata(p, detect_format(p))
    assert meta.format == "GRIB"
    assert meta.grid == UNKNOWN, "디코더 없이 격자를 지어내지 않는다"
    assert meta.variables == [], "변수 이름을 지어내지 않는다"
    assert any("판 2" in n for n in meta.notes), meta.notes


def test_grib_pipeline_succeeds_without_a_cog(tmp_path: Path):
    """**그릴 수 없는 것과 등록할 수 없는 것은 다르다** (정본 §9 · 결정 #4)."""
    p = _grib2(tmp_path / "s.grib")
    res = run_file(p, workdir=tmp_path / "wd")
    assert res.status == "SUCCESS", res.failures
    assert res.cog_path is None
    assert res.artifact is None
    assert any("미리보기 대상이 아니다" in n for n in res.notes), res.notes


def test_grib_pipeline_does_not_demand_a_reference_grid(tmp_path: Path):
    """**음성** — 기준 격자가 없다는 이유로 GRIB 이 실패하면 안 된다.

    그리지 않을 것에 격자를 요구하면 「받아서 저장한다」가 거짓이 된다.
    """
    res = run_file(_grib2(tmp_path / "s.grib"), workdir=tmp_path / "wd", grid_dir=None)
    assert res.status == "SUCCESS", res.failures
