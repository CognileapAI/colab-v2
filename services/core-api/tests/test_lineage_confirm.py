"""계보 확정 3 op + **Lv 파생** + **음성 ㉯ 순환·자기부모 금지**.

Lv 오라클은 지어낸 픽스처가 아니라 **KWRA 다운스케일 묶음**이다 (`SEED-DATA §4.1` ·
`P2.md §2-3`·`§2-4`): 부모 1(D-01 NDVI 2 km) → 자식 4(Nearest·Bilinear·IDW·Co-Kriging),
관계마다 가공 방식이 다르고 **DEM(D-02)이 D-06 에 `보조입력`으로 붙는다.**
검증 오라클 = **D-06 의 Lv 가 1 이고, DEM(Lv0)이 그 값을 바꾸지 않는다.**

지어낸 픽스처는 *네 자식이 한 부모를 공유한다* 와 *DEM 은 Lv 계산에서 빠진다* 를 동시에
때리지 못한다 (`P2.md §8-B`).
"""
from __future__ import annotations

from conftest import DS_A1, DS_A2, TOKEN_PROF, TOKEN_RES, auth
from test_dataset_registration import make_upload, register
from test_uploads import HDF5_MAGIC

from colab_core.app.main import API_PREFIX


def _new_dataset(client, name: str, **extra) -> str:
    receipt = make_upload(client, files=[
        ("files", (f"{name}.nc", HDF5_MAGIC, "application/octet-stream"))])
    body = {"uploadId": receipt["uploadId"], "name": name, "summary": "시험용 설명 한 줄", **extra}
    r = client.post(f"{API_PREFIX}/datasets", json=body, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    return r.json()["datasetId"]


def _add_parent(client, child, parent, **extra):
    """op = `addLineageParent`. (짝 op = `removeLineageParent` · `confirmLineage`)"""
    return client.post(f"{API_PREFIX}/datasets/{child}/lineage/parents",
                       json={"parentDatasetId": parent, **extra}, headers=auth(TOKEN_RES))


# ═══════════════════════ 양성 ③ — KWRA 다운스케일 묶음 ══════════════════════
def test_the_kwra_downscale_bundle_is_the_lv_oracle(p2_client) -> None:
    """**양성 ③** — 한 부모 4자식 · 관계별 가공 방식 4종 · **D-06 의 Lv 가 1** ·
    **DEM 이 그 값을 바꾸지 않는다.**"""
    client = p2_client()
    ndvi = _new_dataset(client, "D-01 NDVI 2km")            # 부모. 부모가 없으니 Lv0
    dem = _new_dataset(client, "D-02 DEM")                   # 보조입력. 역시 Lv0
    methods = ["Nearest", "Bilinear", "IDW", "Co-Kriging"]
    children = {}
    for index, method in enumerate(methods, start=3):
        child = _new_dataset(client, f"D-0{index} {method}")
        r = _add_parent(client, child, ndvi, parentRole="주입력", method=method)
        assert r.status_code == 201, r.text
        children[method] = child

    detail = client.get(f"{API_PREFIX}/datasets/{ndvi}", headers=auth(TOKEN_RES)).json()
    assert detail["processingLevel"] == 0, "부모가 없는 데이터는 Lv0 이다."

    d06 = children["Co-Kriging"]
    before = client.get(f"{API_PREFIX}/datasets/{d06}", headers=auth(TOKEN_RES)).json()
    assert before["processingLevel"] == 1, "주입력 부모(Lv0)의 자식은 Lv1 이다."

    # **DEM 을 `보조입력` 으로 붙인다 — Lv 는 그대로 1 이어야 한다.**
    r = _add_parent(client, d06, dem, parentRole="보조입력", method="지형 보정")
    assert r.status_code == 201, r.text
    after = client.get(f"{API_PREFIX}/datasets/{d06}", headers=auth(TOKEN_RES)).json()
    assert after["processingLevel"] == 1, \
        "보조입력이 Lv 계산에 들어갔다 — `P2.md §2-4` 가 빼라고 한 자리다."

    graph = r.json()
    roles = sorted(e["parentRole"] for e in graph["edges"] if e["childDatasetId"] == d06)
    assert roles == ["보조입력", "주입력"]
    # **가공 방식은 데이터셋이 아니라 관계에 붙는다** (`P2.md §2-5`).
    by_parent = {e["parentDatasetId"]: e["method"] for e in graph["edges"]}
    assert by_parent[ndvi] == "Co-Kriging"
    assert by_parent[dem] == "지형 보정"

    # 네 자식이 **한 부모를 공유한다.**
    parent_graph = _add_parent(client, children["IDW"], dem, parentRole="보조입력")
    assert parent_graph.status_code == 201
    ndvi_children = client.post(f"{API_PREFIX}/datasets/{ndvi}/lineage/confirmation",
                                headers=auth(TOKEN_RES)).json()
    derived = [n for n in ndvi_children["nodes"] if n["kind"] == "파생"]
    assert len(derived) == 4, f"한 부모의 자식이 4건이어야 한다 — {len(derived)} 건이다."


def test_lv_is_derived_and_never_stored(p2_client, sql) -> None:
    """**Lv 는 저장하지 않는다** (`P2.md §2-4`·`§2-6` · `PLAN-SoT §9-⑳`).

    저장 컬럼이 없는 것이 이 계산의 강제다 — 컬럼이 생기면 계산과 저장이 갈라진다.
    """
    columns = sql("SELECT column_name FROM information_schema.columns"
                  "  WHERE table_name IN ('d3_dataset', 'd3_dataset_description',"
                  "                       'd3_dataset_autometa', 'd4_lineage_edge')")
    names = {c["column_name"] for c in columns}
    for forbidden in ("processing_level", "lv", "level", "lineage_state"):
        assert forbidden not in names, f"파생값이 컬럼으로 저장되고 있다: {forbidden}"


# ═════════════════ 음성 ㉯ — 순환·자기부모 금지 (`DR-15`) ═══════════════════
def test_self_parent_is_refused(p2_client, sql) -> None:
    """`A → A`. **들어가면 되돌릴 수 없는 오염이다.**"""
    client = p2_client()
    dataset_id = _new_dataset(client, "자기부모 시험")
    r = _add_parent(client, dataset_id, dataset_id)
    assert r.status_code == 409, r.text
    assert sql("SELECT count(*) AS n FROM d4_lineage_edge WHERE child_dataset_id = :d",
               {"d": dataset_id})[0]["n"] == 0


def test_a_two_hop_cycle_is_refused(p2_client, sql) -> None:
    """`A→B→A`. **DB 제약이 못 막는 자리다** — `CHECK(child <> parent)` 도
    `UNIQUE(child, parent)` 도 이것을 통과시킨다. 그래서 애플리케이션이 막는다."""
    client = p2_client()
    a = _new_dataset(client, "순환 A")
    b = _new_dataset(client, "순환 B")
    assert _add_parent(client, b, a).status_code == 201     # B ← A
    r = _add_parent(client, a, b)                            # A ← B 를 붙이면 순환
    assert r.status_code == 409, r.text
    assert sql("SELECT count(*) AS n FROM d4_lineage_edge WHERE child_dataset_id = :d",
               {"d": a})[0]["n"] == 0


def test_a_three_hop_cycle_is_refused(p2_client, sql) -> None:
    """`A→B→C→A`. **길이 2 만 막는 규칙은 규칙이 아니다** — 재귀로 끝까지 훑는다."""
    client = p2_client()
    a = _new_dataset(client, "긴 순환 A")
    b = _new_dataset(client, "긴 순환 B")
    c = _new_dataset(client, "긴 순환 C")
    assert _add_parent(client, b, a).status_code == 201     # B ← A
    assert _add_parent(client, c, b).status_code == 201     # C ← B
    r = _add_parent(client, a, c)                            # A ← C → 순환
    assert r.status_code == 409, r.text
    assert sql("SELECT count(*) AS n FROM d4_lineage_edge WHERE child_dataset_id = :d",
               {"d": a})[0]["n"] == 0


def test_a_cycle_through_a_secondary_parent_is_also_refused(p2_client) -> None:
    """**보조입력도 관계다.** Lv 계산에서만 빠질 뿐, 순환은 역할을 가리지 않는다."""
    client = p2_client()
    a = _new_dataset(client, "보조 순환 A")
    b = _new_dataset(client, "보조 순환 B")
    assert _add_parent(client, b, a, parentRole="보조입력").status_code == 201
    assert _add_parent(client, a, b).status_code == 409


def test_registration_time_parents_are_cycle_checked_too(p2_client, sql) -> None:
    """`createDataset` 이 실어 온 관계도 같은 문을 지난다 — **한 문만 잠그면 다른 문이 열려 있다.**"""
    client = p2_client()
    child = _new_dataset(client, "등록 순환 자식")
    receipt = make_upload(client)
    # 새 데이터셋의 부모로 자기 자식을 지목할 수는 없으니(아직 ID 가 없다), 대신
    # 등록 경로가 `add_parent` 를 지나는지 확인한다 — 지나면 순환 판정이 함께 걸린다.
    r = register(client, receipt,
                 lineageParents=[{"parentDatasetId": child, "origin": "manual"}])
    assert r.status_code == 201
    new_id = r.json()["datasetId"]
    assert _add_parent(client, child, new_id).status_code == 409, \
        "등록으로 만든 관계가 순환 판정에서 빠졌다."


# ═══════════════════════ 만들어진 경로 · 확인 기록 ══════════════════════════
def test_add_lineage_parent_always_records_a_manual_origin(p2_client, sql) -> None:
    """**요청이 만들어진 경로를 고르지 않는다** (`LineageParentCreate` 산문).

    상세 화면의 수동 추가는 언제나 `manual` 이다 — 요청이 `origin` 을 실어
    보내면 AI 가 붙인 것처럼 위장할 수 있다.
    """
    client = p2_client()
    child = _new_dataset(client, "경로 시험")
    r = _add_parent(client, child, DS_A1, origin="ai")
    assert r.status_code == 400, "요청이 origin 을 실을 수 있으면 안 된다."

    assert _add_parent(client, child, DS_A1).status_code == 201
    rows = sql("SELECT origin, confirmed_by_account_id FROM d4_lineage_edge"
               "  WHERE child_dataset_id = :d", {"d": child})
    assert rows[0]["origin"] == "manual"
    # **확인 기록은 NOT NULL 이다** — 누가 확인했는지 없이 관계가 들어갈 수 없다.
    assert rows[0]["confirmed_by_account_id"] == "000000000000000000000000A1"


def test_adding_a_parent_clears_the_unknown_mark(p2_client, sql) -> None:
    """`기록 없음` 표시는 관계가 붙으면 사라진다 (`DataModel §4.2`)."""
    client = p2_client()
    child = _new_dataset(client, "기록 없음 시험")
    assert sql("SELECT count(*) AS n FROM d4_lineage_unknown WHERE dataset_id = :d",
               {"d": child})[0]["n"] == 1
    graph = _add_parent(client, child, DS_A1).json()
    assert graph["unknownParents"] is False
    assert sql("SELECT count(*) AS n FROM d4_lineage_unknown WHERE dataset_id = :d",
               {"d": child})[0]["n"] == 0


# ═══════════════════════ removeLineageParent ════════════════════════════════
def test_removing_a_parent_removes_only_the_pair(p2_client, sql) -> None:
    """관계 한 쌍만 지운다 — **데이터셋은 지워지지 않는다.**"""
    client = p2_client()
    child = _new_dataset(client, "관계 끊기 시험")
    _add_parent(client, child, DS_A1)
    r = client.delete(f"{API_PREFIX}/datasets/{child}/lineage/parents/{DS_A1}",
                      headers=auth(TOKEN_RES))
    assert r.status_code == 204
    assert sql("SELECT count(*) AS n FROM d4_lineage_edge WHERE child_dataset_id = :d",
               {"d": child})[0]["n"] == 0
    assert sql("SELECT count(*) AS n FROM d3_dataset WHERE id = :d", {"d": child})[0]["n"] == 1
    assert sql("SELECT count(*) AS n FROM d3_dataset WHERE id = :d", {"d": DS_A1})[0]["n"] == 1


def test_removing_a_relation_that_does_not_exist_is_404(p2_client) -> None:
    client = p2_client()
    child = _new_dataset(client, "없는 관계")
    assert client.delete(f"{API_PREFIX}/datasets/{child}/lineage/parents/{DS_A1}",
                         headers=auth(TOKEN_RES)).status_code == 404


# ═══════════════════════════ confirmLineage ═════════════════════════════════
def test_confirming_moves_the_confirmed_at_but_not_the_last_modified(p2_client, sql) -> None:
    """사람이 다시 확인하면 **계보 확정일이 갱신되고 `이후 수정됨` 표시가 사라진다.**

    계보 상태는 이 호출의 **결과로 계산될 뿐** 요청이 값을 싣지 않는다 (`PLAN-SoT §9-⑳`).
    """
    client = p2_client()
    before = sql("SELECT last_modified_at, lineage_confirmed_at FROM d3_dataset WHERE id = :d",
                 {"d": DS_A2})[0]
    detail = client.get(f"{API_PREFIX}/datasets/{DS_A2}", headers=auth(TOKEN_RES)).json()
    assert detail["lineageState"] == "확정"

    r = client.post(f"{API_PREFIX}/datasets/{DS_A2}/lineage/confirmation", headers=auth(TOKEN_RES))
    assert r.status_code == 200, r.text
    after = sql("SELECT last_modified_at, lineage_confirmed_at FROM d3_dataset WHERE id = :d",
                {"d": DS_A2})[0]
    assert after["lineage_confirmed_at"] > before["lineage_confirmed_at"]
    assert after["last_modified_at"] == before["last_modified_at"]
    assert r.json()["lineageState"] == "확정"


def test_confirming_folds_a_needs_review_state_back_to_confirmed(p2_client, sql) -> None:
    """`확인 필요` → 확인 → `확정`. 판정식은 `마지막 수정 > 계보 확정일` 하나다."""
    client = p2_client()
    sql("UPDATE d3_dataset SET lineage_confirmed_at = last_modified_at - interval '1 day'"
        " WHERE id = :d", {"d": DS_A2})
    assert client.get(f"{API_PREFIX}/datasets/{DS_A2}",
                      headers=auth(TOKEN_RES)).json()["lineageState"] == "확인 필요"
    graph = client.post(f"{API_PREFIX}/datasets/{DS_A2}/lineage/confirmation",
                        headers=auth(TOKEN_RES)).json()
    assert graph["lineageState"] == "확정"


def test_lineage_edits_need_the_upload_edit_switch(p2_client, sql) -> None:
    sql("UPDATE d2_permission_switch SET enabled = false"
        " WHERE account_id = :a AND switch = '업로드·편집'", {"a": "000000000000000000000000A1"},
        account_id="00000000000000000000000AP1")
    try:
        client = p2_client()
        assert _add_parent(client, DS_A2, DS_A1).status_code == 403
        assert client.post(f"{API_PREFIX}/datasets/{DS_A2}/lineage/confirmation",
                           headers=auth(TOKEN_RES)).status_code == 403
    finally:
        sql("UPDATE d2_permission_switch SET enabled = true"
            " WHERE account_id = :a AND switch = '업로드·편집'",
            {"a": "000000000000000000000000A1"}, account_id="00000000000000000000000AP1")


def test_lineage_ops_do_not_cross_the_lab_boundary(p2_client) -> None:
    """남의 연구실 데이터셋은 **없는 것**이다 — 403 이 아니라 404."""
    from conftest import DS_B1, TOKEN_B
    client = p2_client()
    assert _add_parent(client, DS_A2, DS_B1).status_code == 404
    assert client.post(f"{API_PREFIX}/datasets/{DS_A2}/lineage/confirmation",
                       headers=auth(TOKEN_B)).status_code == 404


def test_the_professor_can_edit_lineage_without_a_stored_switch(p2_client) -> None:
    """교수는 네 스위치가 **판정으로** 켜진다 (P-5) — 저장된 행이 없어도 된다."""
    client = p2_client()
    r = client.post(f"{API_PREFIX}/datasets/{DS_A2}/lineage/confirmation", headers=auth(TOKEN_PROF))
    assert r.status_code == 200
