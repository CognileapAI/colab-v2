"""WU-A2 · 미리보기 **생성** 권한 검사 (PRD-26 · `R-A-2-server.md` §2 WU-A2).

**구멍의 모양** — `createPreviewRender` 는 `_target_in_lab` 으로 연구실 경계만 봤다.
`업로드·편집` 검사도, 대상 데이터셋 **본체 접근** 검사도 없었다. 같은 파일의 값 조회
(`lookupDatasetValue`)는 내려받기와 **같은 판정 함수**(`catalog.require_body_access`)를
쓰는데 생성 경로만 비어 있었다 — 잠긴 남의 데이터셋을 대상으로 한 렌더 요청이 안 막혔다.

⛔ **새 판정 로직을 만들지 않는다** — 아래 ⓔ 가 그 재사용을 코드로도 확인한다.
"""
from __future__ import annotations

import json
import pathlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from conftest import ACC_A_RES, DS_A1, DS_A2, DS_B1, TOKEN_RES, auth
from test_dataset_registration import make_upload

from colab_core.app.main import API_PREFIX

JOB_RUNNING = {"renderId": "01ARZ3NDEKTSV4RRFFQ69G5FAV", "status": "그리는 중"}


class _FakeViz(BaseHTTPRequestHandler):
    received: list = []

    def do_POST(self) -> None:                                    # noqa: N802
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        _FakeViz.received.append({"path": self.path, "body": json.loads(body)})
        raw = json.dumps(JOB_RUNNING).encode()
        self.send_response(202)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args) -> None:                         # 시험 출력을 더럽히지 않는다
        return


@pytest.fixture()
def fake_viz():
    _FakeViz.received = []
    server = HTTPServer(("127.0.0.1", 0), _FakeViz)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}", _FakeViz
    server.shutdown()
    server.server_close()


def _render(client, target: dict):
    return client.post(f"{API_PREFIX}/previews",
                       json={"target": target, "style": {"palette": "blues"}},
                       headers=auth(TOKEN_RES))


# ═══════════════════ ⓐ `업로드·편집` 이 없으면 403 ═══════════════════════════
def test_creating_a_render_needs_the_upload_edit_switch(p2_client, fake_viz, sql) -> None:
    """화면에서 숨긴 것을 서버도 같은 기준으로 막는다 — 스크린샷 중계와 같은 판정이다."""
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    sql("UPDATE d2_permission_switch SET enabled = false"
        " WHERE account_id = :a AND switch = '업로드·편집'", {"a": ACC_A_RES})
    r = _render(client, {"datasetId": DS_A1})
    assert r.status_code == 403, f"스위치 없는 사람이 렌더를 시작했다: {r.status_code} {r.text}"
    assert fake.received == [], "권한 판정 전에 중계가 나갔다."


# ═════════════ ⓑ 잠긴 남의 데이터셋을 대상으로 하면 거절 ═════════════════════
def test_a_locked_dataset_target_is_refused(p2_client, fake_viz) -> None:
    """`DSA2` 는 잠김이고 `TOKEN_RES` 는 허용 목록 밖이다 — 내려받기·값 조회와 같은 답이다."""
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    r = _render(client, {"datasetId": DS_A2})
    assert r.status_code == 403, f"잠긴 데이터셋을 그려 줬다: {r.status_code} {r.text}"
    assert fake.received == [], "접근 판정 전에 중계가 나갔다 — 잠긴 파일을 그려 준다."


# ═══════════════════ ⓒ 자기 업로드는 그대로 성공 (회귀 방지) ═════════════════
def test_my_own_unregistered_upload_still_renders(p2_client, fake_viz) -> None:
    """S-08 — 등록 전 업로드는 **소유자 판정만** 본다. 그 화면이 P2 의 절반이다."""
    base, _ = fake_viz
    client = p2_client(viz_base_url=base)
    receipt = make_upload(client)
    r = _render(client, {"uploadId": receipt["uploadId"]})
    assert r.status_code == 202, r.text


# ═══════════════════ ⓓ 다른 연구실 id 는 404 (현행 유지) ══════════════════════
def test_a_dataset_from_another_lab_is_still_404(p2_client, fake_viz) -> None:
    """**경계 밖은 존재를 알리지 않는다** — 403 이 아니라 404 다."""
    base, fake = fake_viz
    client = p2_client(viz_base_url=base)
    r = _render(client, {"datasetId": DS_B1})
    assert r.status_code == 404, r.text
    assert fake.received == [], "경계 확인 전에 중계가 나갔다."


# ══════════ ⓔ 판정 함수 재사용 — 새 로직을 만들지 않았음을 코드로 잰다 ════════
def test_the_render_guard_reuses_the_value_lookup_judgment() -> None:
    """완료 판정에 붙는 diff 증명을 시험으로도 못 박는다 (§2 WU-A2 · §3-㉴).

    값 조회가 부르는 것과 **같은 이름**을 생성 경로도 부른다. 판정을 복사하면
    한쪽만 고쳐지는 날이 온다(`catalog.require_body_access` 머리 주석 축자).
    """
    src = pathlib.Path(__file__).resolve().parents[1] / "src" / "colab_core"
    preview = (src / "app" / "routes" / "preview.py").read_text(encoding="utf-8")
    assert preview.count("catalog.require_body_access") >= 2, \
        "생성 경로가 값 조회와 같은 판정 함수를 쓰지 않는다 — 새 판정을 만들었다."
    # ⚠ `body_accessible` 은 이 파일의 **주석**에 이미 있다(값 조회 머리 설명) — 이름이 아니라
    #    **판정을 다시 짓는 호출**을 금지한다.
    for invented in ("DatasetAccessAdapter", "dataset_access("):
        assert invented not in preview, f"preview.py 가 접근 판정을 다시 구현했다: {invented}"
