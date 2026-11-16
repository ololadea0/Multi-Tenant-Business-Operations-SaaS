"""add missing subscription billing fields

Revision ID: f2a4b7c9d1e3
Revises: d6e7f8a9b0c1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f2a4b7c9d1e3"
down_revision: Union[str, Sequence[str], None] = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("organization_subscriptions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("next_billing_date", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("grace_period_end", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("cancel_at_period_end", sa.Boolean(), nullable=True, server_default=sa.false()))
        batch_op.add_column(sa.Column("cancelled_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("expired_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("suspended_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("payment_provider", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("provider_subscription_reference", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("provider", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("provider_reference", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("metadata_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("organization_subscriptions", schema=None) as batch_op:
        batch_op.drop_column("metadata_json")
        batch_op.drop_column("provider_reference")
        batch_op.drop_column("provider")
        batch_op.drop_column("provider_subscription_reference")
        batch_op.drop_column("payment_provider")
        batch_op.drop_column("suspended_at")
        batch_op.drop_column("expired_at")
        batch_op.drop_column("cancelled_at")
        batch_op.drop_column("cancel_at_period_end")
        batch_op.drop_column("grace_period_end")
        batch_op.drop_column("next_billing_date")
