import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.organization import require_roles, get_user_membership
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_invitation_token, hash_invitation_token, create_access_token, create_refresh_token, hash_password
from app.models.invitation import OrganizationInvitation
from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from app.models.user import User
from app.schemas.invitation import CreateInvitationRequest, AcceptInvitationRequest, RegisterWithInvitationRequest
from app.services.activity import create_activity
from app.services.email import send_organization_invitation_email
from app.api.dependencies import get_current_user
from app.models.refresh_token import RefreshToken

logger = logging.getLogger(__name__)


def _normalize_utc_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


router = APIRouter(
    prefix="/api/organizations/{organization_id}/invitations",
    tags=["Invitations"]
)

public_router = APIRouter(prefix="/api/invitations", tags=["Invitations"])

@router.get("/")
def list_invitations(
    organization_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db),
):
    invitations = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.organization_id == organization_id,
        OrganizationInvitation.accepted_at.is_(None),
        OrganizationInvitation.expires_at > datetime.now(timezone.utc),
    ).order_by(OrganizationInvitation.created_at.desc()).all()
    return [{"id": item.id, "email": item.email, "role": item.role.value, "created_at": item.created_at, "expires_at": item.expires_at} for item in invitations]

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

    create_activity(
        db=db,
        organization_id=organization_id,
        user_id=membership.user_id,
        action="invitation.created",
        entity_type="invitation",
        entity_id=invitation.id,
        description=f"Invitation for '{email}' was created for the {data.role.value} role"
    )

    db.commit()
    db.refresh(invitation)

    inviter = membership.user

    invitation_url = (
        f"{settings.FRONTEND_URL}/invitations/accept"
        f"?token={raw_token}"
    )

    try:
        sent = send_organization_invitation_email(
            recipient=email,
            organization_name=organization.name,
            inviter_name=inviter.full_name,
            role=data.role.value,
            invitation_url=invitation_url,
            expires_at=expires_at
        )
        if not sent:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invitation was saved, but the email provider did not accept the message. Please try again.")
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Failed to send organization invitation email for organization_id=%s email=%s",
            organization_id,
            email,
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

    existing_membership = db.query(Membership).filter(Membership.user_id == current_user.id, Membership.organization_id == invitation.organization_id).first()
    if invitation.accepted_at is not None:
        if existing_membership:
            return {"message": "Invitation already accepted", "organization_id": invitation.organization_id, "role": existing_membership.role}
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has already been accepted")

    expires_at = _normalize_utc_datetime(invitation.expires_at)
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired"
        )

    if current_user.email.lower() != invitation.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was sent to a different email address"
        )

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

    create_activity(
        db=db,
        organization_id=invitation.organization_id,
        user_id=current_user.id,
        action="invitation.accepted",
        entity_type="invitation",
        entity_id=invitation.id,
        description=f"Invitation for '{current_user.email}' was accepted"
    )

    invitation.accepted_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(membership)
    except IntegrityError:
        db.rollback()
        logger.exception("Invitation membership conflict for user_id=%s organization_id=%s", current_user.id, invitation.organization_id)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You may already belong to this organization, or the invitation is no longer available.")
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Invitation acceptance database failure for user_id=%s organization_id=%s", current_user.id, invitation.organization_id)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="The organization could not be joined right now. Please try again.")

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

    expires_at = _normalize_utc_datetime(invitation.expires_at)
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
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

    create_activity(
        db=db,
        organization_id=invitation.organization_id,
        user_id=user.id,
        action="invitation.accepted",
        entity_type="invitation",
        entity_id=invitation.id,
        description=f"Invitation for '{user.email}' was accepted during signup"
    )

    invitation.accepted_at = datetime.now(timezone.utc)

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

    inviter = membership.user

    invitation_url = (
        f"{settings.FRONTEND_URL}/invitations/accept"
        f"?token={raw_token}"
    )

    sent = send_organization_invitation_email(
        recipient=invitation.email,
        organization_name=organization.name,
        inviter_name=inviter.full_name,
        role=invitation.role.value,
        invitation_url=invitation_url,
        expires_at=invitation.expires_at
    )

    if not sent:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="The invitation email could not be sent. Please try again.")

    db.commit()

    return {
        "message": "Invitation resent successfully"
    }

@public_router.post("/accept")
def public_accept_invitation(data: AcceptInvitationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return accept_invitation(data=data, current_user=current_user, db=db)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Invitation acceptance failed for user_id=%s", current_user.id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Invitation acceptance failed: {exc}")

@public_router.post("/register")
def public_register_with_invitation(data: RegisterWithInvitationRequest, db: Session = Depends(get_db)):
    return register_with_invitation(data=data, db=db)
