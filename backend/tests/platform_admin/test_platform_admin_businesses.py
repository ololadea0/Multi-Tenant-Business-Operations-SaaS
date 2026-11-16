from datetime import datetime, timedelta

from app.core.security import create_access_token, hash_password
from app.models.billing import BillingInterval, OrganizationSubscription, SubscriptionPlan, SubscriptionStatus
from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from app.models.user import PlatformRole, User


def test_platform_business_management_endpoints_work(client, db):
    admin = User(
        email="business-admin@daymark.app",
        full_name="Business Admin",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    plan = SubscriptionPlan(
        key="starter",
        name="Starter",
        description="Starter plan",
        monthly_price=50000,
        annual_price=500000,
        currency="NGN",
        max_team_members=5,
        max_products=100,
        max_monthly_orders=200,
        is_active=True,
        display_order=1,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    organization = Organization(name="Northwind Labs", slug="northwind-labs")
    db.add(organization)
    db.commit()
    db.refresh(organization)

    owner = User(
        email="owner@northwind.example",
        full_name="Northwind Owner",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    db.add(Membership(user_id=owner.id, organization_id=organization.id, role=MembershipRole.OWNER))
    db.commit()

    subscription = OrganizationSubscription(
        organization_id=organization.id,
        plan_id=plan.id,
        billing_interval=BillingInterval.MONTHLY,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    token = create_access_token(admin.id)
    list_response = client.get("/api/admin/businesses?search=Northwind", headers={"Authorization": f"Bearer {token}"})
    assert list_response.status_code == 200
    businesses = list_response.json()["items"]
    assert any(item["name"] == "Northwind Labs" for item in businesses)

    details_response = client.get(f"/api/admin/businesses/{organization.id}", headers={"Authorization": f"Bearer {token}"})
    assert details_response.status_code == 200
    data = details_response.json()
    assert data["owner_email"] == "owner@northwind.example"
    assert data["subscription"]["status"] == "active"

    suspend_response = client.post(f"/api/admin/businesses/{organization.id}/suspend", headers={"Authorization": f"Bearer {token}"})
    assert suspend_response.status_code == 200
    assert suspend_response.json()["status"] == "suspended"

    reactivate_response = client.post(f"/api/admin/businesses/{organization.id}/reactivate", headers={"Authorization": f"Bearer {token}"})
    assert reactivate_response.status_code == 200
    assert reactivate_response.json()["status"] == "active"
