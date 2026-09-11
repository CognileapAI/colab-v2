"""I4 ai-service 요청 trace와 JSON 로그."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from colab_ai.app.main import create_app
from colab_ai.kernel.config import Settings


def test_ai_creates_trace_and_emits_required_json_fields(capsys) -> None:
    response = TestClient(create_app(Settings())).get("/healthz")
    assert response.status_code == 200
    parts = response.headers["traceparent"].split("-")
    assert len(parts) == 4 and len(parts[1]) == 32 and len(parts[2]) == 16

    events = []
    for line in capsys.readouterr().out.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if value.get("event") == "http.server.request":
            events.append(value)
    event = events[-1]
    assert event["schema"] == "colab.ops.v1"
    assert event["service"] == "ai-service"
    assert event["level"] == "INFO"
    assert event["status"] == 200
    assert event["timestamp"].endswith("Z")
