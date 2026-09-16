"""An out-of-lab actor's hidden account must not hide in-lab datasets or lineage."""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from conftest import LAB_B, DS_B1, TOKEN_PROF, auth
from test_admin_role_scope import isolate_created_accounts
from test_operator_designation import _operator_identity, _email, _normal_token, INITIAL, SECRET
from test_uploads import one_body


def _register(client, headers):
    uploaded = client.post("/api/v1/uploads", files=one_body(), headers=headers)
    assert uploaded.status_code == 201, uploaded.text
    registered = client.post("/api/v1/datasets", headers=headers, json={
        "uploadId": uploaded.json()["uploadId"], "name": "다른 소속 관리자가 등록한 자료",
        "summary": "행위자의 소속과 자료의 소속은 다르다", "category": "기상·기후 인자",
        "dataType": "재분석자료", "observationInterval": {"value": 10, "unit": "분"},
    })
    assert registered.status_code == 201, registered.text
    return registered.json()["datasetId"]


@pytest.mark.parametrize("labless", [False, True])
def test_admin_registered_dataset_remains_visible_to_its_lab_professor(
        p2_client, admin_db_url, isolate_created_accounts, labless):
    client = p2_client(session_secret=SECRET)
    if labless:
        email = _email("labless-register")
        made = client.post("/api/v1/admin/accounts-v2", headers=auth(TOKEN_PROF), json={
            "email": email, "name": "시스템 관리자", "initialPassword": INITIAL, "operator": True})
        assert made.status_code == 201, made.text
        actor = made.json()["accountId"]
        isolate_created_accounts.append(actor)
        token = _normal_token(client, email)
    else:
        actor, token = _operator_identity(client)
    dataset = _register(client, {**auth(token), "X-CoLAB-Target-Lab": LAB_B})
    professor = auth("b1-prof-token")
    detail = client.get(f"/api/v1/datasets/{dataset}", headers=professor)
    assert detail.status_code == 200, detail.text
    assert detail.json()["labId"] == LAB_B
    assert detail.json()["basicInfo"]["uploader"]["accountId"] == actor
    assert detail.json()["basicInfo"]["owner"]["accountId"] == actor
    assert isinstance(detail.json()["basicInfo"]["uploader"]["name"], str)
    listed = client.get("/api/v1/datasets", headers=professor)
    assert dataset in {item["datasetId"] for item in listed.json()["items"]}
    candidates = client.get("/api/v1/lineage-candidates", headers=professor)
    assert candidates.status_code == 200, candidates.text
    assert dataset in {item["datasetId"] for item in candidates.json()["items"]}
    engine = create_engine(make_url(admin_db_url).set(username="postgres", password=None))
    try:
        with engine.connect() as db:
            assert tuple(db.execute(text("SELECT lab_id,owner_account_id,uploader_account_id FROM d3_dataset WHERE id=:id"),
                                    {"id": dataset}).one()) == (LAB_B, actor, actor)
    finally:
        engine.dispose()


def test_admin_confirmed_lineage_remains_visible_to_target_lab_professor(p2_client):
    client = p2_client(session_secret=SECRET)
    dataset = _register(client, auth("b1-prof-token"))
    actor, token = _operator_identity(client)
    added = client.post(f"/api/v1/datasets/{dataset}/lineage/parents", headers=auth(token),
                        json={"parentDatasetId": DS_B1, "parentRole": "주입력"})
    assert added.status_code == 201, added.text
    lineage = client.get(f"/api/v1/datasets/{dataset}/lineage", headers=auth("b1-prof-token"))
    assert lineage.status_code == 200, lineage.text
    edges = lineage.json()["edges"]
    assert len(edges) == 1
    assert edges[0]["parentDatasetId"] == DS_B1
    assert edges[0]["confirmedBy"]["accountId"] == actor
    assert isinstance(edges[0]["confirmedBy"]["name"], str)
