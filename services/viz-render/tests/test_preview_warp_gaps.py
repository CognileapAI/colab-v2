"""③지도형 warp 의 **구멍** — 버그 4(점 격자)·13·14(가로 흰 줄)의 오라클.

전방 산란(`np.add.at` 으로 원본 셀을 출력 격자에 던져 넣기)은 **원본이 출력보다
촘촘할 때만** 옳다. 출력은 항상 긴 변 1024 인데 원본은 그보다 성길 수 있고,
그러면 원본 셀 수만큼만 채워지고 나머지는 결측 → 알파 0 이다.

- 성긴 원본(126×128) → 채워진 픽셀 **1.95 %**. 화면에는 **점 격자**로 보인다(버그 4).
- 같은 해상도(1024×1024) → 전 결측 **행 2줄**. lat→y 가 비선형이라 행 간격만
  불균등해져 **가로 흰 줄**이 남는다(버그 13·14). 세로 줄은 없다 — lon→x 는 선형이다.

**역방향(출력 주도) 매핑**이면 둘 다 성립하지 않는다. 다만 두 성질을 함께 지켜야 한다 —
⑴ 원본 결측을 **채우지 않는다**(NoData 를 이웃 값으로 메우면 없는 관측을 그린 것이다)
⑵ 원본이 출력보다 촘촘하면 **여전히 평균**이다(`downsample.block_average` 의 이유 그대로).
"""
from __future__ import annotations

import numpy as np

from colab_viz.domains.d7_visualization.preview import warp_to_3857

#: D-04 `GK-2A_NDVI_20240615_bilinear_1km.tif` 의 실측 경계와 같은 자리(충청권).
BOUNDS = (126.70, 36.08, 127.96, 37.36)


def _mesh(values: np.ndarray, bounds=BOUNDS):
    """`jobs._mesh_from_bounds` 와 같은 규칙 격자를 세운다 — 실제 경로가 주는 모양이다."""
    w, s, e, n = bounds
    ny, nx = values.shape
    lat = np.repeat(np.linspace(n, s, ny)[:, None], nx, axis=1)
    lon = np.repeat(np.linspace(w, e, nx)[None, :], ny, axis=0)
    return lat, lon


def test_원본이_출력보다_성기면_출력이_점_격자가_된다는_결함():
    """⒜ 성긴 원본(126×128)이 1024 격자를 **거의 다** 채워야 한다."""
    rng = np.random.default_rng(7)
    values = rng.random((126, 128)).astype("f4")
    out, geom = warp_to_3857(values, *_mesh(values), max_side=1024)

    assert (geom.height, geom.width) == out.shape
    assert max(out.shape) == 1024, "출력 긴 변은 1024 로 고정이다 — 원본 해상도로 낮추지 않는다"
    filled = float(np.isfinite(out).mean())
    assert filled >= 0.95, f"성긴 원본이 출력을 못 채운다: {filled:.4f}"


def test_성긴_원본에서_전_결측_행과_열이_남지_않는다():
    """⒝ 발자국 안에 통째로 빈 행·열이 없어야 한다 — 규칙 격자면 발자국 = 출력 전체다."""
    rng = np.random.default_rng(7)
    values = rng.random((126, 128)).astype("f4")
    out, _ = warp_to_3857(values, *_mesh(values), max_side=1024)

    empty = ~np.isfinite(out)
    assert int(empty.all(axis=1).sum()) == 0, "전 결측 행이 남았다"
    assert int(empty.all(axis=0).sum()) == 0, "전 결측 열이 남았다"


def test_같은_해상도에서도_가로_흰_줄이_남지_않는다():
    """⒝′ 버그 13·14 — 1024×1024 원본인데도 전 결측 행이 2줄 남던 자리."""
    rng = np.random.default_rng(11)
    values = rng.random((1024, 1024)).astype("f4")
    out, _ = warp_to_3857(values, *_mesh(values), max_side=1024)

    empty = ~np.isfinite(out)
    assert int(empty.all(axis=1).sum()) == 0, "가로 흰 줄이 남았다"
    assert int(empty.all(axis=0).sum()) == 0, "세로 흰 줄이 생겼다"


def test_원본의_결측은_이웃_값으로_메워지지_않는다():
    """⒞ 역방향 매핑이 NoData 까지 채우면 **없는 관측을 그린 것**이다.

    결측 덩어리를 안쪽에 두고(경계 계산이 값 있는 셀에서 나오므로 가장자리를 피한다)
    ① 알려진 덩어리가 통째로 결측으로 남는지 ② 결측 비율이 보존되는지를 함께 본다.
    """
    rng = np.random.default_rng(13)
    values = rng.random((126, 128)).astype("f4")
    values[40:70, 30:60] = np.nan                 # 원본 셀 900 개 = 5.58 %
    src_nan = float(np.isnan(values).mean())

    out, geom = warp_to_3857(values, *_mesh(values), max_side=1024)
    out_nan = float(np.isnan(out).mean())
    assert abs(out_nan - src_nan) <= 0.02, f"결측 비율이 갈렸다: 원본 {src_nan:.4f} / 출력 {out_nan:.4f}"

    # 알려진 결측 덩어리의 **한가운데**는 출력에서도 통째로 결측이어야 한다.
    w4326, s4326, e4326, n4326 = BOUNDS
    lat_c = n4326 + (s4326 - n4326) * (55.0 / 125.0)      # 행 40~69 의 중앙
    lon_c = w4326 + (e4326 - w4326) * (44.0 / 127.0)      # 열 30~59 의 중앙
    y = 6378137.0 * np.log(np.tan(np.pi / 4 + np.radians(lat_c) / 2))
    x = 6378137.0 * np.radians(lon_c)
    minx, miny, maxx, maxy = geom.bbox_3857
    col = int((x - minx) / (maxx - minx) * geom.width)
    row = int((maxy - y) / (maxy - miny) * geom.height)
    block = out[row - 3:row + 4, col - 3:col + 4]
    assert np.isnan(block).all(), f"결측 덩어리 한가운데가 채워졌다: {block}"


def test_원본이_출력보다_촘촘하면_여전히_평균이다():
    """⒟ 「촘촘 → 평균」 성질의 보존 확인. **처음부터 green 인 회귀 방지선**이다.

    행마다 0·10 을 번갈아 둔 2048×2048 은 2×2 블록평균이면 전부 5.0 이고,
    최근접이면 0 또는 10 이 그대로 남는다. 값으로 둘을 가른다.
    """
    values = np.zeros((2048, 2048), dtype="f4")
    values[1::2, :] = 10.0
    out, _ = warp_to_3857(values, *_mesh(values), max_side=1024)

    finite = out[np.isfinite(out)]
    assert finite.size > 0
    assert np.allclose(finite, 5.0, atol=1e-3), (
        f"촘촘한 원본이 평균되지 않았다: min={finite.min()} max={finite.max()}")


def test_곡선_격자의_발자국_밖은_채우지_않는다():
    """구멍을 메우는 것과 **발자국을 부풀리는 것**은 다르다 — 회전 격자의 모서리는 결측이다."""
    rng = np.random.default_rng(17)
    ny, nx = 200, 200
    values = rng.random((ny, nx)).astype("f4")
    u = np.linspace(-0.6, 0.6, nx)[None, :]
    vv = np.linspace(-0.6, 0.6, ny)[:, None]
    ang = np.radians(45.0)
    lon = 127.3 + (u * np.cos(ang) - vv * np.sin(ang))
    lat = 36.7 + (u * np.sin(ang) + vv * np.cos(ang))
    out, _ = warp_to_3857(values, lat, lon, max_side=1024)

    h, w = out.shape
    k = max(2, min(h, w) // 25)
    for corner in (out[:k, :k], out[:k, -k:], out[-k:, :k], out[-k:, -k:]):
        assert np.isnan(corner).all(), "마름모 격자의 bbox 모서리가 채워졌다"
    inner = out[h // 2 - h // 8:h // 2 + h // 8, w // 2 - w // 8:w // 2 + w // 8]
    assert float(np.isfinite(inner).mean()) >= 0.95, "발자국 안쪽에 구멍이 남았다"
