"""`POST /lineage-suggestions` 표면 — **계약이 오라클이다.**

`contracts/seams/core-ai.yaml` 은 2026-08-22 에 동결됐다. 시험은 계약을 재선언하지 않고
**yaml 에서 읽어 대조한다** — 옮겨 적으면 두 벌이 되고 갈린다.

⚠ **이 표면은 저장하지 않는다.** 계약에 쓰기 오퍼레이션이 없는 것이 그 계약 쪽 표현이고,
게이트 `ai-no-lineage-write` 가 코드 쪽에서 같은 것을 본다.
"""
from __future__ import annotations

import json
import pathlib

import pytest
import yaml
from conftest import ACC_A_RES, LAB_A, LAB_B
from fastapi.testclient import TestClient

REPO = pathlib.Path(__file__).resolve().parents[3]
CONTRACT = REPO / "contracts" / "seams" / "core-ai.yaml"
PATH = "/lineage-suggestions"


@pytest.fixture(scope="module")
def spec() -> dict:
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))


@pytest.fixture()
def client() -> TestClient:
    """**설정을 하나도 주지 않는다** — 「AI 없이도 v2 는 완결된 제품이다」의 표면 증명."""
    from colab_ai.app.main import create_app
    from colab_ai.kernel.config import Settings
    return TestClient(create_app(Settings()))


def _file(**over):
    meta = {"fileName": "rain_2024.nc", "kind": "본체", "format": "NetCDF",
            "variables": ["pr", "lat", "lon"]}
    meta.update(over)
    return meta


def _body(lab_id=LAB_A, **over):
    body = {"scope": {"labId": lab_id, "labName": "A 연구실", "searchedCount": 12},
            "file": _file()}
    body.update(over)
    return body


def _headers(lab_id=LAB_A, account_id=ACC_A_RES):
    return {"X-CoLAB-Lab": lab_id, "X-CoLAB-Account": account_id}


# ── 계약 대조 ───────────────────────────────────────────────────────────────
def test_계약이_요구한_응답_열쇠가_전부_있다(client, spec) -> None:
    schemas = spec["components"]["schemas"]
    required = set(schemas["LineageSuggestionResponse"]["allOf"][1]["required"])
    required |= set(schemas["Degradable"]["required"])
    res = client.post(PATH, json=_body(), headers=_headers())
    assert res.status_code == 200, res.text
    assert required <= set(res.json()), f"계약 required 가 응답에 없다: {required - set(res.json())}"


def test_계약이_이_표면에_쓰기_오퍼레이션을_두지_않았다(spec) -> None:
    """제안은 D10 안에서 태어나 D10 안에서 죽는다 (`core-ai.yaml` 머리 주석 1)."""
    for path, item in spec["paths"].items():
        if "lineage" in path:
            assert set(item) <= {"post"}, f"{path} 에 쓰기 메서드가 생겼다"


def test_뒤진_범위가_바이트에서도_제안보다_앞이다(client) -> None:
    raw = client.post(PATH, json=_body(), headers=_headers()).text
    assert raw.index('"scope"') < raw.index('"suggestions"')


# ── 요청 검증 — 계약이 required 로 적은 것을 실제로 요구한다 ────────────────
def test_file_없는_요청은_400_이다(client, spec) -> None:
    assert "file" in spec["components"]["schemas"]["LineageSuggestionRequest"]["required"]
    body = _body()
    del body["file"]
    assert client.post(PATH, json=body, headers=_headers()).status_code == 400


def test_계약에_없는_열쇠를_실은_요청은_400_이다(client, spec) -> None:
    """`additionalProperties: false` — **소비자의 표류를 표면이 잡는다.**

    ⚠ 이 시험이 이번 회차의 red 하나를 만들었다: 중계가 계약에 없는 `uploadId` 를
    보내고 있었고(2026-08-23 이후), 생산자가 없어 아무도 거절하지 않고 있었다.
    """
    assert spec["components"]["schemas"]["LineageSuggestionRequest"][
        "additionalProperties"] is False
    res = client.post(PATH, json=_body(uploadId="01ARZ3NDEKTSV4RRFFQ69G5FAV"),
                      headers=_headers())
    assert res.status_code == 400, res.text


# ── 후보 목록 — WU0 계약 개정 (Ted 서명 2026-09-24 · 판정 기록 3) ────────────
def test_요청에_후보_목록을_실을_자리가_있다(spec) -> None:
    """후보는 **core-api 가 고른다**(`〈72〉-㉮` 와 같은 분담). ai-service 는 D3 에 닿지 않는다.

    선택 필드다 — 안 보내던 소비자가 그대로 200 이어야 파괴적 변경이 아니다.
    """
    req = spec["components"]["schemas"]["LineageSuggestionRequest"]
    assert "candidates" in req["properties"], "요청에 후보를 실을 자리가 없다"
    assert "candidates" not in req["required"], "후보는 선택 필드다 — required 에 넣지 않는다"
    candidates = req["properties"]["candidates"]
    assert candidates["type"] == "array"
    assert candidates["maxItems"] == 20, "후보 상한 k=20 (미해결 4 권고)"
    assert candidates["items"]["$ref"] == "#/components/schemas/LineageParentCandidate"


def test_후보가_지고_갈_열쇠_집합이_닫혀_있다(spec) -> None:
    """근거로 인용할 수 있는 값만 싣는다 — J3 이 이 집합을 오라클로 쓴다(미해결 2)."""
    cand = spec["components"]["schemas"]["LineageParentCandidate"]
    assert cand["required"] == ["datasetId", "name"]
    assert cand["additionalProperties"] is False
    optional = set(cand["properties"]) - set(cand["required"])
    assert optional == {"topic", "summary", "sourceLabel", "processingLevel",
                        "periodStart", "periodEnd",
                        # ⭑ `WU-S0` — 인용 가능한 원메타 4축(`R-K3-STRUCTURE` 판정 2)
                        "crs", "grid", "variables", "fileName"}, \
        f"선택 열쇠 집합이 다르다: {optional}"


def test_scope_없이는_뒤지지_않는다(client) -> None:
    body = _body()
    del body["scope"]
    assert client.post(PATH, json=body, headers=_headers()).status_code == 400


def test_본문의_연구실과_헤더의_연구실이_다르면_400_이다(client) -> None:
    """경계를 이쪽이 고르지 않는다 (`CLAUDE.md §3-5` · `/searches` 와 같은 규칙)."""
    res = client.post(PATH, json=_body(lab_id=LAB_A), headers=_headers(lab_id=LAB_B))
    assert res.status_code == 400


def test_주체가_없으면_401_이다(client) -> None:
    res = client.post(PATH, json=_body(), headers={"X-CoLAB-Lab": LAB_A})
    assert res.status_code == 401


def test_파일_종류가_계약_밖이면_400_이다(client, spec) -> None:
    res = client.post(PATH, json=_body(file=_file(kind="스프레드시트")), headers=_headers())
    assert res.status_code == 400


# ── 정직한 빈 상태 ──────────────────────────────────────────────────────────
def test_빈_결과는_에러가_아니다(client) -> None:
    res = client.post(PATH, json=_body(), headers=_headers())
    assert res.status_code == 200
    assert res.json()["suggestions"] == []


def test_0건이_사유_없이_나오지_않는다(client) -> None:
    """**「제안하지 않았다」가 값어치를 가지려면 왜인지가 붙어야 한다.**"""
    body = client.post(PATH, json=_body(), headers=_headers()).json()
    assert body["suggestions"] == []
    assert body["degradedReason"], "0건의 사유를 응답이 스스로 말해야 한다"
    assert "0건" in body["degradedReason"]


def test_재료가_없어_못_만든_것을_찾고_못_찾은_것으로_말하지_않는다(client) -> None:
    """㈏(뒤졌는데 0건)와 ㈐(물어볼 재료가 없다)를 같은 값으로 접지 않는다.

    지금 이 표면은 **부모 후보를 실을 자리가 요청에 없다** — 계약
    `LineageSuggestionRequest` 에 후보 목록이 없고 이 배포 단위는 카탈로그(D3)를
    읽지 못한다(`〈72〉-㉮`). 그러므로 참인 값은 **`degraded: true`** 다.
    `false` 로 내면 「살펴봤는데 없더라」라는 하지 않은 판정을 주장하게 된다.
    """
    body = client.post(PATH, json=_body(), headers=_headers()).json()
    assert body["degraded"] is True


def test_억지_제안을_만들지_않는다(client) -> None:
    """파일 메타를 아무리 그럴듯하게 줘도 제안이 지어지지 않는다."""
    rich = _file(format="NetCDF", variables=["pr"], crs="EPSG:4326",
                 gridDescription="0.25도 격자", sourceNoteDraft="기상청 AWS")
    body = client.post(PATH, json=_body(file=rich, datasetNameDraft="일강수량 집계"),
                       headers=_headers()).json()
    assert body["suggestions"] == []


def test_원자료라고_주장하지_않는다(client) -> None:
    body = client.post(PATH, json=_body(), headers=_headers()).json()
    assert body["rawDataLikely"] is False


def test_응답_어디에도_숫자_확신도가_없다(client) -> None:
    raw = json.dumps(client.post(PATH, json=_body(), headers=_headers()).json(),
                     ensure_ascii=False)
    for forbidden in ("score", "confidencePercent", "probability", "%"):
        assert forbidden not in raw


def test_묶음_승인_열쇠가_응답에_없다(client) -> None:
    body = client.post(PATH, json=_body(), headers=_headers()).json()
    for forbidden in ("approveAll", "batchStatus", "approved"):
        assert forbidden not in body


def test_범위를_요청_그대로_되비춘다(client) -> None:
    """core-api 는 보낸 값과 받은 값이 다르면 응답을 버린다 — 여기서 지어내면 전부 버려진다."""
    scope = client.post(PATH, json=_body(), headers=_headers()).json()["scope"]
    assert scope == {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 12}


# ── 후보를 실은 요청 — 표면이 계약을 실제로 요구한다 (WU2) ───────────────────
CAND_A = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
CAND_B = "01ARZ3NDEKTSV4RRFFQ69G5FB0"


def _cand(**over):
    item = {"datasetId": CAND_A, "name": "강수 — 원자료", "topic": "강우·강수",
            "summary": "기상청 AWS 일강수량", "processingLevel": 0}
    item.update(over)
    return item


class _Fake:
    """모델 자리에 앉는 가짜 전송. **부른 횟수를 센다.**"""

    def __init__(self, reply: str = '{"suggestions": []}') -> None:
        self.reply, self.calls = reply, 0
        self.payloads: list[dict] = []

    def __call__(self, payload: dict) -> str:
        self.calls += 1
        self.payloads.append(payload)
        return self.reply


def _app(settings, suggester=None):
    from colab_ai.app.main import create_app
    return TestClient(create_app(settings, suggester=suggester))


def _llm_client(fake: _Fake) -> TestClient:
    """플래그를 켠 조립 — **전송만 가짜다.** 게이트에서 모델을 부르지 않는다."""
    from colab_ai.app.suggest import LlmLineageSuggester
    from colab_ai.kernel.config import Settings
    settings = Settings(openai_api_key="sk-테스트", suggest_lineage_mode="llm")
    return _app(settings, LlmLineageSuggester(
        api_key=settings.openai_api_key, model=settings.model, transport=fake))


def test_후보_항목에_계약에_없는_열쇠가_있으면_400_이다(client, spec) -> None:
    assert spec["components"]["schemas"]["LineageParentCandidate"][
        "additionalProperties"] is False
    res = client.post(PATH, json=_body(candidates=[_cand(relevance=0.9)]),
                      headers=_headers())
    assert res.status_code == 400, res.text


def test_후보의_ID_가_정규_ID_가_아니면_400_이다(client) -> None:
    res = client.post(PATH, json=_body(candidates=[_cand(datasetId="12")]),
                      headers=_headers())
    assert res.status_code == 400, res.text


def test_후보_상한을_넘으면_400_이다(client, spec) -> None:
    cap = spec["components"]["schemas"]["LineageSuggestionRequest"][
        "properties"]["candidates"]["maxItems"]
    res = client.post(PATH, json=_body(candidates=[_cand()] * (cap + 1)),
                      headers=_headers())
    assert res.status_code == 400, res.text


def test_후보를_생략하면_모델을_부르지_않고_200_이다() -> None:
    """안 보내던 소비자가 그대로 200 이어야 파괴적 변경이 아니다."""
    fake = _Fake()
    res = _llm_client(fake).post(PATH, json=_body(), headers=_headers())
    assert res.status_code == 200, res.text
    assert res.json()["suggestions"] == []
    assert fake.calls == 0, "살펴볼 후보가 없는데 토큰을 태웠다"


def test_플래그가_꺼져_있으면_후보가_있어도_모델을_부르지_않는다() -> None:
    from colab_ai.app.main import build_suggester
    from colab_ai.app.suggest import EmptyLineageSuggester
    from colab_ai.kernel.config import Settings
    settings = Settings(openai_api_key="sk-테스트")       # 기본값 = off
    assert isinstance(build_suggester(settings), EmptyLineageSuggester)

    res = _app(settings).post(PATH, json=_body(candidates=[_cand()]),
                              headers=_headers())
    assert res.status_code == 200
    assert res.json()["suggestions"] == []


def test_플래그를_켜려_했는데_키가_없으면_고장_문구다() -> None:
    from colab_ai.app.main import build_suggester
    from colab_ai.app.suggest import EmptyLineageSuggester
    from colab_ai.kernel.config import Settings
    chosen = build_suggester(Settings(suggest_lineage_mode="llm"))
    assert isinstance(chosen, EmptyLineageSuggester)
    out = chosen.suggest(file_meta=_file(), candidates=(),
                         dataset_name_draft=None, subject=None)
    assert out.empty_declaration == EmptyLineageSuggester.NO_CREDENTIALS_REASON


#: 모델이 낼 수 있는 인용 한 항목 (`ParentCandidateSuggestion.evidence.items`).
_EV = {"field": "variables", "uploadValue": "pr", "candidateValue": "pr"}


def _model_item(parent_id=CAND_A, **over):
    item = {"parentDatasetId": parent_id, "suggestedParentRole": "주입력",
            "evidence": [dict(_EV)]}
    item.update(over)
    return item


def test_켠_회차의_제안이_표면까지_흐른다() -> None:
    fake = _Fake(json.dumps({"suggestions": [_model_item()]}, ensure_ascii=False))
    res = _llm_client(fake).post(
        PATH, json=_body(candidates=[_cand(), _cand(datasetId=CAND_B, name="DEM")]),
        headers=_headers())
    assert res.status_code == 200, res.text
    body = res.json()
    assert fake.calls == 1
    assert body["degraded"] is False
    assert len(body["suggestions"]) == 1
    one = body["suggestions"][0]
    assert one["parentDatasetId"] == CAND_A
    assert one["parentDatasetName"] == "강수 — 원자료"
    assert one["kind"] == "가공 전 데이터"
    # **인용이 표면까지 나간다** — core-api 가 이 값을 실제 메타와 대조한다.
    assert one["evidence"] == [_EV]
    for forbidden in ("score", "confidencePercent", "%"):
        assert forbidden not in json.dumps(body, ensure_ascii=False)


def test_표면이_내는_확신도와_근거가_자리채움이다() -> None:
    """**모델이 만든 값이 아니다**(판정 기록 2회차 4) — core-api 가 다시 쓴다.
    계약 required 라 열쇠 자체는 있어야 한다."""
    from colab_ai.domains.d10_suggestion import (
        PLACEHOLDER_CONFIDENCE,
        PLACEHOLDER_RATIONALE,
    )
    fake = _Fake(json.dumps({"suggestions": [
        _model_item(confidence="확실", rationale="모델이 스스로 쓴 문장이다")]},
        ensure_ascii=False))
    one = _llm_client(fake).post(PATH, json=_body(candidates=[_cand()]),
                                 headers=_headers()).json()["suggestions"][0]
    assert one["confidence"] == PLACEHOLDER_CONFIDENCE
    assert one["rationale"] == PLACEHOLDER_RATIONALE
    assert "모델이 스스로 쓴 문장이다" not in json.dumps(one, ensure_ascii=False)


def test_제안_한_장의_열쇠가_계약_안에_있다(spec) -> None:
    """**열쇠 ⊆ 계약** — 계약에 없는 열쇠를 실으면 core-api 가 응답을 통째로 버린다."""
    schemas = spec["components"]["schemas"]
    allowed = set(schemas["AiSuggestionBase"]["properties"])
    allowed |= set(schemas["ParentCandidateSuggestion"]["allOf"][1]["properties"])
    fake = _Fake(json.dumps({"suggestions": [_model_item()]}, ensure_ascii=False))
    one = _llm_client(fake).post(PATH, json=_body(candidates=[_cand()]),
                                 headers=_headers()).json()["suggestions"][0]
    assert set(one) <= allowed, f"계약 밖 열쇠가 실렸다: {set(one) - allowed}"
    item = schemas["ParentCandidateSuggestion"]["allOf"][1][
        "properties"]["evidence"]["items"]
    for ev in one["evidence"]:
        assert set(ev) == set(item["required"]), f"근거 항목이 계약 밖이다: {set(ev)}"
        assert ev["field"] in item["properties"]["field"]["enum"]


def test_인용이_한_항목도_없는_후보는_표면에서도_제안이_아니다() -> None:
    fake = _Fake(json.dumps({"suggestions": [_model_item(evidence=[])]},
                            ensure_ascii=False))
    body = _llm_client(fake).post(PATH, json=_body(candidates=[_cand()]),
                                  headers=_headers()).json()
    assert body["suggestions"] == []
    assert body["degradedReason"], "0건의 사유를 응답이 스스로 말해야 한다"


def test_후보_밖_ID_는_표면에서도_사라진다() -> None:
    fake = _Fake(json.dumps({"suggestions": [
        _model_item("01ARZ3NDEKTSV4RRFFQ69G5FZZ")]}, ensure_ascii=False))
    body = _llm_client(fake).post(PATH, json=_body(candidates=[_cand()]),
                                  headers=_headers()).json()
    assert body["suggestions"] == []
    assert body["degradedReason"], "0건의 사유를 응답이 스스로 말해야 한다"


# ══════════════════ 게이트 ② 판정 2026-09-24 ══════════════════════════════
@pytest.mark.parametrize("key", ["topic", "summary", "sourceLabel",
                                 "periodStart", "periodEnd"])
@pytest.mark.parametrize("bad", [7, 0.5, True, [], {}, "", "   "])
def test_후보의_선택_문자열_열쇠가_계약_밖이면_400_이다(client, key, bad) -> None:
    """**표면이 막지 않으면 아래에서 터진다.**

    계약은 이 다섯을 `type: string · minLength: 1` 로 적었는데 표면은 `datasetId`·
    `name`·`processingLevel` 만 검사하고 나머지는 **그대로 통과**시켰다. 그 값은
    `suggest_wire.candidate_payload` 의 `c.summary[:200]` 까지 내려가 `TypeError` 가
    되고, 계약대로면 **400** 일 요청이 **500** 으로 나간다 — 소비자의 표류가
    「이쪽 고장」으로 뒤바뀌는 자리다.
    """
    res = client.post(PATH, json=_body(candidates=[_cand(**{key: bad})]),
                      headers=_headers())
    assert res.status_code == 400, res.text


def test_표면의_열쇠_집합이_계약_한_벌에서_온다(spec) -> None:
    """**옮겨 적은 두 벌은 언젠가 갈린다.** 계약에 열쇠가 하나 늘어도 표면 상수를
    같이 고치지 않으면 새 열쇠가 400 으로 되튀고, 그 어긋남은 계약 게이트가 못 본다
    (정적 스펙만 보고 표면 상수를 보지 않는다). 여기가 그 유일한 대조다.
    """
    from colab_ai.app.main import CANDIDATE_KEYS, SUGGEST_KEYS

    schemas = spec["components"]["schemas"]
    assert SUGGEST_KEYS == set(schemas["LineageSuggestionRequest"]["properties"]), \
        "표면의 요청 열쇠 집합이 계약과 갈렸다"
    assert CANDIDATE_KEYS == set(schemas["LineageParentCandidate"]["properties"]), \
        "표면의 후보 열쇠 집합이 계약과 갈렸다"


# ══════════════ WU-S0 계약 개정 (R-K3-STRUCTURE · Ted 서명 2026-09-24) ═══════
#: `evidence.field` 의 축 이름. **`WU-S1` 비교기의 축 이름과 같은 문자열이다** —
#: 두 벌이 되는 순간 「모델이 인용한 축」과 「core-api 가 검증하는 축」이 갈린다.
EVIDENCE_FIELDS = ["period", "crs", "grid", "variables", "fileName"]


def test_요청에_업로드_가공단계를_실을_자리가_있다(spec) -> None:
    """사람이 등록 폼 ① 에서 고른 자기 Lv. 적격 필터의 기준값이고 필터는 core-api 가 건다.

    ⚠ **`common.json#/$defs/ProcessingLevel` 을 `$ref` 하지 않는다** — 그 타입은
    `readOnly: true`(응답 전용)라고 스스로 적었고, 요청 본문에 실으면 그 산문이 거짓이 된다.
    """
    req = spec["components"]["schemas"]["LineageSuggestionRequest"]
    assert "processingLevel" in req["properties"], "요청에 업로드 Lv 를 실을 자리가 없다"
    assert "processingLevel" not in req["required"], "선택 필드다 — required 에 넣지 않는다"
    lv = req["properties"]["processingLevel"]
    assert "$ref" not in lv and "allOf" not in lv, \
        "readOnly 인 응답 전용 타입을 요청 본문에 참조했다"
    assert lv["type"] == "integer"
    assert (lv["minimum"], lv["maximum"]) == (0, 3), "LV_CAP=3 (`ports/lineage.py` LV_CAP)"
    assert "readOnly" in lv["description"], "인라인으로 적은 사유가 산문에 없다"


def test_후보가_인용_가능한_원메타를_지고_간다(spec) -> None:
    """`d3_dataset_autometa` 에 저장된 **날값 그대로**. 파생 신호는 싣지 않는다(판정 2)."""
    schemas = spec["components"]["schemas"]
    props = schemas["LineageParentCandidate"]["properties"]
    for key in ("crs", "grid", "fileName"):
        assert props[key]["type"] == "string", f"{key} 는 문자열이다"
        assert props[key]["minLength"] == 1, f"{key} 는 빈 문자열을 받지 않는다"
    variables = props["variables"]
    assert variables["type"] == "array"
    assert variables["items"] == \
        schemas["UploadedFileMeta"]["properties"]["variables"]["items"], \
        "업로드 쪽 변수 항목과 모양이 두 벌이다 — 같은 값을 대조하는데 규격이 갈렸다"
    assert isinstance(variables["maxItems"], int) and variables["maxItems"] > 0, \
        "본문이 부풀지 않게 상한을 계약이 건다"


def test_후보_원메타에_파생_신호를_싣지_않는다(spec) -> None:
    """모델이 축 대조를 **스스로** 해야 J3' 오라클이 산다 — 우리가 답을 보내면 자기 값을
    자기가 검증하게 된다(열린 권고 ① 채택)."""
    props = spec["components"]["schemas"]["LineageParentCandidate"]["properties"]
    for forbidden in ("signals", "periodOverlap", "variableOverlap", "score"):
        assert forbidden not in props, f"파생 신호를 후보에 실었다: {forbidden}"


def test_제안이_모델의_인용_근거를_지고_간다(spec) -> None:
    """모델이 하는 일은 **인용까지**다. 대조·폐기는 core-api 가 한다."""
    node = spec["components"]["schemas"]["ParentCandidateSuggestion"]["allOf"][1]
    assert "evidence" in node["properties"], "인용 근거를 실을 자리가 없다"
    assert "evidence" not in node["required"], "선택 필드다 — 안 보내던 생산자가 그대로 유효하다"
    ev = node["properties"]["evidence"]
    assert ev["type"] == "array"
    assert ev["maxItems"] == 5, "축이 5개다 — 같은 축을 여러 번 인용해 채우지 못한다"
    item = ev["items"]
    assert item["type"] == "object"
    assert item["additionalProperties"] is False, "근거 항목도 닫혀 있다"
    assert item["required"] == ["field", "uploadValue", "candidateValue"]
    assert item["properties"]["field"]["enum"] == EVIDENCE_FIELDS
    for key in ("uploadValue", "candidateValue"):
        assert item["properties"][key]["type"] == "string"
        assert item["properties"][key]["minLength"] == 1
        assert item["properties"][key]["maxLength"] == 200


def test_근거가_주장이지_판정이_아니라고_계약이_적는다(spec) -> None:
    ev = spec["components"]["schemas"]["ParentCandidateSuggestion"][
        "allOf"][1]["properties"]["evidence"]
    desc = ev["description"]
    assert "core-api" in desc and "버린다" in desc, "검증·폐기의 주인이 산문에 없다"


def test_확신도와_근거_문장의_산지가_계약_산문에_적혀_있다(spec) -> None:
    """**계약이 거짓말하면 안 된다.** ai-service 가 싣는 두 값은 required 를 채우는
    잠정값이고 core-api 가 덮어쓴다(판정 4). 그 사실이 산문에 없으면 소비자는
    모델이 판정한 값으로 읽는다.
    """
    base = spec["components"]["schemas"]["AiSuggestionBase"]["properties"]
    for key in ("confidence", "rationale"):
        desc = str(base[key].get("description", ""))
        assert "잠정값" in desc, f"{key} 산문에 잠정값이라는 사실이 없다"
        assert "core-api" in desc, f"{key} 산문에 누가 다시 쓰는지가 없다"


def test_오퍼레이션_산문이_인용_검증_모형을_적는다(spec) -> None:
    desc = ""
    for path, item in spec["paths"].items():
        if "lineage" in path:
            desc = str(item["post"].get("description", ""))
    assert "인용" in desc and "core-api" in desc, \
        "적격 필터·인용 검증의 주인이 오퍼레이션 산문에 없다"


# ── 표면이 새 열쇠를 실제로 받는다 ──────────────────────────────────────────
def test_요청의_가공단계_열쇠를_표면이_받는다(client) -> None:
    res = client.post(PATH, json=_body(processingLevel=2), headers=_headers())
    assert res.status_code == 200, res.text


@pytest.mark.parametrize("bad", [-1, 4, 2.0, True, "2", None, []])
def test_요청의_가공단계가_계약_밖이면_400_이다(client, spec, bad) -> None:
    """계약은 `integer · 0..3` 이다. 표면이 값을 안 보면 **계약 밖 값이 그대로 흘러간다**
    — 아래층에서 터지거나, 순위 문장이 틀린 기준으로 읽힌다."""
    lv = spec["components"]["schemas"]["LineageSuggestionRequest"][
        "properties"]["processingLevel"]
    assert (lv["minimum"], lv["maximum"]) == (0, 3)
    res = client.post(PATH, json=_body(processingLevel=bad), headers=_headers())
    assert res.status_code == 400, res.text


def test_업로드_가공단계가_모델에게_가는_본문에_실린다() -> None:
    fake = _Fake()
    _llm_client(fake).post(PATH, json=_body(processingLevel=1, candidates=[_cand()]),
                           headers=_headers())
    assert fake.calls == 1
    body = json.loads(fake.payloads[0]["messages"][1]["content"])
    assert body["processingLevel"] == 1


def test_후보의_원메타_열쇠를_표면이_받는다(client) -> None:
    res = client.post(PATH, json=_body(candidates=[_cand(
        crs="EPSG:4326", grid="0.25도 격자", variables=["pr", "lat"],
        fileName="rain_2024.nc")]), headers=_headers())
    assert res.status_code == 200, res.text


@pytest.mark.parametrize("key", ["crs", "grid", "fileName"])
@pytest.mark.parametrize("bad", [7, 0.5, True, [], {}, "", "   "])
def test_후보의_원메타_문자열이_계약_밖이면_400_이다(client, key, bad) -> None:
    res = client.post(PATH, json=_body(candidates=[_cand(**{key: bad})]),
                      headers=_headers())
    assert res.status_code == 400, res.text


@pytest.mark.parametrize("bad", ["pr", 7, True, {}, [""], ["   "], [1], [None]])
def test_후보의_변수_목록이_계약_밖이면_400_이다(client, bad) -> None:
    res = client.post(PATH, json=_body(candidates=[_cand(variables=bad)]),
                      headers=_headers())
    assert res.status_code == 400, res.text


def test_후보의_빈_변수_목록은_정상이다(client) -> None:
    """변수 행이 한 줄도 없는 데이터셋이 실재한다 — `minItems` 를 여기 걸지 않는 이유다."""
    res = client.post(PATH, json=_body(candidates=[_cand(variables=[])]),
                      headers=_headers())
    assert res.status_code == 200, res.text
