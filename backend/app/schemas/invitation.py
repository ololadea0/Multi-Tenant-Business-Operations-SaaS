from pydantic import BaseModel, EmailStr

from app.models.membership import MembershipRole
from app.schemas.auth import RegisterRequest
from datetime import datetime


class CreateInvitationRequest(BaseModel):
    email: EmailStr
    role: MembershipRole = MembershipRole.STAFF

class AcceptInvitationRequest(BaseModel):
    token: str

class RegisterWithInvitationRequest(RegisterRequest):
    token: str

class InvitationResponse(BaseModel):
    id: int
    email: EmailStr
    role: MembershipRole
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime