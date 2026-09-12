"""서비스 계정의 활성 상태 열을 더한다.

Revision ID: 0027_account_status
Revises: 0026_login_sessions
"""
from alembic import op

revision = "0027_account_status"
down_revision = "0026_login_sessions"
branch_labels = None
depends_on = None

# 기존 행은 전부 `active` 로 남는다 — 퇴소는 운영자가 화면에서 고르는 것이지
# 마이그레이션이 판단할 것이 아니다.
UPGRADE = r"""
ALTER TABLE account_admin.login_credential
  ADD COLUMN status text NOT NULL DEFAULT 'active'
  CHECK (status IN ('active','inactive'));
"""

# 비활성 계정이 남아 있으면 열을 지우지 않는다. 지우는 순간 그 계정들이 조용히
# 로그인 가능 상태로 되살아난다 — `0025`·`0026` 의 downgrade 와 같은 배치다.
DOWNGRADE = r"""
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM account_admin.login_credential WHERE status <> 'active') THEN
    RAISE EXCEPTION '비활성 계정이 있어 상태 열을 제거하지 않는다';
  END IF;
END $$;
ALTER TABLE account_admin.login_credential DROP COLUMN status;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
