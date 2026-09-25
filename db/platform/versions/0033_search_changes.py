"""Transactional source changes for incremental search indexing."""
from alembic import op

revision = "0033_search_changes"
down_revision = "0032_private_owner_access"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
-- Transactional, coalescing source pointers. No source FK: tombstones must survive deletion.
CREATE TABLE d3_search_change (
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  source_kind text NOT NULL CHECK (source_kind IN ('metadata', 'file', 'evidence')),
  source_id ulid NOT NULL,
  dataset_id ulid NOT NULL,
  requested_version bigint NOT NULL DEFAULT 1 CHECK (requested_version > 0),
  processed_version bigint NOT NULL DEFAULT 0,
  deleted boolean NOT NULL DEFAULT false,
  updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  lease_generation bigint NOT NULL DEFAULT 0 CHECK (lease_generation >= 0),
  claimed_version bigint,
  lease_until timestamptz,
  attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  retry_after timestamptz NOT NULL DEFAULT clock_timestamp(),
  last_error_code text CHECK (last_error_code IN ('source_unavailable', 'processing_failed', 'transient')),
  PRIMARY KEY (lab_id, source_kind, source_id),
  CHECK (processed_version >= 0 AND processed_version <= requested_version),
  CHECK ((claimed_version IS NULL) = (lease_until IS NULL)),
  CHECK (claimed_version IS NULL OR (claimed_version > processed_version AND claimed_version <= requested_version))
);
CREATE INDEX d3_search_change_pending_idx ON d3_search_change (lab_id, retry_after, updated_at)
  WHERE requested_version > processed_version;
ALTER TABLE d3_search_change ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_search_change FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_search_change FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

CREATE FUNCTION record_d3_search_change() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  source_row jsonb;
  kind text := TG_ARGV[0];
  source_key ulid;
  dataset_key ulid;
  is_deleted boolean;
BEGIN
  IF TG_OP = 'UPDATE' AND NEW IS NOT DISTINCT FROM OLD THEN RETURN NEW; END IF;
  IF TG_OP = 'DELETE' THEN source_row := to_jsonb(OLD);
  ELSE source_row := to_jsonb(NEW); END IF;
  IF TG_TABLE_NAME = 'd3_dataset' THEN dataset_key := source_row->>'id';
  ELSE dataset_key := source_row->>'dataset_id'; END IF;
  IF kind = 'metadata' THEN
    source_key := dataset_key;
    SELECT NOT EXISTS (SELECT 1 FROM d3_dataset WHERE id=dataset_key AND deleted_at IS NULL)
      INTO is_deleted;
  ELSE
    source_key := coalesce(source_row->>'file_id', source_row->>'id');
    is_deleted := TG_OP = 'DELETE';
  END IF;
  INSERT INTO d3_search_change (lab_id, source_kind, source_id, dataset_id, deleted)
    VALUES ((source_row->>'lab_id')::ulid, kind, source_key, dataset_key, is_deleted)
  ON CONFLICT (lab_id, source_kind, source_id) DO UPDATE
    SET requested_version=d3_search_change.requested_version+1,
        dataset_id=EXCLUDED.dataset_id, deleted=EXCLUDED.deleted, updated_at=clock_timestamp();
  IF TG_OP = 'DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
END $$;
CREATE CONSTRAINT TRIGGER d3_dataset_search_change AFTER INSERT OR UPDATE OR DELETE ON d3_dataset
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION record_d3_search_change('metadata');
CREATE CONSTRAINT TRIGGER d3_dataset_description_search_change AFTER INSERT OR UPDATE OR DELETE ON d3_dataset_description
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION record_d3_search_change('metadata');
CREATE CONSTRAINT TRIGGER d3_dataset_autometa_search_change AFTER INSERT OR UPDATE OR DELETE ON d3_dataset_autometa
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION record_d3_search_change('metadata');
CREATE CONSTRAINT TRIGGER d3_dataset_variable_search_change AFTER INSERT OR UPDATE OR DELETE ON d3_dataset_variable
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION record_d3_search_change('metadata');
CREATE CONSTRAINT TRIGGER d3_dataset_grid_profile_search_change AFTER INSERT OR UPDATE OR DELETE ON d3_dataset_grid_profile
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION record_d3_search_change('metadata');
CREATE CONSTRAINT TRIGGER d3_file_search_change AFTER INSERT OR UPDATE OR DELETE ON d3_file
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION record_d3_search_change('file');
CREATE CONSTRAINT TRIGGER d3_search_evidence_search_change AFTER INSERT OR UPDATE OR DELETE ON d3_search_evidence
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION record_d3_search_change('evidence');
    """)


def downgrade() -> None:
    # This ledger retains deletion pointers; rollback must not silently discard them.
    raise RuntimeError("Search change ledger rollback requires an explicit retention plan")
