from pydantic import BaseModel

from app.models.membership import MembershipRole


class AddMemberRequest(BaseModel):
    user_id: int
    role: MembershipRole = MembershipRole.STAFF


class UpdateMemberRoleRequest(BaseModel):
    role: MembershipRole