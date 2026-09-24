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
                        "periodStart", "periodEnd"}, f"선택 열쇠 집합이 다르다: {optional}"


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

    def __call__(self, payload: dict) -> str:
        self.calls += 1
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


def test_켠_회차의_제안이_표면까지_흐른다() -> None:
    fake = _Fake(json.dumps({"suggestions": [
        {"parentDatasetId": CAND_A, "confidence": "확실",
         "rationale": "기상청 AWS 일강수량을 crop 한 표본이다",
         "suggestedParentRole": "주입력"}]}, ensure_ascii=False))
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
    assert one["confidence"] == "확실"
    assert one["kind"] == "가공 전 데이터"
    for forbidden in ("score", "confidencePercent", "%"):
        assert forbidden not in json.dumps(body, ensure_ascii=False)


def test_후보_밖_ID_는_표면에서도_사라진다() -> None:
    fake = _Fake(json.dumps({"suggestions": [
        {"parentDatasetId": "01ARZ3NDEKTSV4RRFFQ69G5FZZ", "confidence": "확실",
         "rationale": "지어낸 ID 다"}]}, ensure_ascii=False))
    body = _llm_client(fake).post(PATH, json=_body(candidates=[_cand()]),
                                  headers=_headers()).json()
    assert body["suggestions"] == []
    assert body["degradedReason"], "0건의 사유를 응답이 스스로 말해야 한다"
