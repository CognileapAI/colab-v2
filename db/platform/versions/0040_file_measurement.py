"""D5 per-file proof and D3 registered immutable binding, separate from aggregate events."""

from alembic import op

revision = "0040_file_measurement"
down_revision = "0039_knowledge_projection"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
CREATE TABLE d5_file_measurement (
  id ulid PRIMARY KEY,
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  upload_id ulid NOT NULL REFERENCES d5_upload(id) ON DELETE CASCADE,
  upload_file_id ulid NOT NULL REFERENCES d5_upload_file(id) ON DELETE CASCADE,
  issuer text NOT NULL DEFAULT 'pipeline-worker' CHECK (issuer='pipeline-worker'),
  parser_version text NOT NULL CHECK (parser_version='file-measurement-v1'),
  storage_key text NOT NULL CHECK (length(storage_key)>0),
  source_digest text NOT NULL CHECK (source_digest ~ '^[0-9a-f]{64}$'),
  byte_size bigint NOT NULL CHECK (byte_size>=0),
  measured_format text NOT NULL CHECK (measured_format IN ('npy','netcdf','tif','hdf5')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (upload_file_id,storage_key,source_digest,byte_size,parser_version)
);
ALTER TABLE d5_file_measurement ENABLE ROW LEVEL SECURITY;
ALTER TABLE d5_file_measurement FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d5_file_measurement FOR ALL
 USING (lab_id=current_lab_id())
 WITH CHECK (lab_id=current_lab_id() AND EXISTS (
   SELECT 1 FROM d5_upload_file f WHERE f.id=upload_file_id
     AND f.upload_id=d5_file_measurement.upload_id AND f.lab_id=d5_file_measurement.lab_id
     AND f.storage_key=d5_file_measurement.storage_key AND f.kind='본체'));
CREATE FUNCTION d5_measurement_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'file measurement receipts are immutable' USING ERRCODE='23514';
END $$;
CREATE TRIGGER d5_measurement_immutable BEFORE UPDATE ON d5_file_measurement
 FOR EACH ROW EXECUTE FUNCTION d5_measurement_immutable();
CREATE TABLE d3_file_measurement (
  file_id ulid PRIMARY KEY REFERENCES d3_file(id) ON DELETE CASCADE,
  lab_id ulid NOT NULL REFERENCES d1_lab(id),
  dataset_id ulid NOT NULL REFERENCES d3_dataset(id) ON DELETE CASCADE,
  file_revision bigint NOT NULL CHECK (file_revision>0),
  storage_key text NOT NULL CHECK (length(storage_key)>0),
  receipt_id ulid NOT NULL,
  issuer text NOT NULL CHECK (issuer='pipeline-worker'),
  parser_version text NOT NULL CHECK (parser_version='file-measurement-v1'),
  source_digest text NOT NULL CHECK (source_digest ~ '^[0-9a-f]{64}$'),
  byte_size bigint NOT NULL CHECK (byte_size>=0),
  measured_format text NOT NULL CHECK (measured_format IN ('npy','netcdf','tif','hdf5'))
);
ALTER TABLE d3_file_measurement ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_file_measurement FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_file_measurement FOR ALL
 USING (lab_id=current_lab_id() AND EXISTS (
   SELECT 1 FROM d3_file f JOIN d3_dataset d ON d.id=f.dataset_id
    WHERE f.id=file_id AND f.dataset_id=d3_file_measurement.dataset_id
      AND f.lab_id=d3_file_measurement.lab_id AND d.deleted_at IS NULL));
CREATE FUNCTION d3_measurement_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'registered measurement snapshots are immutable' USING ERRCODE='23514';
END $$;
CREATE TRIGGER d3_measurement_immutable BEFORE UPDATE ON d3_file_measurement
 FOR EACH ROW EXECUTE FUNCTION d3_measurement_immutable();
""")
    for table in ('d3_knowledge_source','d3_knowledge_grant','d3_knowledge_fence',
                  'd3_knowledge_deletion_grant','d3_knowledge_projection'):
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {table}_source_kind_check")
        op.execute(f"ALTER TABLE {table} ADD CONSTRAINT {table}_source_kind_check CHECK (source_kind IN ('evidence','file'))")


def downgrade():
    raise RuntimeError("Measurement rollback requires an explicit provenance retention plan")
