"""Password hashing and JWT helpers.

Password hashing uses Argon2 (via argon2-cffi), the algorithm recommended by
OWASP over bcrypt/PBKDF2 for new applications: it is memory-hard, which makes
GPU-based cracking significantly more expensive.

JWTs are used for stateless session handling. Access tokens are short-lived;
refresh tokens are longer-lived and only ever used to mint new access tokens.
"""

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

_password_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def _create_token(subject: UUID, token_type: TokenType, expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: UUID) -> str:
    settings = get_settings()
    return _create_token(
        user_id, TokenType.ACCESS, timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: UUID) -> str:
    settings = get_settings()
    return _create_token(
        user_id, TokenType.REFRESH, timedelta(minutes=settings.refresh_token_expire_minutes)
    )


class InvalidTokenError(Exception):
    pass


def decode_token(token: str, expected_type: TokenType) -> UUID:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Token is invalid or expired") from exc

    if payload.get("type") != expected_type.value:
        raise InvalidTokenError(f"Expected a {expected_type.value} token")

    try:
        return UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise InvalidTokenError("Token subject is missing or malformed") from exc
