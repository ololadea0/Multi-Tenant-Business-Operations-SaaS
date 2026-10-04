"""add product status

Revision ID: 867390ab03e3
Revises: 633794cff8c0
Create Date: 2026-10-04 04:08:22.782813

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '867390ab03e3'
down_revision: Union[str, Sequence[str], None] = '633794cff8c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    productstatus = sa.Enum(
        "ACTIVE",
        "INACTIVE",
        name="productstatus"
    )

    productstatus.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "products",
        sa.Column(
            "status",
            productstatus,
            nullable=False,
            server_default="ACTIVE"
        )
    )

    op.alter_column(
        "products",
        "status",
        server_default=None
    )


def downgrade() -> None:
    op.drop_column("products", "status")

    productstatus = sa.Enum(
        "ACTIVE",
        "INACTIVE",
        name="productstatus"
    )

    productstatus.drop(op.get_bind(), checkfirst=True)
