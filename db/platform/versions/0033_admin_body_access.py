"""System administrators and lab professors may manage private dataset bodies."""
from alembic import op
revision = "0033_admin_body_access"
down_revision = "0032_labless_operator"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE FUNCTION is_dataset_manager(target_lab char(26)) RETURNS boolean\nLANGUAGE sql STABLE AS $$\n  SELECT COALESCE(current_setting('app.operator_manage', true), '') = 'on' OR EXISTS (\n    SELECT 1 FROM d2_member_role r WHERE r.account_id = current_account_id()\n      AND r.lab_id = target_lab AND r.role = '교수'\n  )\n$$;\n\n")
    op.execute("DROP POLICY body_access ON d3_file")
    op.execute("CREATE POLICY body_access ON d3_file AS RESTRICTIVE FOR ALL\n  USING (\n    is_dataset_manager(d3_file.lab_id) OR COALESCE(\n      (SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),\n      (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)\n    ) = '열림'\n    OR EXISTS (\n      SELECT 1 FROM d2_dataset_access_grant g\n      WHERE g.dataset_id = d3_file.dataset_id\n        AND g.grantee_account_id = current_account_id()\n        AND g.expires_at > now()\n    )\n  )\n  WITH CHECK (\n    is_dataset_manager(d3_file.lab_id) OR COALESCE(\n      (SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),\n      (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)\n    ) = '열림'\n    OR EXISTS (\n      SELECT 1 FROM d2_dataset_access_grant g\n      WHERE g.dataset_id = d3_file.dataset_id\n        AND g.grantee_account_id = current_account_id()\n        AND g.expires_at > now()\n    )\n  );\n")


def downgrade():
    op.execute("DROP POLICY body_access ON d3_file")
    op.execute("CREATE POLICY body_access ON d3_file AS RESTRICTIVE FOR ALL\n  USING (\n    COALESCE(\n      (SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),\n      (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)\n    ) = '열림'\n    OR EXISTS (\n      SELECT 1 FROM d2_dataset_access_grant g\n      WHERE g.dataset_id = d3_file.dataset_id\n        AND g.grantee_account_id = current_account_id()\n        AND g.expires_at > now()\n    )\n  )\n  WITH CHECK (\n    COALESCE(\n      (SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),\n      (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)\n    ) = '열림'\n    OR EXISTS (\n      SELECT 1 FROM d2_dataset_access_grant g\n      WHERE g.dataset_id = d3_file.dataset_id\n        AND g.grantee_account_id = current_account_id()\n        AND g.expires_at > now()\n    )\n  );\n")
    op.execute("DROP FUNCTION is_dataset_manager(char(26))")
