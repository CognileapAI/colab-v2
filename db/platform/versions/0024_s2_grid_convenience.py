"""Stage 2 격자 편의 프로필·기본값·첫 파일 미리보기 자리를 더한다.

Revision ID: 0024_s2_grid_convenience
Revises: 0023_upv_image_grid
"""
from __future__ import annotations

from alembic import op

revision = "0024_s2_grid_convenience"
down_revision = "0023_upv_image_grid"
branch_labels = None
depends_on = None


UPGRADE = r"""
ALTER TABLE d3_dataset
  ADD CONSTRAINT d3_dataset_lab_id_id_unique UNIQUE (lab_id, id);

CREATE TABLE d3_dataset_grid_profile (
  dataset_id            ulid        PRIMARY KEY,
  lab_id                ulid        NOT NULL REFERENCES d1_lab(id),
  body_shape            integer[],
  grid_shape            integer[],
  grid_digest           text,
  grid_format_signature text,
  west                  double precision,
  south                 double precision,
  east                  double precision,
  north                 double precision,
  map_state             text        NOT NULL CHECK (map_state IN ('지도 있음', '지도 없음', '아직 모름')),
  grid_source           text        NOT NULL CHECK (grid_source IN ('직접 업로드', '가져오기')),
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT d3_dataset_grid_profile_dataset_fk
    FOREIGN KEY (lab_id, dataset_id) REFERENCES d3_dataset(lab_id, id) ON DELETE CASCADE,
  CONSTRAINT d3_dataset_grid_profile_body_shape_2d
    CHECK (body_shape IS NULL OR (cardinality(body_shape) = 2 AND 0 < ALL(body_shape))),
  CONSTRAINT d3_dataset_grid_profile_grid_shape_2d
    CHECK (grid_shape IS NULL OR (cardinality(grid_shape) = 2 AND 0 < ALL(grid_shape))),
  CONSTRAINT d3_dataset_grid_profile_digest_sha256
    CHECK (grid_digest IS NULL OR grid_digest ~ '^[0-9a-f]{64}$'),
  CONSTRAINT d3_dataset_grid_profile_bounds_whole
    CHECK ((west IS NULL AND south IS NULL AND east IS NULL AND north IS NULL)
           OR (west IS NOT NULL AND south IS NOT NULL AND east IS NOT NULL AND north IS NOT NULL
               AND west BETWEEN -180 AND 180 AND east BETWEEN -180 AND 180
               AND south BETWEEN -90 AND 90 AND north BETWEEN -90 AND 90
               AND west < east AND south < north))
);
CREATE INDEX d3_dataset_grid_profile_lab_shape_idx
  ON d3_dataset_grid_profile (lab_id, grid_shape);
CREATE INDEX d3_dataset_grid_profile_lab_state_idx
  ON d3_dataset_grid_profile (lab_id, map_state);
ALTER TABLE d3_dataset_grid_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset_grid_profile FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_dataset_grid_profile FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

CREATE TABLE d3_lab_default_grid (
  lab_id      ulid        PRIMARY KEY REFERENCES d1_lab(id),
  dataset_id  ulid        NOT NULL UNIQUE,
  set_by      ulid        NOT NULL REFERENCES d1_account(id),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT d3_lab_default_grid_dataset_fk
    FOREIGN KEY (lab_id, dataset_id) REFERENCES d3_dataset(lab_id, id) ON DELETE CASCADE
);
ALTER TABLE d3_lab_default_grid ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_lab_default_grid FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_lab_default_grid FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

CREATE TABLE d5_upload_grid_profile (
  upload_id             ulid        PRIMARY KEY REFERENCES d5_upload(id) ON DELETE CASCADE,
  lab_id                ulid        NOT NULL REFERENCES d1_lab(id),
  body_shape            integer[],
  grid_shape            integer[],
  grid_digest           text,
  grid_format_signature text,
  west                  double precision,
  south                 double precision,
  east                  double precision,
  north                 double precision,
  map_state             text        NOT NULL CHECK (map_state IN ('지도 있음', '지도 없음', '아직 모름')),
  grid_source           text        NOT NULL CHECK (grid_source IN ('직접 업로드', '가져오기')),
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT d5_upload_grid_profile_body_shape_2d
    CHECK (body_shape IS NULL OR (cardinality(body_shape) = 2 AND 0 < ALL(body_shape))),
  CONSTRAINT d5_upload_grid_profile_grid_shape_2d
    CHECK (grid_shape IS NULL OR (cardinality(grid_shape) = 2 AND 0 < ALL(grid_shape))),
  CONSTRAINT d5_upload_grid_profile_digest_sha256
    CHECK (grid_digest IS NULL OR grid_digest ~ '^[0-9a-f]{64}$'),
  CONSTRAINT d5_upload_grid_profile_bounds_whole
    CHECK ((west IS NULL AND south IS NULL AND east IS NULL AND north IS NULL)
           OR (west IS NOT NULL AND south IS NOT NULL AND east IS NOT NULL AND north IS NOT NULL
               AND west BETWEEN -180 AND 180 AND east BETWEEN -180 AND 180
               AND south BETWEEN -90 AND 90 AND north BETWEEN -90 AND 90
               AND west < east AND south < north))
);
CREATE INDEX d5_upload_grid_profile_lab_idx ON d5_upload_grid_profile (lab_id);
ALTER TABLE d5_upload_grid_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE d5_upload_grid_profile FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d5_upload_grid_profile FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d5_upload_transfer
  ADD COLUMN early_preview_upload_id ulid REFERENCES d5_upload(id) ON DELETE SET NULL;
"""

DOWNGRADE = r"""
ALTER TABLE d5_upload_transfer DROP COLUMN early_preview_upload_id;
DROP TABLE d5_upload_grid_profile;
DROP TABLE d3_lab_default_grid;
DROP TABLE d3_dataset_grid_profile;
ALTER TABLE d3_dataset DROP CONSTRAINT d3_dataset_lab_id_id_unique;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
