"""create platform settings"""
from alembic import op
import sqlalchemy as sa

revision = "c5d6e7f8a9b0"
down_revision = "b4d8c9e4baf1"
branch_labels = None
depends_on = None

def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("platform_settings"):
        return
    op.create_table(
        "platform_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trial_duration_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("annual_billing_discount_percent", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("payment_grace_period_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("support_email", sa.String(length=255), nullable=False, server_default="support@daymark.app"),
        sa.Column("support_phone", sa.String(length=255), nullable=False, server_default="+234 800 000 0000"),
        sa.Column("help_center_url", sa.String(length=255), nullable=False, server_default="https://help.daymark.app"),
        sa.Column("allow_new_registrations", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("maintenance_notice_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("maintenance_message", sa.Text(), nullable=False, server_default="Scheduled maintenance is in progress. Please check back shortly."),
        sa.Column("maintenance_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )

def downgrade() -> None:
    op.drop_table("platform_settings")
