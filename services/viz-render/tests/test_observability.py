"""I4 viz-render 요청 trace와 JSON 로그."""
from __future__ import annotations

import json


TRACE_ID = "fedcba9876543210fedcba9876543210"
TRACEPARENT = f"00-{TRACE_ID}-1111111111111111-00"


def test_viz_continues_trace_and_emits_json_without_query(client, capsys) -> None:
    response = client.get("/healthz?token=must-not-appear",
                          headers={"traceparent": TRACEPARENT})
    assert response.status_code == 200
    assert response.headers["traceparent"].split("-")[1] == TRACE_ID

    events = []
    for line in capsys.readouterr().out.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if value.get("event") == "http.server.request":
            events.append(value)
    event = events[-1]
    assert event["service"] == "viz-render"
    assert event["trace_id"] == TRACE_ID
    assert event["path"] == "/healthz"
    assert "must-not-appear" not in json.dumps(event)
