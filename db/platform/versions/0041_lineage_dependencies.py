"""Retained D4 incident-set revisions, including deleted datasets.

Migration requires the existing table owner; scoped runtime readers never backfill.
"""
from alembic import op

revision = '0041_lineage_dependencies'
down_revision = '0040_file_measurement'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('''
CREATE TABLE d4_lineage_revision (
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  dataset_id ulid NOT NULL,
  revision bigint NOT NULL CHECK (revision>0),
  deleted boolean NOT NULL,
  PRIMARY KEY (lab_id,dataset_id)
);
ALTER TABLE d3_dataset DISABLE ROW LEVEL SECURITY;
INSERT INTO d4_lineage_revision
  SELECT lab_id,id,1,deleted_at IS NOT NULL FROM d3_dataset;
ALTER TABLE d3_dataset ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset FORCE ROW LEVEL SECURITY;
ALTER TABLE d4_lineage_revision ENABLE ROW LEVEL SECURITY;
ALTER TABLE d4_lineage_revision FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d4_lineage_revision FOR ALL
  USING (lab_id=current_lab_id()) WITH CHECK (lab_id=current_lab_id());
CREATE TABLE d3_knowledge_dependency (
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  dataset_id ulid NOT NULL,
  source_kind text NOT NULL CHECK (source_kind IN ('evidence','file')),
  source_id ulid NOT NULL,
  lineage_revision bigint NOT NULL CHECK (lineage_revision>0),
  PRIMARY KEY (lab_id,source_kind,source_id)
);
ALTER TABLE d3_knowledge_dependency ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_knowledge_dependency FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_knowledge_dependency FOR ALL USING (
  lab_id=current_lab_id() AND EXISTS (SELECT 1 FROM d3_file f JOIN d3_dataset d ON d.id=f.dataset_id
    WHERE f.id=source_id AND f.dataset_id=d3_knowledge_dependency.dataset_id
      AND f.lab_id=d3_knowledge_dependency.lab_id AND d.deleted_at IS NULL)
);
''')


def downgrade():
    raise RuntimeError('Retained lineage revision rollback requires an explicit retention plan')
