"""⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 4⟩ — `listPalettes` 중계.

**이 묶음의 최우선 항이고, 이유는 완료 정의가 통째로 닫혀 있었기 때문이다.**

`core-viz.yaml` 의 `RenderStyle.required` 가 `[palette]` 인데 **FE 가 팔레트 값을 얻을 계약
경로가 없었다.** 그래서 실서버 구현은 항상 예외를 던졌고, `PreviewPanel` 은 `palette` 가 빈
문자열이라 `createRender` 를 **한 번도 부르지 않았다** — 즉 **실서버에서 미리보기 렌더가
단 한 번도 시작되지 않았다**(`sessions/S1-CONTRACT-GAP-SWEEP.md` `D-1`).

⚠ **시험이 왜 못 잡았나** — 프런트 시험은 전부 픽스처 소스를 주입한다. 실서버 구현만 죽어
있었고 시험은 그 파일을 지나지 않았다. `〈87〉-㉯` 의 「서버가 200 을 내는 바람에 그 자리가
도달 불능이었을 뿐이다」와 **정확히 같은 무늬**다.

**중계만 한다** — 값 집합은 viz-render 가 소유하고 core 는 지어내지 않는다.
"""
from __future__ import annotations

import json
import pathlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from conftest import TOKEN_RES, auth

from colab_core.app.main import API_PREFIX

#: viz-render 가 실제로 내는 모양 (`core-viz.yaml#listPalettes` — `ListEnvelope` + `PaletteOption`).
#: **이름은 저쪽 것이다** — 여기서 고르지 않고 받아 적기만 한다.
PALETTES = {"items": [{"palette": "seq-blue", "label": "파랑 계열",
                       "sampleColors": ["#f7fbff", "#08306b"]},
                      {"palette": "seq-warm", "label": "따뜻한 계열"}],
            "totalCount": 2, "nextCursor": None}


class _FakeViz(BaseHTTPRequestHandler):
    seen: list = []

    def do_GET(self) -> None:                                     # noqa: N802
        _FakeViz.seen.append({"path": self.path, "lab": self.headers.get("X-CoLAB-Lab")})
        raw = json.dumps(PALETTES).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args) -> None:
        return


@pytest.fixture()
def fake_viz():
    _FakeViz.seen = []
    server = HTTPServer(("127.0.0.1", 0), _FakeViz)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}", _FakeViz
    server.shutdown()
    server.server_close()


def test_팔레트_목록이_viz_render_의_것_그대로_내려온다(p2_client, fake_viz) -> None:
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    r = client.get(f"{API_PREFIX}/preview-palettes", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"items", "totalCount", "nextCursor"}
    assert body["items"], "빈 목록이면 화면이 렌더를 시작할 수 없다 — 그것이 `D-1` 이었다"
    for item in body["items"]:
        assert item["palette"] and item["label"]
    assert body == PALETTES, "중계가 응답을 가공했다 — 값 집합은 viz-render 것이다"
    assert fake.seen[0]["path"].endswith("/palettes")
    # **경계는 중계에도 실린다** — 저쪽에는 주체가 없다
    assert fake.seen[0]["lab"] == "0000000000000000000000000A"


def test_그리는_서버에_못_닿으면_503_이고_목록을_지어내지_않는다(p2_client) -> None:
    """**폴백을 두지 않는다** — 죽으면 「동작하지 않음」이 드러나야 한다.
    빈 200 을 내면 화면이 「고를 팔레트가 없다」고 말하는데 사실은 「못 물어봤다」이다.
    """
    client = p2_client(viz_base_url=None)
    r = client.get(f"{API_PREFIX}/preview-palettes", headers=auth(TOKEN_RES))
    assert r.status_code == 503
    assert r.json()["code"] == "RENDER_UNAVAILABLE"


def test_인증_없이는_못_본다(p2_client, fake_viz) -> None:
    base, _ = fake_viz
    r = p2_client(viz_base_url=base).get(f"{API_PREFIX}/preview-palettes")
    assert r.status_code == 401


def test_core_api_가_팔레트_이름을_지어내지_않는다() -> None:
    """**값 집합은 viz-render 소유다.** 여기 이름이 박히는 순간 정본이 두 곳에 생긴다
    (`core-viz.yaml` — 「이름을 계약에 박지 않는다」).
    """
    src = pathlib.Path(__file__).resolve().parents[1] / "src" / "colab_core"
    preview = (src / "app" / "routes" / "preview.py").read_text(encoding="utf-8")
    relay = (src / "app" / "relay.py").read_text(encoding="utf-8")
    for invented in ("viridis", "magma", "단색-파랑", "PALETTES", "palette_names"):
        assert invented not in preview, f"라우트가 팔레트 값을 지어냈다: {invented}"
        assert invented not in relay, f"중계가 팔레트 값을 지어냈다: {invented}"
