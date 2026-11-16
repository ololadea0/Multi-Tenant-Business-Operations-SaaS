
"""add missing platform billing settings

Revision ID: a8a3980197db
Revises: a1b2c3d4e5f6
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a8a3980197db"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "platform_settings",
        sa.Column(
            "trial_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.add_column(
        "platform_settings",
        sa.Column(
            "trial_plan_key",
            sa.String(50),
            nullable=False,
            server_default="growth",
        ),
    )

    op.add_column(
        "platform_settings",
        sa.Column(
            "billing_intervals",
            sa.String(255),
            nullable=False,
            server_default="monthly,annual",
        ),
    )

    op.add_column(
        "platform_settings",
        sa.Column(
            "renewal_policy",
            sa.String(40),
            nullable=False,
            server_default="manual",
        ),
    )


def downgrade() -> None:
    op.drop_column("platform_settings", "renewal_policy")
    op.drop_column("platform_settings", "billing_intervals")
    op.drop_column("platform_settings", "trial_plan_key")
    op.drop_column("platform_settings", "trial_enabled")
