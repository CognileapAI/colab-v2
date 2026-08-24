"""`/healthz` 본문 판정 — 상태 코드만으로는 이 단위의 생사를 못 본다.

`03-HANDOFF §4` #23 의 자리다. 실이미지의 `/healthz` 가 `implemented: false` 를 냈다.
`〈73〉` 이 워커 루프를 켠 뒤로 그 값은 사실과 어긋나고, **본문 대조로 판정하는 모든 검증이
이 단위를 「빈 단위」로 읽게 만든다.** 자리표시가 전 경로 200 을 내므로 코드로는 구분되지 않는다.
"""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from colab_pipeline.app import health


@pytest.fixture()
def base_url():
    server = ThreadingHTTPServer(("127.0.0.1", 0), health._Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def test_healthz_reports_implemented(base_url):
    with urllib.request.urlopen(f"{base_url}{health.PATH}") as response:
        assert response.status == 200
        body = json.loads(response.read().decode("utf-8"))

    assert body["unit"] == "pipeline-worker"
    assert body["status"] == "alive"
    assert body["implemented"] is True


def test_other_paths_are_not_ok(base_url):
    with pytest.raises(urllib.error.HTTPError) as caught:
        urllib.request.urlopen(f"{base_url}/nope")
    assert caught.value.code == 404
