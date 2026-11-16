from datetime import datetime, timedelta

from app.models.billing import BillingInterval, OrganizationSubscription, SubscriptionPlan, SubscriptionStatus
from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from app.models.user import User
from app.services.billing import refresh_subscription_status


def test_manager_cannot_start_subscription_checkout(client, organization, db):
    manager_user = User(
        email="manager@example.com",
        full_name="Manager User",
        password_hash="hashed",
        is_active=True,
    )
    db.add(manager_user)
    db.commit()
    db.refresh(manager_user)

    manager_membership = Membership(
        user_id=manager_user.id,
        organization_id=organization.id,
        role=MembershipRole.MANAGER,
    )
    db.add(manager_membership)
    db.commit()

    def override_current_user():
        return manager_user

    from app.api.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.post(
        f"/api/organizations/{organization.id}/billing/checkout",
        json={
            "plan_key": "starter",
            "interval": "monthly",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Only the organization owner or an admin can start a subscription payment. Managers cannot pay for the plan."
    )

    app.dependency_overrides.clear()


def test_expired_subscription_blocks_write_operations(client, organization, db, user):
    plan = SubscriptionPlan(
        key="growth",
        name="Growth",
        description="Growth plan",
        monthly_price=15000,
        annual_price=150000,
        currency="NGN",
        max_team_members=5,
        max_products=500,
        max_monthly_orders=1000,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    expired_subscription = OrganizationSubscription(
        organization_id=organization.id,
        plan_id=plan.id,
        billing_interval=BillingInterval.MONTHLY,
        status=SubscriptionStatus.EXPIRED,
        start_date=datetime.utcnow() - timedelta(days=30),
        current_period_start=datetime.utcnow() - timedelta(days=30),
        current_period_end=datetime.utcnow() - timedelta(days=1),
        trial_start=None,
        trial_end=None,
    )
    db.add(expired_subscription)
    db.commit()

    def override_current_user():
        return user

    from app.api.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.post(
        f"/api/organizations/{organization.id}/products",
        json={
            "name": "Blocked Product",
            "sku": "BLOCKED-001",
            "unit_price": "15000.00",
            "stock_quantity": 2,
            "low_stock_threshold": 1,
        },
    )

    assert response.status_code == 403
    assert "read-only" in response.json()["detail"].lower()

    app.dependency_overrides.clear()


def test_past_due_subscription_blocks_write_operations(client, organization, db, user):
    plan = SubscriptionPlan(
        key="growth",
        name="Growth",
        description="Growth plan",
        monthly_price=15000,
        annual_price=150000,
        currency="NGN",
        max_team_members=5,
        max_products=500,
        max_monthly_orders=1000,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    past_due_subscription = OrganizationSubscription(
        organization_id=organization.id,
        plan_id=plan.id,
        billing_interval=BillingInterval.MONTHLY,
        status=SubscriptionStatus.PAST_DUE,
        start_date=datetime.utcnow() - timedelta(days=45),
        current_period_start=datetime.utcnow() - timedelta(days=45),
        current_period_end=datetime.utcnow() - timedelta(days=2),
        trial_start=None,
        trial_end=None,
    )
    db.add(past_due_subscription)
    db.commit()

    def override_current_user():
        return user

    from app.api.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.post(
        f"/api/organizations/{organization.id}/products",
        json={
            "name": "Past Due Product",
            "sku": "PAST-DUE-001",
            "unit_price": "15000.00",
            "stock_quantity": 1,
            "low_stock_threshold": 1,
        },
    )

    assert response.status_code == 403
    assert "read-only" in response.json()["detail"].lower()

    app.dependency_overrides.clear()


def test_refresh_subscription_status_moves_active_subscription_into_past_due_and_expired_grace_period(db, organization):
    plan = SubscriptionPlan(
        key="growth",
        name="Growth",
        description="Growth plan",
        monthly_price=15000,
        annual_price=150000,
        currency="NGN",
        max_team_members=5,
        max_products=500,
        max_monthly_orders=1000,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    subscription = OrganizationSubscription(
        organization_id=organization.id,
        plan_id=plan.id,
        billing_interval=BillingInterval.MONTHLY,
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.utcnow() - timedelta(days=60),
        current_period_start=datetime.utcnow() - timedelta(days=40),
        current_period_end=datetime.utcnow() - timedelta(days=1),
        trial_start=None,
        trial_end=None,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    refreshed = refresh_subscription_status(db, subscription)

    assert refreshed.status == SubscriptionStatus.PAST_DUE

    subscription.current_period_end = datetime.utcnow() - timedelta(days=10)
    subscription.status = SubscriptionStatus.ACTIVE
    db.commit()

    refreshed = refresh_subscription_status(db, subscription)
    assert refreshed.status == SubscriptionStatus.EXPIRED


def test_process_billing_reminders_sends_owner_email_for_expiring_subscription(db, organization):
    plan = SubscriptionPlan(
        key="growth",
        name="Growth",
        description="Growth plan",
        monthly_price=15000,
        annual_price=150000,
        currency="NGN",
        max_team_members=5,
        max_products=500,
        max_monthly_orders=1000,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    owner = User(
        email="owner@example.com",
        full_name="Owner Name",
        password_hash="hashed",
        is_active=True,
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
        start_date=datetime.utcnow() - timedelta(days=20),
        current_period_start=datetime.utcnow() - timedelta(days=20),
        current_period_end=datetime.utcnow() + timedelta(hours=12),
        trial_start=None,
        trial_end=None,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    sent = []

    def fake_send(recipient, subject, title, body, text):
        sent.append({"recipient": recipient, "subject": subject})
        return True

    from app.services import billing as billing_service
    original = billing_service.send_generic_email
    billing_service.send_generic_email = fake_send
    try:
        result = billing_service.process_billing_reminders(db)
    finally:
        billing_service.send_generic_email = original

    assert result >= 1
    assert any(item["recipient"] == owner.email for item in sent)


def test_get_organization(
    authenticated_client,
    organization,
):
    response = authenticated_client.get(
        f"/api/organizations/{organization.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == organization.id
    assert data["name"] == organization.name
    assert data["slug"] == organization.slug
    assert data["role"] == "owner"


def test_get_nonexistent_organization(
    authenticated_client,
):
    response = authenticated_client.get(
        "/api/organizations/999999"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have access to this organization"
    )


def test_get_organization_without_membership(
    client,
    user,
    db,
):
    other_organization = Organization(
        name="Other Organization",
        slug="other-organization",
    )

    db.add(other_organization)
    db.commit()
    db.refresh(other_organization)

    def override_current_user():
        return user

    from app.api.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.get(
        f"/api/organizations/{other_organization.id}"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have access to this organization"
    )

    app.dependency_overrides.clear()


def test_create_organization(
    authenticated_client,
):
    response = authenticated_client.post(
        "/api/organizations/",
        params={
            "name": "New Organization"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "New Organization"
    assert data["slug"].startswith("new-organization-")
    assert data["role"] == "owner"


def test_list_user_organizations(
    authenticated_client,
    organization,
):
    response = authenticated_client.get(
        "/api/organizations/"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == organization.id
    assert data[0]["name"] == organization.name
    assert data[0]["role"] == "owner"

def test_admin_cannot_update_organization_metadata(
    client,
    organization,
    db,
):
    admin_user = User(
        email="admin@example.com",
        full_name="Admin User",
        password_hash="hashed",
        is_active=True,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    admin_membership = Membership(
        user_id=admin_user.id,
        organization_id=organization.id,
        role=MembershipRole.ADMIN,
    )
    db.add(admin_membership)
    db.commit()

    def override_current_user():
        return admin_user

    from app.api.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.patch(
        f"/api/organizations/{organization.id}",
        json={
            "name": "Updated by admin",
            "email": "admin@updated.com",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to perform this action"
    )

    app.dependency_overrides.clear()


def test_member_can_leave_organization(
    client,
    organization,
    db,
):
    member_user = User(
        email="member@example.com",
        full_name="Member User",
        password_hash="hashed",
        is_active=True,
    )
    db.add(member_user)
    db.commit()
    db.refresh(member_user)

    member_membership = Membership(
        user_id=member_user.id,
        organization_id=organization.id,
        role=MembershipRole.STAFF,
    )
    db.add(member_membership)
    db.commit()

    def override_current_user():
        return member_user

    from app.api.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.delete(f"/api/organizations/{organization.id}/leave")

    assert response.status_code == 200
    assert response.json()["message"] == "You left the organization"

    remaining_membership = (
        db.query(Membership)
        .filter(
            Membership.organization_id == organization.id,
            Membership.user_id == member_user.id,
        )
        .first()
    )
    assert remaining_membership is None

    app.dependency_overrides.clear()

def test_update_organization_metadata(
    authenticated_client,
    organization,
):
    response = authenticated_client.patch(
        f"/api/organizations/{organization.id}",
        json={
            "name": "Updated Studio",
            "email": "hello@updatedstudio.com",
            "address_line_1": "123 Main Street",
            "city": "Lagos",
            "country": "Nigeria",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Studio"
    assert data["email"] == "hello@updatedstudio.com"
    assert data["address_line_1"] == "123 Main Street"
    assert data["city"] == "Lagos"
    assert data["country"] == "Nigeria"


def test_staff_can_access_organization(
    staff_authenticated_client,
    organization,
):
    response = staff_authenticated_client.get(
        f"/api/organizations/{organization.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == organization.id
    assert data["role"] == "staff"


def test_staff_organizations_list(
    staff_authenticated_client,
    organization,
):
    response = staff_authenticated_client.get(
        "/api/organizations/"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == organization.id
    assert data[0]["role"] == "staff"