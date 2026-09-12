"""Operator audit snapshots and per-domain export queues.

Revision ID: 0027_operator_audit
Revises: 0026_login_sessions
"""
from alembic import op

revision = "0027_operator_audit"
down_revision = "0026_login_sessions"
branch_labels = None
depends_on = None
DOMAINS = ("d2", "d3", "d6")
EXPORT_DOMAINS = ("d2", "d3", "d5", "d6", "d8")

def upgrade() -> None:
    for domain in DOMAINS:
        op.execute(f"""
        CREATE TABLE {domain}_operator_audit (
          id ulid PRIMARY KEY, source_id ulid NOT NULL UNIQUE, lab_id ulid NOT NULL REFERENCES d1_lab(id),
          actor_id ulid NOT NULL, target_id ulid NOT NULL, action text NOT NULL,
          before_snapshot jsonb, after_snapshot jsonb, occurred_at timestamptz NOT NULL DEFAULT now());
        CREATE INDEX {domain}_operator_audit_pending_idx ON {domain}_operator_audit(lab_id, occurred_at, source_id);
        CREATE TRIGGER {domain}_operator_audit_append_only BEFORE UPDATE OR DELETE ON {domain}_operator_audit
          FOR EACH ROW EXECUTE FUNCTION deny_update_delete();
        ALTER TABLE {domain}_operator_audit ENABLE ROW LEVEL SECURITY;
        ALTER TABLE {domain}_operator_audit FORCE ROW LEVEL SECURITY;
        CREATE POLICY lab_boundary ON {domain}_operator_audit FOR ALL
          USING (lab_id=current_lab_id()) WITH CHECK (lab_id=current_lab_id());
        """)
    for domain in EXPORT_DOMAINS:
        op.execute(f"""
        CREATE TABLE {domain}_operator_export (
          id ulid PRIMARY KEY, source_id ulid NOT NULL UNIQUE, lab_id ulid NOT NULL REFERENCES d1_lab(id),
          occurred_at timestamptz NOT NULL, payload jsonb NOT NULL,
          receipt_hash text CHECK(receipt_hash IS NULL OR receipt_hash ~ '^[0-9a-f]{{64}}$'),
          received_at timestamptz, CHECK((receipt_hash IS NULL)=(received_at IS NULL)));
        CREATE INDEX {domain}_operator_export_pending_idx ON {domain}_operator_export(lab_id, occurred_at, source_id)
          WHERE receipt_hash IS NULL;
        ALTER TABLE {domain}_operator_export ENABLE ROW LEVEL SECURITY;
        ALTER TABLE {domain}_operator_export FORCE ROW LEVEL SECURITY;
        CREATE POLICY lab_boundary ON {domain}_operator_export FOR ALL
          USING (lab_id=current_lab_id()) WITH CHECK (lab_id=current_lab_id());
        """)

def downgrade() -> None:
    for domain in reversed(EXPORT_DOMAINS):
        op.execute(f"DROP TABLE {domain}_operator_export")
    for domain in reversed(DOMAINS):
        op.execute(f"DROP TABLE {domain}_operator_audit")
