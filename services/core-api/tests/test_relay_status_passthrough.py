"""viz 의 **4xx 를 503 으로 뭉개지 않는다** (`CODE-REVIEW-20260903` #8).

`HttpPreviewRelay` 는 `status not in (200, 201, 202)` 를 전부 `RelayUnavailable` 로 접어
viz-render 의 **415 NOT_RENDERABLE**(`details.renderableFormats`)·413·400 이 core-api 에서
503 「연결하지 못했다」가 됐다. 결과 —
  · 사용자는 **그릴 수 없는 파일**을 「서버 장애」로 읽고 계속 재시도한다.
  · 지원 형식 목록이 화면에 영영 도달하지 않는다.
  · FE 의 `status === 415` 분기 4곳이 **죽은 코드**다.

여기서 재는 것 넷 —
  ⓐ 통과 상태 집합(400·404·410·413·415·422)은 **상태·본문 그대로** 올라간다
  ⓑ 연결 실패·5xx 는 **여전히 503** 이다 (「못 닿았다」는 사실이다)
  ⓒ **401·403 은 통과시키지 않는다** — 그것은 우리 서비스 토큰이 틀렸다는 뜻이고
    사용자가 고칠 수 있는 것이 아니다
  ⓓ 경계 헤더(`X-CoLAB-Lab`·`X-CoLAB-Account`)가 **다섯 호출 전부**에 실린다
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from conftest import DS_A1, TOKEN_PROF, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX

#: viz-render 의 415 본문. **core-api 는 이 모양을 만들지도 해석하지도 않는다** —
#: 지원 형식 목록은 렌더러의 사실이고, 그것이 화면까지 닿아야 사용자가 다음 수를 안다.
NOT_RENDERABLE = {
    "code": "NOT_RENDERABLE",
    "message": "이 형식은 아직 그리지 못해요.",
    "details": {"renderableFormats": ["GeoTIFF", "NetCDF", "HDF4", "NumPy"]},
}
POINT = {"lat": 37.4, "lon": 126.9}
LAB_A = "0000000000000000000000000A"


class _FakeViz(BaseHTTPRequestHandler):
    """상태코드를 마음대로 내는 가짜 viz. 헤더도 함께 기록한다."""

    received: list = []
    status = 415
    body: dict | None = NOT_RENDERABLE

    def _record(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        _FakeViz.received.append({
            "path": self.path,
            "lab": self.headers.get("X-CoLAB-Lab"),
            "account": self.headers.get("X-CoLAB-Account"),
            "authorization": self.headers.get("Authorization"),
            "body": json.loads(raw) if raw else None,
        })

    def _reply(self) -> None:
        raw = b"" if _FakeViz.body is None else json.dumps(_FakeViz.body).encode()
        self.send_response(_FakeViz.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:                                    # noqa: N802
        self._record()
        self._reply()

    def do_GET(self) -> None:                                     # noqa: N802
        self._record()
        self._reply()

    def log_message(self, *args) -> None:
        return


@pytest.fixture()
def fake_viz():
    _FakeViz.received = []
    _FakeViz.status = 415
    _FakeViz.body = NOT_RENDERABLE
    server = HTTPServer(("127.0.0.1", 0), _FakeViz)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}", _FakeViz
    server.shutdown()
    server.server_close()


def _create(client):
    return client.post(f"{API_PREFIX}/previews",
                       json={"target": {"datasetId": DS_A1}, "style": {"palette": "blues"}},
                       headers=auth(TOKEN_RES))


def _palettes(client):
    return client.get(f"{API_PREFIX}/preview-palettes", headers=auth(TOKEN_RES))


def _lookup(client):
    return client.post(f"{API_PREFIX}/datasets/{DS_A1}/value-lookup",
                       json={"point": POINT}, headers=auth(TOKEN_PROF))


# ═════════════════ ⓐ 저쪽이 낸 거절은 상태·본문 그대로 올라간다 ═══════════════
def test_a_415_from_viz_reaches_the_screen_with_its_renderable_formats(
        p2_client, fake_viz) -> None:
    """**그릴 수 없는 파일은 장애가 아니다.** 지원 형식 목록이 사용자에게 닿아야 한다."""
    base, _ = fake_viz
    r = _create(p2_client(viz_base_url=base))
    assert r.status_code == 415, r.text
    assert r.json() == NOT_RENDERABLE
    assert r.json()["details"]["renderableFormats"], \
        "형식 목록이 사라졌다 — 사용자는 다음 수를 알 수 없다."


@pytest.mark.parametrize("status", [400, 404, 410, 413, 415, 422])
def test_every_pass_through_status_keeps_its_own_status(p2_client, fake_viz, status) -> None:
    base, fake = fake_viz
    fake.status = status
    r = _create(p2_client(viz_base_url=base))
    assert r.status_code == status, f"{status} 가 {r.status_code} 로 바뀌었다: {r.text}"


def test_palettes_and_value_lookup_pass_the_status_too(p2_client, fake_viz) -> None:
    """세 자리가 같은 규칙을 쓴다 — 한 자리만 고치면 나머지가 조용히 다르게 답한다."""
    base, fake = fake_viz
    fake.status = 422
    fake.body = {"code": "INVALID_POINT", "message": "위경도가 범위 밖이다."}
    client = p2_client(viz_base_url=base)
    assert _palettes(client).status_code == 422
    assert _lookup(client).status_code == 422
    assert _lookup(client).json()["code"] == "INVALID_POINT"


def test_a_refusal_without_a_body_still_keeps_the_status(p2_client, fake_viz) -> None:
    """본문이 없어도 **상태는 사실이다** — 503 「못 닿았다」로 바꾸면 거짓말이 된다."""
    base, fake = fake_viz
    fake.status = 413
    fake.body = None
    r = _create(p2_client(viz_base_url=base))
    assert r.status_code == 413, r.text
    assert r.json()["code"], "봉투가 없다 — 화면이 분기할 코드가 필요하다."


# ═══════════════════ ⓑ·ⓒ 못 닿음·5xx·자격 실패는 503 이다 ════════════════════
@pytest.mark.parametrize("status", [500, 502, 503, 401, 403])
def test_server_faults_and_credential_failures_are_still_503(
        p2_client, fake_viz, status) -> None:
    """**우리 쪽 고장을 사용자 오류로 위장하지 않는다.**

    5xx 는 저쪽 사정이고, 401·403 은 **우리 서비스 토큰이 틀렸다**는 뜻이다 — 둘 다
    사용자가 고칠 수 있는 것이 아니다. 통과시키면 화면이 「네 요청이 틀렸다」를 말한다.
    """
    base, fake = fake_viz
    fake.status = status
    fake.body = {"code": "SOMETHING", "message": "저쪽 사정"}
    r = _create(p2_client(viz_base_url=base))
    assert r.status_code == 503, f"{status} 가 통과했다: {r.text}"
    assert r.json()["code"] == "RENDER_UNAVAILABLE"


def test_an_unreachable_render_server_is_still_503(p2_client) -> None:
    client = p2_client(viz_base_url="http://127.0.0.1:1")
    r = _create(client)
    assert r.status_code == 503
    assert r.json()["code"] == "RENDER_UNAVAILABLE"


# ══════════════════════════ 위경도 범위·bool ═════════════════════════════════
@pytest.mark.parametrize("point", [
    {"lat": True, "lon": 126.9},        # `bool` 은 `int` 의 하위형이라 종전 검사를 통과했다
    {"lat": 37.4, "lon": False},
    {"lat": 200, "lon": 126.9},
    {"lat": -91, "lon": 126.9},
    {"lat": 37.4, "lon": 181},
    {"lat": 37.4, "lon": -180.5},
])
def test_a_point_outside_the_globe_is_400_here_not_503_over_there(
        p2_client, fake_viz, point) -> None:
    """**클라이언트 오류가 장애 계수에 섞이지 않는다.**

    종전에는 타입만 봐서(`bool` 도 통과) `{"lat": 200}` 이 viz 의 pydantic(ge=-90) 에서
    422 가 되고, 그 422 가 같은 경로로 **503** 이 됐다.
    """
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/value-lookup",
                    json={"point": point}, headers=auth(TOKEN_PROF))
    assert r.status_code == 400, f"{point} → {r.status_code}: {r.text}"
    assert fake.received == [], "범위 밖 좌표가 그리는 서버까지 나갔다."


def test_a_point_on_the_boundary_is_still_accepted(p2_client, fake_viz) -> None:
    """**넓히지도 좁히지도 않았음**을 함께 잰다 — 경계값은 유효하다."""
    base, fake = fake_viz
    fake.status = 200
    fake.body = {"available": False, "value": None, "unit": None, "variable": None,
                 "exactness": "원본과 같은 칸", "cell": None,
                 "unavailableReason": "범위 밖이다"}
    client = p2_client(viz_base_url=base)
    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/value-lookup",
                    json={"point": {"lat": -90, "lon": 180}}, headers=auth(TOKEN_PROF))
    assert r.status_code == 200, r.text


# ══════════════════ ⓓ 경계 헤더가 다섯 호출 전부에 실린다 ════════════════════
def test_the_scope_headers_ride_on_every_one_of_the_five_relay_calls(
        p2_client, fake_viz) -> None:
    """**경계는 중계에도 실린다** — 저쪽에는 주체가 없다.

    이미 다섯 호출 전부에 실려 있다. 이 시험은 그것을 **못으로 박는다**: viz-render 는
    지금 이 헤더로 job 의 연구실을 대조하는 중이고(레인 C), 한 호출에서라도 헤더가
    빠지면 그 대조는 **헤더 없음 = 400** 이 되어 그 표면만 조용히 죽는다.
    호출 다섯 = `create` · `get` · `screenshot` · `palettes` · `lookup_value`.
    """
    base, fake = fake_viz
    fake.status = 200
    fake.body = {"renderId": "01ARZ3NDEKTSV4RRFFQ69G5FAV", "status": "그리는 중",
                 "palettes": [], "available": False, "value": None, "unit": None,
                 "variable": None, "exactness": "원본과 같은 칸", "cell": None,
                 "unavailableReason": "자리에 산출물이 없다"}
    client = p2_client(viz_base_url=base)

    _create(client)
    _palettes(client)
    _lookup(client)
    client.get(f"{API_PREFIX}/previews/01ARZ3NDEKTSV4RRFFQ69G5FAV", headers=auth(TOKEN_RES))
    client.post(f"{API_PREFIX}/preview-screenshots",
                json={"layers": [{"renderId": "01ARZ3NDEKTSV4RRFFQ69G5FAV"}],
                      "viewport": {"width": 800, "height": 600}},
                headers=auth(TOKEN_RES))

    paths = {call["path"] for call in fake.received}
    assert {"/renders", "/palettes", "/value-lookups", "/screenshots"} <= paths, \
        f"다섯 호출이 다 나가지 않았다: {sorted(paths)}"
    assert any(p.startswith("/renders/") for p in paths), "렌더 조회가 나가지 않았다."
    for call in fake.received:
        assert call["lab"] == LAB_A, f"{call['path']} 에 X-CoLAB-Lab 이 없다: {call['lab']}"
        assert call["account"], f"{call['path']} 에 X-CoLAB-Account 가 없다."
        assert call["authorization"], f"{call['path']} 에 서비스 자격 증명이 없다."
