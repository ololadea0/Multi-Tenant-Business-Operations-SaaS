"""align billing and sync indexes

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
"""
from typing import Sequence, Union
from alembic import op

revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "d2e3f4a5b6c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_sync_queue_items_operation_id", table_name="sync_queue_items")
    op.create_index("ix_payment_transactions_status", "payment_transactions", ["status"])
    op.create_index("ix_payment_transactions_subscription_id", "payment_transactions", ["subscription_id"])
    op.create_index("ix_payment_webhook_events_provider_event_id", "payment_webhook_events", ["provider_event_id"])
    op.create_index("ix_subscription_events_organization_id", "subscription_events", ["organization_id"])
    op.create_index("ix_subscription_events_subscription_id", "subscription_events", ["subscription_id"])


def downgrade() -> None:
    for name, table in (("ix_subscription_events_subscription_id", "subscription_events"), ("ix_subscription_events_organization_id", "subscription_events"), ("ix_payment_webhook_events_provider_event_id", "payment_webhook_events"), ("ix_payment_transactions_subscription_id", "payment_transactions"), ("ix_payment_transactions_status", "payment_transactions")):
        op.drop_index(name, table_name=table)
    op.create_index("ix_sync_queue_items_operation_id", "sync_queue_items", ["operation_id"], unique=True)
