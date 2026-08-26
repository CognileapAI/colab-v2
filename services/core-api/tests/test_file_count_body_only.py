"""파일 수 = **본체 파일 수**. 기준 격자 파일은 세지 않는다 (Ted 판정 2026-08-26).

데이터셋은 관측 자료의 묶음이고 기준 격자는 좌표를 붙이기 위한 부속이다. 사용자가
파일 수를 보는 목적은 「자료가 몇 개인가」이므로 요약 숫자는 본체만 센다.
파일 **목록**은 종류를 구분해 표시하므로 격자를 그대로 담는다 — 줄이는 것은 요약 숫자뿐이다.

읽는 지점은 `d3_catalog.DatasetCore.file_count` 하나로 모여 있다(실측) — 그래서 저장 열
`d3_dataset.file_count`(격자 포함 총수)는 그대로 두고 **읽는 시점에** 격자를 뺀다.

**잠긴 데이터셋은 예외다** — `body_access` RESTRICTIVE 아래서 `d3_file` 이 0행이라
격자 수를 읽을 수 없다. 그 경우 저장 열의 총수가 그대로 나간다(최대 2 초과 계상).
그 경로를 아래 `test_locked_dataset_falls_back_to_the_stored_total` 이 못 박는다.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import DS_A1, DS_A2, TOKEN_PROF, auth

from colab_core.app.main import API_PREFIX

#: 시드 실측 — `DS_A1` 은 본체 1 + 결합축 격자 1 = 저장 열 2 (seed.sql:68-72).
DS_A1_BODY = 1
DS_A1_STORED = 2
#: `DS_A2` 는 본체 1 · 격자 0 — 격자 없는 데이터셋은 값이 바뀌지 않는다.
DS_A2_BODY = 1


def _catalog_row(client: TestClient, dataset_id: str) -> dict:
    r = client.get(f"{API_PREFIX}/datasets", headers=auth(TOKEN_PROF))
    assert r.status_code == 200, r.text
    return next(x for x in r.json()["items"] if x["datasetId"] == dataset_id)


def test_catalog_row_counts_bodies_only(live_client: TestClient) -> None:
    """격자가 붙은 데이터셋의 카탈로그 `fileCount` 가 본체 수와 같다."""
    assert _catalog_row(live_client, DS_A1)["fileCount"] == DS_A1_BODY


def test_a_dataset_without_a_grid_file_is_unchanged(live_client: TestClient) -> None:
    """격자가 없으면 뺄 것이 없다 — 값이 종전 그대로다."""
    assert _catalog_row(live_client, DS_A2)["fileCount"] == DS_A2_BODY


def test_detail_files_count_counts_bodies_only(live_client: TestClient) -> None:
    """상세 `기본 정보`의 조각 수도 같은 규칙을 쓴다 — 두 화면이 갈리지 않는다."""
    r = live_client.get(f"{API_PREFIX}/datasets/{DS_A1}", headers=auth(TOKEN_PROF))
    assert r.status_code == 200, r.text
    info = r.json()["basicInfo"]
    assert info["files"]["count"] == DS_A1_BODY
    assert info["files"]["hasReferenceGridFile"] is True, \
        "요약 숫자에서 뺀 것이지 격자가 없다고 말하는 것이 아니다."


def test_catalog_and_detail_never_disagree(live_client: TestClient) -> None:
    """같은 데이터셋을 두 화면이 다른 수로 그리지 않는다 — 읽는 지점이 하나이기 때문이다."""
    r = live_client.get(f"{API_PREFIX}/datasets/{DS_A1}", headers=auth(TOKEN_PROF))
    assert r.status_code == 200
    assert (_catalog_row(live_client, DS_A1)["fileCount"]
            == r.json()["basicInfo"]["files"]["count"] == DS_A1_BODY)


# ── 음성 ────────────────────────────────────────────────────────────────────
def test_the_file_list_still_carries_the_grid_file(live_client: TestClient) -> None:
    """**목록은 줄지 않는다.** 요약 숫자만 본체 기준이다."""
    r = live_client.get(f"{API_PREFIX}/datasets/{DS_A1}/files", headers=auth(TOKEN_PROF))
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert len(items) == DS_A1_STORED
    assert [i["kind"] for i in items].count("기준 격자 파일") == 1


def test_the_stored_column_still_holds_the_total(sql) -> None:
    """저장 열은 **격자 포함 총수**로 남는다 — 트리거·드리프트 시험의 기준이 그대로다."""
    assert sql("SELECT file_count FROM d3_dataset WHERE id = :d",
               {"d": DS_A1})[0]["file_count"] == DS_A1_STORED


def test_locked_dataset_falls_back_to_the_stored_total(live_client: TestClient) -> None:
    """잠긴 데이터셋은 격자 수를 읽을 수 없다 — 저장 열의 총수가 그대로 나간다.

    `DS_A2` 는 격자가 0건이라 두 값이 같다. 이 시험이 못 박는 것은 **경로**다 —
    잠김에서도 0 이 나오지 않는다(㊼ 가 메타 열을 둔 이유).
    """
    row = _catalog_row(live_client, DS_A2)
    assert row["bodyAccessible"] is False
    assert row["fileCount"] == DS_A2_BODY and row["fileCount"] >= 1
