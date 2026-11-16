"""add payment transaction lifecycle fields

Revision ID: d6f7a8b9c0d1
Revises: a8a3980197db
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = "d6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = "a8a3980197db"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {
        row[0]
        for row in bind.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'payment_transactions'")
        ).fetchall()
    }

    if "provider" not in existing:
        op.add_column("payment_transactions", sa.Column("provider", sa.String(length=40), nullable=True, server_default="paystack"))

    if "purpose" not in existing:
        op.add_column("payment_transactions", sa.Column("purpose", sa.String(length=50), nullable=True, server_default="INITIAL_SUBSCRIPTION"))

    for column_name in [
        "payment_period_start",
        "payment_period_end",
        "initiated_at",
        "verified_at",
    ]:
        if column_name not in existing:
            op.add_column("payment_transactions", sa.Column(column_name, sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    existing = {
        row[0]
        for row in bind.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'payment_transactions'")
        ).fetchall()
    }

    for column_name in [
        "provider",
        "purpose",
        "payment_period_start",
        "payment_period_end",
        "initiated_at",
        "verified_at",
    ]:
        if column_name in existing:
            op.drop_column("payment_transactions", column_name)
