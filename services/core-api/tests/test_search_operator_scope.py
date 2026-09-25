"""무소속 시스템 관리자(운영자)의 자료 검색 — **운영자 범위 표식**으로 연다.

intent `dev-package/intent/2026-09-25-operator-search-scope.md` (이슈 #158) 의 오라클 —
  ⑴ 요청: 운영자는 ai-service 에 `scope.operatorScope: true` 를 보내고 `labId` 도 헤더
     `X-CoLAB-Lab` 도 싣지 않는다. 문자열 `"None"` 이 본문 어디에도 없다(Q1·Q6).
  ⑵ 응답: 되비춘 운영자 범위를 받아 200 이고, 응답 `scope` 는 `AiOperatorSearchScope` 모양이다.
     `searchedCount` 는 결과와 같은 범위(전 연구실)에서 센 값이다.
  ⑶ 되비춤이 다르면(운영자 요청에 연구실 범위가 돌아오면) 버린다 → 503 (이중 대조).
  ⑷ 운영자 결과 카드마다 소속 연구실 이름(`labName`)이 붙는다(Q2). 비운영자에게는 없다.
  ⑸ 조건 검색 갈래도 운영자 범위로 답하고, 검토된 근거를 전 연구실에서 읽는다(Q7).

⚠ 비운영자 대조군은 `test_search_scope.py` 가 그대로 지킨다. 여기서는 비운영자의 **요청 본문과
헤더가 종전 그대로인지**만 한 번 더 본다.
"""
from __future__ import annotations

import json

import pytest
from conftest import ACC_A_RES, LAB_A, LAB_B, TOKEN_RES, auth
from test_search_relay import _ai_body, fake_ai  # noqa: F401  (픽스처 재사용)

from colab_core.app.main import API_PREFIX

SEARCH = f"{API_PREFIX}/dataset-searches"
OPERATOR_SCOPE_LABEL = "전체 연구실"
OPERATOR_TOKEN = "labless-operator-token"
#: 시드의 두 연구실에 하나씩 있는 이름 낱말 — `A 강우 원자료` · `B 토지피복 원자료`.
TERMS = ["원자료"]


def _operator():
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    return Subject(account_id=Ulid(ACC_A_RES), lab_id=None, operator=True)


def _operator_ai_body(terms, **kw) -> dict:
    body = _ai_body(terms, lab_id=LAB_A, **kw)
    body["scope"] = {"operatorScope": True, "labName": OPERATOR_SCOPE_LABEL,
                     "searchedCount": kw.get("searched", 3)}
    return body


def _with_operator(client):
    inner = client.app.state.authenticators
    operator = _operator()

    class _WithOperator:
        adapters = getattr(inner, "adapters", ())

        def resolve(self, token: str):
            return operator if token == OPERATOR_TOKEN else inner.resolve(token)

    client.app.state.authenticators = _WithOperator()
    return client


@pytest.fixture()
def labless_operator(p2_client, fake_ai):  # noqa: F811
    fake_ai["body"] = _operator_ai_body(TERMS)
    return _with_operator(p2_client(ai_base_url=fake_ai["url"]))


def _every_dataset_lab_name(session_factory) -> dict[str, str]:
    """운영자 읽기 스코프에서 데이터셋 → 연구실 이름. 라우트의 결과 스코프와 같은 인자다."""
    from sqlalchemy import text

    from colab_core.kernel.scope import read_only_scope
    with read_only_scope(session_factory, _operator(), operator_read=True) as ro:
        rows = ro.execute(text(
            "SELECT d.id, l.name FROM d3_dataset d JOIN d1_lab l ON l.id = d.lab_id "
            "WHERE d.deleted_at IS NULL")).mappings()
        return {str(r["id"]).strip(): r["name"] for r in rows}


# ════════ ⑴ 요청 — 운영자 표식을 명시적으로 넘긴다 ════════

def test_a_labless_operator_sends_the_operator_marker_not_a_fake_lab(labless_operator,
                                                                    fake_ai) -> None:  # noqa: F811
    r = labless_operator.post(SEARCH, json={"query": "원자료"}, headers=auth(OPERATOR_TOKEN))
    assert r.status_code == 200, r.text
    sent = fake_ai["seen"][-1]
    assert sent["scope"]["operatorScope"] is True
    assert sent["scope"]["labName"] == OPERATOR_SCOPE_LABEL
    assert "labId" not in sent["scope"], f"운영자 요청에 연구실 식별자가 실렸다: {sent['scope']}"
    assert "None" not in json.dumps(sent, ensure_ascii=False), \
        "가짜 식별자 `None` 이 ai-service 요청에 실렸다(이슈 #158)."
    headers = {k.lower(): v for k, v in fake_ai["headers"][-1].items()}
    assert "x-colab-lab" not in headers, \
        "운영자 범위인데 헤더가 한 연구실을 말한다 — 경계가 두 곳에서 갈린다."
    assert headers.get("x-colab-account") == ACC_A_RES, "주체 헤더는 그대로 필수다."


def test_a_member_request_to_the_ai_service_is_unchanged(p2_client, fake_ai) -> None:  # noqa: F811
    """⑸-대조 — 비운영자는 종전 그대로 `labId` 와 `X-CoLAB-Lab` 을 보낸다."""
    fake_ai["body"] = _ai_body(TERMS, lab_id=LAB_A)
    r = p2_client(ai_base_url=fake_ai["url"]).post(SEARCH, json={"query": "원자료"},
                                                   headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    sent = fake_ai["seen"][-1]
    assert list(sent["scope"]) == ["labId", "labName", "searchedCount"]
    assert sent["scope"]["labId"] == LAB_A
    headers = {k.lower(): v for k, v in fake_ai["headers"][-1].items()}
    assert headers.get("x-colab-lab") == LAB_A
    assert "labName" not in r.json()["items"][0], "비운영자 카드에 연구실 이름 칸이 생겼다."


# ════════ ⑵ 응답 — 운영자 범위 변형으로 답한다 ════════

def test_the_operator_response_scope_is_the_operator_variant(labless_operator,
                                                             session_factory) -> None:
    r = labless_operator.post(SEARCH, json={"query": "원자료"}, headers=auth(OPERATOR_TOKEN))
    assert r.status_code == 200, r.text
    scope = r.json()["scope"]
    assert set(scope) == {"operatorScope", "labName", "searchedCount"}, scope
    assert scope["operatorScope"] is True
    assert scope["labName"] == OPERATOR_SCOPE_LABEL
    assert scope["searchedCount"] == len(_every_dataset_lab_name(session_factory))
    assert "None" not in r.text


# ════════ ⑶ 되비춤이 다르면 버린다 ════════

def test_a_lab_scope_echo_to_an_operator_request_is_discarded(labless_operator,
                                                             fake_ai) -> None:  # noqa: F811
    fake_ai["body"] = _ai_body(TERMS, lab_id=LAB_A)
    r = labless_operator.post(SEARCH, json={"query": "원자료"}, headers=auth(OPERATOR_TOKEN))
    assert r.status_code == 503, r.text
    assert r.json()["code"] == "SEARCH_UNAVAILABLE"


def test_an_operator_echo_to_a_member_request_is_discarded(p2_client, fake_ai) -> None:  # noqa: F811
    fake_ai["body"] = _operator_ai_body(TERMS)
    r = p2_client(ai_base_url=fake_ai["url"]).post(SEARCH, json={"query": "원자료"},
                                                   headers=auth(TOKEN_RES))
    assert r.status_code == 503, r.text


# ════════ ⑷ 운영자 카드에 연구실 이름 ════════

def test_operator_cards_carry_their_own_lab_name(labless_operator, session_factory) -> None:
    r = labless_operator.post(SEARCH, json={"query": "원자료"}, headers=auth(OPERATOR_TOKEN))
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    expected = _every_dataset_lab_name(session_factory)
    assert items, "운영자 결과가 비었다 — 시드의 `원자료` 두 건이 보여야 한다."
    for row in items:
        assert row["labName"] == expected[row["datasetId"]], row
    names = {row["labName"] for row in items}
    assert {"A 연구실", "B 연구실"} <= names, \
        f"전 연구실 결과가 아니다 — 두 연구실이 함께 나와야 한다: {names}"


# ════════ ⑸ 조건 검색 갈래 — 운영자 범위 · 검토된 근거(Q7) ════════

def test_the_typed_search_answers_an_operator_from_every_lab(p2_client, sql,
                                                            monkeypatch) -> None:
    """무소속 운영자에게 `d3_search_evidence` 가 0행이면 조건 검색 후보가 0건이다(Q7)."""
    from test_client_search import CASES, CLOCK, _dataset

    from colab_core.app import client_search
    original = client_search.plan_query
    monkeypatch.setattr(client_search, "plan_query",
                        lambda query, **kw: original(query, now=CLOCK, **kw))
    client = _with_operator(p2_client())
    good, _ = _dataset(sql, client, {"variable": "precipitation", "region": "seoul",
                                     "representation": "spatial_grid"})
    r = client.post(SEARCH, json={"query": CASES[2]["query"]}, headers=auth(OPERATOR_TOKEN))
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body["scope"]) == {"operatorScope", "labName", "searchedCount"}, body["scope"]
    assert body["scope"]["operatorScope"] is True
    by_id = {row["datasetId"]: row for row in body["items"]}
    assert good in by_id, f"운영자가 검토된 근거로 확인된 자료를 못 찾았다: {body}"
    assert by_id[good]["labName"] == "A 연구실"
    assert LAB_B not in json.dumps(body["scope"])
