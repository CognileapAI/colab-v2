"""`RenderResult` 의 **단일 이미지 갈래** — 계약 `core-viz.yaml` `oneOf` (`〈80〉-㉯ 1`).

stage 1 은 **이미지 갈래만** 낸다. 타일 갈래는 계약에 살아 있되(stage 2 확대 뷰가 쓴다)
**stage 1 이 내지 않는다** — 둘을 함께 실으면 `oneOf` 위반이고, 「무엇을 그릴지 두 번
적힌 완료」가 된다.

함께 세우는 것 둘:
- **V-2** 공통 스케일 — 범례 구간이 **프레임 자신의 min/max 가 아니라** 2–98 % 공통
  범위에서 나온다(`§10-7`).
- **K-4** 배지 두 종 — 정밀도 배지 · 색 범위 단계.
"""
from __future__ import annotations

import numpy as np
from conftest import AUTH


def _render(client, target: dict) -> dict:
    r = client.post("/viz/v1/renders",
                    json={"target": target, "style": {"palette": "단색-파랑"}},
                    headers=AUTH)
    assert r.status_code == 202, r.text
    job = r.json()
    job["_renderId"] = job["renderId"]
    return job


def test_결과는_이미지_갈래이고_타일틀을_함께_싣지_않는다(client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    job = _render(client, {"datasetId": tid})
    assert job["status"] == "완료", job.get("failure")
    res = job["result"]

    assert "tileUrlTemplate" not in res, "oneOf 다 — 둘을 함께 내지 않는다"
    assert set(res) <= {"imageUrl", "sidecarUrl", "worldFileUrl", "bounds", "legend",
                        "precisionBadge", "colorRangeStage"}
    assert res["imageUrl"] and res["sidecarUrl"] and res["worldFileUrl"]
    assert set(res["bounds"]) == {"west", "south", "east", "north"}


def test_지도형_결과에는_정밀도_배지가_붙는다(client, put_target, tiny_geotiff):
    """GeoTIFF 는 파일 안에서 격자가 계산된다 — 오차 2.8e-14°(`DATA-PIPELINE-MEASUREMENT §1.1`)."""
    tid = put_target(copy_from=[tiny_geotiff])
    job = _render(client, {"datasetId": tid})
    assert job["result"]["precisionBadge"] == "투영 계산 격자"


def test_등록_전_업로드는_잠정_등록된_데이터셋은_확정이다(client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    assert _render(client, {"uploadId": tid})["result"]["colorRangeStage"] == "잠정"
    tid2 = put_target(copy_from=[tiny_geotiff])
    assert _render(client, {"datasetId": tid2})["result"]["colorRangeStage"] == "확정"


def test_범례_구간은_프레임_min_max_가_아니라_2_98_공통_범위다(client, put_target, tiny_geotiff):
    """**V-2** — 현행은 프레임 자신의 값에서 구간을 잡았다. nc LST 에서 최대 42 DN 어긋난다."""
    tid = put_target(copy_from=[tiny_geotiff])
    job = _render(client, {"datasetId": tid})
    classes = job["result"]["legend"]["classes"]
    lo, hi = classes[0]["min"], classes[-1]["max"]

    values = np.arange(64, dtype="f4")             # tiny_geotiff 가 실제로 담은 값
    p2, p98 = (float(v) for v in np.percentile(values, [2, 98]))
    assert abs(lo - p2) < 0.5 and abs(hi - p98) < 0.5
    assert lo > float(values.min()) and hi < float(values.max()), \
        "프레임 min/max 를 그대로 쓰고 있다 — 공통 범위가 주입되지 않았다"


def test_산출물이_실제로_디스크에_세_벌_이상_놓인다(client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    job = _render(client, {"datasetId": tid})
    stored = client.app.state.jobs.get(job["renderId"]).artifacts
    kinds = {(a.layer, a.kind) for a in stored.all()}
    assert ("썸네일", "image") in kinds
    assert ("비지도형", "image") in kinds
    assert ("지도형", "image") in kinds
    assert ("지도형", "sidecar") in kinds and ("지도형", "worldfile") in kinds
    for a in stored.all():
        assert a.path.is_file() and a.size_bytes > 0


def test_타일_경로는_계약에_살아_있고_서명도_그대로다(client, put_target, tiny_geotiff):
    """**갈래를 안 내는 것과 경로를 지우는 것은 다르다** — stage 2 가 이 자리를 쓴다."""
    tid = put_target(copy_from=[tiny_geotiff])
    job = _render(client, {"datasetId": tid})
    template = client.app.state.jobs.get(job["renderId"]).tile_url_template
    url = template.replace("{z}", "0").replace("{x}", "0").replace("{y}", "0")
    assert "sig=" in url
    assert client.get(url).status_code == 200
