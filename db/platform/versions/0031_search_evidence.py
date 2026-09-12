"""File content revisions and source-backed search evidence.

Revision ID: 0031_search_evidence
Revises: 0027_operator_audit
"""
from alembic import op

revision = "0031_search_evidence"
down_revision = "0030_merge_audit_and_backoffice"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    ALTER TABLE d3_file
      ADD COLUMN content_revision integer NOT NULL DEFAULT 1
        CHECK (content_revision > 0),
      ADD CONSTRAINT d3_file_lab_dataset_id_unique UNIQUE (lab_id, dataset_id, id);
    CREATE FUNCTION increment_d3_file_content_revision() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
      NEW.content_revision := OLD.content_revision + 1;
      RETURN NEW;
    END $$;
    CREATE TRIGGER d3_file_content_revision BEFORE UPDATE OF storage_key, size_bytes ON d3_file
      FOR EACH ROW EXECUTE FUNCTION increment_d3_file_content_revision();
    CREATE TABLE d3_search_evidence (
      file_id ulid PRIMARY KEY, lab_id ulid NOT NULL REFERENCES d1_lab(id), dataset_id ulid NOT NULL,
      file_revision integer NOT NULL CHECK (file_revision > 0),
      revision integer NOT NULL CHECK (revision > 0),
      status text NOT NULL CHECK (status IN ('draft', 'reviewed')),
      facts jsonb NOT NULL CHECK (jsonb_typeof(facts) = 'object' AND facts <> '{}'::jsonb),
      source_label text NOT NULL CHECK (length(btrim(source_label)) BETWEEN 1 AND 200),
      source_locator text NOT NULL CHECK (length(btrim(source_locator)) BETWEEN 1 AND 300),
      source_text text NOT NULL CHECK (length(source_text) BETWEEN 1 AND 20000),
      source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
      reviewed_by ulid REFERENCES d1_account(id), reviewed_at timestamptz,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
      CONSTRAINT d3_search_evidence_file_fk FOREIGN KEY (lab_id, dataset_id, file_id)
        REFERENCES d3_file(lab_id, dataset_id, id) ON DELETE CASCADE,
      CONSTRAINT d3_search_evidence_review_pair CHECK (
        (status = 'reviewed' AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)
        OR (status = 'draft' AND reviewed_by IS NULL AND reviewed_at IS NULL)));
    CREATE INDEX d3_search_evidence_dataset_idx ON d3_search_evidence(dataset_id, file_id);
    ALTER TABLE d3_search_evidence ENABLE ROW LEVEL SECURITY;
    ALTER TABLE d3_search_evidence FORCE ROW LEVEL SECURITY;
    CREATE POLICY lab_boundary ON d3_search_evidence FOR ALL
      USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());
    CREATE POLICY body_access ON d3_search_evidence AS RESTRICTIVE FOR ALL
      USING (EXISTS (SELECT 1 FROM d3_file f WHERE f.id=d3_search_evidence.file_id
        AND f.dataset_id=d3_search_evidence.dataset_id AND f.lab_id=d3_search_evidence.lab_id))
      WITH CHECK (EXISTS (SELECT 1 FROM d3_file f WHERE f.id=d3_search_evidence.file_id
        AND f.dataset_id=d3_search_evidence.dataset_id AND f.lab_id=d3_search_evidence.lab_id));
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE d3_search_evidence;
    DROP TRIGGER d3_file_content_revision ON d3_file;
    DROP FUNCTION increment_d3_file_content_revision();
    ALTER TABLE d3_file DROP CONSTRAINT d3_file_lab_dataset_id_unique;
    ALTER TABLE d3_file DROP COLUMN content_revision;
    """)
