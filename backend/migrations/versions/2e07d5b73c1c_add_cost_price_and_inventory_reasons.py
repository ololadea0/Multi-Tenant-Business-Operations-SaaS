"""add product cost prices and inventory movement reasons

Revision ID: 2e07d5b73c1c
Revises: f5a6b7c8d9e0
Create Date: 2026-11-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2e07d5b73c1c"
down_revision: Union[str, Sequence[str], None] = "f5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "products",
        sa.Column(
            "cost_price",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "inventory_movements",
        sa.Column("reason", sa.String(length=50), nullable=True),
    )
    op.alter_column("products", "cost_price", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("inventory_movements", "reason")
    op.drop_column("products", "cost_price")
