"""add offline sync tables to migration history

Revision ID: d2e3f4a5b6c7
Revises: c1b2c3d4e5f6
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "c1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("sync_entity_versions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.Integer(), nullable=False), sa.Column("entity_type", sa.String(100), nullable=False), sa.Column("entity_id", sa.Integer(), nullable=False), sa.Column("version", sa.Integer(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"), sa.UniqueConstraint("organization_id", "entity_type", "entity_id", name="uq_sync_entity_version"))
    for name, column in (("ix_sync_entity_versions_organization_id", "organization_id"), ("ix_sync_entity_versions_entity_type", "entity_type"), ("ix_sync_entity_versions_entity_id", "entity_id")):
        op.create_index(name, "sync_entity_versions", [column])
    op.create_table("sync_queue_items", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.Integer(), nullable=False), sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("operation_id", sa.String(255), nullable=False), sa.Column("entity_type", sa.String(100), nullable=False), sa.Column("entity_id", sa.Integer(), nullable=False), sa.Column("action", sa.String(50), nullable=False), sa.Column("payload", sa.JSON()), sa.Column("base_version", sa.Integer(), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("operation_id"))
    for name, column in (("ix_sync_queue_items_organization_id", "organization_id"), ("ix_sync_queue_items_user_id", "user_id"), ("ix_sync_queue_items_operation_id", "operation_id"), ("ix_sync_queue_items_entity_type", "entity_type"), ("ix_sync_queue_items_entity_id", "entity_id"), ("ix_sync_queue_items_action", "action"), ("ix_sync_queue_items_status", "status")):
        op.create_index(name, "sync_queue_items", [column], unique=name == "ix_sync_queue_items_operation_id")


def downgrade() -> None:
    for name in ("ix_sync_queue_items_status", "ix_sync_queue_items_action", "ix_sync_queue_items_entity_id", "ix_sync_queue_items_entity_type", "ix_sync_queue_items_operation_id", "ix_sync_queue_items_user_id", "ix_sync_queue_items_organization_id"):
        op.drop_index(name, table_name="sync_queue_items")
    op.drop_table("sync_queue_items")
    for name in ("ix_sync_entity_versions_entity_id", "ix_sync_entity_versions_entity_type", "ix_sync_entity_versions_organization_id"):
        op.drop_index(name, table_name="sync_entity_versions")
    op.drop_table("sync_entity_versions")
