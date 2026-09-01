"""사이드카가 **소유 판정의 근거**가 된다 — `A-1` 안 ⑷(사이드카 판정) 최소 묶음 1→3.

세 가지를 못 박는다.
1. `source` 는 **`fileId`** 다. 종전 문면은 「파일명」이었고 실배포에서만 우연히 같았다
   (`dev-package/notes/A-1-PORT-COST.md §1`).
2. 사이드카가 **세 층 전부**에 놓인다 — 썸네일 `.webp` · 비지도형 `.png` · 지도형 `.png`
   (완료 정의 ⑹).
3. 사이드카가 **구운 시점의 소유 대상**을 싣는다 — `baked_for.target_id`·`is_upload`
   (완료 정의 ⑴⑵). Port 를 새로 열지 않는다: 값은 이미 D7 안에 있다.
"""
from __future__ import annotations

import json
import re

import numpy as np
import pytest
from conftest import AUTH

from colab_viz.domains.d7_visualization import colormap, preview, scale
from colab_viz.kernel.ids import _ALPHABET

_LUT = colormap.lut256(colormap.VIRIDIS_ANCHORS)
_KEY_PARAMS = dict(source_digest="d", fills=(), palette="단색-파랑", selection="v")
_ULID_RE = re.compile(rf"^[{_ALPHABET}]{{26}}$")
_FID_A = "01J0FAB" + "0" * 18 + "A"
_FID_B = "01J0FAB" + "0" * 18 + "B"
assert len(_FID_A) == len(_FID_B) == 26
_OWNER = preview.BakeOwner(target_id="01J0TARGET00000000000000", is_upload=True)


def _range():
    return scale.for_dataset("01ARZ3NDEKTSV4RRFFQ69G5FAW",
                             [np.linspace(0, 100, 100, dtype="f4").reshape(-1, 1)])


def _korea_grid(ny: int = 200, nx: int = 160):
    lat = np.repeat(np.linspace(38.0, 33.0, ny)[:, None], nx, axis=1)
    lon = np.repeat(np.linspace(125.0, 130.0, nx)[None, :], ny, axis=0)
    values = np.linspace(0, 100, ny * nx, dtype="f4").reshape(ny, nx)
    return values, lat, lon


# ── ⑹ 세 층 전부에 사이드카가 놓인다 ────────────────────────────────────────
def test_썸네일과_비지도형에도_사이드카가_놓인다(tmp_path):
    values = np.linspace(0, 100, 512 * 512, dtype="f4").reshape(512, 512)
    thumb, detail, thumb_sc, detail_sc = preview.build_value_layers(
        values, color_range=_range(), lut=_LUT, out_dir=tmp_path,
        url_base="/previews", key_params=_KEY_PARAMS,
        source=_FID_A, sources=(_FID_A,),
        owner=_OWNER)

    assert thumb_sc.path.suffix == ".json" and detail_sc.path.suffix == ".json"
    # 자리는 **같은 키 아래**다 — `layout.json` `why ④`「확장자가 층을 가른다」
    assert thumb_sc.cache_key == thumb.cache_key
    assert detail_sc.cache_key == detail.cache_key
    assert (thumb_sc.layer, thumb_sc.kind) == (preview.LAYER_THUMBNAIL, "sidecar")
    assert (detail_sc.layer, detail_sc.kind) == (preview.LAYER_DETAIL, "sidecar")

    doc = json.loads(thumb_sc.path.read_text(encoding="utf-8"))
    # 좌표 없는 층이다 — **없는 경계를 지어내지 않는다**(`DR-9`)
    assert "bbox_3857" not in doc and "bbox_4326" not in doc and "crs" not in doc
    assert doc["layer"] == preview.LAYER_THUMBNAIL
    assert doc["name"] == thumb.path.name
    assert doc["width"] > 0 and doc["height"] > 0


# ── ⑴ `source` 는 fileId 다 ──────────────────────────────────────────────────
def test_사이드카_source_는_fileId_이고_사이드카_판이_박힌다(tmp_path):
    values, lat, lon = _korea_grid()
    _, sidecar, _, _ = preview.build_map_layer(
        values, lat, lon, color_range=_range(), lut=_LUT, out_dir=tmp_path,
        url_base="/previews", key_params=_KEY_PARAMS, grid_digest=None,
        source=_FID_A,
        sources=(_FID_A, _FID_B),
        owner=_OWNER)
    doc = json.loads(sidecar.path.read_text(encoding="utf-8"))
    assert doc["source"] == _FID_A
    assert doc["sources"] == [_FID_A, _FID_B]
    # 구판(파일명을 싣던 사이드카)과 **기계가 갈라 볼 수 있어야 한다**
    assert doc["sidecarVersion"] == preview.SIDECAR_VERSION == 2


# ── ⑴⑵ 구운 시점의 소유 대상 ────────────────────────────────────────────────
def test_사이드카는_구운_시점의_대상을_싣는다(tmp_path):
    values, lat, lon = _korea_grid()
    _, sidecar, _, _ = preview.build_map_layer(
        values, lat, lon, color_range=_range(), lut=_LUT, out_dir=tmp_path,
        url_base="/previews", key_params=_KEY_PARAMS, grid_digest=None,
        source=_FID_A, sources=(_FID_A,),
        owner=_OWNER)
    doc = json.loads(sidecar.path.read_text(encoding="utf-8"))
    # 이름이 「구운 시점」임을 말한다 — 등록 전환 뒤에는 낡는다(최신 소유는 원장 대조가 답한다)
    assert doc["baked_for"] == {"target_id": _OWNER.target_id, "is_upload": True}


# ── 배선: 렌더 경로가 실제로 fileId 를 넣는가 ───────────────────────────────
def _render(client, target: dict) -> dict:
    r = client.post("/viz/v1/renders",
                    json={"target": target, "style": {"palette": "단색-파랑"}},
                    headers=AUTH)
    assert r.status_code == 202, r.text
    return r.json()


def test_렌더_경로는_파일명이_아니라_fileId_를_적는다(client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    job = _render(client, {"uploadId": tid})
    assert job["status"] == "완료", job.get("failure")
    store = client.app.state.jobs.get(job["renderId"]).artifacts

    for sc in (store.sidecar, store.thumbnail_sidecar, store.detail_sidecar):
        doc = json.loads(sc.path.read_text(encoding="utf-8"))
        assert doc["source"] != "tiny.tif", "파일명이 그대로 실렸다"
        assert _ULID_RE.match(doc["source"]), doc["source"]
        assert doc["baked_for"] == {"target_id": tid, "is_upload": True}

    # 산출물 목록에 새 두 벌이 함께 선다 — 무효화가 이들을 함께 치운다(`invalidation`)
    kinds = {(a.layer, a.kind) for a in store.all()}
    assert (preview.LAYER_THUMBNAIL, "sidecar") in kinds
    assert (preview.LAYER_DETAIL, "sidecar") in kinds


def test_이름이_이미_ULID_면_그_값이_그대로_source_다(client, put_target, tiny_geotiff):
    """실배포 배치 — 본체 키가 `{uploadsPrefix}/{targetId}/{fileId}` 라 이름이 곧 fileId 다."""
    fid = _FID_A
    tid = put_target(files={fid: tiny_geotiff.read_bytes()})
    job = _render(client, {"datasetId": tid})
    assert job["status"] == "완료", job.get("failure")
    store = client.app.state.jobs.get(job["renderId"]).artifacts
    doc = json.loads(store.detail_sidecar.path.read_text(encoding="utf-8"))
    assert doc["source"] == fid
    assert doc["baked_for"] == {"target_id": tid, "is_upload": False}
