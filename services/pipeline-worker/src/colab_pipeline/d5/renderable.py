"""`renderable` 판정 — 「지도로 그릴 수 있는 포맷인가」.

**계약은 목록을 박지 않는다**(`NB-3`). `FormatDetectedPayload.renderable` ·
`UploadReadyPayload.renderable` 은 boolean 이고, 그 boolean 을 만드는 목록은 **여기**
(pipeline-worker) 에 있다. 그릴 수 있는 범위는 viz-render 가 자라면서 바뀌고 정본도
§11 미결로 남겼으므로, 값 집합을 계약에 넣으면 정본에 없는 어휘를 계약이 만든다.

**목록은 지원 포맷에서 파생한다** — 두 곳에 적으면 갈라진다(`formats.SUPPORTED_FORMATS`).
지금은 지원 4종이 곧 그릴 수 있는 4종이다. 갈라지는 날이 오면 **여기 한 줄**이 갈라진다.

⚠ **그릴 수 없는 것과 등록할 수 없는 것은 다르다** — `renderable=false` 는 등록·다운로드·
계보 확정을 막지 않는다(정본 §9 「그릴 수 없는 형식」).
"""
from __future__ import annotations

from .formats import SUPPORTED_FORMATS

#: 미리보기를 그릴 수 있는 포맷. **숫자가 아니라 목록이다**(`〈51〉`).
RENDERABLE_FORMATS: list[str] = list(SUPPORTED_FORMATS)


def is_renderable(detected_format: str | None) -> bool:
    """감지 실패(`None`)면 false — 계약이 그렇게 적었다."""
    if detected_format is None:
        return False
    return detected_format in RENDERABLE_FORMATS
