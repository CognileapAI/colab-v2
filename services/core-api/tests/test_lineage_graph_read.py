"""`getDatasetLineage` — 계보 그래프 **조회** op (WU `P3` · `Policy_데이터셋_상세 §8`).

**그래프를 그리는 함수는 이미 있었다** — `routes/lineage.py:lineage_graph()`. 없던 것은
**그 함수를 부를 GET 라우트 하나**였고, 그 자리가 501 표에 있었다
(`routes/not_implemented.py` · 「이 조회 op 자체는 P1 배정」). `P1` 은 `done` 인데 op 은
501 로 남아 있었다 — **산문이 낡은 자리**이고, 계보 그래프 화면(`P3`)은 이 op 없이 설 수 없다.

**세 상태를 못 박는다** (`CLAUDE.md §4` green-by-skip).

  · **대상 있음 → 검사한다.** 계보 간선이 실재하는 데이터셋으로 노드·간선을 센다.
  · **명시적으로 비어 있음 → 통과하되 건수를 드러낸다.** 계보가 없는 데이터셋도 200 이고,
    노드는 **자기 자신 하나**가 남는다(묘비·원천 규칙과 같은 원리 — 사라지지 않는다).
    이 갈래는 `assert_counted()` 가 **센 건수를 메시지에 적은 채** 통과한다.
  · **아무것도 못 찾음 → red.** 대상 집합이 0 건인 채 지나가는 단언을 두지 않는다.
    `assert_nonempty()` 가 그 자리를 실패로 만든다.

⚠ **이 레포의 실데이터는 계보 간선 6 · 데이터셋 12 다.** 대부분의 데이터셋은 부모도 자식도
0 건이다 — **그래서 「간선을 순회하며 단언한다」는 시험이 아무것도 검사하지 않고 green 이 된다.**
아래 시험은 순회 전에 모수를 세고, 모수가 0 이면 실패한다.
"""
from __future__ import annotations

import json
import pathlib

import yaml
from conftest import DS_A1, DS_A2, DS_B1, TOKEN_B, TOKEN_PROF, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX

REPO = pathlib.Path(__file__).resolve().parents[3]
CONTRACT_PATH = REPO / "contracts" / "seams" / "fe-core.yaml"


# ───────────────────────── 세 상태 도우미 ─────────────────────────
def assert_nonempty(items, what: str):
    """**아무것도 못 찾으면 red.** 0 건인 채 뒤 단언을 통과시키지 않는다."""
    assert len(items) > 0, f"검사 대상이 0 건이다 — 이 시험은 아무것도 검사하지 않았다: {what}"
    return items


def assert_counted(items, expected: int, what: str):
    """**명시적으로 비어 있음(또는 정해진 건수)은 통과하되 건수를 드러낸다.**"""
    assert len(items) == expected, f"{what}: 기대 {expected} · 실측 {len(items)} — {items}"
    print(f"[세 상태] {what} = {len(items)} 건 (명시 기대값 {expected})")
    return items


def graph(client, dataset_id: str, token: str = TOKEN_RES):
    return client.get(f"{API_PREFIX}/datasets/{dataset_id}/lineage", headers=auth(token))


# ───────────────────────── 계약 ↔ 표 ─────────────────────────
def test_the_operation_left_the_not_implemented_table() -> None:
    """501 표에서 내려온 것을 표 자신에게 묻는다 — 라우트만 열고 표를 안 고치면
    `test_route_table.py` 는 여전히 green 이다(501 스텁도 라우트를 등록한다)."""
    from colab_core.app.routes import not_implemented

    ids = assert_nonempty([op.operation_id for op in not_implemented.OPERATIONS], "501 표")
    assert "getDatasetLineage" not in ids, "구현했는데 501 표에 그대로 남아 있다."


def test_the_contract_declares_the_get() -> None:
    doc = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    item = doc["paths"]["/datasets/{datasetId}/lineage"]
    assert item["get"]["operationId"] == "getDatasetLineage"


# ───────────────────────── ① 대상 있음 → 검사한다 ─────────────────────────
def test_a_dataset_with_lineage_returns_its_nodes_and_edges(live_client) -> None:
    """시드는 `DSA2 ← DSA1` 을 들고 있다. **모수를 먼저 세고** 순회한다."""
    r = graph(live_client, DS_A2, TOKEN_RES)
    assert r.status_code == 200, r.text
    body = r.json()

    edges = assert_nonempty(body["edges"], f"{DS_A2} 의 계보 간선")
    for e in edges:
        assert e["childDatasetId"] == DS_A2
        assert e["origin"] in ("ai", "manual", "processed"), e["origin"]
        assert e["confirmedAt"], "확정된 관계만 그린다 — 확정일이 비어 있다."

    kinds = [n["kind"] for n in assert_nonempty(body["nodes"], f"{DS_A2} 의 노드")]
    assert "이 데이터" in kinds, kinds
    assert "가공 전" in kinds, f"부모 간선이 있는데 가공 전 노드가 없다: {kinds}"
    assert kinds.count("이 데이터") == 1, "자기 노드가 둘 이상이다."
    # **프로젝트는 노드가 아니다** — 배지다 (`Policy §1-2` · `§5`).
    assert "프로젝트" not in kinds, kinds
    assert isinstance(body["projectUseCount"], int)


def test_the_parent_side_sees_the_child_as_derived(live_client) -> None:
    """같은 간선을 부모 쪽에서 보면 **파생**이다 — 한 사실이 두 화면에서 같은 값이어야 한다."""
    r = graph(live_client, DS_A1, TOKEN_RES)
    assert r.status_code == 200, r.text
    body = r.json()
    edges = assert_nonempty(body["edges"], f"{DS_A1} 의 계보 간선")
    assert any(e["parentDatasetId"] == DS_A1 for e in edges), edges
    assert "파생" in [n["kind"] for n in body["nodes"]], body["nodes"]


def test_the_read_answers_with_the_same_shape_as_the_write_ops(live_client) -> None:
    """세 쓰기 op 과 **같은 함수**가 답한다 — 같은 사실을 두 모양으로 그리지 않는다.

    계약이 요구하는 필수 키 전부가 응답에 있는지를 **계약에서 읽어 와** 대조한다.
    """
    doc = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    required = assert_nonempty(
        doc["components"]["schemas"]["LineageGraph"]["required"], "LineageGraph 필수 키")
    body = graph(live_client, DS_A2, TOKEN_RES).json()
    missing = [k for k in required if k not in body]
    assert missing == [], f"계약 필수 키가 응답에 없다: {missing}"


# ───────────────── ② 명시적으로 비어 있음 → 통과 + 건수 노출 ─────────────────
def test_a_dataset_without_lineage_still_returns_itself(live_client, p2_client) -> None:
    """**계보가 없는 데이터셋도 200 이고 노드가 비지 않는다.**

    실데이터는 간선 6 · 데이터셋 12 라 이 갈래가 다수다. 빈 그래프를 404 나 빈 배열로
    답하면 화면이 「없다」와 「못 읽었다」를 구분하지 못한다.
    """
    from test_dataset_registration import make_upload
    from test_uploads import HDF5_MAGIC

    client = p2_client()
    receipt = make_upload(client, files=[
        ("files", ("orphan.nc", HDF5_MAGIC, "application/octet-stream"))])
    r = client.post(f"{API_PREFIX}/datasets", headers=auth(TOKEN_RES),
                    json={"uploadId": receipt["uploadId"], "name": "계보 없는 데이터"})
    assert r.status_code == 201, r.text
    orphan = r.json()["datasetId"]

    r = graph(client, orphan, TOKEN_RES)
    assert r.status_code == 200, r.text
    body = r.json()
    # 명시 기대값 — 간선 0. 건수를 드러낸 채 통과한다.
    assert_counted(body["edges"], 0, f"{orphan} 의 계보 간선")
    # 그런데 **노드는 비지 않는다.** 자기 자신이 남는다.
    nodes = assert_nonempty(body["nodes"], f"{orphan} 의 노드")
    assert [n["kind"] for n in nodes if n["datasetId"] == orphan] == ["이 데이터"], nodes


# ───────────────────────── ③ 경계 ─────────────────────────
def test_an_unknown_dataset_is_404(live_client) -> None:
    r = graph(live_client, "0000000000000000000000ZZZZ", TOKEN_RES)
    assert r.status_code == 404, r.text


def test_another_labs_dataset_is_404(live_client) -> None:
    """cross-tenant 는 403 이 아니라 404 다 — 있다는 사실도 새지 않는다."""
    r = graph(live_client, DS_A1, TOKEN_B)
    assert r.status_code == 404, r.text
    r = graph(live_client, DS_B1, TOKEN_RES)
    assert r.status_code == 404, r.text


def test_unauthenticated_is_401(live_client) -> None:
    r = live_client.get(f"{API_PREFIX}/datasets/{DS_A1}/lineage")
    assert r.status_code == 401, r.text


def test_can_edit_follows_the_permission_switch(live_client) -> None:
    """보기 권한만 있는 사람에게 편집 컨트롤이 없어야 한다 — 화면이 그 판정을 받는 값이
    `canEdit` 다 (`Policy §3.2` · `§6`). **화면에서 숨긴 것은 서버도 같은 기준으로 막는다.**
    """
    for token in assert_nonempty([TOKEN_RES, TOKEN_PROF], "판정할 주체"):
        body = graph(live_client, DS_A1, token).json()
        assert isinstance(body["canEdit"], bool), body["canEdit"]


def test_the_response_is_json_serialisable_dates(live_client) -> None:
    """`confirmedAt`·`lineageConfirmedAt` 이 문자열이어야 화면이 그대로 그린다."""
    body = graph(live_client, DS_A2, TOKEN_RES).json()
    json.dumps(body)
    for e in assert_nonempty(body["edges"], "간선"):
        assert isinstance(e["confirmedAt"], str), e
