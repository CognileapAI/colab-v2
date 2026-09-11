#!/usr/bin/env bash
# dev의 네 서비스가 200뿐 아니라 자기 unit으로 응답하는지 본다.
set -uo pipefail
python3 - <<'PY'
import json
import sys
import urllib.error
import urllib.request

targets = {
    "core-api": "http://127.0.0.1:8000/healthz",
    "pipeline-worker": "http://127.0.0.1:8001/healthz",
    "viz-render": "http://127.0.0.1:8100/healthz",
    "ai-service": "http://127.0.0.1:8200/healthz",
}
failed = 0
for unit, url in targets.items():
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            body = response.read(65536)
            code = response.status
        value = json.loads(body)
        if code != 200 or not isinstance(value, dict) or value.get("unit") != unit:
            raise ValueError("status/body identity mismatch")
        print(f"service-health green — {unit} 200 · unit 일치")
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as exc:
        print(f"service-health red — {unit}: {type(exc).__name__}", file=sys.stderr)
        failed += 1
raise SystemExit(1 if failed else 0)
PY
