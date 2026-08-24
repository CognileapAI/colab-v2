"""S-08 — 등록하지 않은 업로드도 대상이다. 그리고 부분 실패는 전부 실패가 아니다."""
from __future__ import annotations

from conftest import AUTH

_STYLE = {"palette": "단색-파랑"}


def _post(client, target):
    return client.post("/viz/v1/renders", json={"target": target, "style": _STYLE},
                       headers=AUTH)


def test_uploadId_대상_렌더가_동작한다(client, put_target, tiny_geotiff):
    """S-04 모달에서 그린 미리보기를 S-08 이 그대로 이어서 보여준다 (정본 §8.1)."""
    tid = put_target(copy_from=[tiny_geotiff])
    r = _post(client, {"uploadId": tid})
    assert r.status_code == 202
    rid = r.json()["renderId"]
    job = client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()
    assert job["status"] == "완료"
    # stage 1 은 **이미지 갈래**를 낸다 (`oneOf` — `〈80〉-㉯ 1`)
    assert job["result"]["imageUrl"]
    # 등록 전 업로드의 미리보기 결과는 임시로만 둔다 — 수명이 있다
    assert job["expiresAt"]


def test_datasetId_대상에는_수명을_붙이지_않는다(client, put_target, tiny_geotiff):
    tid = put_target(copy_from=[tiny_geotiff])
    rid = _post(client, {"datasetId": tid}).json()["renderId"]
    job = client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()
    assert "expiresAt" not in job


def test_조각_일부를_못_읽어도_완료로_남는다(client, put_target, tiny_geotiff, tmp_path):
    """읽힌 조각으로 그린다. 부분 실패와 전부 실패를 같은 자리에 담지 않는다."""
    broken = tmp_path / "broken.tif"
    broken.write_bytes(b"II*\x00" + b"\x00" * 200)     # TIFF 매직만 있고 내용이 깨졌다
    tid = put_target(copy_from=[tiny_geotiff, broken])
    rid = _post(client, {"datasetId": tid}).json()["renderId"]
    job = client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()

    assert job["status"] == "완료"           # 실패로 만들지 않는다
    assert "failure" not in job              # 부분 실패는 여기가 아니다
    pf = job["partialFailure"]
    assert pf["totalParts"] == 2
    assert pf["renderedParts"] == 1
    assert [m["fileName"] for m in pf["missingParts"]] == ["broken.tif"]


def test_전부_못_읽으면_그때는_실패다(client, put_target, tmp_path):
    a = tmp_path / "a.tif"; a.write_bytes(b"II*\x00" + b"\x00" * 200)
    b = tmp_path / "b.tif"; b.write_bytes(b"II*\x00" + b"\x00" * 200)
    tid = put_target(copy_from=[a, b])
    rid = _post(client, {"datasetId": tid}).json()["renderId"]
    job = client.get(f"/viz/v1/renders/{rid}", headers=AUTH).json()
    assert job["status"] == "실패"
    assert job["failure"]["code"]
    assert "partialFailure" not in job


def test_fileIds_로_조각_하나만_골라_그린다(client, put_target, tiny_geotiff, tmp_path, source_root):
    """413 복구 경로 — 「조각 하나를 골라 그린다」."""
    broken = tmp_path / "broken.tif"
    broken.write_bytes(b"II*\x00" + b"\x00" * 200)
    tid = put_target(copy_from=[tiny_geotiff, broken])
    good_id = client.app.state.source.file_id(tid, "tiny.tif")
    r = client.post("/viz/v1/renders", headers=AUTH, json={
        "target": {"datasetId": tid, "fileIds": [good_id]}, "style": _STYLE})
    job = client.get(f"/viz/v1/renders/{r.json()['renderId']}", headers=AUTH).json()
    assert job["status"] == "완료"
    assert "partialFailure" not in job
