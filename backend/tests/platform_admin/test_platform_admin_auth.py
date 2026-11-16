from datetime import datetime, timedelta

from app.core.security import hash_password
from app.models.billing import BillingInterval, OrganizationSubscription, PaymentStatus, PaymentTransaction, SubscriptionPlan, SubscriptionStatus
from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from app.models.user import PlatformRole, User
from app.core.security import create_access_token


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
