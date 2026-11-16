from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_super_admin
from app.core.database import get_db
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import PlatformRole, User
from app.api.platform_admin.common import format_relative_time

router = APIRouter(tags=["Platform Admin"])


@router.get("/users")
def list_platform_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    role: str | None = Query(default=None),
    organization_id: int | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)

    if search:
        term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(User.full_name).like(term),
                func.lower(User.email).like(term),
            )
        )

    if status:
        normalized_status = status.lower()
        if normalized_status == "active":
            query = query.filter(User.is_active.is_(True))
        elif normalized_status in {"inactive", "suspended"}:
            query = query.filter(User.is_active.is_(False))

    if role:
        try:
            query = query.filter(User.platform_role == PlatformRole(role))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid platform role")

    if organization_id:
        query = query.join(Membership, Membership.user_id == User.id).filter(Membership.organization_id == organization_id)

    valid_sort_fields = {"created_at": User.created_at, "email": User.email, "name": User.full_name}
    sort_field = valid_sort_fields.get(sort_by, User.created_at)
    direction = getattr(sort_field, "desc" if order.lower() == "desc" else "asc")()
    total = query.count()
    users = query.order_by(direction).offset((page - 1) * limit).limit(limit).all()

    items = []
    for user in users:
        memberships = (
            db.query(Membership)
            .join(Organization, Organization.id == Membership.organization_id)
            .filter(Membership.user_id == user.id)
            .all()
        )
        organizations = []
        for membership in memberships:
            organization = db.query(Organization).filter(Organization.id == membership.organization_id).first()
            organizations.append({
                "id": organization.id if organization else None,
                "name": organization.name if organization else "Unknown business",
                "role": membership.role.value if hasattr(membership.role, "value") else str(membership.role),
            })

        items.append({
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "platform_role": user.platform_role.value,
            "status": "active" if user.is_active else "suspended",
            "email_verified": user.is_email_verified,
            "last_active": format_relative_time(user.updated_at or user.created_at),
            "organizations": organizations,
            "business_count": len(organizations),
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })

    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit if total else 0,
    }


@router.get("/users/{user_id}")
def get_platform_user_detail(
    user_id: int,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    memberships = (
        db.query(Membership)
        .join(Organization, Organization.id == Membership.organization_id)
        .filter(Membership.user_id == user.id)
        .all()
    )

    organizations = []
    for membership in memberships:
        org = db.query(Organization).filter(Organization.id == membership.organization_id).first()
        organizations.append({
            "id": org.id if org else membership.organization_id,
            "name": org.name if org else "Unknown business",
            "role": membership.role.value if hasattr(membership.role, "value") else str(membership.role),
            "joined_at": membership.created_at.isoformat() if membership.created_at else None,
        })

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "platform_role": user.platform_role.value,
        "status": "active" if user.is_active else "suspended",
        "email_verified": user.is_email_verified,
        "is_active": user.is_active,
        "google_id": user.google_id,
        "organizations": organizations,
        "business_count": len(organizations),
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }
