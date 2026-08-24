"""거절과 실패 — 「그릴 수 없는 것」과 「등록할 수 없는 것」은 다르다.

413 렌더 상한 · 415 어느 표현으로도 못 그림(`details.renderableFormats` 필수) ·
대상 둘 다/하나도 없음 · 실패 3종의 `failure.code` 구분.
"""
from __future__ import annotations

import pytest

from colab_viz.kernel.ids import new_ulid
from conftest import AUTH

_STYLE = {"palette": "단색-파랑"}


def _post(client, target, **kw):
    body = {"target": target, "style": _STYLE}
    body.update(kw)
    return client.post("/viz/v1/renders", json=body, headers=AUTH)


def test_대상은_정확히_하나다(client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    assert _post(client, {"datasetId": tid, "uploadId": new_ulid()}).status_code in (400, 422)
    assert _post(client, {}).status_code in (400, 422)


def test_없는_대상은_404(client):
    assert _post(client, {"datasetId": new_ulid()}).status_code == 404


def test_렌더_상한을_넘으면_413(source_root, put_target):
    """정본 「미리보기는 500MB까지 그려요」 [가정] — 화면은 「조각 하나를 골라 그린다」로 안내한다."""
    from fastapi.testclient import TestClient
    from colab_viz.app.main import create_app
    from colab_viz.kernel.config import Settings
    from conftest import SIGNING_SECRET, TOKEN

    tid = put_target(files={"big.tif": b"II*\x00" + b"\x00" * 4096})
    app = create_app(Settings(source_root=source_root, service_token=TOKEN,
                              tile_signing_secret=SIGNING_SECRET,
                              execution="inline", max_render_bytes=1024,
                              result_ttl_seconds=3600))
    c = TestClient(app)
    r = c.post("/viz/v1/renders", json={"target": {"datasetId": tid}, "style": _STYLE},
               headers=AUTH)
    assert r.status_code == 413
    assert r.json()["code"]


def test_그릴_수_없는_포맷은_415_이고_그릴_수_있는_형식을_함께_말한다(client, put_target):
    """안 되는 것만 말하면 무엇을 올려야 하는지 모른 채 떠난다 (정본 §8·계약 산문)."""
    tid = put_target(files={"메모.txt": "이건 래스터가 아니다\n".encode()})
    r = _post(client, {"datasetId": tid})
    assert r.status_code == 415
    body = r.json()
    assert set(body) >= {"code", "message"}
    formats = body["details"]["renderableFormats"]
    # 〈51〉·〈77〉 — 숫자가 아니라 목록이다. GRIB 은 v2 범위 밖이고 HDF 는 버전이 다르며,
    # `NumPy` 가 **독립 포맷**으로 들어왔다(Ted 판정 — 「nc 랑은 다른 파일이다」).
    assert formats == ["NetCDF", "Binary", "HDF4", "GeoTIFF", "NumPy"]


def test_실패_3종은_failure_code_로_갈린다():
    """정본 §9 — 그리는 서버에 연결 못 함 · 시간 초과 · 알 수 없는 오류."""
    from colab_viz.domains.d7_visualization.failures import FAILURE_MESSAGES, RenderFailure

    codes = {RenderFailure.UNREACHABLE, RenderFailure.TIMEOUT, RenderFailure.UNKNOWN}
    assert len(codes) == 3
    for c in codes:
        assert FAILURE_MESSAGES[c]              # 정본 문구가 붙어 있다


def test_실패해도_200_이고_이유는_failure_에_담긴다(source_root, put_target, tiny_geotiff):
    """실패는 4xx 가 아니다 — 작업 조회는 200 이고 `failure` 가 이유를 말한다."""
    from fastapi.testclient import TestClient
    from colab_viz.app.main import create_app
    from colab_viz.domains.d7_visualization.failures import RenderFailure
    from colab_viz.kernel.config import Settings
    from conftest import SIGNING_SECRET, TOKEN

    tid = put_target(copy_from=[tiny_geotiff])
    app = create_app(Settings(source_root=source_root, service_token=TOKEN,
                              tile_signing_secret=SIGNING_SECRET,
                              execution="inline", max_render_bytes=500 * 1024 * 1024,
                              result_ttl_seconds=3600, render_deadline_seconds=0.0))
    c = TestClient(app)
    rid = c.post("/viz/v1/renders", json={"target": {"datasetId": tid}, "style": _STYLE},
                 headers=AUTH).json()["renderId"]
    job = c.get(f"/viz/v1/renders/{rid}", headers=AUTH)
    assert job.status_code == 200
    body = job.json()
    assert body["status"] == "실패"
    assert body["failure"]["code"] == RenderFailure.TIMEOUT
    assert "result" not in body


def test_수명이_다한_렌더의_타일은_410(source_root, put_target, tiny_geotiff):
    from fastapi.testclient import TestClient
    from colab_viz.app.main import create_app
    from colab_viz.kernel.config import Settings
    from conftest import SIGNING_SECRET, TOKEN

    tid = put_target(copy_from=[tiny_geotiff])
    app = create_app(Settings(source_root=source_root, service_token=TOKEN,
                              tile_signing_secret=SIGNING_SECRET,
                              execution="inline", max_render_bytes=500 * 1024 * 1024,
                              result_ttl_seconds=-1))
    c = TestClient(app)
    rid = c.post("/viz/v1/renders", json={"target": {"uploadId": tid}, "style": _STYLE},
                 headers=AUTH).json()["renderId"]
    assert c.get(f"/viz/v1/renders/{rid}/tiles/0/0/0.png", headers=AUTH).status_code == 410


def test_인증이_없으면_401(client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    assert client.post("/viz/v1/renders",
                       json={"target": {"datasetId": tid}, "style": _STYLE}).status_code == 401
