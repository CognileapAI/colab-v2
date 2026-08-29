"""`listUploadLineageSuggestions` — 중계, 그리고 **정직한 빈 상태**.

`ai-service` 가 지금 비어 있으므로 이 op 이 낼 수 있는 참인 답은 **0건**이다.
그것을 200 + `degraded: true` + 빈 배열로 말한다 (`P2.md §2-8`).

**억지 제안을 만들지 않는다.** 그리고 5xx 로 끝내지도 않는다 —
`AI 없이도 v2 는 완결된 제품이다` (`CLAUDE.md §3`). AI 가 없다는 사실이
「업로드를 못 한다」가 되면 그 성질을 잃는다.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from conftest import LAB_A, TOKEN_RES, auth
from test_dataset_registration import make_upload

from colab_core.app.main import API_PREFIX


def _get(client, upload_id, **params):
    return client.get(f"{API_PREFIX}/uploads/{upload_id}/lineage-suggestions",
                      params=params, headers=auth(TOKEN_RES))


# ═════════════════════ ai-service 가 없을 때 (지금) ═════════════════════════
def test_with_no_ai_service_the_answer_is_zero_suggestions_not_an_error(p2_client) -> None:
    client = p2_client(ai_base_url=None)
    receipt = make_upload(client)
    r = _get(client, receipt["uploadId"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["suggestions"] == []
    assert body["degraded"] is True
    assert body["degradedReason"], "무엇이 없어서 0건인지 한 줄로 말해야 한다."


def test_the_searched_scope_comes_before_the_suggestions(p2_client) -> None:
    """**먼저 밝히는 범위** — 무엇을 근거로 삼았는지를 제안보다 앞에 둔다
    (`CLAUDE.md §3` · `AiSearchScope`). 0건이어도 어디를 찾았는지 말한다."""
    client = p2_client(ai_base_url=None)
    receipt = make_upload(client)
    scope = _get(client, receipt["uploadId"]).json()["scope"]
    assert scope["labId"] == LAB_A
    assert scope["labName"] == "A 연구실"
    # **연구실 경계 안에서 센다** — 시드의 3건 중 A 연구실 것은 둘이다(DSB1 은 B 것).
    # 범위 셈이 경계를 넘으면 「뒤진 범위」가 남의 연구실을 포함했다고 말하게 된다.
    assert scope["searchedCount"] == 2, "A 연구실의 데이터셋 2건을 뒤진 범위로 밝혀야 한다."


def test_no_confidence_percentage_field_exists_anywhere(p2_client) -> None:
    """확신도는 `확실|애매|모름` **enum** 이고 **숫자·퍼센트 필드가 없다** (`CLAUDE.md §3`)."""
    client = p2_client(ai_base_url=None)
    receipt = make_upload(client)
    body = json.dumps(_get(client, receipt["uploadId"]).json(), ensure_ascii=False)
    for forbidden in ("score", "confidencePercent", "probability", "%"):
        assert forbidden not in body


def test_a_missing_or_expired_upload_is_404(p2_client, sql) -> None:
    client = p2_client(ttl_hours=1, ai_base_url=None)
    receipt = make_upload(client)
    sql("UPDATE d5_upload SET created_at = created_at - interval '2 hours',"
        "                     expires_at = expires_at - interval '2 hours' WHERE id = :u",
        {"u": receipt["uploadId"]})
    assert _get(client, receipt["uploadId"]).status_code == 404


# ═════════════════════ ai-service 가 생겼을 때 (중계) ═══════════════════════
class _FakeAi(BaseHTTPRequestHandler):
    payload: dict = {}
    status: int = 200

    def do_POST(self) -> None:                                    # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        raw = json.dumps(_FakeAi.payload).encode()
        self.send_response(_FakeAi.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args) -> None:
        return


@pytest.fixture()
def fake_ai():
    server = HTTPServer(("127.0.0.1", 0), _FakeAi)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}", _FakeAi
    server.shutdown()
    server.server_close()


def test_a_real_answer_is_relayed_without_reshaping(p2_client, fake_ai) -> None:
    """스키마는 중계라 **재선언하지 않는다** — `core-ai.yaml` 정의를 그대로 지난다."""
    base, fake = fake_ai
    fake.status = 200
    fake.payload = {
        "degraded": False,
        "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 3},
        "rawDataLikely": False,
        "suggestions": [{"suggestionId": "01ARZ3NDEKTSV4RRFFQ69G5FAV", "kind": "가공 전 데이터",
                         "confidence": "애매", "rationale": "이름이 비슷하다"}],
    }
    client = p2_client(ai_base_url=base)
    receipt = make_upload(client)
    body = _get(client, receipt["uploadId"]).json()
    assert body == fake.payload
    assert body["suggestions"][0]["confidence"] in ("확실", "애매", "모름")


def test_an_answer_from_another_lab_is_thrown_away(p2_client, fake_ai) -> None:
    """**요청의 범위와 다르면 응답을 버린다** (`core-ai.yaml LineageSuggestionResponse.scope`).

    버린 자리를 5xx 가 아니라 **0건**으로 메운다 — 화면은 계속 그려져야 한다.
    """
    base, fake = fake_ai
    fake.status = 200
    fake.payload = {
        "degraded": False,
        "scope": {"labId": "0000000000000000000000000B", "labName": "B 연구실",
                  "searchedCount": 9},
        "rawDataLikely": True,
        "suggestions": [{"suggestionId": "01ARZ3NDEKTSV4RRFFQ69G5FAV", "kind": "가공 전 데이터",
                         "confidence": "확실", "rationale": "남의 연구실 근거"}],
    }
    client = p2_client(ai_base_url=base)
    receipt = make_upload(client)
    body = _get(client, receipt["uploadId"]).json()
    assert body["suggestions"] == []
    assert body["degraded"] is True
    assert body["scope"]["labId"] == LAB_A


def test_an_ai_failure_degrades_instead_of_breaking_the_upload_screen(p2_client, fake_ai) -> None:
    base, fake = fake_ai
    fake.status = 500
    fake.payload = {"code": "INTERNAL", "message": "터졌다"}
    client = p2_client(ai_base_url=base)
    receipt = make_upload(client)
    r = _get(client, receipt["uploadId"])
    assert r.status_code == 200, "AI 장애가 제품을 멈췄다."
    assert r.json()["suggestions"] == []
    assert r.json()["degraded"] is True


# ═══════ 0건의 두 뜻을 가른다 (`PLAN-SoT §9 〈211〉`-㉮ 음성 판정) ═══════════
#
# ⚠ **제안 기능은 데이터가 없으면 무엇이든 0건이라 음성 테스트가 공짜로 통과한다.**
# 「제안하지 않았다」가 값어치를 가지려면 **제안이 가능했던 자리에서 하지 않은 것**이어야 한다.
# 그래서 아래 둘을 픽스처로 갈라 둔다 — 응답만 보고도 구별되어야 한다.
#
#   ㈏ searched-none    뒤질 대상이 **있었고**, 서비스가 **답했고**, 0건이 **참인 답**이다.
#                       → `degraded: false` · `scope.searchedCount > 0` · `suggestions: []`
#   ㈎ nothing-to-search 뒤질 대상이 **0건**이었다. 제안이 가능했던 적이 없다.
#                       → `scope.searchedCount == 0`
#   ㈐ not-asked        물어보지 못했다. 「없다」가 아니라 **모른다**다.
#                       → `degraded: true` + `degradedReason`


def test_a_live_service_that_searched_real_candidates_and_returned_none(
        p2_client, fake_ai) -> None:
    """㈏ **제안이 가능했으나 하지 않았다** — 이 자리가 음성 판정의 본체다.

    ai-service 가 살아 있고, 연구실 안에 뒤질 데이터셋이 실재하고(2건), 그 서비스가
    **0건을 참인 답으로** 돌려준다. 억지 제안이 만들어지지 않았음이 여기서 증명된다.
    """
    base, fake = fake_ai
    fake.status = 200
    fake.payload = {
        "degraded": False,
        "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 2},
        "rawDataLikely": False,
        "suggestions": [],
    }
    client = p2_client(ai_base_url=base)
    receipt = make_upload(client)
    body = _get(client, receipt["uploadId"]).json()
    assert body["suggestions"] == []
    # **`degraded` 가 거짓이어야 한다** — 참이면 「못 물어봤다」가 되어 음성 판정이 아니다.
    assert body["degraded"] is False, "물어보지 못한 것을 「제안 안 함」으로 세면 안 된다."
    # **뒤진 대상이 0 이 아니어야 한다** — 0 이면 애초에 제안이 가능하지 않았다.
    assert body["scope"]["searchedCount"] > 0, "뒤질 대상이 없으면 음성 판정이 공짜다."
    assert "degradedReason" not in body or not body.get("degradedReason")


def test_a_scope_with_no_candidates_is_not_the_same_as_searched_and_found_none(
        p2_client, fake_ai, monkeypatch) -> None:
    """㈎ **뒤질 대상이 0건** — 「찾지 못했다」가 아니라 「살펴볼 것이 없었다」다.

    두 응답이 **같은 모양이면 화면이 구별할 수 없다.** 여기서 갈리는 값은 `scope.searchedCount`.
    """
    from colab_core.app.routes import ingestion as _ing
    monkeypatch.setattr(_ing.d3_catalog, "count_datasets", lambda db: 0)

    base, fake = fake_ai
    fake.status = 200
    fake.payload = {
        "degraded": False,
        "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 0},
        "rawDataLikely": False,
        "suggestions": [],
    }
    client = p2_client(ai_base_url=base)
    receipt = make_upload(client)
    body = _get(client, receipt["uploadId"]).json()
    assert body["suggestions"] == []
    assert body["scope"]["searchedCount"] == 0


def test_the_three_zero_states_are_distinguishable_from_the_response_alone(
        p2_client, fake_ai, monkeypatch) -> None:
    """세 0건이 **응답만으로** 갈린다 — 갈리지 않으면 화면은 거짓말밖에 못 한다.

    ⚠ 이 시험이 이 항목의 green-by-skip 방지다. 위 셋을 따로 통과시켜도 셋이 **같은 값**이면
    「제안하지 않았다」는 아무것도 증명하지 않는다.
    """
    def kind(body: dict) -> str:
        if body["degraded"]:
            return "not-asked"
        return "nothing-to-search" if body["scope"]["searchedCount"] == 0 else "searched-none"

    base, fake = fake_ai
    fake.status = 200

    # ㈏ 살펴봤고 0건이 참이다
    fake.payload = {"degraded": False,
                    "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 2},
                    "rawDataLikely": False, "suggestions": []}
    c = p2_client(ai_base_url=base)
    searched_none = _get(c, make_upload(c)["uploadId"]).json()

    # ㈐ 물어보지 못했다
    c2 = p2_client(ai_base_url=None)
    not_asked = _get(c2, make_upload(c2)["uploadId"]).json()

    # ㈎ 뒤질 대상이 0건
    from colab_core.app.routes import ingestion as _ing
    monkeypatch.setattr(_ing.d3_catalog, "count_datasets", lambda db: 0)
    fake.payload = {"degraded": False,
                    "scope": {"labId": LAB_A, "labName": "A 연구실", "searchedCount": 0},
                    "rawDataLikely": False, "suggestions": []}
    c3 = p2_client(ai_base_url=base)
    nothing_to_search = _get(c3, make_upload(c3)["uploadId"]).json()

    assert all(b["suggestions"] == [] for b in (searched_none, not_asked, nothing_to_search))
    kinds = {kind(searched_none), kind(not_asked), kind(nothing_to_search)}
    assert kinds == {"searched-none", "not-asked", "nothing-to-search"}, (
        f"세 0건이 응답에서 갈리지 않는다: {kinds}")
