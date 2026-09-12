"""운영자의 전 연구실 **읽기** 스코프를 RLS 에 더한다.

Revision ID: 0028_operator_read_policy
Revises: 0027_account_status
"""
from alembic import op

revision = "0028_operator_read_policy"
down_revision = "0027_account_status"
branch_labels = None
depends_on = None

# 경계를 **끄지 않는다.** `lab_boundary` 는 한 글자도 바뀌지 않고, 그 옆에 `FOR SELECT` 정책
# 하나가 더 선다. PERMISSIVE 정책은 OR 로 합쳐지므로 읽기만 넓어지고,
# INSERT·UPDATE·DELETE 는 `lab_boundary` 의 USING·WITH CHECK 을 그대로 통과해야 한다 —
# **쓰기 정책에는 이 스위치가 없다.**
#
# 스위치는 커널이 운영자에게만, 그것도 **읽기 요청에서만** 켠다
# (`kernel/scope.py` · `app/deps.py`). 값이 없으면 `false` 다 — fail-closed.
UPGRADE = r"""
CREATE FUNCTION is_operator_read() RETURNS boolean
  LANGUAGE sql STABLE
  AS $$
    SELECT COALESCE(current_setting('app.operator_read', true), '') = 'on'
  $$;
CREATE POLICY operator_read ON d1_lab_profile                  FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d1_account                      FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d2_member_role                  FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d2_permission_switch            FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d2_permission_change            FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d2_dataset_access               FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d2_dataset_access_grant         FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d2_dataset_access_request       FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d2_verification_request         FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d2_verified                     FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d3_dataset                      FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d3_dataset_description          FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d3_dataset_representative_image FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d3_representative_image_cleanup FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d3_dataset_autometa             FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d3_dataset_variable             FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d3_dataset_grid_profile         FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d3_lab_default_grid             FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d3_file                         FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d5_upload                       FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d5_upload_file                  FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d5_upload_grid_profile          FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d5_pipeline_event               FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d5_upload_transfer              FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d5_upload_transfer_file         FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d4_lineage_edge                 FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d4_lineage_unknown              FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d6_project                      FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d6_project_dataset              FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d8_activity                     FOR SELECT USING (is_operator_read());
CREATE POLICY operator_read ON d8_download                     FOR SELECT USING (is_operator_read());
"""

# 정책을 먼저 지우고 함수를 지운다(의존 순서).
DOWNGRADE = r"""
DROP POLICY operator_read ON d1_lab_profile;
DROP POLICY operator_read ON d1_account;
DROP POLICY operator_read ON d2_member_role;
DROP POLICY operator_read ON d2_permission_switch;
DROP POLICY operator_read ON d2_permission_change;
DROP POLICY operator_read ON d2_dataset_access;
DROP POLICY operator_read ON d2_dataset_access_grant;
DROP POLICY operator_read ON d2_dataset_access_request;
DROP POLICY operator_read ON d2_verification_request;
DROP POLICY operator_read ON d2_verified;
DROP POLICY operator_read ON d3_dataset;
DROP POLICY operator_read ON d3_dataset_description;
DROP POLICY operator_read ON d3_dataset_representative_image;
DROP POLICY operator_read ON d3_representative_image_cleanup;
DROP POLICY operator_read ON d3_dataset_autometa;
DROP POLICY operator_read ON d3_dataset_variable;
DROP POLICY operator_read ON d3_dataset_grid_profile;
DROP POLICY operator_read ON d3_lab_default_grid;
DROP POLICY operator_read ON d3_file;
DROP POLICY operator_read ON d5_upload;
DROP POLICY operator_read ON d5_upload_file;
DROP POLICY operator_read ON d5_upload_grid_profile;
DROP POLICY operator_read ON d5_pipeline_event;
DROP POLICY operator_read ON d5_upload_transfer;
DROP POLICY operator_read ON d5_upload_transfer_file;
DROP POLICY operator_read ON d4_lineage_edge;
DROP POLICY operator_read ON d4_lineage_unknown;
DROP POLICY operator_read ON d6_project;
DROP POLICY operator_read ON d6_project_dataset;
DROP POLICY operator_read ON d8_activity;
DROP POLICY operator_read ON d8_download;
DROP FUNCTION is_operator_read();
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
