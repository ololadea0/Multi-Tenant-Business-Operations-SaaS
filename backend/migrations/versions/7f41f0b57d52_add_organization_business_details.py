"""add organization business details

Revision ID: 7f41f0b57d52
Revises: 2e07d5b73c1c
Create Date: 2026-11-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f41f0b57d52"
down_revision: Union[str, Sequence[str], None] = "2e07d5b73c1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("organizations", sa.Column("address_line_1", sa.String(length=255), nullable=True))
    op.add_column("organizations", sa.Column("address_line_2", sa.String(length=255), nullable=True))
    op.add_column("organizations", sa.Column("city", sa.String(length=120), nullable=True))
    op.add_column("organizations", sa.Column("state", sa.String(length=120), nullable=True))
    op.add_column("organizations", sa.Column("postal_code", sa.String(length=50), nullable=True))
    op.add_column("organizations", sa.Column("country", sa.String(length=120), nullable=True))
    op.add_column("organizations", sa.Column("phone", sa.String(length=50), nullable=True))
    op.add_column("organizations", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("organizations", sa.Column("website", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("organizations", "website")
    op.drop_column("organizations", "email")
    op.drop_column("organizations", "phone")
    op.drop_column("organizations", "country")
    op.drop_column("organizations", "postal_code")
    op.drop_column("organizations", "state")
    op.drop_column("organizations", "city")
    op.drop_column("organizations", "address_line_2")
    op.drop_column("organizations", "address_line_1")
