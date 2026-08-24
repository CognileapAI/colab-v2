"""아직 구현하지 않은 21 개 오퍼레이션 — **501 + ErrorEnvelope**.

두 종으로 나눈다 (NIGHT-20260823 §3).
  · `NOT_IMPLEMENTED_NO_STORE` — 저장처 자체가 P0 스키마에 없다(접근 요청 4 · Verified 요청 2 ·
    다운로드 1). 구현 전에 스키마가 먼저 필요하다는 사실을 코드가 말한다.
  · `NOT_IMPLEMENTED_P1` — 저장 자리는 있고 로직이 P1 이다.

**200 으로 가짜 값을 내리지 않는다.** 하나 구현할 때마다 이 표가 한 줄씩 줄고,
그 줄어듦이 진척의 계측이 된다. **뺀 자리마다 실동작 시험이 있어야 한다** (`P2.md §2-19`).

P2 가 열둘을 가져갔다 (36 → 24) —
  업로드 6 `createUpload` `getUploadStatus` `createDataset` `addDatasetFile`
          `replaceDatasetGridFile` `deleteDatasetGridFile`
  계보 3  `addLineageParent` `removeLineageParent` `confirmLineage`
  중계 3  `createPreviewRender` `getPreviewRender` `listUploadLineageSuggestions`

**남긴 것과 이유** (`P2-EXEC §4 W2 P2-api`)
  · `updateDataset` — 상세 편집이라 P2 화면(S-04·S-08) 범위 밖이다.
  · `getDatasetLineage` — 그래프를 그리는 함수는 P2 가 만들었지만(`routes/lineage.py`),
    이 **조회 op 자체는 P1 배정**이라 범위를 늘리지 않는다 (`CLAUDE.md §5`).

**S1 의 `P5` 레인이 셋을 가져갔다 (24 → 21)** — `listProjects` · `getProject` ·
`linkProjectDataset`. 앞의 둘은 S-02·S-02b 화면 본체이고, 셋째는 `S1-PLAN.md §4.2` 의
P5 행이 「여기서 열린다」고 지목한 op 이다. **셋 다 실동작 시험이 뒤에 있다**
(`tests/test_project_screens.py`) — 그 규칙이 없으면 501 을 200 으로 바꾼 것과 다르지 않다.

**남은 프로젝트 op 넷은 그대로 501 이다** — `updateProject` · `deleteProject` ·
`setProjectStatus` · `unlinkProjectDataset`. 넷 다 `NOT_IMPLEMENTED_P1` 배정이라
P5 가 범위를 늘려 가져오지 않았다 (`CLAUDE.md §5` 범위 늘리기 금지).
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


#: 계약(`contracts/seams/fe-core.yaml`) **46** 개 중 실동작 **25** 개를 뺀 **21** 개.
#: 25 → 36(D2c 신설 11) → **24**(P2 구현 12) → **24 유지**(S1 W3 — `searchDatasets` 를
#: 신설과 동시에 구현했으므로 표에 더할 행이 없다. `〈80〉-㉯ 5` · `〈74〉-㉱`)
#: → **21**(S1 W5 `P5` — 프로젝트 목록·상세·연결 셋).
#: 이 표와 계약의 대조는 `tests/test_route_table.py` 가 오라클로 검사한다.
OPERATIONS: tuple[Op, ...] = (
    Op("updateLab", "PATCH", "/lab", "NOT_IMPLEMENTED_P1"),
    Op("deleteDataset", "DELETE", "/datasets/{datasetId}", "NOT_IMPLEMENTED_P1"),
    Op("getDatasetDeletionImpact", "GET", "/datasets/{datasetId}/deletion-impact",
       "NOT_IMPLEMENTED_P1"),
    Op("downloadDataset", "GET", "/datasets/{datasetId}/download", "NOT_IMPLEMENTED_NO_STORE"),
    Op("getDatasetLineage", "GET", "/datasets/{datasetId}/lineage", "NOT_IMPLEMENTED_P1"),
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
    Op("updateProject", "PATCH", "/projects/{projectId}", "NOT_IMPLEMENTED_P1"),
    Op("deleteProject", "DELETE", "/projects/{projectId}", "NOT_IMPLEMENTED_P1"),
    Op("setProjectStatus", "PUT", "/projects/{projectId}/status", "NOT_IMPLEMENTED_P1"),
    Op("unlinkProjectDataset", "DELETE", "/projects/{projectId}/datasets/{datasetId}",
       "NOT_IMPLEMENTED_P1"),
    Op("getDashboardSummary", "GET", "/dashboard/summary", "NOT_IMPLEMENTED_P1"),
    Op("getDataMap", "GET", "/dashboard/data-map", "NOT_IMPLEMENTED_P1"),
    Op("listActivities", "GET", "/dashboard/activities", "NOT_IMPLEMENTED_P1"),
    # ── D2c 신설 11 중 P2 가 안 가져간 둘 (윗 문단이 이유를 적었다) ──
    Op("updateDataset", "PATCH", "/datasets/{datasetId}", "NOT_IMPLEMENTED_NO_STORE"),
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
