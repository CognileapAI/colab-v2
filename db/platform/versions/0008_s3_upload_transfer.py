"""0008 — 프리사인드 전송 원장 2표 신설 + `d5_upload_file.relative_path` (〈337〉·〈338〉).

무엇
  ⑴ `d5_upload_transfer` · `d5_upload_transfer_file` — 저장 모드 s3 의 **전송 전용 원장.**
     브라우저→S3 프리사인드 전송이 완결되기 전의 상태(계획·파트 크기·S3 멀티파트 id·
     실측 결과)만 담고, 완결되는 순간 같은 ULID 로 `d5_upload` 가 선다. 기존 d5 표의
     의미는 바뀌지 않는다 — 격자 축 CHECK·워커의 행 생성 시점(`〈79〉`) 전부 그대로다.
  ⑵ `d5_upload_file.relative_path` — 폴더째 업로드의 `폴더/이름` 메타 (NULL 허용 추가만).
     저장 키 규약(contracts/storage/layout.json)은 손대지 않는다.

왜 additive 인가
  `0007` 과 같은 방식 — 기존 행은 전부 NULL/무영향이라 백필이 없고, 그래서
  `NO FORCE RLS` 구간도 없다. staging 라이브 DB 에 그대로 적용된다.

`downgrade` 는 전송 원장 2표를 DROP 한다 — 진행 중이던 전송 상태가 사라진다.
(그 시점의 S3 미완 멀티파트는 버킷 라이프사이클 abort-7d 가 최후 백스톱이다.)

Revision ID: 0008_s3_upload_transfer
Revises: 0007_p2_human_written_meta
"""
from __future__ import annotations

from alembic import op

revision = "0008_s3_upload_transfer"
down_revision = "0007_p2_human_written_meta"
branch_labels = None
depends_on = None


UPGRADE = r"""
ALTER TABLE d5_upload_file
  ADD COLUMN relative_path text
  CHECK (relative_path IS NULL OR length(relative_path) BETWEEN 1 AND 1024);

CREATE TABLE d5_upload_transfer (
  id                   ulid        PRIMARY KEY,
  lab_id               ulid        NOT NULL REFERENCES d1_lab(id),
  uploader_account_id  ulid        NOT NULL REFERENCES d1_account(id),
  source_label         text        NOT NULL CHECK (length(source_label) <= 255),
  created_at           timestamptz NOT NULL DEFAULT now(),
  expires_at           timestamptz NOT NULL,
  completed_at         timestamptz,
  CONSTRAINT d5_upload_transfer_expiry_after_birth CHECK (expires_at > created_at)
);
CREATE INDEX d5_upload_transfer_lab_idx ON d5_upload_transfer (lab_id);
CREATE INDEX d5_upload_transfer_open_idx ON d5_upload_transfer (expires_at)
  WHERE completed_at IS NULL;

CREATE TABLE d5_upload_transfer_file (
  id             ulid        PRIMARY KEY,
  lab_id         ulid        NOT NULL REFERENCES d1_lab(id),
  transfer_id    ulid        NOT NULL REFERENCES d5_upload_transfer(id) ON DELETE CASCADE,
  kind           text        NOT NULL CHECK (kind IN ('본체', '기준 격자 파일')),
  file_name      text        NOT NULL CHECK (length(btrim(file_name)) > 0
                                             AND length(file_name) <= 255),
  relative_path  text        CHECK (relative_path IS NULL
                                    OR length(relative_path) BETWEEN 1 AND 1024),
  byte_size      bigint      NOT NULL CHECK (byte_size >= 0),
  storage_key    text        NOT NULL CHECK (length(btrim(storage_key)) > 0),
  part_size      bigint      CHECK (part_size IS NULL OR part_size > 0),
  transfer_ref   text,
  outcome        text        NOT NULL DEFAULT '대기' CHECK (outcome IN ('대기', '올라감', '실패')),
  created_at     timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT d5_upload_transfer_file_ref_only_for_multipart
    CHECK (transfer_ref IS NULL OR part_size IS NOT NULL)
);
CREATE INDEX d5_upload_transfer_file_transfer_idx ON d5_upload_transfer_file (transfer_id);
CREATE INDEX d5_upload_transfer_file_lab_idx ON d5_upload_transfer_file (lab_id);

ALTER TABLE d5_upload_transfer      ENABLE ROW LEVEL SECURITY;
ALTER TABLE d5_upload_transfer      FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d5_upload_transfer FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());

ALTER TABLE d5_upload_transfer_file ENABLE ROW LEVEL SECURITY;
ALTER TABLE d5_upload_transfer_file FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d5_upload_transfer_file FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());
"""

DOWNGRADE = r"""
DROP TABLE d5_upload_transfer_file;
DROP TABLE d5_upload_transfer;
ALTER TABLE d5_upload_file DROP COLUMN relative_path;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
