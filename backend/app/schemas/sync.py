from typing import Any

from pydantic import BaseModel, Field


class SyncOperation(BaseModel):
    operation_id: str
    entity_type: str
    entity_id: int
    action: str
    base_version: int = 0
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncPushRequest(BaseModel):
    operations: list[SyncOperation]
