from app.core.security import create_access_token, hash_password
from app.models.billing import SubscriptionPlan
from app.models.platform_settings import PlatformSettings
from app.models.user import PlatformRole, User


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
    db.commit()

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


def test_super_admin_can_update_trial_policy_and_billing_options(client, db):
    user = User(
        email="superadmin.billing-policy@daymark.app",
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
            "trial_enabled": False,
            "trial_plan_key": "business",
            "billing_intervals": ["annual"],
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
    assert response.json()["trial_enabled"] is False
    assert response.json()["trial_plan_key"] == "business"
    assert response.json()["billing_intervals"] == ["annual"]

    saved = db.query(PlatformSettings).first()
    assert saved.trial_enabled is False
    assert saved.trial_plan_key == "business"
    assert saved.billing_intervals == "annual"


def test_super_admin_can_toggle_plan_availability(client, db):
    user = User(
        email="superadmin.plan-toggle@daymark.app",
        full_name="Platform Admin",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(user)
    db.commit()

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
        is_active=True,
        display_order=2,
    )
    db.add(plan)
    db.commit()

    token = create_access_token(user.id)
    response = client.patch(
        "/api/admin/plans/growth",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Growth",
            "description": "Growth plan",
            "monthly_price": 16000,
            "annual_price": 160000,
            "max_team_members": 6,
            "max_products": 600,
            "max_monthly_orders": 1200,
            "is_active": False,
            "display_order": 9,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["display_order"] == 9

    saved = db.query(SubscriptionPlan).filter(SubscriptionPlan.key == "growth").one()
    assert saved.is_active is False
    assert saved.display_order == 9


def test_platform_health_reports_worker_and_prunes_stale_debug_plan(client, db):
    user = User(
        email="superadmin.health@daymark.app",
        full_name="Platform Admin",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(user)
    db.commit()

    stale_plan = SubscriptionPlan(
        key="growth2",
        name="Growth2",
        description="Debug plan",
        monthly_price=5000,
        annual_price=50000,
        currency="NGN",
        max_team_members=5,
        max_products=500,
        max_monthly_orders=1000,
    )
    db.add(stale_plan)
    db.commit()

    token = create_access_token(user.id)
    response = client.get(
        "/api/admin/health",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["billing_worker_running"] in {True, False}
    assert payload["database_connected"] is True
    assert db.query(SubscriptionPlan).filter(SubscriptionPlan.key == "growth2").count() == 0


def test_super_admin_can_recreate_stale_debug_plan_key(client, db):
    user = User(
        email="superadmin.plan-recreate@daymark.app",
        full_name="Platform Admin",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
        is_email_verified=True,
        platform_role=PlatformRole.SUPER_ADMIN,
    )
    db.add(user)
    db.commit()

    stale_plan = SubscriptionPlan(
        key="growth2",
        name="Growth2",
        description="Debug plan",
        monthly_price=5000,
        annual_price=50000,
        currency="NGN",
        max_team_members=5,
        max_products=500,
        max_monthly_orders=1000,
    )
    db.add(stale_plan)
    db.commit()

    token = create_access_token(user.id)
    response = client.post(
        "/api/admin/plans",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "key": "growth2",
            "name": "Growth 2",
            "description": "Fresh replacement plan",
            "monthly_price": 19000,
            "annual_price": 190000,
            "currency": "NGN",
            "max_team_members": 7,
            "max_products": 700,
            "max_monthly_orders": 1200,
            "is_active": True,
            "display_order": 20,
        },
    )

    assert response.status_code == 201
    assert response.json()["key"] == "growth2"
    assert db.query(SubscriptionPlan).filter(SubscriptionPlan.key == "growth2").count() == 1


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
