"""`POST /searches` 의 **운영자 범위 표식** — 경계를 빼지 않고 명시적으로 넘긴다.

intent `dev-package/intent/2026-09-25-operator-search-scope.md` §설계트리 Q1·Q6 (이슈 #158).
계약 = `core-ai.yaml#OperatorRequestedScope`(요청) · `common.json#AiOperatorSearchScope`(응답).

오라클
  ⑴ `operatorScope: true` + `labName` + 주체 헤더, 연구실 헤더 없음 → 200 이고 운영자 범위를 되비춘다.
  ⑵ 경계 없는 요청은 계속 거절한다 — scope 부재·표식도 연구실도 없음·주체 부재.
  ⑶ 표식과 연구실을 함께 보내면 400(정확히 하나) · 표식에 연구실 헤더가 붙으면 400(이중 대조).
  ⑷ `labId: "None"` 은 여전히 400 이다 — 가짜 식별자를 받지 않는다.

⚠ DB 없이 돈다 — `test_search_route_threadpool.py` 와 같은 최소 설정 판이다.
"""
from __future__ import annotations

import json
import pathlib

from colab_ai.app.main import create_app
from colab_ai.kernel.config import Settings
from fastapi.testclient import TestClient

REPO = pathlib.Path(__file__).resolve().parents[3]
COMMON = REPO / "contracts" / "schemas" / "common.json"

LAB = "0000000000000000000000000A"
ACC = "000000000000000000000000A1"
LABEL = "전체 연구실"


def _client() -> TestClient:
    return TestClient(create_app(Settings(dict_db_url=None, openai_api_key=None)))


def _operator_body(**scope) -> dict:
    return {"scope": {"operatorScope": True, "labName": LABEL, **scope},
            "query": "강우 데이터 찾아줘"}


def _account_only() -> dict:
    return {"X-CoLAB-Account": ACC}


def test_an_operator_scope_is_accepted_and_echoed() -> None:
    res = _client().post("/searches", json=_operator_body(searchedCount=26),
                         headers=_account_only())
    assert res.status_code == 200, res.text
    assert res.text.lstrip().startswith('{"scope"'), "뒤진 범위가 바이트에서도 먼저다."
    scope = res.json()["scope"]
    assert scope == {"operatorScope": True, "labName": LABEL, "searchedCount": 26}


def test_the_echoed_operator_scope_matches_the_contract_variant() -> None:
    schema = json.loads(COMMON.read_text(encoding="utf-8"))["$defs"]["AiOperatorSearchScope"]
    scope = _client().post("/searches", json=_operator_body(searchedCount=3),
                           headers=_account_only()).json()["scope"]
    assert set(schema["required"]) <= set(scope) <= set(schema["properties"]), scope
    assert scope["operatorScope"] in schema["properties"]["operatorScope"]["enum"]


def test_a_request_without_any_boundary_is_still_refused() -> None:
    client = _client()
    no_scope = {"query": "강우"}
    assert client.post("/searches", json=no_scope, headers=_account_only()).status_code == 400
    neither = {"scope": {"labName": LABEL}, "query": "강우"}
    assert client.post("/searches", json=neither, headers=_account_only()).status_code == 400


def test_an_operator_scope_without_a_subject_is_401() -> None:
    assert _client().post("/searches", json=_operator_body()).status_code == 401


def test_the_marker_and_a_lab_together_are_refused() -> None:
    """정확히 하나 — 둘 다 오면 어느 쪽 경계인지 이쪽이 고르게 된다."""
    res = _client().post("/searches", json=_operator_body(labId=LAB), headers=_account_only())
    assert res.status_code == 400, res.text


def test_an_operator_scope_with_a_lab_header_is_refused() -> None:
    """이중 대조 — 본문은 전 연구실, 헤더는 한 연구실이면 경계가 두 곳에서 갈린다."""
    res = _client().post("/searches", json=_operator_body(),
                         headers={"X-CoLAB-Lab": LAB, "X-CoLAB-Account": ACC})
    assert res.status_code == 400, res.text


def test_only_a_literal_true_marker_is_accepted() -> None:
    client = _client()
    for marker in (False, "true", 1, None):
        body = _operator_body()
        body["scope"]["operatorScope"] = marker
        res = client.post("/searches", json=body, headers=_account_only())
        assert res.status_code == 400, (marker, res.text)


def test_a_fake_none_lab_id_is_still_400() -> None:
    """이슈 #158 의 요청 모양 — 비운영자 규칙은 지금과 같다."""
    body = {"scope": {"labId": "None", "labName": LABEL}, "query": "강우"}
    res = _client().post("/searches", json=body, headers=_account_only())
    assert res.status_code == 400, res.text
