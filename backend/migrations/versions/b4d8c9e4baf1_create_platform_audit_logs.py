"""create platform audit logs

Revision ID: b4d8c9e4baf1
Revises: 7d5c2c0d4e8f
Create Date: 2026-11-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b4d8c9e4baf1"
down_revision = "7d5c2c0d4e8f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("platform_audit_logs"):
        return
    op.create_table(
        "platform_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("actor_name", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False, server_default="platform"),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="platform-admin"),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_platform_audit_logs_action"), "platform_audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_platform_audit_logs_actor_id"), "platform_audit_logs", ["actor_id"], unique=False)
    op.create_index(op.f("ix_platform_audit_logs_created_at"), "platform_audit_logs", ["created_at"], unique=False)
    op.create_index(op.f("ix_platform_audit_logs_entity_id"), "platform_audit_logs", ["entity_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_platform_audit_logs_entity_id"), table_name="platform_audit_logs")
    op.drop_index(op.f("ix_platform_audit_logs_created_at"), table_name="platform_audit_logs")
    op.drop_index(op.f("ix_platform_audit_logs_actor_id"), table_name="platform_audit_logs")
    op.drop_index(op.f("ix_platform_audit_logs_action"), table_name="platform_audit_logs")
    op.drop_table("platform_audit_logs")
