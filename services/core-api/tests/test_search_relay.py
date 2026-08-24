"""`searchDatasets` — 자연어 검색 **해석 중계 + 실행 + 조립** (`PLAN-SoT §9-〈80〉-㉯ 5`).

⚠ **2026-08-25 판정 ㈎ 로 이 자리의 몫이 늘었다.** `K4-a` 까지는 ai-service 가 `tsvector` 를
직접 던지고 core-api 는 중계만 했다 — D10 이 D3 테이블에 붙는 도메인 경계 위반이었다
(`CLAUDE.md §3-1`). 이제 **AI 는 질의를 해석만 하고, 찾고 매기는 것은 여기다.**
D3 는 core-api 의 자기 도메인이라 이 실행은 아무 경계도 넘지 않는다.

이 파일이 지키는 정본 다섯 (`Policy_데이터_찾기` · `CLAUDE.md §3 AI 응답 규격`)
  ① **뒤진 범위를 먼저 밝힌다.** 0건이어도 `scope` 가 먼저다.
  ② **AI 는 검색어·필터만 낸다.** 순위는 `tsvector`, 카드 값은 D3·D2·D4·D6 가 낸다.
  ③ **잠긴 데이터가 결과에서 빠지지 않고, 잠김으로 표시되어 온다** (`§1.3-6` · `P-13`·`P-34`).
  ④ **AI 가 없어도 200 이다** — 빈 결과 + `degraded: true`.
  ⑤ **경계는 서버가 주입한다.** FE 도 AI 도 `labId` 를 정하지 않는다.
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
    (`scope`·`isDataQuery`·`results`)에 판정 ㈎ 가 더한 `interpretation` 만 낸다.
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


def _ai_body(terms, *, lab_id, topic=None, source="llm", searched=3,
             is_data_query: bool = True, degraded: bool = False, expansions=None) -> dict:
    body = {
        "degraded": degraded,
        "scope": {"labId": lab_id, "labName": "연구실 A", "searchedCount": searched},
        "isDataQuery": is_data_query,
        "results": {"items": [], "totalCount": 0, "nextCursor": None},
        "interpretation": {"terms": list(terms), "topic": topic, "source": source},
    }
    if expansions is not None:
        body["interpretation"]["expansions"] = expansions
    return body


# ════════ ④ 검색이 죽으면 **「동작하지 않음」이 드러난다** — 0건으로 위장하지 않는다 ════════
#
# ⚠ **2026-08-25 Ted 판정 〈87〉-㉯ 로 이 묶음이 뒤집혔다.** 여기까지의 판은
# 「AI 가 없으면 200 + 0건 + degraded」였다. 그런데 **0건은 「뒤졌는데 없다」는 뜻**이고,
# 못 닿은 상태의 사실은 **「뒤지지도 못했다」**다. 둘을 같은 화면으로 그리면 화면이 거짓말을
# 한다. Ted 의 말 그대로 — 「서비스 죽으면 동작하지 않음이 노출되어야 함. 모니터링 달 거야.」
#
# **`degraded`(해석만 무너짐 · 결과는 진짜)는 그대로 살아 있다** — 아래 마지막 묶음이 지킨다.
def test_a_dead_ai_service_is_503_not_a_zero_hit_result(p2_client) -> None:
    """**0건처럼 보이지 않는다.** 주소가 없어 한 건도 뒤지지 못했다."""
    r = p2_client().post(SEARCH, json={"query": "2023년 강수량"}, headers=auth(TOKEN_RES))
    assert r.status_code == 503, r.text
    body = r.json()
    assert body["code"] == "SEARCH_UNAVAILABLE", "감시가 긁을 코드가 없다."
    assert body["message"], "왜 못 했는지 한 줄이 없으면 정직하지 않다."
    assert "items" not in body and "totalCount" not in body, \
        "0건 봉투를 함께 내면 화면이 「없다」로 그릴 수 있다 — 둘을 섞지 않는다."


def test_an_unreachable_ai_service_is_503_too(p2_client) -> None:
    """주소는 있는데 아무도 안 받는다. **주소 없음과 같은 사실이다** — 뒤지지 못했다."""
    r = p2_client(ai_base_url="http://127.0.0.1:9").post(
        SEARCH, json={"query": "강수"}, headers=auth(TOKEN_RES))
    assert r.status_code == 503, r.text
    assert r.json()["code"] == "SEARCH_UNAVAILABLE"


def test_the_failure_leaves_a_signal_a_monitor_can_scrape(p2_client, caplog) -> None:
    """**감시가 긁을 것이 응답 밖에도 있어야 한다** — Ted 가 모니터링을 붙인다.
    로그 한 줄에 `event`·`code` 가 고정된 이름으로 선다."""
    import logging
    with caplog.at_level(logging.WARNING, logger="colab_core.search"):
        p2_client().post(SEARCH, json={"query": "강수"}, headers=auth(TOKEN_RES))
    hits = [rec for rec in caplog.records if getattr(rec, "event", None) == "search.unavailable"]
    assert hits, "장애가 로그에 이름을 남기지 않았다 — 감시가 붙을 자리가 없다."
    assert hits[0].code == "SEARCH_UNAVAILABLE"
    assert hits[0].reason, "이유 없는 신호는 대시보드에서 아무 말도 못 한다."


def test_the_catalogue_still_works_when_search_is_down(p2_client) -> None:
    """**「검색이 죽었다」가 「제품이 죽었다」가 아니다** (`CLAUDE.md §3`).
    503 은 검색 op 하나에만 서고 카탈로그는 그대로 돈다 — 화면의 카탈로그 링크가 공허하지 않다."""
    client = p2_client()
    assert client.post(SEARCH, json={"query": "강수"},
                       headers=auth(TOKEN_RES)).status_code == 503
    r = client.get(f"{API_PREFIX}/datasets", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert r.json()["items"], "카탈로그가 비면 「카탈로그에서 직접 찾기」 안내가 거짓이 된다."


# ═════════════════ ② AI 는 검색어만 · 나머지는 core 가 만든다 ═════════════════
def test_results_are_catalog_rows_found_by_core_and_enriched(p2_client, fake_ai) -> None:
    """AI 가 준 것은 **검색어뿐**이다. 후보·순위·근거는 core 의 `tsvector` 가 내고,
    카드 값(이름·Lv·업로더·계보·Verified·잠김)은 core 가 D3·D2·D4·D6 에서 붙인다."""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body(["강우"], lab_id=LAB_A)
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강우"}, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert {i["datasetId"] for i in items} == {DS_A1, DS_A2}
    item = items[0]
    assert 0.0 <= item["relevanceBar"] <= 1.0
    assert item["rationale"] and "\n" not in item["rationale"]
    for field in ("name", "processingLevel", "uploader", "lineageState", "verified",
                  "accessState", "bodyAccessible", "lastModifiedAt", "fileCount", "projects"):
        assert field in item, f"카탈로그 값 {field} 를 core 가 안 붙였다 — 카드가 안 그려진다."


def test_the_ai_never_names_a_dataset(p2_client, fake_ai) -> None:
    """**AI 가 식별자를 말해도 읽지 않는다.** 읽는 순간 순서가 모델의 것이 되고
    같은 질의가 때마다 다른 답을 낸다 (`〈72〉-㉮`)."""
    from conftest import DS_B1, LAB_A
    body = _ai_body(["염분"], lab_id=LAB_A)
    body["results"]["items"] = [{"datasetId": DS_B1, "relevanceBar": 1.0, "rationale": "x"}]
    fake_ai["body"] = body
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "염분"}, headers=auth(TOKEN_RES))
    assert r.json()["items"] == [], "AI 가 얹어 보낸 식별자가 결과로 샜다."


def test_the_order_is_the_tsvector_relevance_order(p2_client, fake_ai) -> None:
    """**순서가 이미 관련도다** (`§4`). 「격자화」는 A2 의 이름에만 있고 이름 가중치가 A 다."""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body(["강우", "격자화"], lab_id=LAB_A)
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강우 격자화"}, headers=auth(TOKEN_RES))
    assert [i["datasetId"] for i in r.json()["items"]] == [DS_A2, DS_A1]


def test_the_same_query_gives_the_same_order(p2_client, fake_ai) -> None:
    """순위 재현성 — 평가셋이 회귀를 잡으려면 같은 입력이 같은 순서를 내야 한다."""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body(["강우"], lab_id=LAB_A)
    client = p2_client(ai_base_url=fake_ai["url"])
    runs = [[i["datasetId"] for i in client.post(
        SEARCH, json={"query": "강우"}, headers=auth(TOKEN_RES)).json()["items"]]
        for _ in range(3)]
    assert runs[0] == runs[1] == runs[2]


# ═════════════════ ③ 잠긴 데이터 — 빼지 않고, **표시해서** 낸다 ═════════════════
def test_a_locked_dataset_stays_in_the_results_and_is_marked(p2_client, fake_ai) -> None:
    """`§1.3-6` — **결과에서 빼지 않는다.** 빼 버리면 「요청할 상대가 누구인지」를
    사용자가 영영 못 본다 (`P-13`·`P-34`).

    ⚠ **`K4-a` 는 잠긴 `DS_A2` 를 표시 없이 돌려줬다** — D10 이 D2 를 못 읽었기 때문이다.
    실행이 core-api 로 온 지금 그 사유가 사라졌다. 이름·요약은 서고 본체는 잠김으로 선다."""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body(["강우"], lab_id=LAB_A)
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강우"}, headers=auth(TOKEN_RES))
    locked = next(i for i in r.json()["items"] if i["datasetId"] == DS_A2)
    assert locked["accessState"] == "잠김"
    assert locked["bodyAccessible"] is False
    assert locked["name"], "이름은 보여야 한다 — 없는 것으로 만들면 요청할 상대가 사라진다."

    opened = next(i for i in r.json()["items"] if i["datasetId"] == DS_A1)
    assert opened["bodyAccessible"] is True, "표시가 공허하지 않다 — 열린 것은 열림으로 온다."


# ═════════════════ ⑤ 경계 ═════════════════
def test_the_lab_scope_is_injected_by_the_server_not_by_the_caller(p2_client, fake_ai) -> None:
    """`CLAUDE.md §3-5` — FE 는 `labId` 를 보내지 않고 **서버가 주체에서 주입한다.**"""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body([], lab_id=LAB_A)
    p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강수"}, headers=auth(TOKEN_RES))
    assert fake_ai["seen"][-1]["scope"]["labId"] == LAB_A


def test_the_ai_never_sees_the_lab_boundary_as_a_search_term(p2_client, fake_ai) -> None:
    """경계는 요청의 `scope` 로만 간다 — 질의 문자열에 실려 나가지 않는다."""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body(["강우"], lab_id=LAB_A)
    p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강우"}, headers=auth(TOKEN_RES))
    assert fake_ai["seen"][-1]["query"] == "강우"


def test_another_labs_dataset_never_comes_back(p2_client, fake_ai) -> None:
    """cross-tenant 음성 — 다른 연구실 데이터셋의 낱말로 찾아도 0건이다.
    **RLS 가 지운다.** 그리고 위 시험들이 A 의 낱말로 2건을 내므로 음성이 공허하지 않다."""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body(["토지피복"], lab_id=LAB_A)
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "토지피복"}, headers=auth(TOKEN_RES))
    assert r.json()["items"] == []


def test_a_response_from_another_scope_is_discarded(p2_client, fake_ai) -> None:
    """`core-ai.yaml SearchResponse.scope` — 요청의 범위와 다르면 **응답을 버린다.**

    버린 뒤에 남는 사실은 **「뒤지지 못했다」**다. 0건이 아니라 503 이다 (`〈87〉-㉯`)."""
    from conftest import LAB_B
    fake_ai["body"] = _ai_body(["강우"], lab_id=LAB_B)
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강우"}, headers=auth(TOKEN_RES))
    assert r.status_code == 503, r.text
    assert r.json()["code"] == "SEARCH_UNAVAILABLE"


# ═════════════════ AI 가 해석에 실패해도 검색은 돈다 ═════════════════
def test_a_degraded_interpretation_still_searches(p2_client, fake_ai) -> None:
    """**「AI 없이도 검색이 돈다」** — 모델이 죽어 낱말 그대로 온 검색어로도 결과가 나오고,
    근거 한 줄이 그 사실을 숨기지 않는다."""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body(["강우"], lab_id=LAB_A, source="literal", degraded=True)
    fake_ai["body"]["degradedReason"] = "질의 해석 모델 자격 증명이 없다 — 낱말 그대로 찾았다."
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강우"}, headers=auth(TOKEN_RES))
    body = r.json()
    assert body["degraded"] is True and body["degradedReason"]
    assert len(body["items"]) == 2
    assert all("질의 해석 없이" in i["rationale"] for i in body["items"])


def test_an_unreadable_answer_is_not_a_zero_hit_result(p2_client, fake_ai) -> None:
    """해석을 아예 못 읽었으면 **검색어가 없어 한 건도 뒤지지 않았다.**

    ⚠ **여기가 `degraded` 와 갈리는 자리다.** 위 시험(`literal`)은 검색어가 있어서 **진짜로
    뒤졌고 진짜 결과가 나왔다** — 그래서 200 이다. 이쪽은 뒤진 적이 없다 — 그래서 503 이다."""
    from conftest import LAB_A
    body = _ai_body([], lab_id=LAB_A)
    body.pop("interpretation")
    fake_ai["body"] = body
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강우"}, headers=auth(TOKEN_RES))
    assert r.status_code == 503, r.text
    assert r.json()["code"] == "SEARCH_UNAVAILABLE"


def test_ai_answering_with_an_error_status_is_503(p2_client, fake_ai) -> None:
    """저쪽이 5xx 로 답했다. **그 상태코드를 0건으로 번역하지 않는다.**"""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body(["강우"], lab_id=LAB_A)
    fake_ai["status"] = 500
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "강우"}, headers=auth(TOKEN_RES))
    assert r.status_code == 503, r.text
    assert r.json()["code"] == "SEARCH_UNAVAILABLE"


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


def test_zero_hits_is_a_normal_200(p2_client, fake_ai) -> None:
    """**0건은 막다른 길이 아니라 다음 행동을 안내할 상태다** (`§1.3-7`)."""
    from conftest import LAB_A
    fake_ai["body"] = _ai_body(["염분"], lab_id=LAB_A)
    r = p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": "염분"}, headers=auth(TOKEN_RES))
    body = r.json()
    assert r.status_code == 200 and body["items"] == [] and body["totalCount"] == 0
    assert body["degraded"] is False, "0건은 장애가 아니다."
    assert body["scope"]["searchedCount"] >= 1


@pytest.mark.parametrize("body", [{}, {"query": ""}, {"query": "가" * 201}])
def test_query_outside_the_input_rule_is_400(p2_client, body) -> None:
    """`§5 검색 질문 — 1~200자`. 규칙 밖을 200 으로 받으면 규칙이 없는 것과 같다."""
    r = p2_client().post(SEARCH, json=body, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text


def test_search_requires_authentication(p2_client) -> None:
    r = p2_client().post(SEARCH, json={"query": "강수"})
    assert r.status_code == 401


# ════════ K4-b — 그래프 확장이 **HTTP 를 지나서도** 근거가 된다 (`〈90〉-㉱`) ════════
#
# core-api 는 그래프에 붙지 않는다. 붙으면 2026-08-25 판정 ㈎ 로 고친 위반의 거울상이다
# (`PLAN-SoT §9-〈90〉-㉮`). 그래서 이쪽이 받는 것은 **행이 아니라 말과 그 엣지**이고,
# 아래 셋이 「받은 것을 믿고 쓰지 않고 검사하고 쓴다」를 붙잡는다.

def _graph_search(p2_client, fake_ai, expansions, *, terms=("강우",), query="강우"):
    from conftest import LAB_A
    fake_ai["body"] = _ai_body(list(terms), lab_id=LAB_A, expansions=expansions)
    return p2_client(ai_base_url=fake_ai["url"]).post(
        SEARCH, json={"query": query}, headers=auth(TOKEN_RES))


def test_graph_expansion_reaches_the_rationale(p2_client, fake_ai) -> None:
    r = _graph_search(p2_client, fake_ai,
                      [{"term": "강우", "relation": "~의 한 가지다", "parent": "강수"}])
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert items and all("‘강수’의 한 가지인 ‘강우’" in i["rationale"] for i in items)


def test_an_expansion_for_a_term_we_never_searched_is_dropped(p2_client, fake_ai) -> None:
    """**근거가 하지 않은 검색을 말하지 않는다** — `terms` 에 없는 말은 버린다."""
    r = _graph_search(p2_client, fake_ai,
                      [{"term": "재격자화", "relation": "~의 한 가지다", "parent": "전처리"}])
    assert r.status_code == 200
    assert all("재격자화" not in i["rationale"] for i in r.json()["items"])


def test_a_malformed_expansion_does_not_break_search(p2_client, fake_ai) -> None:
    """모양이 계약과 다르면 **그 행만 버리고 검색은 그대로 돈다.**"""
    r = _graph_search(p2_client, fake_ai, ["쓰레기", {"term": "강우"}, {}])
    assert r.status_code == 200 and r.json()["items"]


def test_no_expansions_means_the_old_sentence(p2_client, fake_ai) -> None:
    """선택 속성이다 — 안 오면 예전 근거 그대로다(하위 호환)."""
    r = _graph_search(p2_client, fake_ai, None)
    assert r.status_code == 200
    assert all("한 가지" not in i["rationale"] for i in r.json()["items"])
