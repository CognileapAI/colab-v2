"""Allow private dataset owners through the file body policy.

Revision ID: 0032_private_owner_access
Revises: 0031_search_evidence
"""
from alembic import op

revision = "0032_private_owner_access"
down_revision = "0031_search_evidence"
branch_labels = None
depends_on = None

UPGRADE = """
ALTER POLICY body_access ON d3_file
  USING (
    COALESCE(
      (SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),
      (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)
    ) = '열림'
    OR EXISTS (
      SELECT 1 FROM d3_dataset owner_dataset
      WHERE owner_dataset.id = d3_file.dataset_id
        AND owner_dataset.lab_id = current_lab_id()
        AND owner_dataset.owner_account_id = current_account_id()
    )
    OR EXISTS (
      SELECT 1 FROM d2_dataset_access_grant g
      WHERE g.dataset_id = d3_file.dataset_id
        AND g.grantee_account_id = current_account_id()
        AND g.expires_at > now()
    )
  )
  WITH CHECK (
    COALESCE(
      (SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),
      (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)
    ) = '열림'
    OR EXISTS (
      SELECT 1 FROM d3_dataset owner_dataset
      WHERE owner_dataset.id = d3_file.dataset_id
        AND owner_dataset.lab_id = current_lab_id()
        AND owner_dataset.owner_account_id = current_account_id()
    )
    OR EXISTS (
      SELECT 1 FROM d2_dataset_access_grant g
      WHERE g.dataset_id = d3_file.dataset_id
        AND g.grantee_account_id = current_account_id()
        AND g.expires_at > now()
    )
  );
"""
DOWNGRADE = """
ALTER POLICY body_access ON d3_file
  USING (
    COALESCE(
      (SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),
      (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)
    ) = '열림'
    OR EXISTS (
      SELECT 1 FROM d2_dataset_access_grant g
      WHERE g.dataset_id = d3_file.dataset_id
        AND g.grantee_account_id = current_account_id()
        AND g.expires_at > now()
    )
  )
  WITH CHECK (
    COALESCE(
      (SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),
      (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)
    ) = '열림'
    OR EXISTS (
      SELECT 1 FROM d2_dataset_access_grant g
      WHERE g.dataset_id = d3_file.dataset_id
        AND g.grantee_account_id = current_account_id()
        AND g.expires_at > now()
    )
  );
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
