from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

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

    try:
        total = query.count()
        activities = query.order_by(Activity.created_at.desc(), Activity.id.desc()).offset((page - 1) * limit).limit(limit).all()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Activity history is temporarily unavailable. Please try again.")

    return {
        "items": [{
            "id": item.id,
            "organization_id": item.organization_id,
            "user_id": item.user_id,
            "action": item.action,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "description": item.description,
            "created_at": item.created_at,
        } for item in activities],
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit
    }
