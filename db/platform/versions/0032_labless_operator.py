"""Allow service operators to exist without lab membership."""
from alembic import op

revision = "0032_labless_operator"
down_revision = "0031_search_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE d1_account ALTER COLUMN lab_id DROP NOT NULL")
    op.execute("ALTER TABLE account_admin.login_session ALTER COLUMN lab_id DROP NOT NULL")


def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM d1_account WHERE lab_id IS NULL) THEN
            RAISE EXCEPTION '소속 없는 계정이 있어 lab_id NOT NULL을 복원하지 않는다';
          END IF;
        END $$;
        ALTER TABLE account_admin.login_session ALTER COLUMN lab_id SET NOT NULL;
        ALTER TABLE d1_account ALTER COLUMN lab_id SET NOT NULL;
    """)
