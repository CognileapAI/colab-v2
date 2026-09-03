"""작업 보관 — **수명이 다한 뒤에만 축출한다** · 스크린샷 층 상한.

⭑ ⟨2026-09-03 · 코드리뷰 `CODE-REVIEW-20260903.md` #11⟩
`JobStore._jobs` 에는 삽입·조회·전체 스캔만 있고 `del`/`pop`/`clear` 가 **한 자리도**
없었다. 완료된 작업이 `rendered.values`(f4 2D 래스터)를 프로세스 수명 내내 붙들고,
`_produced_for` 는 submit 마다 **전 작업**을 순회했다.

**그렇다고 완료 시점에 놓으면 안 된다** — 타일(`getRenderTile`)과 스크린샷
(`createScreenshot`)이 `job.rendered` 를 **메모리에서** 읽는다. 놓는 자리는 **만료
뒤**이고, 만료된 id 는 계약이 요구하는 410 을 계속 답해야 하므로 가벼운 묘비를 남긴다.
묘비도 무한하지 않다 — 개수를 묶는다.
"""
from __future__ import annotations

import numpy as np
import pytest

from colab_viz.domains.d7_visualization import jobs as jobs_mod
from colab_viz.domains.d7_visualization import screenshot
from colab_viz.kernel import errors

from conftest import AUTH, make_client

_STYLE = {"palette": "단색-파랑"}
_TIF_BOUNDS = {"west": 126.0, "south": 36.0, "east": 128.0, "north": 38.0}


def _render(client, target: dict) -> str:
    r = client.post("/viz/v1/renders", headers=AUTH,
                    json={"target": target, "style": _STYLE})
    assert r.status_code == 202, r.text
    return r.json()["renderId"]


# ── ① 완료 시점에는 놓지 않는다 (음성) ───────────────────────────────────────
def test_완료해도_래스터를_놓지_않는다(client, put_target, tiny_geotiff):
    """**음성 · 이 항목의 가장 큰 덫.** 「메모리를 줄인다」를 완료 시점 해제로 읽으면
    타일과 스크린샷이 곧바로 죽는다 — 둘 다 `job.rendered` 를 메모리에서 읽는다."""
    rid = _render(client, {"datasetId": put_target(copy_from=[tiny_geotiff])})
    job = client.app.state.jobs.get(rid)
    assert job.status == "완료" and job.rendered is not None, "완료 직후에 래스터를 놓았다"
    assert job.artifacts is not None
    r = client.post("/viz/v1/screenshots", headers=AUTH, json={
        "layers": [{"renderId": rid, "opacity": 1.0}],
        "viewport": {"width": 16, "height": 16, "bounds": _TIF_BOUNDS}})
    assert r.status_code == 200, r.text


# ── ② 만료 뒤에 축출하고, 묘비가 410 을 답한다 ───────────────────────────────
def test_수명이_다한_작업만_축출되고_410_은_남는다(source_root, put_target, tiny_geotiff):
    """수명이 붙는 것은 **등록 전 업로드**의 결과뿐이다(정본 §8 ③ · `NB-2`)."""
    client = make_client(source_root, "inline", result_ttl_seconds=-1)
    rid = _render(client, {"uploadId": put_target(copy_from=[tiny_geotiff])})
    store = client.app.state.jobs

    tomb = store.get(rid)
    assert tomb is not None, "만료된 id 가 통째로 사라져 410 을 답할 수 없다"
    assert tomb.expired
    assert tomb.rendered is None, "만료됐는데 래스터를 그대로 붙들고 있다"
    assert tomb.artifacts is None
    assert client.get(f"/viz/v1/renders/{rid}/tiles/0/0/0.png",
                      headers=AUTH).status_code == 410


def test_수명이_남은_작업은_축출되지_않는다(source_root, put_target, tiny_geotiff):
    """**음성.** 축출의 조건은 `expires_at` 하나다 — 개수도 순서도 아니다."""
    client = make_client(source_root, "inline", result_ttl_seconds=3600)
    store = client.app.state.jobs
    rid = _render(client, {"uploadId": put_target(copy_from=[tiny_geotiff])})
    for _ in range(5):                       # submit 이 축출을 부른다
        _render(client, {"uploadId": put_target(copy_from=[tiny_geotiff])})
    assert store.get(rid).rendered is not None, "수명이 남았는데 축출됐다"


def test_묘비는_개수가_묶여_있다(source_root, put_target, tiny_geotiff):
    """묘비를 무한히 쌓으면 그것이 다시 같은 결함이다 — 가장 오래된 것부터 놓는다.
    그때는 404 이고, 그것이 정직하다(그 id 에 대해 아는 것이 없다)."""
    client = make_client(source_root, "inline", result_ttl_seconds=-1)
    store = client.app.state.jobs
    store._max_tombstones = 3                # 상한을 시험이 낮춘다 — 값이 아니라 성질을 잰다
    ids = [_render(client, {"uploadId": put_target(copy_from=[tiny_geotiff])})
           for _ in range(5)]
    assert store.get(ids[0]) is None, "묘비가 무한히 쌓인다"
    assert store.get(ids[-1]) is not None, "가장 최근 묘비까지 놓았다"
    assert len(store._jobs) <= 3 + 1, "축출됐는데 작업 표가 안 줄었다"


# ── ③ 산출물 색인 — 전체 스캔을 대신한다 ─────────────────────────────────────
def test_산출물_후보를_대상별_색인에서_찾는다(source_root, put_target, tiny_geotiff):
    """`_produced_for` 가 submit 마다 전 작업을 순회했다 — 1000번째 submit 은 그리기
    전에 1000회 순회했다. 색인은 **대상별**이라 남의 작업 수와 무관하다."""
    client = make_client(source_root, "inline")
    store = client.app.state.jobs
    mine = put_target(copy_from=[tiny_geotiff])
    _render(client, {"datasetId": mine})
    for _ in range(4):                       # 남의 대상들
        _render(client, {"datasetId": put_target(copy_from=[tiny_geotiff])})

    assert set(store._produced) >= {mine}, "대상별 색인이 아니다"
    got = store._produced_for(mine)
    assert got, "내 대상의 산출물 후보가 비었다"
    assert all(c.path.exists() for c in got)
    assert len(got) == len(store._produced[mine]), "색인 밖에서 다시 훑고 있다"


def test_축출돼도_산출물_후보는_남는다(source_root, put_target, tiny_geotiff):
    """**작업을 놓는 것과 디스크의 산출물을 잊는 것은 다른 사실이다.** 색인을 작업에
    매달아 두면 축출과 함께 후보가 사라지고, 그 파일들은 영원히 무효화되지 않는다."""
    client = make_client(source_root, "inline", result_ttl_seconds=-1)
    store = client.app.state.jobs
    tid = put_target(copy_from=[tiny_geotiff])
    rid = _render(client, {"uploadId": tid})
    before = {c.path for c in store._produced_for(tid)}
    assert before
    assert store.get(rid).artifacts is None, "축출되지 않았다 — 시험이 아무것도 안 잰다"
    assert {c.path for c in store._produced_for(tid)} == before


# ── ④ 스크린샷 층 상한 ───────────────────────────────────────────────────────
def test_층_상한을_넘으면_400_이고_상한을_알려_준다(client, put_target, tiny_geotiff):
    """**계약이 선언한 코드 안에서 막는다** — `/screenshots` 의 응답은
    200·400·401·404·409·503 이고 **413 이 없다.** 없는 상태 코드를 지어내지 않는다.
    상한을 응답에 실어야 화면이 「몇 층까지인가」를 코드에 박지 않는다."""
    rid = _render(client, {"datasetId": put_target(copy_from=[tiny_geotiff])})
    over = screenshot.MAX_LAYERS + 1
    r = client.post("/viz/v1/screenshots", headers=AUTH, json={
        "layers": [{"renderId": rid, "opacity": 1.0} for _ in range(over)],
        "viewport": {"width": 16, "height": 16, "bounds": _TIF_BOUNDS}})
    assert r.status_code == 400, r.text
    body = r.json()
    assert body["code"] == errors.TOO_MANY_LAYERS
    assert body["details"]["maxLayers"] == screenshot.MAX_LAYERS
    assert body["details"]["layers"] == over


def test_상한까지는_그대로_합성한다(client, put_target, tiny_geotiff):
    """**음성 · 좁히지 않는다.** 상한은 상한이지 새 하한이 아니다."""
    rid = _render(client, {"datasetId": put_target(copy_from=[tiny_geotiff])})
    r = client.post("/viz/v1/screenshots", headers=AUTH, json={
        "layers": [{"renderId": rid, "opacity": 1.0}
                   for _ in range(screenshot.MAX_LAYERS)],
        "viewport": {"width": 16, "height": 16, "bounds": _TIF_BOUNDS}})
    assert r.status_code == 200, r.text


def test_뷰포트_상한은_계약_값_그대로다():
    """**음성 · 계약을 좁히지 않는다.** 뷰포트는 계약(`Viewport.width`·`height` 의
    `maximum`)이 이미 4096 으로 묶었다 — 이 레인이 더 좁히면 계약대로 부르는 쪽이
    이유 없이 거절당한다."""
    assert screenshot.MAX_SIDE == 4096
