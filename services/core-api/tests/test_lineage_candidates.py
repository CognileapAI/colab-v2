"""계보 편집기가 쓰는 후보 전용 페이지 계약."""
from __future__ import annotations

from sqlalchemy import event

from conftest import DS_A1, DS_A2, DS_B1, LAB_A, TOKEN_PROF, TOKEN_RES, auth
from test_dataset_registration import make_upload, register

from colab_core.app.main import API_PREFIX


def _get(client, *, token=TOKEN_PROF, **params):
    return client.get(f"{API_PREFIX}/lineage-candidates", params=params,
                      headers=auth(token))


def test_candidate_contains_lineage_facts_and_searches_name_or_accessible_file(p2_client, sql) -> None:
    """일반 목록을 재사용해 파일명·출처·기간·Lv가 빠지는 회귀를 잡는다."""
    sql("UPDATE d3_dataset_description SET category = '기상·기후 인자' WHERE dataset_id IN (:a,:b)",
        {"a": DS_A1, "b": DS_A2})
    sql("UPDATE d3_dataset SET source_url = 'https://example.test/a1',"
        " source_downloaded_on = '2026-01-02' WHERE id = :d", {"d": DS_A1})
    sql("UPDATE d3_dataset_autometa SET period_start = '2024-01-01T00:00:00Z',"
        " period_end = NULL WHERE dataset_id = :d", {"d": DS_A1})
    client = p2_client()

    named = _get(client, q="A 강우 원자료")
    assert named.status_code == 200, named.text
    item = next(x for x in named.json()["items"] if x["datasetId"] == DS_A1)
    assert item == {
        "datasetId": DS_A1, "name": "A 강우 원자료", "fileNames": ["a1-body.csv"],
        "fileExtensions": ["csv"], "category": "기상·기후 인자",
        "period": {"start": "2024-01-01T00:00:00+00:00", "end": None},
        "source": {"label": "기상청", "url": "https://example.test/a1",
                   "downloadedOn": "2026-01-02"},
        "processingLevel": 0, "topic": "강우·강수", "bodyAccessible": True,
    }
    by_file = _get(client, q="a1-body.csv")
    assert [x["datasetId"] for x in by_file.json()["items"]] == [DS_A1]


def test_filters_are_anded_and_period_means_overlap_with_open_end(p2_client, sql) -> None:
    """OR로 섞인 필터와 끝 없는 기간·미기재 기간의 거짓 포함을 잡는다."""
    sql("UPDATE d3_dataset_description SET category = '기상·기후 인자' WHERE dataset_id = :d",
        {"d": DS_A1})
    sql("UPDATE d3_dataset_autometa SET period_start = '2024-01-01T00:00:00Z',"
        " period_end = NULL WHERE dataset_id = :d", {"d": DS_A1})
    response = _get(p2_client(), q="강우", category="기상·기후 인자",
                    periodStart="2025-01-01T00:00:00Z", periodEnd="2025-12-31T00:00:00Z")
    assert response.status_code == 200, response.text
    assert [x["datasetId"] for x in response.json()["items"]] == [DS_A1]


def test_locked_candidate_keeps_public_metadata_but_hides_body_names(p2_client) -> None:
    """잠긴 후보를 없애거나 본체 파일명을 노출하는 두 회귀를 함께 잡는다."""
    client = p2_client()
    response = _get(client, token=TOKEN_RES, q="A 강우 격자화")
    assert response.status_code == 200, response.text
    item = response.json()["items"][0]
    assert item["datasetId"] == DS_A2 and item["bodyAccessible"] is False
    assert item["fileNames"] == [] and item["fileExtensions"] == []
    assert _get(client, token=TOKEN_RES, q="a2-body.nc").json()["items"] == []
    assert all(x["datasetId"] != DS_B1 for x in _get(client).json()["items"])


def test_cursor_is_stable_without_duplicates_and_query_count_is_page_size_independent(
        p2_client, sql) -> None:
    """동률 정렬에서 후보가 중복되고 행마다 SQL이 늘어나는 회귀를 잡는다."""
    client = p2_client()
    statements: list[str] = []
    listener = lambda conn, cursor, statement, parameters, context, executemany: statements.append(statement)
    event.listen(client.app.state.engine, "before_cursor_execute", listener)
    try:
        small = _get(client, limit=1)
        small_selects = sum(s.lstrip().upper().startswith("SELECT") for s in statements)
        statements.clear()
        large = _get(client, limit=20)
        large_selects = sum(s.lstrip().upper().startswith("SELECT") for s in statements)
    finally:
        event.remove(client.app.state.engine, "before_cursor_execute", listener)
    assert small.status_code == large.status_code == 200
    assert small_selects == large_selects, (small_selects, large_selects)
    cursor = small.json()["nextCursor"]
    second = _get(client, limit=1, cursor=cursor)
    first_ids = {x["datasetId"] for x in small.json()["items"]}
    assert first_ids.isdisjoint(x["datasetId"] for x in second.json()["items"])


def test_invalid_period_and_cursor_are_client_errors(p2_client) -> None:
    """잘못된 페이지 입력을 500이나 첫 페이지로 되감는 회귀를 잡는다."""
    client = p2_client()
    assert _get(client, periodStart="not-a-date").status_code == 400
    assert _get(client, cursor="not-a-cursor").status_code == 400


def test_candidate_without_autometa_is_visible_until_a_period_filter_is_used(p2_client, sql) -> None:
    """분석 전 후보를 INNER JOIN으로 잃거나 기간 조건에서 미기재를 포함하는 회귀를 잡는다."""
    client = p2_client()
    dataset_id = register(client, make_upload(client), name="자동 메타 없는 후보").json()["datasetId"]
    sql("DELETE FROM d3_dataset_autometa WHERE dataset_id = :d", {"d": dataset_id})
    visible = _get(client, q="자동 메타 없는 후보")
    assert [x["datasetId"] for x in visible.json()["items"]] == [dataset_id]
    assert visible.json()["items"][0]["period"] is None
    filtered = _get(client, q="자동 메타 없는 후보", periodStart="2025-01-01T00:00:00Z")
    assert filtered.json()["items"] == []


def test_duplicate_names_from_different_folders_are_returned_once(p2_client, sql) -> None:
    """폴더별 동명 본체가 계약의 uniqueItems 배열을 깨는 회귀를 잡는다."""
    sql("""INSERT INTO d3_file
             (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key, relative_path)
           VALUES ('00000000000000000000000FD1', :lab, :dataset, '본체',
                   'a1-body.csv', 3, 'k/a1-duplicate', '다른폴더/a1-body.csv')""",
        {"lab": LAB_A, "dataset": DS_A1})
    response = _get(p2_client(), q="a1-body.csv")
    assert response.status_code == 200, response.text
    item = next(row for row in response.json()["items"] if row["datasetId"] == DS_A1)
    assert item["fileNames"] == ["a1-body.csv"]
    assert item["fileExtensions"] == ["csv"]


def test_topic_and_effective_level_filter_before_page_limit(p2_client, sql) -> None:
    """topic/Lv를 페이지 뒤에서 거르면 뒤 페이지의 유효 후보를 영영 놓치는 회귀를 잡는다."""
    client = p2_client()
    sql("""UPDATE d3_dataset
              SET last_modified_at = CASE id
                    WHEN :older THEN '2027-01-01T00:00:00Z'::timestamptz
                    WHEN :newer THEN '2027-01-02T00:00:00Z'::timestamptz END
            WHERE id IN (:older, :newer)""", {"older": DS_A1, "newer": DS_A2})
    # DSA2가 더 최신이지만 Lv1, DSA1은 Lv0이다. limit 뒤 Lv 필터면 빈 첫 페이지가 된다.
    level = _get(client, q="A 강우", processingLevel=0, limit=1)
    assert level.status_code == 200, level.text
    assert [row["datasetId"] for row in level.json()["items"]] == [DS_A1]

    # 최신 DSA2를 다른 주제로 바꿔 D3 topic 선필터를 잰다.
    sql("UPDATE d3_dataset_description SET topic = '식생·NDVI' WHERE dataset_id = :d",
        {"d": DS_A2})
    topic = _get(client, q="A 강우", topic="강우·강수", limit=1)
    assert topic.status_code == 200, topic.text
    assert [row["datasetId"] for row in topic.json()["items"]] == [DS_A1]

    # 사람이 고른 값은 파생 Lv보다 먼저 보이는 기존 표시 규칙이고 서버 필터도 같은 값을 쓴다.
    sql("UPDATE d3_dataset SET processing_level_user_set = 'Lv3' WHERE id = :d", {"d": DS_A1})
    human = _get(client, q="A 강우", processingLevel=3, limit=1)
    assert human.status_code == 200, human.text
    assert [(row["datasetId"], row["processingLevel"]) for row in human.json()["items"]] == [
        (DS_A1, 3)]
