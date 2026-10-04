from pydantic import BaseModel, ConfigDict

from app.models.membership import MembershipRole


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    role: MembershipRole


class OrganizationListItem(OrganizationResponse):
    pass
