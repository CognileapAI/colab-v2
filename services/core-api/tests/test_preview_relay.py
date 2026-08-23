"""미리보기 중계 2 op (`〈63〉-㉮`) — `createPreviewRender` · `getPreviewRender`.

**중계는 해석하지 않는다.** 그래서 이 시험은 「무엇을 그렸나」를 묻지 않고 셋만 묻는다:
  ⓐ 경계를 확인하는가 (남의 연구실 대상은 404)
  ⓑ 요청·응답을 **그대로** 지나 보내는가 (재선언·가공 없음)
  ⓒ **geo 라이브러리가 core-api 에 들어오지 않는가** (`CLAUDE.md §3-4` · `banned-import`)

viz-render 는 P2-viz 레인이 만드는 중이라, 여기서는 **가짜 viz 서버**를 세워 중계 자체를 잰다.
"""
from __future__ import annotations

import json
import pathlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from conftest import DS_A1, DS_B1, TOKEN_RES, auth
from test_dataset_registration import make_upload

from colab_core.app.main import API_PREFIX

RENDER_ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
#: viz-render 가 돌려줄 `RenderJob`. **core-api 는 이 모양을 재선언하지 않는다** —
#: `core-viz.yaml#RenderJob` 이 정본이다.
JOB_RUNNING = {"renderId": RENDER_ID, "status": "그리는 중", "stage": "파일 읽는 중"}
JOB_DONE = {
    "renderId": RENDER_ID, "status": "완료",
    "result": {"tileUrlTemplate": "https://tiles.example/{z}/{x}/{y}.png",
               "bounds": {"west": 124.0, "south": 33.0, "east": 132.0, "north": 43.0},
               "legend": {"unit": "mm", "breaks": [0, 1, 2, 3, 4, 5]}},
    # **부분 실패는 `status` 를 `실패` 로 만들지 않는다** — 읽힌 조각으로 그리고 `완료` 로 남는다.
    "partialFailure": {"failedFileIds": ["01ARZ3NDEKTSV4RRFFQ69G5FAW"], "reason": "조각 하나를 못 읽음"},
}


class _FakeViz(BaseHTTPRequestHandler):
    received: list = []

    def _send(self, status: int, payload) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:                                    # noqa: N802
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        _FakeViz.received.append({"path": self.path, "body": json.loads(body),
                                  "lab": self.headers.get("X-CoLAB-Lab")})
        self._send(202, JOB_RUNNING)

    def do_GET(self) -> None:                                     # noqa: N802
        if self.path.endswith("/00000000000000000000000000"):
            self._send(404, {"code": "NOT_FOUND", "message": "없다"})
            return
        self._send(200, JOB_DONE)

    def log_message(self, *args) -> None:                         # 시험 출력을 더럽히지 않는다
        return


@pytest.fixture()
def fake_viz():
    _FakeViz.received = []
    server = HTTPServer(("127.0.0.1", 0), _FakeViz)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}", _FakeViz
    server.shutdown()
    server.server_close()


# ══════════════════════════ ⓑ 그대로 지나 보낸다 ════════════════════════════
def test_create_preview_render_relays_the_request_untouched(p2_client, fake_viz) -> None:
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    request = {"target": {"datasetId": DS_A1}, "variable": "강우량",
               "style": {"palette": "blues", "classCount": 6},
               "withoutReferenceGrid": True}

    r = client.post(f"{API_PREFIX}/previews", json=request, headers=auth(TOKEN_RES))
    assert r.status_code == 202, r.text
    assert r.json() == JOB_RUNNING, "중계가 응답을 가공했다 — RenderJob 은 그대로 지나가야 한다."
    assert fake.received[0]["body"] == request, "중계가 요청을 가공했다."
    # **경계는 중계에도 실린다** — 저쪽에는 주체가 없다.
    assert fake.received[0]["lab"] == "0000000000000000000000000A"


def test_get_preview_render_relays_the_job_including_partial_failure(p2_client, fake_viz) -> None:
    """**부분 실패와 전부 실패를 같은 자리에 담지 않는다** — 계약이 갈라 뒀고 중계는 안 합친다."""
    base, _ = fake_viz
    client = p2_client(viz_base_url=base)
    r = client.get(f"{API_PREFIX}/previews/{RENDER_ID}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert r.json() == JOB_DONE
    assert r.json()["status"] == "완료"
    assert "partialFailure" in r.json()


def test_core_api_does_not_proxy_tiles(p2_client, fake_viz) -> None:
    """**타일 URL 은 중계하지 않는다** — FE 가 `tileUrlTemplate` 을 직접 소비한다.

    core-api 에 타일 경로가 생기면 모든 타일이 이 프로세스를 지나게 되고,
    그것이 v1 에서 core 안에 래스터 라이브러리가 들어온 경위였다.
    """
    base, _ = fake_viz
    client = p2_client(viz_base_url=base)
    paths = {route.path for route in client.app.routes}
    assert not any("tiles" in p for p in paths), f"core-api 에 타일 경로가 있다: {paths}"


# ══════════════════════════════ ⓐ 경계 ══════════════════════════════════════
def test_a_target_from_another_lab_is_404(p2_client, fake_viz) -> None:
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    r = client.post(f"{API_PREFIX}/previews",
                    json={"target": {"datasetId": DS_B1}, "style": {"palette": "blues"}},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 404
    assert fake.received == [], "경계 확인 전에 중계가 나갔다 — 남의 연구실 파일을 그려 준다."


def test_an_unregistered_upload_is_a_valid_target(p2_client, fake_viz) -> None:
    """S-08 — **등록하지 않은 업로드도 대상이 된다.** 그 화면이 P2 의 절반이다."""
    base, _ = fake_viz
    client = p2_client(viz_base_url=base)
    receipt = make_upload(client)
    r = client.post(f"{API_PREFIX}/previews",
                    json={"target": {"uploadId": receipt["uploadId"]},
                          "style": {"palette": "blues"}},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 202, r.text


def test_the_target_must_be_exactly_one_of_the_two(p2_client, fake_viz) -> None:
    base, _ = fake_viz
    client = p2_client(viz_base_url=base)
    for target in ({}, {"datasetId": DS_A1, "uploadId": DS_A1}):
        r = client.post(f"{API_PREFIX}/previews",
                        json={"target": target, "style": {"palette": "blues"}},
                        headers=auth(TOKEN_RES))
        assert r.status_code == 400


def test_palette_is_required_and_core_does_not_invent_its_values(p2_client, fake_viz) -> None:
    """`style.palette` 는 required 이고 **값 집합은 viz-render 소유**다 — 여기서 만들지 않는다."""
    base, _ = fake_viz
    client = p2_client(viz_base_url=base)
    r = client.post(f"{API_PREFIX}/previews", json={"target": {"datasetId": DS_A1}, "style": {}},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 400

    import pathlib as _p
    src = _p.Path(__file__).resolve().parents[1] / "src" / "colab_core"
    preview = (src / "app" / "routes" / "preview.py").read_text(encoding="utf-8")
    for invented in ("viridis", "magma", "PALETTES", "palette_names"):
        assert invented not in preview, f"core-api 가 팔레트 값을 지어냈다: {invented}"


def test_a_missing_render_is_404(p2_client, fake_viz) -> None:
    base, _ = fake_viz
    client = p2_client(viz_base_url=base)
    r = client.get(f"{API_PREFIX}/previews/00000000000000000000000000", headers=auth(TOKEN_RES))
    assert r.status_code == 404


def test_when_the_render_server_is_unreachable_registration_still_works(p2_client) -> None:
    """**그릴 수 없는 것과 등록할 수 없는 것은 다르다.**

    그리는 서버가 없어도 등록은 그대로 된다 — 가짜 성공을 만들지도 않는다.
    """
    client = p2_client(viz_base_url=None)
    r = client.post(f"{API_PREFIX}/previews",
                    json={"target": {"datasetId": DS_A1}, "style": {"palette": "blues"}},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 503
    assert r.json()["code"] == "RENDER_UNAVAILABLE"

    receipt = make_upload(client)
    registered = client.post(f"{API_PREFIX}/datasets",
                             json={"uploadId": receipt["uploadId"], "name": "미리보기 없이 등록"},
                             headers=auth(TOKEN_RES))
    assert registered.status_code == 201, "미리보기가 안 된다고 등록이 막혔다 — 정본 :192 위반이다."


# ═════════════════════ ⓒ core-api 에 geo 가 없다 ════════════════════════════
def test_no_geo_library_is_imported_anywhere_in_core_api() -> None:
    """`banned-import` 게이트와 같은 규칙을 **레인 안에서도** 건다.

    게이트는 레포 전체를 나중에 보고, 이 시험은 이 서비스를 지금 본다 — 미리보기를
    「중계」가 아니라 「구현」으로 바꾸려는 순간 여기가 먼저 red 를 낸다.
    """
    import tomllib
    repo = pathlib.Path(__file__).resolve().parents[3]
    config = tomllib.loads((repo / "gates" / "config" / "boundaries.toml")
                           .read_text(encoding="utf-8"))
    banned = set(config["units"]["core-api"]["banned"])
    assert banned, "금지 목록이 비었다 — 목록 없이 통과시키지 않는다."

    src = pathlib.Path(__file__).resolve().parents[1] / "src" / "colab_core"
    hits = []
    for path in sorted(src.rglob("*.py")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                continue
            for module in banned:
                if stripped.startswith((f"import {module}", f"from {module}")):
                    hits.append(f"{path.name}:{line_no}: {stripped}")
    assert hits == [], f"core-api 에 geo 라이브러리가 들어왔다:\n" + "\n".join(hits)
