"""계보 관계의 **출처 레이블 셋** — `ai` · `manual` · `processed` (`PLAN-SoT §9 〈205〉` · 10 차 동결 해제).

종전 두 한국어 값(`AI 제안을 사람이 확인` · `사람이 직접 연결`)을 영어 단어로 통일하고,
가공으로 자동 생성된 관계를 뜻하는 `processed` 를 **값만** 신설했다.

⚠ **`ai` 의 뜻은 「AI 가 제안하고 사람이 확인한 것」이지 「AI 가 만든 것」이 아니다.**
이 레포의 불변 규칙은 그대로다 — **AI 는 계보를 쓰지 않는다** (`CLAUDE.md §3-2` ·
게이트 `ai-no-lineage-write` 가 계약·코드·체인 세 층에서 강제). 레이블이 짧아 그 뜻을
못 담으므로 값의 뜻은 `contracts/schemas/common.json#/$defs/LineageOrigin` 의
`description` 이 한 줄로 못 박는다.

⚠ **`processed` 를 만드는 경로는 아직 없다.** 만드는 주체(데이터 프로세스 `DP-1`)가
`after_stage2` 다. 이 회차는 **값만 열고 쓰는 쪽을 만들지 않았다** — 그래서 아래 마지막
시험은 API 가 아니라 **DB 에 직접 넣어** 「저장 가능한가」만 본다.
"""
from __future__ import annotations

import json
import pathlib

import pytest
from conftest import ACC_A_RES, DS_A1, DS_A2, LAB_A, TOKEN_RES, auth

from colab_core.app.main import API_PREFIX

REPO = pathlib.Path(__file__).resolve().parents[3]
OLD_VALUES = ("AI 제안을 사람이 확인", "사람이 직접 연결")


# ───────────────────────── 계약 ─────────────────────────
def test_the_contract_enumerates_the_three_english_labels() -> None:
    common = json.loads((REPO / "contracts" / "schemas" / "common.json").read_text("utf-8"))
    origin = common["$defs"]["LineageOrigin"]
    assert origin["enum"] == ["ai", "manual", "processed"], origin["enum"]


def test_the_contract_spells_out_what_ai_means() -> None:
    """레이블만 보고 「AI 가 만들었다」로 읽히지 않게 뜻을 계약 산문이 못 박는다."""
    common = json.loads((REPO / "contracts" / "schemas" / "common.json").read_text("utf-8"))
    description = common["$defs"]["LineageOrigin"]["description"]
    assert "제안" in description and "사람이 확인" in description, description
    assert "CLAUDE.md §3-2" in description


# ───────────────────────── 코드 ─────────────────────────
@pytest.mark.parametrize("old", OLD_VALUES)
def test_the_domain_rejects_the_old_korean_values(old: str) -> None:
    from colab_core.domains import d4_lineage
    import inspect
    source = inspect.getsource(d4_lineage.add_parent)
    assert old not in source, f"옛 값이 도메인에 남아 있다: {old}"
    assert '"ai", "manual", "processed"' in source or \
           "'ai', 'manual', 'processed'" in source, source


def test_the_manual_add_records_manual(p2_client, sql) -> None:
    """상세 화면의 수동 추가는 언제나 `manual` 이다 — 요청이 고르지 않는다.

    **새 데이터셋을 만들어 붙인다** — 시드는 `DSA2 ← DSA1` 을 이미 들고 있어
    같은 쌍을 다시 붙이면 유니크 제약에 걸린다(그 갈래는 이 시험의 관심이 아니다).
    """
    from test_dataset_registration import make_upload
    from test_uploads import HDF5_MAGIC
    client = p2_client()
    receipt = make_upload(client, files=[
        ("files", ("manual.nc", HDF5_MAGIC, "application/octet-stream"))])
    r = client.post(f"{API_PREFIX}/datasets", headers=auth(TOKEN_RES),
                    json={"uploadId": receipt["uploadId"], "name": "수동 추가 대상"})
    assert r.status_code == 201, r.text
    child = r.json()["datasetId"]

    r = client.post(f"{API_PREFIX}/datasets/{child}/lineage/parents",
                    json={"parentDatasetId": DS_A1}, headers=auth(TOKEN_RES))
    assert r.status_code == 201, r.text
    rows = sql("SELECT origin FROM d4_lineage_edge WHERE child_dataset_id = :c",
               {"c": child})
    assert [row["origin"] for row in rows] == ["manual"], rows


def test_the_seeded_edges_were_migrated_to_manual(sql) -> None:
    """시드가 심은 관계가 새 값으로 들어가 있다 — 옛 값 잔존 0."""
    rows = sql("SELECT origin, count(*) AS n FROM d4_lineage_edge GROUP BY origin")
    assert rows, "계보 간선이 하나도 없다 — 시드가 안 들어갔다."
    for row in rows:
        assert row["origin"] in ("ai", "manual", "processed"), row


@pytest.mark.parametrize("old", OLD_VALUES)
def test_the_registration_rejects_the_old_korean_values(p2_client, old: str) -> None:
    """등록 요청이 옛 값을 실으면 400 이다."""
    from test_dataset_registration import make_upload
    from test_uploads import HDF5_MAGIC
    client = p2_client()
    receipt = make_upload(client, files=[
        ("files", ("old.nc", HDF5_MAGIC, "application/octet-stream"))])
    r = client.post(f"{API_PREFIX}/datasets", headers=auth(TOKEN_RES), json={
        "uploadId": receipt["uploadId"], "name": f"옛 값 {old}",
        "lineageParents": [{"parentDatasetId": DS_A1, "origin": old}]})
    assert r.status_code == 400, r.text


def test_the_registration_accepts_ai(p2_client, sql) -> None:
    """새 값 `ai` 는 받아들여진다."""
    from test_dataset_registration import make_upload
    from test_uploads import HDF5_MAGIC
    client = p2_client()
    receipt = make_upload(client, files=[
        ("files", ("ai.nc", HDF5_MAGIC, "application/octet-stream"))])
    r = client.post(f"{API_PREFIX}/datasets", headers=auth(TOKEN_RES), json={
        "uploadId": receipt["uploadId"], "name": "새 값 ai",
        "lineageParents": [{"parentDatasetId": DS_A1, "origin": "ai"}]})
    assert r.status_code == 201, r.text
    child = r.json()["datasetId"]
    rows = sql("SELECT origin FROM d4_lineage_edge WHERE child_dataset_id = :c", {"c": child})
    assert [row["origin"] for row in rows] == ["ai"], rows


# ───────────────────────── DB ─────────────────────────
@pytest.mark.parametrize("old", OLD_VALUES)
def test_the_check_constraint_rejects_the_old_values(sql, old: str) -> None:
    """DB 의 `CHECK` 가 옛 값을 거절한다 — 마이그레이션이 실제로 좁혔다는 증거."""
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        sql("""INSERT INTO d4_lineage_edge
                 (id, lab_id, child_dataset_id, parent_dataset_id, parent_role,
                  method, origin, confirmed_by_account_id)
               VALUES ('00000000000000000000OLD001', :lab, :child, :parent,
                       '주입력', NULL, :origin, :acc)""",
            {"lab": LAB_A, "child": DS_A1, "parent": DS_A2,
             "origin": old, "acc": ACC_A_RES})


def test_processed_is_storable_even_though_nothing_produces_it(sql) -> None:
    """`processed` 가 **실제로 저장 가능**하다.

    ⚠ 이것을 만드는 **생산 경로는 이 회차에 만들지 않았다** — `DP-1` 이 `after_stage2` 다.
    그래서 API 가 아니라 DB 에 직접 넣어 값 집합만 증명한다.
    """
    rows = sql("""INSERT INTO d4_lineage_edge
                    (id, lab_id, child_dataset_id, parent_dataset_id, parent_role,
                     method, origin, confirmed_by_account_id)
                  VALUES ('00000000000000000000PRC001', :lab, :child, :parent,
                          '주입력', '가공', 'processed', :acc)
                  RETURNING origin""",
               {"lab": LAB_A, "child": DS_A1, "parent": DS_A2, "acc": ACC_A_RES})
    assert rows == [{"origin": "processed"}]


# ───────────────────────── 잔존 ─────────────────────────
def test_no_old_value_survives_in_the_contract_or_the_declared_schema() -> None:
    for relative in ("contracts/schemas/common.json", "contracts/seams/fe-core.yaml",
                     "db/platform/schema.sql"):
        text = (REPO / relative).read_text("utf-8")
        for old in OLD_VALUES:
            assert old not in text, f"{relative} 에 옛 값이 남아 있다: {old}"
