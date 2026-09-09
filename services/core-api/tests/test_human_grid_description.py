"""사람이 적은 격자 설명과 자동 분석값의 분리 계약."""
from __future__ import annotations

from conftest import ACC_A_RES, LAB_A, TOKEN_RES, auth
from test_dataset_registration import make_upload, register

from colab_core.app.main import API_PREFIX


def _detail(client, dataset_id: str) -> dict:
    response = client.get(f"{API_PREFIX}/datasets/{dataset_id}", headers=auth(TOKEN_RES))
    assert response.status_code == 200, response.text
    return response.json()["basicInfo"]


def test_create_and_update_keep_human_grid_description_separate_from_autometa(
        p2_client, sql) -> None:
    """사람 문장을 자동 grid 열에 써서 재분석 때 유실하는 회귀를 잡는다."""
    client = p2_client()
    response = register(client, make_upload(client), gridDescription="0.1도 규칙 격자")
    assert response.status_code == 201, response.text
    dataset_id = response.json()["datasetId"]
    assert _detail(client, dataset_id)["gridDescription"] == "0.1도 규칙 격자"

    sql("UPDATE d3_dataset_autometa SET grid = '3600 × 1800 자동 분석' WHERE dataset_id = :d",
        {"d": dataset_id})
    changed = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                           json={"gridDescription": "한반도 Lambert 격자"},
                           headers=auth(TOKEN_RES))
    assert changed.status_code == 200, changed.text
    info = changed.json()["basicInfo"]
    assert info["gridDescription"] == "한반도 Lambert 격자"
    assert info["gridDescriptionAutomatic"] == "3600 × 1800 자동 분석"
    assert info["grid"] == "3600 × 1800 자동 분석"


def test_clearing_or_reanalysing_falls_back_without_destroying_the_other_value(
        p2_client, sql, session_factory) -> None:
    """null 삭제와 `_CLEAR_GRID_META`가 서로의 설명까지 지우는 회귀를 잡는다."""
    from colab_core.domains import d3_catalog
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import apply_scope

    client = p2_client()
    dataset_id = register(client, make_upload(client), gridDescription="사람이 확인한 격자").json()[
        "datasetId"]
    sql("UPDATE d3_dataset_autometa SET grid = '자동 분석 격자' WHERE dataset_id = :d",
        {"d": dataset_id})
    cleared = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                           json={"gridDescription": None}, headers=auth(TOKEN_RES))
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["basicInfo"]["gridDescription"] is None
    assert cleared.json()["basicInfo"]["gridDescriptionAutomatic"] == "자동 분석 격자"

    assert client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                        json={"gridDescription": "재분석에도 남을 설명"},
                        headers=auth(TOKEN_RES)).status_code == 200
    session = session_factory()
    try:
        session.begin()
        apply_scope(session, Subject(account_id=Ulid(ACC_A_RES), lab_id=Ulid(LAB_A)))
        d3_catalog.recompute_grid_metadata(session, Ulid(dataset_id))
        session.commit()
    finally:
        session.close()
    info = _detail(client, dataset_id)
    assert info["gridDescription"] == "재분석에도 남을 설명"
    assert info["gridDescriptionAutomatic"] is None


def test_grid_description_rejects_non_string_blank_and_over_limit(p2_client) -> None:
    """형상 오류를 DB 500이나 공백 저장으로 흘리는 회귀를 잡는다."""
    client = p2_client()
    dataset_id = register(client, make_upload(client)).json()["datasetId"]
    for value in ({"text": "격자"}, "   ", "가" * 1001):
        response = client.patch(f"{API_PREFIX}/datasets/{dataset_id}",
                                json={"gridDescription": value}, headers=auth(TOKEN_RES))
        assert response.status_code == 400, response.text
