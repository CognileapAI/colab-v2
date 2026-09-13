"""Public API golden: quality percentages must not broaden candidate matching."""
import pytest
from conftest import DS_A1, DS_A2, LAB_A, TOKEN_RES, auth
from test_search_relay import fake_ai, _ai_body, SEARCH  # noqa: F401

pytestmark = pytest.mark.search_golden


@pytest.fixture(autouse=True)
def restore_seed_descriptions(sql):
    # The shared DB cleanup restores rows, not arbitrary seed description edits.
    rows = sql("SELECT dataset_id,name,summary FROM d3_dataset_description WHERE dataset_id IN (:a,:b)",
               {"a": DS_A1, "b": DS_A2})
    try:
        yield
    finally:
        for row in rows:
            sql("UPDATE d3_dataset_description SET name=:name,summary=:summary WHERE dataset_id=:dataset_id", dict(row))


@pytest.mark.parametrize("source", ["literal", "llm"])
@pytest.mark.parametrize("phrase,noise", [
    ("결측률 0%", ["결측률", "0%"]),
    ("결측률이 0%인", ["결측률이", "0%인"]),
    ("결측률 0.5% 이하", ["결측률", "0", "5%", "이하"]),
    ("결측률0%", ["결측률0%"]),
    ("결측률이 0%인", ["결측률", "0%"]),
    ("결측률이 0%로 검증된", ["결측률이", "0%로", "검증된"]),
    ("결측률 0 %", ["결측률", "0%"]),
])
def test_quality_percentage_does_not_add_unrelated_hits(p2_client, sql, fake_ai, source, phrase, noise):
    sql("UPDATE d3_dataset_description SET name='ST검색검증20260913',summary='합성 자료' WHERE dataset_id=:id", {"id": DS_A1})
    sql("UPDATE d3_dataset_description SET name='0% 5% 무관한 자료',summary='다른 자료' WHERE dataset_id=:id", {"id": DS_A2})
    client = p2_client(ai_base_url=fake_ai["url"])
    fake_ai["body"] = _ai_body(["ST검색검증20260913", *noise], lab_id=LAB_A, source=source)
    result = client.post(SEARCH, headers=auth(TOKEN_RES), json={"query": "ST검색검증20260913 " + phrase})
    assert result.status_code == 200, result.text
    items = result.json()["items"]
    assert [item["datasetId"] for item in items] == [DS_A1]
    assert "품질" in items[0]["rationale"]
    assert "확인하지 못" in items[0]["rationale"]


@pytest.mark.parametrize("name", ["0%", "SPEI03", "2023년", "100m"])
def test_numeric_identifiers_without_quality_context_still_match(p2_client, sql, fake_ai, name):
    sql("UPDATE d3_dataset_description SET name=:name,summary='숫자 자료명' WHERE dataset_id=:id", {"id": DS_A1, "name": name})
    client = p2_client(ai_base_url=fake_ai["url"])
    fake_ai["body"] = _ai_body([name], lab_id=LAB_A, source="literal")
    result = client.post(SEARCH, headers=auth(TOKEN_RES), json={"query": name})
    assert result.status_code == 200
    assert DS_A1 in [item["datasetId"] for item in result.json()["items"]]


def test_quality_only_query_does_not_return_all_numeric_matches(p2_client, sql, fake_ai):
    sql("UPDATE d3_dataset_description SET name='0% 시험' WHERE dataset_id=:id", {"id": DS_A1})
    fake_ai["body"] = _ai_body(["결측률", "0%"], lab_id=LAB_A, source="literal")
    result = p2_client(ai_base_url=fake_ai["url"]).post(SEARCH, headers=auth(TOKEN_RES), json={"query": "결측률 0%"})
    assert result.status_code == 200
    assert result.json()["items"] == []


@pytest.mark.parametrize("query,terms,want", [
    ("강수 결측률이 0%인", ["강수", "결측률", "0%"], ["강수"]),
    ("강수 결측률이 0%로 검증된", ["강수", "0%로"], ["강수"]),
    ("강수 결측률 0 %", ["강수", "0%"], ["강수"]),
    ("0%인 실험 결측률 0%", ["0%", "실험"], ["0%", "실험"]),
])
def test_quality_normalization_preserves_outside_numeric_intent(query, terms, want):
    from colab_core.app.search_conditions import candidate_terms
    assert candidate_terms(query, terms) == want
