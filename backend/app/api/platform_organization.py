import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.membership import Membership, MembershipRole
from app.services.billing import require_subscription_write_access
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import (
    OrganizationListItem,
    OrganizationResponse,
    OrganizationUpdate,
)


router = APIRouter(
    prefix="/api/organizations",
    tags=["Organizations"],
)


def slugify_organization_name(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return cleaned or "organization"


def get_user_membership(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Membership:
    membership = db.query(Membership).filter(
        Membership.organization_id == organization_id,
        Membership.user_id == current_user.id,
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization",
        )

    return membership


def require_roles(*allowed_roles: MembershipRole):
    def role_checker(
        membership: Membership = Depends(get_user_membership),
    ) -> Membership:
        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return membership

    return role_checker


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    organization_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db),
):
    organization = db.query(Organization).filter(
        Organization.id == organization_id,
    ).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return OrganizationResponse(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        role=membership.role,
        address_line_1=organization.address_line_1,
        address_line_2=organization.address_line_2,
        city=organization.city,
        state=organization.state,
        postal_code=organization.postal_code,
        country=organization.country,
        phone=organization.phone,
        email=organization.email,
        website=organization.website,
    )


@router.patch("/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    organization_id: int,
    data: OrganizationUpdate,
    membership: Membership = Depends(require_roles(MembershipRole.OWNER)),
    db: Session = Depends(get_db),
):
    require_subscription_write_access(db, organization_id)
    organization = db.query(Organization).filter(
        Organization.id == organization_id,
    ).first()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    if data.name is not None:
        clean_name = data.name.strip()
        if not clean_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name cannot be empty",
            )
        organization.name = clean_name

    for field in [
        "address_line_1",
        "address_line_2",
        "city",
        "state",
        "postal_code",
        "country",
        "phone",
        "email",
        "website",
    ]:
        value = getattr(data, field)
        if value is not None:
            clean_value = value.strip() if isinstance(value, str) else value
            setattr(organization, field, clean_value or None)

    db.commit()
    db.refresh(organization)

    return OrganizationResponse(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        role=membership.role,
        address_line_1=organization.address_line_1,
        address_line_2=organization.address_line_2,
        city=organization.city,
        state=organization.state,
        postal_code=organization.postal_code,
        country=organization.country,
        phone=organization.phone,
        email=organization.email,
        website=organization.website,
    )


@router.post("/", response_model=OrganizationResponse)
def create_organization(
    name: str,
    email: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slug_base = slugify_organization_name(name)
    slug = f"{slug_base}-{current_user.id}"

    try:
        organization = Organization(
            name=name,
            slug=slug,
            email=email.strip() if email else None,
        )

        db.add(organization)
        db.flush()

        membership = Membership(
            user_id=current_user.id,
            organization_id=organization.id,
            role=MembershipRole.OWNER,
        )

        db.add(membership)
        db.commit()
        db.refresh(organization)

        return OrganizationResponse(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            role=membership.role,
            address_line_1=organization.address_line_1,
            address_line_2=organization.address_line_2,
            city=organization.city,
            state=organization.state,
            postal_code=organization.postal_code,
            country=organization.country,
            phone=organization.phone,
            email=organization.email,
            website=organization.website,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization could not be created. Please try a different name.",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization. Please try again.",
        )


@router.get("/", response_model=list[OrganizationListItem])
def get_user_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organizations = (
        db.query(Organization, Membership.role)
        .join(Membership, Membership.organization_id == Organization.id)
        .filter(Membership.user_id == current_user.id)
        .all()
    )

    return [
        OrganizationListItem(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            role=role,
            address_line_1=organization.address_line_1,
            address_line_2=organization.address_line_2,
            city=organization.city,
            state=organization.state,
            postal_code=organization.postal_code,
            country=organization.country,
            phone=organization.phone,
            email=organization.email,
            website=organization.website,
        )
        for organization, role in organizations
    ]


@router.delete("/{organization_id}/leave")
def leave_organization(
    organization_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db),
):
    if membership.role == MembershipRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The organization owner cannot leave. Transfer ownership first.",
        )

    db.delete(membership)
    db.commit()

    return {
        "message": "You left the organization",
    }
