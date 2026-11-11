from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.notification import NotificationCategory, NotificationPreference, ensure_default_notification_preferences
from app.models.user import User


router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


class NotificationPreferencePatch(BaseModel):
    category: NotificationCategory
    email_enabled: bool | None = None
    sms_enabled: bool | None = None
    push_enabled: bool | None = None

    model_config = ConfigDict(use_enum_values=True)


@router.get("/preferences")
def get_notification_preferences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    preferences = ensure_default_notification_preferences(db, current_user.id)
    return [
        {
            "category": pref.category.value,
            "email_enabled": pref.email_enabled,
            "sms_enabled": pref.sms_enabled,
            "push_enabled": pref.push_enabled,
            "is_required": pref.is_required,
        }
        for pref in preferences
    ]


@router.patch("/preferences")
def update_notification_preferences(
    updates: list[NotificationPreferencePatch],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preferences = ensure_default_notification_preferences(db, current_user.id)
    preference_map = {pref.category: pref for pref in preferences}

    for update in updates:
        pref = preference_map.get(update.category)
        if pref is None:
            continue
        if update.email_enabled is not None:
            pref.email_enabled = update.email_enabled
        if update.sms_enabled is not None:
            pref.sms_enabled = update.sms_enabled
        if update.push_enabled is not None:
            pref.push_enabled = update.push_enabled

    db.commit()

    return get_notification_preferences(current_user=current_user, db=db)
