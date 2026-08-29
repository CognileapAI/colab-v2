"""`createScreenshot` — 지금 장면을 한 장의 PNG 로 (`core-viz.yaml` `/screenshots`).

**시각화 설정은 저장하지 않으므로 남길 장면은 여기서 뽑는다**(`Policy_데이터셋_상세 §8
스크린샷`). 층이 여럿이면 합성이 필요해 장면을 통째로 받는다 — 층 목록·순서·불투명도·
화면 크기는 지도 위젯만 아는 값이다.

**권한은 여기서 판정하지 않는다**(계약 산문) — `업로드·편집` 판정은 core-api 의 몫이고,
이 seam 이 보는 것은 서비스 자격 증명 하나다.
"""
from __future__ import annotations

import io

import numpy as np
from conftest import AUTH, make_client
from PIL import Image

URL = "/viz/v1/screenshots"


def _render(client, target: dict, palette: str = "단색-파랑") -> str:
    r = client.post("/viz/v1/renders",
                    json={"target": target, "style": {"palette": palette}},
                    headers=AUTH)
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["status"] == "완료", body.get("failure")
    return body["renderId"]


def _viewport(bounds: dict, width: int = 64, height: int = 64) -> dict:
    return {"width": width, "height": height, "bounds": bounds}


_TIF_BOUNDS = {"west": 126.0, "south": 36.0, "east": 128.0, "north": 38.0}


def _png(resp) -> Image.Image:
    assert resp.headers["content-type"] == "image/png", resp.headers
    return Image.open(io.BytesIO(resp.content))


def test_한_층을_뷰포트_크기의_PNG_로_뽑는다(client, put_target, tiny_geotiff):
    rid = _render(client, {"datasetId": put_target(copy_from=[tiny_geotiff])})
    r = client.post(URL, json={"layers": [{"renderId": rid, "opacity": 1}],
                               "viewport": _viewport(_TIF_BOUNDS, 40, 24)}, headers=AUTH)
    assert r.status_code == 200, r.text
    img = _png(r)
    assert img.size == (40, 24)
    assert img.mode == "RGBA"
    # 값이 있는 자리는 실제로 칠해진다 — 투명 판을 돌려주는 것이 아니다.
    assert np.asarray(img)[..., 3].max() == 255


def test_첫_항목이_맨_아래_층이다(client, put_target, tiny_geotiff):
    """층 순서는 배열 순서이고 **첫 항목이 맨 아래**다 (계약 `ScreenshotRequest` 산문)."""
    tid = put_target(copy_from=[tiny_geotiff])
    bottom = _render(client, {"datasetId": tid}, "단색-파랑")
    top = _render(client, {"datasetId": tid}, "발산-한난")

    up = client.post(URL, json={"layers": [{"renderId": bottom, "opacity": 1},
                                           {"renderId": top, "opacity": 1}],
                                "viewport": _viewport(_TIF_BOUNDS)}, headers=AUTH)
    down = client.post(URL, json={"layers": [{"renderId": top, "opacity": 1},
                                             {"renderId": bottom, "opacity": 1}],
                                  "viewport": _viewport(_TIF_BOUNDS)}, headers=AUTH)
    assert up.status_code == 200 and down.status_code == 200
    assert up.content != down.content, "순서를 뒤집었는데 같은 그림이면 순서를 안 쓴 것이다"


def test_얹은_층의_불투명도가_실제로_섞인다(client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    bottom = _render(client, {"datasetId": tid}, "단색-파랑")
    top = _render(client, {"datasetId": tid}, "발산-한난")
    view = _viewport(_TIF_BOUNDS)

    opaque = client.post(URL, json={"layers": [{"renderId": bottom, "opacity": 1},
                                               {"renderId": top, "opacity": 1}],
                                    "viewport": view}, headers=AUTH)
    blended = client.post(URL, json={"layers": [{"renderId": bottom, "opacity": 1},
                                                {"renderId": top, "opacity": 0.55}],
                                     "viewport": view}, headers=AUTH)
    assert opaque.status_code == 200 and blended.status_code == 200
    assert opaque.content != blended.content, "불투명도를 무시하면 두 그림이 같다"


def test_데이터_밖_뷰포트는_투명한_장면이다(client, put_target, tiny_geotiff):
    """없는 좌표를 지어내지 않는다 — 밖이면 빈 장면이고 실패가 아니다 (`DR-9`)."""
    rid = _render(client, {"datasetId": put_target(copy_from=[tiny_geotiff])})
    far = {"west": 10.0, "south": 10.0, "east": 12.0, "north": 12.0}
    r = client.post(URL, json={"layers": [{"renderId": rid}],
                               "viewport": _viewport(far, 16, 16)}, headers=AUTH)
    assert r.status_code == 200, r.text
    assert np.asarray(_png(r))[..., 3].max() == 0


def test_아직_그리는_중인_층이_있으면_409(manual_client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    r = manual_client.post("/viz/v1/renders",
                           json={"target": {"datasetId": tid},
                                 "style": {"palette": "단색-파랑"}}, headers=AUTH)
    assert r.status_code == 202
    rid = r.json()["renderId"]
    shot = manual_client.post(URL, json={"layers": [{"renderId": rid}],
                                         "viewport": _viewport(_TIF_BOUNDS)}, headers=AUTH)
    assert shot.status_code == 409, shot.text
    assert shot.json()["code"] == "RENDER_NOT_READY"


def test_없는_렌더는_404(client):
    r = client.post(URL, json={"layers": [{"renderId": "01J0000000000000000000000A"}],
                               "viewport": _viewport(_TIF_BOUNDS)}, headers=AUTH)
    assert r.status_code == 404, r.text
    assert r.json()["code"] == "NOT_FOUND", "라우트 부재의 404 를 판정으로 세지 않는다"


def test_수명이_다한_렌더는_404(source_root, put_target, tiny_geotiff):
    """계약의 `/screenshots` 에는 410 이 없다 — 없는 상태 코드를 지어내지 않는다."""
    # 수명이 붙는 것은 **등록 전 업로드**의 결과뿐이다 (정본 §8 ③ · `NB-2`).
    client = make_client(source_root, "inline", result_ttl_seconds=-1)
    rid = _render(client, {"uploadId": put_target(copy_from=[tiny_geotiff])})
    r = client.post(URL, json={"layers": [{"renderId": rid}],
                               "viewport": _viewport(_TIF_BOUNDS)}, headers=AUTH)
    assert r.status_code == 404, r.text
    assert r.json()["code"] == "NOT_FOUND", "라우트 부재의 404 를 판정으로 세지 않는다"


def test_층이_비면_400(client):
    r = client.post(URL, json={"layers": [], "viewport": _viewport(_TIF_BOUNDS)}, headers=AUTH)
    assert r.status_code == 400, r.text


def test_자격_증명이_없으면_401(client):
    r = client.post(URL, json={"layers": [{"renderId": "01J0000000000000000000000A"}],
                               "viewport": _viewport(_TIF_BOUNDS)})
    assert r.status_code == 401, r.text
