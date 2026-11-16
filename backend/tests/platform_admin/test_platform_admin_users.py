from app.core.security import create_access_token, hash_password
from app.models.billing import BillingInterval, OrganizationSubscription, PaymentStatus, PaymentTransaction, SubscriptionPlan, SubscriptionStatus
from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from app.models.user import PlatformRole, User


def test_platform_user_directory_and_search_endpoints_work(client, db):
    admin = User(
        email="directory-admin@daymark.app",
        full_name="Directory Admin",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    org = Organization(name="Atlas Freight", slug="atlas-freight")
    db.add(org)
    db.commit()
    db.refresh(org)

    users = [
        User(email="sarah@atlas.example", full_name="Sarah Lee", password_hash=hash_password("StrongPassword123!"), is_active=True, is_email_verified=True),
        User(email="alex@northstar.example", full_name="Alex Green", password_hash=hash_password("StrongPassword123!"), is_active=False, is_email_verified=True),
        User(email="maria@atlas.example", full_name="Maria Scott", password_hash=hash_password("StrongPassword123!"), is_active=True, is_email_verified=False),
    ]
    db.add_all(users)
    db.commit()
    for user in users:
        db.refresh(user)

    db.add_all([
        Membership(user_id=users[0].id, organization_id=org.id, role=MembershipRole.OWNER),
        Membership(user_id=users[2].id, organization_id=org.id, role=MembershipRole.ADMIN),
    ])
    db.commit()

    token = create_access_token(admin.id)
    response = client.get("/api/admin/users?search=atlas&status=active", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(item["email"] == "sarah@atlas.example" for item in data["items"])
    assert all(item["status"] == "active" for item in data["items"])

    detail = client.get(f"/api/admin/users/{users[0].id}", headers={"Authorization": f"Bearer {token}"})
    assert detail.status_code == 200
    detail_data = detail.json()
    assert detail_data["email"] == "sarah@atlas.example"
    assert detail_data["organizations"][0]["name"] == "Atlas Freight"


def test_platform_subscription_payment_and_analytics_endpoints_work(client, db):
    admin = User(
        email="metrics-platform@daymark.app",
        full_name="Metrics Platform Admin",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    plan = SubscriptionPlan(
        key="scale",
        name="Scale",
        description="Scale plan",
        monthly_price=200000,
        annual_price=2000000,
        currency="NGN",
        max_team_members=25,
        max_products=800,
        max_monthly_orders=5000,
        is_active=True,
        display_order=1,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    org = Organization(name="Solstice Pro", slug="solstice-pro")
    db.add(org)
    db.commit()
    db.refresh(org)

    subscription = OrganizationSubscription(
        organization_id=org.id,
        plan_id=plan.id,
        billing_interval=BillingInterval.ANNUAL,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=org.created_at,
        current_period_end=org.created_at,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    for reference, status in [("PAY-001", PaymentStatus.SUCCESS), ("PAY-002", PaymentStatus.FAILED)]:
        db.add(PaymentTransaction(
            organization_id=org.id,
            subscription_id=subscription.id,
            plan_id=plan.id,
            reference=reference,
            amount=200000,
            currency="NGN",
            interval=BillingInterval.ANNUAL,
            status=status,
        ))
    db.commit()

    token = create_access_token(admin.id)
    subs = client.get("/api/admin/subscriptions?status=active", headers={"Authorization": f"Bearer {token}"})
    assert subs.status_code == 200
    assert subs.json()["total"] >= 1

    pay = client.get("/api/admin/payments?status=success", headers={"Authorization": f"Bearer {token}"})
    assert pay.status_code == 200
    assert pay.json()["total"] >= 1

    analytics = client.get("/api/admin/analytics", headers={"Authorization": f"Bearer {token}"})
    assert analytics.status_code == 200
    body = analytics.json()
    assert body["summary"]["active_subscriptions"] >= 1
    assert body["summary"]["successful_payments"] >= 1
    assert body["summary"]["organizations"] >= 1
