"""공통 색 범위 — **데이터셋 단위 고정, 잠정/확정 2단계** (`S1-PLAN-REFOUND §D.4-⑶`).

**프레임별 스트레치를 하지 마라**(`PREVIEW-IMPLEMENTATION §10-7`). 실측 — nc LST 5프레임에서
개별 스트레치와 공통 범위가 평균 2.9~26.8 DN · **최대 42 DN** 어긋나고 p98 이 50분 만에
4.4 K 이동한다. 재생하면 색이 튄다.

**그런데 0번째 업로드에는 데이터셋이 없다.** 「등록 확정 뒤 1회 산출」과 「범위가 없으면
안 그린다」를 겹치면 첫 미리보기가 영원히 안 나온다. 그래서 두 단계다:

| 단계 | 언제 | 무엇에서 | 어디에 |
|---|---|---|---|
| **잠정** | 업로드 직후(등록 확정 전) | 그 업로드에 함께 올라온 파일 집합 | **모달 미리보기 전용** |
| **확정** | 등록 확정 시 1회 | 그 데이터셋의 전체 파일 집합 | 상세·목록·이후 전부 |

⚠ **파일이 1장뿐이면 잠정 범위는 프레임별 스트레치와 수학적으로 같다. 숨기지 않는다.**
금지와 갈리는 근거는 셋뿐이고 **셋 다 지켜야 한다** —
ⓐ **출고되지 않는다**: `잠정` 은 `scope="upload"` 에서만 만들어진다(이 모듈이 강제한다).
ⓑ **라벨이 붙는다**: 계약 `ColorRangeStage` 로 산출물에 실린다.
ⓒ **등록 시 다시 잡힌다**: 확정 범위는 데이터셋 전체에서 새로 산출되고, 단계 토큰이
   캐시 키에 들어가 **값이 우연히 같아도 잠정 산출물이 확정으로 승격되지 않는다**(`cache.py`).

⚠ **잠정 범위로 재생·애니메이션을 열지 않는다**(`§D.4-⑶ⓕ`). stage 1 에 재생 경로가
없다는 것이 지금의 보장이고, 생기면 그때 `stage` 를 조건으로 건다.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: 계약 `common.json#/$defs/ColorRangeStage` 의 두 값. **여기서 새로 만들지 않는다.**
STAGE_PROVISIONAL = "잠정"
STAGE_FINAL = "확정"

SCOPE_UPLOAD = "upload"
SCOPE_DATASET = "dataset"

#: 백분위 (`§6.2`). 2–98 % — 정본이 준 값이다.
LOW_PERCENT = 2.0
HIGH_PERCENT = 98.0

#: 범위는 **512 px 축약본**에서 잡는다 (`§6.2` 산출 비용 — HSR 12파일 884 ms ·
#: nc 5파일 204 ms). **전 해상도로 재지 마라.**
SAMPLE_SIDE = 512


class RangeUnavailableError(Exception):
    """유효값이 없어 범위를 못 잡았다. **지어내지 않는다** — 호출자가 실패로 끝낸다."""


@dataclass(frozen=True)
class ColorRange:
    vmin: float
    vmax: float
    stage: str
    scope: str
    scope_id: str

    def __post_init__(self) -> None:
        if self.stage not in (STAGE_PROVISIONAL, STAGE_FINAL):
            raise ValueError(f"모르는 색 범위 단계다: {self.stage}")
        if self.scope not in (SCOPE_UPLOAD, SCOPE_DATASET):
            raise ValueError(f"모르는 범위 대상이다: {self.scope}")
        # ⓐ 출고 금지의 코드 표현 — 데이터셋 산출물에 잠정 라벨을 붙일 길이 없다.
        if self.stage == STAGE_PROVISIONAL and self.scope != SCOPE_UPLOAD:
            raise ValueError("잠정 범위는 업로드 범위에서만 성립한다 — 데이터셋으로 출고되지 않는다")
        if self.stage == STAGE_FINAL and self.scope != SCOPE_DATASET:
            raise ValueError("확정 범위는 데이터셋 전체에서만 산출된다")

    def token(self) -> str:
        """캐시 키에 들어가는 **단계 토큰**. 값이 아니라 **어느 집합의 범위인가**를 싣는다."""
        return f"{self.stage}({self.scope}:{self.scope_id})"


def sample_for_range(values: np.ndarray) -> np.ndarray:
    """범위 산출용 축약본 — 긴 변 512 px. **stride 로 줄인다**(통계용이라 값 보존이 목적이 아니다)."""
    a = np.asarray(values)
    sy = max(1, int(np.ceil(a.shape[0] / SAMPLE_SIDE)))
    sx = max(1, int(np.ceil(a.shape[1] / SAMPLE_SIDE)))
    return np.asarray(a[::sy, ::sx], dtype="f4")


def percentile_range(arrays: list[np.ndarray]) -> tuple[float, float]:
    """집합 전체의 2–98 % 백분위. **집합이 무엇인가는 호출자가 정한다.**"""
    finite = []
    for arr in arrays:
        s = sample_for_range(arr)
        finite.append(s[np.isfinite(s)])
    if not finite:
        raise RangeUnavailableError("범위를 잡을 배열이 하나도 없다")
    pool = np.concatenate(finite) if len(finite) > 1 else finite[0]
    if pool.size == 0:
        raise RangeUnavailableError("유효값이 하나도 없다 — 범위를 지어내지 않는다")
    lo, hi = (float(v) for v in np.percentile(pool, [LOW_PERCENT, HIGH_PERCENT]))
    if lo == hi:
        hi = lo + 1.0        # 폭 0 을 만들지 않는다 — 값을 바꾸는 것이 아니라 경계를 정한다
    return lo, hi


def for_upload(upload_id: str, arrays: list[np.ndarray]) -> ColorRange:
    """**잠정** — 그 업로드에 함께 올라온 파일 집합에서 잡는다(첫 파일 하나가 아니다)."""
    lo, hi = percentile_range(arrays)
    return ColorRange(vmin=lo, vmax=hi, stage=STAGE_PROVISIONAL,
                      scope=SCOPE_UPLOAD, scope_id=upload_id)


def for_dataset(dataset_id: str, arrays: list[np.ndarray]) -> ColorRange:
    """**확정** — 데이터셋 전체 파일 집합에서 잡는다. 등록 확정 시 1회."""
    lo, hi = percentile_range(arrays)
    return ColorRange(vmin=lo, vmax=hi, stage=STAGE_FINAL,
                      scope=SCOPE_DATASET, scope_id=dataset_id)
