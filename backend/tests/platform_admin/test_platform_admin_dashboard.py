from datetime import datetime, timedelta

from app.core.security import create_access_token, hash_password
from app.models.audit_log import PlatformAuditLog
from app.models.billing import BillingInterval, OrganizationSubscription, PaymentStatus, PaymentTransaction, SubscriptionPlan, SubscriptionStatus
from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from app.models.user import PlatformRole, User


def test_platform_admin_audit_logs_are_available_to_super_admin(client, db):
    admin = User(
        email="platform-audit@daymark.app",
        full_name="Platform Auditor",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(admin)
    db.commit()

    db.add_all([
        PlatformAuditLog(
            actor_id=admin.id,
            actor_name=admin.full_name,
            action="suspended_business",
            entity_type="organization",
            entity_id=42,
            description="Suspended Meridian Retail",
            source="platform-admin",
            ip_address="203.0.113.10",
            user_agent="Daymark admin console",
        ),
        PlatformAuditLog(
            actor_id=admin.id,
            actor_name=admin.full_name,
            action="updated_plan",
            entity_type="subscription_plan",
            entity_id=7,
            description="Updated Growth plan pricing",
            source="platform-admin",
        ),
    ])
    db.commit()

    token = create_access_token(admin.id)
    response = client.get(
        "/api/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["action"] in {"suspended_business", "updated_plan"}
    assert data["total"] >= 2


def test_platform_admin_dashboard_returns_live_data(client, db):
    admin = User(
        email="platform-admin@daymark.app",
        full_name="Platform Admin",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    organizations = [
        Organization(name="Northstar Supply", slug="northstar-supply"),
        Organization(name="Harbor Trade", slug="harbor-trade"),
    ]
    db.add_all(organizations)
    db.commit()
    for org in organizations:
        db.refresh(org)

    members = [
        User(email="alex@northstar.example", full_name="Alex Morgan", password_hash=hash_password("StrongPassword123!"), is_active=True, is_email_verified=True),
        User(email="imani@harbortrade.example", full_name="Imani Cole", password_hash=hash_password("StrongPassword123!"), is_active=True, is_email_verified=True),
    ]
    db.add_all(members)
    db.commit()
    for member in members:
        db.refresh(member)

    db.add_all([
        Membership(user_id=members[0].id, organization_id=organizations[0].id, role=MembershipRole.OWNER),
        Membership(user_id=members[1].id, organization_id=organizations[1].id, role=MembershipRole.OWNER),
    ])
    db.commit()

    token = create_access_token(admin.id)
    response = client.get(
        "/api/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["totals"]["organizations"] == 2
    assert data["totals"]["users"] >= 2
    assert data["businesses"][0]["name"] == "Northstar Supply"
    assert data["businesses"][0]["owner_email"] == "alex@northstar.example"
    assert data["users"][0]["email"] in {"alex@northstar.example", "imani@harbortrade.example", "platform-admin@daymark.app"}


def test_platform_dashboard_metrics_are_derived_from_records(client, db):
    admin = User(
        email="metrics-admin@daymark.app",
        full_name="Metrics Admin",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    plan = SubscriptionPlan(
        key="growth",
        name="Growth",
        description="Growth plan",
        monthly_price=120000,
        annual_price=1200000,
        currency="NGN",
        max_team_members=15,
        max_products=500,
        max_monthly_orders=1000,
        is_active=True,
        display_order=1,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    org1 = Organization(name="Alpha Retail", slug="alpha-retail")
    org2 = Organization(name="Beta Commerce", slug="beta-commerce")
    db.add_all([org1, org2])
    db.commit()

    owner1 = User(
        email="owner1@alpha.example",
        full_name="Owner Alpha",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
    )
    owner2 = User(
        email="owner2@beta.example",
        full_name="Owner Beta",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
    )
    db.add_all([owner1, owner2])
    db.commit()

    db.add_all([
        Membership(user_id=owner1.id, organization_id=org1.id, role=MembershipRole.OWNER),
        Membership(user_id=owner2.id, organization_id=org2.id, role=MembershipRole.OWNER),
    ])
    db.commit()

    sub1 = OrganizationSubscription(
        organization_id=org1.id,
        plan_id=plan.id,
        billing_interval=BillingInterval.MONTHLY,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
        trial_start=datetime.utcnow() - timedelta(days=15),
        trial_end=datetime.utcnow() + timedelta(days=15),
    )
    sub2 = OrganizationSubscription(
        organization_id=org2.id,
        plan_id=plan.id,
        billing_interval=BillingInterval.MONTHLY,
        status=SubscriptionStatus.SUSPENDED,
        current_period_start=datetime.utcnow() - timedelta(days=30),
        current_period_end=datetime.utcnow() + timedelta(days=5),
        trial_end=datetime.utcnow() - timedelta(days=2),
    )
    db.add_all([sub1, sub2])
    db.commit()

    db.add_all([
        PaymentTransaction(
            organization_id=org1.id,
            subscription_id=sub1.id,
            plan_id=plan.id,
            reference="PAY-100",
            amount=120000,
            currency="NGN",
            interval=BillingInterval.MONTHLY,
            status=PaymentStatus.SUCCESS,
        ),
        PaymentTransaction(
            organization_id=org1.id,
            subscription_id=sub1.id,
            plan_id=plan.id,
            reference="PAY-200",
            amount=120000,
            currency="NGN",
            interval=BillingInterval.MONTHLY,
            status=PaymentStatus.FAILED,
        ),
        PaymentTransaction(
            organization_id=org2.id,
            subscription_id=sub2.id,
            plan_id=plan.id,
            reference="PAY-300",
            amount=120000,
            currency="NGN",
            interval=BillingInterval.MONTHLY,
            status=PaymentStatus.SUCCESS,
        ),
    ])
    db.commit()

    token = create_access_token(admin.id)
    response = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["totals"]["organizations"] == 2
    assert data["totals"]["active_subscriptions"] == 1
    assert data["totals"]["suspended_businesses"] == 1
    assert data["totals"]["successful_payments"] == 2
    assert data["totals"]["failed_payments"] == 1
    assert data["totals"]["mrr"] == 120000
    assert data["totals"]["arr"] == 1440000
