from pydantic import BaseModel, EmailStr

from app.models.membership import MembershipRole
from app.schemas.auth import RegisterRequest


class CreateInvitationRequest(BaseModel):
    email: EmailStr
    role: MembershipRole = MembershipRole.STAFF

class AcceptInvitationRequest(BaseModel):
    token: str

class RegisterWithInvitationRequest(RegisterRequest):
    token: str