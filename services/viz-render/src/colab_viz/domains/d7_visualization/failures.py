"""렌더 실패의 종류 — 정본 §9 의 상황을 `ErrorEnvelope.code` 로 가른다.

**`NB-B` 에 대한 이 레인의 답** — `RenderFailureCode` 는 계약에 신설되지 않았지만,
`common.json#ErrorEnvelope.code` 가 **enum 없는 자유 문자열**이라 정본이 요구한 구분은
계약 개정 없이 표현된다. 그래서 **계약을 고치지 않았고, 멈출 이유도 없었다.**
남는 것은 「코드 문자열 자체는 정본에 없다」는 사실뿐이고 그것은 `[정본 무근거]`다.

메시지는 **정본 문구 그대로**다 (`Policy_데이터셋_상세 §8 미리보기를 그릴 수 없을 때` ·
`Policy_업로드와_계보_확정 §9`). 화면이 다시 지어내지 않게 여기서 내려보낸다.
"""
from __future__ import annotations

from typing import Final


class RenderFailure:
    """`failure.code` 값. 앞 셋이 정본 §9 가 구분을 요구한 3종이다."""

    UNREACHABLE: Final = "RENDER_SERVER_UNREACHABLE"   # 그리는 서버에 연결 못 함
    TIMEOUT: Final = "RENDER_TIMEOUT"                  # 그리다 시간 초과
    UNKNOWN: Final = "RENDER_UNKNOWN_ERROR"            # 그리다 알 수 없는 오류
    # 넷째 — 정본이 **별도 행으로** 둔 상황이라 「알 수 없는 오류」에 섞지 않는다.
    # 안내 문구도 다르고 복구 경로(`짝 파일 없이 그려 보기`)도 다르다.
    NO_REFERENCE_GRID: Final = "REFERENCE_GRID_MISSING"
    # 다섯째 — 격자는 있었는데 **결과 위치가 상식 밖**이다(`PREVIEW-IMPLEMENTATION §9` warp 행).
    # 「격자가 없다」와 섞으면 화면이 「올려 주세요」라고 말하는데 이미 올린 상태가 된다.
    MAP_BOUNDS_IMPLAUSIBLE: Final = "MAP_BOUNDS_IMPLAUSIBLE"
    # 여섯째 — **못 그리는 것이 아니라 그릴 수 없는 요청**이다(`〈2026-09-03 레인 C 수용 검토 #2〉`).
    # 값은 `kernel/errors.NOT_RENDERABLE` 과 **같은 문자열**이다 — 접수 때 415 로 나가는
    # 것과 그리다 드러나는 것이 같은 성질이라, 부르는 쪽이 코드를 두 번 배우지 않는다.
    # ⚠ 이 코드가 붙는 실패는 `is_retry_pointless` 가 True 인 자리와 **같아야 한다** —
    # 「다시 그리기」를 감출지 말지가 이 한 값에 걸려 있다.
    NOT_RENDERABLE: Final = "NOT_RENDERABLE"


#: 415 안내 문구. **그릴 수 있는 형식을 함께 적는다** — 안 되는 것만 말하면
#: 무엇을 올려야 하는지 모른 채 떠난다 (정본 §8 · 개정 이력 v2.1-③).
NOT_RENDERABLE_MESSAGE: Final = "이 형식은 아직 지도로 못 그려요."

FAILURE_MESSAGES: Final[dict[str, str]] = {
    RenderFailure.UNREACHABLE: "지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.",
    RenderFailure.TIMEOUT: "그리는 데 너무 오래 걸려요. 조각 하나나 좁은 기간으로 다시 해 보세요.",
    RenderFailure.UNKNOWN: "미리보기를 만들다 문제가 생겼어요.",
    RenderFailure.NO_REFERENCE_GRID: "위경도를 담은 짝 파일이 없어요.",
    RenderFailure.MAP_BOUNDS_IMPLAUSIBLE:
        "격자를 적용했지만 결과 위치가 상식 밖이라 지도에 얹지 않았어요.",
    # **라우트가 415 로 내는 문구와 같은 것**을 쓴다. 실물 사유(무엇을 요청했고 파일에
    # 무엇이 있는가)는 `details.detail` 에 실린다 — 라우트의 NOT_RENDERABLE 봉투와
    # 같은 배치다.
    RenderFailure.NOT_RENDERABLE: NOT_RENDERABLE_MESSAGE,
}

#: 정본 「미리보기는 500MB까지 그려요」 [가정] — 복구 경로는 「조각 하나를 골라 그린다」.
TOO_LARGE_MESSAGE: Final = "미리보기는 500MB까지 그려요. 조각 하나를 골라 그려 보세요."


class RenderError(Exception):
    """렌더 도중의 실패. `code` 가 정본 실패 종류를 가른다."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(detail or FAILURE_MESSAGES.get(code, code))
        self.code = code
        self.detail = detail

    @property
    def message(self) -> str:
        return FAILURE_MESSAGES.get(self.code, str(self))


class NotRenderableError(Exception):
    """어느 표현으로도 그릴 수 없다 — 415. **등록·다운로드·계보 확정은 그대로 된다.**"""


#: **그리지 않는 것**과 **못 그리는 것**을 가른다 (`C-5` · 결정 2-3 · `〈135〉`).
#: 정본이 요구한 분리 = 「못 그렸어요(**재시도 가능**)」 vs
#: 「이 형식은 원래 안 그려져요(**재시도 무의미**)」.
#:
#: 결정 #8 이 「못 그렸어요 ＋ **다시 그리기**」 상태를 만들라고 했으므로 **그 버튼을
#: 언제 감출지가 정해져 있어야 한다.** 안 그러면 GRIB 에도 「다시 그리기」가 뜨고,
#: 눌러도 영원히 같은 실패가 돌아온다 — 사용자가 자기 파일을 의심하게 된다.
NOT_A_PREVIEW_TARGET_MESSAGE: Final = (
    "이 형식은 지도로 그리지 않아요. 내려받아서 쓰는 자료예요.")


def is_retry_pointless(error: Exception) -> bool:
    """다시 그려도 결과가 같은가.

    `NotRenderableError` 는 **파일의 성질**에서 오는 실패라 재시도가 무의미하다 —
    포맷이 바뀌지 않는 한 몇 번을 눌러도 같다. 반대로 `RenderError`(연결 실패·시간
    초과·알 수 없는 오류)는 **그때의 사정**이라 다시 해 볼 만하다.
    """
    return isinstance(error, NotRenderableError)
