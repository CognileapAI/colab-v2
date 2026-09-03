"""축 판별의 **데이터 오류는 예외가 아니라 판별 실패다** (코드리뷰 20260903 #4).

`〈66〉` 이 정한 출력은 둘뿐이다 — 축을 확정하거나, `AxisUndeterminedError` 로 거절하거나.
그런데 `_stats` 가 `arr[:4096, :4096]` 을 **`ndim` 검사보다 먼저** 하고 있어 1차원 격자
`.npy` 가 `IndexError` 로 탈출했고, `np.load` 가 거부하는 바이트(object dtype · 절단)도
같은 자리로 새어 나갔다. 그 예외는 `detect_axes_for_upload` 의 `except AxisUndeterminedError`
를 지나쳐 `process_upload` → `_lab_pass` 의 rollback → `serve()` 종료로 이어졌다 —
**한 파일의 형상 하나가 전 연구실의 워커를 크래시 루프에 넣었다.**

여기서 지키는 것은 하나다 — **파일의 내용이 이상한 것은 배관이 깨진 것이 아니다.**
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from colab_pipeline.d5.axis import (
    AxisUndeterminedError,
    detect_axes,
    detect_axes_for_upload,
)


def _one_dim(path: Path, n: int = 2881) -> Path:
    """실물 무늬 — `Lat_*.npy` 가 (2881,) 1차원으로 올라온다."""
    np.save(path, np.linspace(33.0, 39.0, n))
    return path


def test_1차원_격자는_IndexError_가_아니라_판별_실패다(tmp_path):
    p = _one_dim(tmp_path / "lat_1d.npy")
    with pytest.raises(AxisUndeterminedError):
        detect_axes(p)


def test_절단된_npy_는_판별_실패다(tmp_path):
    """헤더는 맞는데 본문이 잘렸다 — `np.load` 가 `ValueError` 를 던진다."""
    full = tmp_path / "lat_full.npy"
    np.save(full, np.linspace(33.0, 39.0, 4096).reshape(64, 64))
    cut = tmp_path / "lat_cut.npy"
    cut.write_bytes(full.read_bytes()[:200])
    with pytest.raises(AxisUndeterminedError):
        detect_axes(cut)


def test_object_dtype_npy_는_판별_실패다(tmp_path):
    """`allow_pickle=False` 가 거부하는 배열 — 거절 사유이지 배관 고장이 아니다."""
    p = tmp_path / "lat_obj.npy"
    np.save(p, np.array([{"a": 1}, {"b": 2}], dtype=object), allow_pickle=True)
    with pytest.raises(AxisUndeterminedError):
        detect_axes(p)


def test_업로드_단위_판별이_1차원_격자에서_터지지_않는다(tmp_path):
    """`detect_axes_for_upload` 는 못 정한 파일을 **거절 목록**에 담고 계속 돈다.

    ⚠ 여기서 예외가 새면 `process_upload` 가 통째로 죽고, `〈63〉-ⓒ`「그 파일만 막고
    등록은 막지 않는다」가 배선에서 성립하지 않는다.
    """
    bad = _one_dim(tmp_path / "lat_1d.npy")
    good = tmp_path / "lon_2d.npy"
    np.save(good, np.repeat(np.linspace(124.0, 132.0, 8)[None, :], 8, axis=0))

    res = detect_axes_for_upload([bad, good])

    assert bad in res.rejected, "1차원 격자가 거절 목록에 없다"
    assert res.reasons[bad], "거절 사유가 계약 enum 으로 안 붙었다"
    assert good in res.resolved, "정상 격자까지 함께 넘어졌다"
