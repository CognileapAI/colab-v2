"""J-1~J-5 — 격자 재사용·기본값·불일치·예상 영역·지도 상태.

시험은 지리값을 계산하지 않는다. pipeline-worker가 이미 읽어 원장에 남긴 프로필을
재현하고 core-api가 그 사실만 경계 안에서 조립하는지 확인한다.
"""
from __future__ import annotations

from conftest import DS_B1, LAB_A, TOKEN_B, TOKEN_PROF, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX
from colab_core.kernel.ids import Ulid
from colab_core.kernel import storage_layout

BODY = "본체"
GRID = "기준 격자 파일"


def _upload(client, *, with_grid: bool = False, token: str = TOKEN_RES) -> tuple[str, list[dict]]:
    names = ["body.npy"] + (["grid.nc"] if with_grid else [])
    kinds = [BODY] + ([GRID] if with_grid else [])
    response = client.post(
        f"{API_PREFIX}/uploads",
        files=[("files", (name, b"grid-source-bytes" if kind == GRID else b"body", "application/octet-stream"))
               for name, kind in zip(names, kinds)],
        data={"fileKinds": kinds},
        headers=auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()["uploadId"], response.json()["files"]


def _profile_upload(sql, upload_id: str, *, body_shape=(2, 2), grid_shape=None,
                    digest: str | None = None, signature: str | None = None,
                    map_state: str = "지도 없음", source: str = "직접 업로드",
                    bounds: tuple[float, float, float, float] | None = None) -> None:
    sql(
        """INSERT INTO d5_upload_grid_profile
             (upload_id, lab_id, body_shape, grid_shape, grid_digest, grid_format_signature,
              west, south, east, north, map_state, grid_source)
           VALUES (:u, :l, :body, :grid, :digest, :signature,
                   :west, :south, :east, :north, :state, :source)
           ON CONFLICT (upload_id) DO UPDATE SET
             body_shape=EXCLUDED.body_shape, grid_shape=EXCLUDED.grid_shape,
             grid_digest=EXCLUDED.grid_digest, grid_format_signature=EXCLUDED.grid_format_signature,
             west=EXCLUDED.west, south=EXCLUDED.south, east=EXCLUDED.east, north=EXCLUDED.north,
             map_state=EXCLUDED.map_state, grid_source=EXCLUDED.grid_source""",
        {"u": upload_id, "l": LAB_A, "body": list(body_shape) if body_shape else None,
         "grid": list(grid_shape) if grid_shape else None, "digest": digest,
         "signature": signature, "state": map_state, "source": source,
         "west": bounds[0] if bounds else None, "south": bounds[1] if bounds else None,
         "east": bounds[2] if bounds else None, "north": bounds[3] if bounds else None},
    )


def _ready(sql, upload_id: str) -> None:
    sql("UPDATE d5_upload SET ready=true, renderable=true, metadata_complete=true WHERE id=:u",
        {"u": upload_id})


def _register(client, upload_id: str, *, name: str, token: str = TOKEN_RES) -> str:
    response = client.post(
        f"{API_PREFIX}/datasets",
        json={"uploadId": upload_id, "name": name, "summary": "격자 편의 시험 설명",
              "category": "기상·기후 인자", "dataType": "재분석자료"},
        headers=auth(token),
    )
    assert response.status_code == 201, response.text
    return response.json()["datasetId"]


def _source_dataset(client, sql, *, name: str = "같은 형상 격자") -> tuple[str, bytes]:
    upload_id, files = _upload(client, with_grid=True)
    grid_ref = next(item for item in files if item["kind"] == GRID)
    # 워커가 축을 판별해 세우는 D5 행을 재현한다. 바이트는 createUpload가 이미 저장했다.
    sql(
        """INSERT INTO d5_upload_file
             (id, lab_id, upload_id, kind, file_name, byte_size, storage_key, carries_lat, carries_lon)
           VALUES (:id, :lab, :upload, :kind, :name, :size, :key, true, true)""",
        {"id": grid_ref["fileId"], "lab": LAB_A, "upload": upload_id, "kind": GRID,
         "name": grid_ref["fileName"], "size": len(b"grid-source-bytes"),
         "key": storage_layout.storage_key(upload_id, file_id=grid_ref["fileId"],
                                             kind=GRID, file_name=grid_ref["fileName"])},
    )
    _profile_upload(
        sql, upload_id, grid_shape=(2, 2), digest="a" * 64, signature="HDF5",
        map_state="지도 있음", bounds=(121.9, 31.1, 133.6, 43.3),
    )
    _ready(sql, upload_id)
    return _register(client, upload_id, name=name), b"grid-source-bytes"


def _target_upload(client, sql, *, shape=(2, 2)) -> str:
    upload_id, _ = _upload(client)
    _profile_upload(sql, upload_id, body_shape=shape)
    _ready(sql, upload_id)
    return upload_id


def test_candidates_are_same_lab_same_shape_and_default_is_suggestion_only(p2_client, sql) -> None:
    client = p2_client()
    source_id, _ = _source_dataset(client, sql)
    target_id = _target_upload(client, sql)
    set_default = client.put(
        f"{API_PREFIX}/lab/default-grid", json={"datasetId": source_id}, headers=auth(TOKEN_PROF))
    assert set_default.status_code == 200, set_default.text

    before = sql("SELECT count(*) AS n FROM d5_upload_file WHERE upload_id=:u AND kind=:k",
                 {"u": target_id, "k": GRID})[0]["n"]
    response = client.get(f"{API_PREFIX}/uploads/{target_id}/grid-options", headers=auth(TOKEN_RES))
    assert response.status_code == 200, response.text
    assert [(item["datasetId"], item["isDefault"]) for item in response.json()["candidates"]] == [
        (source_id, True)
    ]
    assert response.json()["bodyShape"] == [2, 2]
    assert response.json()["candidates"][0]["expectedBounds"] == {
        "west": 121.9, "south": 31.1, "east": 133.6, "north": 43.3}
    after = sql("SELECT count(*) AS n FROM d5_upload_file WHERE upload_id=:u AND kind=:k",
                {"u": target_id, "k": GRID})[0]["n"]
    assert before == after == 0, "기본 격자는 제시일 뿐 조회만으로 자동 적용되면 안 된다"


def test_shape_mismatch_is_not_a_candidate(p2_client, sql) -> None:
    client = p2_client()
    _source_dataset(client, sql)
    target_id = _target_upload(client, sql, shape=(3, 4))
    response = client.get(f"{API_PREFIX}/uploads/{target_id}/grid-options", headers=auth(TOKEN_RES))
    assert response.status_code == 200
    assert response.json()["candidates"] == []


def test_reuse_copies_exact_bytes_then_registration_records_activity_without_lineage(
    p2_client, sql,
) -> None:
    client = p2_client(session_secret="grid-copy-test-secret")
    source_id, payload = _source_dataset(client, sql)
    target_id = _target_upload(client, sql)
    reused = client.post(
        f"{API_PREFIX}/uploads/{target_id}/grid-reuse",
        json={"sourceDatasetId": source_id}, headers=auth(TOKEN_RES))
    assert reused.status_code == 201, reused.text
    assert reused.json()["gridDigest"] == "a" * 64
    grid_file = next(item for item in reused.json()["files"] if item["kind"] == GRID)

    # local 저장 대역에서 새 키의 바이트를 실제로 내려받아 exact-copy를 증명한다.
    downloaded = client.get(
        f"{API_PREFIX}/uploads/{target_id}", headers=auth(TOKEN_RES))
    assert downloaded.status_code == 200
    _ready(sql, target_id)
    dataset_id = _register(client, target_id, name="격자 가져온 자료")
    ticket = client.get(
        f"{API_PREFIX}/datasets/{dataset_id}/files/{grid_file['fileId']}/download",
        headers=auth(TOKEN_RES),
    )
    assert ticket.status_code == 200, ticket.text
    bytes_response = client.get(ticket.json()["url"], headers=auth(TOKEN_RES))
    assert bytes_response.content == payload

    activity = sql(
        "SELECT count(*) AS n FROM d8_activity WHERE target_id=:d AND action='격자 가져오기'",
        {"d": dataset_id},
    )[0]["n"]
    lineage = sql(
        "SELECT count(*) AS n FROM d4_lineage_edge WHERE child_dataset_id=:d OR parent_dataset_id=:d",
        {"d": dataset_id},
    )[0]["n"]
    assert activity == 1
    assert lineage == 0


def test_cross_lab_manual_source_id_is_404(p2_client, sql) -> None:
    client = p2_client()
    target_id = _target_upload(client, sql)
    response = client.post(
        f"{API_PREFIX}/uploads/{target_id}/grid-reuse",
        json={"sourceDatasetId": DS_B1}, headers=auth(TOKEN_RES))
    assert response.status_code == 404


def test_only_professor_can_set_default_grid(p2_client, sql) -> None:
    client = p2_client()
    source_id, _ = _source_dataset(client, sql)
    denied = client.put(
        f"{API_PREFIX}/lab/default-grid", json={"datasetId": source_id}, headers=auth(TOKEN_RES))
    assert denied.status_code == 403
    allowed = client.put(
        f"{API_PREFIX}/lab/default-grid", json={"datasetId": source_id}, headers=auth(TOKEN_PROF))
    assert allowed.status_code == 200
    assert allowed.json() == {"datasetId": source_id}


def test_mismatch_warning_is_nonblocking_and_distance_is_pair_derived(p2_client, sql) -> None:
    client = p2_client()
    source_id, _ = _source_dataset(client, sql)
    assert client.put(f"{API_PREFIX}/lab/default-grid", json={"datasetId": source_id},
                      headers=auth(TOKEN_PROF)).status_code == 200
    target_id, _ = _upload(client, with_grid=True)
    _profile_upload(
        sql, target_id, grid_shape=(2, 2), digest="b" * 64, signature="NumPy+NumPy",
        map_state="지도 있음", bounds=(122.0, 31.2, 133.7, 43.4),
    )
    _ready(sql, target_id)
    response = client.get(f"{API_PREFIX}/uploads/{target_id}/grid-options", headers=auth(TOKEN_RES))
    assert response.status_code == 200
    warning = response.json()["mismatchWarning"]
    assert warning["formatDiffers"] is True
    assert warning["hashDiffers"] is True
    assert warning["blocksRegistration"] is False
    assert isinstance(warning["distanceMeters"], int) and warning["distanceMeters"] > 0
    assert response.json()["currentGrid"]["expectedBounds"] == {
        "west": 122.0, "south": 31.2, "east": 133.7, "north": 43.4}


def test_missing_geometry_reports_unknown_distance_not_a_fabricated_number(p2_client, sql) -> None:
    client = p2_client()
    source_id, _ = _source_dataset(client, sql)
    assert client.put(f"{API_PREFIX}/lab/default-grid", json={"datasetId": source_id},
                      headers=auth(TOKEN_PROF)).status_code == 200
    target_id, _ = _upload(client, with_grid=True)
    _profile_upload(sql, target_id, grid_shape=(2, 2), digest="b" * 64, signature="HDF5",
                    map_state="아직 모름", bounds=None)
    _ready(sql, target_id)
    body = client.get(f"{API_PREFIX}/uploads/{target_id}/grid-options",
                      headers=auth(TOKEN_RES)).json()
    assert body["mismatchWarning"]["distanceMeters"] is None
    assert "expectedBounds" not in body["currentGrid"]


def test_catalog_badge_state_and_filter_share_the_same_profile_value(p2_client, sql) -> None:
    client = p2_client()
    source_id, _ = _source_dataset(client, sql, name="지도 없는 자료")
    sql("UPDATE d3_dataset_grid_profile SET map_state='지도 없음' WHERE dataset_id=:d",
        {"d": source_id})
    response = client.get(
        f"{API_PREFIX}/datasets", params={"mapState": "지도 없음"}, headers=auth(TOKEN_RES))
    assert response.status_code == 200, response.text
    by_id = {item["datasetId"]: item for item in response.json()["items"]}
    assert by_id[source_id]["mapState"] == "지도 없음"
    assert all(item["mapState"] == "지도 없음" for item in response.json()["items"])

    unknown = client.get(
        f"{API_PREFIX}/datasets", params={"mapState": "아직 모름"}, headers=auth(TOKEN_RES))
    assert unknown.status_code == 200
    assert all(item["mapState"] == "아직 모름" for item in unknown.json()["items"])


def test_other_lab_catalog_rows_never_enter_map_filter_counts(p2_client) -> None:
    client = p2_client()
    a = client.get(f"{API_PREFIX}/datasets", params={"mapState": "아직 모름"},
                   headers=auth(TOKEN_RES)).json()["items"]
    b = client.get(f"{API_PREFIX}/datasets", params={"mapState": "아직 모름"},
                   headers=auth(TOKEN_B)).json()["items"]
    assert DS_B1 not in {item["datasetId"] for item in a}
    assert all(item["datasetId"] == DS_B1 for item in b)
