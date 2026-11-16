"""create platform announcements

Revision ID: f4c0d9e8a1b2
Revises: d6f7a8b9c0d1
Create Date: 2026-11-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4c0d9e8a1b2"
down_revision: Union[str, Sequence[str], None] = "d6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = set()
    if inspector.has_table("platform_announcements"):
        existing_columns = {column["name"] for column in inspector.get_columns("platform_announcements")}

    if not inspector.has_table("platform_announcements"):
        op.create_table(
            "platform_announcements",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("kind", sa.String(length=32), nullable=False, server_default="announcement"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("starts_at", sa.DateTime(), nullable=True),
            sa.Column("ends_at", sa.DateTime(), nullable=True),
            sa.Column("created_by_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_platform_announcements_created_by_id"), "platform_announcements", ["created_by_id"], unique=False)
        return

    columns = {
        "title": sa.Column("title", sa.String(length=255), nullable=False),
        "message": sa.Column("message", sa.Text(), nullable=False),
        "kind": sa.Column("kind", sa.String(length=32), nullable=False, server_default="announcement"),
        "is_active": sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        "starts_at": sa.Column("starts_at", sa.DateTime(), nullable=True),
        "ends_at": sa.Column("ends_at", sa.DateTime(), nullable=True),
        "created_by_id": sa.Column("created_by_id", sa.Integer(), nullable=True),
        "created_at": sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        "updated_at": sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    }

    for column_name, column in columns.items():
        if column_name not in existing_columns:
            op.add_column("platform_announcements", column)

    if "created_by_id" not in existing_columns and not bind.dialect.name.startswith("sqlite"):
        op.create_index(op.f("ix_platform_announcements_created_by_id"), "platform_announcements", ["created_by_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("platform_announcements"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("platform_announcements")}
    for column_name in [
        "title",
        "message",
        "kind",
        "is_active",
        "starts_at",
        "ends_at",
        "created_by_id",
        "created_at",
        "updated_at",
    ]:
        if column_name in existing_columns:
            op.drop_column("platform_announcements", column_name)

    if inspector.has_index("platform_announcements", "ix_platform_announcements_created_by_id"):
        op.drop_index(op.f("ix_platform_announcements_created_by_id"), table_name="platform_announcements")
