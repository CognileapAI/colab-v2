"""다운샘플 두 가지와 256엔트리 LUT — `PREVIEW-IMPLEMENTATION §3.1·§3.2·§6.1·§6.3`.

**상세(1024 px)에 stride 를 쓰면 점 형태 강수가 사라진다** — 실측 전역 5.79 % ·
국지 16.9 %(`§3.2` 대비표). 그래서 상세는 블록평균이고, 썸네일(128 px)에서만
stride 가 **의도된** 타협이다(`§10-6`).

결측은 **알파 0** 이다 — 컬러맵의 색 하나를 결측에 배정하지 않는다(`§6.1`).
"""
from __future__ import annotations

import numpy as np

from colab_viz.domains.d7_visualization import colormap, downsample


def test_블록평균은_점_형태_값을_잃지_않고_stride_는_잃는다():
    """`§3.2` 의 대비 실험을 축소해 그대로 세운다."""
    arr = np.full((90, 90), np.nan, dtype="f4")
    # 3의 배수가 아닌 자리에만 점을 찍는다 — stride 3 이 지나치는 자리다
    arr[1::3, 2::3] = 5.0
    points = int(np.isfinite(arr).sum())          # 900 — 블록마다 정확히 하나

    strided = downsample.stride(arr, (3, 3))
    averaged = downsample.block_average(arr, (3, 3))

    assert int(np.isfinite(strided).sum()) == 0, "stride 는 점을 통째로 지나친다"
    assert int(np.isfinite(averaged).sum()) == points
    assert averaged.shape == strided.shape == (30, 30)


def test_블록평균은_유효값만_평균하고_전부_결측이면_결측이다():
    arr = np.array([[1.0, np.nan], [3.0, 5.0]], dtype="f4")
    out = downsample.block_average(arr, (2, 2))
    assert out.shape == (1, 1)
    assert abs(float(out[0, 0]) - 3.0) < 1e-6      # (1+3+5)/3 — NaN 은 평균에서 뺀다

    empty = downsample.block_average(np.full((2, 2), np.nan, dtype="f4"), (2, 2))
    assert np.isnan(empty[0, 0])


def test_블록평균은_나누어떨어지지_않는_가장자리도_버리지_않는다():
    arr = np.ones((5, 5), dtype="f4")
    out = downsample.block_average(arr, (2, 2))
    assert out.shape == (3, 3)
    assert np.isfinite(out).all()


def test_steps_for_는_긴_변을_상한_아래로_내린다():
    assert downsample.steps_for((2881, 2305), 1024) == (3, 3)
    assert downsample.steps_for((2881, 2305), 128) == (23, 19)
    assert downsample.steps_for((8, 8), 1024) == (1, 1)


def test_viridis_는_11앵커에서_뽑은_256엔트리다():
    lut = colormap.lut256(colormap.VIRIDIS_ANCHORS)
    assert lut.shape == (256, 3)
    assert tuple(lut[0]) == (0x44, 0x01, 0x54)
    assert tuple(lut[255]) == (0xFD, 0xE7, 0x25)
    # 단조롭게 밝아진다 — 보간이 앵커를 건너뛰면 여기서 깨진다
    assert lut[:, 1].tolist() == sorted(lut[:, 1].tolist())


def test_결측은_알파_0_이고_색을_배정하지_않는다():
    values = np.array([[0.0, np.nan], [5.0, 10.0]], dtype="f4")
    rgba = colormap.to_rgba(values, vmin=0.0, vmax=10.0,
                            lut=colormap.lut256(colormap.VIRIDIS_ANCHORS))
    assert rgba.shape == (2, 2, 4)
    assert rgba[0, 1, 3] == 0                       # 결측 = 알파 0
    assert (rgba[0, 1, :3] == 0).all()              # 색조차 남기지 않는다
    assert rgba[0, 0, 3] == 255 and rgba[1, 1, 3] == 255
    assert tuple(rgba[0, 0, :3]) == (0x44, 0x01, 0x54)
    assert tuple(rgba[1, 1, :3]) == (0xFD, 0xE7, 0x25)


def test_범위_밖_값은_잘라_넣지_지어내지_않는다():
    lut = colormap.lut256(colormap.VIRIDIS_ANCHORS)
    values = np.array([[-100.0, 100.0]], dtype="f4")
    rgba = colormap.to_rgba(values, vmin=0.0, vmax=10.0, lut=lut)
    assert tuple(rgba[0, 0, :3]) == tuple(lut[0])
    assert tuple(rgba[0, 1, :3]) == tuple(lut[255])
    assert rgba[0, 0, 3] == 255                     # 잘린 값은 여전히 값이다
