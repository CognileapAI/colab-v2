"""Body-free source fence survives private source deletion.

Requires the existing migration table-owner privilege. RLS is disabled only
inside this transactional upgrade so hidden rows cannot silently evade backfill.
No runtime role obtains BYPASSRLS and all policies are restored before commit.
"""
from alembic import op

revision = '0038_knowledge_deletion'
down_revision = '0037_knowledge_source_grants'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
CREATE TABLE d3_knowledge_fence (
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  dataset_id ulid NOT NULL,
  source_kind text NOT NULL CHECK (source_kind='evidence'),
  source_id ulid NOT NULL,
  generation bigint NOT NULL CHECK (generation>0),
  source_revision bigint NOT NULL CHECK (source_revision>0),
  deleted boolean NOT NULL,
  PRIMARY KEY (lab_id,dataset_id,source_kind,source_id)
);
ALTER TABLE d3_knowledge_source DISABLE ROW LEVEL SECURITY;
INSERT INTO d3_knowledge_fence
  SELECT lab_id,dataset_id,source_kind,source_id,generation,
         (command->'source_version'->>'revision')::bigint,false
  FROM d3_knowledge_source;
ALTER TABLE d3_knowledge_source ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_knowledge_source FORCE ROW LEVEL SECURITY;
ALTER TABLE d3_knowledge_fence ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_knowledge_fence FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_knowledge_fence FOR ALL
  USING (lab_id=current_lab_id()) WITH CHECK (lab_id=current_lab_id());
CREATE TABLE d3_knowledge_deletion_grant (
  grant_hash text PRIMARY KEY CHECK (grant_hash ~ '^[0-9a-f]{64}$'),
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  dataset_id ulid NOT NULL,
  source_kind text NOT NULL CHECK (source_kind='evidence'),
  source_id ulid NOT NULL,
  source_revision bigint NOT NULL CHECK (source_revision>0),
  generation bigint NOT NULL CHECK (generation>0),
  payload_digest text NOT NULL CHECK (payload_digest ~ '^[0-9a-f]{64}$'),
  expires_at timestamptz NOT NULL
);
ALTER TABLE d3_knowledge_deletion_grant ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_knowledge_deletion_grant FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_knowledge_deletion_grant FOR ALL
  USING (lab_id=current_lab_id() AND current_account_id() IS NULL)
  WITH CHECK (lab_id=current_lab_id() AND current_account_id() IS NULL);
''')


def downgrade():
    raise RuntimeError('Deletion fences require an explicit retention plan')
