"""D3 receipt sequence ledger; snapshot deletion does not erase its fence."""

from alembic import op

revision = "0039_knowledge_projection"
down_revision = "0038_knowledge_deletion"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
CREATE TABLE d3_knowledge_projection (
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  dataset_id ulid NOT NULL,
  source_kind text NOT NULL CHECK (source_kind='evidence'),
  source_id ulid NOT NULL,
  receipt_id ulid NOT NULL,
  publication_sequence bigint NOT NULL CHECK (publication_sequence>0),
  payload_digest text NOT NULL CHECK (payload_digest ~ '^[0-9a-f]{64}$'),
  source_revision bigint NOT NULL CHECK (source_revision>0),
  processing_generation bigint NOT NULL CHECK (processing_generation>0),
  ontology_release text NOT NULL CHECK (ontology_release ~ '^[0-9a-f]{64}$'),
  snapshot_id ulid REFERENCES d3_search_fact_snapshot(id) ON DELETE SET NULL,
  PRIMARY KEY (lab_id,dataset_id,source_kind,source_id)
);
ALTER TABLE d3_knowledge_projection ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_knowledge_projection FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_knowledge_projection FOR ALL USING (
  lab_id=current_lab_id() AND EXISTS (SELECT 1 FROM d3_file f JOIN d3_dataset d ON d.id=f.dataset_id
    WHERE f.id=source_id AND f.dataset_id=d3_knowledge_projection.dataset_id
      AND f.lab_id=d3_knowledge_projection.lab_id AND d.deleted_at IS NULL)
);
""")


def downgrade():
    raise RuntimeError(
        "Projection sequence rollback requires an explicit retention plan"
    )
