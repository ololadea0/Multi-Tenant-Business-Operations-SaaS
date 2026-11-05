"""add order number

Revision ID: 426838c64b63
Revises: 867390ab03e3
Create Date: 2026-10-04 04:40:52.877194

"""
from typing import Sequence, Union
import secrets

from alembic import op
import sqlalchemy as sa


revision: str = "426838c64b63"
down_revision: Union[str, Sequence[str], None] = "867390ab03e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def generate_order_number() -> str:
    date_part = "LEGACY"
    random_part = secrets.token_hex(4).upper()
    return f"ORD-{date_part}-{random_part}"


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "order_number",
            sa.String(length=50),
            nullable=True
        )
    )

    connection = op.get_bind()

    orders = connection.execute(
        sa.text("SELECT id FROM orders")
    ).fetchall()

    for order in orders:
        connection.execute(
            sa.text(
                """
                UPDATE orders
                SET order_number = :order_number
                WHERE id = :order_id
                """
            ),
            {
                "order_number": generate_order_number(),
                "order_id": order.id
            }
        )

    op.alter_column(
        "orders",
        "order_number",
        nullable=False
    )

    op.create_index(
        op.f("ix_orders_order_number"),
        "orders",
        ["order_number"],
        unique=True
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_orders_order_number"),
        table_name="orders"
    )

    op.drop_column(
        "orders",
        "order_number"
    )