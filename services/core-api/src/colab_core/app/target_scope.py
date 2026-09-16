"""Resolve existing object ownership before granting one lab's write scope."""
from ..domains import d1_identity, d2_access, d3_catalog, d5_ingestion, d6_project
from ..kernel import errors
from ..kernel.ids import Ulid
from ..kernel.scope import select_target_lab

TARGET_LAB_HEADER = "X-CoLAB-Target-Lab"
_CREATIONS = {"createProject", "createUpload", "initiateUploadTransfer", "createDataset"}
_CONTEXT = {"getLab", "updateLab", "listLabMembers", "saveLabMemberPermissions",
            "setLabDefaultGrid", "listPalettes", "getPreviewRender", "createPreviewScreenshot"}


def _references(value):
    if not isinstance(value, dict):
        return
    for key in ("datasetId", "parentDatasetId", "sourceDatasetId", "projectId", "uploadId"):
        if key in value and value[key] is not None:
            yield key, value[key]
    if isinstance(value.get("projectIds"), list):
        yield from (("projectId", ref) for ref in value["projectIds"])
    if isinstance(value.get("target"), dict):
        yield from _references(value["target"])
    if isinstance(value.get("lineageParents"), list):
        for parent in value["lineageParents"]:
            if isinstance(parent, dict) and "parentDatasetId" in parent:
                yield "parentDatasetId", parent["parentDatasetId"]


async def prepare_target_scope(request, db, subject):
    selected = request.headers.get(TARGET_LAB_HEADER)
    if not subject.operator:
        if selected is not None:
            raise errors.forbidden("대상 연구실 선택은 시스템 관리자만 할 수 있어요.")
        return
    operation = request.scope["route"].name
    if selected is not None:
        if not Ulid.is_valid(selected):
            raise errors.bad_request("대상 연구실 ID가 올바르지 않아요.")
        labs = d1_identity.list_operator_labs(db)
        if selected not in {str(row["id"]).strip() for row in labs}:
            raise errors.not_found("대상 연구실이 없어요.")
    if operation in _CREATIONS | _CONTEXT and selected is None:
        raise errors.bad_request("대상 연구실을 선택해 주세요.")
    references = list(_references(request.path_params))
    if "application/json" in request.headers.get("content-type", ""):
        references.extend(_references(await request.json()))
    labs = set()
    for kind, ref in references:
        if not Ulid.is_valid(ref):
            raise errors.bad_request("대상 ID가 올바르지 않아요.")
        if kind in {"datasetId", "parentDatasetId", "sourceDatasetId"}:
            row = d3_catalog.find_dataset_core(db, Ulid(ref))
            lab = row.lab_id if row else None
        elif kind == "projectId":
            row = d6_project.find_project(db, Ulid(ref))
            lab = row.lab_id if row else None
        else:
            lab = d5_ingestion.upload_lab(db, ref, transfer="/uploads/transfers/" in request.url.path)
        if lab is None:
            raise errors.not_found()
        labs.add(str(lab).strip())
    if "requestId" in request.path_params and operation in {"approveAccessRequest", "rejectAccessRequest"}:
        lab = d2_access.access_request_lab(db, request.path_params["requestId"])
        if lab is None:
            raise errors.not_found()
        labs.add(str(lab).strip())
    if len(labs) > 1 or (selected is not None and labs and selected not in labs):
        raise errors.bad_request("서로 다른 연구실의 자료를 함께 변경할 수 없어요.")
    target = selected or next(iter(labs), None)
    if target is not None:
        select_target_lab(db, subject, target)
    db.info["explicit_target_lab"] = selected
