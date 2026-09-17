"""Source-scoped knowledge replacement, independent of public ontology ACL."""
from alembic import op

revision = '0008_dataset_knowledge'
down_revision = '0007_merge_vocab_and_category'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
CREATE SCHEMA knowledge;
REVOKE ALL ON SCHEMA knowledge FROM PUBLIC;
CREATE DOMAIN knowledge.ulid AS text CHECK (VALUE ~ '^[0-9A-HJKMNP-TV-Z]{26}$');
CREATE TABLE knowledge.d9_knowledge_source (
  lab_id knowledge.ulid NOT NULL,
  dataset_id knowledge.ulid NOT NULL,
  source_kind text NOT NULL CHECK (source_kind IN ('metadata','file','evidence','lineage')),
  source_id knowledge.ulid NOT NULL,
  generation bigint NOT NULL CHECK (generation > 0),
  source_revision bigint NOT NULL CHECK (source_revision > 0),
  publication_sequence bigint NOT NULL CHECK (publication_sequence > 0),
  payload_digest text NOT NULL CHECK (length(payload_digest) = 64),
  payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object' AND NOT payload ? 'grant'),
  receipt jsonb NOT NULL CHECK (jsonb_typeof(receipt) = 'object'),
  PRIMARY KEY (lab_id,dataset_id,source_kind,source_id)
);
ALTER TABLE knowledge.d9_knowledge_source ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge.d9_knowledge_source FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON knowledge.d9_knowledge_source
  USING (lab_id = current_setting('knowledge.lab_id',true)
    AND dataset_id = current_setting('knowledge.dataset_id',true)
    AND source_kind = current_setting('knowledge.source_kind',true)
    AND source_id = current_setting('knowledge.source_id',true))
  WITH CHECK (lab_id = current_setting('knowledge.lab_id',true)
    AND dataset_id = current_setting('knowledge.dataset_id',true)
    AND source_kind = current_setting('knowledge.source_kind',true)
    AND source_id = current_setting('knowledge.source_id',true));
''')


def downgrade():
    raise RuntimeError('Knowledge history requires an explicit forward migration.')
