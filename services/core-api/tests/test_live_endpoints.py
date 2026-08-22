"""실질의 5 개 오퍼레이션을 **진짜 DB 에 붙여** 확인한다.

DB 가 없으면 skip 이 아니라 **fail** 이다 — 그 skip 이 정확히 v1 의 실패였다 (P0.md §6).
환경변수 —
  COLAB_CORE_TEST_DATABASE_URL   앱 롤(NOBYPASSRLS·비소유자)로 접속하는 URL
  COLAB_CORE_TEST_SUBJECTS_FILE  심어 둔 토큰 표 (P-17)
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from colab_core.app.main import API_PREFIX, create_app
from colab_core.kernel.config import Settings

LAB_A = "0000000000000000000000000A"
DS_A1 = "0000000000000000000000DSA1"   # 열림 · 파일 2 · Verified · 원천 표기 있음
DS_A2 = "0000000000000000000000DSA2"   # 잠김 · 파일 1 · DSA1 의 자식
DS_B1 = "0000000000000000000000DSB1"   # 다른 연구실


@pytest.fixture(scope="module")
def client() -> TestClient:
    url = os.environ.get("COLAB_CORE_TEST_DATABASE_URL")
    subjects = os.environ.get("COLAB_CORE_TEST_SUBJECTS_FILE")
    if not url or not subjects:
        pytest.fail("COLAB_CORE_TEST_DATABASE_URL · COLAB_CORE_TEST_SUBJECTS_FILE 가 없다. "
                    "DB 를 못 붙인 것은 통과가 아니다 (CLAUDE.md §4).")
    app = create_app(Settings(database_url=url, subjects_file=subjects))
    return TestClient(app)


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_get_current_account(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/me", headers=auth("a1-res-token"))
    assert r.status_code == 200
    body = r.json()
    assert body["labId"] == LAB_A and body["role"] == "연구원"
    assert set(body["permissions"]) == {"업로드·편집", "프로젝트 생성", "승인 위임", "연구실 설정"}
    assert body["permissions"]["연구실 설정"] is False


def test_professor_switches_are_all_on(client: TestClient) -> None:
    body = client.get(f"{API_PREFIX}/me", headers=auth("a1-prof-token")).json()
    assert all(body["permissions"].values()), "교수는 네 스위치가 항상 켜져 내려간다 (P-5·P-6)."


def test_get_lab_is_scoped(client: TestClient) -> None:
    a = client.get(f"{API_PREFIX}/lab", headers=auth("a1-prof-token")).json()
    b = client.get(f"{API_PREFIX}/lab", headers=auth("b1-prof-token")).json()
    assert a["labId"] != b["labId"]
    assert a["memberCount"] == 2 and b["memberCount"] == 1, "구성원 수가 경계를 넘어 세어졌다."


def test_list_datasets_never_crosses_the_boundary(client: TestClient) -> None:
    a = client.get(f"{API_PREFIX}/datasets", headers=auth("a1-prof-token")).json()
    ids = {row["datasetId"] for row in a["items"]}
    assert ids == {DS_A1, DS_A2}
    assert DS_B1 not in ids, "다른 연구실 데이터가 보였다 — 스코프 커널이 뚫렸다."
    assert a["totalCount"] == 2 and a["nextCursor"] is None


def test_derived_values_are_computed(client: TestClient) -> None:
    rows = {r["datasetId"]: r for r in
            client.get(f"{API_PREFIX}/datasets", headers=auth("a1-prof-token")).json()["items"]}
    assert rows[DS_A1]["processingLevel"] == 0        # 원자료
    assert rows[DS_A2]["processingLevel"] == 1        # 주입력 부모의 최대 + 1
    assert rows[DS_A1]["lineageState"] == "원천"       # 부모 없음 + 원천 표기
    assert rows[DS_A2]["lineageState"] == "확정"       # 부모 있음 + 확정일이 최신
    assert rows[DS_A1]["verified"] is True
    assert rows[DS_A2]["accessState"] == "잠김"
    assert rows[DS_A2]["bodyAccessible"] is False
    assert rows[DS_A2]["projects"]["representative"]["name"] == "A 논문"


def test_locked_dataset_stays_in_the_list(client: TestClient) -> None:
    """잠긴 데이터는 목록에서 **사라지지 않는다** (P-13)."""
    rows = client.get(f"{API_PREFIX}/datasets", headers=auth("a1-prof-token")).json()["items"]
    assert any(r["datasetId"] == DS_A2 and r["name"] for r in rows)


def test_list_files_open_and_locked(client: TestClient) -> None:
    ok = client.get(f"{API_PREFIX}/datasets/{DS_A1}/files", headers=auth("a1-prof-token"))
    assert ok.status_code == 200
    assert {i["kind"] for i in ok.json()["items"]} == {"본체", "기준 격자 파일"}

    locked = client.get(f"{API_PREFIX}/datasets/{DS_A2}/files", headers=auth("a1-prof-token"))
    assert locked.status_code == 403, "본체는 두 번째 층(body_access)이 막는다 (P-34)."


def test_cross_lab_dataset_is_404_not_403(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/datasets/{DS_B1}/files", headers=auth("a1-prof-token"))
    assert r.status_code == 404, "경계 밖은 존재를 알리지 않는다 (P-9·P-10)."


def test_create_project_writes_into_the_own_lab_only(client: TestClient) -> None:
    r = client.post(f"{API_PREFIX}/projects", headers=auth("a1-res-token"),
                    json={"type": "논문", "name": "a1 가 만든 논문", "period": {"start": "2026-03", "end": None}})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "진행 중" and body["period"]["start"] == "2026-03"
    listed = client.get(f"{API_PREFIX}/datasets", headers=auth("b1-prof-token")).json()
    assert listed["totalCount"] == 1, "쓴 것이 다른 연구실로 새지 않았는지 함께 본다."


def test_unknown_subject_is_401(client: TestClient) -> None:
    assert client.get(f"{API_PREFIX}/me", headers=auth("no-such-token")).status_code == 401
    assert client.get(f"{API_PREFIX}/me").status_code == 401


def test_lab_id_cannot_be_injected(client: TestClient) -> None:
    """labId 를 헤더·쿼리로 주입하는 경로가 없다 (P-9·P-10)."""
    r = client.get(f"{API_PREFIX}/datasets?labId={LAB_A}", headers=auth("b1-prof-token"))
    assert r.status_code == 200
    assert {row["datasetId"] for row in r.json()["items"]} == {DS_B1}
