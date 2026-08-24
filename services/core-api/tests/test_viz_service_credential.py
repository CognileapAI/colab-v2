"""viz-render 중계가 **계약이 요구하는 자격 증명을 실제로 보낸다**.

⚠ **이 시험은 스윕이 세지 않은 자리다 — 실서버 2대로 실측해서 찾았다.**
`core-viz.yaml` 은 `security: [serviceToken]` 로 **모든 렌더 표면에 bearer 를 요구**하는데,
core-api 의 중계는 `X-CoLAB-Lab`·`X-CoLAB-Account` 만 실었다. 그래서 실제 viz-render 를
세우고 부르면 **401 → `RelayUnavailable` → 503** 이다. 즉 `listPalettes` 중계를 열어도
**체인이 core→viz 구간에서 그대로 죽어 있었다.**

시험이 못 잡은 이유는 `D-1` 과 같다 — 시험용 가짜 viz 가 **자격 증명을 검사하지 않았다.**
계약이 요구하는 것을 가짜가 요구하지 않으면, 그 가짜는 계약의 대역이 아니다.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from conftest import TOKEN_RES, auth

from colab_core.app.main import API_PREFIX

SERVICE_TOKEN = "e2e-service-token"
PALETTES = {"items": [{"palette": "seq-blue", "label": "파랑 계열"}],
            "totalCount": 1, "nextCursor": None}


class _AuthenticatingViz(BaseHTTPRequestHandler):
    """**계약대로 bearer 를 요구한다** (`core-viz.yaml` `security: [serviceToken]`)."""

    def _send(self, status: int, payload) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _authorized(self) -> bool:
        scheme, _, token = self.headers.get("Authorization", "").partition(" ")
        return scheme.lower() == "bearer" and token == SERVICE_TOKEN

    def do_GET(self) -> None:                                     # noqa: N802
        if not self._authorized():
            self._send(401, {"code": "UNAUTHORIZED", "message": "서비스 자격 증명이 없다."})
            return
        self._send(200, PALETTES)

    def do_POST(self) -> None:                                    # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if not self._authorized():
            self._send(401, {"code": "UNAUTHORIZED", "message": "서비스 자격 증명이 없다."})
            return
        self._send(202, {"renderId": "01ARZ3NDEKTSV4RRFFQ69G5FAV", "status": "그리는 중"})

    def log_message(self, *args) -> None:
        return


@pytest.fixture()
def strict_viz():
    server = HTTPServer(("127.0.0.1", 0), _AuthenticatingViz)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


def test_팔레트_중계가_서비스_자격_증명을_싣는다(p2_client, strict_viz) -> None:
    client = p2_client(viz_base_url=strict_viz, viz_service_token=SERVICE_TOKEN)
    r = client.get(f"{API_PREFIX}/preview-palettes", headers=auth(TOKEN_RES))
    assert r.status_code == 200, \
        f"계약이 요구하는 bearer 를 안 실으면 여기서 503 이 난다: {r.text}"
    assert r.json() == PALETTES


def test_렌더_생성_중계도_같은_자격_증명을_싣는다(p2_client, strict_viz, sql) -> None:
    """**표면마다 다르면 하나만 살아 있는 상태가 된다.**"""
    client = p2_client(viz_base_url=strict_viz, viz_service_token=SERVICE_TOKEN)
    dataset_id = sql("SELECT id FROM d3_dataset LIMIT 1")[0]["id"]
    r = client.post(f"{API_PREFIX}/previews",
                    json={"target": {"datasetId": dataset_id},
                          "style": {"palette": "seq-blue"}},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 202, r.text


def test_자격_증명이_배선되지_않으면_503_이고_조용히_넘어가지_않는다(p2_client, strict_viz) -> None:
    """**「토큰이 없으니 안 보낸다」로 통과시키지 않는다** — 그것이 지금까지의 상태였고,
    저쪽이 검사를 시작하는 순간 전 표면이 조용히 죽는다.
    """
    client = p2_client(viz_base_url=strict_viz, viz_service_token=None)
    r = client.get(f"{API_PREFIX}/preview-palettes", headers=auth(TOKEN_RES))
    assert r.status_code == 503
    assert r.json()["code"] == "RENDER_UNAVAILABLE"
