import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.models.user import Language


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    display_name: str
    preferred_language: Language
    is_active: bool


class UserUpdate(BaseModel):
    """PATCH /users/me: only the fields present are changed."""

    display_name: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
        | None
    ) = None
    preferred_language: Language | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    # Required only when the server is configured with REGISTRATION_INVITE_CODE.
    invite_code: str | None = Field(default=None, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    # Optional so a client that lost its refresh token can still revoke the access token.
    refresh_token: str | None = None


class RegistrationInfo(BaseModel):
    enabled: bool
    invite_required: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
