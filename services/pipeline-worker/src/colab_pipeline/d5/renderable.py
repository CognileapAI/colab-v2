"""`renderable` 판정 — 「지도로 그릴 수 있는 포맷인가」.

**계약은 목록을 박지 않는다**(`NB-3`). `FormatDetectedPayload.renderable` ·
`UploadReadyPayload.renderable` 은 boolean 이고, 그 boolean 을 만드는 목록은 **여기**
(pipeline-worker) 에 있다. 그릴 수 있는 범위는 viz-render 가 자라면서 바뀌고 정본도
§11 미결로 남겼으므로, 값 집합을 계약에 넣으면 정본에 없는 어휘를 계약이 만든다.

**목록은 지원 포맷에서 파생한다** — 두 곳에 적으면 갈라진다(`formats.SUPPORTED_FORMATS`).
~~지금은 지원 4종이 곧 그릴 수 있는 4종이다.~~ 갈라지는 날이 오면 **여기 한 줄**이 갈라진다.

⭑ **그날이 왔다 (`〈134〉` · 2026-08-26).** `GRIB` 이 지원 포맷으로 돌아왔지만
**미리보기 대상은 아니다** — 결정 2-3 이 스스로 적었다: 「5종이어도 grib 은 미리보기
대상이 아니다(미리보기는 bin·nc·tif·HDF)」. 그래서 파생이 **뺄셈**이 됐다.

**빼는 목록을 여기 한 곳에만 둔다.** 「그릴 수 있는 것」을 따로 나열하면 지원 포맷이
늘 때마다 두 목록이 조용히 갈라진다 — 새 포맷이 렌더 목록에 안 들어가도 아무도 모른다.
**뺄셈으로 적으면 새 포맷은 기본이 「그릴 수 있음」이고, 못 그리는 것만 명시적으로 뺀다.**

⚠ **그릴 수 없는 것과 등록할 수 없는 것은 다르다** — `renderable=false` 는 등록·다운로드·
계보 확정을 막지 않는다(정본 §9 「그릴 수 없는 형식」).

**stage2 대기.** `renderable` 값 자체는 완료 정의 밖이다 — 배포 단위·시험은 유지한다
(`〈71〉-㉰`). 근거: `dev-package/sessions/S1-PLAN.md` §5.2 행 7 · `PLAN-SoT.md §9 〈74〉〈75〉`.
"""
from __future__ import annotations

from .formats import SUPPORTED_FORMATS

#: 지원은 하되 **그릴 수는 없는** 포맷. 정본이 미리보기 대상을 `bin·nc·tif·HDF` 로
#: 못 박았으므로(결정 2-3) `GRIB` 이 여기 들어온다. **등록·다운로드·계보 확정은 막지
#: 않는다** — 「그릴 수 없는 것과 등록할 수 없는 것은 다르다」.
NOT_RENDERABLE_FORMATS: list[str] = ["GRIB"]

#: 미리보기를 그릴 수 있는 포맷. **숫자가 아니라 목록이다**(`〈51〉`·`〈134〉`).
RENDERABLE_FORMATS: list[str] = [
    fmt for fmt in SUPPORTED_FORMATS if fmt not in NOT_RENDERABLE_FORMATS]


def is_renderable(detected_format: str | None) -> bool:
    """감지 실패(`None`)면 false — 계약이 그렇게 적었다."""
    if detected_format is None:
        return False
    return detected_format in RENDERABLE_FORMATS
