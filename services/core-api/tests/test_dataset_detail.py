"""`getDataset` (S-05 상단) 실동작 — 진짜 DB 에 붙는다.

정본 —
  · `Policy_데이터셋_상세 §5`  기본 정보 아홉 칸 · `파일` 칸은 조각 수 + 용량 합계
  · `Policy_데이터셋_상세 §7`  묘비는 상세 화면이 없다(404) · 잠김(허용 안 됨)은 헤더 요약까지
  · `Policy_데이터셋_상세 §8`  헤더는 줄마다 하나 · 헤더 우측 한 자리가 상태 × 보는 사람으로 갈린다
  · `Policy_승인_처리 §8`      상세 헤더 액션 3분기 · 잠긴 상세
  · `PLAN-SoT §9-㊼`           조각 수는 메타다 — `d3_file` 을 세지 않는다
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from colab_core.app.main import API_PREFIX, create_app
from colab_core.kernel.config import Settings

DS_A1 = "0000000000000000000000DSA1"   # 열림 · 파일 2 · Verified · 원천 표기
DS_A2 = "0000000000000000000000DSA2"   # 잠김 · 파일 1 · DSA1 의 자식 · PRJA 에 쓰임
DS_B1 = "0000000000000000000000DSB1"   # 다른 연구실
ACC_A_PROF = "00000000000000000000000AP1"
ACC_A_RES = "000000000000000000000000A1"


@pytest.fixture(scope="module")
def client() -> TestClient:
    url = os.environ.get("COLAB_CORE_TEST_DATABASE_URL")
    subjects = os.environ.get("COLAB_CORE_TEST_SUBJECTS_FILE")
    if not url or not subjects:
        pytest.fail("COLAB_CORE_TEST_DATABASE_URL · COLAB_CORE_TEST_SUBJECTS_FILE 가 없다.")
    return TestClient(create_app(Settings(database_url=url, subjects_file=subjects)))


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def get(client: TestClient, dataset_id: str, token: str):
    return client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(token))


# ── 헤더 ────────────────────────────────────────────────────────────────────
def test_header_says_one_thing_per_line(client: TestClient) -> None:
    r = get(client, DS_A1, "a1-prof-token")
    assert r.status_code == 200
    b = r.json()
    assert b["datasetId"] == DS_A1
    assert b["name"] == "A 강우 원자료"
    assert b["summary"] == "관측 원자료"
    assert b["topic"] == "강우·강수"
    assert b["processingLevel"] == 0
    assert b["lineageState"] == "원천"
    assert b["accessState"] == "열림"
    assert b["bodyAccessible"] is True


def test_the_response_has_exactly_the_contract_keys(client: TestClient) -> None:
    b = get(client, DS_A1, "a1-prof-token").json()
    assert set(b) == {
        "datasetId", "name", "fileName", "summary", "topic", "processingLevel",
        "lineageState", "verification", "accessState", "bodyAccessible",
        "accessRequestPending", "uploadedAt", "lastModifiedAt", "lineageConfirmedAt",
        "basicInfo", "projects", "actions",
    }


def test_verification_record_carries_the_approver(client: TestClient) -> None:
    v = get(client, DS_A1, "a1-prof-token").json()["verification"]
    assert v["verified"] is True
    assert v["approver"] == {"accountId": ACC_A_PROF, "name": "A 교수"}
    assert v["approvedAt"].startswith("2026-01-03")
    assert v["cancelledBy"] is None and v["cancelledAt"] is None
    assert v["cancellationReason"] is None


# ── 기본 정보 아홉 칸 ────────────────────────────────────────────────────────
def test_basic_info_is_the_nine_cells(client: TestClient) -> None:
    info = get(client, DS_A1, "a1-prof-token").json()["basicInfo"]
    assert set(info) == {"variables", "crs", "period", "grid", "format",
                         "files", "sourceLabel", "owner", "uploader"}
    assert info["variables"] == ["강우량"]
    assert info["crs"] == "EPSG:5179"
    assert info["format"] == "CSV"
    assert info["period"] is None and info["grid"] is None
    assert info["sourceLabel"] == "기상청"
    assert info["owner"] == {"accountId": ACC_A_PROF, "name": "A 교수"}
    assert info["uploader"] == {"accountId": ACC_A_RES, "name": "A 연구원"}


def test_files_cell_says_count_and_total_size_only(client: TestClient) -> None:
    files = get(client, DS_A1, "a1-prof-token").json()["basicInfo"]["files"]
    assert set(files) == {"count", "totalSizeBytes", "hasReferenceGridFile"}
    # 메타 열 `file_count`(격자 포함 2) 에서 격자를 뺀 **본체 수 1** 이다
    # (㊼ · Ted 판정 2026-08-26 — `test_file_count_body_only.py`).
    assert files["count"] == 1
    assert files["totalSizeBytes"] == 100
    assert files["hasReferenceGridFile"] is True


def test_file_count_comes_from_the_meta_column_not_from_counting_rows(client: TestClient) -> None:
    """`d3_file` 을 `count(*)` 하면 잠긴 데이터에서 0 이 나온다 (㊼ · 실측)."""
    from sqlalchemy import text

    engine = client.app.state.engine
    with engine.begin() as conn:
        conn.execute(text("SELECT set_config('app.current_lab', :l, true)"),
                     {"l": "0000000000000000000000000A"})
        conn.execute(text("SELECT set_config('app.current_account', :a, true)"),
                     {"a": ACC_A_PROF})
        counted = conn.execute(
            text("SELECT count(*) FROM d3_file WHERE dataset_id = :d"), {"d": DS_A2}
        ).scalar_one()
    assert counted == 0, "본체 정책 아래에서 잠긴 데이터의 파일 행은 0 이어야 한다."
    # 그런데도 조각 수는 1 이다 — 그것이 메타 층의 존재 이유다.
    from colab_core.kernel.ids import Ulid  # noqa: F401
    body = get(client, DS_A2, "a1-prof-token").json()
    assert body["bodyAccessible"] is False
    assert body["basicInfo"] is None      # 잠긴 상세는 기본 정보를 통째로 비운다 (P1.md §2-④)


# ── 잠김 ────────────────────────────────────────────────────────────────────
def test_locked_dataset_is_200_with_header_only(client: TestClient) -> None:
    """403 을 쓰면 접근 요청 흐름이 죽는다 (P-13 · Policy_승인_처리 §8)."""
    r = get(client, DS_A2, "a1-prof-token")
    assert r.status_code == 200
    b = r.json()
    assert b["name"] == "A 강우 격자화"
    assert b["summary"] == "격자화 결과"
    assert b["topic"] == "강우·강수"
    assert b["processingLevel"] == 1
    assert b["lineageState"] == "확정"
    assert b["accessState"] == "잠김"
    assert b["bodyAccessible"] is False
    assert b["basicInfo"] is None
    assert b["projects"] is None


def test_locked_dataset_offers_access_request_and_nothing_else(client: TestClient) -> None:
    a = get(client, DS_A2, "a1-prof-token").json()["actions"]
    assert a["canRequestAccess"] is True
    assert a["canDownload"] is False
    assert a["canEditLineage"] is False


# ── 활용 프로젝트 ────────────────────────────────────────────────────────────
def test_open_dataset_with_no_project_gets_an_empty_list(client: TestClient) -> None:
    assert get(client, DS_A1, "a1-prof-token").json()["projects"] == []


def test_project_use_carries_its_own_usage_note(client: TestClient) -> None:
    """의미 문장은 연결마다 따로다 (Policy_데이터셋_상세 §5). 잠기지 않은 눈으로 본다."""
    from sqlalchemy import text

    engine = client.app.state.engine
    with engine.begin() as conn:                     # 허용 목록에 잠깐 넣는다
        conn.execute(text("SELECT set_config('app.current_lab', :l, true)"),
                     {"l": "0000000000000000000000000A"})
        conn.execute(text("SELECT set_config('app.current_account', :a, true)"),
                     {"a": ACC_A_PROF})
        conn.execute(text("""
            INSERT INTO d2_dataset_access_grant
              (id, lab_id, dataset_id, grantee_account_id, approver_account_id, expires_at)
            VALUES ('0000000000000000000000GRT1', '0000000000000000000000000A', :d,
                    :a, :a, now() + interval '1 day')
        """), {"d": DS_A2, "a": ACC_A_PROF})
    try:
        b = get(client, DS_A2, "a1-prof-token").json()
        assert b["bodyAccessible"] is True
        assert b["basicInfo"] is not None
        assert b["basicInfo"]["files"]["count"] == 1
        assert b["projects"] == [{
            "projectId": "0000000000000000000000PRJA",
            "name": "A 논문",
            "type": "논문",
            "period": {"start": "2026-03", "end": None},
            "usageNote": "격자 입력으로 썼다",
        }]
    finally:
        with engine.begin() as conn:
            conn.execute(text("SELECT set_config('app.current_lab', :l, true)"),
                         {"l": "0000000000000000000000000A"})
            conn.execute(text("SELECT set_config('app.current_account', :a, true)"),
                         {"a": ACC_A_PROF})
            conn.execute(text("DELETE FROM d2_dataset_access_grant WHERE id = :i"),
                         {"i": "0000000000000000000000GRT1"})


# ── 헤더 우측 한 자리 (Policy_승인_처리 §8) ──────────────────────────────────
def test_uploader_of_an_unverified_dataset_can_request_verification(client: TestClient) -> None:
    """① 미승인 + 올린 사람·소유자 → `✓ 승인 요청` (Policy_승인_처리 §8).

    잠긴 상세에는 접근 요청 자리 하나뿐이므로(같은 표), 올린 사람을 허용 목록에 넣고 본다.
    """
    from sqlalchemy import text

    engine = client.app.state.engine

    def _scope(conn):
        conn.execute(text("SELECT set_config('app.current_lab', :l, true)"),
                     {"l": "0000000000000000000000000A"})
        conn.execute(text("SELECT set_config('app.current_account', :a, true)"),
                     {"a": ACC_A_PROF})

    with engine.begin() as conn:
        _scope(conn)
        conn.execute(text("""
            INSERT INTO d2_dataset_access_grant
              (id, lab_id, dataset_id, grantee_account_id, approver_account_id, expires_at)
            VALUES ('0000000000000000000000GRT2', '0000000000000000000000000A', :d,
                    :g, :a, now() + interval '1 day')
        """), {"d": DS_A2, "g": ACC_A_RES, "a": ACC_A_PROF})
    try:
        a = get(client, DS_A2, "a1-res-token").json()["actions"]
        assert a["canRequestVerification"] is True
        assert a["canCancelVerification"] is False, "Verified 는 교수만이다 (E-01 §2)."
        assert a["canApproveVerification"] is False, "검토 대기의 저장처가 아직 없다 (P6)."
    finally:
        with engine.begin() as conn:
            _scope(conn)
            conn.execute(text("DELETE FROM d2_dataset_access_grant WHERE id = :i"),
                         {"i": "0000000000000000000000GRT2"})


def test_a_locked_detail_offers_only_the_access_request(client: TestClient) -> None:
    """잠긴 상세는 `이름·요약·헤더 태그` + 잠김 안내 + 접근 요청뿐이다 (Policy_승인_처리 §8).

    올린 사람이어도 본체에 닿지 못하면 승인 요청 자리는 서지 않는다.
    """
    a = get(client, DS_A2, "a1-res-token").json()["actions"]
    assert a["canRequestAccess"] is True
    assert a["canRequestVerification"] is False
    assert a["canDownload"] is False
    assert a["canEditLineage"] is False


def test_professor_of_a_verified_dataset_can_cancel(client: TestClient) -> None:
    a = get(client, DS_A1, "a1-prof-token").json()["actions"]
    assert a["canCancelVerification"] is True, "③ 승인됨 + 교수 → `⋯` 더보기 → `승인 취소`"
    assert a["canRequestVerification"] is False, "이미 승인된 건에는 요청 자리가 없다."


def test_a_plain_researcher_sees_no_verification_action(client: TestClient) -> None:
    a = get(client, DS_A1, "a1-res-token").json()["actions"]
    assert a["canCancelVerification"] is False, "Verified 는 교수만이다 (E-01 §2)."
    assert a["canRequestVerification"] is False, "이미 승인된 건이다."


def test_delete_is_for_the_owner_or_the_professor(client: TestClient) -> None:
    assert get(client, DS_A1, "a1-prof-token").json()["actions"]["canDelete"] is True
    assert get(client, DS_A1, "a1-res-token").json()["actions"]["canDelete"] is False


def test_lineage_edit_follows_the_upload_switch(client: TestClient) -> None:
    assert get(client, DS_A1, "a1-res-token").json()["actions"]["canEditLineage"] is True
    assert get(client, DS_A1, "a1-prof-token").json()["actions"]["canEditLineage"] is True


# ── 경계 ────────────────────────────────────────────────────────────────────
def test_other_lab_dataset_is_404_not_403(client: TestClient) -> None:
    r = get(client, DS_B1, "a1-prof-token")
    assert r.status_code == 404, "경계 밖은 존재를 알리지 않는다 (P-9·P-10)."
    assert r.json()["code"] == "NOT_FOUND"


def test_tombstone_has_no_detail_screen(client: TestClient) -> None:
    """삭제된 데이터셋은 상세 화면이 없다 (Policy_데이터셋_상세 §7)."""
    from sqlalchemy import text

    engine = client.app.state.engine

    def _scope(conn):
        conn.execute(text("SELECT set_config('app.current_lab', :l, true)"),
                     {"l": "0000000000000000000000000A"})
        conn.execute(text("SELECT set_config('app.current_account', :a, true)"),
                     {"a": ACC_A_PROF})

    with engine.begin() as conn:
        _scope(conn)
        conn.execute(text("UPDATE d3_dataset SET deleted_at = now(), "
                          "deleted_by_account_id = :a WHERE id = :d"),
                     {"a": ACC_A_PROF, "d": DS_A1})
    try:
        assert get(client, DS_A1, "a1-prof-token").status_code == 404
    finally:
        with engine.begin() as conn:
            _scope(conn)
            conn.execute(text("UPDATE d3_dataset SET deleted_at = NULL, "
                              "deleted_by_account_id = NULL WHERE id = :d"), {"d": DS_A1})


def test_bad_id_is_400(client: TestClient) -> None:
    assert get(client, "not-a-ulid", "a1-prof-token").status_code == 400


def test_requires_a_subject(client: TestClient) -> None:
    assert client.get(f"{API_PREFIX}/datasets/{DS_A1}").status_code == 401
