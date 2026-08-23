"""`addDatasetFile` · `replaceDatasetGridFile` · `deleteDatasetGridFile` — 그리고 **`〈60〉`**.

`〈60〉` 이 못 박은 셋을 실물로 확인한다:
  ① `마지막 수정` 을 **건드리지 않는다** → 파생인 `계보 상태` 가 `확정` → `확인 필요` 로
     **접히지 않는다.** 경보가 잦으면 사람이 경보를 끈다.
  ② `자동으로 읽은 정보`(좌표계·격자)를 **재계산한다.**
  ③ `d8_activity` 에 **`좌표계·격자 변경` 한 행** — 그 문자열 그대로.

그리고 `〈59〉-③` — **본체는 이 경로의 대상이 아니다** (409).
"""
from __future__ import annotations

from conftest import DS_A1, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX
from colab_core.domains.d8_insight import ACTION_GRID_CHANGED

#: 시드의 `a1-grid.nc` — 결합축(둘 다 true) 기준 격자 파일이다 (seed.sql:70).
GRID_FILE = "00000000000000000000000FA2"
#: 시드의 `a1-body.csv` — 본체다.
BODY_FILE = "00000000000000000000000FA1"


def _activities(sql, dataset_id):
    return sql("SELECT action, actor_account_id FROM d8_activity"
               "  WHERE target_id = :d AND action = :a",
               {"d": dataset_id, "a": ACTION_GRID_CHANGED})


def _dataset_times(sql, dataset_id):
    return sql("SELECT last_modified_at, lineage_confirmed_at FROM d3_dataset WHERE id = :d",
               {"d": dataset_id})[0]


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


def test_replacing_a_body_file_is_409(p2_client) -> None:
    """`〈59〉-③` — **본체를 갈아 끼우는 것은 다른 데이터다** (`DataModel §4.3`)."""
    r = p2_client().put(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}",
                        files={"file": ("b.csv", b"a,b\n", "text/csv")},
                        headers=auth(TOKEN_RES))
    assert r.status_code == 409
    assert r.json()["code"] == "CONFLICT"


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


def test_deleting_a_body_file_is_409(p2_client, sql) -> None:
    """**본체는 지우지 않는다.** 지워지면 마지막 본체가 사라진 데이터셋이 생긴다."""
    r = p2_client().delete(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}",
                           headers=auth(TOKEN_RES))
    assert r.status_code == 409
    assert sql("SELECT count(*) AS n FROM d3_file WHERE id = :f", {"f": BODY_FILE})[0]["n"] == 1


# ═════════════════════════ 후주입 (`addDatasetFile`) ════════════════════════
def test_adding_a_body_file_works_and_records_one_activity_row(p2_client, sql) -> None:
    """후주입 경로. 조각 수(메타)는 트리거가 유지한다 (`㊼`)."""
    client = p2_client()
    before = len(_activities(sql, DS_A1))
    count_before = sql("SELECT file_count FROM d3_dataset WHERE id = :d",
                       {"d": DS_A1})[0]["file_count"]

    r = client.post(f"{API_PREFIX}/datasets/{DS_A1}/files",
                    files={"file": ("extra.csv", b"a,b\n1,2\n", "text/csv")},
                    data={"kind": "본체"}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    assert r.json()["kind"] == "본체"
    assert len(r.json()["fileId"]) == 26
    assert len(_activities(sql, DS_A1)) == before + 1
    assert sql("SELECT file_count FROM d3_dataset WHERE id = :d",
               {"d": DS_A1})[0]["file_count"] == count_before + 1


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
    finally:
        sql("UPDATE d2_permission_switch SET enabled = true"
            " WHERE account_id = :a AND switch = '업로드·편집'",
            {"a": "000000000000000000000000A1"}, account_id="00000000000000000000000AP1")


def test_the_activity_action_string_is_exactly_the_one_the_decision_fixed() -> None:
    """값 집합이 열린 것은 **아무 문자열이나 써도 된다는 뜻이 아니다** — 정본이 안 닫았다는
    뜻이다 (`〈60〉`). 레인마다 다른 문자열을 쓰면 활동 화면이 뒤죽박죽이 된다."""
    assert ACTION_GRID_CHANGED == "좌표계·격자 변경"
