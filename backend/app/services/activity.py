from sqlalchemy.orm import Session

from app.models.activity import Activity


def create_activity(
    db: Session,
    organization_id: int,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None,
    description: str
) -> Activity:
    activity = Activity(
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description
    )

    db.add(activity)
    db.flush()

    return activity
