from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.organization import get_user_membership, require_roles
from app.core.database import get_db
from app.models.membership import Membership, MembershipRole
from app.models.user import User
from app.schemas.member import (
    AddMemberRequest,
    UpdateMemberRoleRequest,
)


router = APIRouter(
    prefix="/api/organizations/{organization_id}/members",
    tags=["Members"]
)

@router.post("/")
def add_member(
    organization_id: int,
    data: AddMemberRequest,
    membership: Membership = Depends(
        require_roles(
            MembershipRole.OWNER,
            MembershipRole.ADMIN
        )
    ),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == data.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    existing_membership = db.query(Membership).filter(
        Membership.user_id == data.user_id,
        Membership.organization_id == organization_id
    ).first()

    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this organization"
        )

    if data.role == MembershipRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the ownership transfer flow to assign ownership"
        )

    new_membership = Membership(
        user_id=data.user_id,
        organization_id=organization_id,
        role=data.role
    )

    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)

    return {
        "message": "Member added successfully",
        "user_id": new_membership.user_id,
        "organization_id": new_membership.organization_id,
        "role": new_membership.role
    }


@router.post("/")
def add_member(
    organization_id: int,
    data: AddMemberRequest,
    membership: Membership = Depends(
        require_roles(
            MembershipRole.OWNER,
            MembershipRole.ADMIN
        )
    ),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == data.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    existing_membership = db.query(Membership).filter(
        Membership.user_id == data.user_id,
        Membership.organization_id == organization_id
    ).first()

    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this organization"
        )

    if data.role == MembershipRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the ownership transfer flow to assign ownership"
        )

    new_membership = Membership(
        user_id=data.user_id,
        organization_id=organization_id,
        role=data.role
    )

    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)

    return {
        "message": "Member added successfully",
        "user_id": new_membership.user_id,
        "organization_id": new_membership.organization_id,
        "role": new_membership.role
    }

@router.patch("/{user_id}")
def update_member_role(
    organization_id: int,
    user_id: int,
    data: UpdateMemberRoleRequest,
    membership: Membership = Depends(
        require_roles(
            MembershipRole.OWNER,
            MembershipRole.ADMIN
        )
    ),
    db: Session = Depends(get_db)
):
    target_membership = db.query(Membership).filter(
        Membership.organization_id == organization_id,
        Membership.user_id == user_id
    ).first()

    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    if target_membership.role == MembershipRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner role cannot be changed here"
        )

    if data.role == MembershipRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the ownership transfer flow to assign ownership"
        )

    target_membership.role = data.role

    db.commit()
    db.refresh(target_membership)

    return {
        "message": "Member role updated successfully",
        "user_id": target_membership.user_id,
        "role": target_membership.role
    }

@router.delete("/{user_id}")
def remove_member(
    organization_id: int,
    user_id: int,
    membership: Membership = Depends(
        require_roles(
            MembershipRole.OWNER,
            MembershipRole.ADMIN
        )
    ),
    db: Session = Depends(get_db)
):
    target_membership = db.query(Membership).filter(
        Membership.organization_id == organization_id,
        Membership.user_id == user_id
    ).first()

    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    if target_membership.role == MembershipRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The organization owner cannot be removed"
        )

    db.delete(target_membership)
    db.commit()

    return {
        "message": "Member removed successfully"
    }

