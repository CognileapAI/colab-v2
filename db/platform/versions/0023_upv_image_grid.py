"""대표 그림 원장과 사람 격자 설명을 더한다.

Revision ID: 0023_upv_image_grid
Revises: 0022_rc7_variable_mirror_stmt
"""
from __future__ import annotations

from alembic import op

revision = "0023_upv_image_grid"
down_revision = "0022_rc7_variable_mirror_stmt"
branch_labels = None
depends_on = None


UPGRADE = r"""
ALTER TABLE d3_dataset_description
  ADD COLUMN human_grid_description text
  CONSTRAINT d3_dataset_description_human_grid_description_check
  CHECK (human_grid_description IS NULL
         OR length(btrim(human_grid_description)) BETWEEN 1 AND 1000);

CREATE TABLE d3_dataset_representative_image (
  dataset_id  ulid        PRIMARY KEY REFERENCES d3_dataset(id) ON DELETE CASCADE,
  lab_id      ulid        NOT NULL REFERENCES d1_lab(id),
  image_id    ulid        NOT NULL UNIQUE,
  file_name   text        NOT NULL CHECK (length(btrim(file_name)) BETWEEN 1 AND 255),
  content_type text       NOT NULL CHECK (content_type IN ('image/png', 'image/jpeg', 'image/webp')),
  size_bytes  bigint      NOT NULL CHECK (size_bytes BETWEEN 1 AND 10485760),
  storage_key text        NOT NULL UNIQUE CHECK (length(btrim(storage_key)) BETWEEN 1 AND 1024),
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX d3_dataset_representative_image_lab_idx
  ON d3_dataset_representative_image (lab_id);
ALTER TABLE d3_dataset_representative_image ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset_representative_image FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_dataset_representative_image FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

CREATE TABLE d3_representative_image_cleanup (
  cleanup_id  ulid        PRIMARY KEY,
  lab_id      ulid        NOT NULL REFERENCES d1_lab(id),
  dataset_id  ulid        NOT NULL,
  storage_key text        NOT NULL UNIQUE CHECK (length(btrim(storage_key)) BETWEEN 1 AND 1024),
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX d3_representative_image_cleanup_lab_dataset_idx
  ON d3_representative_image_cleanup (lab_id, dataset_id, created_at, cleanup_id);
ALTER TABLE d3_representative_image_cleanup ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_representative_image_cleanup FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_representative_image_cleanup FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());
"""

DOWNGRADE = r"""
DROP TABLE d3_representative_image_cleanup;
DROP TABLE d3_dataset_representative_image;
ALTER TABLE d3_dataset_description DROP COLUMN human_grid_description;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
