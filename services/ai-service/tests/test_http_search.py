"""`POST /searches` 표면 — 계약(`contracts/seams/core-ai.yaml`)이 오라클이다.

**계약을 시험이 재선언하지 않는다** — 필수 열쇠 목록을 yaml 에서 읽어 대조한다.
그리고 **키가 없는 판**(LLM 부재)으로 끝까지 돌린다: 이 서비스는 그 상태에서도 결과를 낸다.
"""
from __future__ import annotations

import pathlib

import pytest
import yaml
from conftest import ACC_A_RES, DS_A1, DS_A2, LAB_A, LAB_B
from fastapi.testclient import TestClient

REPO = pathlib.Path(__file__).resolve().parents[3]
CONTRACT = REPO / "contracts" / "seams" / "core-ai.yaml"


@pytest.fixture(scope="module")
def spec() -> dict:
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))


@pytest.fixture()
def client(platform_db_url: str, dict_db_url: str) -> TestClient:
    """**OPENAI_API_KEY 를 주지 않는다** — 「AI 없이도 v2 는 완결된 제품이다」의 표면 증명."""
    from colab_ai.app.main import create_app
    from colab_ai.kernel.config import Settings
    app = create_app(Settings(platform_db_url=platform_db_url, dict_db_url=dict_db_url,
                              openai_api_key=None, model="gpt-5.6-luna"))
    return TestClient(app)


def _body(lab_id=LAB_A, query="강우 데이터 찾아줘"):
    return {"scope": {"labId": lab_id, "labName": "A 연구실"}, "query": query, "limit": 20}


def test_키가_없어도_200_이고_결과가_나온다(client: TestClient) -> None:
    res = client.post("/searches", json=_body(),
                      headers={"X-CoLAB-Lab": LAB_A, "X-CoLAB-Account": ACC_A_RES})
    assert res.status_code == 200
    body = res.json()
    assert body["degraded"] is True and body["degradedReason"]
    ids = [h["datasetId"] for h in body["results"]["items"]]
    assert set(ids) == {DS_A1, DS_A2}


def test_응답이_계약의_필수_열쇠를_전부_낸다(client: TestClient, spec: dict) -> None:
    required = spec["components"]["schemas"]["SearchResponse"]["allOf"][1]["required"]
    hit_required = spec["components"]["schemas"]["SearchHit"]["required"]
    hit_props = set(spec["components"]["schemas"]["SearchHit"]["properties"])
    res = client.post("/searches", json=_body(),
                      headers={"X-CoLAB-Lab": LAB_A, "X-CoLAB-Account": ACC_A_RES})
    body = res.json()
    assert set(required) | {"degraded"} <= set(body)
    assert set(spec["components"]["schemas"]["RequestedScope"]["required"]) <= set(body["scope"])
    for hit in body["results"]["items"]:
        assert set(hit_required) <= set(hit) <= hit_props     # 계약 밖 필드를 얹지 않는다


def test_뒤진_범위가_JSON_에서도_먼저다(client: TestClient) -> None:
    res = client.post("/searches", json=_body(),
                      headers={"X-CoLAB-Lab": LAB_A, "X-CoLAB-Account": ACC_A_RES})
    assert res.text.lstrip().startswith('{"scope"')


def test_요청_경계와_헤더_경계가_다르면_거절한다(client: TestClient) -> None:
    """경계가 두 곳에서 오면 **둘이 같을 때만** 뒤진다. 다르면 400 이다."""
    res = client.post("/searches", json=_body(lab_id=LAB_B),
                      headers={"X-CoLAB-Lab": LAB_A, "X-CoLAB-Account": ACC_A_RES})
    assert res.status_code == 400
    assert set(res.json()) <= {"code", "message", "details"}


def test_다른_연구실_경계로는_A_의_데이터가_안_나온다(client: TestClient) -> None:
    res = client.post("/searches", json=_body(lab_id=LAB_B),
                      headers={"X-CoLAB-Lab": LAB_B, "X-CoLAB-Account": "00000000000000000000000BP1"})
    body = res.json()
    assert body["results"]["items"] == []
    assert body["scope"]["labId"] == LAB_B


def test_빈_질의는_400_이다(client: TestClient) -> None:
    res = client.post("/searches", json=_body(query="  "),
                      headers={"X-CoLAB-Lab": LAB_A, "X-CoLAB-Account": ACC_A_RES})
    assert res.status_code == 400


def test_200자를_넘으면_400_이다(client: TestClient) -> None:
    res = client.post("/searches", json=_body(query="강" * 201),
                      headers={"X-CoLAB-Lab": LAB_A, "X-CoLAB-Account": ACC_A_RES})
    assert res.status_code == 400


def test_core_api_가_보내는_searchedCount_를_받아도_깨지지_않는다(client: TestClient) -> None:
    """core-api 의 중계는 `scope` 에 `searchedCount` 를 얹어 보낸다(실측). 계약은 안 적었다 —
    **받아 주되 쓰지 않는다.** 뒤진 개수는 이쪽이 실제로 세서 답한다."""
    payload = _body()
    payload["scope"]["searchedCount"] = 999
    res = client.post("/searches", json=payload,
                      headers={"X-CoLAB-Lab": LAB_A, "X-CoLAB-Account": ACC_A_RES})
    assert res.status_code == 200 and res.json()["scope"]["searchedCount"] == 2


def test_헬스는_이제_구현됐다고_말한다(client: TestClient) -> None:
    res = client.get("/healthz")
    assert res.status_code == 200 and res.json()["implemented"] is True
