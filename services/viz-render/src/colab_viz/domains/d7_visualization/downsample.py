"""다운샘플 두 가지 — **상세는 블록평균, 썸네일은 stride** (`PREVIEW-IMPLEMENTATION §3.1·§3.2`).

**둘을 섞지 마라.** 상세(1024 px)에 stride 를 쓰면 점 형태 강수가 실제로 사라진다 —
실측 전역 **5.79 %**(69,568 중 4,031) · 산발 에코 확대 **16.9 %**(2,392 중 404).
블록평균은 픽셀 수에 비례한 비용을 문다(bin 98.3 ms · tif 157.5 ms) — **그 비용을 낸다**
(`§3.2`). 썸네일 128 px 에서 stride 는 **의도된** 타협이다: 형상 식별용이라 누락을
허용하고, 값이 0.0 ms 다(뷰만 생성).

**결측은 평균에서 뺀다.** 블록 전체가 결측이면 결과도 결측이다 — 0 으로 채우면 없는
값을 그린 것이고, 부등호로 자르는 것과 같은 종류의 조용한 거짓이다(`§6.1`).
"""
from __future__ import annotations

import numpy as np


def steps_for(shape: tuple[int, int], max_side: int) -> tuple[int, int]:
    """긴 변이 `max_side` 아래로 내려가는 정수 간격 (행, 열)."""
    return (max(1, int(np.ceil(shape[0] / max_side))),
            max(1, int(np.ceil(shape[1] / max_side))))


def stride(arr: np.ndarray, steps: tuple[int, int]) -> np.ndarray:
    """`arr[::sy, ::sx]` — **뷰만 만든다.** 썸네일 전용이다(`§3.1`)."""
    return np.asarray(arr[::steps[0], ::steps[1]])


def block_average(arr: np.ndarray, steps: tuple[int, int]) -> np.ndarray:
    """`sy × sx` 블록의 **유효값 평균**. 블록 전체가 결측이면 결측이다.

    ⚠ `np.nanmean` 을 쓰지 않는다 — 전부 NaN 인 블록에서 경고를 내고 NaN 을 돌려주는데,
    경고를 끄는 것과 「센 적이 없다」를 구분해 두는 편이 낫다. 합과 개수를 따로 세면
    **개수 0 이 곧 결측**이라 판정이 값에서 나온다.

    가장자리가 나누어떨어지지 않으면 **버리지 않고** 남은 만큼만 평균한다.
    """
    sy, sx = steps
    a = np.asarray(arr, dtype="f4")
    if sy == 1 and sx == 1:
        return a.copy()
    ny, nx = a.shape
    ty, tx = -(-ny // sy), -(-nx // sx)          # 올림 나눗셈 — 가장자리를 버리지 않는다
    pad_y, pad_x = ty * sy - ny, tx * sx - nx
    if pad_y or pad_x:
        a = np.pad(a, ((0, pad_y), (0, pad_x)), constant_values=np.nan)

    valid = np.isfinite(a)
    sums = np.where(valid, a, 0.0).reshape(ty, sy, tx, sx).sum(axis=(1, 3))
    counts = valid.reshape(ty, sy, tx, sx).sum(axis=(1, 3))
    out = np.full((ty, tx), np.nan, dtype="f4")
    hit = counts > 0
    out[hit] = (sums[hit] / counts[hit]).astype("f4")
    return out


def sample_centers(arr: np.ndarray, steps: tuple[int, int]) -> np.ndarray:
    """블록 **중심의 실측값**을 집는다 — 좌표 배열 전용.

    값은 평균해도 되지만 **좌표는 평균하지 않는다.** 평균은 측정된 좌표들 사이의 값을
    만들고, 그 순간 가장자리가 안쪽으로 밀려 **격자의 최솟값·최댓값이 바뀐다**
    (HSR 실측에서 `.npy` 판과 `.nc` 판을 가르는 차이가 612 m 인데, 반 블록 평균만으로
    같은 크기의 이동이 생긴다). 그래서 **집되, 모서리가 아니라 중심을 집고**,
    마지막 블록은 배열 끝으로 붙여 **양 끝 실측값이 살아남게** 한다.
    """
    a = np.asarray(arr)
    sy, sx = steps
    if sy == 1 and sx == 1:
        return np.asarray(a)
    ny, nx = a.shape
    ty, tx = -(-ny // sy), -(-nx // sx)
    rows = np.minimum(np.arange(ty) * sy + sy // 2, ny - 1)
    cols = np.minimum(np.arange(tx) * sx + sx // 2, nx - 1)
    rows[-1] = ny - 1                       # 마지막 행의 실측 좌표를 잃지 않는다
    cols[-1] = nx - 1
    return np.asarray(a[np.ix_(rows, cols)])
