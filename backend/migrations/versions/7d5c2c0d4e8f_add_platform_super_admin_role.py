"""add platform super admin role

Revision ID: 7d5c2c0d4e8f
Revises: e3f4a5b6c7d8
Create Date: 2026-11-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7d5c2c0d4e8f"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade():
    platformrole = sa.Enum("user", "super_admin", name="platformrole")
    platformrole.create(op.get_bind(), checkfirst=True)
    inspector = sa.inspect(op.get_bind())
    if "platform_role" not in {column["name"] for column in inspector.get_columns("users")}:
        op.add_column("users", sa.Column("platform_role", platformrole, nullable=False, server_default="user"))
    op.execute("UPDATE users SET platform_role = 'user' WHERE platform_role IS NULL")


def downgrade():
    op.drop_column("users", "platform_role")
    op.execute("DROP TYPE IF EXISTS platformrole")
