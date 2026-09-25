"""Receipt projection shares snapshot/ack/ledger transaction and current source authority."""

import importlib
import importlib.util
from dataclasses import replace
import pytest
from sqlalchemy import text
from conftest import LAB_B, ACC_B_PROF
from test_knowledge_source_authority import (
    prepared,
    sources,
    issue,
    principal,
    receipt_for,
)
from test_search_changes import scoped
from test_knowledge_http import connected
from colab_core.domains import d3_search_changes as changes
from colab_core.domains import d4_lineage
from colab_core.kernel.knowledge_wire import AuthorizedKnowledge


def domain():
    name = "colab_core.domains.d3_knowledge_projection"
    assert importlib.util.find_spec(name), "receipt projection missing"
    return importlib.import_module(name)


@pytest.fixture
def projection(prepared, session_factory):
    command = issue(session_factory, prepared)
    result = AuthorizedKnowledge(
        payload=command.model_dump(exclude={"grant"}), receipt=receipt_for(command)
    )
    with scoped(session_factory) as db:
        items = changes.claim(db, limit=100, authorized_only=True)
    claim = next(
        item
        for item in items
        if item.source_id == prepared.source_id and item.source_kind == "evidence"
    )
    return claim, result


def apply(factory, claim, result, who=None):
    who = who or principal()
    with scoped(factory, lab=who.lab_id, account=who.account_id) as db:
        return domain().apply(db, claim, result, who,lineage=d4_lineage.LineageRevisionAdapter(db))


def test_projection_creates_snapshot_ack_and_replay_is_noop(
    projection, session_factory, sql
):
    claim, result = projection
    applied = apply(session_factory, claim, result)
    assert applied["status"] == "applied"
    ledger = sql("SELECT * FROM d3_knowledge_projection")
    queue = sql("SELECT * FROM d3_search_change WHERE source_kind='evidence'")
    snapshots = sql("SELECT * FROM d3_search_fact_snapshot")
    assert len(ledger) == len(snapshots) == 1
    assert snapshots[0]["facts"] == [
        {
            "predicate": "roles",
            "value": ["validation"],
            "source_locator": "readme:1#/roles",
        }
    ]
    assert (
        queue[0]["processed_version"] == claim.claimed_version
        and queue[0]["lease_until"] is None
    )
    assert apply(session_factory, claim, result)["status"] == "already_applied"
    assert ledger == sql("SELECT * FROM d3_knowledge_projection")
    assert queue == sql("SELECT * FROM d3_search_change WHERE source_kind='evidence'")


@pytest.mark.parametrize("kind", ["expired", "new_lease", "wrong_source", "cross_lab"])
def test_projection_rejects_invalid_claim(projection, session_factory, sql, kind):
    claim, result = projection
    who = principal()
    if kind == "expired":
        sql(
            "UPDATE d3_search_change SET lease_until=clock_timestamp()-interval '1 second' WHERE source_kind='evidence'"
        )
    elif kind == "new_lease":
        sql(
            "UPDATE d3_search_change SET lease_generation=lease_generation+1 WHERE source_kind='evidence'"
        )
    elif kind == "wrong_source":
        claim = replace(claim, source_id="5" * 26)
    else:
        who = principal(ACC_B_PROF, LAB_B)
    with pytest.raises(ValueError):
        apply(session_factory, claim, result, who)
    assert not sql("SELECT * FROM d3_search_fact_snapshot")


@pytest.mark.parametrize("kind", ["facts", "locator", "duplicate", "mapping"])
def test_projection_rejects_forged_or_unsupported_content(
    projection, session_factory, kind
):
    claim, result = projection
    if kind == "facts":
        result.payload.facts[0].value = ["prediction"]
    elif kind == "locator":
        result.payload.facts[0].source_locator = "invented"
    elif kind == "duplicate":
        result.payload.facts.append(result.payload.facts[0])
    else:
        from colab_core.kernel.knowledge_wire import Mapping

        result.payload.mappings = [
            Mapping(
                fact_id=result.payload.facts[0].fact_id,
                concept_id="ndvi",
                basis={"mapping_rule_id": "unapproved"},
            )
        ]
    with pytest.raises(ValueError):
        apply(session_factory, claim, result)


def test_projection_ledger_failure_rolls_back_snapshot_and_ack(
    projection, session_factory, sql, monkeypatch
):
    claim, result = projection
    module = domain()

    def fail(*args):
        raise ValueError("ledger unavailable")

    monkeypatch.setattr(module, "_save", fail)
    with pytest.raises(ValueError):
        apply(session_factory, claim, result)
    assert not sql("SELECT * FROM d3_search_fact_snapshot")
    assert not sql("SELECT * FROM d3_knowledge_projection")
    assert (
        sql(
            "SELECT processed_version FROM d3_search_change WHERE source_kind='evidence'"
        )[0]["processed_version"]
        == 0
    )


def test_projection_retains_sequence_when_snapshot_deleted(
    projection, session_factory, sql
):
    claim, result = projection
    apply(session_factory, claim, result)
    sql("DELETE FROM d3_search_fact_snapshot")
    row = sql("SELECT * FROM d3_knowledge_projection")[0]
    assert row["snapshot_id"] is None and row["publication_sequence"] == 1
    with pytest.raises(ValueError):
        apply(session_factory, claim, result)


@pytest.mark.parametrize(
    "kind", ["old_sequence", "receipt_conflict", "digest_conflict"]
)
def test_projection_sequence_fence(projection, session_factory, sql, kind):
    claim, result = projection
    result.receipt.publication_sequence = 2
    apply(session_factory, claim, result)
    before = sql("SELECT * FROM d3_knowledge_projection")
    if kind == "old_sequence":
        result.receipt.publication_sequence = 1
    elif kind == "receipt_conflict":
        result.receipt.receipt_id = "5" * 26
    else:
        sql(
            "UPDATE d3_knowledge_projection SET payload_digest=:digest",
            {"digest": "f" * 64},
        )
        before = sql("SELECT * FROM d3_knowledge_projection")
    with pytest.raises(ValueError, match="stale_sequence|idempotency_conflict"):
        apply(session_factory, claim, result)
    assert before == sql("SELECT * FROM d3_knowledge_projection")


def test_same_receipt_requeued_work_requires_new_claim(
    projection, session_factory, sql
):
    claim, result = projection
    first = apply(session_factory, claim, result)
    sql("UPDATE d3_search_change SET processed_version=0 WHERE source_kind='evidence'")
    with scoped(session_factory) as db:
        fresh = next(
            c for c in changes.claim(db, limit=100) if c.source_kind == "evidence"
        )
    with pytest.raises(ValueError, match="stale_claim"):
        apply(session_factory, claim, result)
    applied = apply(session_factory, fresh, result)
    assert applied == {"status": "applied", "fact_id": first["fact_id"]}
    assert sql(
        "SELECT processed_version,lease_until FROM d3_search_change WHERE source_kind='evidence'"
    ) == [{"processed_version": fresh.claimed_version, "lease_until": None}]


@pytest.mark.parametrize("change", ["source", "release", "generation", "private"])
def test_completed_receipt_rechecks_current_source_and_access(
    projection, session_factory, sql, change
):
    from test_search_ontology import manifest
    from colab_core.domains import d3_search_ontology

    claim, result = projection
    apply(session_factory, claim, result)
    who = principal()
    viewer = None
    if change == "source":
        sql(
            "UPDATE d3_search_evidence SET revision=revision+1 WHERE file_id=:id",
            {"id": claim.source_id},
        )
    elif change == "release":
        with scoped(session_factory) as db:
            d3_search_ontology.publish(
                db,
                manifest(discovery="d" * 64),
                expected_previous=manifest()["version"],
            )
    elif change == "generation":
        sql(
            "UPDATE d3_knowledge_fence SET generation=generation+1 WHERE source_id=:id",
            {"id": claim.source_id},
        )
    else:
        from colab_core.kernel.ids import Ulid

        viewer = str(Ulid.generate())
        sql(
            "INSERT INTO d1_account(id,lab_id,name,email) VALUES (:id,:lab,'projection-viewer',:email)",
            {"id": viewer, "lab": claim.lab_id, "email": viewer + "@example.test"},
        )
        who = principal(viewer)
        assert apply(session_factory, claim, result, who)["status"] == "already_applied"
        sql(
            "INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,:lab,'잠김') ON CONFLICT(dataset_id) DO UPDATE SET state='잠김'",
            {"id": claim.dataset_id, "lab": claim.lab_id},
        )
    try:
        with pytest.raises(ValueError):
            apply(session_factory, claim, result, who)
        if change == "private":
            assert sql("SELECT * FROM d3_knowledge_projection", account_id=viewer) == []
    finally:
        if change == "private":
            sql(
                "UPDATE d2_dataset_access SET state='열림' WHERE dataset_id=:id",
                {"id": claim.dataset_id},
            )
            sql("DELETE FROM d1_account WHERE id=:id", {"id": viewer})


def test_projection_ledger_is_hidden_from_other_lab(projection, session_factory, sql):
    claim, result = projection
    apply(session_factory, claim, result)
    assert (
        sql(
            "SELECT * FROM d3_knowledge_projection", lab_id=LAB_B, account_id=ACC_B_PROF
        )
        == []
    )


@pytest.mark.parametrize("change", ["value", "locator", "extra"])
def test_projection_compares_source_facts_even_if_canonical_storage_is_corrupt(
    projection, session_factory, sql, change
):
    import json
    from colab_core.kernel.knowledge_wire import KnowledgePayload, payload_digest

    claim, result = projection
    body = result.payload.model_dump(mode="json")
    if change == "value":
        body["facts"][0]["value"] = ["prediction"]
    elif change == "locator":
        body["facts"][0]["source_locator"] = "invented"
    else:
        body["facts"].append(
            {
                **body["facts"][0],
                "fact_id": "6" * 26,
                "predicate": "variable",
                "value": "NDVI",
            }
        )
    result.payload = KnowledgePayload.model_validate(body)
    result.receipt.payload_digest = payload_digest(result.payload)
    sql(
        "UPDATE d3_knowledge_source SET command=CAST(:body AS jsonb) WHERE source_id=:id",
        {"body": json.dumps(body), "id": claim.source_id},
    )
    with pytest.raises(ValueError, match="source facts mismatch"):
        apply(session_factory, claim, result)


@pytest.mark.parametrize("first", ["legacy", "knowledge"])
def test_legacy_complete_and_projection_cannot_complete_same_claim(
    prepared, session_factory, first
):
    from test_search_refresh_tools import make_tools

    tools = make_tools(session_factory)
    command = issue(session_factory, prepared)
    result = AuthorizedKnowledge(
        payload=command.model_dump(exclude={"grant"}), receipt=receipt_for(command)
    )
    handle = next(
        job["handle"] for job in tools.claim() if job["source_kind"] == "evidence"
    )
    captured = tools._handles[handle].claim
    version = tools.read(handle)["ontology_version"]
    if first == "legacy":
        tools.complete(handle, expected_version=version, concept_ids=[])
        with pytest.raises(ValueError, match="stale_claim"):
            apply(session_factory, captured, result)
        with pytest.raises(ValueError, match="unknown or expired"):
            tools.complete(handle, expected_version=version, concept_ids=[])
    else:
        apply(session_factory, captured, result)
        with pytest.raises(ValueError, match="source or lease changed"):
            tools.complete(handle, expected_version=version, concept_ids=[])


@pytest.mark.parametrize("change", ["logout", "version", "private"])
def test_projector_reauthenticates_after_network(
    connected, session_factory, sql, monkeypatch, change
):
    client, key, issued, account = connected
    name = "colab_core.app.knowledge_projector"
    assert importlib.util.find_spec(name), "trusted projector missing"
    module = importlib.import_module(name)
    who = principal(account)
    command = issue(session_factory, key, who)
    result = AuthorizedKnowledge(
        payload=command.model_dump(exclude={"grant"}), receipt=receipt_for(command)
    )
    with scoped(session_factory, account=account) as db:
        claim = next(
            c
            for c in changes.claim(db, limit=100)
            if c.source_kind == "evidence" and c.source_id == key.source_id
        )

    def read(self, actual_key, receipt_id, *, session_token):
        assert (
            actual_key == key
            and receipt_id == result.receipt.receipt_id
            and session_token == issued.token
        )
        if change == "logout":
            client.app.state.login_sessions.revoke(issued.session_id)
        elif change == "version":
            with client.app.state.account_admin_factory.begin() as db:
                db.execute(
                    text(
                        "UPDATE account_admin.login_credential SET session_version=session_version+1 WHERE account_id=:id"
                    ),
                    {"id": account},
                )
        else:
            sql(
                "INSERT INTO d2_dataset_access(dataset_id,lab_id,state) VALUES (:id,:lab,'잠김') ON CONFLICT(dataset_id) DO UPDATE SET state='잠김'",
                {"id": key.dataset_id, "lab": key.lab_id},
            )
        return result

    monkeypatch.setattr(module.KnowledgeHttpClient, "read", read)
    projector = module.KnowledgeProjector(
        session_factory,
        client.app.state.login_sessions,
        client.app.state.database_credentials,
        base_url="http://127.0.0.1:1",
        reader_token="dedicated-reader",
        timeout=1,
    )
    with pytest.raises(ValueError):
        projector.apply(claim, result.receipt.receipt_id, session_token=issued.token)
    assert not sql("SELECT * FROM d3_search_fact_snapshot")
