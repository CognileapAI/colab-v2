"""브라우저별 회수 가능한 로그인 세션 원장을 더한다.

Revision ID: 0026_login_sessions
Revises: 0025_stage3_accounts
"""
from alembic import op

revision = "0026_login_sessions"
down_revision = "0025_stage3_accounts"
branch_labels = None
depends_on = None

UPGRADE = r"""
CREATE TABLE account_admin.login_session (
  id ulid PRIMARY KEY,
  account_id ulid NOT NULL REFERENCES d1_account(id) ON DELETE CASCADE,
  lab_id ulid NOT NULL REFERENCES d1_lab(id) ON DELETE CASCADE,
  issued_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL CHECK (expires_at > issued_at),
  revoked_at timestamptz,
  generation integer NOT NULL DEFAULT 1 CHECK (generation > 0),
  credential_kind text NOT NULL
    CHECK (credential_kind IN ('database','planted-code','legacy-file')),
  purpose text NOT NULL CHECK (purpose IN ('normal','password-change')),
  credential_version integer CHECK (credential_version > 0),
  revoke_digest text NOT NULL UNIQUE CHECK (length(revoke_digest) = 64),
  CHECK (
    (credential_kind = 'database' AND credential_version IS NOT NULL)
    OR (credential_kind <> 'database' AND credential_version IS NULL)
  )
);
CREATE INDEX login_session_account_expiry_idx
  ON account_admin.login_session(account_id, expires_at);
REVOKE ALL ON account_admin.login_session FROM PUBLIC;
"""

DOWNGRADE = r"""
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM account_admin.login_session) THEN
    RAISE EXCEPTION '로그인 세션이 있어 원장을 제거하지 않는다';
  END IF;
END $$;
DROP TABLE account_admin.login_session;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
