from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from sqlalchemy.orm import Session
import hashlib

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, hash_refresh_token, create_password_reset_token
from datetime import datetime, timedelta, timezone
from app.core.config import settings

from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership, MembershipRole
from app.schemas.auth import RegisterRequest, LoginRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.api.dependencies import get_current_user
from app.models.refresh_token import RefreshToken
from app.models.password_reset_token import PasswordResetToken
from app.services.email import send_password_reset_email
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url=(
        "https://accounts.google.com/.well-known/openid-configuration"
    ),
    client_kwargs={
        "scope": "openid email profile"
    }
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

@router.get("/google")
async def google_login(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )

@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    token = await oauth.google.authorize_access_token(request)

    user_info = token.get("userinfo")

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to retrieve Google user information"
        )

    google_id = user_info.get("sub")
    email = user_info.get("email")
    full_name = user_info.get("name")
    avatar_url = user_info.get("picture")

    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account information is incomplete"
        )

    user = db.query(User).filter(
        User.google_id == google_id
    ).first()

    if not user:
        user = db.query(User).filter(
            User.email == email
        ).first()

    if not user:
        user = User(
            email=email,
            full_name=full_name or email.split("@")[0],
            google_id=google_id,
            avatar_url=avatar_url
        )

        db.add(user)
        db.flush()

        organization = Organization(
            name=f"{user.full_name}'s Organization",
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

    else:
        if not user.google_id:
            user.google_id = google_id

        if avatar_url:
            user.avatar_url = avatar_url

        db.commit()
        db.refresh(user)

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

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

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
    response: Response,
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

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        secure=False,  # True in production with HTTPS
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
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
        "token_type": "bearer"
    }

@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if user:
        raw_token, token_hash = create_password_reset_token()

        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )

        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )

        db.add(reset_token)
        db.commit()

        reset_url = (
            f"{settings.FRONTEND_URL}"
            f"/reset-password?token={raw_token}"
        )

        send_password_reset_email(
            user.email,
            reset_url
        )

    return {
        "message": "If an account with that email exists, "
        "a password reset link has been sent."
    }

@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    token_hash = hashlib.sha256(
        data.token.encode("utf-8")
    ).hexdigest()

    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash
    ).first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    if reset_token.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    now = datetime.now(timezone.utc)

    if reset_token.expires_at.replace(
        tzinfo=timezone.utc
    ) < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    user = db.query(User).filter(
        User.id == reset_token.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    user.password_hash = hash_password(data.new_password)

    reset_token.used_at = now

    db.commit()

    return {
        "message": "Password reset successful"
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
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing"
        )
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

    response.set_cookie(
        key="refresh_token",
        value=new_raw_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
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
        "token_type": "bearer"
}

@router.post("/logout")
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if refresh_token:
        token_hash = hash_refresh_token(refresh_token)

        stored_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        if stored_token:
            stored_token.revoked_at = datetime.now(timezone.utc)
            db.commit()

    response.delete_cookie(
        key="refresh_token"
    )

    return {
        "message": "Logout successful"
    }