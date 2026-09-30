from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership, MembershipRole
from app.schemas.auth import RegisterRequest


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name
    )

    db.add(user)
    db.flush()

    organization = Organization(
        name=f"{data.full_name}'s Organization",
        slug=f"user-{user.id}"
    )

    db.add(organization)
    db.flush()

    membership = Membership(
        user_id=user.id,
        organization_id=organization.id,
        role=MembershipRole.OWNER
    )

    db.add(membership)
    db.commit()

    db.refresh(user)

    return {
        "message": "Registration successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        },
        "organization": {
            "id": organization.id,
            "name": organization.name,
            "slug": organization.slug
        }
    }