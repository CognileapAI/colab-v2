"""`.npy` 는 **독립 지원 포맷**이고, 축은 **사다리**로 가른다 (`〈77〉` · `§5.4.2`).

`.npy` — Ted 판정(2026-08-24): 「npy 도 처리해야 하는 포맷이다만. 추가 포맷으로 한다.
nc 랑은 다른 파일이다.」 지원 포맷은 **숫자가 아니라 목록**이다(`〈51〉`).
**결측은 NaN 만이다**(`〈77〉`) — `.npy` 에는 메타가 없어 다른 규약이 없다.

축 사다리 — ①내장 좌표 ②**값 범위(절댓값 최대 > 90 → 경도, 실측 14/14)** ③쌍 정합
④파일명. **파일명은 맨 아래다** — 외부 반입 파일에서 가장 먼저 깨진다(`§10-4`).
"""
from __future__ import annotations

import numpy as np
import pytest

from colab_viz.domains.d7_visualization import grid as vgrid
from colab_viz.domains.d7_visualization.readers import SUPPORTED_FORMATS, detect_format, read_field


def _save(path, arr):
    np.save(path, arr)
    return path.with_suffix(".npy") if path.suffix != ".npy" else path


# ── `.npy` 포맷 ─────────────────────────────────────────────────────────────
def test_지원_목록에_NumPy_가_있다():
    assert "NumPy" in SUPPORTED_FORMATS


def test_npy_는_매직바이트로_감지된다_확장자가_아니라(tmp_path):
    """저장 키에 확장자가 없는 자리가 실재한다 — 확장자로 가르면 거기서 깨진다(`§0 M-1`)."""
    p = tmp_path / "키에는_확장자가_없다"
    p.write_bytes(_bytes_of(np.zeros((4, 4), dtype="f4")))
    assert detect_format(p) == "NumPy"


def _bytes_of(arr) -> bytes:
    import io
    buf = io.BytesIO()
    np.save(buf, arr)
    return buf.getvalue()


def test_npy_의_결측은_NaN_만이다(tmp_path):
    """`〈77〉` — 정본에 `.npy` 결측 규약이 없다. **기본값을 지어내지 않는다.**"""
    arr = np.array([[1.0, np.nan], [-9999.0, 3.0]], dtype="f4")
    p = tmp_path / "values.npy"
    np.save(p, arr)
    fmt, field = read_field(p)
    assert fmt == "NumPy"
    assert np.isnan(field.values[0, 1])
    # −9999 는 tif 의 규약이지 `.npy` 의 규약이 아니다 — 여기서는 **유효값**이다
    assert field.values[1, 0] == -9999.0
    assert field.fills == ()


def test_npy_는_좌표를_말하지_않는다(tmp_path):
    """배열·dtype·shape 가 전부다 — ③지도형은 HSR 과 같은 자리에 선다(`§E.4-⑶`)."""
    p = tmp_path / "values.npy"
    np.save(p, np.ones((8, 8), dtype="f4"))
    _, field = read_field(p)
    assert field.has_position is False


def test_3차원_npy_는_한_번에_값_하나만_그린다(tmp_path):
    p = tmp_path / "stack.npy"
    np.save(p, np.ones((10, 8, 8), dtype="f4"))
    _, field = read_field(p)
    assert field.values.shape == (8, 8)


# ── 축 사다리 ───────────────────────────────────────────────────────────────
def test_값_범위가_파일명을_이긴다(tmp_path):
    """`Lat` 이라 적혀 있어도 값이 90 을 넘으면 경도다 — **파일명은 맨 아래다.**"""
    g = tmp_path / "grid"
    g.mkdir()
    np.save(g / "Lat_HSR.npy", np.full((4, 4), 127.0))     # 이름은 위도, 값은 경도
    np.save(g / "Lon_HSR.npy", np.full((4, 4), 37.0))      # 이름은 경도, 값은 위도
    found = vgrid.find_reference_grid(g, expect_shape=(4, 4))
    assert float(found.lat.max()) == 37.0, "파일명을 따라가 축이 뒤바뀌었다"
    assert float(found.lon.max()) == 127.0


def test_둘_다_90_이하면_판별_실패다_파일명으로_정하지_않는다(tmp_path):
    """`§E.2-⑦` — 「두 파일 모두 값이 ±90 안에 있어 구분할 수 없습니다.」
    ⚠ 이름이 `lat`·`lon` 이어도 정하지 않는다. **파일명은 확정 근거가 아니다**(`§10-4`)."""
    g = tmp_path / "grid"
    g.mkdir()
    np.save(g / "lat_seoul.npy", np.full((4, 4), 37.0))
    np.save(g / "lon_seoul.npy", np.full((4, 4), 38.0))
    with pytest.raises(vgrid.GridUnavailableError) as e:
        vgrid.find_reference_grid(g, expect_shape=(4, 4))
    assert "축" in str(e.value)


def test_대소문자가_달라도_같은_격자를_찾는다(tmp_path):
    """같은 배열이 트리마다 `Lat_HSR.npy` · `LAT_HSR.npy` 로 다르게 적힌다(`§5.4.1`)."""
    g = tmp_path / "grid"
    g.mkdir()
    np.save(g / "LAT_HSR.npy", np.full((4, 4), 37.0))
    np.save(g / "LON_HSR.npy", np.full((4, 4), 127.0))
    found = vgrid.find_reference_grid(g, expect_shape=(4, 4))
    assert float(found.lat.max()) == 37.0


def test_한_폴더에_여러_쌍이_있으면_stem_으로_짝짓는다(tmp_path):
    """`LAT_HSR`·`LAT_RN15`·`LAT_crop` 이 한 폴더에 공존한다 — 정렬 첫 항목은 규칙이 아니다."""
    g = tmp_path / "grid"
    g.mkdir()
    np.save(g / "LAT_HSR.npy", np.full((4, 4), 37.0))
    np.save(g / "LON_HSR.npy", np.full((4, 4), 127.0))
    np.save(g / "LAT_RN15.npy", np.full((6, 6), 35.0))
    np.save(g / "LON_RN15.npy", np.full((6, 6), 129.0))
    found = vgrid.find_reference_grid(g, expect_shape=(6, 6))
    assert found.shape == (6, 6)
    assert float(found.lat.max()) == 35.0 and float(found.lon.max()) == 129.0
    assert "RN15" in found.source


def test_짝이_안_맞으면_거절하고_리샘플로_맞추지_않는다(tmp_path):
    g = tmp_path / "grid"
    g.mkdir()
    np.save(g / "lat.npy", np.full((4, 4), 37.0))
    np.save(g / "lon.npy", np.full((5, 5), 127.0))
    with pytest.raises(vgrid.GridUnavailableError):
        vgrid.find_reference_grid(g, expect_shape=(4, 4))
