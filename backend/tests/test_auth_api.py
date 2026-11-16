from app.models.user import User
from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from app.models.billing import BillingInterval, OrganizationSubscription, PaymentStatus, PaymentTransaction, SubscriptionPlan, SubscriptionStatus
from app.models.platform_settings import PlatformSettings
from app.models.announcement import PlatformAnnouncement
from datetime import datetime, timedelta, timezone

from app.core.security import hash_refresh_token
from app.models.refresh_token import RefreshToken
from unittest.mock import patch, AsyncMock

from app.models.password_reset_token import PasswordResetToken
from app.core.security import create_access_token, create_password_reset_token, hash_password
from app.core.security import verify_password
from app.models.user import PlatformRole
from app.models.audit_log import PlatformAuditLog

def test_root_has_cors_headers(client):
    response = client.get(
        "/",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_register_user(client, db):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "full_name": "New User",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["message"] == "Registration successful"
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["full_name"] == "New User"

    assert "organization" in data
    assert data["organization"]["name"] == "New User's Organization"

    user = db.query(User).filter(
        User.email == "newuser@example.com"
    ).first()

    assert user is not None
    assert user.password_hash is not None

    membership = db.query(Membership).filter(
        Membership.user_id == user.id
    ).first()

    assert membership is not None
    assert membership.role == MembershipRole.OWNER


def test_register_duplicate_email(client, user):
    response = client.post(
        "/api/auth/register",
        json={
            "email": user.email,
            "password": "StrongPassword123!",
            "full_name": "Another User",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already registered"


def test_register_validation_error_has_consistent_shape(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "missing-full-name@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert data["detail"] == "Validation failed"
    assert "errors" in data
    assert any(error["loc"] == ["body", "full_name"] for error in data["errors"])


def test_register_normalizes_user_input_and_rejects_blank_name(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "  NewUser@Example.com   ",
            "password": "StrongPassword123!",
            "full_name": "   ",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Full name cannot be blank."

    response = client.post(
        "/api/auth/register",
        json={
            "email": "  NewUser@Example.com   ",
            "password": "StrongPassword123!",
            "full_name": "  Jane Doe  ",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["full_name"] == "Jane Doe"


def test_register_rejects_weak_password(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "weakpass@example.com",
            "password": "weak",
            "full_name": "Weak Password",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Password must be at least 8 characters long and include an uppercase letter, "
        "a lowercase letter, a number, and a special character."
    )


def test_login_success(client, user):
    response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "refresh_token" in response.cookies


def test_login_wrong_password(client, user):
    response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "doesnotexist@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_inactive_user(client, user, db):
    user.is_active = False
    db.commit()

    response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User account is inactive"

def test_get_current_user(authenticated_client, user):
    response = authenticated_client.get("/api/auth/me")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user.id
    assert data["email"] == user.email
    assert data["full_name"] == user.full_name
    assert data["is_active"] is True


def test_super_admin_can_update_plan_persistence(client, db):
    user = User(
        email="superadmin.plan@daymark.app",
        full_name="Platform Admin",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(user)
    db.flush()

    plan = SubscriptionPlan(
        key="starter",
        name="Starter",
        description="Default starter plan",
        monthly_price=7500,
        annual_price=75000,
        currency="NGN",
        max_team_members=2,
        max_products=100,
        max_monthly_orders=200,
        display_order=1,
    )
    db.add(plan)
    db.commit()

    token = create_access_token(user.id)
    response = client.patch(
        "/api/admin/plans/starter",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Starter Plus",
            "description": "Updated starter plan",
            "monthly_price": 9000,
            "annual_price": 90000,
            "max_team_members": 4,
            "max_products": 180,
            "max_monthly_orders": 300,
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Starter Plus"

    saved = db.query(SubscriptionPlan).filter(SubscriptionPlan.key == "starter").one()
    assert saved.monthly_price == 9000
    assert saved.max_products == 180


def test_super_admin_can_persist_platform_settings(client, db):
    user = User(
        email="superadmin.settings@daymark.app",
        full_name="Platform Admin",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(user)
    db.commit()

    token = create_access_token(user.id)
    response = client.put(
        "/api/admin/settings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "trial_duration_days": 21,
            "annual_billing_discount_percent": 18,
            "payment_grace_period_days": 5,
            "support_email": "support@daymark.io",
            "support_phone": "+234 800 111 0000",
            "help_center_url": "https://help.daymark.io",
            "allow_new_registrations": False,
            "maintenance_notice_enabled": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["support_email"] == "support@daymark.io"

    saved = db.query(PlatformSettings).first()
    assert saved is not None
    assert saved.support_email == "support@daymark.io"
    assert saved.allow_new_registrations is False


def test_super_admin_can_manage_platform_announcements(client, db):
    user = User(
        email="superadmin.announce@daymark.app",
        full_name="Platform Admin",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(user)
    db.commit()

    token = create_access_token(user.id)
    create_response = client.post(
        "/api/admin/announcements",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Scheduled maintenance",
            "message": "We are applying a security patch to the platform.",
            "kind": "maintenance",
            "is_active": True,
            "starts_at": "2026-11-11T12:00:00Z",
            "ends_at": "2026-11-12T12:00:00Z",
        },
    )

    assert create_response.status_code == 201
    assert create_response.json()["title"] == "Scheduled maintenance"

    list_response = client.get(
        "/api/admin/announcements",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["title"] == "Scheduled maintenance"


def test_authenticated_user_can_read_public_maintenance_notice(client, db):
    user = User(
        email="business.owner@daymark.app",
        full_name="Business Owner",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.USER,
    )
    db.add(user)
    db.flush()

    db.add(
        PlatformSettings(
            maintenance_notice_enabled=True,
            maintenance_message="Planned maintenance from 12:00 UTC",
        )
    )
    db.add(
        PlatformAnnouncement(
            title="Scheduled maintenance",
            message="The platform will be briefly unavailable for maintenance.",
            kind="maintenance",
            is_active=True,
        )
    )
    db.commit()

    token = create_access_token(user.id)

    settings_response = client.get(
        "/api/admin/public/settings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert settings_response.status_code == 200
    assert settings_response.json()["maintenance_notice_enabled"] is True

    announcements_response = client.get(
        "/api/admin/public/announcements",
        headers={"Authorization": f"Bearer {token}"},
        params={"active_only": True},
    )
    assert announcements_response.status_code == 200
    assert announcements_response.json()["items"][0]["title"] == "Scheduled maintenance"


def test_super_admin_login_includes_platform_role(client, db):
    user = User(
        email="superadmin@daymark.app",
        full_name="Platform Admin",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/auth/login",
        json={
            "email": "superadmin@daymark.app",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["user"]["platform_role"] == "super_admin"

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {response.json()['access_token']}"})
    assert me.status_code == 200
    assert me.json()["platform_role"] == "super_admin"


def test_get_current_user_without_auth(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


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
        User(
            email="alex@northstar.example",
            full_name="Alex Morgan",
            password_hash=hash_password("StrongPassword123!"),
            is_active=True,
            is_email_verified=True,
        ),
        User(
            email="imani@harbortrade.example",
            full_name="Imani Cole",
            password_hash=hash_password("StrongPassword123!"),
            is_active=True,
            is_email_verified=True,
        ),
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


def test_platform_super_admin_bootstrap_creates_single_super_admin(client, db):
    response = client.post(
        "/api/admin/bootstrap",
        json={
            "email": "superadmin@daymark.app",
            "password": "StrongPassword123!",
            "full_name": "Platform Admin",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["platform_role"] == "super_admin"

    user = db.query(User).filter(User.email == "superadmin@daymark.app").first()
    assert user is not None
    assert user.platform_role == PlatformRole.SUPER_ADMIN

    second = client.post(
        "/api/admin/bootstrap",
        json={
            "email": "another@daymark.app",
            "password": "StrongPassword123!",
            "full_name": "Another Admin",
        },
    )

    assert second.status_code == 409
    assert "already exists" in second.json()["detail"].lower()


def test_platform_admin_login_requires_super_admin(client, db):
    regular = User(
        email="regular@daymark.app",
        full_name="Regular User",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
    )
    db.add(regular)
    db.commit()

    response = client.post(
        "/api/admin/auth/login",
        json={
            "email": "regular@daymark.app",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Super admin access required"


def test_platform_admin_login_requires_verified_email(client, db):
    admin = User(
        email="pending-admin@daymark.app",
        full_name="Pending Admin",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=False,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(admin)
    db.commit()

    response = client.post(
        "/api/admin/login",
        json={
            "email": "pending-admin@daymark.app",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "email_verification_required"


def test_platform_role_enum_supports_future_admin_roles():
    assert PlatformRole.SUPER_ADMIN.value == "super_admin"
    assert PlatformRole.SUPPORT_ADMIN.value == "support_admin"
    assert PlatformRole.BILLING_ADMIN.value == "billing_admin"
    assert PlatformRole.PLATFORM_ANALYST.value == "platform_analyst"


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
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=365),
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


def test_refresh_token(client, user):
    # First login to obtain the refresh-token cookie
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200
    old_refresh_token = login_response.cookies.get("refresh_token")

    response = client.post("/api/auth/refresh")

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    new_refresh_token = response.cookies.get("refresh_token")

    assert new_refresh_token is not None
    assert new_refresh_token != old_refresh_token


def test_refresh_without_token(client):
    response = client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token is missing"


def test_refresh_with_invalid_token(client):
    client.cookies.set("refresh_token", "invalid-token")

    response = client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"

def test_refresh_with_revoked_token(client, user, db):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.cookies.get("refresh_token")

    token_hash = hash_refresh_token(refresh_token)

    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    assert stored_token is not None

    stored_token.revoked_at = datetime.now(timezone.utc)
    db.commit()

    client.cookies.set("refresh_token", refresh_token)

    response = client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token has been revoked"


def test_refresh_with_expired_token(client, user, db):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.cookies.get("refresh_token")
    assert refresh_token is not None

    token_hash = hash_refresh_token(refresh_token)

    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    assert stored_token is not None

    stored_token.expires_at = (
        datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    )
    db.commit()

    db.refresh(stored_token)

    assert stored_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None)

    client.cookies.set("refresh_token", refresh_token)

    response = client.post("/api/auth/refresh")

    print("RESPONSE:", response.status_code, response.json())

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token has expired"

def test_logout(client, user, db):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.cookies.get("refresh_token")
    assert refresh_token is not None

    token_hash = hash_refresh_token(refresh_token)

    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    assert stored_token is not None
    assert stored_token.revoked_at is None

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Logout successful"

    db.refresh(stored_token)

    assert stored_token.revoked_at is not None

def test_logout_without_token(client):
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Logout successful"

def test_forgot_password_existing_user(client, user):
    with patch("app.api.auth.send_password_reset_email") as mock_send:
        response = client.post(
            "/api/auth/forgot-password",
            json={
                "email": user.email,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == (
        "If an account with that email exists, "
        "a password reset link has been sent."
    )

    mock_send.assert_called_once()
    assert mock_send.call_args.args[0] == user.email


def test_forgot_password_nonexistent_user(client):
    with patch("app.api.auth.send_password_reset_email") as mock_send:
        response = client.post(
            "/api/auth/forgot-password",
            json={
                "email": "doesnotexist@example.com",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == (
        "If an account with that email exists, "
        "a password reset link has been sent."
    )

    mock_send.assert_not_called()

def test_reset_password_success(client, user, db):
    raw_token, token_hash = create_password_reset_token()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )

    db.add(reset_token)
    db.commit()

    response = client.post(
        "/api/auth/reset-password",
        json={
            "token": raw_token,
            "new_password": "NewPassword123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successful"

    db.refresh(reset_token)
    db.refresh(user)

    assert reset_token.used_at is not None
    assert verify_password("NewPassword123!", user.password_hash)


def test_reset_password_invalid_token(client):
    response = client.post(
        "/api/auth/reset-password",
        json={
            "token": "invalid-token",
            "new_password": "NewPassword123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token"


def test_reset_password_rejects_weak_password(client, user, db):
    raw_token, token_hash = create_password_reset_token()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )

    db.add(reset_token)
    db.commit()

    response = client.post(
        "/api/auth/reset-password",
        json={
            "token": raw_token,
            "new_password": "weak",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Password must be at least 8 characters long and include an uppercase letter, "
        "a lowercase letter, a number, and a special character."
    )


def test_reset_password_used_token(client, user, db):
    raw_token, token_hash = create_password_reset_token()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        used_at=datetime.now(timezone.utc),
    )

    db.add(reset_token)
    db.commit()

    response = client.post(
        "/api/auth/reset-password",
        json={
            "token": raw_token,
            "new_password": "NewPassword123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token"


def test_reset_password_expired_token(client, user, db):
    raw_token, token_hash = create_password_reset_token()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=(
            datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        ),
    )

    db.add(reset_token)
    db.commit()

    assert reset_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None)

    response = client.post(
        "/api/auth/reset-password",
        json={
            "token": raw_token,
            "new_password": "NewPassword123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token"

def test_google_callback_creates_user_and_organization(client, db):
    google_user_info = {
        "sub": "google-123",
        "email": "googleuser@example.com",
        "name": "Google User",
        "picture": "https://example.com/avatar.jpg",
        "email_verified": True,
    }

    with patch(
        "app.api.auth.oauth.google.authorize_access_token",
        new_callable=AsyncMock,
    ) as mock_authorize:
        mock_authorize.return_value = {
            "userinfo": google_user_info
        }

        response = client.get("/api/auth/google/callback")

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    user = db.query(User).filter(
        User.email == "googleuser@example.com"
    ).first()

    assert user is not None
    assert user.google_id == "google-123"

    organization = db.query(Organization).filter(
        Organization.name == "Google User's Organization"
    ).first()

    assert organization is not None

    membership = db.query(Membership).filter(
        Membership.user_id == user.id,
        Membership.organization_id == organization.id,
    ).first()

    assert membership is not None
    assert membership.role == MembershipRole.OWNER


def test_google_callback_rejects_unverified_email(client):
    google_user_info = {
        "sub": "google-456",
        "email": "unverified@example.com",
        "name": "Unverified User",
        "email_verified": False,
    }

    with patch(
        "app.api.auth.oauth.google.authorize_access_token",
        new_callable=AsyncMock,
    ) as mock_authorize:
        mock_authorize.return_value = {
            "userinfo": google_user_info
        }

        response = client.get("/api/auth/google/callback")

    assert response.status_code == 400
    assert response.json()["detail"] == "Google email is not verified"


def test_google_callback_missing_userinfo(client):
    with patch(
        "app.api.auth.oauth.google.authorize_access_token",
        new_callable=AsyncMock,
    ) as mock_authorize:
        mock_authorize.return_value = {}

        response = client.get("/api/auth/google/callback")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Unable to retrieve Google user information"
    )

def test_google_callback_links_existing_user(client, user, db):
    google_user_info = {
        "sub": "google-existing-123",
        "email": user.email,
        "name": user.full_name,
        "picture": "https://example.com/avatar.jpg",
        "email_verified": True,
    }

    with patch(
        "app.api.auth.oauth.google.authorize_access_token",
        new_callable=AsyncMock,
    ) as mock_authorize:
        mock_authorize.return_value = {
            "userinfo": google_user_info
        }

        response = client.get("/api/auth/google/callback")

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    db.refresh(user)

    assert user.google_id == "google-existing-123"

    users = db.query(User).filter(
        User.email == user.email
    ).all()

    assert len(users) == 1

def test_google_callback_existing_google_user(client, user, db):
    user.google_id = "google-existing-456"
    db.commit()

    organization_count_before = db.query(Organization).filter(
        Organization.name == f"{user.full_name}'s Organization"
    ).count()

    google_user_info = {
        "sub": "google-existing-456",
        "email": user.email,
        "name": user.full_name,
        "picture": "https://example.com/new-avatar.jpg",
        "email_verified": True,
    }

    with patch(
        "app.api.auth.oauth.google.authorize_access_token",
        new_callable=AsyncMock,
    ) as mock_authorize:
        mock_authorize.return_value = {
            "userinfo": google_user_info
        }

        response = client.get("/api/auth/google/callback")

    assert response.status_code == 200

    db.refresh(user)

    assert user.google_id == "google-existing-456"
    assert user.avatar_url == "https://example.com/new-avatar.jpg"

    organization_count_after = db.query(Organization).filter(
        Organization.name == f"{user.full_name}'s Organization"
    ).count()

    assert organization_count_after == organization_count_before
