"""값 조회 중계 (`lookupDatasetValue` · `V-2` · `PLAN-SoT §9 〈294〉` · 15차 해제).

**core-api 는 값을 읽지 않는다** — 이 시험이 묻는 것은 넷이다:
  ⓐ **경계 밖은 404** (존재를 알리지 않는다 · P-9·P-10)
  ⓑ **잠긴 데이터의 본체는 403** (P-34 · 완료 정의 권한 ⓐ — 값은 내용이다)
  ⓒ **신원이 없으면 401**
  ⓓ **요청·응답을 그대로 지난다** — 조각 식별자는 **원장이** 붙인다(화면이 아니다)

red 만드는 법 — `routes/preview.py` `lookup_dataset_value` 의 `require_body_access`
호출을 지운다(그러면 잠긴 행이 열린다) · 조각을 `d3_file` 이 아니라 요청에서 받게 바꾼다
(그러면 화면이 원장을 대신 기억한다).
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from conftest import DS_A1, DS_A2, DS_B1, TOKEN_PROF, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX

#: viz-render 가 돌려줄 `ValueLookupResult`. **core-api 는 이 모양을 재선언하지 않는다.**
RESULT = {
    "available": True, "value": 12.5, "unit": "mm", "variable": "강우량",
    "exactness": "원본과 같은 칸",
    "cell": {"row": 2, "col": 3, "center": {"lat": 37.375, "lon": 126.875},
             "sizeDegrees": 0.25},
    "unavailableReason": None,
}
NO_TILE = {"available": False, "value": None, "unit": None, "variable": None,
           "exactness": "원본과 같은 칸", "cell": None,
           "unavailableReason": "자리에 산출물이 없다"}

POINT = {"lat": 37.4, "lon": 126.9}


class _FakeViz(BaseHTTPRequestHandler):
    received: list = []
    reply = RESULT
    extra_headers: list = []

    def do_POST(self) -> None:                                    # noqa: N802
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        _FakeViz.received.append({"path": self.path, "body": json.loads(body),
                                  "lab": self.headers.get("X-CoLAB-Lab")})
        raw = json.dumps(_FakeViz.reply).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        for k, v in _FakeViz.extra_headers:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args) -> None:
        return


@pytest.fixture()
def fake_viz():
    _FakeViz.received = []
    _FakeViz.reply = RESULT
    _FakeViz.extra_headers = []
    server = HTTPServer(("127.0.0.1", 0), _FakeViz)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}", _FakeViz
    server.shutdown()
    server.server_close()


# ══════════════════════ ⓓ 그대로 지난다 · 조각은 원장이 준다 ═══════════════════
def test_값을_그대로_지나_보내고_조각은_원장이_붙인다(p2_client, fake_viz) -> None:
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)

    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/value-lookup",
                    json={"point": POINT}, headers=auth(TOKEN_PROF))
    assert r.status_code == 200, r.text
    assert r.json() == RESULT, "중계가 응답을 가공했다 — ValueLookupResult 는 그대로 지나간다."

    sent = fake.received[0]["body"]
    assert sent["datasetId"] == DS_A1
    assert sent["point"] == POINT
    # **조각 식별자를 화면이 보내지 않았는데도 실려 나갔다** — 원장이 붙였다는 뜻이다.
    assert sent["fileId"] and len(sent["fileId"]) == 26
    # 경계는 중계에도 실린다 — 저쪽에는 주체가 없다.
    assert fake.received[0]["lab"] == "0000000000000000000000000A"


def test_없음도_200_으로_지난다(p2_client, fake_viz) -> None:
    """**「없다」를 4xx 로 승격하지 않는다** — 저쪽이 읽어 보고 낸 사실이다."""
    base, fake = fake_viz
    fake.reply = NO_TILE
    client = p2_client(viz_base_url=base)
    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/value-lookup",
                    json={"point": POINT}, headers=auth(TOKEN_PROF))
    assert r.status_code == 200, r.text
    assert r.json() == NO_TILE
    assert r.json()["value"] is None


# ══════════════════════════════ ⓐⓑⓒ 권한 ═══════════════════════════════════
def test_다른_연구실_데이터셋은_404_다(p2_client, fake_viz) -> None:
    """**존재를 알리지 않는다** — 403 이면 「있긴 하다」를 말해 버린다(P-9·P-10)."""
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    r = client.post(f"{API_PREFIX}/datasets/{DS_B1}/value-lookup",
                    json={"point": POINT}, headers=auth(TOKEN_RES))
    assert r.status_code == 404, r.text
    assert fake.received == [], "경계 밖인데 저쪽에 물어봤다."


def test_잠긴_데이터셋은_403_이고_저쪽에_묻지도_않는다(p2_client, fake_viz) -> None:
    """완료 정의 권한 ⓐ — **값은 내용이다.** 확대(보기 권한만)와 다른 자리다."""
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    r = client.post(f"{API_PREFIX}/datasets/{DS_A2}/value-lookup",
                    json={"point": POINT}, headers=auth(TOKEN_RES))
    assert r.status_code == 403, r.text
    assert fake.received == [], "잠긴 데이터인데 저쪽에 물어봤다."


def test_신원이_없으면_401_이다(p2_client, fake_viz) -> None:
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/value-lookup", json={"point": POINT})
    assert r.status_code == 401, r.text
    assert fake.received == []


def test_그리는_서버에_못_닿으면_503_이고_값을_지어내지_않는다(p2_client) -> None:
    client = p2_client(viz_base_url="http://127.0.0.1:1")
    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/value-lookup",
                    json={"point": POINT}, headers=auth(TOKEN_PROF))
    assert r.status_code == 503, r.text
    assert r.json()["code"] == "RENDER_UNAVAILABLE"


def test_점이_없으면_400_이다(p2_client, fake_viz) -> None:
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/value-lookup",
                    json={}, headers=auth(TOKEN_PROF))
    assert r.status_code == 400, r.text
    assert fake.received == []


# ══════════════ 서버 단독 시간 — `Server-Timing` (`VL-1` · `PLAN-SoT §9 〈310〉`) ══════════════
#
# 왜 여기가 그 자리인가 — `〈304〉` 는 공개 엣지 앞 벽시계 하나로만 재서 **서버 단독 p95 가
# `[미확인]`** 이었다. 사용자가 실제로 부르는 표면은 이 op 이므로, **이 표면이 자기 구간을
# 말해야** 엣지·nginx 를 뺀 값이 나온다. ⚠ 몸통(`ValueLookupResult`)은 늘지 않는다.

def _spans(res) -> dict:
    import re
    header = res.headers.get("Server-Timing")
    assert header, "값 조회 응답에 Server-Timing 이 없다 — 서버 단독 시간을 가를 재료가 없다."
    return {m.group(1): float(m.group(2))
            for m in re.finditer(r"([A-Za-z0-9_]+);dur=([0-9.]+)", header)}


def test_중계_응답이_자기_구간을_말한다(p2_client, fake_viz) -> None:
    base, _fake = fake_viz
    client = p2_client(viz_base_url=base)
    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/value-lookup",
                    json={"point": POINT}, headers=auth(TOKEN_PROF))
    assert r.status_code == 200, r.text
    spans = _spans(r)
    # `coreAccess` = 경계·권한 판정 ＋ 조각 조회(DB) · `coreRelay` = viz-render 왕복
    for name in ("coreAccess", "coreRelay", "coreTotal"):
        assert name in spans, f"{name} 구간이 없다: {spans}"
    assert spans["coreTotal"] + 1e-6 >= spans["coreAccess"] + spans["coreRelay"]


def test_저쪽_구간을_지워버리지_않는다(p2_client, fake_viz) -> None:
    """**viz-render 가 낸 구간이 화면까지 살아 온다** — 지우면 「어디가 느린가」가
    core-api 이하로만 갈리고 D7 안이 다시 `[미확인]` 이 된다."""
    base, fake = fake_viz
    fake.extra_headers = [("Server-Timing", "vizTotal;dur=7.500")]
    try:
        client = p2_client(viz_base_url=base)
        r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/value-lookup",
                        json={"point": POINT}, headers=auth(TOKEN_PROF))
        assert _spans(r)["vizTotal"] == 7.5
    finally:
        fake.extra_headers = []
