"""테넌트 경계 — **viz-render 가 `X-CoLAB-Lab` 을 실제로 읽고 대조한다.**

⭑ ⟨2026-09-03 · 코드리뷰 `CODE-REVIEW-20260903.md` #1⟩ 종전에는 `grep -rn 'X-CoLAB'
services/viz-render/src` 가 **0건**이었다. core-api `relay._scope_headers` 가 모든 중계
호출에 두 헤더를 실어 보내는데 받는 쪽이 어디서도 읽지 않았고, core-api `preview.py` 는
그 응답을 「유일한 정직한 경계 확인」으로 삼고 있었다 — 즉 **아무도 경계를 안 봤다.**
타 연구실 `renderId` 로 서명된 `tileUrlTemplate`·`imageUrl`·범례·경계 좌표를 받고,
그 `renderId` 를 층으로 얹어 스크린샷까지 합성할 수 있었다.

**닫는 자리는 `getRender` 다.** 서명된 타일 주소가 나가는 문이 거기 하나뿐이므로,
거기서 막으면 타일도 함께 막힌다.

**타일 경로는 서명만으로 남는다** — 브라우저 지도 위젯이 CDN 을 통해 **직접** 부르는
유일한 경로라(계약 `getRenderTile` 산문) 헤더를 실을 수 없다. 여기에 헤더를 요구하면
계약대로인데 실배포에서 전량 401 이 된다(`renders.py` `tile_router` 주석과 같은 근거).
"""
from __future__ import annotations

from colab_viz.app import deps
from colab_viz.kernel import errors

from conftest import ACCOUNT, AUTH, LAB, TOKEN, auth_as, make_client

_OTHER_LAB = "01JQ00000000000000000LAB02"
_BODY = {"target": {"datasetId": None}, "style": {"palette": "단색-파랑"}}


def _create(client, tid: str, headers=AUTH):
    return client.post("/viz/v1/renders", headers=headers, json={
        "target": {"datasetId": tid}, "style": {"palette": "단색-파랑"}})


def _rendered(client, put_target, tiny_geotiff, headers=AUTH) -> str:
    tid = put_target(copy_from=[tiny_geotiff])
    r = _create(client, tid, headers)
    assert r.status_code == 202, r.text
    return r.json()["renderId"]


# ── ① 접수 — 헤더를 job 에 새긴다 ────────────────────────────────────────────
def test_createRender_가_경계_헤더를_job_에_새긴다(client, put_target, tiny_geotiff):
    rid = _rendered(client, put_target, tiny_geotiff)
    job = client.app.state.jobs.get(rid)
    assert job.lab == LAB, "연구실이 job 에 새겨지지 않았다"
    assert job.account == ACCOUNT


def test_createRender_는_경계_헤더가_없으면_400_이다(client, put_target, tiny_geotiff):
    """**fail-closed.** 「헤더가 없으니 경계 검사를 건너뛴다」가 곧 green-by-skip 이다."""
    tid = put_target(copy_from=[tiny_geotiff])
    r = client.post("/viz/v1/renders", headers={"Authorization": f"Bearer {TOKEN}"},
                    json={"target": {"datasetId": tid}, "style": {"palette": "단색-파랑"}})
    assert r.status_code == 400, r.text
    assert r.json()["code"] == errors.TENANT_SCOPE_MISSING
    assert r.json()["details"]["header"] == deps.LAB_HEADER


def test_빈_문자열_헤더는_없는_것과_같다(client, put_target, tiny_geotiff):
    """공백만 실어 보내는 것으로 경계를 비우지 못한다."""
    tid = put_target(copy_from=[tiny_geotiff])
    r = _create(client, tid, auth_as("   "))
    assert r.status_code == 400
    assert r.json()["code"] == errors.TENANT_SCOPE_MISSING


# ── ② 조회 — 남의 것은 「없다」 ───────────────────────────────────────────────
def test_getRender_는_다른_연구실에_404_다(client, put_target, tiny_geotiff):
    """**존재를 흘리지 않는다** — 403 이면 「그 id 는 있다」를 알려 준다."""
    rid = _rendered(client, put_target, tiny_geotiff)
    r = client.get(f"/viz/v1/renders/{rid}", headers=auth_as(_OTHER_LAB))
    assert r.status_code == 404, r.text
    assert r.json()["code"] == "NOT_FOUND"
    body = r.text
    for leak in ("tileUrlTemplate", "imageUrl", "legend", "bounds"):
        assert leak not in body, f"404 봉투에 {leak} 가 실려 나갔다"


def test_getRender_는_자기_연구실에_200_이다(client, put_target, tiny_geotiff):
    rid = _rendered(client, put_target, tiny_geotiff)
    r = client.get(f"/viz/v1/renders/{rid}", headers=AUTH)
    assert r.status_code == 200 and r.json()["renderId"] == rid


def test_getRender_는_경계_헤더가_없으면_400_이다(client, put_target, tiny_geotiff):
    rid = _rendered(client, put_target, tiny_geotiff)
    r = client.get(f"/viz/v1/renders/{rid}",
                   headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 400
    assert r.json()["code"] == errors.TENANT_SCOPE_MISSING


# ── ③ 스크린샷 — 층마다 본다 ─────────────────────────────────────────────────
def _shot(client, rids, headers=AUTH):
    return client.post("/viz/v1/screenshots", headers=headers, json={
        "layers": [{"renderId": r, "opacity": 1.0} for r in rids],
        "viewport": {"width": 32, "height": 32,
                     "bounds": {"west": 126.0, "south": 36.0,
                                "east": 128.0, "north": 38.0}}})


def test_스크린샷은_남의_층을_합성하지_않는다(client, put_target, tiny_geotiff):
    """**한 층만 남의 것이어도 안 된다** — 층마다 대조한다."""
    mine = _rendered(client, put_target, tiny_geotiff)
    theirs = _rendered(client, put_target, tiny_geotiff, auth_as(_OTHER_LAB))
    assert _shot(client, [mine]).status_code == 200
    r = _shot(client, [mine, theirs])
    assert r.status_code == 404, r.text
    assert r.json()["code"] == "NOT_FOUND"


def test_스크린샷은_경계_헤더가_없으면_400_이다(client, put_target, tiny_geotiff):
    rid = _rendered(client, put_target, tiny_geotiff)
    r = _shot(client, [rid], headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 400
    assert r.json()["code"] == errors.TENANT_SCOPE_MISSING


# ── ④ 값 조회 — 헤더는 요구하고, 대조는 core-api 가 한다 ─────────────────────
def test_값_조회는_경계_헤더가_없으면_400_이다(client, put_target, tiny_geotiff):
    """⚠ **대조할 상대가 없다** — 이 op 은 `renderId` 가 아니라 `datasetId` 로 들어오고
    viz 에는 「그 데이터셋이 어느 연구실 것인가」를 아는 표가 없다(저장 배치가 평평하다).
    그 판정은 core-api 가 `require_body_access` 로 이미 한다(계약 산문 · 권한 ⓑ).
    여기서 잠그는 것은 **헤더가 실려 오는 것 자체**다 — 없으면 부르는 쪽 배선이 깨진 것이고,
    깨진 배선을 통과시키면 그것이 곧 「검사 대상 0건을 통과로 세는 것」이다.
    """
    tid = put_target(copy_from=[tiny_geotiff])
    body = {"datasetId": tid, "fileId": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            "point": {"lat": 37.0, "lon": 127.0}}
    r = client.post("/viz/v1/value-lookups",
                    headers={"Authorization": f"Bearer {TOKEN}"}, json=body)
    assert r.status_code == 400
    assert r.json()["code"] == errors.TENANT_SCOPE_MISSING


# ── ⑤ 타일 — 서명만이다 (음성) ───────────────────────────────────────────────
def test_타일은_경계_헤더_없이도_서명만으로_열린다(tile_client, put_target, tiny_geotiff):
    """**음성 · 넓히지 않는 자리.** 브라우저는 헤더를 실을 수 없다 — 지도 위젯이 CDN 을
    통해 직접 부르는 유일한 경로라 여기에 헤더를 요구하면 실배포에서 전량 401 이다.
    새는 문은 **서명된 주소를 발급하는 `getRender`** 이고 그 문은 ②가 닫았다.
    """
    rid = _rendered(tile_client, put_target, tiny_geotiff, AUTH)
    job = tile_client.app.state.jobs.get(rid)
    url = job.tile_url_template.format(z=0, x=0, y=0)
    r = tile_client.get(url)                       # 헤더 0개 — 서명만
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "image/png"


def test_팔레트_목록은_경계_헤더를_요구하지_않는다(client):
    """**음성.** 팔레트는 연구실 자료가 아니라 이 단위가 소유한 고정 목록이고,
    계약이 이 op 에 400 을 두지 않았다(200·401·503). **없는 상태를 지어내지 않는다.**"""
    r = client.get("/viz/v1/palettes", headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 200


# ── ⑥ 자동 재생성이 경계를 잃지 않는다 ───────────────────────────────────────
def test_재생성된_job_이_원래_연구실을_이어받는다(source_root, put_target, tiny_geotiff):
    """트리거는 연구실을 싣지 않는다(`envelope.json` 은 `labId` 를 싣지만 이 seam 의
    `InvalidationEvent` 에는 그 자리가 없다). **직전 job 에서 이어받는다** — 안 이어받으면
    재생성 한 번에 경계가 빈 job 이 생기고 그것은 아무에게도 안 보인다."""
    from colab_viz.domains.d7_visualization import invalidation

    client = make_client(source_root, "inline")
    tid = put_target(copy_from=[tiny_geotiff])
    assert _create(client, tid).status_code == 202
    outcome = client.app.state.jobs.regenerate(
        invalidation.InvalidationEvent(trigger=invalidation.TRIGGER_BACKEND_RERUN,
                                       target_id=tid),
        source=client.app.state.source)
    assert outcome.job.lab == LAB, "재생성이 경계를 잃었다"
    assert client.get(f"/viz/v1/renders/{outcome.job.render_id}",
                      headers=auth_as(_OTHER_LAB)).status_code == 404
