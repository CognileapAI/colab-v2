"""Internal D3-only projection. Caller owns transaction and authenticates viewer.

No network, grants, ontology mapping or independent queue acknowledgement.
"""

from dataclasses import asdict
import json
from sqlalchemy import text
from ..kernel.knowledge_wire import AuthorizedKnowledge, SourceKey
from . import d3_knowledge_source as authority, d3_search_changes as changes
from . import d3_search_facts as facts, d3_search_ontology as ontology
from . import d3_file_measurement as measured

_KEY = "lab_id=:lab_id AND dataset_id=:dataset_id AND source_kind=:source_kind AND source_id=:source_id"


def _normalized(rows):
    if len({row["predicate"] for row in rows}) != len(rows):
        raise ValueError("duplicate predicate")
    return sorted(
        json.dumps(
            {k: row[k] for k in ("predicate", "value", "source_locator")},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        for row in rows
    )


def _save(session, receipt, snapshot_id):
    session.execute(
        text("""INSERT INTO d3_knowledge_projection
      (lab_id,dataset_id,source_kind,source_id,receipt_id,publication_sequence,payload_digest,
       source_revision,processing_generation,ontology_release,snapshot_id)
      VALUES (:lab_id,:dataset_id,:source_kind,:source_id,:receipt,:sequence,:digest,:revision,:generation,:release,:snapshot)
      ON CONFLICT (lab_id,dataset_id,source_kind,source_id) DO UPDATE SET
        receipt_id=EXCLUDED.receipt_id,publication_sequence=EXCLUDED.publication_sequence,
        payload_digest=EXCLUDED.payload_digest,source_revision=EXCLUDED.source_revision,
        processing_generation=EXCLUDED.processing_generation,ontology_release=EXCLUDED.ontology_release,
        snapshot_id=EXCLUDED.snapshot_id"""),
        {
            **receipt.source_key.model_dump(),
            "receipt": receipt.receipt_id,
            "sequence": receipt.publication_sequence,
            "digest": receipt.payload_digest,
            "revision": receipt.source_version.revision,
            "generation": receipt.processing_version.generation,
            "release": receipt.processing_version.ontology_release,
            "snapshot": snapshot_id,
        },
    )


def apply(session, claim, result, principal, *, lineage):
    result = AuthorizedKnowledge.model_validate(result.model_dump())
    receipt, payload = result.receipt, result.payload
    key = SourceKey.model_validate(
        {
            k: asdict(claim)[k]
            for k in ("lab_id", "dataset_id", "source_kind", "source_id")
        }
    )
    if (
        key != receipt.source_key
        or claim.claimed_version != receipt.source_version.revision
    ):
        raise ValueError("stale_source")
    measured_file = key.source_kind == 'file'
    extractor = measured.EXTRACTOR if measured_file else facts.EXTRACTOR_VERSION
    if payload.mappings or any(
        f.evidence_kind != ("file_measurement" if measured_file else "human_review") for f in payload.facts
    ):
        raise ValueError("unsupported_knowledge")
    ontology.current_manifest(
        session
    )  # Ontology before queue; never acquire knowledge lock here.
    queue = (
        session.execute(
            text("SELECT * FROM d3_search_change WHERE " + _KEY + " FOR UPDATE"),
            key.model_dump(),
        )
        .mappings()
        .first()
    )
    if queue is None:
        raise ValueError("forbidden")
    status = authority.authorize_read(session, receipt, principal,lineage=lineage)
    if status != "current":
        raise ValueError(status)
    source = measured.load_source(session, claim) if measured_file else facts.load_source(session, claim)
    expected = _normalized([f.model_dump(mode="json") for f in payload.facts])
    if (
        source is None
        or source["status"] != "ready"
        or _normalized(source["facts"]) != expected
    ):
        raise ValueError("source facts mismatch")
    ledger = (
        session.execute(
            text("SELECT * FROM d3_knowledge_projection WHERE " + _KEY),
            key.model_dump(),
        )
        .mappings()
        .first()
    )
    if ledger:
        if receipt.publication_sequence < ledger["publication_sequence"]:
            raise ValueError("stale_sequence")
        if receipt.publication_sequence == ledger["publication_sequence"] and (
            receipt.receipt_id != ledger["receipt_id"]
            or receipt.payload_digest != ledger["payload_digest"]
        ):
            raise ValueError("idempotency_conflict")
    current = [
        row
        for row in facts.read_current(session, key.dataset_id, extractor_version=extractor)
        if row["source_kind"] == key.source_kind
        and row["source_id"] == key.source_id
        and row["source_version"] == receipt.source_version.revision
    ]
    snapshot = next(
        (row for row in current if _normalized(row["facts"]) == expected), None
    )
    if (
        ledger
        and receipt.receipt_id == ledger["receipt_id"]
        and receipt.publication_sequence == ledger["publication_sequence"]
        and ledger["source_revision"] == receipt.source_version.revision
        and ledger["processing_generation"] == receipt.processing_version.generation
        and ledger["ontology_release"] == receipt.processing_version.ontology_release
        and snapshot
        and snapshot["id"] == ledger["snapshot_id"]
        and queue["requested_version"]
        == queue["processed_version"]
        == receipt.source_version.revision
        and queue["claimed_version"] is None
        and queue["lease_until"] is None
    ):
        return {"status": "already_applied", "fact_id": snapshot["id"]}
    if not changes.is_current(session, claim):
        raise ValueError("stale_claim")
    if facts.process(session, claim, extractor_version=extractor) != "ready":
        raise ValueError("source unavailable")
    snapshot = next(
        (
            row
            for row in facts.read_current(session, key.dataset_id, extractor_version=extractor)
            if row["source_kind"] == key.source_kind
            and row["source_id"] == key.source_id
            and row["source_version"] == receipt.source_version.revision
            and _normalized(row["facts"]) == expected
        ),
        None,
    )
    if snapshot is None:
        raise ValueError("source changed during projection")
    _save(session, receipt, snapshot["id"])
    return {"status": "applied", "fact_id": snapshot["id"]}
