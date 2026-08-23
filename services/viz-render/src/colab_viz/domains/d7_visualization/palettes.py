"""팔레트 — viz-render 가 소유한다.

정본은 **「팔레트 3종」까지만** 말하고 이름을 열거하지 않는다
(`Policy_데이터셋_상세.md:163` — 「값 선택(하나)·팔레트 3종·구간 수 3~9」).
그래서 계약이 이름을 안 박고 `listPalettes` 로 서빙한다.

`[정본 무근거]` — **팔레트의 이름·라벨·색값은 정본에 없다.** 정한 것은 개수(3)뿐이고
나머지는 이 단위의 결정이다. 셋을 고른 기준은 「무엇을 그리는가」가 아니라
「값이 어떻게 생겼는가」다 — 한 방향으로 커지는 값 · 범주를 구분해야 하는 값 ·
가운데 기준이 있는 값. `matplotlib` 을 끌어오지 않는다(런타임 의존을 하나 줄인다).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    key: str
    label: str
    #: 구간 색을 뽑아 쓰는 기준점들. 구간 수(3~9)에 맞춰 선형 보간한다.
    anchors: tuple[str, ...]


PALETTES: tuple[Palette, ...] = (
    Palette("단색-파랑", "단색 · 파랑 (한 방향으로 커지는 값)",
            ("#f0f6ff", "#a9c9ec", "#5b9bd5", "#2a6db0", "#0b3d75")),
    Palette("다색-무지개", "다색 · 무지개 (넓은 범위를 잘게 가르는 값)",
            ("#3b4cc0", "#2fa4a0", "#7cc03a", "#f0c11a", "#e8622a", "#b31b1b")),
    Palette("발산-한난", "발산 · 한난 (가운데 기준이 있는 값)",
            ("#2166ac", "#92c5de", "#f7f7f7", "#f4a582", "#b2182b")),
)

_BY_KEY = {p.key: p for p in PALETTES}

#: 구간 수 — 정본 `§5 시각화 구간 수 — 3~9 단계, 기본 6`.
MIN_CLASS_COUNT = 3
MAX_CLASS_COUNT = 9
DEFAULT_CLASS_COUNT = 6


class UnknownPalette(Exception):
    pass


def get(key: str) -> Palette:
    try:
        return _BY_KEY[key]
    except KeyError:
        raise UnknownPalette(f"모르는 팔레트다: {key}") from None


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    return (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def ramp(palette: Palette, count: int) -> list[str]:
    """기준점들을 구간 수만큼 선형 보간해 `#rrggbb` 목록으로 만든다."""
    if not (MIN_CLASS_COUNT <= count <= MAX_CLASS_COUNT):
        raise ValueError(f"구간 수는 {MIN_CLASS_COUNT}~{MAX_CLASS_COUNT} 다: {count}")
    anchors = [_hex_to_rgb(a) for a in palette.anchors]
    last = len(anchors) - 1
    out: list[str] = []
    for i in range(count):
        pos = 0.0 if count == 1 else i * last / (count - 1)
        lo = int(pos)
        hi = min(lo + 1, last)
        t = pos - lo
        out.append(_rgb_to_hex(tuple(
            round(anchors[lo][c] + (anchors[hi][c] - anchors[lo][c]) * t) for c in range(3)
        )))
    return out


def options() -> list[dict]:
    """`PaletteOption` 목록 — 고르는 자리에 색 견본을 함께 준다."""
    return [{"palette": p.key, "label": p.label,
             "sampleColors": ramp(p, DEFAULT_CLASS_COUNT)} for p in PALETTES]
