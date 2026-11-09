"""add subscription and payment billing domain

Revision ID: c1b2c3d4e5f6
Revises: 674852d38695
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "674852d38695"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("subscription_plans",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("key", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False), sa.Column("description", sa.String(500), nullable=False),
        sa.Column("monthly_price", sa.Integer(), nullable=False), sa.Column("annual_price", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False), sa.Column("max_team_members", sa.Integer(), nullable=False),
        sa.Column("max_products", sa.Integer(), nullable=False), sa.Column("max_monthly_orders", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True), sa.UniqueConstraint("key"))
    op.create_index("ix_subscription_plans_key", "subscription_plans", ["key"])
    op.create_table("organization_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False), sa.Column("billing_interval", sa.Enum("MONTHLY", "ANNUAL", name="billinginterval"), nullable=False),
        sa.Column("status", sa.Enum("TRIALING", "ACTIVE", "PAST_DUE", "CANCELLED", "EXPIRED", "SUSPENDED", name="subscriptionstatus"), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False), sa.Column("current_period_start", sa.DateTime(), nullable=False),
        sa.Column("current_period_end", sa.DateTime(), nullable=False), sa.Column("trial_start", sa.DateTime()), sa.Column("trial_end", sa.DateTime()),
        sa.Column("cancellation_date", sa.DateTime()), sa.Column("payment_provider", sa.String(40)), sa.Column("provider_subscription_reference", sa.String(255)),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"]), sa.UniqueConstraint("organization_id"))
    op.create_index("ix_organization_subscriptions_organization_id", "organization_subscriptions", ["organization_id"])
    op.create_index("ix_organization_subscriptions_status", "organization_subscriptions", ["status"])
    op.create_table("payment_transactions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.Integer(), nullable=False), sa.Column("subscription_id", sa.Integer(), nullable=False), sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("reference", sa.String(255), nullable=False), sa.Column("provider_transaction_id", sa.String(100)), sa.Column("amount", sa.Integer(), nullable=False), sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("interval", sa.Enum("MONTHLY", "ANNUAL", name="billinginterval", create_type=False), nullable=False), sa.Column("status", sa.Enum("INITIALIZED", "SUCCESS", "FAILED", "PENDING", name="paymentstatus"), nullable=False),
        sa.Column("provider_response", sa.JSON()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["subscription_id"], ["organization_subscriptions.id"]), sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"]), sa.UniqueConstraint("reference"))
    op.create_index("ix_payment_transactions_reference", "payment_transactions", ["reference"])
    op.create_index("ix_payment_transactions_organization_id", "payment_transactions", ["organization_id"])
    op.create_table("payment_webhook_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("provider_event_id", sa.String(255), nullable=False), sa.Column("event_type", sa.String(100), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("processed_at", sa.DateTime()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("provider_event_id"))
    op.create_table("subscription_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("organization_id", sa.Integer(), nullable=False), sa.Column("subscription_id", sa.Integer(), nullable=False), sa.Column("event_type", sa.String(100), nullable=False), sa.Column("payload", sa.JSON()), sa.Column("created_at", sa.DateTime(), nullable=False), sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["subscription_id"], ["organization_subscriptions.id"]))


def downgrade() -> None:
    op.drop_table("subscription_events"); op.drop_table("payment_webhook_events"); op.drop_table("payment_transactions"); op.drop_table("organization_subscriptions"); op.drop_index("ix_subscription_plans_key", table_name="subscription_plans"); op.drop_table("subscription_plans")
    op.execute("DROP TYPE IF EXISTS paymentstatus"); op.execute("DROP TYPE IF EXISTS subscriptionstatus"); op.execute("DROP TYPE IF EXISTS billinginterval")
