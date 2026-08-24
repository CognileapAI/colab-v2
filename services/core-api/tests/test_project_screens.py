"""S-02 프로젝트 목록 · S-02b 상세 · `linkProjectDataset` — WU-P5 의 실동작 시험.

오라클 = `E-05_프로젝트/documents/Policy_프로젝트.md` v2.0 · 계약 `contracts/seams/fe-core.yaml`.

**이 파일이 501 표에서 셋을 빼는 근거다** (`test_not_implemented.py` 의 「뺀 자리마다 실동작
시험이 있다」 규칙). 셋 = `listProjects` · `getProject` · `linkProjectDataset`.

지키는 것 셋 —
  · **연구실 경계는 요청에 실리지 않는다** (`CLAUDE.md §3-5` · P-9·P-10). 음성 시험이 그것을 잰다.
  · **잠긴 데이터셋은 소속 데이터셋 표에서 사라지지 않는다** (P-13·P-34). 이름은 보이고
    본체 쪽 사실만 `bodyAccessible: false` 로 닫힌다.
  · **D6 은 D3 테이블을 직접 읽지 않는다** (`CLAUDE.md §3-1`). 조립은 app 이 한다.
"""
from __future__ import annotations

import pytest

from conftest import (ACC_A_RES, DS_A1, DS_A2, DS_B1, LAB_A, PRJ_B, TOKEN_B, TOKEN_PROF,
                      TOKEN_RES, auth)

from colab_core.app.main import API_PREFIX

PRJ_A = "0000000000000000000000PRJA"
ABSENT = "0000000000000000000000ZZZZ"


@pytest.fixture()
def client(p2_client):
    return p2_client()


# ═══════════════════════════════════════════════════════════════════════════
# S-02 목록
# ═══════════════════════════════════════════════════════════════════════════

def test_list_projects_returns_the_contract_envelope(client) -> None:
    r = client.get(f"{API_PREFIX}/projects", headers=auth(TOKEN_RES))
    assert r.status_code == 200, "listProjects 가 아직 501 이다."
    body = r.json()
    assert set(body) == {"items", "totalCount", "nextCursor"}
    row = next(x for x in body["items"] if x["projectId"] == PRJ_A)
    assert set(row) == {"projectId", "name", "type", "status", "period", "description",
                        "datasetCount", "verifiedCount", "unknownLineageCount"}
    assert row["name"] == "A 논문" and row["type"] == "논문" and row["status"] == "진행 중"
    assert row["period"] == {"start": "2026-03", "end": None}, \
        "기간은 연·월까지이고 진행 중이면 종료가 비어 있다 (Policy_프로젝트 §5)."


def test_list_project_metrics_are_counted_from_the_linked_datasets(client) -> None:
    """지표 타일 세 칸 — 데이터셋 · 승인 · 기록 없음 (`§5` 카드 구성).

    시드의 `PRJA` 에는 `DSA2` 한 건만 붙어 있다. `DSA2` 는 Verified 가 꺼져 있고
    확정된 부모가 있어 계보 상태는 `확정` 이다 → 1 · 0 · 0.
    """
    body = client.get(f"{API_PREFIX}/projects", headers=auth(TOKEN_RES)).json()
    row = next(x for x in body["items"] if x["projectId"] == PRJ_A)
    assert (row["datasetCount"], row["verifiedCount"], row["unknownLineageCount"]) == (1, 0, 0)


def test_list_projects_filters_by_status_and_type(client) -> None:
    assert client.get(f"{API_PREFIX}/projects", params={"status": "닫힘"},
                      headers=auth(TOKEN_RES)).json()["totalCount"] == 0
    assert client.get(f"{API_PREFIX}/projects", params={"type": "논문"},
                      headers=auth(TOKEN_RES)).json()["totalCount"] == 1
    assert client.get(f"{API_PREFIX}/projects", params={"type": "국가과제"},
                      headers=auth(TOKEN_RES)).json()["totalCount"] == 0


def test_list_projects_rejects_values_outside_the_two_enums(client) -> None:
    """값 집합의 정본은 계약이다. 밖의 값을 200 으로 받으면 규칙이 없는 것과 같다."""
    for params in ({"status": "정리 중"}, {"type": "보고서"}, {"sort": "이름 순"}):
        r = client.get(f"{API_PREFIX}/projects", params=params, headers=auth(TOKEN_RES))
        assert r.status_code == 400, f"{params} 를 받아 버렸다."


def test_list_projects_never_crosses_the_lab_boundary(client) -> None:
    """**경계는 요청에 실리지 않는다** — 인증 주체에서 서버가 넣는다 (P-9·P-10).

    A 의 토큰으로는 B 의 프로젝트가 **어떤 조건으로도** 나타나지 않는다.
    """
    a = client.get(f"{API_PREFIX}/projects", params={"status": "전체"},
                   headers=auth(TOKEN_PROF)).json()
    b = client.get(f"{API_PREFIX}/projects", params={"status": "전체"},
                   headers=auth(TOKEN_B)).json()
    assert {x["projectId"] for x in a["items"]} == {PRJ_A}
    assert {x["projectId"] for x in b["items"]} == {PRJ_B}
    assert PRJ_B not in {x["projectId"] for x in a["items"]}, \
        "다른 연구실 프로젝트가 보였다 — 스코프 커널이 뚫렸다."


def test_list_projects_requires_a_subject(client) -> None:
    assert client.get(f"{API_PREFIX}/projects").status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# S-02b 상세
# ═══════════════════════════════════════════════════════════════════════════

def test_get_project_returns_the_detail_and_all_its_datasets(client) -> None:
    r = client.get(f"{API_PREFIX}/projects/{PRJ_A}", headers=auth(TOKEN_RES))
    assert r.status_code == 200, "getProject 가 아직 501 이다."
    body = r.json()
    assert set(body) == {"projectId", "name", "type", "status", "period", "description",
                         "link", "datasets", "canManage"}
    assert body["canManage"] is True, "연구원 A1 은 `프로젝트 생성` 이 켜져 있다 (seed.sql)."
    assert [d["datasetId"] for d in body["datasets"]] == [DS_A2]
    row = body["datasets"][0]
    assert set(row) == {"datasetId", "name", "fileCount", "processingLevel", "period",
                        "lineageState", "verified", "accessState", "bodyAccessible",
                        "usageNote"}
    assert row["usageNote"] == "격자 입력으로 썼다", "의미 문장은 연결마다 따로다 (§5)."
    assert row["lineageState"] == "확정" and row["processingLevel"] == 1


def test_a_locked_dataset_stays_in_the_project_table(client) -> None:
    """**잠긴 데이터는 숨기지 않는다** (P-13·P-34).

    `DSA2` 는 잠김이다. 표에서 빼면 접근 요청 흐름 자체가 사라진다 — 없는 데이터는
    요청할 수 없다. 이름·조각 수는 메타라 그대로 보이고, 닫히는 것은 본체뿐이다.
    """
    body = client.get(f"{API_PREFIX}/projects/{PRJ_A}", headers=auth(TOKEN_RES)).json()
    row = next(d for d in body["datasets"] if d["datasetId"] == DS_A2)
    assert row["accessState"] == "잠김" and row["bodyAccessible"] is False
    assert row["name"] == "A 강우 격자화", "잠겼다고 이름까지 지우면 P-13 이 깨진다."
    assert row["fileCount"] == 1, "조각 수는 메타 열에서 온다 — 본체를 세지 않는다 (㊼)."


def test_get_project_across_the_boundary_is_a_404(client) -> None:
    """경계 밖은 **존재를 알리지 않는 404** 다. 403 을 내면 그 자체가 존재의 누설이다."""
    assert client.get(f"{API_PREFIX}/projects/{PRJ_B}",
                      headers=auth(TOKEN_PROF)).status_code == 404
    assert client.get(f"{API_PREFIX}/projects/{ABSENT}",
                      headers=auth(TOKEN_PROF)).status_code == 404


def test_get_project_rejects_a_non_ulid(client) -> None:
    assert client.get(f"{API_PREFIX}/projects/not-a-ulid",
                      headers=auth(TOKEN_RES)).status_code == 400


# ═══════════════════════════════════════════════════════════════════════════
# `linkProjectDataset` — 이 op 이 여기서 열린다 (S1-PLAN §4.2 P5 행)
# ═══════════════════════════════════════════════════════════════════════════

def test_link_creates_the_connection_with_its_usage_note(client, sql) -> None:
    r = client.put(f"{API_PREFIX}/projects/{PRJ_A}/datasets/{DS_A1}",
                   json={"usageNote": "검증 자료로 썼다"}, headers=auth(TOKEN_RES))
    assert r.status_code == 204, "linkProjectDataset 가 아직 501 이다."
    rows = sql("SELECT dataset_id, usage_note FROM d6_project_dataset "
               "WHERE project_id = :p AND dataset_id = :d", {"p": PRJ_A, "d": DS_A1})
    assert len(rows) == 1 and rows[0]["usage_note"] == "검증 자료로 썼다"


def test_link_is_idempotent_and_edits_the_note(client, sql) -> None:
    """이미 있는 연결이면 `usageNote` 를 고친다 — 멱등 PUT (계약 산문)."""
    for note in ("첫 문장", "고친 문장"):
        assert client.put(f"{API_PREFIX}/projects/{PRJ_A}/datasets/{DS_A1}",
                          json={"usageNote": note}, headers=auth(TOKEN_RES)).status_code == 204
    rows = sql("SELECT usage_note FROM d6_project_dataset "
               "WHERE project_id = :p AND dataset_id = :d", {"p": PRJ_A, "d": DS_A1})
    assert len(rows) == 1 and rows[0]["usage_note"] == "고친 문장"


def test_link_accepts_an_explicit_null_note(client, sql) -> None:
    """`usageNote` 는 required 다 — 아직 못 적었으면 **null 로 명시**한다 (계약 산문)."""
    assert client.put(f"{API_PREFIX}/projects/{PRJ_A}/datasets/{DS_A1}",
                      json={"usageNote": None}, headers=auth(TOKEN_RES)).status_code == 204
    rows = sql("SELECT usage_note FROM d6_project_dataset "
               "WHERE project_id = :p AND dataset_id = :d", {"p": PRJ_A, "d": DS_A1})
    assert rows[0]["usage_note"] is None


def test_link_shows_up_in_the_detail_and_moves_the_metrics(client) -> None:
    client.put(f"{API_PREFIX}/projects/{PRJ_A}/datasets/{DS_A1}",
               json={"usageNote": "검증 자료로 썼다"}, headers=auth(TOKEN_RES))
    body = client.get(f"{API_PREFIX}/projects/{PRJ_A}", headers=auth(TOKEN_RES)).json()
    assert {d["datasetId"] for d in body["datasets"]} == {DS_A1, DS_A2}
    added = next(d for d in body["datasets"] if d["datasetId"] == DS_A1)
    assert added["bodyAccessible"] is True and added["verified"] is True
    assert added["lineageState"] == "원천" and added["fileCount"] == 2

    row = next(x for x in client.get(f"{API_PREFIX}/projects",
                                     headers=auth(TOKEN_RES)).json()["items"]
               if x["projectId"] == PRJ_A)
    assert (row["datasetCount"], row["verifiedCount"]) == (2, 1)


def test_link_rejects_a_body_the_contract_does_not_have(client) -> None:
    for body in ({}, {"usageNote": "x", "role": "주입력"}, {"usageNote": 3}):
        r = client.put(f"{API_PREFIX}/projects/{PRJ_A}/datasets/{DS_A1}",
                       json=body, headers=auth(TOKEN_RES))
        assert r.status_code == 400, f"{body} 를 받아 버렸다."


def test_link_to_an_absent_dataset_is_a_400(client) -> None:
    """`dataset_id` 는 bare 컬럼이라 DB 는 유령 연결도 받는다 — **존재 확인은 부르는 쪽**이다."""
    r = client.put(f"{API_PREFIX}/projects/{PRJ_A}/datasets/{ABSENT}",
                   json={"usageNote": None}, headers=auth(TOKEN_RES))
    assert r.status_code == 400


def test_link_never_crosses_the_boundary_in_either_direction(client, sql) -> None:
    """경계는 권한보다 바깥이다 (P-10) — 스위치가 다 켜진 교수라도 남의 것은 못 만진다."""
    assert client.put(f"{API_PREFIX}/projects/{PRJ_B}/datasets/{DS_A1}",
                      json={"usageNote": None}, headers=auth(TOKEN_PROF)).status_code == 404
    assert client.put(f"{API_PREFIX}/projects/{PRJ_A}/datasets/{DS_B1}",
                      json={"usageNote": None}, headers=auth(TOKEN_PROF)).status_code == 400
    assert sql("SELECT 1 AS x FROM d6_project_dataset WHERE dataset_id = :d",
               {"d": DS_B1}) == [], "경계를 넘은 연결이 남았다."


def test_link_is_hidden_from_a_member_without_the_switch(client, sql) -> None:
    """화면에서 숨긴 것을 서버가 같은 기준으로 막는다 (P-11·P-12 · `Policy_프로젝트 §6`)."""
    sql("UPDATE d2_permission_switch SET enabled = false "
        "WHERE account_id = :a AND switch = '프로젝트 생성'", {"a": ACC_A_RES})
    r = client.put(f"{API_PREFIX}/projects/{PRJ_A}/datasets/{DS_A1}",
                   json={"usageNote": None}, headers=auth(TOKEN_RES))
    assert r.status_code == 403
    assert client.get(f"{API_PREFIX}/projects/{PRJ_A}",
                      headers=auth(TOKEN_RES)).json()["canManage"] is False
    assert client.get(f"{API_PREFIX}/projects/{PRJ_A}",
                      headers=auth(TOKEN_RES)).status_code == 200, \
        "조회에는 권한 차이가 없다 (§6) — 스위치가 꺼져도 목록·상세는 본다."


def test_link_requires_a_subject(client) -> None:
    assert client.put(f"{API_PREFIX}/projects/{PRJ_A}/datasets/{DS_A1}",
                      json={"usageNote": None}).status_code == 401


def test_lab_a_never_sees_lab_b_link_notes(client) -> None:
    """`usageNote` 도 경계 안이다 — B 의 문장이 A 의 어떤 응답에도 실리지 않는다."""
    body = client.get(f"{API_PREFIX}/projects/{PRJ_A}", headers=auth(TOKEN_PROF)).json()
    assert "수질 분석에 썼다" not in repr(body)
    assert LAB_A  # 경계값은 시드 상수에서 온다 — 시험이 다시 적지 않는다
