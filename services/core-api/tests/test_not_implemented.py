"""오라클 — 어떤 오퍼레이션이 501 을 내는가, 그리고 **어떤 code 로** 내는가.

이 표가 없으면 나중에 누군가 501 을 가짜 200 으로 바꿔도 아무도 모른다.
"""
from __future__ import annotations

import json
import pathlib
import tempfile

import pytest
from fastapi.testclient import TestClient

from colab_core.app.main import API_PREFIX, create_app
from colab_core.app.routes.not_implemented import OPERATIONS
from colab_core.kernel.config import Settings

# 실동작 9 개. P1 이 넷을 501 표에서 빼 왔다 (P1.md §2-⑤).
REAL = {"getCurrentAccount", "getLab", "listLabMembers", "saveLabMemberPermissions",
        "listDatasets", "listDatasetFacets", "getDataset", "listDatasetFiles", "createProject"}
NO_STORE = {
    "createAccessRequest", "listPendingAccessRequests", "approveAccessRequest",
    "rejectAccessRequest", "requestVerification", "listPendingVerificationRequests",
    "downloadDataset",
}
TOKEN = "a1-test-token"
ACCOUNT = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
LAB = "01ARZ3NDEKTSV4RRFFQ69G5FAW"


@pytest.fixture(scope="module")
def client() -> TestClient:
    tmp = pathlib.Path(tempfile.mkdtemp()) / "subjects.json"
    tmp.write_text(json.dumps({TOKEN: {"accountId": ACCOUNT, "labId": LAB}}), encoding="utf-8")
    app = create_app(Settings(database_url="postgresql+psycopg://unused/unused",
                              subjects_file=str(tmp)))
    return TestClient(app, raise_server_exceptions=False)


def test_the_25_unimplemented_operations_are_exactly_these() -> None:
    assert len(OPERATIONS) == 25
    assert REAL & {op.operation_id for op in OPERATIONS} == set()


def test_codes_are_the_two_kinds() -> None:
    no_store = {op.operation_id for op in OPERATIONS if op.code == "NOT_IMPLEMENTED_NO_STORE"}
    p1 = {op.operation_id for op in OPERATIONS if op.code == "NOT_IMPLEMENTED_P1"}
    assert no_store == NO_STORE
    assert len(p1) == 18
    assert no_store & p1 == set()


@pytest.mark.parametrize("op", OPERATIONS, ids=lambda o: o.operation_id)
def test_returns_501_with_envelope(client: TestClient, op) -> None:
    url = API_PREFIX + op.path.replace("{datasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{parentDatasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{projectId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{requestId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV")
    r = client.request(op.method, url, headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 501, f"{op.operation_id} 가 501 이 아니다 — 가짜 200 은 거짓말이다."
    body = r.json()
    assert body["code"] == op.code
    assert body["message"]
    assert body["details"]["operationId"] == op.operation_id


@pytest.mark.parametrize("op", OPERATIONS, ids=lambda o: o.operation_id)
def test_requires_subject(client: TestClient, op) -> None:
    url = API_PREFIX + op.path.replace("{datasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{parentDatasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{projectId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{requestId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV")
    r = client.request(op.method, url)
    assert r.status_code == 401, "미구현이어도 인증은 건다 — 경계 밖에 오퍼레이션 목록을 열지 않는다."
    assert r.json()["code"] == "UNAUTHORIZED"


def test_404_is_never_used_for_unimplemented(client: TestClient) -> None:
    """404 는 「경계 밖」의 뜻으로 예약돼 있다 (PLAN-SoT §9-㊱)."""
    for op in OPERATIONS:
        url = API_PREFIX + op.path.replace("{datasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                                  .replace("{parentDatasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                                  .replace("{projectId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                                  .replace("{requestId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV")
        r = client.request(op.method, url, headers={"Authorization": f"Bearer {TOKEN}"})
        assert r.status_code != 404
