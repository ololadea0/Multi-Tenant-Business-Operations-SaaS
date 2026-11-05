from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    description: str
    created_at: datetime
