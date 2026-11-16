from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_super_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import PlatformRole, User
from app.api.platform_admin.common import AdminLoginRequest, BootstrapSuperAdminRequest, normalize_email, normalize_name

router = APIRouter(tags=["Platform Admin"])


@router.post("/bootstrap", status_code=status.HTTP_201_CREATED)
def bootstrap_super_admin(
    data: BootstrapSuperAdminRequest,
    db: Session = Depends(get_db),
):
    normalized_email = normalize_email(data.email)
    normalized_name = normalize_name(data.full_name)

    if db.query(User).filter(User.platform_role == PlatformRole.SUPER_ADMIN).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A platform super admin already exists.",
        )

    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        existing_user.full_name = normalized_name
        existing_user.password_hash = hash_password(data.password)
        existing_user.platform_role = PlatformRole.SUPER_ADMIN
        existing_user.is_active = True
        existing_user.is_email_verified = True
        db.commit()
        db.refresh(existing_user)
        return {
            "id": existing_user.id,
            "email": existing_user.email,
            "full_name": existing_user.full_name,
            "platform_role": existing_user.platform_role.value,
            "message": "Super admin bootstrapped successfully.",
        }

    user = User(
        email=normalized_email,
        full_name=normalized_name,
        password_hash=hash_password(data.password),
        platform_role=PlatformRole.SUPER_ADMIN,
        is_active=True,
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "platform_role": user.platform_role.value,
        "message": "Super admin bootstrapped successfully.",
    }


@router.post(
    "/login",
    dependencies=[Depends(rate_limit("admin-login", limit=settings.AUTH_LOGIN_RATE_LIMIT, window_seconds=60))],
)
@router.post(
    "/auth/login",
    dependencies=[Depends(rate_limit("admin-login", limit=settings.AUTH_LOGIN_RATE_LIMIT, window_seconds=60))],
)
def admin_login(
    data: AdminLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    normalized_email = normalize_email(data.email)
    user = db.query(User).filter(User.email == normalized_email).first()

    if not user or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "email_verification_required", "email": user.email, "message": "Please verify your email address first."},
        )

    if user.platform_role != PlatformRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super admin access required")

    access_token = create_access_token(user.id)
    raw_refresh_token, token_hash, expires_at = create_refresh_token()

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "platform_role": user.platform_role.value,
        },
    }


@router.get("/me")
def admin_me(current_user: User = Depends(get_current_super_admin)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "platform_role": current_user.platform_role.value,
        "is_active": current_user.is_active,
    }
