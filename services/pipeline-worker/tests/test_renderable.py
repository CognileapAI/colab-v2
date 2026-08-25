"""`renderable` 판정 — `FormatDetectedPayload`·`UploadReadyPayload` 가 required 로 요구한다.

계약은 **목록을 박지 않는다**(`NB-3` — 정본 §11 이 미리보기 지원 범위를 미결로 남겼다).
그래서 목록은 이 레포(pipeline-worker) 안에 있고, 계약에는 boolean 만 나간다.
"""
from __future__ import annotations

import pytest

from colab_pipeline.d5.formats import SUPPORTED_FORMATS
from colab_pipeline.d5.renderable import RENDERABLE_FORMATS, is_renderable


# `stage2` 대기 모듈을 단언한다 — 배포 단위·완료 정의에서는 빠지고
# 시험은 CI 에서 계속 돈다(`PLAN-SoT §9 〈71〉-㉰`).
pytestmark = pytest.mark.stage2


def test_supported_four_are_renderable():
    for fmt in ("NetCDF", "Binary", "HDF4", "GeoTIFF"):
        assert is_renderable(fmt) is True, fmt


def test_detection_failure_is_not_renderable():
    # 계약: "감지 실패면 format 은 null 이고 그때 renderable 은 false 다"
    assert is_renderable(None) is False


def test_unsupported_formats_are_not_renderable():
    # 〈51〉 로 범위 밖이 된 GRIB · 지원 목록 밖인 순수 HDF5
    assert is_renderable("GRIB") is False
    assert is_renderable("HDF5") is False
    assert is_renderable("무엇인지 모를 것") is False


def test_renderable_list_is_not_a_number_and_lives_here():
    # 숫자가 아니라 목록이다 (〈51〉). 그리고 지원 목록과 한 자리에서 파생된다 —
    # 두 곳에 적으면 갈라진다.
    assert RENDERABLE_FORMATS == list(SUPPORTED_FORMATS)


def test_contract_does_not_pin_the_list(repo_root):
    # NB-3 — 계약이 목록을 박지 않았음을 시험이 지킨다. 박히면 이 시험이 red 다.
    text = (repo_root / "contracts" / "events" / "core-pipeline.json").read_text("utf-8")
    assert '"renderable"' in text
    assert '"enum": ["NetCDF"' not in text.replace(" ", " ")
