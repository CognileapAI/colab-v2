"""D4 — 계보 확정 3 op: `addLineageParent` · `removeLineageParent` · `confirmLineage`.

**여기가 되돌릴 수 없는 것이 만들어지는 자리다.** 규칙 넷을 코드가 지킨다.

  ① **사람이 확인한 것만 저장된다.** D10 이 이 파일에 닿는 경로가 없다 (`CLAUDE.md §3-2`).
     `addLineageParent` 는 만들어진 경로를 요청에서 받지 않고 **`manual` 로 못 박는다**
     (`LineageParentCreate` 산문 — 「요청이 고르지 않는다」).
  ② **순환·자기부모는 들어가지 않는다** (`DR-15`). 판정은 `d4_lineage.would_create_cycle`.
  ③ **Lv 는 파생이다 — 저장하지 않는다** (`P2.md §2-4`·`§2-6` · `PLAN-SoT §9-⑳`).
     `(주입력 부모 중 최대 Lv) + 1`, **보조입력은 계산에서 뺀다**, 부모 없으면 Lv0.
  ④ **`확인` 은 `마지막 수정` 을 밀지 않는다** — 계보 확정일만 갱신한다.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from fastapi import APIRouter, Body, Depends, Response
from sqlalchemy.orm import Session

from ...domains import d2_access, d3_catalog, d4_lineage, d6_project, d8_insight
from ...kernel import errors
from ...kernel.auth import Subject
from ...kernel.ids import Ulid
from ..deps import current_subject, scoped_db

router = APIRouter()

#: 상세 화면의 수동 추가는 **언제나 이 경로**다. 요청이 고르지 않는다.
#: 값 셋의 뜻은 `contracts/schemas/common.json#/$defs/LineageOrigin` 이 정본이다 —
#: `ai` 는 **AI 가 제안하고 사람이 확인한 것**이지 「AI 가 만든 것」이 아니다 (`CLAUDE.md §3-2`).
MANUAL_ORIGIN = "manual"
_ALLOWED_PARENT_FIELDS = {"parentDatasetId", "parentRole", "method"}


def _iso(value: Any) -> Any:
    return value.astimezone(dt.timezone.utc).isoformat() if isinstance(value, dt.datetime) else value


def _require_edit(db: Session, subject: Subject) -> None:
    role = d2_access.role_of(db, subject.account_id)
    permissions = d2_access.permissions_of(db, subject.account_id, role)
    if not permissions.get("업로드·편집"):
        raise errors.forbidden("`업로드·편집` 스위치가 꺼져 있다.")


def lineage_graph(db: Session, subject: Subject, dataset_id: Ulid) -> dict:
    """`LineageGraph` 한 벌. 세 op 이 **같은 함수**로 답한다 — 같은 사실을 세 모양으로
    그리면 어느 것이 맞는지 아무도 모른다.

    **확정된 관계만 그린다.** 제안 상태가 이 응답에 없는 것이 D10→D4 쓰기 경로 부재의
    표현이다 (`getDatasetLineage` 산문).
    """
    core = d3_catalog.find_dataset_core(db, dataset_id)
    if core is None:
        raise errors.not_found()
    datasetId = str(dataset_id)
    edges = d4_lineage.edges_of(db, dataset_id)

    # 그래프에 세울 이웃들. 이름·Lv 는 각 데이터셋의 사실이라 다시 읽는다.
    neighbour_ids = {e["parent_dataset_id"] for e in edges if e["child_dataset_id"] == datasetId}
    child_ids = {e["child_dataset_id"] for e in edges if e["parent_dataset_id"] == datasetId}
    all_ids = [Ulid(i) for i in ({datasetId} | neighbour_ids | child_ids)]
    summaries = d4_lineage.LineageSummaryAdapter(db).summaries(all_ids)
    access = d2_access.DatasetAccessAdapter(db).dataset_access(all_ids)

    def node(node_id: str, kind: str) -> dict:
        c = d3_catalog.find_dataset_core(db, Ulid(node_id))
        acc = access.get(node_id)
        return {
            "kind": kind,
            "datasetId": node_id,
            "name": "(지워진 데이터)" if c is None else c.name,
            "processingLevel": (None if c is None
                                else d3_catalog.processing_level(summaries.get(node_id))),
            "verified": False if acc is None else acc.verified,
            # 지워진 데이터셋은 묘비다 — **사라지지 않는다.** 지운 데이터가 부모였다면
            # 자식의 출처가 끊긴다 (schema.sql d3_dataset 주석).
            "navigable": c is not None,
            "bodyAccessible": False if acc is None else acc.body_accessible,
            "deletedAt": None,
        }

    nodes = [node(datasetId, "이 데이터")]
    nodes += [node(i, "가공 전") for i in sorted(neighbour_ids)]
    nodes += [node(i, "파생") for i in sorted(child_ids)]
    if core.source_label:
        # **`원천` 은 데이터셋이 아니라 표기다** — `datasetId` 가 null 이고 눌리지 않는다.
        nodes.append({"kind": "원천", "datasetId": None, "name": core.source_label,
                      "processingLevel": None, "verified": False, "navigable": False,
                      "bodyAccessible": False, "deletedAt": None})

    permissions = d2_access.permissions_of(
        db, subject.account_id, d2_access.role_of(db, subject.account_id))
    return {
        "datasetId": datasetId,
        "lineageState": d3_catalog.lineage_state(core, summaries.get(datasetId)),
        "lineageConfirmedAt": _iso(core.lineage_confirmed_at),
        "unknownParents": d4_lineage.is_unknown(db, dataset_id),
        "nodes": nodes,
        "edges": [
            {
                "childDatasetId": e["child_dataset_id"],
                "parentDatasetId": e["parent_dataset_id"],
                "parentRole": e["parent_role"],
                "method": e["method"],
                "origin": e["origin"],
                "confirmedBy": {"accountId": e["confirmed_by_account_id"],
                                "name": e["confirmed_by_name"]},
                "confirmedAt": _iso(e["confirmed_at"]),
            }
            for e in edges
        ],
        "projectUseCount": len(d6_project.ProjectLinkAdapter(db).uses_of(dataset_id)),
        "canEdit": bool(permissions.get("업로드·편집", False)),
    }


@router.get("/datasets/{datasetId}/lineage", name="getDatasetLineage")
def get_dataset_lineage(datasetId: str,
                        subject: Subject = Depends(current_subject),
                        db: Session = Depends(scoped_db)) -> dict:
    """계보 그래프 조회 — **화면이 쓰기 없이 그래프를 얻는 유일한 자리** (WU `P3`).

    **그리는 함수는 새로 만들지 않았다.** 세 쓰기 op 이 이미 `lineage_graph()` 로 답하고
    있었고, 없던 것은 그 함수를 부를 GET 하나였다 (`not_implemented.py` 의 「이 조회 op
    자체는 P1 배정」 — `P1` 은 닫혔는데 op 은 501 로 남아 있었다). **같은 함수가 답한다** —
    조회와 쓰기가 다른 그래프를 그리면 어느 쪽이 맞는지 아무도 모른다.

    **없는 데이터셋은 404 다** — 다른 연구실의 것도 404 이고, 403 이 아니다
    (`find_dataset_core` 가 RLS 아래에서 읽으므로 있다는 사실 자체가 새지 않는다).
    **계보가 0 건이어도 200 이다** — 노드는 자기 자신이 남는다. 「없다」와 「못 읽었다」를
    같은 응답으로 답하지 않는다 (`CLAUDE.md §4`).
    """
    if not Ulid.is_valid(datasetId):
        raise errors.not_found()
    return lineage_graph(db, subject, Ulid(datasetId))


@router.post("/datasets/{datasetId}/lineage/parents", name="addLineageParent", status_code=201)
def add_lineage_parent(datasetId: str, body: dict = Body(...),
                       subject: Subject = Depends(current_subject),
                       db: Session = Depends(scoped_db)) -> dict:
    """부모 관계 추가. **여기서 붙인 관계는 언제나 `manual` 이다.**

    파생(자식) 관계는 자식 상세에서 고친다 — 이 엔드포인트로 자식을 붙이지 않는다.
    """
    if not Ulid.is_valid(datasetId):
        raise errors.bad_request("datasetId 가 정규 ID 가 아니다.")
    dataset_id = Ulid(datasetId)
    _require_edit(db, subject)
    if not d3_catalog.dataset_exists(db, dataset_id):
        raise errors.not_found()

    unknown = set(body) - _ALLOWED_PARENT_FIELDS
    if unknown:
        raise errors.bad_request(f"계약에 없는 필드다: {sorted(unknown)}")
    parent_ref = body.get("parentDatasetId")
    if not Ulid.is_valid(parent_ref):
        raise errors.bad_request("parentDatasetId 가 정규 ID 가 아니다.")
    parent_id = Ulid(parent_ref)
    role = body.get("parentRole") or "주입력"
    if role not in ("주입력", "보조입력"):
        raise errors.bad_request("parentRole 은 `주입력` 또는 `보조입력` 이다.")
    if not d3_catalog.dataset_exists(db, parent_id):
        # 경계 밖이면 RLS 가 이미 행을 지웠다 — 404 로 답한다(존재를 누설하지 않는다).
        raise errors.not_found()

    try:
        d4_lineage.add_parent(db, child_id=dataset_id, parent_id=parent_id, parent_role=role,
                              method=body.get("method"), origin=MANUAL_ORIGIN,
                              confirmed_by=subject.account_id)
    except d4_lineage.LineageCycle as e:
        # **되돌릴 수 없는 오염을 삽입 전에 막는다** (`DR-15`).
        raise errors.conflict(str(e)) from None
    return lineage_graph(db, subject, dataset_id)


@router.delete("/datasets/{datasetId}/lineage/parents/{parentDatasetId}",
               name="removeLineageParent", status_code=204)
def remove_lineage_parent(datasetId: str, parentDatasetId: str,
                          subject: Subject = Depends(current_subject),
                          db: Session = Depends(scoped_db)) -> Response:
    """관계 한 쌍만 지운다 — **데이터셋은 지워지지 않는다.**"""
    if not Ulid.is_valid(datasetId) or not Ulid.is_valid(parentDatasetId):
        raise errors.bad_request("정규 ID 가 아니다.")
    dataset_id = Ulid(datasetId)
    _require_edit(db, subject)
    if not d3_catalog.dataset_exists(db, dataset_id):
        raise errors.not_found()
    if not d4_lineage.remove_parent(db, child_id=dataset_id, parent_id=Ulid(parentDatasetId)):
        raise errors.not_found("그런 관계가 없다.")
    return Response(status_code=204)


@router.post("/datasets/{datasetId}/lineage/confirmation", name="confirmLineage")
def confirm_lineage(datasetId: str,
                    subject: Subject = Depends(current_subject),
                    db: Session = Depends(scoped_db)) -> dict:
    """사람이 다시 확인하면 **계보 확정일이 갱신되고 `이후 수정됨` 표시가 사라진다.**

    계보 상태는 이 호출의 **결과로 계산될 뿐** 요청이 값을 싣지 않는다.
    """
    if not Ulid.is_valid(datasetId):
        raise errors.bad_request("datasetId 가 정규 ID 가 아니다.")
    dataset_id = Ulid(datasetId)
    _require_edit(db, subject)
    if not d3_catalog.confirm_lineage(db, dataset_id):
        raise errors.not_found()
    # **계보 고침이 최근 활동을 만든다** (계약 `listActivities` 산문 · WU-P7).
    d8_insight.record_activity(db, actor_id=subject.account_id,
                               action=d8_insight.ACTION_LINEAGE_CONFIRMED,
                               target_kind="데이터셋", target_id=dataset_id)
    return lineage_graph(db, subject, dataset_id)
