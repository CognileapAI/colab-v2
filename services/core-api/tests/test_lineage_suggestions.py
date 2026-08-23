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
