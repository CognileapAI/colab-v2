"""⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 7⟩ — 등록 전 세계가 격자 판정을 말한다.

**무엇이 닫히는가** (스윕 `B-2`)

`S1-PLAN-REFOUND §E.2` 의 ③격자 확인 중 · ⑤위치 확인 · ⑥⑦⑧거절 3종은 전부 「워커가 이
격자를 어떻게 판정했는가」를 알아야 서는데, **그 사실이 seam 을 건너오지 않았다.**
화면이 그 상태들을 만드는 유일한 근거가 **viz-render 의 렌더 실패 문장**이었다 —
즉 판정자(pipeline-worker)와 화면이 인용하는 근거(viz-render)가 **다른 기계**였다.

그리고 조용한 사라짐 — 축을 못 정한 격자는 `d5_upload_file` 행이 아예 만들어지지 않는다
(`0004` CHECK · `〈63〉-ⓒ`). 그래서 접수 201 에 있던 격자 파일이 조회 200 에서 **말없이
사라진다.** `gridRejections` 가 그 자리를 말한다.
"""
from __future__ import annotations

import json

from conftest import TOKEN_RES, auth

from colab_core.app.main import API_PREFIX

HDF5_MAGIC = b"\x89HDF\r\n\x1a\n" + b"\x00" * 32


def _upload(client, *, files, kinds=None):
    data = {} if kinds is None else {"fileKinds": kinds}
    return client.post(f"{API_PREFIX}/uploads", files=files, data=data,
                       headers=auth(TOKEN_RES))


def _status(client, upload_id):
    r = client.get(f"{API_PREFIX}/uploads/{upload_id}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    return r.json()


def test_격자_거절_목록은_기본이_빈_배열이다(p2_client) -> None:
    """`null` 로 「모른다」를 말하지 않는다 — 그 뜻은 `ready: false` 가 이미 말한다."""
    client = p2_client()
    upload_id = _upload(client, files=[
        ("files", ("a.nc", HDF5_MAGIC, "application/octet-stream"))]).json()["uploadId"]
    assert _status(client, upload_id)["gridRejections"] == []


def test_축이_확정된_격자_파일은_그_배정을_말한다(p2_client, sql) -> None:
    """**화면이 뒤집기 버튼을 그리려면 지금 배정이 무엇인지 알아야 한다.**
    등록 뒤의 `DatasetFile.gridAxis` 와 같은 모양을 쓴다 — 새 스키마를 만들지 않는다.
    """
    client = p2_client()
    body = _upload(client, files=[
        ("files", ("a.nc", HDF5_MAGIC, "application/octet-stream")),
        ("files", ("lat.npy", b"\x93NUMPY" + b"\x00" * 32, "application/octet-stream")),
    ], kinds=["본체", "기준 격자 파일"]).json()
    upload_id = body["uploadId"]
    grid_id = next(f["fileId"] for f in body["files"] if f["kind"] == "기준 격자 파일")

    # 워커가 축을 확정하고 행을 세운 상태를 만든다 (`〈79〉-㈎ⓒ` — 행은 워커가 만든다)
    sql("""INSERT INTO d5_upload_file
             (id, lab_id, upload_id, kind, file_name, byte_size, storage_key,
              carries_lat, carries_lon)
           VALUES (:id, current_lab_id(), :u, '기준 격자 파일', 'lat.npy', 8, 'k/lat',
                   true, false)""", {"id": grid_id, "u": upload_id})

    files = {f["fileName"]: f for f in _status(client, upload_id)["files"]}
    assert files["lat.npy"]["gridAxis"] == {"carriesLat": True, "carriesLon": False}
    # 본체에는 없다 — 축이 붙은 본체는 `0004` 의 CHECK 가 애초에 만들지 않는다
    assert "gridAxis" not in files["a.nc"]


def test_거절된_격자는_사라지지_않고_사유로_남는다(p2_client, sql) -> None:
    """행이 없으니 `files` 에는 못 서지만, **왜 없는지**는 말해야 한다."""
    client = p2_client()
    body = _upload(client, files=[
        ("files", ("a.nc", HDF5_MAGIC, "application/octet-stream")),
        ("files", ("g.npy", b"\x93NUMPY" + b"\x00" * 32, "application/octet-stream")),
    ], kinds=["본체", "기준 격자 파일"]).json()
    upload_id = body["uploadId"]
    grid_id = next(f["fileId"] for f in body["files"] if f["kind"] == "기준 격자 파일")

    # 워커의 ⑥ `upload.ready` — 축을 못 정해 거절했다
    payload = {"renderable": True, "metadataComplete": False,
               "gridResolution": [{"fileId": grid_id, "fileName": "g.npy",
                                   "rejectionReason": "짝 불일치",
                                   "shapes": {"gridShape": [4, 4]}}]}
    sql("""INSERT INTO d5_pipeline_event
             (id, lab_id, actor_account_id, upload_id, event_type, schema_version,
              source, idempotency_key, payload)
           SELECT CAST(:id AS char(26)), current_lab_id(), u.uploader_account_id,
                  u.id, 'upload.ready', '1.0',
                  'pipeline-worker', CAST(:k AS text), CAST(:p AS jsonb)
             FROM d5_upload u WHERE u.id = CAST(:u AS char(26))""",
        {"id": "01JQ0000000000000000000RDY", "u": upload_id,
         "k": f"upload.ready:{upload_id}", "p": json.dumps(payload, ensure_ascii=False)})

    status = _status(client, upload_id)
    assert [f["fileName"] for f in status["files"]] == ["a.nc"], \
        "행이 없는 격자는 files 에 못 선다 — 그것이 이 항의 전제다"
    assert status["gridRejections"] == [
        {"fileName": "g.npy", "reason": "짝 불일치", "shapes": {"gridShape": [4, 4]}}], \
        "사라진 파일의 사유가 seam 을 건너와야 한다 — 아니면 화면이 렌더 문장을 인용한다"


def test_사유는_계약의_세_값_밖을_중계하지_않는다(p2_client, sql) -> None:
    """core-api 는 **판정하지 않지만 값 집합 밖은 중계하지 않는다.**
    워커가 어휘를 늘리면 화면이 모르는 값을 받는다 — 조용히 지나가지 않게 막는다.
    """
    client = p2_client()
    body = _upload(client, files=[
        ("files", ("a.nc", HDF5_MAGIC, "application/octet-stream")),
        ("files", ("g.npy", b"\x93NUMPY" + b"\x00" * 32, "application/octet-stream")),
    ], kinds=["본체", "기준 격자 파일"]).json()
    upload_id = body["uploadId"]
    grid_id = next(f["fileId"] for f in body["files"] if f["kind"] == "기준 격자 파일")
    payload = {"renderable": True, "metadataComplete": False,
               "gridResolution": [{"fileId": grid_id, "fileName": "g.npy",
                                   "rejectionReason": "네 번째 사유"}]}
    sql("""INSERT INTO d5_pipeline_event
             (id, lab_id, actor_account_id, upload_id, event_type, schema_version,
              source, idempotency_key, payload)
           SELECT CAST(:id AS char(26)), current_lab_id(), u.uploader_account_id,
                  u.id, 'upload.ready', '1.0',
                  'pipeline-worker', CAST(:k AS text), CAST(:p AS jsonb)
             FROM d5_upload u WHERE u.id = CAST(:u AS char(26))""",
        {"id": "01JQ0000000000000000000RD2", "u": upload_id,
         "k": f"upload.ready:{upload_id}", "p": json.dumps(payload, ensure_ascii=False)})

    assert _status(client, upload_id)["gridRejections"] == []
