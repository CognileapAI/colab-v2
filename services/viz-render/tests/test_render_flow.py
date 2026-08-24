"""createRender · getRender · getRenderTile — 미리보기 최소 렌더 경로.

정본이 값을 준 것만 단언한다:
  단계 3값 = `파일 읽는 중` → `지도 그리는 중` → `범례 만드는 중` (정본 문구 그대로)
  상태 3값 = `그리는 중` · `완료` · `실패` (취소 없음)
  구간 수 = 3~9, 기본 6
"""
from __future__ import annotations

from conftest import AUTH

STAGES = ["파일 읽는 중", "지도 그리는 중", "범례 만드는 중"]


def _create(client, target, **kw):
    body = {"target": target, "style": {"palette": "단색-파랑"}}
    body.update(kw)
    return client.post("/viz/v1/renders", json=body, headers=AUTH)


def test_createRender_는_202_와_RenderJob_을_돌려준다(client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    r = _create(client, {"datasetId": tid})
    assert r.status_code == 202
    job = r.json()
    assert set(job) <= {"renderId", "status", "stage", "expiresAt", "result",
                        "failure", "partialFailure"}
    assert len(job["renderId"]) == 26
    assert job["status"] in ("그리는 중", "완료", "실패")


def test_진행_단계_3값이_실제로_흐른다(client, put_target, tiny_geotiff):
    """한 덩어리 「로딩 중」으로 두지 않는다 — 멈춘 것과 진행이 구분돼야 한다."""
    tid = put_target(copy_from=[tiny_geotiff])
    rid = _create(client, {"datasetId": tid}).json()["renderId"]
    assert client.app.state.jobs.get(rid).stage_history == STAGES


def test_그리는_중일_때만_stage_가_있다(manual_client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    rid = _create(manual_client, {"datasetId": tid}).json()["renderId"]
    drawing = manual_client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()
    assert drawing["status"] == "그리는 중"
    assert drawing["stage"] in STAGES
    assert "result" not in drawing

    manual_client.app.state.jobs.run_pending()
    done = manual_client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()
    assert done["status"] == "완료"
    assert "stage" not in done          # 그리는 중일 때만 있다
    assert "failure" not in done


def test_완료_결과는_이미지_경계_범례를_준다(client, put_target, tiny_geotiff):
    """⚠ **개정** — `〈80〉-㉯ 1` 로 결과가 `oneOf` 가 됐고 stage 1 은 이미지 갈래를 낸다.
    타일 갈래는 계약에 살아 있되 stage 2 것이다 — 여기서 둘을 함께 요구하면 `oneOf` 위반을
    시험이 강요하게 된다."""
    tid = put_target(copy_from=[tiny_geotiff])
    rid = _create(client, {"datasetId": tid}).json()["renderId"]
    job = client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()
    res = job["result"]
    assert set(res) == {"imageUrl", "sidecarUrl", "worldFileUrl", "bounds", "legend",
                        "precisionBadge", "colorRangeStage"}
    assert res["imageUrl"].endswith(".png") and res["worldFileUrl"].endswith(".pgw")
    b = res["bounds"]
    assert set(b) == {"west", "south", "east", "north"}
    assert -180 <= b["west"] < b["east"] <= 180
    assert -90 <= b["south"] < b["north"] <= 90
    lg = res["legend"]
    assert lg["palette"] == "단색-파랑"
    assert len(lg["classes"]) == 6            # 기본 6
    for c in lg["classes"]:
        assert set(c) == {"color", "min", "max"}
        assert len(c["color"]) == 7 and c["color"][0] == "#"


def test_구간_수는_3에서_9까지다(client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    for n in (3, 9):
        rid = _create(client, {"datasetId": tid},
                      style={"palette": "단색-파랑", "classCount": n}).json()["renderId"]
        job = client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()
        assert len(job["result"]["legend"]["classes"]) == n
    for bad in (2, 10):
        r = _create(client, {"datasetId": tid},
                    style={"palette": "단색-파랑", "classCount": bad})
        assert r.status_code in (400, 422)


def test_타일은_PNG_이고_빈_타일도_200_이다(client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    rid = _create(client, {"datasetId": tid}).json()["renderId"]
    # z=0 한 장에 전 지구가 들어간다 — 데이터가 있는 타일
    hit = client.get(f"/viz/v1/renders/{rid}/tiles/0/0/0.png", headers=AUTH)
    assert hit.status_code == 200
    assert hit.headers["content-type"] == "image/png"
    assert hit.content[:8] == b"\x89PNG\r\n\x1a\n"
    # 값이 없는 자리도 404 가 아니다 — 404 면 지도 위젯이 재시도를 반복한다
    empty = client.get(f"/viz/v1/renders/{rid}/tiles/2/0/0.png", headers=AUTH)
    assert empty.status_code == 200
    assert empty.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_그리는_중인_작업의_타일은_409(manual_client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    rid = _create(manual_client, {"datasetId": tid}).json()["renderId"]
    r = manual_client.get(f"/viz/v1/renders/{rid}/tiles/0/0/0.png", headers=AUTH)
    assert r.status_code == 409
    assert set(r.json()) >= {"code", "message"}


def test_없는_렌더는_404(client):
    from colab_viz.kernel.ids import new_ulid
    r = client.get(f"/viz/v1/renders/{new_ulid()}", headers=AUTH)
    assert r.status_code == 404
