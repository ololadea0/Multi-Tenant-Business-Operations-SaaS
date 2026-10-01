from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.organization import require_roles, get_user_membership
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_invitation_token, hash_invitation_token, create_access_token, create_refresh_token, hash_password
from app.models.invitation import OrganizationInvitation
from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from app.models.user import User
from app.schemas.invitation import CreateInvitationRequest, AcceptInvitationRequest, RegisterWithInvitationRequest
from app.services.email import send_organization_invitation_email
from app.api.dependencies import get_current_user
from app.models.refresh_token import RefreshToken



router = APIRouter(
    prefix="/api/organizations/{organization_id}/invitations",
    tags=["Invitations"]
)

@router.post("/")
def create_invitation(
    organization_id: int,
    data: CreateInvitationRequest,
    membership: Membership = Depends(
        require_roles(
            MembershipRole.OWNER,
            MembershipRole.ADMIN
        )
    ),
    db: Session = Depends(get_db)
):
    organization = db.query(Organization).filter(
        Organization.id == organization_id
    ).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    email = data.email.lower().strip()

    user = db.query(User).filter(
        User.email == email
    ).first()

    if user:
        existing_membership = db.query(Membership).filter(
            Membership.user_id == user.id,
            Membership.organization_id == organization_id
        ).first()

        if existing_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization"
            )

    existing_invitation = db.query(
        OrganizationInvitation
    ).filter(
        OrganizationInvitation.organization_id == organization_id,
        OrganizationInvitation.email == email,
        OrganizationInvitation.accepted_at.is_(None),
        OrganizationInvitation.expires_at > datetime.now(timezone.utc)
    ).first()

    if existing_invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active invitation already exists for this email"
        )

    if data.role == MembershipRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner role cannot be assigned through an invitation"
        )

    raw_token, token_hash = create_invitation_token()

    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invitation = OrganizationInvitation(
        organization_id=organization_id,
        invited_by_user_id=membership.user_id,
        email=email,
        role=data.role,
        token_hash=token_hash,
        expires_at=expires_at
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    inviter = db.query(User).filter(
        User.id == membership.user_id
    ).first()

    invitation_url = (
        f"{settings.FRONTEND_URL}/invitations/accept"
        f"?token={raw_token}"
    )

    send_organization_invitation_email(
        recipient=email,
        organization_name=organization.name,
        inviter_name=inviter.full_name,
        role=data.role.value,
        invitation_url=invitation_url
    )

    return {
        "message": "Invitation sent successfully",
        "invitation_id": invitation.id
    }

@router.post("/accept")
def accept_invitation(
    data: AcceptInvitationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    token_hash = hash_invitation_token(data.token)

    invitation = db.query(
        OrganizationInvitation
    ).filter(
        OrganizationInvitation.token_hash == token_hash
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invitation"
        )

    if invitation.accepted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has already been accepted"
        )

    if invitation.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired"
        )

    if current_user.email.lower() != invitation.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was sent to a different email address"
        )

    existing_membership = db.query(Membership).filter(
        Membership.user_id == current_user.id,
        Membership.organization_id == invitation.organization_id
    ).first()

    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this organization"
        )

    membership = Membership(
        user_id=current_user.id,
        organization_id=invitation.organization_id,
        role=invitation.role
    )

    db.add(membership)

    invitation.accepted_at = datetime.utcnow()

    db.commit()
    db.refresh(membership)

    return {
        "message": "Invitation accepted successfully",
        "organization_id": membership.organization_id,
        "role": membership.role
    }

@router.post("/register")
def register_with_invitation(
    data: RegisterWithInvitationRequest,
    db: Session = Depends(get_db)
):
    token_hash = hash_invitation_token(data.token)

    invitation = db.query(
        OrganizationInvitation
    ).filter(
        OrganizationInvitation.token_hash == token_hash
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invitation"
        )

    if invitation.accepted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has already been accepted"
        )

    if invitation.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired"
        )

    existing_user = db.query(User).filter(
        User.email == invitation.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "An account already exists for this email. "
                "Please log in and accept the invitation."
            )
        )

    user = User(
        email=invitation.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name
    )

    db.add(user)
    db.flush()

    membership = Membership(
        user_id=user.id,
        organization_id=invitation.organization_id,
        role=invitation.role
    )

    db.add(membership)

    invitation.accepted_at = datetime.utcnow()

    db.commit()
    db.refresh(user)
    db.refresh(membership)

    access_token = create_access_token(user.id)

    raw_refresh_token, token_hash, expires_at = (
        create_refresh_token()
    )

    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )

    db.add(refresh_token)
    db.commit()

    return {
        "message": "Account created and invitation accepted successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "organization_id": membership.organization_id,
        "role": membership.role
    }

@router.get("/")
def get_organization_invitations(
    organization_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    invitations = db.query(
        OrganizationInvitation
    ).filter(
        OrganizationInvitation.organization_id == organization_id
    ).order_by(
        OrganizationInvitation.created_at.desc()
    ).all()

    return [
        {
            "id": invitation.id,
            "email": invitation.email,
            "role": invitation.role,
            "expires_at": invitation.expires_at,
            "accepted_at": invitation.accepted_at,
            "created_at": invitation.created_at
        }
        for invitation in invitations
    ]

@router.delete("/{invitation_id}")
def revoke_invitation(
    organization_id: int,
    invitation_id: int,
    membership: Membership = Depends(
        require_roles(
            MembershipRole.OWNER,
            MembershipRole.ADMIN
        )
    ),
    db: Session = Depends(get_db)
):
    invitation = db.query(
        OrganizationInvitation
    ).filter(
        OrganizationInvitation.id == invitation_id,
        OrganizationInvitation.organization_id == organization_id
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    if invitation.accepted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has already been accepted"
        )

    db.delete(invitation)
    db.commit()

    return {
        "message": "Invitation revoked successfully"
    }

@router.post("/{invitation_id}/resend")
def resend_invitation(
    organization_id: int,
    invitation_id: int,
    membership: Membership = Depends(
        require_roles(
            MembershipRole.OWNER,
            MembershipRole.ADMIN
        )
    ),
    db: Session = Depends(get_db)
):
    invitation = db.query(
        OrganizationInvitation
    ).filter(
        OrganizationInvitation.id == invitation_id,
        OrganizationInvitation.organization_id == organization_id
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    if invitation.accepted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has already been accepted"
        )

    organization = db.query(Organization).filter(
        Organization.id == organization_id
    ).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    raw_token, token_hash = create_invitation_token()

    invitation.token_hash = token_hash
    invitation.expires_at = (
        datetime.now(timezone.utc) + timedelta(days=7)
    )

    inviter = db.query(User).filter(
        User.id == membership.user_id
    ).first()

    invitation_url = (
        f"{settings.FRONTEND_URL}/invitations/accept"
        f"?token={raw_token}"
    )

    send_organization_invitation_email(
        recipient=invitation.email,
        organization_name=organization.name,
        inviter_name=inviter.full_name,
        role=invitation.role.value,
        invitation_url=invitation_url
    )

    db.commit()

    return {
        "message": "Invitation resent successfully"
    }