"""D10 모델 호출 실행 원장 — **호출 한 번에 행 하나**.

정본 = `dev-package/intent/2026-09-24-d10-model-call-ledger.md` 「판정 기록 (2026-09-24 Ted)」.
목적은 **호출 품질·효율 모니터링**이지 질의 로그가 아니다. 그래서 이 파일의 절반은
「무엇이 적히는가」가 아니라 **「무엇이 적히지 않는가」**를 잰다.

무엇을 강제하나
  ㈎ **정확히 1행** — 성공·폴백·미호출 어느 갈래로 끝나도. 두 자리(`search.interpret` ·
     `lineage.suggest`) 다.
  ㈏ **응답은 원장과 독립이다** — 원장이 터져도 해석·제안은 그대로 나온다 (`CLAUDE.md §3`
     「AI 없이도 v2 는 완결된 제품이다」의 한 칸 아래 — 원장 없이도 AI 는 완결된다).
  ㈐ **질의 원문·검색어·데이터셋 이름이 행에 없다** — 직렬화한 값을 통째로 뒤져서 잰다.
     열쇠 목록만 보면 나중에 붙는 칸을 놓친다.
  ㈑ 캐시 토큰은 **있으면 읽고 없으면 NULL** — 0 과 「모른다」를 같은 값으로 접지 않는다.
  ㈒ **선언 ↔ 리비전 ↔ 코드 드리프트** — 세 자리가 갈리면 red (`test_topics_drift.py` 와 같은 계열).

⛔ **「행 0건」을 실패로 재는 시험을 만들지 않는다** (intent 「원한 결과」 축자). 기본 설정은
   두 자리 다 모델을 부르지 않고, 그때 원장이 비는 것이 정상이다.
"""
from __future__ import annotations

import dataclasses
import json
import logging
import pathlib
import re
import urllib.error

import pytest

from colab_ai.app.interpret import LlmQueryInterpreter
from colab_ai.app.ledger import (
    LEDGER_FAIL_EVENT,
    NullModelCallLedger,
    build_ledger,
    record_call,
)
from colab_ai.app.suggest import EmptyLineageSuggester, LlmLineageSuggester
from colab_ai.kernel.config import Settings
from colab_ai.kernel.ids import is_valid_ulid
from colab_ai.ports import (
    CALL_SITES,
    NOT_CALLED_REASONS,
    OUTCOMES,
    ModelCallEntry,
    ModelReply,
    ModelUsage,
    ParentCandidate,
)

LAB = "0000000000000000000000000A"
MODEL = "gpt-5.6-luna"


# ── 재료 ────────────────────────────────────────────────────────────────────
class FakeLedger:
    """행을 모은다. **정렬·요약하지 않는다** — 건수 자체가 판정 대상이다."""

    def __init__(self) -> None:
        self.rows: list[ModelCallEntry] = []

    def record(self, entry: ModelCallEntry) -> None:
        self.rows.append(entry)


class ExplodingLedger:
    def record(self, entry: ModelCallEntry) -> None:
        raise RuntimeError("원장 DB 가 죽었다")


def openai_body(content: str, *, model: str = "gpt-5.6-luna-2026-08-01",
                prompt: int | None = 1280, completion: int | None = 64,
                cached: int | None = 1024) -> dict:
    """실제 chat completions 응답 모양 한 벌. **여기서 형태를 새로 정하지 않는다.**"""
    usage: dict = {}
    if prompt is not None:
        usage["prompt_tokens"] = prompt
    if completion is not None:
        usage["completion_tokens"] = completion
    if cached is not None:
        usage["prompt_tokens_details"] = {"cached_tokens": cached}
    body: dict = {"model": model, "choices": [{"message": {"content": content}}]}
    if usage:
        body["usage"] = usage
    return body


def reply(content: str, **kw) -> ModelReply:
    return ModelReply.from_openai(openai_body(content, **kw))


INTERPRETED = json.dumps({"isDataQuery": True, "terms": ["낙동강", "강우"], "topic": "강우·강수"},
                         ensure_ascii=False)

CAND_A = ParentCandidate(dataset_id="00000000000000000000000AA1", name="낙동강 관측 원자료",
                         topic="강우·강수", summary="관측소 시간 강우")
CAND_B = ParentCandidate(dataset_id="00000000000000000000000BB2", name="한강 격자 강우")

#: ⭑ ⟨2026-09-24 · K3 `WU-S3`⟩ 모델은 확신도·근거 문장을 내지 않는다 — **인용까지**다.
#: 인용이 한 항목도 없으면 그 후보는 제안이 아니라서 `result_count` 가 0이 된다.
SUGGESTED = json.dumps({"suggestions": [
    {"parentDatasetId": CAND_A.dataset_id, "suggestedParentRole": "주입력",
     "evidence": [{"field": "variables", "uploadValue": "pr",
                   "candidateValue": "pr"}]}]},
    ensure_ascii=False)

FILE_META = {"fileName": "nakdong_rain_2024.nc", "kind": "본체"}


def interpreter(transport, *, ledger, api_key: str | None = "k") -> LlmQueryInterpreter:
    return LlmQueryInterpreter(api_key=api_key, model=MODEL, transport=transport,
                               ledger=ledger, lab_id=LAB)


def suggester(transport, *, ledger, api_key: str | None = "k") -> LlmLineageSuggester:
    return LlmLineageSuggester(api_key=api_key, model=MODEL, transport=transport,
                               ledger=ledger, lab_id=LAB)


def only(ledger: FakeLedger) -> ModelCallEntry:
    assert len(ledger.rows) == 1, f"호출 1회에 행 1건이어야 한다 — 실측 {len(ledger.rows)}건"
    return ledger.rows[0]


# ── ㈎ 자리 ①: search.interpret — 갈래마다 정확히 한 행 ──────────────────────
def test_해석_성공이_행_하나를_남긴다() -> None:
    led = FakeLedger()
    result = interpreter(lambda _p: reply(INTERPRETED), ledger=led).interpret("낙동강 강우")
    row = only(led)
    assert result.source == "llm"
    assert row.call_site == "search.interpret"
    assert row.outcome == "ok"
    assert row.provider == "openai"
    assert row.model_requested == MODEL
    assert row.model_returned == "gpt-5.6-luna-2026-08-01"
    assert row.not_called_reason is None
    assert row.result_count == 2                 # 검색어 수 — 낱말 자체는 싣지 않는다
    assert row.lab_id == LAB
    assert is_valid_ulid(row.id)
    assert row.latency_ms is not None and row.latency_ms >= 0


def test_해석_토큰과_캐시_토큰을_읽는다() -> None:
    led = FakeLedger()
    interpreter(lambda _p: reply(INTERPRETED), ledger=led).interpret("낙동강 강우")
    row = only(led)
    assert (row.prompt_tokens, row.completion_tokens, row.cached_prompt_tokens) == (1280, 64, 1024)


def test_캐시_토큰이_없으면_0_이_아니라_NULL_이다() -> None:
    """**0 과 「모른다」는 다른 사실이다.** 0 으로 채우면 캐시율이 0% 로 보인다."""
    led = FakeLedger()
    interpreter(lambda _p: reply(INTERPRETED, cached=None), ledger=led).interpret("낙동강 강우")
    row = only(led)
    assert row.cached_prompt_tokens is None
    assert row.prompt_tokens == 1280


def test_전송이_맨_문자열을_돌려줘도_돈다() -> None:
    """`eval/` 실측 탐침과 시험 가짜 전송은 **문자열**을 돌려준다 — 그 표면을 깨지 않는다."""
    led = FakeLedger()
    result = interpreter(lambda _p: INTERPRETED, ledger=led).interpret("낙동강 강우")
    row = only(led)
    assert result.source == "llm"
    assert row.outcome == "ok"
    assert row.model_returned is None            # 맨 문자열에는 응답 모델이 없다
    assert row.prompt_tokens is None


def test_키가_없으면_미호출_한_행이다() -> None:
    led = FakeLedger()

    def never(_payload):                         # pragma: no cover - 불려선 안 된다
        raise AssertionError("키가 없는데 모델을 불렀다")

    result = interpreter(never, ledger=led, api_key=None).interpret("낙동강 강우")
    row = only(led)
    assert result.source == "literal"
    assert row.outcome == "not_called"
    assert row.not_called_reason == "no_credentials"
    assert row.latency_ms is None                # 부르지 않았으니 잴 지연이 없다
    assert row.model_returned is None


def test_시간_초과와_못_닿음을_가른다() -> None:
    """둘 다 「답을 못 받았다」이지만 **고칠 곳이 다르다** — 접으면 그 구분이 사라진다."""
    for exc, expected in ((TimeoutError("timed out"), "timeout"),
                          (urllib.error.URLError(TimeoutError("timed out")), "timeout"),
                          (urllib.error.URLError("connection refused"), "unreachable"),
                          (OSError("broken pipe"), "unreachable")):
        led = FakeLedger()

        def boom(_payload, _e=exc):
            raise _e

        result = interpreter(boom, ledger=led).interpret("낙동강 강우")
        assert result.source == "literal"
        assert only(led).outcome == expected, exc


def test_못_읽은_답은_unreadable_이다() -> None:
    led = FakeLedger()
    result = interpreter(lambda _p: reply("이건 JSON 이 아니다"), ledger=led).interpret("낙동강")
    row = only(led)
    assert result.source == "literal"
    assert row.outcome == "unreadable"
    assert row.model_returned == "gpt-5.6-luna-2026-08-01"   # 닿긴 했다 — 그 사실은 남는다


def test_모델이_데이터_질문이_아니라_하면_empty_by_model_이다() -> None:
    led = FakeLedger()
    raw = json.dumps({"isDataQuery": False, "terms": [], "topic": None})
    result = interpreter(lambda _p: reply(raw), ledger=led).interpret("안녕")
    row = only(led)
    assert result.is_data_query is False
    assert row.outcome == "empty_by_model"
    assert row.result_count == 0


# ── ㈎ 자리 ②: lineage.suggest ──────────────────────────────────────────────
def test_제안_성공이_행_하나를_남긴다() -> None:
    led = FakeLedger()
    out = suggester(lambda _p: reply(SUGGESTED), ledger=led).suggest(
        file_meta=FILE_META, candidates=(CAND_A, CAND_B))
    row = only(led)
    assert len(out.suggestions) == 1
    assert row.call_site == "lineage.suggest"
    assert row.outcome == "ok"
    assert row.input_count == 2                  # 받은 후보 수
    assert row.result_count == 1                 # 남긴 제안 수
    assert row.cached_prompt_tokens == 1024
    assert row.lab_id == LAB


def test_후보가_없으면_부르지_않고_한_행을_남긴다() -> None:
    led = FakeLedger()

    def never(_payload):                         # pragma: no cover - 불려선 안 된다
        raise AssertionError("후보가 없는데 모델을 불렀다")

    out = suggester(never, ledger=led).suggest(file_meta=FILE_META, candidates=())
    row = only(led)
    assert out.suggestions == ()
    assert row.outcome == "not_called"
    assert row.not_called_reason == "no_candidates"
    assert row.input_count == 0


def test_제안_키가_없으면_미호출_한_행이다() -> None:
    led = FakeLedger()
    out = suggester(lambda _p: reply(SUGGESTED), ledger=led, api_key=None).suggest(
        file_meta=FILE_META, candidates=(CAND_A,))
    row = only(led)
    assert out.suggestions == ()
    assert row.outcome == "not_called"
    assert row.not_called_reason == "no_credentials"


def test_제안의_나머지_세_갈래도_각각_한_행이다() -> None:
    cases = [
        (lambda _p: (_ for _ in ()).throw(urllib.error.URLError("refused")), "unreachable"),
        (lambda _p: reply("JSON 아님"), "unreadable"),
        (lambda _p: reply(json.dumps({"suggestions": []})), "empty_by_model"),
    ]
    for transport, expected in cases:
        led = FakeLedger()
        suggester(transport, ledger=led).suggest(file_meta=FILE_META, candidates=(CAND_A,))
        row = only(led)
        assert row.outcome == expected
        assert row.input_count == 1
        assert row.result_count == 0


def test_켜려_했으나_키가_없는_조립도_한_행을_남긴다() -> None:
    """`build_suggester` 의 `llm` 갈래가 `EmptyLineageSuggester` 로 떨어지는 자리."""
    led = FakeLedger()
    out = EmptyLineageSuggester(EmptyLineageSuggester.NO_CREDENTIALS_REASON,
                                ledger=led, not_called_reason="no_credentials",
                                model="gpt-5.6-luna", lab_id=LAB).suggest(
        file_meta=FILE_META, candidates=(CAND_A,))
    row = only(led)
    assert out.suggestions == ()
    assert row.outcome == "not_called"
    assert row.not_called_reason == "no_credentials"


def test_끈_회차는_원장에_아무것도_남기지_않는다() -> None:
    """**결정으로 끈 것은 「부르지 못한 호출」이 아니다** (intent 「원한 결과」 — 게이트가
    도는 동안 행이 쌓이지 않는 것이 정상이다). 원장이 없으면 조용히 아무 일도 없다."""
    out = EmptyLineageSuggester(EmptyLineageSuggester.BY_DESIGN_REASON).suggest(
        file_meta=FILE_META, candidates=(CAND_A,))
    assert out.empty_declaration == EmptyLineageSuggester.BY_DESIGN_REASON


# ── ㈏ 원장이 터져도 응답은 산다 ────────────────────────────────────────────
def test_원장이_터져도_해석은_그대로_나온다(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="colab_ai.degraded"):
        result = interpreter(lambda _p: reply(INTERPRETED),
                             ledger=ExplodingLedger()).interpret("낙동강 강우")
    assert result.source == "llm"
    assert result.terms == ("낙동강", "강우")
    assert LEDGER_FAIL_EVENT in caplog.text


def test_원장이_터져도_제안은_그대로_나온다(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="colab_ai.degraded"):
        out = suggester(lambda _p: reply(SUGGESTED), ledger=ExplodingLedger()).suggest(
            file_meta=FILE_META, candidates=(CAND_A,))
    assert len(out.suggestions) == 1
    assert LEDGER_FAIL_EVENT in caplog.text


def test_record_call_은_어떤_예외도_새지_않게_한다(caplog: pytest.LogCaptureFixture) -> None:
    entry = ModelCallEntry(call_site="search.interpret", provider="openai",
                           model_requested=MODEL, outcome="ok")
    with caplog.at_level(logging.WARNING, logger="colab_ai.degraded"):
        record_call(ExplodingLedger(), entry)    # 던지면 이 시험이 실패한다
    assert LEDGER_FAIL_EVENT in caplog.text


def test_DB_주소가_없으면_빈_원장이고_한_번만_경고한다(caplog: pytest.LogCaptureFixture) -> None:
    ledger = build_ledger(Settings())
    assert isinstance(ledger, NullModelCallLedger)
    entry = ModelCallEntry(call_site="search.interpret", provider="openai",
                           model_requested=MODEL, outcome="ok")
    with caplog.at_level(logging.WARNING, logger="colab_ai.degraded"):
        ledger.record(entry)
        ledger.record(entry)
    assert len([r for r in caplog.records if "ledger.disabled" in r.getMessage()]) == 1


# ── ㈐ 무엇이 적히지 않는가 ─────────────────────────────────────────────────
def _serialized(entry: ModelCallEntry) -> str:
    return json.dumps(dataclasses.asdict(entry), ensure_ascii=False, default=str)


def test_해석_행에_질의_원문도_검색어도_없다() -> None:
    led = FakeLedger()
    interpreter(lambda _p: reply(INTERPRETED), ledger=led).interpret("낙동강 유역 강우 자료 줘")
    blob = _serialized(only(led))
    for forbidden in ("낙동강", "유역", "강우", "자료", "강우·강수"):
        assert forbidden not in blob, f"원장에 질의에서 온 말이 실렸다: {forbidden}"


def test_제안_행에_데이터셋_이름도_근거_문장도_파일명도_없다() -> None:
    led = FakeLedger()
    suggester(lambda _p: reply(SUGGESTED), ledger=led).suggest(
        file_meta=FILE_META, candidates=(CAND_A, CAND_B))
    blob = _serialized(only(led))
    for forbidden in ("낙동강 관측 원자료", "한강 격자 강우", "같은 유역의 관측 원자료다.",
                      "nakdong_rain_2024.nc", CAND_A.dataset_id, "확실", "주입력"):
        assert forbidden not in blob, f"원장에 도메인 데이터가 실렸다: {forbidden}"


def test_행의_칸_목록이_닫혀_있다() -> None:
    """칸이 늘면 이 시험이 먼저 red 를 낸다 — 늘리려면 선언·리비전을 함께 고치게 된다."""
    assert {f.name for f in dataclasses.fields(ModelCallEntry)} == {
        "id", "called_at", "call_site", "provider", "model_requested", "model_returned",
        "outcome", "not_called_reason", "latency_ms", "prompt_tokens", "completion_tokens",
        "cached_prompt_tokens", "input_count", "result_count", "lab_id"}


# ── ㈑ 캐시율은 **저장하지 않는다** ─────────────────────────────────────────
def test_캐시율_칸이_없다() -> None:
    """파생값은 조회 때 계산한다 — 저장하면 토큰 둘과 비율 셋이 갈릴 자리가 생긴다."""
    names = {f.name for f in dataclasses.fields(ModelCallEntry)}
    assert not [n for n in names if "ratio" in n or "rate" in n]


# ── ㈒ 드리프트 — 선언(schema.sql) ↔ 리비전 ↔ 코드 ─────────────────────────
_REPO = pathlib.Path(__file__).resolve().parents[3]
_SCHEMA = _REPO / "db" / "ai" / "schema.sql"
_REVISION = _REPO / "db" / "ai" / "versions" / "0008_d10_model_call_ledger.py"
_TABLE = "d10_model_call"


def _table_block(text: str) -> str:
    """`CREATE TABLE d10_model_call ( … )` 한 덩어리를 **SQL 만 남겨** 돌려준다.

    ⚠ **주석을 지우고 공백을 접는다.** 두 파일의 산문까지 한 글자씩 견주면 들여쓰기 한 칸에
    시험이 red 를 내고, 그 red 는 「선언과 적용이 갈렸다」가 아니다 — 이 오라클이 지켜야
    하는 것은 **DB 가 보는 것**이다. 주석은 DB 에 닿지 않는다.
    (이 DDL 의 문자열 리터럴에는 `--` 가 없다 — 있으면 이 방식이 틀린다.)
    """
    match = re.search(rf"CREATE TABLE {_TABLE} \((.*?)\n\s*\);?", text, re.S)
    assert match, f"{_TABLE} 의 CREATE TABLE 을 찾지 못했다"
    sql_only = re.sub(r"--[^\n]*", "", match.group(1))
    return re.sub(r"\s+", " ", sql_only).strip()


def _checked_values(block: str, column: str) -> tuple[str, ...]:
    """그 칸의 `… IN ( … )` 목록. `IS NULL OR` 가 앞에 붙는 칸도 같은 자리로 읽는다."""
    match = re.search(rf"(?:^|, ){column} .*?{column} IN \(([^)]*)\)", block, re.S)
    assert match, f"{column} 의 IN CHECK 를 찾지 못했다"
    return tuple(re.findall(r"'([^']+)'", match.group(1)))


def test_선언과_리비전의_DDL_이_한_글자도_다르지_않다() -> None:
    """`env.py` 가 autogenerate 를 쓰지 않으므로 **사람이 두 곳에 같은 것을 적는다** —
    갈리면 `schema-diff`·`0008-drift.sh` 가 red 를 내고, 이 시험이 그보다 먼저 낸다."""
    assert _table_block(_SCHEMA.read_text(encoding="utf-8")) == \
        _table_block(_REVISION.read_text(encoding="utf-8"))


def test_두_색인이_선언과_리비전에_다_있다() -> None:
    for text in (_SCHEMA.read_text(encoding="utf-8"), _REVISION.read_text(encoding="utf-8")):
        assert f"{_TABLE}_called_at_idx ON {_TABLE} (called_at)" in text
        assert f"{_TABLE}_site_time_idx ON {_TABLE} (call_site, called_at)" in text


def test_코드의_세_어휘가_선언_CHECK_와_같다() -> None:
    """⛔ 기대값을 여기 다시 적지 않는다 — 세 곳에 적으면 갈라진다 (`test_topics_drift` 규율)."""
    block = _table_block(_SCHEMA.read_text(encoding="utf-8"))
    assert CALL_SITES == _checked_values(block, "call_site")
    assert OUTCOMES == _checked_values(block, "outcome")
    assert NOT_CALLED_REASONS == _checked_values(block, "not_called_reason")


def test_선언의_칸_목록이_행의_칸_목록과_같다() -> None:
    block = _table_block(_SCHEMA.read_text(encoding="utf-8"))
    declared = {m.group(1) for m in re.finditer(r"(?:^|, )([a-z_]+) +(?:text|timestamptz|integer)\b",
                                                block)}
    assert declared == {f.name for f in dataclasses.fields(ModelCallEntry)}


def test_원장_표에_리전_칸이_없다() -> None:
    """2026-09-24 Ted 판정 — ㊷ 근거③의 「처리 리전 필수 기록」은 철회됐다.
    OpenAI 공개 API 가 리전을 노출하지 않아 그 칸은 **항상 미상**이 된다."""
    block = _table_block(_SCHEMA.read_text(encoding="utf-8"))
    assert "region" not in block


# ── ㈏ 표면 — 원장이 터져도 200 이다 ────────────────────────────────────────
def test_원장이_터져도_제안_표면은_200_을_낸다(caplog: pytest.LogCaptureFixture) -> None:
    """`CLAUDE.md §3` 의 한 칸 아래 — **원장 없이도 AI 는 완결된다.**"""
    from fastapi.testclient import TestClient

    from colab_ai.app.main import create_app

    client = TestClient(create_app(
        Settings(), suggester=suggester(lambda _p: reply(SUGGESTED), ledger=ExplodingLedger())))
    body = {"scope": {"labId": LAB, "labName": "A 연구실", "searchedCount": 12},
            "file": {"fileName": "rain_2024.nc", "kind": "본체"},
            "candidates": [{"datasetId": CAND_A.dataset_id, "name": CAND_A.name}]}
    with caplog.at_level(logging.WARNING, logger="colab_ai.degraded"):
        res = client.post(
            "/lineage-suggestions", json=body,
            headers={"X-CoLAB-Lab": LAB, "X-CoLAB-Account": "000000000000000000000000A1"})
    assert res.status_code == 200
    assert len(res.json()["suggestions"]) == 1
    assert LEDGER_FAIL_EVENT in caplog.text


def test_사용량_파서가_bool_과_음수를_값으로_세지_않는다() -> None:
    usage = ModelUsage.from_openai({"prompt_tokens": True, "completion_tokens": -3,
                                    "prompt_tokens_details": {"cached_tokens": "많음"}})
    assert (usage.prompt_tokens, usage.completion_tokens, usage.cached_prompt_tokens) == \
        (None, None, None)
