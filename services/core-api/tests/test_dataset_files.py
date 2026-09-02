"""`addDatasetFile` · `replaceDatasetGridFile` · `deleteDatasetGridFile` — `〈60〉` 과 `〈278〉-(라)`.

`〈60〉` 이 못 박은 셋을 **격자 경로**에서 실물로 확인한다:
  ① `마지막 수정` 을 **건드리지 않는다** → 파생인 `계보 상태` 가 `확정` → `확인 필요` 로
     **접히지 않는다.** 경보가 잦으면 사람이 경보를 끈다.
  ② `자동으로 읽은 정보`(좌표계·격자)를 **재계산한다.**
  ③ `d8_activity` 에 **`좌표계·격자 변경` 한 행** — 그 문자열 그대로.

`〈278〉-(라)` 가 `〈59〉-③`(본체는 이 경로의 대상이 아니다 — 409)을 **번복**했다. 본체 경로의 규칙은
격자와 **셋 다 반대**다 — 바뀐 것이 좌표를 읽을 수단이 아니라 **과학 데이터 자체**이기 때문이다:
  ① `마지막 수정` 이 **움직인다** → `계보 상태` 가 `확인 필요` 로 접힌다 (`〈278〉` 권고 · Ted 판정 대기).
  ② `crs/grid` 를 **건드리지 않는다** — `recompute_grid_metadata` 는 사람이 적은 `crs` 를 지운다.
  ③ `d8_activity` 에 **`본체 파일 변경` 한 행** (`[정본 무근거]`).
남는 불변식은 하나 — **본체 ≥ 1** (마지막 본체 삭제 409). `flipAxes` 는 여전히 격자 사이의 조작이다.
"""
from __future__ import annotations

import pytest
from conftest import DS_A1, TOKEN_B, TOKEN_RES, auth
from test_dataset_registration import make_upload, register
from test_uploads import HDF5_MAGIC

from colab_core.app.main import API_PREFIX
from colab_core.app.routes.ingestion import ACTION_BODY_CHANGED
from colab_core.domains.d8_insight import ACTION_GRID_CHANGED
from colab_core.kernel import storage_layout

#: 시드의 `a1-grid.nc` — 결합축(둘 다 true) 기준 격자 파일이다 (seed.sql:70).
GRID_FILE = "00000000000000000000000FA2"
#: 시드의 `a1-body.csv` — 본체다. **DS_A1 의 유일한 본체**라 그대로는 못 지운다.
BODY_FILE = "00000000000000000000000FA1"


@pytest.fixture(autouse=True)
def _restore_seed_columns_the_shared_cleanup_does_not(sql):
    """본체 조작이 시드 데이터셋의 **`last_modified_at`·`representative_file_id`·`relative_path`** 를
    움직인다 — conftest 의 되돌리기(`_RESTORE`)는 그 세 열을 모르므로 여기서 되돌린다.
    값은 `seed.sql` 의 것 그대로다. 안 되돌리면 다음 시험의 「전제 확인」이 오라클이 아니게 된다."""
    yield
    sql("UPDATE d3_dataset SET last_modified_at = '2026-01-02T00:00:00Z',"
        " representative_file_id = NULL WHERE id = :d", {"d": DS_A1})
    sql("UPDATE d3_file SET relative_path = NULL WHERE id = :f", {"f": BODY_FILE})


def _activities(sql, dataset_id, action=ACTION_GRID_CHANGED):
    return sql("SELECT action, actor_account_id FROM d8_activity"
               "  WHERE target_id = :d AND action = :a",
               {"d": dataset_id, "a": action})


def _dataset_times(sql, dataset_id):
    return sql("SELECT last_modified_at, lineage_confirmed_at FROM d3_dataset WHERE id = :d",
               {"d": dataset_id})[0]


def _total_size(sql, dataset_id) -> int:
    return sql("SELECT total_size_bytes FROM d3_dataset_autometa WHERE dataset_id = :d",
               {"d": dataset_id})[0]["total_size_bytes"]


def _autometa(sql, dataset_id):
    return sql("SELECT crs, grid, bundle_file_name FROM d3_dataset_autometa WHERE dataset_id = :d",
               {"d": dataset_id})[0]


def _add_body(client, name="extra.csv", payload=b"a,b\n1,2\n") -> dict:
    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/files",
                    files={"file": (name, payload, "text/csv")},
                    data={"kind": "본체"}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    return r.json()


def _body_path(tmp_path, dataset_id, file_id):
    """본체 바이트가 놓이는 자리 — 키 규약(`layout.json`)은 본체 키에 이름을 넣지 않는다.
    `p2_client` 가 `tmp_path / "uploads"` 를 저장 루트로 준다 (conftest)."""
    key = storage_layout.storage_key(dataset_id, file_id=file_id, kind="본체", file_name=None)
    return tmp_path / "uploads" / key


# ═════════════════════════ 교체 (`replaceDatasetGridFile`) ══════════════════
def test_replacing_a_grid_file_records_one_activity_row(p2_client, sql) -> None:
    """`〈60〉-③` — **한 행**이다. 0 이면 흔적이 사라지고, 여럿이면 이력이 소음이 된다."""
    client = p2_client()
    before = len(_activities(sql, DS_A1))
    r = client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{GRID_FILE}",
                   files={"file": ("new-grid.nc", b"\x89HDF\r\n\x1a\n", "application/octet-stream")},
                   headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert r.json()["fileId"] == GRID_FILE, "교체가 fileId 를 갈아 끼웠다 — 이력이 다른 것을 가리키게 된다."
    assert r.json()["fileName"] == "new-grid.nc"

    rows = _activities(sql, DS_A1)
    assert len(rows) == before + 1
    assert rows[-1]["action"] == "좌표계·격자 변경"


def test_replacing_a_grid_file_does_not_fold_the_lineage_state(p2_client, sql) -> None:
    """`〈60〉-①` — **`마지막 수정` 을 건드리지 않는다.**

    바뀐 것은 과학 데이터가 아니라 **좌표를 읽을 수단**이다. 파생 관계는 그대로인데 「확정」이
    접히면 사람이 확인하러 갔다가 아무것도 안 바뀐 걸 본다. 그게 반복되면 그 상태값을 안 믿게 된다.
    """
    client = p2_client()
    # DSA2 는 부모(DSA1)가 있고 확정일이 `마지막 수정` 보다 뒤다 → `확정` 이다 (seed.sql:43).
    from conftest import DS_A2
    grid = client.post(f"{API_PREFIX}/uploads", files=[
        ("files", ("x.nc", b"\x89HDF\r\n\x1a\n", "application/octet-stream"))],
        headers=auth(TOKEN_RES))
    assert grid.status_code == 201

    state_before = client.get(f"{API_PREFIX}/datasets/{DS_A2}",
                              headers=auth(TOKEN_RES)).json()["lineageState"]
    assert state_before == "확정", "전제 확인 — 시드의 DSA2 는 `확정` 이어야 한다."
    times_before = _dataset_times(sql, DS_A2)

    # DSA2 에는 격자 파일이 없으므로 DSA1 의 격자를 교체해 같은 규칙을 확인한다.
    times_a1_before = _dataset_times(sql, DS_A1)
    client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{GRID_FILE}",
               files={"file": ("g2.nc", b"\x89HDF\r\n\x1a\n", "application/octet-stream")},
               headers=auth(TOKEN_RES))
    assert _dataset_times(sql, DS_A1)["last_modified_at"] == times_a1_before["last_modified_at"], \
        "격자 교체가 `마지막 수정` 을 밀었다 — 계보 상태가 접힌다."
    assert _dataset_times(sql, DS_A2) == times_before


def test_replacing_a_grid_file_recomputes_the_auto_read_metadata(p2_client, sql) -> None:
    """`〈60〉-②` — 좌표계·격자는 **그 파일에서 나오는 값**이라 재계산한다.

    core-api 는 파일을 읽지 못하므로(`CLAUDE.md §3-4`) 재계산의 결과는 **「모른다」(NULL)** 다.
    낡은 값을 그대로 두면 **지워진 파일에서 읽은 값이 화면에 남는다** — 새 값은 파일을 읽는
    쪽이 채운다. 「모른다」와 「전과 같다」를 같게 두지 않는 것이 이 시험의 요지다.
    """
    client = p2_client()
    sql("UPDATE d3_dataset_autometa SET crs = 'EPSG:5179', grid = '1km' WHERE dataset_id = :d",
        {"d": DS_A1})
    assert sql("SELECT crs FROM d3_dataset_autometa WHERE dataset_id = :d",
               {"d": DS_A1})[0]["crs"] == "EPSG:5179"

    client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{GRID_FILE}",
               files={"file": ("g3.nc", b"\x89HDF\r\n\x1a\n", "application/octet-stream")},
               headers=auth(TOKEN_RES))
    row = sql("SELECT crs, grid FROM d3_dataset_autometa WHERE dataset_id = :d", {"d": DS_A1})[0]
    assert row["crs"] is None and row["grid"] is None, \
        "격자를 갈아 끼웠는데 옛 파일에서 읽은 좌표계가 그대로 남았다."


# ═════════════════════ 본체 교체 (`〈278〉-(라)` — `〈59〉-③` 번복) ═════════════════════
def test_replacing_a_body_file_swaps_the_bytes_in_place(p2_client, sql, tmp_path) -> None:
    """`〈278〉-(라)` — **본체도 갈아 끼운다.** `〈59〉-③` 의 409 는 번복됐다 (계약 산문).

    같은 행·같은 `fileId`·같은 저장 키다 — 본체 키(`{datasetId}/{fileId}`)는 이름을 담지 않아
    **키가 불변**이고, 바이트는 그 자리에 덮어써진다. `relative_path`·`created_at` 은 그대로다.
    """
    client = p2_client()
    sql("UPDATE d3_file SET relative_path = 'sub/a1-body.csv' WHERE id = :f", {"f": BODY_FILE})
    created_before = sql("SELECT created_at FROM d3_file WHERE id = :f", {"f": BODY_FILE})[0]
    payload = b"lon,lat,rain\n127.0,37.5,1.0\n"

    r = client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}",
                   files={"file": ("b.csv", payload, "text/csv")}, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["fileId"] == BODY_FILE and body["kind"] == "본체"
    assert body["fileName"] == "b.csv" and body["byteSize"] == len(payload)
    assert body["relativePath"] == "sub/a1-body.csv", "교체가 폴더 경로를 잃었다."
    assert "gridAxis" not in body

    row = sql("SELECT file_name, size_bytes, storage_key, relative_path, created_at"
              "  FROM d3_file WHERE id = :f", {"f": BODY_FILE})[0]
    expected_key = storage_layout.storage_key(DS_A1, file_id=BODY_FILE, kind="본체")
    assert row["storage_key"] == expected_key
    assert row["size_bytes"] == len(payload) and row["relative_path"] == "sub/a1-body.csv"
    assert row["created_at"] == created_before["created_at"], "교체가 행의 생성 시각을 밀었다."
    assert _body_path(tmp_path, DS_A1, BODY_FILE).read_bytes() == payload, \
        "응답은 200 인데 저장소의 바이트가 새 것이 아니다."


def test_replacing_a_body_file_moves_the_total_size_by_the_difference(p2_client, sql) -> None:
    """`total_size_bytes` 는 **`0009` 트리거가 차분으로 옮긴다** — 앱 코드가 다시 쓰지 않는다.
    시드 DS_A1 = 본체 50 + 격자 50 = 100. 본체를 N 바이트로 갈아 끼우면 50 + N 이다."""
    client = p2_client()
    assert _total_size(sql, DS_A1) == 100, "전제 확인 — 시드 합계."
    payload = b"x" * 17
    r = client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}",
                   files={"file": ("b.csv", payload, "text/csv")}, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert _total_size(sql, DS_A1) == 50 + 17


def test_a_body_change_leaves_the_human_written_crs_alone(p2_client, sql) -> None:
    """`〈278〉-(라)` — 본체 경로는 **`crs/grid` 를 건드리지 않는다.**

    `crs` 는 `updateDataset` 으로 **사람이 적는 값**이다 (`d3_catalog._UPDATABLE`). 격자 경로의
    재계산(`_CLEAR_GRID_META`)은 그 값을 NULL 로 지운다 — 본체를 바꿨다고 사람이 적은 좌표계를
    지우면 「모른다」가 아니라 **「지웠다」**다. 추가·교체·삭제 셋 다 같은 규칙이다.
    """
    client = p2_client()
    r = client.patch(f"{API_PREFIX}/datasets/{DS_A1}", json={"crs": "EPSG:4326"},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    sql("UPDATE d3_dataset_autometa SET grid = '500m' WHERE dataset_id = :d", {"d": DS_A1})

    r = client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}",
                   files={"file": ("b.csv", b"a,b\n", "text/csv")}, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert _autometa(sql, DS_A1)["crs"] == "EPSG:4326", "본체 교체가 사람이 적은 crs 를 지웠다."
    assert _autometa(sql, DS_A1)["grid"] == "500m"

    extra = _add_body(client)
    assert _autometa(sql, DS_A1)["crs"] == "EPSG:4326", "본체 추가가 사람이 적은 crs 를 지웠다."

    r = client.delete(f"{API_PREFIX}/datasets/{DS_A1}/files/{extra['fileId']}",
                      headers=auth(TOKEN_RES))
    assert r.status_code == 204, r.text
    assert _autometa(sql, DS_A1)["crs"] == "EPSG:4326", "본체 삭제가 사람이 적은 crs 를 지웠다."
    assert _autometa(sql, DS_A1)["grid"] == "500m"


def test_a_body_change_records_one_body_activity_row_and_no_grid_row(p2_client, sql) -> None:
    """`d8_activity` 에 **`본체 파일 변경` 한 행** — 격자 문자열이 아니다. 활동 화면에서 「좌표를
    읽을 수단이 바뀐 것」과 「데이터 자체가 바뀐 것」이 갈려 보여야 한다 (`[정본 무근거]`)."""
    client = p2_client()
    grid_before = len(_activities(sql, DS_A1, ACTION_GRID_CHANGED))
    body_before = len(_activities(sql, DS_A1, ACTION_BODY_CHANGED))

    r = client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}",
                   files={"file": ("b.csv", b"a,b\n", "text/csv")}, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    rows = _activities(sql, DS_A1, ACTION_BODY_CHANGED)
    assert len(rows) == body_before + 1
    assert rows[-1]["action"] == "본체 파일 변경"
    assert rows[-1]["actor_account_id"] == "000000000000000000000000A1"
    assert len(_activities(sql, DS_A1, ACTION_GRID_CHANGED)) == grid_before, \
        "본체 교체가 격자 활동 행을 남겼다 — 두 사건이 한 문자열로 접힌다."


def test_a_body_change_moves_last_modified_and_folds_the_lineage_state(p2_client, sql) -> None:
    """`〈278〉` 권고(Ted 판정 대기) — 본체 변경은 **`마지막 수정` 을 민다.**

    `〈60〉-①` 이 격자 변경에는 그 열을 안 건드린 이유는 「바뀐 것이 과학 데이터가 아니라 좌표를
    읽을 수단」이어서였다. 본체는 **과학 데이터 자체**라 파생 관계를 다시 봐야 하고, 그래서
    `계보 상태` 가 `확정` → `확인 필요` 로 접히는 것이 맞다. 격자 경로는 대조로 그대로다.
    """
    client = p2_client()
    receipt = make_upload(client, files=[("files", ("a.nc", HDF5_MAGIC, "application/octet-stream"))])
    r = register(client, receipt,
                 # ⭑ **병합 2026-09-02** — 다른 레인이 계보 출처 레이블을 영어 세 값으로
                 #   통일했다(`ai`·`manual`·`processed`). 여기 있던 「사람이 직접 연결」은
                 #   그 통일 **이전의 값**이라 400 이 났다. 뜻은 그대로 「사람이 걸었다」다.
                 lineageParents=[{"parentDatasetId": DS_A1, "origin": "manual"}])
    assert r.status_code == 201, r.text
    dataset_id = r.json()["datasetId"]
    assert r.json()["lineageState"] == "확정", "전제 확인 — 부모를 확인하고 등록하면 `확정` 이다."
    body_id = receipt["files"][0]["fileId"]
    times_before = _dataset_times(sql, dataset_id)

    r = client.put(f"{API_PREFIX}/datasets/{dataset_id}/files/{body_id}",
                   files={"file": ("a2.nc", HDF5_MAGIC + b"z", "application/octet-stream")},
                   headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    times_after = _dataset_times(sql, dataset_id)
    assert times_after["last_modified_at"] > times_before["last_modified_at"], \
        "본체 교체가 `마지막 수정` 을 안 밀었다 — 계보를 다시 볼 신호가 없다."
    assert times_after["lineage_confirmed_at"] == times_before["lineage_confirmed_at"]
    assert client.get(f"{API_PREFIX}/datasets/{dataset_id}",
                      headers=auth(TOKEN_RES)).json()["lineageState"] == "확인 필요"

    # 대조 — 격자 경로는 `〈60〉-①` 그대로다.
    a1_before = _dataset_times(sql, DS_A1)
    r = client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{GRID_FILE}",
                   files={"file": ("g.nc", b"\x89HDF\r\n\x1a\n", "application/octet-stream")},
                   headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert _dataset_times(sql, DS_A1)["last_modified_at"] == a1_before["last_modified_at"]


def test_flipping_axes_on_a_body_file_is_409(p2_client, sql) -> None:
    """`flipAxes` 는 **격자 사이의 조작**이다 — 본체에는 축이 없다 (계약 409-②).
    본체가 이 op 의 대상이 됐어도 이 409 는 남는다."""
    r = p2_client().put(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}",
                        data={"flipAxes": "true"}, headers=auth(TOKEN_RES))
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "CONFLICT"
    assert "본체" in r.json()["message"]


# ═════════════════════════ 삭제 (`deleteDatasetGridFile`) ═══════════════════
def test_deleting_a_grid_file_is_normal_and_records_one_activity_row(p2_client, sql) -> None:
    """삭제도 **정상 동작**이다 (`〈59〉-①`). 격자를 지우면 그릴 수 없게 될 수 있을 뿐이다 —
    **그릴 수 없는 것과 등록할 수 없는 것은 다르다.**"""
    client = p2_client()
    before = len(_activities(sql, DS_A1))
    times_before = _dataset_times(sql, DS_A1)

    r = client.delete(f"{API_PREFIX}/datasets/{DS_A1}/files/{GRID_FILE}", headers=auth(TOKEN_RES))
    assert r.status_code == 204, r.text
    assert sql("SELECT count(*) AS n FROM d3_file WHERE id = :f", {"f": GRID_FILE})[0]["n"] == 0
    assert len(_activities(sql, DS_A1)) == before + 1
    assert _dataset_times(sql, DS_A1)["last_modified_at"] == times_before["last_modified_at"]
    # 격자가 0건이어도 데이터셋은 그대로 선다 (`P2.md §2-21` — 격자 0건은 정상 상태다).
    detail = client.get(f"{API_PREFIX}/datasets/{DS_A1}", headers=auth(TOKEN_RES))
    assert detail.status_code == 200
    assert detail.json()["basicInfo"]["files"]["hasReferenceGridFile"] is False


def test_deleting_the_last_body_file_is_409(p2_client, sql) -> None:
    """**본체 ≥ 1** — 남는 불변식은 이것 하나다 (`DataModel §4.3` · `〈278〉-(라)`).
    시드 DS_A1 의 본체는 한 건이라 그것이 곧 마지막 본체다. 행·이력·`마지막 수정` 전부 그대로다."""
    before = len(_activities(sql, DS_A1, ACTION_BODY_CHANGED))
    times_before = _dataset_times(sql, DS_A1)
    r = p2_client().delete(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}",
                           headers=auth(TOKEN_RES))
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "CONFLICT"
    assert "마지막 본체" in r.json()["message"]
    assert sql("SELECT count(*) AS n FROM d3_file WHERE id = :f", {"f": BODY_FILE})[0]["n"] == 1
    assert len(_activities(sql, DS_A1, ACTION_BODY_CHANGED)) == before
    assert _dataset_times(sql, DS_A1)["last_modified_at"] == times_before["last_modified_at"]


def test_deleting_a_body_file_is_normal_when_another_body_remains(p2_client, sql, tmp_path) -> None:
    """본체가 둘이면 하나는 지운다 — 204 · 행 삭제 · 바이트 폐기 · 합계 차분 · 이력 한 행 ·
    `마지막 수정` 이동. 그리고 하나가 남는 순간 그것이 마지막 본체가 되어 409 다."""
    client = p2_client()
    extra = _add_body(client)                       # 8 바이트 → 합계 108
    assert _total_size(sql, DS_A1) == 108
    assert _body_path(tmp_path, DS_A1, extra["fileId"]).is_file()
    body_before = len(_activities(sql, DS_A1, ACTION_BODY_CHANGED))
    times_before = _dataset_times(sql, DS_A1)

    r = client.delete(f"{API_PREFIX}/datasets/{DS_A1}/files/{extra['fileId']}",
                      headers=auth(TOKEN_RES))
    assert r.status_code == 204, r.text
    assert sql("SELECT count(*) AS n FROM d3_file WHERE id = :f",
               {"f": extra["fileId"]})[0]["n"] == 0
    assert not _body_path(tmp_path, DS_A1, extra["fileId"]).exists(), "행은 지웠는데 바이트가 남았다."
    assert _total_size(sql, DS_A1) == 100
    assert len(_activities(sql, DS_A1, ACTION_BODY_CHANGED)) == body_before + 1
    assert _dataset_times(sql, DS_A1)["last_modified_at"] > times_before["last_modified_at"]

    # 이제 시드 본체가 마지막이다.
    assert client.delete(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}",
                         headers=auth(TOKEN_RES)).status_code == 409


def test_the_seed_body_can_go_once_a_second_body_exists(p2_client, sql) -> None:
    """마지막 본체 판정은 **어느 파일이냐**가 아니라 **몇 건 남느냐**다 — 처음 올린 본체도 지울 수 있다."""
    client = p2_client()
    extra = _add_body(client)
    r = client.delete(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}", headers=auth(TOKEN_RES))
    assert r.status_code == 204, r.text
    remaining = sql("SELECT id FROM d3_file WHERE dataset_id = :d AND kind = '본체'", {"d": DS_A1})
    assert [x["id"] for x in remaining] == [extra["fileId"]]
    assert _total_size(sql, DS_A1) == 50 + 8


def test_deleting_the_representative_body_file_resets_the_representative_to_auto(
        p2_client, sql) -> None:
    """대표 조각(`representative_file_id`)이 지워지면 **FK `ON DELETE SET NULL`** 이 되돌린다
    (`schema.sql` `d3_dataset_representative_file_fk`). 그 열의 `NULL` 은 「없음」이 아니라
    **「자동」**이다 — 값이 있으면 사람이 지정한 것이라 렌더 결과가 바뀌어도 따라 움직이지 않는다
    (`d3_dataset.representative_file_id` 열 주석 · 결정 2-4·2-8). 그래서 앱 코드가 남은 본체를
    골라 써 넣지 않는다 — 써 넣으면 「사람이 지정했다」는 없는 사실이 된다.
    """
    client = p2_client()
    r = client.patch(f"{API_PREFIX}/datasets/{DS_A1}", json={"representativeFileId": BODY_FILE},
                     headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert sql("SELECT representative_file_id AS r FROM d3_dataset WHERE id = :d",
               {"d": DS_A1})[0]["r"] == BODY_FILE
    _add_body(client)

    r = client.delete(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}", headers=auth(TOKEN_RES))
    assert r.status_code == 204, r.text
    assert sql("SELECT representative_file_id AS r FROM d3_dataset WHERE id = :d",
               {"d": DS_A1})[0]["r"] is None, "지워진 조각을 대표가 그대로 가리킨다."


def test_the_bundle_name_follows_the_body_it_came_from(p2_client, sql) -> None:
    """`bundle_file_name`(상세의 `fileName`)은 등록 전환이 **첫 본체의 이름**으로 세운다. 그 본체가
    지워지거나 이름이 바뀌면 지워진 파일의 이름이 화면에 남는다 — 남은 본체 중 가장 오래된 것의
    이름으로 따라간다 (`[정본 무근거]` · 대표 조각과 같은 「가장 오래된 본체」 규칙). 다른 이름이
    적혀 있으면(사람이 바꾼 묶음 이름) 건드리지 않는다."""
    client = p2_client()
    receipt = make_upload(client, files=[
        ("files", ("a.nc", HDF5_MAGIC, "application/octet-stream")),
        ("files", ("b.nc", HDF5_MAGIC + b"x", "application/octet-stream"))])
    dataset_id = register(client, receipt).json()["datasetId"]
    by_name = {f["fileName"]: f["fileId"] for f in receipt["files"]}
    assert _autometa(sql, dataset_id)["bundle_file_name"] == "a.nc", "전제 확인 — 첫 본체의 이름."

    r = client.delete(f"{API_PREFIX}/datasets/{dataset_id}/files/{by_name['a.nc']}",
                      headers=auth(TOKEN_RES))
    assert r.status_code == 204, r.text
    assert _autometa(sql, dataset_id)["bundle_file_name"] == "b.nc"
    assert client.get(f"{API_PREFIX}/datasets/{dataset_id}",
                      headers=auth(TOKEN_RES)).json()["fileName"] == "b.nc"

    r = client.put(f"{API_PREFIX}/datasets/{dataset_id}/files/{by_name['b.nc']}",
                   files={"file": ("c.nc", HDF5_MAGIC, "application/octet-stream")},
                   headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert _autometa(sql, dataset_id)["bundle_file_name"] == "c.nc"

    # 사람이 적은 묶음 이름은 파일 조작이 안 건드린다.
    sql("UPDATE d3_dataset_autometa SET bundle_file_name = '강우 묶음' WHERE dataset_id = :d",
        {"d": dataset_id})
    r = client.put(f"{API_PREFIX}/datasets/{dataset_id}/files/{by_name['b.nc']}",
                   files={"file": ("d.nc", HDF5_MAGIC, "application/octet-stream")},
                   headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert _autometa(sql, dataset_id)["bundle_file_name"] == "강우 묶음"


def test_body_file_operations_across_the_lab_boundary_are_404(p2_client, sql) -> None:
    """경계 밖은 **404** 다 — 존재 자체를 알리지 않는다 (P-9·P-10). 본체가 열렸다고 경계가 열리지 않는다."""
    client = p2_client()
    files = {"file": ("b.csv", b"a,b\n", "text/csv")}
    assert client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}", files=files,
                      headers=auth(TOKEN_B)).status_code == 404
    assert client.delete(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}",
                         headers=auth(TOKEN_B)).status_code == 404
    assert client.post(f"{API_PREFIX}/datasets/{DS_A1}/files", files=files, data={"kind": "본체"},
                       headers=auth(TOKEN_B)).status_code == 404
    assert sql("SELECT size_bytes FROM d3_file WHERE id = :f", {"f": BODY_FILE})[0]["size_bytes"] == 50
    assert sql("SELECT count(*) AS n FROM d3_file WHERE dataset_id = :d", {"d": DS_A1})[0]["n"] == 2


# ═════════════════════════ 후주입 (`addDatasetFile`) ════════════════════════
def test_adding_a_body_file_works_and_records_one_body_activity_row(p2_client, sql) -> None:
    """후주입 경로. 조각 수(메타)는 트리거가 유지한다 (`㊼`). 이력은 **본체 문자열**이고
    격자 행은 늘지 않는다 — 추가도 교체·삭제와 같은 규칙(`마지막 수정` 이동 · `crs` 무변경)이다."""
    client = p2_client()
    grid_before = len(_activities(sql, DS_A1, ACTION_GRID_CHANGED))
    body_before = len(_activities(sql, DS_A1, ACTION_BODY_CHANGED))
    count_before = sql("SELECT file_count FROM d3_dataset WHERE id = :d",
                       {"d": DS_A1})[0]["file_count"]
    times_before = _dataset_times(sql, DS_A1)
    crs_before = _autometa(sql, DS_A1)["crs"]
    assert crs_before == "EPSG:5179", "전제 확인 — 시드의 crs."

    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/files",
                    files={"file": ("extra.csv", b"a,b\n1,2\n", "text/csv")},
                    data={"kind": "본체"}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    assert r.json()["kind"] == "본체"
    assert len(r.json()["fileId"]) == 26
    assert len(_activities(sql, DS_A1, ACTION_BODY_CHANGED)) == body_before + 1
    assert len(_activities(sql, DS_A1, ACTION_GRID_CHANGED)) == grid_before, \
        "본체 추가가 격자 활동 행을 남겼다."
    assert sql("SELECT file_count FROM d3_dataset WHERE id = :d",
               {"d": DS_A1})[0]["file_count"] == count_before + 1
    assert _dataset_times(sql, DS_A1)["last_modified_at"] > times_before["last_modified_at"]
    assert _autometa(sql, DS_A1)["crs"] == crs_before, "본체 추가가 crs 를 지웠다 (`_CLEAR_GRID_META`)."


def test_post_injecting_a_grid_file_is_refused_because_nobody_decides_its_axis(
        p2_client) -> None:
    """⚠ **미구현을 시험이 고정한다 — 이것은 통과가 아니라 등재다.**

    `d3_file` 의 CHECK 는 「기준 격자 파일 → `carries_lat`·`carries_lon` 중 최소 하나 true」를
    요구하는데(`0004` · `〈66〉`), **축은 파일을 열어야 나오고** 그 판별은 pipeline-worker 의
    일이다 — core-api 에는 geo 라이브러리가 없다(`CLAUDE.md §3-4`).
    업로드 경로에서는 워커가 뒤늦게 행을 세우면 되지만(`record_file_axes_row`), **후주입은
    업로드를 지나지 않아 축을 채워 줄 주체가 어디에도 없다.**

    그래서 **축을 지어내지 않고 거절한다**(`〈66〉` — 축이 빈 행을 만들지 않는다).
    이 자리는 `P2-api-report.md` 에 경계 멈춤으로 올렸다. **200 으로 그럴듯하게 넘기지 않는다.**
    """
    r = p2_client().post(f"{API_PREFIX}/datasets/{DS_A1}/files",
                         files={"file": ("grid.npy", b"\x93NUMPY", "application/octet-stream")},
                         data={"kind": "기준 격자 파일"}, headers=auth(TOKEN_RES))
    assert r.status_code == 400
    assert "축" in r.json()["message"]


def test_file_operations_need_the_upload_edit_switch(p2_client, sql) -> None:
    """`〈59〉-②` — 판정은 스위치가 한다. **소유자는 별도 관문이 아니다** (`P2.md §2-23`)."""
    sql("UPDATE d2_permission_switch SET enabled = false"
        " WHERE account_id = :a AND switch = '업로드·편집'", {"a": "000000000000000000000000A1"},
        account_id="00000000000000000000000AP1")
    try:
        client = p2_client()
        assert client.delete(f"{API_PREFIX}/datasets/{DS_A1}/files/{GRID_FILE}",
                             headers=auth(TOKEN_RES)).status_code == 403
        assert client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}",
                          files={"file": ("b.csv", b"a,b\n", "text/csv")},
                          headers=auth(TOKEN_RES)).status_code == 403
    finally:
        sql("UPDATE d2_permission_switch SET enabled = true"
            " WHERE account_id = :a AND switch = '업로드·편집'",
            {"a": "000000000000000000000000A1"}, account_id="00000000000000000000000AP1")


def test_the_activity_action_strings_are_exactly_the_ones_fixed() -> None:
    """값 집합이 열린 것은 **아무 문자열이나 써도 된다는 뜻이 아니다** — 정본이 안 닫았다는
    뜻이다 (`〈60〉`). 레인마다 다른 문자열을 쓰면 활동 화면이 뒤죽박죽이 된다.
    본체 쪽 문자열은 `[정본 무근거]` 이고 `routes/ingestion.py` 한 곳에 산다 (`〈280〉-⑦-⑾` Ted 판정 대기)."""
    assert ACTION_GRID_CHANGED == "좌표계·격자 변경"
    assert ACTION_BODY_CHANGED == "본체 파일 변경"
    assert ACTION_BODY_CHANGED != ACTION_GRID_CHANGED


# ═══════════ 파일 메타 — `byteSize`·`createdAt`·`relativePath` (`〈278〉-(가)·(나)`) ═══════════
def test_grid_replace_response_carries_size_and_created_at(p2_client, sql) -> None:
    """모든 파일 응답이 `d3_catalog.file_ref` 하나를 지난다 — 교체 응답에도 크기·시각이 있고,
    `total_size_bytes` 는 트리거가 차분(50 → 8)으로 따라온다."""
    client = p2_client()
    payload = b"\x89HDF\r\n\x1a\n"
    r = client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{GRID_FILE}",
                   files={"file": ("new-grid.nc", payload, "application/octet-stream")},
                   headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["byteSize"] == len(payload)
    assert body["createdAt"].endswith("Z")
    assert body["gridAxis"] == {"carriesLat": True, "carriesLon": True}
    assert "relativePath" not in body
    assert sql("SELECT total_size_bytes FROM d3_dataset_autometa WHERE dataset_id = :d",
               {"d": DS_A1})[0]["total_size_bytes"] == 50 + len(payload)


def test_adding_a_body_file_with_a_relative_path_keeps_the_folder(p2_client, sql) -> None:
    """`addDatasetFile` 의 `relativePath` 가 `d3_file.relative_path`(0009)에 남고, 응답과 목록에
    **있을 때만** 키로 선다. 합계는 트리거가 더한다(100 → 108)."""
    client = p2_client()
    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/files",
                    files={"file": ("extra.csv", b"a,b\n1,2\n", "text/csv")},
                    data={"kind": "본체", "relativePath": "sub\\dir/extra.csv"},
                    headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["relativePath"] == "sub/dir/extra.csv"
    assert body["byteSize"] == 8 and body["createdAt"].endswith("Z")
    assert "gridAxis" not in body

    listed = {f["fileId"]: f for f in
              client.get(f"{API_PREFIX}/datasets/{DS_A1}/files",
                         headers=auth(TOKEN_RES)).json()["items"]}
    assert listed[body["fileId"]]["relativePath"] == "sub/dir/extra.csv"
    assert "relativePath" not in listed[BODY_FILE]
    assert listed[BODY_FILE]["byteSize"] == 50
    assert sql("SELECT total_size_bytes FROM d3_dataset_autometa WHERE dataset_id = :d",
               {"d": DS_A1})[0]["total_size_bytes"] == 108


def test_adding_a_file_with_an_unnormalizable_relative_path_is_400(p2_client, sql) -> None:
    before = sql("SELECT count(*) AS n FROM d3_file WHERE dataset_id = :d", {"d": DS_A1})[0]["n"]
    r = p2_client().post(f"{API_PREFIX}/datasets/{DS_A1}/files",
                         files={"file": ("x.csv", b"a\n", "text/csv")},
                         data={"kind": "본체", "relativePath": ".."}, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text
    assert sql("SELECT count(*) AS n FROM d3_file WHERE dataset_id = :d",
               {"d": DS_A1})[0]["n"] == before
