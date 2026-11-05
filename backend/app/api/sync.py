from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.organization import get_user_membership
from app.core.database import get_db
from app.models.membership import Membership
from app.models.sync import SyncEntityVersion, SyncQueueItem
from app.schemas.sync import SyncPushRequest

router = APIRouter(
    prefix="/api/organizations/{organization_id}/sync",
    tags=["Sync"]
)


@router.get("/status")
def get_sync_status(
    organization_id: int,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    pending_items = db.query(SyncQueueItem).filter(
        SyncQueueItem.organization_id == organization_id,
        SyncQueueItem.status.in_(["queued", "processing", "failed"])
    ).count()

    last_item = db.query(SyncQueueItem).filter(
        SyncQueueItem.organization_id == organization_id
    ).order_by(
        SyncQueueItem.updated_at.desc()
    ).first()

    latest_version = db.query(SyncEntityVersion).filter(
        SyncEntityVersion.organization_id == organization_id
    ).order_by(
        SyncEntityVersion.updated_at.desc()
    ).first()

    return {
        "organization_id": organization_id,
        "user_id": membership.user_id,
        "pending_count": pending_items,
        "last_synced_at": last_item.updated_at.isoformat() if last_item else None,
        "server_version": latest_version.version if latest_version else 0,
    }


@router.get("/changes")
def get_sync_changes(
    organization_id: int,
    since: datetime | None = Query(default=None),
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    query = db.query(SyncQueueItem).filter(
        SyncQueueItem.organization_id == organization_id
    )

    if since is not None:
        query = query.filter(SyncQueueItem.updated_at >= since)

    items = query.order_by(
        SyncQueueItem.updated_at.desc(),
        SyncQueueItem.id.desc(),
    ).all()

    latest_version = db.query(SyncEntityVersion).filter(
        SyncEntityVersion.organization_id == organization_id
    ).order_by(
        SyncEntityVersion.updated_at.desc()
    ).first()

    return {
        "items": [
            {
                "id": item.id,
                "operation_id": item.operation_id,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "action": item.action,
                "status": item.status,
                "base_version": item.base_version,
                "payload": item.payload,
                "updated_at": item.updated_at.isoformat(),
            }
            for item in items
        ],
        "server_version": latest_version.version if latest_version else 0,
        "last_synced_at": items[0].updated_at.isoformat() if items else None,
    }


@router.post("/push")
def push_sync_operations(
    organization_id: int,
    data: SyncPushRequest,
    membership: Membership = Depends(get_user_membership),
    db: Session = Depends(get_db)
):
    accepted = 0
    duplicates = 0
    results = []

    for operation in data.operations:
        existing = db.query(SyncQueueItem).filter(
            SyncQueueItem.organization_id == organization_id,
            SyncQueueItem.operation_id == operation.operation_id,
        ).first()

        if existing:
            results.append({
                "operation_id": operation.operation_id,
                "entity_type": operation.entity_type,
                "entity_id": operation.entity_id,
                "status": "duplicate",
                "base_version": operation.base_version,
            })
            duplicates += 1
            continue

        current_version = db.query(SyncEntityVersion).filter(
            SyncEntityVersion.organization_id == organization_id,
            SyncEntityVersion.entity_type == operation.entity_type,
            SyncEntityVersion.entity_id == operation.entity_id,
        ).first()

        current_version_number = current_version.version if current_version else 0

        if operation.base_version != current_version_number:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Stale sync version for {operation.entity_type}:{operation.entity_id}. "
                    f"Current version is {current_version_number}, but base version was {operation.base_version}."
                )
            )

        queue_item = SyncQueueItem(
            organization_id=organization_id,
            user_id=membership.user_id,
            operation_id=operation.operation_id,
            entity_type=operation.entity_type,
            entity_id=operation.entity_id,
            action=operation.action,
            payload=operation.payload,
            base_version=operation.base_version,
            status="queued",
        )

        db.add(queue_item)

        if current_version is None:
            current_version = SyncEntityVersion(
                organization_id=organization_id,
                entity_type=operation.entity_type,
                entity_id=operation.entity_id,
                version=1,
            )
            db.add(current_version)
        else:
            current_version.version += 1
            current_version.updated_at = datetime.utcnow()

        accepted += 1
        results.append({
            "operation_id": operation.operation_id,
            "entity_type": operation.entity_type,
            "entity_id": operation.entity_id,
            "status": "queued",
            "base_version": operation.base_version,
            "new_version": current_version.version,
        })

    db.commit()

    return {
        "accepted": accepted,
        "duplicates": duplicates,
        "results": results,
    }
