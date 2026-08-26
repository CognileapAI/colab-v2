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
    # ⭑ GRIB 의 **값은 그대로 false 인데 이유가 바뀌었다** (`〈134〉`).
    #   종전 = 「`〈51〉` 로 범위 밖」. 지금 = **지원 목록 안이지만 미리보기 대상이 아니다**
    #   (결정 2-3 — 「5종이어도 grib 은 미리보기 대상이 아니다」).
    #   같은 false 라도 근거가 다르면 주석이 거짓말을 한다.
    assert is_renderable("GRIB") is False
    # 지원 목록 밖인 순수 HDF5

    assert is_renderable("HDF5") is False
    assert is_renderable("무엇인지 모를 것") is False


def test_renderable_list_is_not_a_number_and_lives_here():
    # 숫자가 아니라 목록이다 (〈51〉·〈134〉). 그리고 지원 목록과 **한 자리에서**
    # 파생된다 — 두 곳에 적으면 갈라진다.
    #
    # ⭑ **파생이 항등에서 뺄셈이 됐다** (`〈134〉`). 이 파일의 주석이 예고한 자리다 —
    #   「갈라지는 날이 오면 여기 한 줄이 갈라진다」. GRIB 이 그 첫 포맷이다.
    from colab_pipeline.d5.renderable import NOT_RENDERABLE_FORMATS

    assert RENDERABLE_FORMATS == [
        f for f in SUPPORTED_FORMATS if f not in NOT_RENDERABLE_FORMATS]
    assert RENDERABLE_FORMATS != SUPPORTED_FORMATS, "더는 같지 않다."
    # **뺄셈으로 적은 것이 요점이다** — 새 포맷은 기본이 「그릴 수 있음」이고
    # 못 그리는 것만 명시적으로 빠진다. 따로 나열하면 새 포맷이 조용히 누락된다.
    assert NOT_RENDERABLE_FORMATS == ["GRIB"]


def test_contract_does_not_pin_the_list(repo_root):
    # NB-3 — 계약이 목록을 박지 않았음을 시험이 지킨다. 박히면 이 시험이 red 다.
    text = (repo_root / "contracts" / "events" / "core-pipeline.json").read_text("utf-8")
    assert '"renderable"' in text
    assert '"enum": ["NetCDF"' not in text.replace(" ", " ")
