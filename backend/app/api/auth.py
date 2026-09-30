from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, hash_refresh_token
from datetime import datetime, timezone




from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership, MembershipRole
from app.schemas.auth import RegisterRequest, LoginRequest
from app.api.dependencies import get_current_user

from app.models.refresh_token import RefreshToken


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

@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

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
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "token_type": "bearer"
    }

@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "is_active": current_user.is_active
    }

@router.post("/refresh")
def refresh(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    token_hash = hash_refresh_token(refresh_token)

    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    now = datetime.now(timezone.utc)

    if stored_token.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )

    if stored_token.expires_at.replace(
        tzinfo=timezone.utc
    ) < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )

    user = db.query(User).filter(
        User.id == stored_token.user_id
    ).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not available"
        )

    stored_token.revoked_at = now

    access_token = create_access_token(user.id)

    new_raw_token, new_token_hash, new_expires_at = (
        create_refresh_token()
    )

    new_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        expires_at=new_expires_at
    )

    db.add(new_refresh_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_raw_token,
        "token_type": "bearer"
    }

@router.post("/logout")
def logout(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    token_hash = hash_refresh_token(refresh_token)

    stored_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    if stored_token:
        stored_token.revoked_at = datetime.now(timezone.utc)
        db.commit()

    return {
        "message": "Logout successful"
    }