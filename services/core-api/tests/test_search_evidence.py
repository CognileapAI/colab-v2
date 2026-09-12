"""파일 내용 버전에 묶인 검색 근거의 저장·검토·접근 경계."""
from __future__ import annotations

import hashlib
import json

from conftest import ACC_A_RES, DS_A1, DS_A2, DS_B1, LAB_A, TOKEN_RES, auth, scoped_ro

from colab_core.app.main import API_PREFIX
from colab_core.domains import d3_search_evidence

FILE_A1 = "00000000000000000000000FA1"
FILE_B1 = "00000000000000000000000FB1"


def _payload(*, revision=0, file_revision=1, status="draft") -> dict:
    return {
        "expectedRevision": revision,
        "expectedFileRevision": file_revision,
        "facts": {
            "roles": ["model_input", "validation"],
            "period": {"start": "2025-01-01", "end": "2025-12-31"},
            "region": "한반도",
            "cadence": "daily",
            "directObservation": True,
            "nativeResolutionM": 100.0,
            "interpolated": False,
        },
        "source": {"label": "자료 설명서", "locator": "2장 3문단", "text": "일 강수 관측 입력"},
        "status": status,
    }


def _file_revision(client) -> int:
    response = client.get(f"{API_PREFIX}/datasets/{DS_A1}/search-evidence",
                          headers=auth(TOKEN_RES))
    assert response.status_code == 200, response.text
    return next(row["fileRevision"] for row in response.json()["items"]
                if row["fileId"] == FILE_A1)


def _save(client, payload: dict):
    return client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{FILE_A1}/search-evidence",
                      json=payload, headers=auth(TOKEN_RES))


def test_draft_can_be_saved_read_and_explicitly_reviewed(p2_client) -> None:
    client = p2_client()
    revision = _file_revision(client)
    draft = _save(client, _payload(file_revision=revision))
    assert draft.status_code == 200, draft.text
    body = draft.json()
    assert body["revision"] == 1 and body["status"] == "draft"
    assert body["reviewedBy"] is None and body["reviewedAt"] is None
    assert body["source"]["sha256"] == hashlib.sha256("일 강수 관측 입력".encode()).hexdigest()

    listed = client.get(f"{API_PREFIX}/datasets/{DS_A1}/search-evidence",
                        headers=auth(TOKEN_RES)).json()["items"]
    assert next(row for row in listed if row["fileId"] == FILE_A1)["evidence"] == body

    reviewed = _save(client, _payload(revision=1, file_revision=revision, status="reviewed"))
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["revision"] == 2 and reviewed.json()["status"] == "reviewed"
    assert reviewed.json()["reviewedBy"] is not None and reviewed.json()["reviewedAt"] is not None


def test_documentation_and_analysis_code_roles_are_stored_without_observation_claims(p2_client) -> None:
    client = p2_client()
    payload = _payload(file_revision=_file_revision(client))
    payload["facts"] = {"roles": ["documentation", "analysis_code"]}
    response = _save(client, payload)
    assert response.status_code == 200, response.text
    assert response.json()["facts"] == {"roles": ["documentation", "analysis_code"]}


def test_concurrent_evidence_and_file_versions_are_rejected(p2_client) -> None:
    client = p2_client()
    revision = _file_revision(client)
    assert _save(client, _payload(file_revision=revision)).status_code == 200
    assert _save(client, _payload(file_revision=revision)).status_code == 409
    assert _save(client, _payload(revision=1, file_revision=revision + 1)).status_code == 409


def test_same_value_content_update_increments_revision_and_makes_evidence_stale(
        p2_client, sql) -> None:
    client = p2_client()
    revision = _file_revision(client)
    assert _save(client, _payload(file_revision=revision, status="reviewed")).status_code == 200
    sql("UPDATE d3_file SET storage_key = storage_key, size_bytes = size_bytes WHERE id = :f",
        {"f": FILE_A1})
    listed = client.get(f"{API_PREFIX}/datasets/{DS_A1}/search-evidence",
                        headers=auth(TOKEN_RES)).json()["items"]
    row = next(row for row in listed if row["fileId"] == FILE_A1)
    assert row["fileRevision"] == revision + 1
    assert row["evidence"]["status"] == "stale"


def test_reviewed_reader_excludes_drafts_and_stale_rows(p2_client, session_factory, sql) -> None:
    client = p2_client()
    revision = _file_revision(client)
    assert _save(client, _payload(file_revision=revision)).status_code == 200
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        assert d3_search_evidence.read_reviewed(session, [DS_A1]) == []
    assert _save(client, _payload(revision=1, file_revision=revision,
                                  status="reviewed")).status_code == 200
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        rows = d3_search_evidence.read_reviewed(session, [DS_A1])
    assert len(rows) == 1 and rows[0]["file_id"] == FILE_A1
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        assert d3_search_evidence.read_reviewed(session, []) == []
        without_text = d3_search_evidence.read_reviewed(
            session, [DS_A1], include_source_text=False)
    assert "text" not in without_text[0]["source"]
    sql("UPDATE d3_file SET size_bytes = size_bytes WHERE id = :f", {"f": FILE_A1})
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        assert d3_search_evidence.read_reviewed(session, [DS_A1]) == []


def test_file_delete_cascades_evidence(p2_client, sql) -> None:
    client = p2_client()
    assert _save(client, _payload(file_revision=_file_revision(client))).status_code == 200
    sql("DELETE FROM d3_file WHERE id = :f", {"f": FILE_A1})
    assert sql("SELECT count(*) AS n FROM d3_search_evidence WHERE file_id = :f",
               {"f": FILE_A1})[0]["n"] == 0


def test_access_and_edit_boundaries_are_reused(p2_client, sql) -> None:
    client = p2_client()
    assert client.get(f"{API_PREFIX}/datasets/{DS_B1}/search-evidence",
                      headers=auth(TOKEN_RES)).status_code == 404
    assert client.get(f"{API_PREFIX}/datasets/{DS_A2}/search-evidence",
                      headers=auth(TOKEN_RES)).status_code == 403
    foreign = client.put(f"{API_PREFIX}/datasets/{DS_B1}/files/{FILE_B1}/search-evidence",
                         json=_payload(), headers=auth(TOKEN_RES))
    assert foreign.status_code == 404
    locked = client.put(f"{API_PREFIX}/datasets/{DS_A2}/files/{FILE_A1}/search-evidence",
                        json=_payload(), headers=auth(TOKEN_RES))
    assert locked.status_code == 403

    sql("UPDATE d2_permission_switch SET enabled=false"
        " WHERE account_id='000000000000000000000000A1' AND switch='업로드·편집'")
    denied = _save(client, _payload(file_revision=_file_revision(client)))
    assert denied.status_code == 403


def test_invalid_shapes_and_client_hash_are_rejected(p2_client) -> None:
    client = p2_client()
    revision = _file_revision(client)
    for mutation in (
        lambda p: p.update(extra=True),
        lambda p: p.update(expectedRevision=True),
        lambda p: p.update(facts={}),
        lambda p: p.update(facts={"region": None}),
        lambda p: p["facts"].update(cadence="yearly"),
        lambda p: p["facts"].update(nativeResolutionM=0),
        lambda p: p["facts"].update(nativeResolutionM="100"),
        lambda p: p["facts"].update(directObservation="true"),
        lambda p: p["facts"].update(region="   "),
        lambda p: p["facts"].update(period={"start": 1735689600, "end": "2025-12-31"}),
        lambda p: p["source"].update(sha256="client-value"),
        lambda p: p["source"].update(label="   "),
    ):
        payload = _payload(file_revision=revision)
        mutation(payload)
        response = _save(client, payload)
        assert response.status_code == 400, response.text
    payload = _payload(file_revision=revision)
    raw = json.dumps(payload).replace("100.0", "1e999")
    response = client.put(f"{API_PREFIX}/datasets/{DS_A1}/files/{FILE_A1}/search-evidence",
                          content=raw,
                          headers={**auth(TOKEN_RES), "Content-Type": "application/json"})
    assert response.status_code == 400, response.text


def test_operator_read_does_not_expand_evidence_lab_or_locked_body_access(p2_client, session_factory, sql):
    from conftest import ACC_B_PROF, LAB_B
    from colab_core.kernel.auth import Subject
    from colab_core.kernel.ids import Ulid
    from colab_core.kernel.scope import read_only_scope
    from sqlalchemy import text

    client = p2_client()
    assert _save(client, _payload(file_revision=_file_revision(client), status='reviewed')).status_code == 200
    other_operator = Subject(account_id=Ulid(ACC_B_PROF), lab_id=Ulid(LAB_B), operator=True)
    with read_only_scope(session_factory, other_operator, operator_read=True) as db:
        # Main's operator metadata/file visibility is active; evidence keeps its own lab boundary.
        assert db.execute(text('SELECT count(*) FROM d3_file WHERE id=:id'), {'id': FILE_A1}).scalar_one() == 1
        assert d3_search_evidence.read_reviewed(db) == []
    sql("INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES(:id,:lab,'잠김') ON CONFLICT(dataset_id) DO UPDATE SET state='잠김'", {'id': DS_A1, 'lab': LAB_A})
    own_operator = Subject(account_id=Ulid(ACC_A_RES), lab_id=Ulid(LAB_A), operator=True)
    try:
        with read_only_scope(session_factory, own_operator, operator_read=True) as db:
            assert d3_search_evidence.read_reviewed(db) == []
    finally:
        sql("DELETE FROM d2_dataset_access WHERE dataset_id=:id", {'id': DS_A1})
