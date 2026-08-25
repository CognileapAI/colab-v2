"""완료조건 ② — 이미-COG 판별 3부류 (DATA-REFERENCE §4).

「타일링 있으면 COG」로 판정하면 원천 16건을 우리 산출물로 오인한다(DR-2 계열).
"""
from pathlib import Path

import pytest

from colab_pipeline.d5.tiff_probe import classify_tiff

from fixture_builders import make_cog_tiff, make_stripped_tiff, make_tiled_only_tiff


# `stage2` 대기 모듈을 단언한다 — 배포 단위·완료 정의에서는 빠지고
# 시험은 CI 에서 계속 돈다(`PLAN-SoT §9 〈71〉-㉰`).
pytestmark = pytest.mark.stage2


def test_cog_class(tmp_path: Path):
    p = make_cog_tiff(tmp_path / "cog.tif", n_overviews=4)
    assert classify_tiff(p) == "cog"


def test_tiled_only_is_not_cog(tmp_path: Path):
    # 급소 — 타일은 있으나 오버뷰(IFD 2+)가 없다 (KWRA Input 11 + vegetation 5)
    p = make_tiled_only_tiff(tmp_path / "kwra_input.tif")
    assert classify_tiff(p) == "tiled-only"


def test_stripped(tmp_path: Path):
    p = make_stripped_tiff(tmp_path / "kwra_output.tif")
    assert classify_tiff(p) == "stripped"


def test_multi_ifd_but_stripped_is_not_cog(tmp_path: Path):
    # 오버뷰 판정만으로도 안 된다 — 타일 AND 오버뷰 둘 다여야 COG 다
    import fixture_builders as fb
    e1 = fb._base_entries(64, 64) + [
        (fb._T_STRIP_OFFSETS, 4, 1, 8),
        (fb._T_ROWS_PER_STRIP, 3, 1, 64),
        (fb._T_STRIP_BYTECOUNTS, 4, 1, 4096),
    ]
    e2 = list(e1)
    p = fb._write_tiff(tmp_path / "multi_strip.tif", [e1, e2])
    assert classify_tiff(p) == "stripped"
