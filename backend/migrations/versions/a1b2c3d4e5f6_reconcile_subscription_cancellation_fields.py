"""reconcile subscription cancellation fields

Revision ID: a1b2c3d4e5f6
Revises: f2a4b7c9d1e3
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f2a4b7c9d1e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {
        row[0]
        for row in bind.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'organization_subscriptions'")
        ).fetchall()
    }

    if "cancel_at_period_end" not in existing:
        op.add_column("organization_subscriptions", sa.Column("cancel_at_period_end", sa.Boolean(), nullable=True, server_default=sa.false()))

    if "cancelled_at" not in existing:
        op.add_column("organization_subscriptions", sa.Column("cancelled_at", sa.DateTime(), nullable=True))

    if "expired_at" not in existing:
        op.add_column("organization_subscriptions", sa.Column("expired_at", sa.DateTime(), nullable=True))

    if "suspended_at" not in existing:
        op.add_column("organization_subscriptions", sa.Column("suspended_at", sa.DateTime(), nullable=True))

    if "cancelled_at" in existing or "cancellation_date" in existing:
        op.execute(
            text(
                """
                UPDATE organization_subscriptions
                SET cancelled_at = cancellation_date
                WHERE cancelled_at IS NULL AND cancellation_date IS NOT NULL
                """
            )
        )

    op.execute(text("ALTER TABLE organization_subscriptions ALTER COLUMN cancel_at_period_end SET DEFAULT false"))


def downgrade() -> None:
    bind = op.get_bind()
    existing = {
        row[0]
        for row in bind.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'organization_subscriptions'")
        ).fetchall()
    }

    for column in ["suspended_at", "expired_at", "cancelled_at", "cancel_at_period_end"]:
        if column in existing:
            op.drop_column("organization_subscriptions", column)
