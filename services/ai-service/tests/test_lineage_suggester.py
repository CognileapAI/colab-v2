"""계보 제안 생산자 — **가짜 전송으로만 돈다. 모델 호출 0회.**

`R-K3-STRUCTURE.md WU-S3`. 이 파일이 지키는 것은 하나다 — **LLM 은 판정하지 않는다.**
core-api 가 골라 보낸 후보에 **근거를 인용하는 것까지**가 모델의 몫이고, 확신도·근거
문장·점수·순위는 **묻지도 읽지도 않는다**(판정 기록 2회차 4 — 정본은 core-api 가 쓴다).
그 밖의 것(후보 밖 ID·새 이름)도 **읽지 않고 버린다**
(`app/interpret.py` 의 「세 값만 읽는다」 규율을 제안에 옮긴 것).

⚠ **게이트에서 모델을 부르지 않는다.** 전송은 전부 주입된 가짜다.
"""
from __future__ import annotations

import json
import logging
import pathlib
import urllib.error

import pytest
from colab_ai.app.suggest import (
    SYSTEM_PROMPT,
    EmptyLineageSuggester,
    LlmLineageSuggester,
)
from colab_ai.app.suggest_wire import (
    CALL_EVENT,
    MAX_CANDIDATE_SOURCE_LABEL,
    MAX_CANDIDATE_SUMMARY,
    SUGGESTER_LOGGER,
)
from colab_ai.domains.d10_suggestion import (
    CONFIDENCE_VALUES,
    EVIDENCE_FIELDS,
    KIND_PARENT,
    MAX_EVIDENCE,
    MAX_EVIDENCE_VALUE,
    PLACEHOLDER_CONFIDENCE,
    PLACEHOLDER_RATIONALE,
    Suggestion,
)
from colab_ai.kernel.config import Settings
from colab_ai.ports import ParentCandidate

P1 = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
P2 = "01ARZ3NDEKTSV4RRFFQ69G5FB0"
P3 = "01ARZ3NDEKTSV4RRFFQ69G5FB1"
OUTSIDE = "01ARZ3NDEKTSV4RRFFQ69G5FZZ"

FILE_META = {"fileName": "rain_2024_crop.nc", "kind": "본체", "format": "NetCDF",
             "variables": ["pr"]}


def _candidates() -> tuple[ParentCandidate, ...]:
    return (
        ParentCandidate(dataset_id=P1, name="강수 — 원자료", topic="강우·강수",
                        summary="기상청 AWS 일강수량", source_label="기상청",
                        processing_level=0),
        ParentCandidate(dataset_id=P2, name="DEM — 한반도"),
        ParentCandidate(dataset_id=P3, name="식생 지수", topic="식생·NDVI"),
    )


class FakeTransport:
    """모델 자리에 앉는 가짜. **부른 횟수와 본문을 기억한다.**"""

    def __init__(self, reply: str = "", raises: BaseException | None = None) -> None:
        self.reply, self.raises = reply, raises
        self.payloads: list[dict] = []

    def __call__(self, payload: dict) -> str:
        self.payloads.append(payload)
        if self.raises is not None:
            raise self.raises
        return self.reply

    @property
    def calls(self) -> int:
        return len(self.payloads)


def _suggester(transport: FakeTransport | None = None, *, api_key: str | None = "sk-테스트"):
    return LlmLineageSuggester(api_key=api_key, model="gpt-5.6-luna",
                               transport=transport, timeout_seconds=8.0)


def _reply(*items: dict) -> str:
    return json.dumps({"suggestions": list(items)}, ensure_ascii=False)


#: 「열쇠 자체가 없다」와 「빈 값을 보냈다」를 가르기 위한 자리 표시.
_MISSING = object()


def _ev(field: str = "variables", up: str = "pr", cand: str = "pr") -> dict:
    """모델이 인용한 근거 한 항목."""
    return {"field": field, "uploadValue": up, "candidateValue": cand}


def _item(parent_id: str = P1, *, evidence=_MISSING, **over) -> dict:
    """**새 출력 모양 한 장** — 확신도·근거 문장을 묻지 않는다."""
    item = {"parentDatasetId": parent_id, "suggestedParentRole": "주입력",
            "evidence": [_ev()] if evidence is _MISSING else evidence}
    item.update(over)
    return item


def _run(transport: FakeTransport, *, candidates=None, **over):
    kw = {"file_meta": FILE_META, "dataset_name_draft": "강수 crop 표본", "subject": None,
          "processing_level": 1}
    kw.update(over)
    return _suggester(transport).suggest(
        candidates=_candidates() if candidates is None else candidates, **kw)


# ── 고른다 · 버린다 ─────────────────────────────────────────────────────────
def test_인용_근거를_지고_온_후보가_제안으로_선다() -> None:
    t = FakeTransport(_reply(_item(
        P1, evidence=[_ev("fileName", "rain_2024_crop.nc", "rain_2024.nc")])))
    out = _run(t)
    assert len(out.suggestions) == 1
    one = out.suggestions[0]
    assert isinstance(one, Suggestion), "dict 를 그대로 실으면 확신도·근거 검사가 통째로 건너뛰어진다"
    assert one.kind == KIND_PARENT
    assert one.parent_dataset_id == P1
    # **이름은 모델이 아니라 후보에서 온다** — 정본값은 D3 에 있고 모델이 고쳐 쓸 자리가 아니다.
    assert one.parent_dataset_name == "강수 — 원자료"
    assert one.parent_processing_level == 0
    assert one.evidence == ({"field": "fileName", "uploadValue": "rain_2024_crop.nc",
                             "candidateValue": "rain_2024.nc"},)
    assert out.empty_declaration is None


def test_확신도와_근거_문장은_상수_자리채움이다() -> None:
    """**모델이 만든 값이 아니다**(판정 기록 2회차 4). 계약 required 를 채울 뿐이고
    정본은 core-api 가 검증된 근거로 다시 쓴다 — 여기서 잠정값을 *계산*하지도 않는다."""
    one = _run(FakeTransport(_reply(_item()))).suggestions[0]
    assert one.confidence == PLACEHOLDER_CONFIDENCE
    assert one.rationale == PLACEHOLDER_RATIONALE
    assert PLACEHOLDER_CONFIDENCE in CONFIDENCE_VALUES, "계약 enum 밖이면 객체가 서지 않는다"
    # 인용 개수가 몇이든 자리채움은 **같은 값**이다 — 세는 일은 core-api 가 한다.
    two = _run(FakeTransport(_reply(_item(evidence=[
        _ev("crs", "EPSG:4326", "EPSG:4326"), _ev("variables", "pr", "pr")])))).suggestions[0]
    assert (two.confidence, two.rationale) == (one.confidence, one.rationale)


def test_모델이_보낸_확신도와_근거_문장을_읽지_않는다() -> None:
    """물으면 모델이 답하고, 답한 값은 누군가 언젠가 읽는다 (`WU-S3` 축자)."""
    t = FakeTransport(_reply(_item(
        confidence="확실", rationale="모델이 스스로 쓴 근거 문장이다",
        score=0.93, rank=1, parentDatasetName="모델이 지어낸 이름")))
    one = _run(t).suggestions[0]
    assert one.confidence == PLACEHOLDER_CONFIDENCE
    assert one.parent_dataset_name == "강수 — 원자료"
    blob = json.dumps(one.to_dict(), ensure_ascii=False)
    for forbidden in ("모델이 스스로 쓴 근거 문장이다", "모델이 지어낸 이름",
                      "score", "rank", "confidencePercent"):
        assert forbidden not in blob, f"모델의 «{forbidden}» 가 살아남았다"


def test_후보_밖_ID_는_그_제안만_버려진다() -> None:
    """**전체가 아니라 그 한 장이다.** 한 장이 틀렸다고 맞은 장까지 버리지 않는다."""
    t = FakeTransport(_reply(
        _item(OUTSIDE), _item(P2, evidence=[_ev("grid", "0.25도", "0.25도")])))
    out = _run(t)
    assert [s.parent_dataset_id for s in out.suggestions] == [P2]


@pytest.mark.parametrize("bad", [
    _item(P1, suggestedParentRole="참고"),
    _item(P1, evidence=[]),
    _item(P1, evidence=None),
    _item(P1, evidence="period"),
    _item(P1, evidence={"field": "crs"}),
    _item(P1, evidence=[_ev("주제", "강우·강수", "강우·강수")]),
    _item(P1, evidence=[{"field": "crs", "uploadValue": "EPSG:4326"}]),
    _item(P1, evidence=[_ev("crs", "EPSG:4326", 4326)]),
    _item(P1, evidence=[_ev("crs", "   ", "EPSG:4326")]),
    _item(P1, evidence=[_ev("crs", "가" * (MAX_EVIDENCE_VALUE + 1), "EPSG:4326")]),
])
def test_규격을_어긴_제안은_그_장만_버려진다(bad: dict) -> None:
    """`d10_suggestion` 의 생성자 검사를 **다시 적지 않고 그대로 쓴다**(`:65-78`).
    인용이 한 항목도 살아남지 못한 후보는 **제안이 아니다**(계약 산문 축자)."""
    t = FakeTransport(_reply(bad, _item(P2, evidence=[_ev("crs", "EPSG:4326", "EPSG:4326")])))
    out = _run(t)
    assert [s.parent_dataset_id for s in out.suggestions] == [P2]


def test_근거_항목_하나가_규격을_어기면_그_항목만_빠진다() -> None:
    """**항목 단위로 버린다** — 한 항목이 틀렸다고 맞은 항목까지 버리지 않는다.
    그러나 남은 항목이 0이면 그 후보는 제안이 아니다(위 시험)."""
    t = FakeTransport(_reply(_item(P1, evidence=[
        _ev("주제", "강우·강수", "강우·강수"),               # enum 밖 축
        _ev("crs", "EPSG:4326", "EPSG:4326"),                 # 성한 항목
        {"field": "period", "uploadValue": "2024-01-01"},     # 열쇠가 모자라다
        _ev("variables", "pr", 7),                            # 값이 문자열이 아니다
        "fileName",                                           # 항목이 객체가 아니다
    ])))
    one = _run(t).suggestions[0]
    assert [e["field"] for e in one.evidence] == ["crs"]


def test_근거_항목의_계약_밖_열쇠는_실려_나가지_않는다() -> None:
    """근거 항목도 `additionalProperties: false` 다 — 그대로 실어 보내면 core-api 표면이
    계약 밖 열쇠로 되튄다."""
    t = FakeTransport(_reply(_item(P1, evidence=[
        dict(_ev("crs", "EPSG:4326", "EPSG:4326"), score=0.9, verified=True)])))
    one = _run(t).suggestions[0]
    assert set(one.evidence[0]) == {"field", "uploadValue", "candidateValue"}


def test_인용_근거는_계약_상한에서_멈춘다() -> None:
    """축이 5개다 — 같은 축을 여러 번 인용해 채우지 못한다(계약 `maxItems: 5`)."""
    many = [_ev(f, "가", "가") for f in EVIDENCE_FIELDS] + [_ev("crs", "나", "나")]
    one = _run(FakeTransport(_reply(_item(P1, evidence=many)))).suggestions[0]
    assert len(one.evidence) == MAX_EVIDENCE == 5


def test_근거가_0건인_답은_빈_제안과_사유가_된다() -> None:
    """모델이 **모른다고 말한 것**이다 — 답을 못 읽은 것과 다르다."""
    out = _run(FakeTransport(_reply(_item(P1, evidence=[]), _item(P2, evidence=[]))))
    assert out.suggestions == ()
    assert out.empty_declaration == LlmLineageSuggester.NO_MATCH_REASON


# ── 못 하면 빈 제안 · 예외를 던지지 않는다 ──────────────────────────────────
@pytest.mark.parametrize("raw", ["", "이건 JSON 이 아니다", "[]", '{"items": []}',
                                 '{"suggestions": "셋"}', "null"])
def test_읽지_못한_답은_빈_제안과_사유가_된다(raw: str) -> None:
    out = _run(FakeTransport(raw))
    assert out.suggestions == ()
    assert out.empty_declaration == LlmLineageSuggester.UNREADABLE_REASON


@pytest.mark.parametrize("exc", [urllib.error.URLError("boom"), TimeoutError("느리다"),
                                 OSError("끊겼다"), ValueError("깨졌다")])
def test_전송이_실패해도_예외가_아니라_안정된_사유가_나온다(exc: BaseException) -> None:
    out = _run(FakeTransport(raises=exc))
    assert out.suggestions == ()
    assert out.empty_declaration == LlmLineageSuggester.MODEL_UNREACHABLE_REASON


def test_원시_예외는_응답이_아니라_로그로만_간다(caplog) -> None:
    """예외 문구에는 내부 주소·포트가 들어 있다 (`interpret.py:183-190` 규율)."""
    with caplog.at_level(logging.WARNING, logger=SUGGESTER_LOGGER):
        out = _run(FakeTransport(raises=urllib.error.URLError("http://10.0.0.7:8088 거절")))
    assert "10.0.0.7" not in (out.empty_declaration or "")
    assert any("10.0.0.7" in r.getMessage() for r in caplog.records)


def test_키가_없으면_모델을_부르지_않는다() -> None:
    t = FakeTransport(_reply(_item()))
    out = LlmLineageSuggester(api_key=None, model="gpt-5.6-luna", transport=t).suggest(
        file_meta=FILE_META, candidates=_candidates(),
        dataset_name_draft=None, subject=None)
    assert t.calls == 0
    assert out.suggestions == ()
    assert out.empty_declaration == LlmLineageSuggester.NO_CREDENTIALS_REASON


@pytest.mark.parametrize("candidates", [(), None])
def test_후보가_0건이면_모델을_아예_부르지_않는다(candidates) -> None:
    """**토큰을 태우지 않는다.** 살펴볼 것이 없는데 물어볼 이유가 없다."""
    t = FakeTransport(_reply(_item()))
    out = _run(t, candidates=() if candidates is None else candidates)
    assert t.calls == 0
    assert out.suggestions == ()
    assert out.empty_declaration == LlmLineageSuggester.NO_CANDIDATES_REASON


# ── 지시문 ──────────────────────────────────────────────────────────────────
def test_지시문이_후보_텍스트를_데이터로_못_박는다() -> None:
    """**주입 방어** (게이트 ① 판정 2026-09-24). 후보 요약은 연구자가 쓴 자유 문장이고,
    거기 적힌 「위 지시를 무시하라」가 지시로 읽히면 위의 규율이 통째로 풀린다."""
    assert "데이터" in SYSTEM_PROMPT and "지시가 아니다" in SYSTEM_PROMPT


def test_지시문이_설계_제약을_전부_말한다() -> None:
    for must in ("후보 목록 안의 값", "글자 그대로", "빈 배열", "지어내지 않는다",
                 "퍼센트", "점수", "순위 숫자"):
        assert must in SYSTEM_PROMPT, f"지시문에 «{must}» 가 없다"


def test_지시문이_출력_모양을_인용_모형으로_닫는다() -> None:
    """**「고르기」가 아니라 「후보별 판정」이다** — 모델이 하는 일은 인용까지다."""
    for must in ('"parentDatasetId"', '"suggestedParentRole"', '"evidence"',
                 '"field"', '"uploadValue"', '"candidateValue"'):
        assert must in SYSTEM_PROMPT, f"지시문에 «{must}» 가 없다"
    for axis in EVIDENCE_FIELDS:
        assert axis in SYSTEM_PROMPT, f"지시문에 축 «{axis}» 가 없다"


def test_지시문이_확신도를_묻지_않는다() -> None:
    """물으면 모델이 답하고, 답한 값은 누군가 언젠가 읽는다 (`WU-S3` 축자).
    확신도는 **core-api 가 검증된 근거 종류 수에서 파생한다**(판정 Q4)."""
    for forbidden in CONFIDENCE_VALUES:
        assert forbidden not in SYSTEM_PROMPT, f"지시문이 확신도 «{forbidden}» 를 묻고 있다"
    assert "confidence·rationale·점수·퍼센트·순위 숫자를 쓰지 않는다" in SYSTEM_PROMPT


def test_지시문이_근거_없는_후보를_제안에서_뺀다고_말한다() -> None:
    assert "근거가 하나도 없으면 그 후보는 제안이 아니다 — 빈 배열이 정답이다." in SYSTEM_PROMPT


def test_지시문이_기권과_가공단계_두_문장을_그대로_말한다() -> None:
    """**순위 도구이지 보장이 아니다** (intent `2026-09-24-k3-abstention-by-structure` Q1).

    두 차례 실측에서 대조군 8회 중 7회가 비지 않았다 — 1차는 자기 자신, 2차는 자기 자식
    (상위 가공 단계)을 골랐다. 「없다」의 보장은 후보 층·인용 검증이 맡고(Q1), 이 두 문장은
    같은 후보 집합 안에서 **순위 품질**을 올리는 자리다. 문구가 바뀌면 재실측 수치와
    대조할 수 없으므로 원문 그대로 못 박는다.

    ⚠ 두 번째 문장의 기준값이 **이름 초안에서 요청의 `processingLevel` 로 바뀌었다**
    (`WU-S0` 가 그 필드를 열었다 · 판정 Q2). 이름에 적힌 「(Lv.1)」 을 읽는 것은
    사람이 고른 값을 추측하는 것이고, 고른 값이 본문에 실리는 지금은 추측할 이유가 없다.
    """
    for must in (
        "후보 중 어느 것도 이 자료를 만드는 데 쓰였다는 근거가 후보 메타·파일 메타에 "
        "없으면 suggestions 를 빈 배열로 둔다.",
        "가공 단계(processingLevel)가 받은 본문의 processingLevel 보다 높은 후보는 "
        "부모가 아니다 — 고르지 않는다.",
    ):
        assert must in SYSTEM_PROMPT, f"지시문에 «{must}» 가 없다"


def test_지시문이_퍼센트_예시를_스스로_쓰지_않는다() -> None:
    assert "%" not in SYSTEM_PROMPT


# ── 전송 본문 ───────────────────────────────────────────────────────────────
def test_전송_본문이_해석기와_같은_모양이다() -> None:
    t = FakeTransport(_reply())
    _run(t)
    payload = t.payloads[0]
    assert payload["model"] == "gpt-5.6-luna"
    assert payload["response_format"] == {"type": "json_object"}
    assert isinstance(payload["seed"], int), "회차 간 같은 seed 를 고정한다"
    # `gpt-5.6-luna` 가 `temperature: 0` 을 400 으로 거부한다(2026-08-26 실측).
    assert "temperature" not in payload
    assert payload["messages"][0] == {"role": "system", "content": SYSTEM_PROMPT}


def test_후보는_지시문이_아니라_데이터로_실린다() -> None:
    t = FakeTransport(_reply())
    _run(t)
    user = t.payloads[0]["messages"][1]
    assert user["role"] == "user"
    body = json.loads(user["content"])
    assert [c["datasetId"] for c in body["candidates"]] == [P1, P2, P3]
    # **모르는 값은 열쇠를 만들지 않는다** — 미지와 빈 값을 가른다(계약 산문과 같은 규율).
    assert set(body["candidates"][1]) == {"datasetId", "name"}
    assert body["file"] == FILE_META


def test_업로드_가공단계가_본문에_실린다() -> None:
    """사람이 등록 폼 ① 에서 고른 값이다. **필터는 core-api 가 건다** — 여기서는
    순위 문장이 읽을 기준값으로만 싣는다(계약 산문 축자)."""
    t = FakeTransport(_reply())
    _run(t, processing_level=1)
    assert json.loads(t.payloads[0]["messages"][1]["content"])["processingLevel"] == 1


def test_가공단계를_안_골랐으면_본문에_열쇠가_없다() -> None:
    """**`0` 으로 채우면 「Lv0 이다」로 읽힌다** — 미지와 Lv0 은 다른 사실이다."""
    t = FakeTransport(_reply())
    _run(t, processing_level=None)
    body = json.loads(t.payloads[0]["messages"][1]["content"])
    assert "processingLevel" not in body


def test_후보의_원메타_네_축이_본문까지_흐른다() -> None:
    """`WU-S0` 가 계약에 연 날값이다. 여기서 떨어뜨리면 **모델이 대조할 값을 못 보고도
    아무도 못 센다** — 기간 축(`test_후보의_기간이_본문까지_흐른다`)과 같은 사유."""
    rich = ParentCandidate(dataset_id=P1, name="강수 — 원자료", crs="EPSG:4326",
                           grid="0.25도 격자", variables=("pr", "lat"),
                           file_name="rain_2024.nc")
    t = FakeTransport(_reply())
    _run(t, candidates=(rich,))
    body = json.loads(t.payloads[0]["messages"][1]["content"])["candidates"][0]
    assert body["crs"] == "EPSG:4326"
    assert body["grid"] == "0.25도 격자"
    assert body["variables"] == ["pr", "lat"]
    assert body["fileName"] == "rain_2024.nc"


def test_후보_요약이_상한에서_잘린다() -> None:
    """상한이 없으면 연구자가 쓴 긴 설명이 본문을 통째로 부풀린다(게이트 ① 판정)."""
    long = ParentCandidate(dataset_id=P1, name="강수", summary="가" * 900)
    t = FakeTransport(_reply())
    _run(t, candidates=(long,))
    summary = json.loads(t.payloads[0]["messages"][1]["content"])["candidates"][0]["summary"]
    assert len(summary) == MAX_CANDIDATE_SUMMARY == 200


# ── 로그 한 줄 ──────────────────────────────────────────────────────────────
def test_호출_한_번에_계수_한_줄이_남는다(caplog) -> None:
    """모델·지연·후보 수·제안 수·결과 (게이트 ① 판정 2026-09-24)."""
    t = FakeTransport(_reply(_item()))
    with caplog.at_level(logging.INFO, logger=SUGGESTER_LOGGER):
        _run(t)
    lines = [r.getMessage() for r in caplog.records if CALL_EVENT in r.getMessage()]
    assert len(lines) == 1, f"호출 1회에 계수 줄이 {len(lines)}개다"
    for field in ("model=gpt-5.6-luna", "latency_ms=", "candidates=3",
                  "suggestions=1", "outcome=ok"):
        assert field in lines[0], f"계수 줄에 «{field}» 가 없다: {lines[0]}"


def test_부르지_않은_회차에는_계수_줄이_없다(caplog) -> None:
    with caplog.at_level(logging.INFO, logger=SUGGESTER_LOGGER):
        _run(FakeTransport(_reply()), candidates=())
    assert not [r for r in caplog.records if CALL_EVENT in r.getMessage()]


def test_실패한_호출도_계수_한_줄을_남긴다(caplog) -> None:
    with caplog.at_level(logging.INFO, logger=SUGGESTER_LOGGER):
        _run(FakeTransport(raises=TimeoutError("느리다")))
    lines = [r.getMessage() for r in caplog.records if CALL_EVENT in r.getMessage()]
    assert len(lines) == 1
    assert "outcome=unreachable" in lines[0] and "suggestions=0" in lines[0]


# ── 끈 쪽 생산자 ────────────────────────────────────────────────────────────
def test_빈_생산자는_모델_자리를_아예_갖지_않는다() -> None:
    out = EmptyLineageSuggester(EmptyLineageSuggester.BY_DESIGN_REASON).suggest(
        file_meta=FILE_META, candidates=_candidates(),
        dataset_name_draft=None, subject=None)
    assert out.suggestions == ()
    assert out.empty_declaration == EmptyLineageSuggester.BY_DESIGN_REASON


def test_결정으로_고른_상태를_고장으로_말하지_않는다() -> None:
    """사용자가 읽는 문장이다 (`LiteralInterpreter.BY_DESIGN_REASON` 과 같은 규율)."""
    reason = EmptyLineageSuggester.BY_DESIGN_REASON
    for broken in ("실패", "무너", "오류", "닿지 못", "못 했"):
        assert broken not in reason, f"결정을 고장으로 말하고 있다: {reason}"


def test_사유_어디에도_퍼센트가_없다() -> None:
    for reason in (EmptyLineageSuggester.BY_DESIGN_REASON,
                   EmptyLineageSuggester.NO_CREDENTIALS_REASON,
                   LlmLineageSuggester.MODEL_UNREACHABLE_REASON,
                   LlmLineageSuggester.UNREADABLE_REASON,
                   LlmLineageSuggester.NO_CANDIDATES_REASON):
        assert "%" not in reason


# ── 이 경로에 쓰기가 없다 (`ai-no-lineage-write` 가 보는 것과 같은 사실) ──────
@pytest.mark.parametrize("name", ["suggest.py", "suggest_wire.py"])
def test_생산자_경로에_저장이_없다(name: str) -> None:
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "src" / "colab_ai" / "app" / name).read_text(encoding="utf-8")
    for forbidden in ("INSERT INTO", "UPDATE ", "DELETE FROM", "sqlalchemy",
                      "create_engine", "psycopg"):
        assert forbidden not in src, f"제안 생산자에 저장 경로가 생겼다: {forbidden}"


# ═══════════ 배선 플래그 (WU3 · `query_interpretation` 과 같은 규율) ═══════════
def test_기본값은_끈_쪽이고_키가_있어도_켜지지_않는다() -> None:
    assert Settings().suggest_lineage_mode == "off"
    assert Settings.from_env({"OPENAI_API_KEY": "sk-테스트"}).suggest_lineage_mode == "off"


def test_플래그는_값으로_켠다() -> None:
    s = Settings.from_env({"COLAB_AI_LINEAGE_SUGGESTION": "llm",
                           "OPENAI_API_KEY": "sk-테스트"})
    assert s.suggest_lineage_mode == "llm"


@pytest.mark.parametrize("typo", ["LLM_", "llm-ish", "on", " ", "literal"])
def test_모르는_값은_끈_쪽으로_떨어진다(typo: str) -> None:
    """오타가 모델 호출을 몰래 켜지 않는다 (`config.py:91-97` 선례)."""
    assert Settings.from_env(
        {"COLAB_AI_LINEAGE_SUGGESTION": typo}).suggest_lineage_mode == "off"


def test_대소문자와_공백은_같은_값으로_읽는다() -> None:
    assert Settings.from_env(
        {"COLAB_AI_LINEAGE_SUGGESTION": " LLM "}).suggest_lineage_mode == "llm"


# ═══════════ 게이트 ② 판정 2026-09-24 — 생산자는 예외를 던지지 않는다 ═══════════
@pytest.mark.parametrize("bad_id", [[P1], {"id": P1}, 1, True, None, 0.5])
def test_parentDatasetId_가_문자열이_아니어도_예외가_아니라_그_장만_버린다(bad_id) -> None:
    """**모델의 답은 신뢰하지 않는다 — 값만이 아니라 모양까지.**

    `known.get(item.get("parentDatasetId"))` 는 배열·객체가 오면
    `TypeError: unhashable type` 이다. 그 예외는 표면까지 새어 **500** 이 되고,
    그 순간 「못 하면 빈 제안 + 사유」(`main.py` 의 「생산자는 예외를 던지지 않는다」)가
    「업로드 화면이 깨진다」가 된다. 한 장이 규격을 어기면 **그 장만** 버린다.
    """
    t = FakeTransport(_reply(
        _item(bad_id), _item(P2, evidence=[_ev("grid", "0.25도", "0.25도")])))
    out = _run(t)
    assert [s.parent_dataset_id for s in out.suggestions] == [P2]
    assert out.empty_declaration is None


def test_후보_원천표기가_상한에서_잘린다() -> None:
    """요약과 **같은 규율**이다 — 상한이 한 곳에만 있으면 그 한 곳이 언젠가 어긋나고,
    그때 본문이 통째로 부푼다. 계약 `LineageParentCandidate.sourceLabel.maxLength` 와
    같은 값을 옮겨 적는다.
    """
    long = ParentCandidate(dataset_id=P1, name="강수", source_label="나" * 300)
    t = FakeTransport(_reply())
    _run(t, candidates=(long,))
    body = json.loads(t.payloads[0]["messages"][1]["content"])["candidates"][0]
    assert len(body["sourceLabel"]) == MAX_CANDIDATE_SOURCE_LABEL == 60


def test_후보의_기간이_본문까지_흐른다() -> None:
    """core-api 가 autometa 에서 읽어 실어 보낸 기간이다(`ingestion._lineage_candidate`).
    근거 한 줄의 재료인데 여기서 떨어뜨리면 **모델이 기간을 못 보고도 아무도 못 센다.**"""
    dated = ParentCandidate(dataset_id=P1, name="강수 — 원자료",
                            period_start="2020-01-01T00:00:00+00:00",
                            period_end="2024-12-31T00:00:00+00:00")
    t = FakeTransport(_reply())
    _run(t, candidates=(dated,))
    body = json.loads(t.payloads[0]["messages"][1]["content"])["candidates"][0]
    assert body["periodStart"] == "2020-01-01T00:00:00+00:00"
    assert body["periodEnd"] == "2024-12-31T00:00:00+00:00"
