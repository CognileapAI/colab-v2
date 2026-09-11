"""I4 HTTP trace와 구조화 로그 — 외부 동작만 고정한다."""
from __future__ import annotations

import json

from conftest import TOKEN_RES


TRACE_ID = "0123456789abcdef0123456789abcdef"
PARENT_ID = "0123456789abcdef"
TRACEPARENT = f"00-{TRACE_ID}-{PARENT_ID}-01"


def _events(capsys) -> list[dict]:
    out = capsys.readouterr().out
    events = []
    for line in out.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("schema") == "colab.ops.v1":
            events.append(value)
    return events


def test_valid_trace_is_continued_and_query_is_not_logged(p2_client, capsys) -> None:
    client = p2_client()
    response = client.get("/healthz?credential=must-not-appear",
                          headers={"traceparent": TRACEPARENT})

    assert response.status_code == 200
    returned = response.headers["traceparent"].split("-")
    assert returned[0] == "00"
    assert returned[1] == TRACE_ID
    assert returned[2] != PARENT_ID
    assert returned[3] == "01"

    event = [item for item in _events(capsys) if item.get("event") == "http.server.request"][-1]
    assert event["service"] == "core-api"
    assert event["trace_id"] == TRACE_ID
    assert event["parent_span_id"] == PARENT_ID
    assert event["path"] == "/healthz"
    assert event["status"] == 200
    assert event["duration_ms"] >= 0
    assert "must-not-appear" not in json.dumps(event)


def test_invalid_all_zero_trace_is_replaced(p2_client) -> None:
    invalid = "00-00000000000000000000000000000000-0000000000000000-01"
    response = p2_client().get("/healthz", headers={"traceparent": invalid})
    returned = response.headers["traceparent"].split("-")
    assert returned[1] != "0" * 32
    assert returned[2] != "0" * 16


def test_core_relay_propagates_the_current_trace(p2_client, monkeypatch) -> None:
    from colab_core.app import relay

    captured: dict[str, str] = {}

    def fake_request(_url, *, method, headers, body):
        del method, body
        captured.update(headers)
        return 200, {"items": []}

    monkeypatch.setattr(relay, "_request", fake_request)
    client = p2_client(viz_base_url="http://viz.invalid")
    response = client.get("/api/v1/preview-palettes",
                          headers={"Authorization": f"Bearer {TOKEN_RES}",
                                   "traceparent": TRACEPARENT})
    assert response.status_code == 200, response.text
    propagated = captured["traceparent"].split("-")
    assert propagated[1] == TRACE_ID
    assert propagated[2] != PARENT_ID
