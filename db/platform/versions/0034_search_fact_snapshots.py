"""Source-versioned, lab-scoped search facts with provenance."""
from alembic import op

revision = "0034_search_fact_snapshots"
down_revision = "0033_search_changes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
-- D3 source facts retain provenance; they never write the common D9 ontology.
CREATE TABLE d3_search_fact_snapshot (
  id ulid PRIMARY KEY,
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  dataset_id ulid NOT NULL,
  source_kind text NOT NULL CHECK (source_kind IN ('metadata','file','evidence')),
  source_id ulid NOT NULL,
  source_version bigint NOT NULL CHECK (source_version > 0),
  file_revision integer CHECK (file_revision > 0),
  evidence_revision integer CHECK (evidence_revision > 0),
  source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
  extractor_version text NOT NULL CHECK (length(btrim(extractor_version)) BETWEEN 1 AND 100),
  ontology_snapshot_id text CHECK (ontology_snapshot_id IS NULL),
  status text NOT NULL CHECK (status IN ('candidate','ready')),
  facts jsonb NOT NULL CHECK (jsonb_typeof(facts) = 'array'),
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  UNIQUE (lab_id,source_kind,source_id,source_version,extractor_version),
  CHECK ((source_kind='metadata') = (file_revision IS NULL)),
  CHECK ((source_kind='evidence') = (evidence_revision IS NOT NULL))
);
CREATE INDEX d3_search_fact_snapshot_source_idx ON d3_search_fact_snapshot
  (lab_id,dataset_id,source_kind,source_id,source_version);
ALTER TABLE d3_search_fact_snapshot ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_search_fact_snapshot FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_search_fact_snapshot FOR ALL
USING (
  lab_id=current_lab_id()
  AND EXISTS (SELECT 1 FROM d3_dataset d WHERE d.id=d3_search_fact_snapshot.dataset_id
    AND d.lab_id=d3_search_fact_snapshot.lab_id AND d.deleted_at IS NULL)
  AND EXISTS (SELECT 1 FROM d3_search_change q WHERE q.lab_id=d3_search_fact_snapshot.lab_id
    AND q.source_kind=d3_search_fact_snapshot.source_kind AND q.source_id=d3_search_fact_snapshot.source_id
    AND q.dataset_id=d3_search_fact_snapshot.dataset_id AND NOT q.deleted
    AND q.requested_version=d3_search_fact_snapshot.source_version)
  AND (source_kind='metadata' OR EXISTS (SELECT 1 FROM d3_file f
    WHERE f.id=d3_search_fact_snapshot.source_id AND f.dataset_id=d3_search_fact_snapshot.dataset_id
      AND f.lab_id=d3_search_fact_snapshot.lab_id AND f.content_revision=d3_search_fact_snapshot.file_revision))
  AND (source_kind<>'evidence' OR EXISTS (SELECT 1 FROM d3_search_evidence e
    WHERE e.file_id=d3_search_fact_snapshot.source_id AND e.lab_id=d3_search_fact_snapshot.lab_id
      AND e.revision=d3_search_fact_snapshot.evidence_revision
      AND e.file_revision=d3_search_fact_snapshot.file_revision))
);
    """)


def downgrade() -> None:
    raise RuntimeError("Fact history rollback requires an explicit retention plan")
