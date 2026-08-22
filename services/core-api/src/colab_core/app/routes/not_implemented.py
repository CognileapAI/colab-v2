"""아직 구현하지 않은 29 개 오퍼레이션 — **501 + ErrorEnvelope**.

두 종으로 나눈다 (NIGHT-20260823 §3).
  · `NOT_IMPLEMENTED_NO_STORE` — 저장처 자체가 P0 스키마에 없다(접근 요청 4 · Verified 요청 2 ·
    다운로드 1). 구현 전에 스키마가 먼저 필요하다는 사실을 코드가 말한다.
  · `NOT_IMPLEMENTED_P1` — 저장 자리는 있고 로직이 P1 이다.

**200 으로 가짜 값을 내리지 않는다.** P1 이 하나 구현할 때마다 이 표가 한 줄씩 줄고,
그 줄어듦이 진척의 계측이 된다.
"""
from __future__ import annotations

import dataclasses

from fastapi import Depends, FastAPI

from ...kernel import errors
from ...kernel.auth import Subject
from ..deps import current_subject


@dataclasses.dataclass(frozen=True)
class Op:
    operation_id: str
    method: str
    path: str
    code: str


#: 계약(`contracts/seams/fe-core.yaml`) 34 개 중 실질의 5 개를 뺀 29 개.
#: 이 표와 계약의 대조는 `tests/test_route_table.py` 가 오라클로 검사한다.
OPERATIONS: tuple[Op, ...] = (
    Op("updateLab", "PATCH", "/lab", "NOT_IMPLEMENTED_P1"),
    Op("listLabMembers", "GET", "/lab/members", "NOT_IMPLEMENTED_P1"),
    Op("saveLabMemberPermissions", "PUT", "/lab/members/permissions", "NOT_IMPLEMENTED_P1"),
    Op("listDatasetFacets", "GET", "/datasets/facets", "NOT_IMPLEMENTED_P1"),
    Op("getDataset", "GET", "/datasets/{datasetId}", "NOT_IMPLEMENTED_P1"),
    Op("deleteDataset", "DELETE", "/datasets/{datasetId}", "NOT_IMPLEMENTED_P1"),
    Op("getDatasetDeletionImpact", "GET", "/datasets/{datasetId}/deletion-impact",
       "NOT_IMPLEMENTED_P1"),
    Op("downloadDataset", "GET", "/datasets/{datasetId}/download", "NOT_IMPLEMENTED_NO_STORE"),
    Op("getDatasetLineage", "GET", "/datasets/{datasetId}/lineage", "NOT_IMPLEMENTED_P1"),
    Op("addLineageParent", "POST", "/datasets/{datasetId}/lineage/parents", "NOT_IMPLEMENTED_P1"),
    Op("removeLineageParent", "DELETE",
       "/datasets/{datasetId}/lineage/parents/{parentDatasetId}", "NOT_IMPLEMENTED_P1"),
    Op("confirmLineage", "POST", "/datasets/{datasetId}/lineage/confirmation",
       "NOT_IMPLEMENTED_P1"),
    Op("createAccessRequest", "POST", "/datasets/{datasetId}/access-requests",
       "NOT_IMPLEMENTED_NO_STORE"),
    Op("listPendingAccessRequests", "GET", "/access-requests/pending",
       "NOT_IMPLEMENTED_NO_STORE"),
    Op("approveAccessRequest", "POST", "/access-requests/{requestId}/approval",
       "NOT_IMPLEMENTED_NO_STORE"),
    Op("rejectAccessRequest", "POST", "/access-requests/{requestId}/rejection",
       "NOT_IMPLEMENTED_NO_STORE"),
    Op("requestVerification", "POST", "/datasets/{datasetId}/verification-request",
       "NOT_IMPLEMENTED_NO_STORE"),
    Op("listPendingVerificationRequests", "GET", "/verification-requests/pending",
       "NOT_IMPLEMENTED_NO_STORE"),
    Op("approveVerification", "POST", "/datasets/{datasetId}/verification",
       "NOT_IMPLEMENTED_P1"),
    Op("cancelVerification", "POST", "/datasets/{datasetId}/verification-cancellation",
       "NOT_IMPLEMENTED_P1"),
    Op("listProjects", "GET", "/projects", "NOT_IMPLEMENTED_P1"),
    Op("getProject", "GET", "/projects/{projectId}", "NOT_IMPLEMENTED_P1"),
    Op("updateProject", "PATCH", "/projects/{projectId}", "NOT_IMPLEMENTED_P1"),
    Op("deleteProject", "DELETE", "/projects/{projectId}", "NOT_IMPLEMENTED_P1"),
    Op("setProjectStatus", "PUT", "/projects/{projectId}/status", "NOT_IMPLEMENTED_P1"),
    Op("unlinkProjectDataset", "DELETE", "/projects/{projectId}/datasets/{datasetId}",
       "NOT_IMPLEMENTED_P1"),
    Op("getDashboardSummary", "GET", "/dashboard/summary", "NOT_IMPLEMENTED_P1"),
    Op("getDataMap", "GET", "/dashboard/data-map", "NOT_IMPLEMENTED_P1"),
    Op("listActivities", "GET", "/dashboard/activities", "NOT_IMPLEMENTED_P1"),
)

_MESSAGE = {
    "NOT_IMPLEMENTED_NO_STORE": "아직 저장처가 없다 — P0 스키마에 이 기록의 자리가 없다.",
    "NOT_IMPLEMENTED_P1": "아직 구현하지 않았다 — P1 범위다.",
}


def _handler(op: Op):
    # 미구현이어도 **인증은 건다.** 인증 없이 501 을 내리면 경계 밖에서 오퍼레이션 목록을 읽게 된다.
    def endpoint(_subject: Subject = Depends(current_subject)) -> None:
        raise errors.ApiError(501, op.code, _MESSAGE[op.code], {"operationId": op.operation_id})

    endpoint.__name__ = op.operation_id
    return endpoint


def register(app: FastAPI, *, prefix: str) -> None:
    for op in OPERATIONS:
        app.add_api_route(
            prefix + op.path,
            _handler(op),
            methods=[op.method],
            name=op.operation_id,
            include_in_schema=False,
        )
