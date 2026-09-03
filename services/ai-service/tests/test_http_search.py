"""`POST /searches` 표면 — 계약(`contracts/seams/core-ai.yaml`)이 오라클이다.

**계약을 시험이 재선언하지 않는다** — 필수 열쇠 목록을 yaml 에서 읽어 대조한다.
그리고 **키가 없는 판**(LLM 부재)으로 끝까지 돌린다: 이 서비스는 그 상태에서도 검색어를 낸다.

⚠ **2026-08-25 판정 ㈎ 이후 이 표면은 카탈로그를 뒤지지 않는다.** `results.items` 는 빈
배열이고, core-api 가 `interpretation` 을 읽어 `tsvector` 로 실제 결과를 만든다.
`SearchResponse` 는 열린 객체라(계약이 `additionalProperties` 를 닫지 않았다) 그 값을
**계약을 고치지 않고** 실을 수 있다 — 다만 계약의 산문은 아직 옛 역할 분담을 적고 있고,
그 갱신은 계약 소유 레인의 몫이다.
"""
from __future__ import annotations

import pathlib

import pytest
import yaml
from conftest import ACC_A_RES, LAB_A, LAB_B
from fastapi.testclient import TestClient

REPO = pathlib.Path(__file__).resolve().parents[3]
CONTRACT = REPO / "contracts" / "seams" / "core-ai.yaml"

# 이 파일의 `client` 픽스처가 `dict_db_url`(= `COLAB_AI_TEST_DICT_DB_URL`)을 통째로 쓴다.
# 표식은 **빼기 위한 이름**이지 skip 의 근거가 아니다 — 고른 실행에서는 그대로 판정한다.
pytestmark = pytest.mark.dictdb


@pytest.fixture(scope="module")
def spec() -> dict:
    return yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))


@pytest.fixture()
def client(dict_db_url: str) -> TestClient:
    """**OPENAI_API_KEY 를 주지 않는다** — 「AI 없이도 v2 는 완결된 제품이다」의 표면 증명."""
    from colab_ai.app.main import create_app
    from colab_ai.kernel.config import Settings
    app = create_app(Settings(dict_db_url=dict_db_url, openai_api_key=None,
                              model="gpt-5.6-luna"))
    return TestClient(app)


def _body(lab_id=LAB_A, query="강우 데이터 찾아줘"):
    return {"scope": {"labId": lab_id, "labName": "A 연구실"}, "query": query, "limit": 20}


def _headers(lab_id=LAB_A, account_id=ACC_A_RES):
    return {"X-CoLAB-Lab": lab_id, "X-CoLAB-Account": account_id}


def test_키가_없어도_200_이고_검색어가_나온다(client: TestClient) -> None:
    res = client.post("/searches", json=_body(), headers=_headers())
    assert res.status_code == 200
    body = res.json()
    # ⭑ `〈148〉` — **기본 회차는 `degraded` 가 아니다.** 이 시험이 지키는 것은
    #   「키가 없어도 **200 이고 검색어가 나온다**」이지 고장 표시가 아니다.
    #   `degraded` 는 계약상 「AI 가 제 몫을 **못 했다**」인데, 이번 릴리즈의 낱말 검색은
    #   **하지 않기로 한 것**이라 정상 동작이다(`〈136〉`).
    #   ⚠ 「켜려 했는데 키가 없다」는 여전히 고장이고, 그 갈래는
    #   `test_query_interpretation_switch.py` 가 따로 지킨다.
    assert body["degraded"] is False, "결정으로 고른 상태를 고장으로 말하면 안 된다"
    assert body["degradedReason"], "그래도 무엇을 했는지는 한 줄로 말한다"
    assert "강우" in body["interpretation"]["terms"]


def test_카탈로그를_뒤지지_않는다(client: TestClient) -> None:
    """**D3 커넥션이 이 단위에 없다** (`CLAUDE.md §3-1`). 결과는 언제나 빈 봉투다."""
    body = client.post("/searches", json=_body(), headers=_headers()).json()
    assert body["results"] == {"items": [], "totalCount": 0, "nextCursor": None}


def test_응답이_계약의_필수_열쇠를_전부_낸다(client: TestClient, spec: dict) -> None:
    required = spec["components"]["schemas"]["SearchResponse"]["allOf"][1]["required"]
    res = client.post("/searches", json=_body(), headers=_headers())
    body = res.json()
    assert set(required) | {"degraded"} <= set(body)
    assert set(spec["components"]["schemas"]["RequestedScope"]["required"]) <= set(body["scope"])
    # `results` 는 `common.json#ListEnvelope` 그대로다 — 비어도 세 열쇠가 다 선다.
    assert {"items", "totalCount", "nextCursor"} == set(body["results"])


def test_뒤진_범위가_JSON_에서도_먼저다(client: TestClient) -> None:
    res = client.post("/searches", json=_body(), headers=_headers())
    assert res.text.lstrip().startswith('{"scope"')


def test_요청_경계와_헤더_경계가_다르면_거절한다(client: TestClient) -> None:
    """경계가 두 곳에서 오면 **둘이 같을 때만** 답한다. 다르면 400 이다."""
    res = client.post("/searches", json=_body(lab_id=LAB_B), headers=_headers())
    assert res.status_code == 400
    assert set(res.json()) <= {"code", "message", "details"}


def test_주체가_없으면_401_이다(client: TestClient) -> None:
    res = client.post("/searches", json=_body(), headers={"X-CoLAB-Lab": LAB_A})
    assert res.status_code == 401


def test_응답의_범위는_요청의_범위를_되비춘다(client: TestClient) -> None:
    """core-api 는 보낸 값과 받은 값이 다르면 응답을 버린다 — 그래서 지어내지 않는다."""
    body = client.post("/searches", json=_body(lab_id=LAB_B),
                       headers=_headers(LAB_B, "00000000000000000000000BP1")).json()
    assert body["scope"]["labId"] == LAB_B


def test_빈_질의는_400_이다(client: TestClient) -> None:
    res = client.post("/searches", json=_body(query="  "), headers=_headers())
    assert res.status_code == 400


def test_200자를_넘으면_400_이다(client: TestClient) -> None:
    res = client.post("/searches", json=_body(query="강" * 201), headers=_headers())
    assert res.status_code == 400


def test_core_api_가_보내는_searchedCount_를_그대로_되비춘다(client: TestClient) -> None:
    """core-api 의 중계는 `scope` 에 `searchedCount` 를 얹어 보낸다(실측). 계약은 안 적었다 —
    **받아서 되비춘다.** 세는 것은 D3 의 일이고 이 단위는 D3 를 못 읽는다."""
    payload = _body()
    payload["scope"]["searchedCount"] = 999
    res = client.post("/searches", json=payload, headers=_headers())
    assert res.status_code == 200 and res.json()["scope"]["searchedCount"] == 999


def test_헬스는_이제_구현됐다고_말한다(client: TestClient) -> None:
    res = client.get("/healthz")
    assert res.status_code == 200 and res.json()["implemented"] is True
