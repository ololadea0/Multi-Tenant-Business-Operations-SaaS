from app.models.user import User
from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from datetime import datetime, timedelta, timezone

from app.core.security import hash_refresh_token
from app.models.refresh_token import RefreshToken
from unittest.mock import patch, AsyncMock

from app.models.password_reset_token import PasswordResetToken
from app.core.security import create_password_reset_token, hash_password
from app.core.security import verify_password

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


def test_get_current_user_without_auth(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401

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