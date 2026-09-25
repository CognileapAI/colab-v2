"""Persistent D3 source authority grants; no D9 storage access."""
from alembic import op

revision = "0037_knowledge_source_grants"
down_revision = "0036_search_refresh_runtime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
-- D3-owned source processing fences; authenticated app adapters own issuance.
CREATE TABLE d3_knowledge_source (
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  dataset_id ulid NOT NULL REFERENCES d3_dataset(id) ON DELETE CASCADE,
  source_kind text NOT NULL CHECK (source_kind='evidence'),
  source_id ulid NOT NULL,
  generation bigint NOT NULL CHECK (generation>0),
  command jsonb NOT NULL CHECK (jsonb_typeof(command)='object' AND NOT command ? 'grant'),
  PRIMARY KEY (lab_id,source_kind,source_id)
);
ALTER TABLE d3_knowledge_source ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_knowledge_source FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_knowledge_source FOR ALL USING (
  lab_id=current_lab_id() AND EXISTS (SELECT 1 FROM d3_file f JOIN d3_dataset d ON d.id=f.dataset_id
    WHERE f.id=source_id AND f.dataset_id=d3_knowledge_source.dataset_id
      AND f.lab_id=d3_knowledge_source.lab_id AND d.deleted_at IS NULL)
);
CREATE TABLE d3_knowledge_grant (
  grant_hash text PRIMARY KEY CHECK (grant_hash ~ '^[0-9a-f]{64}$'),
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  dataset_id ulid NOT NULL REFERENCES d3_dataset(id) ON DELETE CASCADE,
  source_kind text NOT NULL CHECK (source_kind='evidence'),
  source_id ulid NOT NULL,
  account_id ulid NOT NULL REFERENCES d1_account(id),
  session_version bigint NOT NULL CHECK (session_version>0),
  generation bigint NOT NULL CHECK (generation>0),
  payload_digest text NOT NULL CHECK (payload_digest ~ '^[0-9a-f]{64}$'),
  expires_at timestamptz NOT NULL
);
ALTER TABLE d3_knowledge_grant ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_knowledge_grant FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_knowledge_grant FOR ALL USING (
  lab_id=current_lab_id() AND account_id=current_account_id() AND EXISTS (
    SELECT 1 FROM d3_knowledge_source s WHERE s.lab_id=d3_knowledge_grant.lab_id
      AND s.source_kind=d3_knowledge_grant.source_kind AND s.source_id=d3_knowledge_grant.source_id
      AND s.dataset_id=d3_knowledge_grant.dataset_id)
);
    """)


def downgrade() -> None:
    raise RuntimeError("Grant history rollback requires an explicit retention plan")

