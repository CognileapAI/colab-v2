"""`createPreviewScreenshot` 중계 — **11차 동결 해제**(`PLAN-SoT §9 〈231〉` · Ted 2026-08-30).

**왜 이 파일이 생겼나.** 정본은 데이터셋 상세에 스크린샷을 **편집 권한자 컨트롤**로 요구하는데
(`Policy_데이터셋_상세 §2`·`§6`·`§8`), 서버쪽 `core-viz.yaml#createScreenshot` 은 서 있는 채
`fe-core.yaml` 에 중계가 **0건**이라 화면이 그 op 에 닿을 계약 경로가 없었다
(`sessions/P3-DETAIL-PREVIEW-20260830.md` 남은 차단 ㈎). `listPalettes` 부재와 같은 모양이다.

**중계는 해석하지 않는다.** 그래서 이 시험도 「그림이 예쁜가」를 묻지 않고 넷만 묻는다:
  ⓐ **집행되는가** — 가짜가 아니라 실제 HTTP 왕복으로 PNG 바이트가 화면까지 온다
  ⓑ **권한을 판정하는가** — `업로드·편집` 이 꺼지면 403 (`core-viz` 가 이 자리를 여기에 넘겼다)
  ⓒ **경계를 확인하는가** — 남의 연구실 렌더가 담긴 장면은 404 (경계 밖은 존재를 알리지 않는다)
  ⓓ **가짜 성공을 만들지 않는가** — 못 닿으면 503 이고 0바이트 PNG 를 지어내지 않는다
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from conftest import TOKEN_RES, auth

from colab_core.app.main import API_PREFIX

ACC_A_RES = "000000000000000000000000A1"
RENDER_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
#: 남의 연구실 렌더 — 가짜 viz 가 이 id 에만 404 를 낸다(경계는 저쪽이 헤더로 판정한다).
FOREIGN_RENDER_ID = "00000000000000000000000000"
#: 최소 PNG 시그니처. **core-api 는 이 바이트를 해석하지 않는다** — 그대로 지나야 한다.
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"colab-scene"

SCENE = {
    "layers": [{"renderId": RENDER_ID, "opacity": 1}],
    "viewport": {"width": 1200, "height": 800,
                 "bounds": {"west": 124.0, "south": 33.0, "east": 132.0, "north": 43.0}},
}


class _FakeViz(BaseHTTPRequestHandler):
    received: list = []

    def _json(self, status: int, payload) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:                                     # noqa: N802
        if self.path.endswith(FOREIGN_RENDER_ID):
            self._json(404, {"code": "NOT_FOUND", "message": "없다"})
            return
        self._json(200, {"renderId": RENDER_ID, "status": "완료"})

    def do_POST(self) -> None:                                    # noqa: N802
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        _FakeViz.received.append({"path": self.path, "body": json.loads(body),
                                  "lab": self.headers.get("X-CoLAB-Lab")})
        if self.path.endswith("/screenshots"):
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(PNG_BYTES)))
            self.end_headers()
            self.wfile.write(PNG_BYTES)
            return
        self._json(202, {"renderId": RENDER_ID, "status": "그리는 중"})

    def log_message(self, *args) -> None:
        return


@pytest.fixture()
def fake_viz():
    _FakeViz.received = []
    server = HTTPServer(("127.0.0.1", 0), _FakeViz)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}", _FakeViz
    server.shutdown()
    server.server_close()


def _shot(client, scene, token=TOKEN_RES):
    return client.post(f"{API_PREFIX}/preview-screenshots", json=scene, headers=auth(token))


# ══════════════════ ⓐ 집행 증명 — 모의가 아니라 실제 왕복이다 ══════════════════
def test_the_screenshot_reaches_the_screen_as_png_bytes(p2_client, fake_viz) -> None:
    """**집행 없는 신설을 만들지 않는다** (`X2-FREEZE-PROTOCOL §5-㉰-4`).

    op 을 열면서 같은 회차에 구현했고, 이 시험이 그 사실을 실제 HTTP 왕복으로 잰다 —
    PNG 바이트가 저쪽에서 나와 화면까지 **손대지 않은 채** 온다.
    """
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    r = _shot(client, SCENE)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("image/png"), r.headers["content-type"]
    assert r.content == PNG_BYTES, "중계가 그림 바이트를 가공했다."

    posted = [row for row in fake.received if row["path"].endswith("/screenshots")]
    assert len(posted) == 1, "실제 왕복이 일어나지 않았다 — 집행 없는 신설이다."
    assert posted[0]["body"] == SCENE, "중계가 장면을 가공했다 — 스키마는 재선언하지 않는다."
    # **경계는 중계에도 실린다** — 저쪽에는 주체가 없다.
    assert posted[0]["lab"] == "0000000000000000000000000A"


# ═════════════════════════ ⓑ 편집 권한을 판정한다 ═════════════════════════════
def test_the_screenshot_needs_the_upload_edit_switch(p2_client, fake_viz, sql) -> None:
    """정본이 스크린샷을 **편집 권한자 컨트롤**로 둔다(`Policy_데이터셋_상세 §6`).

    `core-viz.yaml` 이 「권한 판정은 core-api 가 한다」로 그 자리를 여기에 넘겼으므로,
    이 판정이 없으면 **아무도 안 하는 판정**이 된다. 화면에서 숨긴 것을 서버가 같은
    기준으로 막는다(`§3.3` 축자).
    """
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    sql("UPDATE d2_permission_switch SET enabled = false"
        " WHERE account_id = :a AND switch = '업로드·편집'", {"a": ACC_A_RES})
    r = _shot(client, SCENE)
    assert r.status_code == 403, "스위치 없는 사람이 장면을 뽑았다."
    assert [row for row in fake.received if row["path"].endswith("/screenshots")] == [], \
        "권한 판정 전에 중계가 나갔다."


# ══════════════════════════════ ⓒ 경계 ═══════════════════════════════════════
def test_a_scene_holding_a_foreign_render_is_404(p2_client, fake_viz) -> None:
    """**경계 밖은 존재를 알리지 않는다** — 403 이 아니라 404 다 (`fe-core.yaml` NotFound)."""
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    scene = {**SCENE, "layers": [{"renderId": FOREIGN_RENDER_ID, "opacity": 1}]}
    r = _shot(client, scene)
    assert r.status_code == 404, r.text
    assert [row for row in fake.received if row["path"].endswith("/screenshots")] == [], \
        "경계 확인 전에 중계가 나갔다 — 남의 연구실 그림을 뽑아 준다."


def test_a_scene_without_layers_or_viewport_is_400(p2_client, fake_viz) -> None:
    base, _ = fake_viz
    client = p2_client(viz_base_url=base)
    for bad in ({"viewport": SCENE["viewport"]},
                {"layers": []},
                {"layers": SCENE["layers"]},
                {"layers": [{"renderId": "not-a-ulid"}], "viewport": SCENE["viewport"]}):
        assert _shot(client, bad).status_code == 400, bad


# ═══════════════════ ⓓ 못 닿으면 가짜 성공을 만들지 않는다 ═══════════════════
def test_when_the_render_server_is_unreachable_it_is_503_not_an_empty_png(p2_client) -> None:
    """**0바이트 PNG 는 「장면이 비었다」로 읽힌다** — 지어내지 않는다.

    `createPreviewRender` 의 503 과 같은 모양이고 코드도 같다.
    """
    client = p2_client(viz_base_url=None)
    r = _shot(client, SCENE)
    assert r.status_code == 503
    assert r.json()["code"] == "RENDER_UNAVAILABLE"
