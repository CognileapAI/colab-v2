"""ai-service 의 **경계 표면**. 값 객체와 Protocol 만 있고 구현은 없다.

왜 값 객체가 여기 사는가
  `import-boundary` 계약 5·7 이 `app > d10 > ports > d9` 를 강제하고 **D10 은 D9 를 직접
  import 하지 못한다.** 그래서 두 층이 함께 쓰는 모양(해석 결과·매칭 행)은 **아래층인
  여기**에 산다. 조립은 `app/` 이 한다.

이 파일에 **없는 것**
  · **카탈로그 조회 표면이 없다.** `K4-a` 의 `CatalogSearchPort`·`MatchRow` 는 2026-08-25
    판정 ㈎ 로 core-api(`domains/d3_catalog.SearchMatch`)로 갔다 — D3 는 저쪽 도메인이고,
    이 단위가 그 표면을 갖고 있는 한 D10 이 D3 에 붙을 자리가 남는다 (`CLAUDE.md §3-1`).
  · 순위 규칙이 없다 — 순위는 core-api 의 `tsvector` 가 낸다 (`PLAN-SoT §9-〈72〉-㉮`).
  · 결과 본문 생성이 없다 — 이름·요약·잠김은 core-api 가 D3·D2 에서 붙인다.
  · 점수·퍼센트 필드가 없다 (`CLAUDE.md §3 AI 응답 규격`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from colab_ai.kernel.ids import new_ulid

#: 주제 고정 4값. **여기서 새로 정하는 것이 아니라** 두 정본(`db/ai/schema.sql`
#: `d9_topic_synonym.topic` CHECK · `db/platform/schema.sql` `d3_dataset_description`
#: CHECK)이 같은 값을 각각 적어 둔 것을 코드 쪽에 한 번 더 옮긴 것이다 (`㊸-④-2`).
TOPICS = ("강우·강수", "식생·NDVI", "지형·DEM", "토지피복·LULC",
          "가뭄", "파일 포맷 예제")


@dataclass(frozen=True)
class Interpretation:
    """자연어 질의 → **검색어·필터**. LLM 의 일은 여기까지다 (`〈72〉-㉮`).

    `source` 가 `"literal"` 이면 모델이 아니라 문자열 분해가 만든 것이다 —
    **그래도 검색은 돈다.** 그 사실을 `degraded` 로 정직하게 말한다.
    """
    is_data_query: bool
    terms: tuple[str, ...]
    topic: str | None
    source: str                      # "llm" | "literal"
    degraded: bool
    degraded_reason: str | None


class QueryInterpreterPort(Protocol):
    """질의 해석기. **실패해도 예외를 던지지 않는다** — 문자열 해석으로 떨어진다."""

    def interpret(self, query: str) -> Interpretation:
        ...


class DictionaryPort(Protocol):
    """D9 사전 3종 조회. D10 은 이 표면으로만 지식을 읽는다 (`DOMAINS §2`)."""

    def expand(self, terms: tuple[str, ...], query: str):
        ...


# ── 계보 제안 (`R-K3-RESUME WU2`) ───────────────────────────────────────────
@dataclass(frozen=True)
class ParentCandidate:
    """**core-api 가 D3 에서 골라 실어 보낸 후보 한 건** (`core-ai.yaml LineageParentCandidate`).

    찾는 것은 D3 의 주인이고 매기는 것만 이쪽이다 (`〈72〉-㉮` 검색과 같은 분담).
    이 단위는 카탈로그에 닿지 않으므로 **스스로 후보를 만들 수 없다** — 그것이
    「후보 밖 ID 를 제안하지 않는다」가 코드에서 참이 되는 이유다.

    ⚠ **모르는 값은 `None` 이고 모델에게 열쇠 자체를 만들어 주지 않는다.** 빈 문자열이나
    `0` 으로 채우면 「못 읽음」과 「값 없음」이 갈리지 않고, 그 둘은 다른 사실이다.
    """

    dataset_id: str
    name: str
    topic: str | None = None
    summary: str | None = None
    source_label: str | None = None
    processing_level: int | None = None
    period_start: str | None = None
    period_end: str | None = None
    #: ⭑ ⟨2026-09-24 · K3 `WU-S0`⟩ `d3_dataset_autometa` 의 **날값 그대로**.
    #: 겹침·교집합 같은 파생 신호는 오지 않는다 — 그것을 보내면 모델이 베껴 돌려주고
    #: core-api 가 자기가 보낸 값을 자기가 검증하게 된다(라운드 열린 권고 ① 채택).
    #: **표면이 받아 여기까지 싣는 것이 이 회차의 일이다** — 본문 조립은 `WU-S3` 가 연다.
    crs: str | None = None
    grid: str | None = None
    variables: tuple[str, ...] | None = None
    file_name: str | None = None


@dataclass(frozen=True)
class SuggestionOutcome:
    """제안 생산자의 답 한 벌.

    ⚠ **왜 `list | None` 이 아닌가.** 라운드 초안은 「못 하면 `None`」이라고 적었는데,
    `None` 하나로는 **왜 0건인지**가 사라진다 — 「살펴볼 후보가 없다」·「켜지 않았다」·
    「닿지 못했다」는 사용자에게 다른 사실이고, `SuggestionEnvelope.build` 는 0건에
    사유를 **요구한다**(`d10_suggestion:161-168`). 그래서 `None` 은 파서 안쪽에만 두고
    (읽지 못한 답 = `None`), 표면으로는 사유를 지고 나온다 —
    `Interpretation` 이 `degraded_reason` 을 지고 나오는 것과 같은 모양이다.

    `suggestions` 는 `d10_suggestion.Suggestion` 들이다. **이 층은 그 형태를 모른다** —
    `import-boundary` 가 `app > d10 > ports` 를 강제하므로 아래층인 여기가 위층을
    import 하지 않는다. 조립은 `app/` 이 한다.
    """

    suggestions: tuple = ()
    #: 0건일 때의 사유. 제안이 있으면 `None` 이다.
    empty_declaration: str | None = None


class LineageSuggesterPort(Protocol):
    """계보 제안 생산자. **예외를 던지지 않는다** — 못 하면 빈 제안 + 사유다.

    모델이 하는 일은 **받은 후보의 순위·근거 한 줄·3값 확신도**까지다 (`〈72〉-㉮`).
    """

    def suggest(self, *, file_meta: dict, candidates: tuple[ParentCandidate, ...],
                dataset_name_draft: str | None = None,
                subject: str | None = None,
                processing_level: int | None = None) -> SuggestionOutcome:
        ...


# ── 모델 호출 실행 원장 (intent `2026-09-24-d10-model-call-ledger`) ─────────
#: 원장이 아는 **호출 지점 둘**. 선언 정본은 `db/ai/schema.sql` 의 `call_site` CHECK 이고
#: 여기는 그 정본을 코드 쪽에 한 번 옮겨 적은 것이다 (`TOPICS` 와 같은 규율).
#: 두 곳이 갈리면 `tests/test_model_call_ledger.py` 의 드리프트 시험이 red 를 낸다.
CALL_SITE_INTERPRET = "search.interpret"
CALL_SITE_SUGGEST = "lineage.suggest"
CALL_SITES = (CALL_SITE_INTERPRET, CALL_SITE_SUGGEST)

#: 호출 한 번이 끝난 모양 여섯. **`not_called` 를 따로 두는 것이 이 목록의 요지다** —
#: 「불렀는데 빈 답」(`empty_by_model`)과 「아예 안 불렀다」는 다른 사실이고,
#: 접으면 「왜 안 불렀나」가 원장에서 사라진다 (판정 기록 축자).
OUTCOMES = ("ok", "timeout", "unreachable", "unreadable", "empty_by_model", "not_called")

#: `not_called` 의 사유 — **안정된 코드**다. 자유 문장을 넣지 않는다:
#: 문구가 바뀌면 같은 사유가 두 값이 되고 집계가 조용히 갈린다.
REASON_NO_CREDENTIALS = "no_credentials"
REASON_NO_CANDIDATES = "no_candidates"
REASON_MODE_OFF = "mode_off"
NOT_CALLED_REASONS = (REASON_NO_CREDENTIALS, REASON_NO_CANDIDATES, REASON_MODE_OFF)

#: 공급자. 오늘 하나뿐이지만 **칸을 둔다** — 어댑터를 갈면(㊷ 근거④) 과거 행이 어느
#: 공급자의 것인지 알 수 없게 된다.
PROVIDER_OPENAI = "openai"


def _count(value: object) -> int | None:
    """**셀 수 있는 수만 센다.** `bool` 은 `int` 의 하위형이라 명시적으로 뺀다 —
    `True` 가 토큰 1건으로 적히면 아무도 그것을 찾지 못한다."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


@dataclass(frozen=True)
class ModelUsage:
    """응답이 실어 보낸 토큰 계수. **모르는 값은 0 이 아니라 `None`** 이다."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    #: OpenAI `usage.prompt_tokens_details.cached_tokens`. 안 실려 오면 `None` —
    #: 0 으로 채우면 「캐시가 안 걸렸다」와 「공급자가 안 알려줬다」가 같은 값이 된다.
    cached_prompt_tokens: int | None = None

    @classmethod
    def from_openai(cls, body: object) -> "ModelUsage":
        if not isinstance(body, dict):
            return cls()
        details = body.get("prompt_tokens_details")
        cached = details.get("cached_tokens") if isinstance(details, dict) else None
        return cls(prompt_tokens=_count(body.get("prompt_tokens")),
                   completion_tokens=_count(body.get("completion_tokens")),
                   cached_prompt_tokens=_count(cached))


class ModelReply(str):
    """전송의 답 — **본문 문자열 그대로**이고, 호출 메타가 얹혀 있다.

    ⭑ **왜 `str` 의 하위형인가.** 전송 표면은 `Callable[[dict], str]` 이고 그것을 감싸는
    자리가 제품 밖에도 있다 — `eval/k4-search/llm_interpreter_probe.py` 와
    `eval/k3-lineage/llm_lineage_probe.py` 의 기록 전송이 답을 `raw` 로 그대로 들고
    `json.dumps` 한다. 별도 객체로 바꾸면 그 두 벌이 조용히 깨지고, 실측 탐침이
    깨진 것은 게이트가 잡지 못한다. `str` 을 물려받으면 **기존 소비자는 한 글자도
    고치지 않고** 새 소비자만 `model`·`usage` 를 본다.

    맨 문자열을 돌려주는 전송(가짜 전송·탐침)에는 이 메타가 없다 — 그때는 `None` 이고,
    그것이 「0 건」이 아니라 「모른다」로 원장에 남는다.
    """

    model: str | None
    usage: ModelUsage | None

    def __new__(cls, content: str, *, model: str | None = None,
                usage: ModelUsage | None = None) -> "ModelReply":
        obj = super().__new__(cls, content)
        obj.model = model
        obj.usage = usage
        return obj

    @classmethod
    def from_openai(cls, body: dict) -> "ModelReply":
        """chat completions 본문 한 벌 → 본문 문자열 ＋ 호출 메타.

        ⚠ `choices[0].message.content` 가 없으면 **여기서 터진다** — 호출자가 이미
        `KeyError`·`IndexError` 를 잡아 `unreachable` 로 떨어뜨린다(전송 실패와 같은 칸).
        """
        content = body["choices"][0]["message"]["content"]
        model = body.get("model")
        return cls(content,
                   model=model.strip() if isinstance(model, str) and model.strip() else None,
                   usage=ModelUsage.from_openai(body.get("usage")))


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ModelCallEntry:
    """실행 원장 한 행. **선언 정본은 `db/ai/schema.sql` 의 `d10_model_call`** 이다.

    **여기 없는 것이 판정의 실물이다** (판정 기록 「넣지 않는 것」 축자) —
    질의 원문 · 검색어 · 데이터셋 이름 · 근거 문장 · API 키 · **처리 리전**.
    남는 것은 전부 **세는 값**이다: 무엇을 물었는지가 아니라 몇 개를 주고 몇 개를 받았는지.

    `cache_hit_ratio` 칸이 없는 것도 같은 규율이다 — 파생값은 **조회 때 계산한다**
    (`schema.sql` 의 조회 예시). 저장하면 토큰 둘과 비율 하나가 갈릴 자리가 생기고,
    갈렸을 때 어느 쪽이 사실인지 아무도 모른다.
    """

    call_site: str
    provider: str
    model_requested: str
    outcome: str
    id: str = field(default_factory=new_ulid)
    called_at: datetime = field(default_factory=_now)
    model_returned: str | None = None
    not_called_reason: str | None = None
    latency_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cached_prompt_tokens: int | None = None
    #: 입력 규모 — 제안은 받은 후보 수다. 해석에는 `None` 이다: 그 자리의 입력은
    #: **질의 그 자체**이고, 그것을 세는 것은 질의를 재는 것이라 담지 않는다.
    input_count: int | None = None
    #: 결과 수 — 해석은 검색어 수, 제안은 남긴 제안 수. **값이 아니라 개수다.**
    result_count: int | None = None
    lab_id: str | None = None


class ModelCallLedgerPort(Protocol):
    """호출 한 번에 행 하나. **응답 경로에서 분리된다** — 이 표면이 터져도 검색·제안은 산다.

    구현은 `app/ledger.py` 에 둘 있다 — SQL 한 줄 쓰기와, 주소가 없을 때의 빈 원장.
    """

    def record(self, entry: ModelCallEntry) -> None:
        ...
