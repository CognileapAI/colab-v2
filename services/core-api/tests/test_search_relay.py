"""`searchDatasets` — 자연어 검색 **중계** (`PLAN-SoT §9-〈80〉-㉯ 5`).

`fe-core.yaml` 상단이 「검색 진입점 op 은 아직 없다 — P4 가 연다」로 비워 뒀던 자리다.
승인된 1회 동결 해제가 그 자리를 열었고, **core-api 는 중계만 한다.**

이 파일이 지키는 정본 넷 (`Policy_데이터_찾기` · `CLAUDE.md §3 AI 응답 규격`)
  ① **뒤진 범위를 먼저 밝힌다.** 0건이어도 `scope` 가 먼저다.
  ② **AI 는 식별자·관련도·근거 한 줄만 낸다.** 이름·Lv·잠김은 **core 가 D3·D2 에서 붙인다** —
     두 곳에서 말하면 갈라진다.
  ③ **잠긴 데이터가 결과에서 빠지지 않는다** (§1.3-6). 잠김 표시는 core 가 붙인다.
  ④ **AI 가 없어도 200 이다** — 빈 결과 + `degraded: true`. AI 없이도 v2 는 완결된 제품이다.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from conftest import DS_A1, DS_A2, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX

SEARCH = f"{API_PREFIX}/dataset-searches"


@pytest.fixture()
def fake_ai():
    """`core-ai.yaml#SearchResponse` 를 그대로 흉내 내는 최소 서버.

    **응답 모양을 시험이 재선언하지 않는다** — 계약이 요구하는 세 필드
    (`scope`·`isDataQuery`·`results`)만 낸다.
    """
    state: dict = {"body": None, "status": 200, "seen": []}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
            state["seen"].append(json.loads(raw or b"{}"))
            payload = json.dumps(state["body"] or {}, ensure_ascii=False).encode()
            self.send_response(state["status"])
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    state["url"] = f"http://127.0.0.1:{server.server_address[1]}"
    yield state
    server.shutdown()


def _hit(dataset_id: str, bar: float, why: str) -> dict:
    return {"datasetId": dataset_id, "relevanceBar": bar, "rationale": why}


def _ai_body(hits: list[dict], *, lab_id: str, searched: int = 3,
             is_data_query: bool = True) -> dict:
    return {
        "degraded": False,
        "scope": {"labId": lab_id, "labName": "연구실 A", "searchedCount": searched},
        "isDataQuery": is_data_query,
        "results": {"items": hits, "totalCount": len(hits), "nextCursor": None},
    }


# ═════════════════ ④ AI 가 없어도 200 · 정직한 빈 상태 ═════════════════
def test_without_ai_service_it_is_200_with_degraded_and_no_results(p2_client) -> None:
    """**5xx 로 끝내지 않는다.** 「AI 가 없다」가 「검색 화면이 죽는다」가 되면
    `CLAUDE.md §3` 의 「AI 없이도 v2 는 완결된 제품」이 거짓이 된다."""
    r = p2_client().post(SEARCH, json={"query": "2023년 강수량"}, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["degraded"] is True
    assert body["items"] == []
    assert body["degradedReason"], "왜 비었는지 한 줄이 없으면 빈 상태가 정직하지 않다."


def test_the_honest_empty_state_still_says_what_it_searched(p2_client) -> None:
    """① **뒤진 범위가 먼저다** (`§3.3` — 「우리 연구실 데이터 128개를 뒤졌지만…」)."""
    r = p2_client().post(SEARCH, json={"query": "강수"}, headers=auth(TOKEN_RES))
    scope = r.json()["scope"]
    assert scope["labName"], "범위 표시줄에 세울 이름이 없다."
    assert scope["searchedCount"] >= 1, "0 을 적으면 「아무것도 없는 연구실」이라 말하는 것이다."


# ═════════════════ ② AI 는 세 값만 · 나머지는 core 가 붙인다 ═════════════════
def test_results_are_catalog_rows_enriched_with_the_two_ai_values(p2_client, fake_ai) -> None:
    """AI 가 준 것은 `datasetId`·`relevanceBar`·`rationale` 셋뿐인데
    카드가 그려지려면 이름·Lv·업로더·계보·Verified 가 있어야 한다 — **core 가 붙인다.**"""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body([_hit(DS_A1, 0.9, "이름과 주제가 질의와 겹친다")], lab_id=LAB_A)
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강수"}, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    item = r.json()["items"][0]
    assert item["datasetId"] == DS_A1
    assert item["relevanceBar"] == 0.9
    assert item["rationale"] == "이름과 주제가 질의와 겹친다"
    for field in ("name", "processingLevel", "uploader", "lineageState", "verified",
                  "accessState", "bodyAccessible", "lastModifiedAt", "fileCount", "projects"):
        assert field in item, f"카탈로그 값 {field} 를 core 가 안 붙였다 — 카드가 안 그려진다."


def test_the_order_is_the_relevance_order_the_ai_gave(p2_client, fake_ai) -> None:
    """**순서가 이미 관련도다** (`§4`). core 가 다시 정렬하면 그 사실이 깨진다."""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body([_hit(DS_A2, 0.4, "b"), _hit(DS_A1, 0.9, "a")], lab_id=LAB_A)
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강수"}, headers=auth(TOKEN_RES))
    assert [i["datasetId"] for i in r.json()["items"]] == [DS_A2, DS_A1]


# ═════════════════ ③ 잠긴 데이터를 빼지 않는다 ═════════════════
def test_a_locked_dataset_stays_in_the_results(p2_client, fake_ai) -> None:
    """`§1.3-6` — **결과에서 빼지 않는다.** 시드의 DS_A2 는 잠긴 데이터셋이다.
    빼 버리면 「요청할 상대가 누구인지」를 사용자가 영영 못 본다 (P-13·P-34)."""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body([_hit(DS_A2, 0.7, "요약이 겹친다")], lab_id=LAB_A)
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강수"}, headers=auth(TOKEN_RES))
    ids = [i["datasetId"] for i in r.json()["items"]]
    assert DS_A2 in ids


def test_ids_outside_the_lab_boundary_are_dropped(p2_client, fake_ai) -> None:
    """**AI 가 경계 밖 식별자를 말해도 core 는 붙일 값이 없다** — RLS 가 이미 행을 지웠다.
    지어내서 채우지 않는다 (`CLAUDE.md §3-5` · P-9·P-10)."""
    from conftest import DS_B1, LAB_A
    fake_ai["body"] = _ai_body([_hit(DS_B1, 0.9, "x"), _hit(DS_A1, 0.5, "y")], lab_id=LAB_A)
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강수"}, headers=auth(TOKEN_RES))
    assert [i["datasetId"] for i in r.json()["items"]] == [DS_A1]


# ═════════════════ 경계는 요청에 실리지 않는다 ═════════════════
def test_the_lab_scope_is_injected_by_the_server_not_by_the_caller(p2_client, fake_ai) -> None:
    """`CLAUDE.md §3-5` — FE 는 `labId` 를 보내지 않고 **서버가 주체에서 주입한다.**"""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body([], lab_id=LAB_A)
    p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강수"}, headers=auth(TOKEN_RES))
    assert fake_ai["seen"][-1]["scope"]["labId"] == LAB_A


def test_a_response_from_another_scope_is_discarded(p2_client, fake_ai) -> None:
    """`core-ai.yaml SearchResponse.scope` — 요청의 범위와 다르면 **응답을 버린다.**"""
    from conftest import LAB_B
    fake_ai["body"] = _ai_body([_hit(DS_A1, 0.9, "x")], lab_id=LAB_B)
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강수"}, headers=auth(TOKEN_RES))
    assert r.json()["degraded"] is True
    assert r.json()["items"] == []


# ═════════════════ 데이터를 찾는 질문이 아닐 때 · 입력 규칙 ═════════════════
def test_not_a_data_query_is_a_normal_200_with_no_items(p2_client, fake_ai) -> None:
    """`§9` — 「데이터를 찾는 질문에 답해요」는 **오류가 아니라 정상 응답**이다."""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body([], lab_id=LAB_A, is_data_query=False)
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "안녕"}, headers=auth(TOKEN_RES))
    assert r.status_code == 200
    assert r.json()["isDataQuery"] is False
    assert r.json()["items"] == []


@pytest.mark.parametrize("body", [{}, {"query": ""}, {"query": "가" * 201}])
def test_query_outside_the_input_rule_is_400(p2_client, body) -> None:
    """`§5 검색 질문 — 1~200자`. 규칙 밖을 200 으로 받으면 규칙이 없는 것과 같다."""
    r = p2_client().post(SEARCH, json=body, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text


def test_search_requires_authentication(p2_client) -> None:
    r = p2_client().post(SEARCH, json={"query": "강수"})
    assert r.status_code == 401
