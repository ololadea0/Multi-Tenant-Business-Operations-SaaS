from app.core.security import create_access_token
from app.models.user import User
from app.models.notification import (
    NotificationCategory,
    NotificationPreference,
    NotificationStatus,
    ensure_default_notification_preferences,
    queue_email_notification,
)


def test_user_receives_default_notification_preferences(db):
    user = User(
        email="notifications@example.com",
        full_name="Notification User",
        password_hash="hashed",
        is_active=True,
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    ensure_default_notification_preferences(db, user.id)

    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user.id
    ).all()

    assert len(preferences) >= 4
    categories = {pref.category for pref in preferences}
    assert NotificationCategory.ACCOUNT_SECURITY in categories
    assert NotificationCategory.INVITATION in categories
    assert NotificationCategory.BILLING in categories

    security = next(pref for pref in preferences if pref.category == NotificationCategory.ACCOUNT_SECURITY)
    assert security.email_enabled is True
    assert security.is_required is True


def test_queue_email_notification_persists_delivery_record(db):
    user = User(
        email="queued@example.com",
        full_name="Queued User",
        password_hash="hashed",
        is_active=True,
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    item = queue_email_notification(
        db,
        user=user,
        category=NotificationCategory.BILLING,
        subject="Your billing update",
        title="Billing update",
        body_html="<p>Your billing plan updated.</p>",
        text_body="Your billing plan updated.",
    )

    assert item is not None
    assert item.status == NotificationStatus.QUEUED
    assert item.user_id == user.id
    assert item.subject == "Your billing update"


def test_super_admin_can_preview_email_template(client, db):
    admin = User(
        email="admin@example.com",
        full_name="Platform Admin",
        password_hash="hashed",
        is_active=True,
        is_email_verified=True,
        platform_role="super_admin",
    )
    db.add(admin)
    db.commit()
    token = create_access_token(admin.id)

    response = client.post(
        "/api/admin/email/preview",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "template_key": "welcome",
            "recipient_email": "customer@example.com",
            "variables": {"first_name": "Ada"},
            "subject": "Welcome to Daymark",
            "is_promotional": False,
        },
    )

    assert response.status_code == 200
    assert "Daymark" in response.json()["html"]
    assert response.json()["subject"] == "Welcome to Daymark"


def test_super_admin_send_is_idempotent(client, db):
    admin = User(
        email="admin-idempotency@example.com",
        full_name="Platform Admin",
        password_hash="hashed",
        is_active=True,
        is_email_verified=True,
        platform_role="super_admin",
    )
    db.add(admin)
    db.commit()
    token = create_access_token(admin.id)

    payload = {
        "template_key": "announcement",
        "recipient_email": "customer@example.com",
        "subject": "Quarterly update",
        "is_promotional": True,
        "idempotency_key": "announcement-001",
        "variables": {"first_name": "Ada"},
    }

    first = client.post("/api/admin/email/send", headers={"Authorization": f"Bearer {token}"}, json=payload)
    second = client.post("/api/admin/email/send", headers={"Authorization": f"Bearer {token}"}, json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["message"] == second.json()["message"]
