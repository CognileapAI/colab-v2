"""`attachUploadGridFiles` — 격자 후주입의 집행 경로.

**설계 = 기존 업로드 흐름 재사용** (Ted 2026-08-25 판정 · 사용자 관점 우선).
사람에게 「격자를 나중에 붙이는 행위」는 **파일 업로드**이므로 새 개념을 만들지 않는다:
`createUpload` 로 격자를 접수하고, 워커가 축을 확정해 `d5_upload_file` 행을 세우고,
사람이 「이 데이터셋에 반영」을 누르면 이 op 이 `uploadId` + `datasetId` 를 한 요청에서 받는다.

**짝(dataset ↔ upload)은 DB 에 없다** — 화면이 들고 있다가 요청에 동봉한다.
`d5_upload` 는 `datasetId` 를 의도적으로 안 가진다(불변규칙 1 · `schema.sql:496-498`).

⚠ **워커 자리를 시험이 대신한다.** core-api 시험에는 pipeline-worker 가 없으므로
축이 확정된 `d5_upload_file` 행을 시험이 직접 세운다 — 그것이 워커가 하는 일
(`colab_pipeline.domains.d5_ingestion._resolve_grid_axes` → `record_file_axes_row`)이다.
**축을 지어내는 것이 아니다** — 판별의 결과가 원장에 있는 상태를 재현하는 것이다.
"""
from __future__ import annotations

from conftest import ACC_A_RES, DS_A1, DS_A2, DS_B1, LAB_A, TOKEN_B, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX
from colab_core.domains.d8_insight import ACTION_GRID_CHANGED

GRID = "기준 격자 파일"
BODY = "본체"

#: 시드의 `a1-grid.nc` — DSA1 의 **결합축**(위도·경도 둘 다) 격자다 (seed.sql:70).
#: 그래서 DSA1 은 `〈58〉` 상한이 이미 찬 데이터셋이고, DSA2 는 비어 있다.
A1_GRID_FILE = "00000000000000000000000FA2"


def _hdf() -> bytes:
    return b"\x89HDF\r\n\x1a\n"


def _upload(client, *, names: list[str], kinds: list[str], token: str = TOKEN_RES) -> str:
    files = [("files", (n, _hdf(), "application/octet-stream")) for n in names]
    r = client.post(f"{API_PREFIX}/uploads", files=files, data={"fileKinds": kinds},
                    headers=auth(token))
    assert r.status_code == 201, r.text
    return r.json()["uploadId"]


def _fresh_dataset(client, *, name: str = "후주입 대상") -> str:
    """본체 하나로 데이터셋을 하나 만든다 — **격자 0건이 정상 상태다** (`P2.md §2-21`).

    시드의 DSA1 은 이미 결합축 격자가 있고(상한이 찼다), DSA2 는 **잠김**이라 본체 쪽
    RLS(`body_access`·`P-13`)가 파일 삽입을 막는다. 그래서 성공 경로는 새로 만든
    데이터셋에서 확인한다 — 그것이 실제 사용자 경로이기도 하다.
    """
    upload_id = _upload(client, names=["body.nc"], kinds=[BODY])
    r = client.post(f"{API_PREFIX}/datasets", json={"uploadId": upload_id, "name": name},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    return r.json()["datasetId"]


def _worker_resolved(sql, upload_id: str, *, file_name: str, lat: bool, lon: bool) -> str:
    """**워커가 하는 일** — 축을 확정한 격자 파일 행을 원장에 세운다 (`〈79〉-㈎`)."""
    from colab_core.kernel.ids import Ulid

    file_id = str(Ulid.generate())
    sql("INSERT INTO d5_upload_file"
        " (id, lab_id, upload_id, kind, file_name, byte_size, storage_key,"
        "  carries_lat, carries_lon)"
        " VALUES (:i, :l, :u, :k, :n, :b, :s, :lat, :lon)",
        {"i": file_id, "l": LAB_A, "u": upload_id, "k": GRID, "n": file_name,
         "b": 8, "s": f"uploads/{upload_id}/{file_id}", "lat": lat, "lon": lon})
    return file_id


def _grid_rows(sql, dataset_id: str):
    return sql("SELECT id, file_name, carries_lat, carries_lon FROM d3_file"
               "  WHERE dataset_id = :d AND kind = :k ORDER BY file_name",
               {"d": dataset_id, "k": GRID})


def _activities(sql, dataset_id: str):
    return sql("SELECT action FROM d8_activity WHERE target_id = :d AND action = :a",
               {"d": dataset_id, "a": ACTION_GRID_CHANGED})


# ═══════════════ 접수 — 격자만 든 묶음이 통과해야 흐름이 성립한다 ══════════════
def test_a_grid_only_upload_is_accepted(p2_client) -> None:
    """**격자만 든 업로드가 접수된다.**

    「본체 1건 이상」은 **데이터셋의 성질**(`DataModel §4.3`)이지 업로드의 성질이 아니다 —
    접수는 D3 에 아무것도 만들지 않는다(`〈64〉-ⓐ`). 그 불변식은 등록 전환이 지킨다
    (아래 `test_registering_a_grid_only_upload_is_400`).
    """
    client = p2_client()
    r = client.post(f"{API_PREFIX}/uploads",
                    files=[("files", ("lat.npy", _hdf(), "application/octet-stream"))],
                    data={"fileKinds": [GRID]}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text


def test_registering_a_grid_only_upload_is_400(p2_client) -> None:
    """등록 전환에는 **본체가 있어야 한다** — 격자만 든 묶음은 데이터가 아니라 좌표다."""
    client = p2_client()
    upload_id = _upload(client, names=["lat.npy"], kinds=[GRID])
    r = client.post(f"{API_PREFIX}/datasets", json={"uploadId": upload_id, "name": "격자만"},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text


# ═════════════════════ 확정 — 위·경도 2건 동시 전송 ═══════════════════════════
def test_two_axes_at_once_become_two_d3_rows(p2_client, sql) -> None:
    """**위·경도를 한 번에 올린다** — `createUpload` 의 `files[]`+`fileKinds[]` 로 성립한다.

    확정 뒤에 `d3_file` 행이 **두 건** 서고, 축 배정이 원장의 판별 그대로 옮겨진다.
    """
    client = p2_client()
    dataset_id = _fresh_dataset(client)
    assert _grid_rows(sql, dataset_id) == [], "전제 확인 — 격자 0건으로 등록됐다 (`§E.1` 기본 경로)."
    upload_id = _upload(client, names=["lat.npy", "lon.npy"], kinds=[GRID, GRID])
    _worker_resolved(sql, upload_id, file_name="lat.npy", lat=True, lon=False)
    _worker_resolved(sql, upload_id, file_name="lon.npy", lat=False, lon=True)

    before = len(_activities(sql, dataset_id))
    r = client.post(f"{API_PREFIX}/datasets/{dataset_id}/grid-files",
                    json={"uploadId": upload_id}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    items = r.json()["items"]
    assert len(items) == 2
    assert {i["fileName"] for i in items} == {"lat.npy", "lon.npy"}
    assert all(i["kind"] == GRID for i in items)

    rows = _grid_rows(sql, dataset_id)
    assert len(rows) == 2, "확정했는데 원장 행이 안 섰다."
    assert {(r_["file_name"], r_["carries_lat"], r_["carries_lon"]) for r_ in rows} == {
        ("lat.npy", True, False), ("lon.npy", False, True)}
    assert len(_activities(sql, dataset_id)) == before + 1, "`〈60〉-③` — 활동 한 행이다."


def test_the_attached_files_appear_in_list_dataset_files(p2_client, sql) -> None:
    """**공개 조회에 나타난다** — 축이 정해진 뒤 목록에 선다는 계약 그대로다."""
    client = p2_client()
    dataset_id = _fresh_dataset(client)
    upload_id = _upload(client, names=["lat.npy"], kinds=[GRID])
    _worker_resolved(sql, upload_id, file_name="lat.npy", lat=True, lon=False)
    assert client.post(f"{API_PREFIX}/datasets/{dataset_id}/grid-files",
                       json={"uploadId": upload_id},
                       headers=auth(TOKEN_RES)).status_code == 201
    listed = client.get(f"{API_PREFIX}/datasets/{dataset_id}/files", headers=auth(TOKEN_RES))
    assert listed.status_code == 200, listed.text
    grids = [f for f in listed.json()["items"] if f["kind"] == GRID]
    assert len(grids) == 1
    assert grids[0]["gridAxis"] == {"carriesLat": True, "carriesLon": False}
    detail = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert detail.json()["basicInfo"]["files"]["hasReferenceGridFile"] is True, \
        "`〈75〉` — 격자는 지도형의 전제인데 상세가 없다고 말한다."


def test_one_axis_only_is_accepted(p2_client, sql) -> None:
    """**1건만 전송해도 된다** — `〈58〉` 상한은 0~2 건이고 1 건은 그 안이다."""
    client = p2_client()
    dataset_id = _fresh_dataset(client)
    upload_id = _upload(client, names=["lat.npy"], kinds=[GRID])
    _worker_resolved(sql, upload_id, file_name="lat.npy", lat=True, lon=False)
    r = client.post(f"{API_PREFIX}/datasets/{dataset_id}/grid-files",
                    json={"uploadId": upload_id}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    assert len(r.json()["items"]) == 1
    assert len(_grid_rows(sql, dataset_id)) == 1


def test_a_dataset_file_response_carries_the_resolved_axis(p2_client, sql) -> None:
    """응답의 `gridAxis` 는 **판별의 결과**다 — 지어낸 값이 아니다."""
    client = p2_client()
    dataset_id = _fresh_dataset(client)
    upload_id = _upload(client, names=["lon.npy"], kinds=[GRID])
    _worker_resolved(sql, upload_id, file_name="lon.npy", lat=False, lon=True)
    r = client.post(f"{API_PREFIX}/datasets/{dataset_id}/grid-files",
                    json={"uploadId": upload_id}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    assert r.json()["items"][0]["gridAxis"] == {"carriesLat": False, "carriesLon": True}


def test_attaching_the_second_axis_later_is_accepted(p2_client, sql) -> None:
    """**순차 후주입** — 위도를 먼저 붙이고 경도를 나중에 붙인다. 둘 다 남는다 (`〈58〉` 2건)."""
    client = p2_client()
    dataset_id = _fresh_dataset(client)
    first = _upload(client, names=["lat.npy"], kinds=[GRID])
    _worker_resolved(sql, first, file_name="lat.npy", lat=True, lon=False)
    assert client.post(f"{API_PREFIX}/datasets/{dataset_id}/grid-files",
                       json={"uploadId": first}, headers=auth(TOKEN_RES)).status_code == 201
    second = _upload(client, names=["lon.npy"], kinds=[GRID])
    _worker_resolved(sql, second, file_name="lon.npy", lat=False, lon=True)
    r = client.post(f"{API_PREFIX}/datasets/{dataset_id}/grid-files",
                    json={"uploadId": second}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    assert len(_grid_rows(sql, dataset_id)) == 2


# ═══════════════════════ `〈58〉` 상한 초과 ════════════════════════════════════
def test_exceeding_the_axis_cap_is_409(p2_client, sql) -> None:
    """DSA1 에는 **결합축 격자**가 이미 있다 (seed.sql:70) — 축이 남지 않았다."""
    client = p2_client()
    upload_id = _upload(client, names=["lat.npy"], kinds=[GRID])
    _worker_resolved(sql, upload_id, file_name="lat.npy", lat=True, lon=False)
    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/grid-files",
                    json={"uploadId": upload_id}, headers=auth(TOKEN_RES))
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "CONFLICT"
    assert len(_grid_rows(sql, DS_A1)) == 1, "거절했는데 행이 늘었다."


def test_one_upload_cannot_hold_two_of_the_same_axis(sql, p2_client) -> None:
    """**한 업로드 안의 축 중복은 원장이 이미 막는다** — 이 op 이 다시 세지 않는 이유다.

    `d5_upload_file_one_lat_grid_per_upload`(`schema.sql:534-537`)가 축별 부분 유니크다.
    그래서 「한 요청 안에서 같은 축 2건」은 이 op 에 도달할 수 없는 상태다 —
    도달할 수 없는 것을 위한 분기를 만들지 않는다.
    """
    import pytest
    client = p2_client()
    upload_id = _upload(client, names=["lat.npy", "lat2.npy"], kinds=[GRID, GRID])
    _worker_resolved(sql, upload_id, file_name="lat.npy", lat=True, lon=False)
    with pytest.raises(Exception):
        _worker_resolved(sql, upload_id, file_name="lat2.npy", lat=True, lon=False)


# ══════════════════ 형상 불일치 · 판별 실패 — 원장에 행이 없다 ════════════════
def test_a_rejected_grid_leaves_nothing_to_attach_and_is_400(p2_client, sql) -> None:
    """형상 불일치·짝 불일치·축 판별 실패는 **`d5_upload_file` 행을 만들지 않는다**(`〈66〉`).

    그래서 확정할 것이 없고, 이 op 은 400 이다. 사유는 `getUploadStatus.gridRejections` 가
    말한다 — 이 op 이 그 어휘를 다시 만들지 않는다.
    """
    client = p2_client()
    upload_id = _upload(client, names=["a.npy", "b.npy"], kinds=[GRID, GRID])
    assert sql("SELECT id FROM d5_upload_file WHERE upload_id = :u", {"u": upload_id}) == [], \
        "전제 확인 — 접수는 격자 행을 만들지 않는다."
    r = client.post(f"{API_PREFIX}/datasets/{DS_A2}/grid-files",
                    json={"uploadId": upload_id}, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text
    assert len(_grid_rows(sql, DS_A2)) == 0


def test_an_upload_carrying_a_body_file_is_400(p2_client, sql) -> None:
    """본체가 든 묶음은 **등록 전환의 대상**이지 후주입의 대상이 아니다 (`〈59〉-③`)."""
    client = p2_client()
    upload_id = _upload(client, names=["body.nc", "lat.npy"], kinds=[BODY, GRID])
    _worker_resolved(sql, upload_id, file_name="lat.npy", lat=True, lon=False)
    r = client.post(f"{API_PREFIX}/datasets/{DS_A2}/grid-files",
                    json={"uploadId": upload_id}, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text
    assert len(_grid_rows(sql, DS_A2)) == 0


# ═══════════════════════════ 두 번 확정 ═══════════════════════════════════════
def test_the_same_upload_cannot_be_attached_twice(p2_client, sql) -> None:
    """업로드 하나 = 소비 한 번. 등록 전환과 **같은 도장**을 쓴다 (`mark_registered`)."""
    client = p2_client()
    dataset_id = _fresh_dataset(client)
    upload_id = _upload(client, names=["lat.npy"], kinds=[GRID])
    _worker_resolved(sql, upload_id, file_name="lat.npy", lat=True, lon=False)
    first = client.post(f"{API_PREFIX}/datasets/{dataset_id}/grid-files",
                        json={"uploadId": upload_id}, headers=auth(TOKEN_RES))
    assert first.status_code == 201, first.text
    second = client.post(f"{API_PREFIX}/datasets/{dataset_id}/grid-files",
                         json={"uploadId": upload_id}, headers=auth(TOKEN_RES))
    assert second.status_code == 409, second.text


def test_an_attached_upload_cannot_be_registered(p2_client, sql) -> None:
    """반영된 업로드로 데이터셋을 만들지 않는다 — 같은 도장이 두 경로를 함께 막는다."""
    client = p2_client()
    dataset_id = _fresh_dataset(client)
    upload_id = _upload(client, names=["lat.npy"], kinds=[GRID])
    _worker_resolved(sql, upload_id, file_name="lat.npy", lat=True, lon=False)
    assert client.post(f"{API_PREFIX}/datasets/{dataset_id}/grid-files",
                       json={"uploadId": upload_id},
                       headers=auth(TOKEN_RES)).status_code == 201
    r = client.post(f"{API_PREFIX}/datasets", json={"uploadId": upload_id, "name": "x"},
                    headers=auth(TOKEN_RES))
    assert r.status_code in (400, 409), r.text


# ═══════════════════════════ 권한 · 경계 ══════════════════════════════════════
def test_without_the_upload_edit_switch_it_is_403(p2_client, sql) -> None:
    """판정은 언제나 `업로드·편집` 스위치가 한다 (`〈59〉-②` · `P-6`)."""
    client = p2_client()
    upload_id = _upload(client, names=["lat.npy"], kinds=[GRID])
    _worker_resolved(sql, upload_id, file_name="lat.npy", lat=True, lon=False)
    sql("UPDATE d2_permission_switch SET enabled = false"
        "  WHERE account_id = :a AND switch = '업로드·편집'", {"a": ACC_A_RES})
    r = client.post(f"{API_PREFIX}/datasets/{DS_A2}/grid-files",
                    json={"uploadId": upload_id}, headers=auth(TOKEN_RES))
    assert r.status_code == 403, r.text
    assert len(_grid_rows(sql, DS_A2)) == 0


def test_a_dataset_outside_the_lab_is_404(p2_client, sql) -> None:
    """연구실 경계 밖은 **404** — 있다는 사실도 말하지 않는다."""
    client = p2_client()
    upload_id = _upload(client, names=["lat.npy"], kinds=[GRID])
    _worker_resolved(sql, upload_id, file_name="lat.npy", lat=True, lon=False)
    r = client.post(f"{API_PREFIX}/datasets/{DS_B1}/grid-files",
                    json={"uploadId": upload_id}, headers=auth(TOKEN_RES))
    assert r.status_code == 404, r.text


def test_an_upload_from_another_lab_is_404(p2_client, sql) -> None:
    """다른 연구실의 업로드는 스코프 커널이 안 보여 준다."""
    client = p2_client()
    upload_id = _upload(client, names=["lat.npy"], kinds=[GRID], token=TOKEN_B)
    r = client.post(f"{API_PREFIX}/datasets/{DS_A2}/grid-files",
                    json={"uploadId": upload_id}, headers=auth(TOKEN_RES))
    assert r.status_code == 404, r.text


# ═══════════════════ 확정 전 업로드 회수 (`〈67〉`) ════════════════════════════
def test_an_expired_upload_is_404_before_attaching(p2_client, sql) -> None:
    """**수명은 일반 업로드와 같다** (`〈67〉-ⓐ` 규칙 ③) — 만료 뒤에는 없는 것으로 답한다.

    후주입 전용 수명을 만들지 않는다. 그래서 고아 행이 생기지 않는다.
    """
    client = p2_client(ttl_hours=24)
    dataset_id = _fresh_dataset(client)
    upload_id = _upload(client, names=["lat.npy"], kinds=[GRID])
    _worker_resolved(sql, upload_id, file_name="lat.npy", lat=True, lon=False)
    # `CHECK (expires_at > created_at)` — 시각 둘을 함께 뒤로 민다.
    sql("UPDATE d5_upload SET created_at = now() - interval '48 hours',"
        "                     expires_at = now() - interval '1 hour' WHERE id = :u",
        {"u": upload_id})
    r = client.post(f"{API_PREFIX}/datasets/{dataset_id}/grid-files",
                    json={"uploadId": upload_id}, headers=auth(TOKEN_RES))
    assert r.status_code == 404, r.text
    assert len(_grid_rows(sql, dataset_id)) == 0


def test_the_pairing_is_not_stored_anywhere(p2_client, sql) -> None:
    """**짝을 DB 에 보관하지 않는다** — `d5_upload` 에 `datasetId` 열이 없어야 한다."""
    cols = sql("SELECT column_name FROM information_schema.columns"
               "  WHERE table_name = 'd5_upload'")
    assert not any("dataset" in c["column_name"] for c in cols), \
        "원장이 D3 를 가리키게 됐다 — 불변규칙 1 위반이다."


# ═══════════════════════════ 요청 형태 ═══════════════════════════════════════
def test_an_unknown_field_is_400(p2_client) -> None:
    """계약이 `additionalProperties: false` 다."""
    r = p2_client().post(f"{API_PREFIX}/datasets/{DS_A2}/grid-files",
                         json={"uploadId": "0" * 26, "datasetId": DS_A2},
                         headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text


def test_a_non_canonical_upload_id_is_400(p2_client) -> None:
    r = p2_client().post(f"{API_PREFIX}/datasets/{DS_A2}/grid-files",
                         json={"uploadId": "not-a-ulid"}, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text


# ═══════ `addDatasetFile` 은 격자를 받지 않고 이 op 을 가리킨다 ═══════════════
def test_add_dataset_file_still_refuses_a_grid_and_points_here(p2_client) -> None:
    """격자는 `attachUploadGridFiles` 가 받는다 — `202` 는 계약에서 철회됐다 (`〈151〉`)."""
    r = p2_client().post(f"{API_PREFIX}/datasets/{DS_A2}/files",
                         files={"file": ("g.npy", _hdf(), "application/octet-stream")},
                         data={"kind": GRID}, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text
    assert "grid-files" in r.json()["message"], "거절하면서 갈 곳을 말하지 않았다."
