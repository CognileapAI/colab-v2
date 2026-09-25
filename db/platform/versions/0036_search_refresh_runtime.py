"""Grounded search selections and persistent scoped refresh state."""
from alembic import op
revision = "0036_search_refresh_runtime"
down_revision = "0035_search_ontology"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
-- Selected search connections are derived facts, never writes to the D9 dictionary.
CREATE TABLE d3_search_concept_match (
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  binding_id ulid NOT NULL REFERENCES d3_search_ontology_binding(id) ON DELETE CASCADE,
  dataset_id ulid NOT NULL,
  concept_id text NOT NULL,
  label text NOT NULL CHECK (length(label) BETWEEN 1 AND 120),
  quote text NOT NULL CHECK (length(quote) BETWEEN 1 AND 500),
  source_locator text NOT NULL CHECK (length(source_locator)>0),
  terms text[] NOT NULL CHECK (cardinality(terms) BETWEEN 1 AND 65),
  PRIMARY KEY (lab_id,binding_id,concept_id)
);
CREATE INDEX d3_search_concept_match_terms_idx ON d3_search_concept_match USING gin(terms);
ALTER TABLE d3_search_concept_match ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_search_concept_match FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_search_concept_match FOR ALL USING (
  lab_id=current_lab_id() AND dataset_id=(
    SELECT f.dataset_id FROM d3_search_fact_snapshot f WHERE f.id=(
      SELECT b.fact_snapshot_id FROM d3_search_ontology_binding b
      WHERE b.id=d3_search_concept_match.binding_id AND b.lab_id=d3_search_concept_match.lab_id))
);
CREATE TABLE d3_search_refresh_run (
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  account_id ulid NOT NULL REFERENCES d1_account(id),
  generation bigint NOT NULL DEFAULT 0,
  lease_until timestamptz,
  next_run timestamptz NOT NULL DEFAULT clock_timestamp(),
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','complete','failed')),
  bootstrap jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(bootstrap)='object'),
  manifest_checked_at timestamptz,
  summary jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(summary)='object'),
  updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (lab_id,account_id)
);
ALTER TABLE d3_search_refresh_run ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_search_refresh_run FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_search_refresh_run FOR ALL USING (
  lab_id=current_lab_id() AND account_id=current_account_id() AND EXISTS (
    SELECT 1 FROM d1_account a WHERE a.id=account_id AND a.lab_id=d3_search_refresh_run.lab_id)
);

-- Zero selections and never-run selection are different states.
CREATE TABLE d3_search_selection_receipt (
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  binding_id ulid NOT NULL REFERENCES d3_search_ontology_binding(id) ON DELETE CASCADE,
  selector_version text NOT NULL CHECK (length(selector_version) BETWEEN 1 AND 100),
  PRIMARY KEY (lab_id,binding_id)
);
ALTER TABLE d3_search_selection_receipt ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_search_selection_receipt FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_search_selection_receipt FOR ALL USING (
  lab_id=current_lab_id() AND EXISTS (SELECT 1 FROM d3_search_ontology_binding b
    WHERE b.id=binding_id AND b.lab_id=d3_search_selection_receipt.lab_id)
);
    """)


def downgrade() -> None:
    raise RuntimeError("Search refresh rollback requires an explicit retention plan")
