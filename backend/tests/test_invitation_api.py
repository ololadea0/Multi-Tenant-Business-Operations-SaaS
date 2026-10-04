from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.models.invitation import OrganizationInvitation
from app.models.membership import Membership, MembershipRole


def test_create_invitation(
    authenticated_client,
    organization,
):
    with patch("app.api.invitation.send_organization_invitation_email"):
        response = authenticated_client.post(
            f"/api/organizations/{organization.id}/invitations/",
            json={
                "email": "invite@example.com",
                "role": "staff",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Invitation sent successfully"
    assert "invitation_id" in data


def test_create_duplicate_active_invitation(
    authenticated_client,
    organization,
    db,
):
    invitation = OrganizationInvitation(
        organization_id=organization.id,
        invited_by_user_id=1,
        email="duplicate@example.com",
        role=MembershipRole.STAFF,
        token_hash="existing-token-hash",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    db.add(invitation)
    db.commit()

    with patch("app.api.invitation.send_organization_invitation_email"):
        response = authenticated_client.post(
            f"/api/organizations/{organization.id}/invitations/",
            json={
                "email": "duplicate@example.com",
                "role": "staff",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "An active invitation already exists for this email"
    )


def test_cannot_invite_owner_role(
    authenticated_client,
    organization,
):
    with patch("app.api.invitation.send_organization_invitation_email"):
        response = authenticated_client.post(
            f"/api/organizations/{organization.id}/invitations/",
            json={
                "email": "owner@example.com",
                "role": "owner",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Owner role cannot be assigned through an invitation"
    )


def test_list_invitations(
    authenticated_client,
    organization,
    db,
    user,
):
    invitation = OrganizationInvitation(
        organization_id=organization.id,
        invited_by_user_id=user.id,
        email="list@example.com",
        role=MembershipRole.STAFF,
        token_hash="list-token-hash",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    response = authenticated_client.get(
        f"/api/organizations/{organization.id}/invitations/"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == invitation.id
    assert data[0]["email"] == "list@example.com"
    assert data[0]["role"] == "staff"


def test_revoke_invitation(
    authenticated_client,
    organization,
    db,
    user,
):
    invitation = OrganizationInvitation(
        organization_id=organization.id,
        invited_by_user_id=user.id,
        email="revoke@example.com",
        role=MembershipRole.STAFF,
        token_hash="revoke-token-hash",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    response = authenticated_client.delete(
        f"/api/organizations/{organization.id}/invitations/{invitation.id}"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Invitation revoked successfully"

    deleted = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.id == invitation.id
    ).first()

    assert deleted is None


def test_resend_invitation(
    authenticated_client,
    organization,
    db,
    user,
):
    invitation = OrganizationInvitation(
        organization_id=organization.id,
        invited_by_user_id=user.id,
        email="resend@example.com",
        role=MembershipRole.STAFF,
        token_hash="resend-token-hash",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    old_expiry = invitation.expires_at

    with patch("app.api.invitation.send_organization_invitation_email"):
        response = authenticated_client.post(
            f"/api/organizations/{organization.id}/invitations/"
            f"{invitation.id}/resend"
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Invitation resent successfully"

    db.refresh(invitation)

    assert invitation.expires_at > old_expiry


def test_staff_cannot_create_invitation(
    staff_authenticated_client,
    organization,
):
    with patch("app.api.invitation.send_organization_invitation_email"):
        response = staff_authenticated_client.post(
            f"/api/organizations/{organization.id}/invitations/",
            json={
                "email": "staff-invite@example.com",
                "role": "staff",
            },
        )

    assert response.status_code == 403


def test_staff_cannot_revoke_invitation(
    staff_authenticated_client,
    organization,
    db,
    user,
):
    invitation = OrganizationInvitation(
        organization_id=organization.id,
        invited_by_user_id=user.id,
        email="revoke-staff@example.com",
        role=MembershipRole.STAFF,
        token_hash="revoke-staff-token",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    response = staff_authenticated_client.delete(
        f"/api/organizations/{organization.id}/invitations/{invitation.id}"
    )

    assert response.status_code == 403


def test_staff_cannot_resend_invitation(
    staff_authenticated_client,
    organization,
    db,
    user,
):
    invitation = OrganizationInvitation(
        organization_id=organization.id,
        invited_by_user_id=user.id,
        email="resend-staff@example.com",
        role=MembershipRole.STAFF,
        token_hash="resend-staff-token",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    with patch("app.api.invitation.send_organization_invitation_email"):
        response = staff_authenticated_client.post(
            f"/api/organizations/{organization.id}/invitations/"
            f"{invitation.id}/resend"
        )

    assert response.status_code == 403