"""`listDatasetFacets` 실동작 — 열 메뉴의 값별 건수.

정본 `Policy_데이터_찾기 §5 값별 건수` —
  · 조건을 걸 수 있는 열은 **다섯**(주제 · Level · 업로더 · 계보 · Verified)
  · **다른 열에 걸린 조건을 먼저 적용한 뒤 센다**
  · 0건인 값도 **사라지지 않는다** — 흐리게 두어 빈 결과로 보내지 않는다
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from colab_core.app.main import API_PREFIX, create_app
from colab_core.kernel.config import Settings

ACC_A_RES = "000000000000000000000000A1"
FILTERABLE = ["주제", "Level", "업로더", "계보", "Verified"]


@pytest.fixture(scope="module")
def client() -> TestClient:
    url = os.environ.get("COLAB_CORE_TEST_DATABASE_URL")
    subjects = os.environ.get("COLAB_CORE_TEST_SUBJECTS_FILE")
    if not url or not subjects:
        pytest.fail("COLAB_CORE_TEST_DATABASE_URL · COLAB_CORE_TEST_SUBJECTS_FILE 가 없다.")
    return TestClient(create_app(Settings(database_url=url, subjects_file=subjects)))


def facets(client: TestClient, token: str = "a1-prof-token", query: str = "") -> dict:
    r = client.get(f"{API_PREFIX}/datasets/facets{query}",
                   headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    return {c["column"]: {(v["value"] if not isinstance(v["value"], bool) else v["value"]): v["count"]
                          for v in c["values"]}
            for c in r.json()["columns"]}


def test_only_the_five_filterable_columns_are_listed(client: TestClient) -> None:
    assert list(facets(client)) == FILTERABLE, "나머지 세 열은 정렬만 갖는다 (§5 카탈로그 조건)."


def test_counts_without_any_condition(client: TestClient) -> None:
    f = facets(client)
    assert f["주제"] == {"강우·강수": 2}
    assert f["Level"] == {0: 1, 1: 1}
    assert f["업로더"] == {ACC_A_RES: 2}
    assert f["Verified"] == {True: 1, False: 1}


def test_the_four_lineage_states_never_disappear(client: TestClient) -> None:
    """0건인 값을 지우면 그 조건이 화면에서 사라진다 — 흐리게 둔다 (§5)."""
    f = facets(client)
    assert f["계보"] == {"확정": 1, "확인 필요": 0, "기록 없음": 0, "원천": 1}


def test_other_columns_conditions_are_applied_first(client: TestClient) -> None:
    f = facets(client, query="?verified=true")
    assert f["주제"] == {"강우·강수": 1}
    assert f["Level"] == {0: 1, 1: 0}
    assert f["계보"] == {"확정": 0, "확인 필요": 0, "기록 없음": 0, "원천": 1}


def test_a_column_does_not_count_its_own_condition(client: TestClient) -> None:
    """자기 조건까지 걸면 고른 값만 남아 다른 값으로 갈아탈 수가 없다 (§5)."""
    f = facets(client, query="?verified=true")
    assert f["Verified"] == {True: 1, False: 1}


def test_facets_stay_inside_the_lab_boundary(client: TestClient) -> None:
    b = facets(client, token="b1-prof-token")
    assert b["주제"] == {"토지피복·LULC": 1}
    assert "강우·강수" not in b["주제"], "다른 연구실 값이 셈에 섞였다."


def test_bad_filter_value_is_400(client: TestClient) -> None:
    r = client.get(f"{API_PREFIX}/datasets/facets?lineageState=없는값",
                   headers={"Authorization": "Bearer a1-prof-token"})
    assert r.status_code == 400


def test_requires_a_subject(client: TestClient) -> None:
    assert client.get(f"{API_PREFIX}/datasets/facets").status_code == 401
