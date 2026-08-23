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

# 실동작 21 개. P1 이 넷을, **P2 가 열둘을** 501 표에서 빼 왔다 (P2-EXEC §4 W2 P2-api ⑸).
P1_REAL = {"getCurrentAccount", "getLab", "listLabMembers", "saveLabMemberPermissions",
           "listDatasets", "listDatasetFacets", "getDataset", "listDatasetFiles",
           "createProject"}
#: P2 가 가져간 열둘. **뺀 자리마다 실동작 시험이 있다** — 옆 칸이 그 시험 파일이다.
P2_REAL = {
    "createUpload":                 "tests/test_uploads.py",
    "getUploadStatus":              "tests/test_uploads.py",
    "createDataset":                "tests/test_dataset_registration.py",
    "addDatasetFile":               "tests/test_dataset_files.py",
    "replaceDatasetGridFile":       "tests/test_dataset_files.py",
    "deleteDatasetGridFile":        "tests/test_dataset_files.py",
    "addLineageParent":             "tests/test_lineage_confirm.py",
    "removeLineageParent":          "tests/test_lineage_confirm.py",
    "confirmLineage":               "tests/test_lineage_confirm.py",
    "createPreviewRender":          "tests/test_preview_relay.py",
    "getPreviewRender":             "tests/test_preview_relay.py",
    "listUploadLineageSuggestions": "tests/test_lineage_suggestions.py",
}
REAL = P1_REAL | set(P2_REAL)
NO_STORE = {
    "createAccessRequest", "listPendingAccessRequests", "approveAccessRequest",
    "rejectAccessRequest", "requestVerification", "listPendingVerificationRequests",
    "downloadDataset",
    # D2c 신설 11 중 P2 가 안 가져간 둘 — 이유는 not_implemented.py 문서주석에 있다.
    "updateDataset", "linkProjectDataset",
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


def test_the_24_unimplemented_operations_are_exactly_these() -> None:
    """**목록이 줄어드는 것이 진척의 계측이다** (P2.md §2-19). 25 → 36 → 24."""
    assert len(OPERATIONS) == 24
    assert REAL & {op.operation_id for op in OPERATIONS} == set()


def test_every_op_p2_took_out_has_a_behavioural_test_behind_it() -> None:
    """뺀 자리에 시험이 없으면 501 을 200 으로 바꾼 것과 다르지 않다 (P2-EXEC §4 W2 ⑸)."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[1]
    for operation_id, test_file in sorted(P2_REAL.items()):
        path = root / test_file
        assert path.is_file(), f"{operation_id} 를 501 표에서 뺐는데 시험 파일이 없다: {test_file}"
        assert operation_id in path.read_text(encoding="utf-8"), \
            f"{test_file} 이 {operation_id} 를 부르지 않는다 — 그 자리는 증명되지 않았다."


def test_codes_are_the_two_kinds() -> None:
    no_store = {op.operation_id for op in OPERATIONS if op.code == "NOT_IMPLEMENTED_NO_STORE"}
    p1 = {op.operation_id for op in OPERATIONS if op.code == "NOT_IMPLEMENTED_P1"}
    assert no_store == NO_STORE
    assert len(p1) == 15
    assert no_store & p1 == set()


@pytest.mark.parametrize("op", OPERATIONS, ids=lambda o: o.operation_id)
def test_returns_501_with_envelope(client: TestClient, op) -> None:
    url = API_PREFIX + op.path.replace("{datasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{parentDatasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{projectId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{requestId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{uploadId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{fileId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{renderId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV")
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
                              .replace("{requestId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{uploadId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{fileId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{renderId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV")
    r = client.request(op.method, url)
    assert r.status_code == 401, "미구현이어도 인증은 건다 — 경계 밖에 오퍼레이션 목록을 열지 않는다."
    assert r.json()["code"] == "UNAUTHORIZED"


def test_404_is_never_used_for_unimplemented(client: TestClient) -> None:
    """404 는 「경계 밖」의 뜻으로 예약돼 있다 (PLAN-SoT §9-㊱)."""
    for op in OPERATIONS:
        url = API_PREFIX + op.path.replace("{datasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                                  .replace("{parentDatasetId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                                  .replace("{projectId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                                  .replace("{requestId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{uploadId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{fileId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV") \
                              .replace("{renderId}", "01ARZ3NDEKTSV4RRFFQ69G5FAV")
        r = client.request(op.method, url, headers={"Authorization": f"Bearer {TOKEN}"})
        assert r.status_code != 404
