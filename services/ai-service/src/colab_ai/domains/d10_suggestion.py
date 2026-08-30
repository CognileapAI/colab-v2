"""D10 계보 제안 — **제안 한 장의 규격을 타입이 진다. 저장 경로는 없다.**

정본(`Policy_업로드와_계보_확정` · `PRD_업로드와_계보_확정`)이 못 박은 것을 값 검사가
아니라 **생성자**에 둔다. 이유는 이 기능의 성질이다 — 재료가 없으면 무엇이든 0건이라
「응답을 검사한다」는 검사 대상이 0건인 채로 통과한다. 이 레포의 대표 실패형이다.
**규격을 만드는 자리에 두면 대상이 0건이어도 규칙은 여전히 시험할 수 있다.**

강제하는 것 넷
  ① 확신도 `확실 | 애매 | 모름` **enum** — 숫자·퍼센트가 들어올 자리가 없다
     (`Policy §1.3-6` 「퍼센트는 쓰지 않는다」 · `§4 용어(확신도)` 「퍼센트 금지」)
  ② 근거 **필수**, nullable 아님 (`Policy §10` 「근거 없는 제안은 내놓지 않는 것이 전제다」)
  ③ 근거는 **한 줄** (`common.json#AiRationale` pattern `^[^\n\r]+$`)
  ④ 종류는 계약의 두 값뿐이고, 종류마다 required 가 다르다

**여기에 없는 것이 결정이다.**
  · 카탈로그 접속이 없다. 부모 후보를 스스로 찾지 못한다 (`〈72〉-㉮` 가 그은 분담)
  · 묶음 상태·일괄 승인 필드가 없다 (`PRD §5.2 Out-of-scope`)
  · 점수·순위·퍼센트 필드가 없다
  · 저장이 없다. 제안은 이 프로세스 안에서 태어나 응답과 함께 죽는다
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

#: `common.json#AiConfidence`. **정본을 여기서 새로 정하지 않는다** — 옮겨 적는다.
CONFIDENCE_VALUES = ("확실", "애매", "모름")
#: `core-ai.yaml LineageSuggestion.discriminator.mapping` 의 두 값.
KIND_PARENT = "가공 전 데이터"
KIND_METHOD = "가공 방식"
KINDS = (KIND_PARENT, KIND_METHOD)
#: `common.json#ParentRole` 의 기본값 (`Policy §5 부모 역할`).
DEFAULT_PARENT_ROLE = "주입력"
#: `Policy §5 가공 방식 문장 — 1~120자`.
MAX_METHOD_TEXT = 120

_ULID = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
#: `common.json#AiRationale` — 화면에서 한 줄로 서므로 줄바꿈을 허용하지 않는다.
_ONE_LINE = re.compile(r"^[^\n\r]+$")


def _ulid(name: str, value: object) -> str:
    if not isinstance(value, str) or not _ULID.match(value):
        raise ValueError(f"{name} 가 정규 ID 가 아니다 — 지어내지 않는다.")
    return value


@dataclass(frozen=True)
class Suggestion:
    """제안 카드 한 장. **규격을 어기면 객체가 서지 않는다.**"""

    suggestion_id: str
    kind: str
    confidence: str
    rationale: str
    parent_dataset_id: str | None = None
    parent_dataset_name: str | None = None
    suggested_parent_role: str = DEFAULT_PARENT_ROLE
    method_text: str | None = None
    applies_to_parent_dataset_id: str | None = None

    def __post_init__(self) -> None:
        _ulid("suggestionId", self.suggestion_id)
        if self.kind not in KINDS:
            raise ValueError(f"제안 종류가 계약 밖이다: {self.kind!r} — 허용은 {list(KINDS)}.")
        # ⚠ `bool` 을 먼저 막는다. 파이썬에서 `True` 는 `1` 이고, 숫자를 막는 검사가
        #    `isinstance(x, str)` 하나뿐이면 통과하지 않지만 순서가 뒤바뀌면 샌다.
        if not isinstance(self.confidence, str) or self.confidence not in CONFIDENCE_VALUES:
            raise ValueError(
                f"확신도가 3값 enum 밖이다: {self.confidence!r} — 허용은 {list(CONFIDENCE_VALUES)}. "
                "숫자·퍼센트는 정본이 금지했다 (`Policy §1.3-6`).")
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("근거가 없다 — 근거 없는 제안은 내놓지 않는다 (`Policy §10`).")
        if not _ONE_LINE.match(self.rationale):
            raise ValueError("근거는 한 줄이다 (`common.json#AiRationale`).")

        if self.kind == KIND_PARENT:
            _ulid("parentDatasetId", self.parent_dataset_id)
            if not isinstance(self.parent_dataset_name, str) or not self.parent_dataset_name.strip():
                raise ValueError("부모 데이터셋 이름이 없다 — 화면이 대조할 것이 없어진다.")
            if self.suggested_parent_role not in ("주입력", "보조입력"):
                raise ValueError(f"부모 역할이 계약 밖이다: {self.suggested_parent_role!r}")
            if self.method_text is not None:
                raise ValueError("가공 전 데이터 제안에 가공 방식 문장을 싣지 않는다.")
        else:
            if not isinstance(self.method_text, str) or not self.method_text.strip():
                raise ValueError("가공 방식 문장이 없다.")
            if len(self.method_text) > MAX_METHOD_TEXT:
                raise ValueError(f"가공 방식 문장은 1~{MAX_METHOD_TEXT}자다 (`Policy §5`).")
            if self.parent_dataset_id is not None:
                _ulid("parentDatasetId", self.parent_dataset_id)
            # **어느 부모인지 모르면 생략한다 — 지어내지 않는다** (계약 산문).
            if self.applies_to_parent_dataset_id is not None:
                _ulid("appliesToParentDatasetId", self.applies_to_parent_dataset_id)

    def to_dict(self) -> dict:
        """계약 모양. **없는 값은 열쇠 자체를 만들지 않는다** — 빈 값과 미지를 가르기 위해서다."""
        body: dict = {"suggestionId": self.suggestion_id, "kind": self.kind,
                      "confidence": self.confidence, "rationale": self.rationale}
        if self.kind == KIND_PARENT:
            body["parentDatasetId"] = self.parent_dataset_id
            body["parentDatasetName"] = self.parent_dataset_name
            body["suggestedParentRole"] = self.suggested_parent_role
        else:
            body["methodText"] = self.method_text
            if self.applies_to_parent_dataset_id:
                body["appliesToParentDatasetId"] = self.applies_to_parent_dataset_id
        return body


@dataclass(frozen=True)
class SuggestionEnvelope:
    """`LineageSuggestionResponse` 조립 — **세 상태로 만든다.**

      ⓐ 제안이 **있다**         전건을 타입으로 검증한다. `dict` 는 받지 않는다
      ⓑ **0건을 명시 선언**한다  통과하되 **건수와 뒤진 범위를 사유에 드러낸다**
      ⓒ **아무 선언도 없다**     실패한다. 「말하지 않은 0건」을 통과로 세지 않는다

    ⓒ 가 이 파일이 존재하는 이유의 절반이다. 제안 기능은 재료가 없으면 언제나 0건이고,
    그 0건이 조용히 통과하면 「제안하지 않았다」가 아무것도 증명하지 않는 값이 된다.
    """

    lab_id: str
    lab_name: str
    searched_count: int
    raw_data_likely: bool = False
    #: 이 응답이 소비될 자리를 적어 두는 칸. 값 자체는 응답에 실리지 않는다.
    notes: tuple[str, ...] = field(default=())

    def build(self, *, suggestions, empty_declaration: str | None = None) -> dict:
        if suggestions is None:
            raise ValueError(
                "제안 목록이 선언되지 않았다. `없다`(빈 배열)와 `말하지 않았다`(None)는 "
                "다른 사실이고, 둘을 같은 응답으로 내면 화면이 거짓말을 한다.")
        if not isinstance(suggestions, (list, tuple)):
            raise TypeError("제안 목록은 배열이다.")
        for item in suggestions:
            if not isinstance(item, Suggestion):
                raise TypeError(
                    f"제안이 타입을 지나지 않았다: {type(item).__name__}. dict 를 그대로 실으면 "
                    "확신도·근거 검사가 통째로 건너뛰어진다.")

        degraded = False
        reason: str | None = None
        if not suggestions:
            if not empty_declaration or not str(empty_declaration).strip():
                raise ValueError(
                    "제안 0건을 사유 없이 내지 않는다. 「제안하지 않았다」가 값어치를 가지려면 "
                    "무엇 때문에 0건인지가 함께 서야 한다.")
            degraded = True
            reason = (f"제안 0건 — 뒤진 범위는 {self.lab_name} 데이터 "
                      f"{self.searched_count}건이다. {str(empty_declaration).strip()}")

        # **`scope` 를 먼저 쓴다.** dict 는 삽입 순서를 지키고 json 은 그 순서로 쓴다 —
        # 「뒤진 범위를 먼저 밝힌다」가 직렬화된 바이트에서도 사실이 된다.
        body: dict = {
            "scope": {"labId": self.lab_id, "labName": self.lab_name,
                      "searchedCount": self.searched_count},
            "rawDataLikely": bool(self.raw_data_likely),
            "degraded": degraded,
            "suggestions": [s.to_dict() for s in suggestions],
        }
        if reason:
            body["degradedReason"] = reason
        return body
