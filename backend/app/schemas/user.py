import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    display_name: str
    is_active: bool


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    # Required only when the server is configured with REGISTRATION_INVITE_CODE.
    invite_code: str | None = Field(default=None, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegistrationInfo(BaseModel):
    enabled: bool
    invite_required: bool


class TokenResponse(BaseModel):
    """Body of login/register/refresh. The refresh token travels only in an
    HttpOnly cookie and is never part of the JSON body."""

    access_token: str
    token_type: str = "bearer"
