"""Stage 3 서비스 계정 자격과 운영자 등록부를 더한다.

Revision ID: 0025_stage3_accounts
Revises: 0024_s2_grid_convenience
"""
from alembic import op

revision = "0025_stage3_accounts"
down_revision = "0024_s2_grid_convenience"
branch_labels = None
depends_on = None

UPGRADE = r"""
CREATE SCHEMA account_admin;
REVOKE ALL ON SCHEMA account_admin FROM PUBLIC;
CREATE TABLE account_admin.login_credential (
  account_id ulid PRIMARY KEY REFERENCES d1_account(id) ON DELETE CASCADE,
  login_name text NOT NULL UNIQUE CHECK (login_name = lower(btrim(login_name))),
  kdf text NOT NULL, salt text NOT NULL, password_hash text NOT NULL,
  n integer NOT NULL CHECK (n > 0), r integer NOT NULL CHECK (r > 0),
  p integer NOT NULL CHECK (p > 0),
  must_change_password boolean NOT NULL DEFAULT true,
  session_version integer NOT NULL DEFAULT 1 CHECK (session_version > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE account_admin.service_operator (
  account_id ulid PRIMARY KEY REFERENCES d1_account(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now()
);
REVOKE ALL ON account_admin.login_credential, account_admin.service_operator FROM PUBLIC;
"""

# 신규 자격이 존재하는 동안 앱 롤백은 표를 보존한다. 명시적 데이터 폐기 절차만 DROP할 수 있다.
DOWNGRADE = r"""
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM account_admin.login_credential)
     OR EXISTS (SELECT 1 FROM account_admin.service_operator) THEN
    RAISE EXCEPTION 'Stage 3 계정 또는 운영자 등록이 있어 스키마를 제거하지 않는다';
  END IF;
END $$;
DROP SCHEMA account_admin CASCADE;
"""

def upgrade() -> None:
    op.execute(UPGRADE)

def downgrade() -> None:
    op.execute(DOWNGRADE)
