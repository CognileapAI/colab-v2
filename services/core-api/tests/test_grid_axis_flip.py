"""축 뒤집기 — `K-3` (`PLAN-SoT §9-〈80〉-㉯ 3`). **새 op 이 없다.**

`replaceDatasetGridFile` 의 의미 안에 든다. 뒤집기 = **같은 두 파일의 축 배정을 맞바꾸는 것**
이고 그것이 `〈59〉` 가 말한 「잘못 붙인 격자를 바로잡는」 정상 동작이다.
**파일을 다시 올리지 않는다.**

왜 「한 파일의 축을 고친다」가 아닌가
  `0004_p2_grid_axis_and_d5:192-195` 가 **축 원소마다 부분 유니크**를 건다. 한쪽만 바꾸면
  중간 상태가 「위도 둘」이라 제약이 깨진다 — 맞바꿈은 한 트랜잭션 안에서 끝나야 한다.
  그래서 격자 파일이 2건이 아니면 **409** 다: 바꿀 배정이 없다.

그리고 `PREVIEW-IMPLEMENTATION §10-16` — **사용자에게 「이 파일이 위도냐 경도냐」를 묻지 않는다.**
서버가 판별하고, 지금 배정을 보여주고(`DatasetFile.gridAxis`), 뒤집기 버튼을 준다.
"""
from __future__ import annotations

import pytest
from conftest import DS_A1, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX
from colab_core.domains.d8_insight import ACTION_GRID_CHANGED

#: 시드의 `a1-grid.nc` — 결합축(둘 다 true) 기준 격자 파일이다 (seed.sql:70).
GRID_FILE = "00000000000000000000000FA2"
BODY_FILE = "00000000000000000000000FA1"

#: 시드의 결합축 파일을 **위도 전용**으로 쓰는 자리 — 짝의 한쪽이다.
LAT_FILE = GRID_FILE
#: 짝의 나머지 한쪽. 시험이 심고 시험이 걷는다.
LON_FILE = "00000000000000000000000FA4"


@pytest.fixture()
def pair(sql):
    """DS_A1 의 격자를 **위도 1 + 경도 1** 짝으로 갈아 놓고, 끝나면 시드 상태로 되돌린다.

    `addDatasetFile` 로는 만들 수 없다 — 그 op 은 축을 지어내지 않으려고 격자 후주입을
    400 으로 막아 뒀다(`〈66〉`). 축을 심는 것은 파일을 읽는 쪽의 일이고, 이 시험이 재는 것은
    **이미 축이 붙은 두 행을 맞바꾸는 조작**이다.

    ⚠ **되돌림을 시험이 직접 한다.** 시드 행(`FA2`)의 축을 바꿔 놓고 나가면 다음 시험이
    「결합축 1건」이라는 전제를 잃는다 — 그 실패는 실행 순서에 따라 나타났다 사라져서
    원인을 못 찾는다.
    """
    sql("DELETE FROM d3_file WHERE id = :f", {"f": LON_FILE})
    sql("UPDATE d3_file SET carries_lat = true, carries_lon = false WHERE id = :f",
        {"f": LAT_FILE})
    sql("INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes,"
        "                     storage_key, carries_lat, carries_lon)"
        " VALUES (:id, current_lab_id(), :d, '기준 격자 파일', 'lon.npy', 4, :k, false, true)",
        {"id": LON_FILE, "d": DS_A1, "k": f"k/{LON_FILE}"})
    yield
    sql("DELETE FROM d3_file WHERE id = :f", {"f": LON_FILE})
    sql("UPDATE d3_file SET carries_lat = true, carries_lon = true WHERE id = :f",
        {"f": LAT_FILE})


def _axes(sql):
    rows = sql("SELECT id, carries_lat, carries_lon FROM d3_file"
               "  WHERE dataset_id = :d AND kind = '기준 격자 파일' ORDER BY id", {"d": DS_A1})
    return {r["id"]: (r["carries_lat"], r["carries_lon"]) for r in rows}


def test_flip_swaps_the_axis_assignment_of_the_two_grid_files(p2_client, sql, pair) -> None:
    """뒤집기는 **두 행을 함께** 바꾼다. 한쪽만 바뀌면 부분 유니크가 깨져 있거나 반쪽만 고쳐진 것이다."""
    assert _axes(sql) == {LAT_FILE: (True, False), LON_FILE: (False, True)}

    r = p2_client().put(f"{API_PREFIX}/datasets/{DS_A1}/files/{LAT_FILE}",
                        data={"flipAxes": "true"}, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    assert r.json()["fileId"] == LAT_FILE, "뒤집기가 fileId 를 갈아 끼웠다 — 이력이 다른 것을 가리킨다."
    assert _axes(sql) == {LAT_FILE: (False, True), LON_FILE: (True, False)}


def test_flip_does_not_touch_the_stored_bytes_or_the_file_name(p2_client, sql, pair) -> None:
    """**파일을 다시 올리지 않는다** (`〈80〉-㉯ 3`). 이름·저장 키가 그대로여야 그 말이 참이다."""
    before = sql("SELECT id, file_name, storage_key, size_bytes FROM d3_file"
                 "  WHERE dataset_id = :d AND kind = '기준 격자 파일' ORDER BY id", {"d": DS_A1})
    r = p2_client().put(f"{API_PREFIX}/datasets/{DS_A1}/files/{LON_FILE}",
                        data={"flipAxes": "true"}, headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text   # 거절당한 요청이 바이트를 안 건드리는 건 당연하다 — 오라클이 아니다
    after = sql("SELECT id, file_name, storage_key, size_bytes FROM d3_file"
                "  WHERE dataset_id = :d AND kind = '기준 격자 파일' ORDER BY id", {"d": DS_A1})
    assert before == after


def test_flip_records_one_grid_change_activity_row(p2_client, sql, pair) -> None:
    """`〈60〉-③` — 축을 바로잡은 것도 **`좌표계·격자 변경`** 이다. 그 문자열 그대로."""
    def rows():
        return sql("SELECT action FROM d8_activity WHERE target_id = :d AND action = :a",
                   {"d": DS_A1, "a": ACTION_GRID_CHANGED})
    before = len(rows())
    p2_client().put(f"{API_PREFIX}/datasets/{DS_A1}/files/{LAT_FILE}",
                    data={"flipAxes": "true"}, headers=auth(TOKEN_RES))
    assert len(rows()) == before + 1


def test_flip_is_409_when_the_dataset_has_no_grid_pair(p2_client) -> None:
    """짝이 없으면 바꿀 배정이 없다. 시드의 DS_A1 은 **결합축 1건**뿐이다 — 뒤집어도 같은 것이다."""
    r = p2_client().put(f"{API_PREFIX}/datasets/{DS_A1}/files/{GRID_FILE}",
                        data={"flipAxes": "true"}, headers=auth(TOKEN_RES))
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "CONFLICT"


def test_flip_false_is_400_because_it_asks_for_nothing(p2_client, pair) -> None:
    """`flipAxes: false` 는 **아무것도 안 하는 요청**이다. 200 으로 답하면 「했다」는 거짓말이 된다."""
    r = p2_client().put(f"{API_PREFIX}/datasets/{DS_A1}/files/{LAT_FILE}",
                        data={"flipAxes": "false"}, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text
    assert "flipAxes" in r.json()["message"], \
        "「파일이 없다」와 「아무것도 안 하는 요청이다」가 같은 문구면 사람이 못 고친다."


def test_neither_file_nor_flip_is_400(p2_client, pair) -> None:
    """계약이 `oneOf` 로 못 박은 택일이다 — 둘 다 없는 요청은 400."""
    r = p2_client().put(f"{API_PREFIX}/datasets/{DS_A1}/files/{LAT_FILE}",
                        data={}, headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text


def test_both_file_and_flip_is_400(p2_client, pair) -> None:
    """택일이므로 둘을 함께 보내면 400 이다 — 어느 쪽을 했는지 응답이 말할 수 없다."""
    r = p2_client().put(f"{API_PREFIX}/datasets/{DS_A1}/files/{LAT_FILE}",
                        data={"flipAxes": "true"},
                        files={"file": ("g.npy", b"\x93NUMPY", "application/octet-stream")},
                        headers=auth(TOKEN_RES))
    assert r.status_code == 400, r.text


def test_flip_on_a_body_file_is_409(p2_client, pair) -> None:
    """`〈59〉-③` 는 뒤집기에도 그대로 걸린다 — 본체에는 축이 없다."""
    r = p2_client().put(f"{API_PREFIX}/datasets/{DS_A1}/files/{BODY_FILE}",
                        data={"flipAxes": "true"}, headers=auth(TOKEN_RES))
    assert r.status_code == 409, r.text


# ══════════════════ 화면이 지금 배정을 볼 수 있는가 (`DatasetFile.gridAxis`) ══════════════════
def test_list_dataset_files_exposes_the_axis_of_grid_files_only(p2_client, sql, pair) -> None:
    """뒤집기 버튼을 그리려면 **지금 무엇이 무엇인지**를 화면이 알아야 한다 (`§10-16`).
    본체에는 축이 없다 — `0004` 의 CHECK 가 축 붙은 본체를 애초에 만들지 않는다."""
    r = p2_client().get(f"{API_PREFIX}/datasets/{DS_A1}/files", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    by_id = {item["fileId"]: item for item in r.json()["items"]}
    assert by_id[LAT_FILE]["gridAxis"] == {"carriesLat": True, "carriesLon": False}
    assert by_id[LON_FILE]["gridAxis"] == {"carriesLat": False, "carriesLon": True}
    assert "gridAxis" not in by_id[BODY_FILE], "본체에 축 자리를 만들면 없는 사실을 있는 척한다."
