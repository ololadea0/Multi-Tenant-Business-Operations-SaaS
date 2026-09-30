from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from app.models.user import User


router = APIRouter(
    prefix="/api/organizations",
    tags=["Organizations"]
)


def get_user_membership(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Membership:
    membership = db.query(Membership).filter(
        Membership.organization_id == organization_id,
        Membership.user_id == current_user.id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization"
        )

    return membership


def require_roles(*allowed_roles: MembershipRole):
    def role_checker(
        membership: Membership = Depends(get_user_membership)
    ) -> Membership:
        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )

        return membership

    return role_checker


@router.get("/{organization_id}")
def get_organization(
    organization_id: int,
    membership: Membership = Depends(get_user_membership),
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

    return {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "role": membership.role
    }

@router.post("/")
def create_organization(
    name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    slug = f"{name.lower().replace(' ', '-').strip()}-{current_user.id}"

    organization = Organization(
        name=name,
        slug=slug
    )

    db.add(organization)
    db.flush()

    membership = Membership(
        user_id=current_user.id,
        organization_id=organization.id,
        role=MembershipRole.OWNER
    )

    db.add(membership)
    db.commit()
    db.refresh(organization)

    return {
        "id": organization.id,
        "name": organization.name,
        "slug": organization.slug,
        "role": membership.role
    }

@router.get("/")
def get_user_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    memberships = db.query(Membership).filter(
        Membership.user_id == current_user.id
    ).all()

    organizations = []

    for membership in memberships:
        organization = db.query(Organization).filter(
            Organization.id == membership.organization_id
        ).first()

        if organization:
            organizations.append({
                "id": organization.id,
                "name": organization.name,
                "slug": organization.slug,
                "role": membership.role
            })

    return organizations

# @router.delete("/{organization_id}")
# def delete_organization(
#     organization_id: int,
#     membership: Membership = Depends(
#         require_roles(MembershipRole.OWNER)
#     ),
#     db: Session = Depends(get_db)
# ):
#     organization = db.query(Organization).filter(
#         Organization.id == organization_id
#     ).first()

#     if not organization:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Organization not found"
#         )

#     db.delete(organization)
#     db.commit()

#     return {
#         "message": "Organization deleted successfully"
#     }
