"""Approved admin-role-scope: real HTTP/DB boundaries, actor and destination."""
from test_operator_designation import _operator_token, SECRET, LAB_C
from test_preview_relay import fake_viz
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from conftest import (ACC_A_PROF, DS_A2, DS_B1, LAB_A, LAB_B, PRJ_B,
                      TOKEN_PROF, TOKEN_RES, auth)


@pytest.fixture
def isolate_created_accounts(admin_db_url):
    # Backoffice test accounts normally belong to the dedicated lab C. Keep
    # their audit references intact while restoring that isolation after A/None cases.
    account_ids = []
    yield account_ids
    engine = create_engine(make_url(admin_db_url).set(username="postgres", password=None))
    with engine.begin() as db:
        for account_id in account_ids:
            db.execute(text("UPDATE d1_account SET lab_id=:lab WHERE id=:id"),
                       {"lab": LAB_C, "id": account_id})
            db.execute(text("UPDATE d2_member_role SET lab_id=:lab WHERE account_id=:id"),
                       {"lab": LAB_C, "id": account_id})
    engine.dispose()


@pytest.fixture(autouse=True)
def restore_foreign_lab(admin_db_url):
    engine = create_engine(make_url(admin_db_url).set(username="postgres", password=None))
    with engine.connect() as db:
        name = db.execute(text("SELECT name FROM d3_dataset_description WHERE dataset_id=:id"), {"id": DS_B1}).scalar_one()
        projects = list(db.execute(text("SELECT id FROM d6_project WHERE lab_id=:lab"), {"lab": LAB_B}).scalars())
    yield
    with engine.begin() as db:
        db.execute(text("UPDATE d3_dataset_description SET name=:name WHERE dataset_id=:id"), {"id": DS_B1, "name": name})
        db.execute(text("DELETE FROM d6_project WHERE lab_id=:lab AND id <> ALL(:ids)"), {"lab": LAB_B, "ids": projects})
    engine.dispose()


def test_operator_edits_foreign_dataset_in_original_lab(p2_client, admin_db_url):
    client = p2_client(session_secret=SECRET)
    operator = _operator_token(client)
    response = client.patch(f"/api/v1/datasets/{DS_B1}", headers=auth(operator),
                            json={"name": "시스템 관리자 수정"})
    assert response.status_code == 200, response.text
    engine = create_engine(make_url(admin_db_url).set(username="postgres", password=None))
    with engine.connect() as db:
        row = db.execute(text("SELECT d.lab_id, m.name FROM d3_dataset d JOIN "
                              "d3_dataset_description m ON m.dataset_id=d.id WHERE d.id=:id"),
                         {"id": DS_B1}).one()
        assert row.lab_id == LAB_B
        assert row.name == "시스템 관리자 수정"
        actor = str(client.app.state.authenticators.resolve(operator).account_id)
        audit = db.execute(text("SELECT lab_id,actor_id FROM d3_operator_audit WHERE target_id=:id AND actor_id=:actor"),
                           {"id": DS_B1, "actor": actor}).first()
        assert audit is not None and audit.lab_id == LAB_B and audit.actor_id == actor
    engine.dispose()


@pytest.mark.parametrize("token,status", [(TOKEN_PROF, 201), (TOKEN_RES, 403)])
def test_new_project_target_is_explicit_and_admin_only(p2_client, admin_db_url, token, status):
    client = p2_client(session_secret=SECRET)
    operator = _operator_token(client)
    response = client.post("/api/v1/projects", headers={**auth(operator if token == TOKEN_PROF else token),
        "X-CoLAB-Target-Lab": LAB_B}, json={"type": "논문", "name": "관리자 범위 시험"})
    assert response.status_code == status, response.text
    if status == 201:
        project = client.get(f"/api/v1/projects/{response.json()['projectId']}",
                             headers=auth(operator))
        assert project.status_code == 200, project.text
        engine = create_engine(make_url(admin_db_url).set(username="postgres", password=None))
        with engine.connect() as db:
            assert db.execute(text("SELECT lab_id FROM d6_project WHERE id=:id"),
                              {"id": response.json()['projectId']}).scalar_one() == LAB_B
        engine.dispose()


def test_operator_creation_requires_target_even_when_affiliated(p2_client):
    client = p2_client(session_secret=SECRET)
    operator = _operator_token(client)
    response = client.post("/api/v1/projects", headers=auth(operator),
                               json={"type": "논문", "name": "소속으로 추정 금지"})
    assert response.status_code == 400, response.text


def test_operator_target_mismatch_and_cross_lab_link_are_rejected(p2_client):
    client = p2_client(session_secret=SECRET)
    operator = _operator_token(client)
    mismatch = client.patch(f"/api/v1/datasets/{DS_B1}",
        headers={**auth(operator), "X-CoLAB-Target-Lab": LAB_A}, json={"name": "충돌"})
    assert mismatch.status_code == 400, mismatch.text
    link = client.put(f"/api/v1/projects/{PRJ_B}/datasets/{DS_A2}",
                       headers=auth(operator), json={})
    assert link.status_code == 400, link.text


def test_professor_can_read_private_body_without_operator(p2_client, admin_db_url):
    client = p2_client(session_secret=SECRET)
    operator = _operator_token(client)
    # The fixture's professor is also operator; exercise the real professor DB scope directly.
    from conftest import scoped_ro
    from colab_core.kernel.db import make_engine, make_session_factory
    from colab_core.domains import d2_access, d3_catalog
    from colab_core.kernel.ids import Ulid
    factory = client.app.state.session_factory
    with scoped_ro(factory, ACC_A_PROF, LAB_A) as db:
        access = d2_access.DatasetAccessAdapter(db).dataset_access([Ulid(DS_A2)])[DS_A2]
        assert access.body_accessible is True
        assert d3_catalog.list_files(db, Ulid(DS_A2))


def test_operator_download_ticket_uses_object_lab_and_rechecks_revocation(p2_client):
    from test_operator_designation import _operator_identity, _set_operator
    from colab_core.kernel.download_ticket import DownloadTicketSigner
    client = p2_client(session_secret=SECRET)
    account_id, operator = _operator_identity(client)
    ticket = client.get(f"/api/v1/datasets/{DS_B1}/download", headers=auth(operator))
    assert ticket.status_code == 200, ticket.text
    encoded = ticket.json()["url"].rsplit("/", 1)[-1]
    claims = DownloadTicketSigner(SECRET).verify(encoded)
    assert str(claims.lab_id) == LAB_B
    assert _set_operator(client, TOKEN_PROF, account_id, False).status_code == 200
    denied = client.get(ticket.json()["url"])
    assert denied.status_code == 404, denied.text


def test_selected_lab_cannot_change_foreign_member_permissions(p2_client):
    from test_operator_designation import _create, _email
    client = p2_client(session_secret=SECRET)
    operator = _operator_token(client)
    foreign = _create(client, _email("foreign-member"), role="연구원")
    response = client.put("/api/v1/lab/members/permissions",
        headers={**auth(operator), "X-CoLAB-Target-Lab": LAB_A},
        json={"items": [{"accountId": foreign, "changes": {"승인 위임": True}}]})
    assert response.status_code == 404, response.text


def test_operator_cannot_reuse_grid_from_a_different_lab(p2_client):
    from test_dataset_registration import make_upload
    client = p2_client(session_secret=SECRET)
    operator = _operator_token(client)
    upload = make_upload(client)
    response = client.post(f"/api/v1/uploads/{upload['uploadId']}/grid-reuse",
        headers=auth(operator), json={"sourceDatasetId": DS_B1})
    assert response.status_code == 400, response.text


def test_professor_role_revocation_closes_private_download_and_preview(p2_client, admin_db_url, monkeypatch, isolate_created_accounts):
    from test_operator_designation import _email, _normal_token, INITIAL
    from test_download import _dataset
    from test_preview_relay import JOB_DONE, RENDER_ID
    from types import SimpleNamespace
    client = p2_client(session_secret=SECRET)
    email = _email("prof-scope")
    made = client.post("/api/v1/admin/accounts", headers=auth(TOKEN_PROF), json={
        "email": email, "name": "교수 관리자", "labId": LAB_A, "role": "교수",
        "initialPassword": INITIAL})
    assert made.status_code == 201, made.text
    isolate_created_accounts.append(made.json()["accountId"])
    professor = _normal_token(client, email)
    # ⭑ **⟨2026-09-18 develop 동기화⟩ 자료는 **다른 구성원**이 갖는다.**
    #   이 시험이 재는 것은 「역할을 잃으면 관리 접근이 닫힌다」다. 새 교수가 자기 자료를 올리면
    #   강등 뒤에도 **소유자**로 계속 보이므로(`0032_private_owner_access`) 재려던 것이 사라진다.
    #   그래서 연구원이 올리고 잠그고, 교수는 **관리자 자격으로만** 닿는다.
    dataset_id, files = _dataset(client, token=TOKEN_RES)
    locked = client.patch(f"/api/v1/datasets/{dataset_id}", headers=auth(TOKEN_RES),
                           json={"accessState": "잠김"})
    assert locked.status_code == 200, locked.text
    ticket = client.get(f"/api/v1/datasets/{dataset_id}/files/{files['a.csv']['fileId']}/download",
                        headers=auth(professor))
    assert ticket.status_code == 200, ticket.text
    assert client.get(ticket.json()['url']).status_code == 200
    client.app.state.previews = SimpleNamespace(get=lambda **kwargs: {
        **JOB_DONE, "target": {"datasetId": dataset_id}})
    assert client.get(f"/api/v1/previews/{RENDER_ID}", headers=auth(professor)).status_code == 200
    engine = create_engine(make_url(admin_db_url).set(username="postgres", password=None))
    with engine.begin() as db:
        db.execute(text("UPDATE d2_member_role SET role='연구원' WHERE account_id=:id"),
                   {"id": made.json()['accountId']})
    engine.dispose()
    assert client.get(ticket.json()['url']).status_code == 404
    assert client.get(f"/api/v1/previews/{RENDER_ID}", headers=auth(professor)).status_code == 403


def test_labless_system_administrator_previews_private_data_and_selects_creation_lab(p2_client, fake_viz, isolate_created_accounts):
    from test_operator_designation import _email, _normal_token, INITIAL
    base, upstream = fake_viz
    client = p2_client(session_secret=SECRET, viz_base_url=base)
    email = _email("labless-scope")
    made = client.post("/api/v1/admin/accounts-v2", headers=auth(TOKEN_PROF), json={
        "email": email, "name": "무소속 시스템 관리자", "initialPassword": INITIAL, "operator": True})
    assert made.status_code == 201, made.text
    isolate_created_accounts.append(made.json()["accountId"])
    token = _normal_token(client, email)
    me = client.get("/api/v1/me-v2", headers=auth(token)).json()
    assert me['labId'] is None and len(me['permissions']) == 4 and all(me['permissions'].values())
    preview = client.post("/api/v1/preview-target-descriptions", headers=auth(token),
                          json={"datasetId": DS_A2})
    assert preview.status_code == 200, preview.text
    assert upstream.received[-1]['lab'] == LAB_A
    project = client.post("/api/v1/projects", headers={**auth(token), "X-CoLAB-Target-Lab": LAB_B},
                          json={"type": "논문", "name": "무소속 관리자 선택 연구실"})
    assert project.status_code == 201, project.text
    assert client.get(f"/api/v1/projects/{project.json()['projectId']}", headers=auth(token)).status_code == 200
    missing = client.post("/api/v1/projects", headers={**auth(token), "X-CoLAB-Target-Lab": "0000000000000000000000000Z"},
                          json={"type": "논문", "name": "없는 연구실"})
    assert missing.status_code == 404, missing.text


def test_operator_project_name_uniqueness_is_scoped_to_target_lab(p2_client):
    client = p2_client(session_secret=SECRET)
    operator = _operator_token(client)
    name = "각 연구실 같은 프로젝트 이름"
    first = client.post("/api/v1/projects", headers=auth(TOKEN_PROF),
                        json={"type": "논문", "name": name})
    assert first.status_code == 201, first.text
    headers = {**auth(operator), "X-CoLAB-Target-Lab": LAB_B}
    second = client.post("/api/v1/projects", headers=headers, json={"type": "논문", "name": name})
    assert second.status_code == 201, second.text
    duplicate = client.post("/api/v1/projects", headers=headers, json={"type": "논문", "name": name})
    assert duplicate.status_code == 400, duplicate.text


def test_selected_operator_scope_reads_only_target_lab_and_keeps_private_access(p2_client):
    from colab_core.kernel.scope import read_only_scope, select_target_lab, reapply_scope
    client = p2_client(session_secret=SECRET)
    token = _operator_token(client)
    subject = client.app.state.authenticators.resolve(token)
    with read_only_scope(client.app.state.session_factory, subject, operator_read=True) as db:
        assert db.execute(text("SELECT id FROM d3_dataset WHERE id=:id"), {"id": DS_B1}).first()
        db.rollback()
        reapply_scope(db, subject)
        assert db.execute(text("SELECT id FROM d3_dataset WHERE id=:id"), {"id": DS_B1}).first()
        select_target_lab(db, subject, LAB_A)
        db.rollback()
        reapply_scope(db, subject)
        assert db.execute(text("SELECT id FROM d3_dataset WHERE id=:id"), {"id": DS_B1}).first() is None
        assert db.execute(text("SELECT id FROM d3_file WHERE dataset_id=:id"), {"id": DS_A2}).first()


def test_verification_reference_preserves_actor_when_display_name_is_outside_lab():
    from colab_core.app.routes.catalog import _account_ref
    assert _account_ref(ACC_A_PROF, None) == {"accountId": ACC_A_PROF, "name": ACC_A_PROF}
