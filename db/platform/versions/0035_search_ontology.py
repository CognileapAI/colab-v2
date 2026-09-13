"""Ontology content receipts and per-source interpretation dependencies."""
from alembic import op

revision = "0035_search_ontology"
down_revision = "0034_search_fact_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
-- Lab-local receipts and read dependencies. The common ontology remains read-only.
CREATE TABLE d3_search_ontology_release (
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  version text NOT NULL CHECK (version ~ '^[0-9a-f]{64}$'),
  manifest jsonb NOT NULL CHECK (jsonb_typeof(manifest)='object'),
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (lab_id,version)
);
CREATE TABLE d3_search_ontology_head (
  lab_id ulid PRIMARY KEY REFERENCES d1_lab(id),
  version text NOT NULL,
  FOREIGN KEY (lab_id,version) REFERENCES d3_search_ontology_release(lab_id,version)
);
CREATE TABLE d3_search_ontology_binding (
  id ulid PRIMARY KEY,
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  fact_snapshot_id ulid NOT NULL REFERENCES d3_search_fact_snapshot(id),
  ontology_version text NOT NULL,
  expected_dependencies jsonb NOT NULL CHECK (jsonb_typeof(expected_dependencies)='object' AND expected_dependencies ? 'discovery'),
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  FOREIGN KEY (lab_id,ontology_version) REFERENCES d3_search_ontology_release(lab_id,version),
  UNIQUE (lab_id,fact_snapshot_id,ontology_version)
);
CREATE TABLE d3_search_ontology_dependency (
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  binding_id ulid NOT NULL REFERENCES d3_search_ontology_binding(id),
  dependency_key text NOT NULL,
  digest text NOT NULL CHECK (digest ~ '^[0-9a-f]{64}$'),
  PRIMARY KEY (lab_id,binding_id,dependency_key)
);
CREATE INDEX d3_search_ontology_dependency_lookup_idx ON d3_search_ontology_dependency
  (lab_id,dependency_key,digest,binding_id);
ALTER TABLE d3_search_ontology_release ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_search_ontology_release FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_search_ontology_release FOR ALL USING (lab_id=current_lab_id());
ALTER TABLE d3_search_ontology_head ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_search_ontology_head FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_search_ontology_head FOR ALL USING (lab_id=current_lab_id());
ALTER TABLE d3_search_ontology_binding ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_search_ontology_binding FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_search_ontology_binding FOR ALL USING (
  lab_id=current_lab_id() AND EXISTS (
    SELECT 1 FROM d3_search_fact_snapshot f WHERE f.id=fact_snapshot_id
      AND f.lab_id=d3_search_ontology_binding.lab_id AND f.status='ready')
);
ALTER TABLE d3_search_ontology_dependency ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_search_ontology_dependency FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_search_ontology_dependency FOR ALL USING (
  lab_id=current_lab_id() AND EXISTS (
    SELECT 1 FROM d3_search_ontology_binding b WHERE b.id=binding_id
      AND b.lab_id=d3_search_ontology_dependency.lab_id)
);
    """)


def downgrade() -> None:
    raise RuntimeError("Ontology receipt rollback requires an explicit retention plan")
