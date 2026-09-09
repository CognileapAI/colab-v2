"""Partial render responses recover original names from the authorized ledger."""
from copy import deepcopy

import pytest
from conftest import DS_A1, FILE_B1, TOKEN_PROF, TOKEN_RES, auth
from test_dataset_registration import make_upload
import test_preview_relay as upstream
from test_preview_relay import fake_viz
from colab_core.app.main import API_PREFIX


def partial(file_id):
    return {"renderId": upstream.RENDER_ID, "status": "완료",
            "partialFailure": {"totalParts": 2, "renderedParts": 1,
                "missingParts": [{"fileId": file_id, "fileName": "internal/storage/key"}]}}


@pytest.mark.parametrize("method", ["create", "get"])
@pytest.mark.parametrize("target_kind", ["upload", "dataset"])
def test_partial_names_use_original_ledger_name(p2_client, fake_viz, monkeypatch,
                                               method, target_kind):
    base, _ = fake_viz
    client = p2_client(viz_base_url=base)
    if target_kind == "upload":
        receipt = make_upload(client, files=[("files", (
            "intentional-unreadable.tif", b"broken", "image/tiff"))])
        target = {"uploadId": receipt["uploadId"]}
        file_id = receipt["files"][0]["fileId"]
        expected = "intentional-unreadable.tif"
    else:
        target = {"datasetId": DS_A1}
        file_id, expected = "00000000000000000000000FA1", "a1-body.csv"
    job = partial(file_id)
    original = deepcopy(job)
    monkeypatch.setattr(upstream, "JOB_RUNNING", job)
    monkeypatch.setattr(upstream, "JOB_DONE", job)
    response = (client.post(f"{API_PREFIX}/previews", headers=auth(TOKEN_RES),
                           json={"target": target, "style": {"palette": "blues"}})
                if method == "create" else
                client.get(f"{API_PREFIX}/previews/{upstream.RENDER_ID}", headers=auth(TOKEN_RES)))
    assert response.status_code == (202 if method == "create" else 200), response.text
    expected_job = deepcopy(original)
    expected_job["partialFailure"]["missingParts"][0]["fileName"] = expected
    assert response.json() == expected_job
    assert job == original


@pytest.mark.parametrize("file_id", [FILE_B1, "00000000000000000000000FA3",
                                    "00000000000000000000000000"])
def test_get_does_not_reveal_inaccessible_or_unknown_file_names(
        p2_client, fake_viz, monkeypatch, file_id):
    base, _ = fake_viz
    client = p2_client(viz_base_url=base)
    job = partial(file_id)
    monkeypatch.setattr(upstream, "JOB_DONE", job)
    response = client.get(f"{API_PREFIX}/previews/{upstream.RENDER_ID}", headers=auth(TOKEN_RES))
    assert response.status_code == 200
    assert response.json() == job


def test_get_does_not_reveal_another_upload_owners_original_name(
        p2_client, fake_viz, monkeypatch):
    base, _ = fake_viz
    client = p2_client(viz_base_url=base)
    receipt = make_upload(client, token=TOKEN_PROF)
    job = partial(receipt["files"][0]["fileId"])
    monkeypatch.setattr(upstream, "JOB_DONE", job)
    response = client.get(f"{API_PREFIX}/previews/{upstream.RENDER_ID}", headers=auth(TOKEN_RES))
    assert response.status_code == 200
    assert response.json() == job
