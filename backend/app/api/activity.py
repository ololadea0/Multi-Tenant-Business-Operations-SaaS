from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.organization import get_user_membership
from app.core.database import get_db
from app.models.activity import Activity
from app.models.membership import Membership

router = APIRouter(
    prefix="/api/organizations/{organization_id}/activities",
    tags=["Activities"]
)


@router.get("/", response_model=dict)
def get_activities(
    organization_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    action: str | None = Query(default=None),
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    query = db.query(Activity).filter(
        Activity.organization_id == organization_id
    )

    if action:
        query = query.filter(Activity.action == action)

    total = query.count()

    activities = query.order_by(
        Activity.created_at.desc(),
        Activity.id.desc()
    ).offset(
        (page - 1) * limit
    ).limit(limit).all()

    return {
        "items": activities,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }
