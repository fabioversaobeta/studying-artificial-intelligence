from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError
from app.core.rate_limit import client_ip, limiter
from app.core.security import InvalidTokenError, TokenClaims, TokenType, decode_token_claims
from app.infrastructure.database.session import get_db
from app.models.user import User
from app.repositories import user_repository
from app.services import auth_service

_bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def rate_limit_by_ip(scope: str) -> Callable[..., None]:
    """Build a dependency limiting `scope` (e.g. "login") per client IP."""

    def dependency(request: Request, settings: SettingsDep) -> None:
        if not settings.rate_limit_enabled:
            return
        limiter.hit(
            f"{scope}:ip:{client_ip(request, settings)}",
            max_requests=settings.rate_limit_max_requests,
            window_seconds=settings.rate_limit_window_seconds,
        )

    return dependency


def get_access_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> TokenClaims:
    if credentials is None:
        raise AuthenticationError("Missing authentication credentials")
    try:
        return decode_token_claims(credentials.credentials, TokenType.ACCESS)
    except InvalidTokenError as exc:
        raise AuthenticationError(str(exc)) from exc


AccessClaims = Annotated[TokenClaims, Depends(get_access_claims)]


def get_optional_access_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> TokenClaims | None:
    """Claims of a valid access token, or None (used by logout, which never fails)."""
    if credentials is None:
        return None
    try:
        return decode_token_claims(credentials.credentials, TokenType.ACCESS)
    except InvalidTokenError:
        return None


OptionalAccessClaims = Annotated[TokenClaims | None, Depends(get_optional_access_claims)]


def get_current_user(db: DbSession, claims: AccessClaims) -> User:
    user = user_repository.get_by_id(db, claims.user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("User no longer exists or is inactive")
    auth_service.ensure_not_revoked(db, claims, user)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_optional_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> User | None:
    """The authenticated user, or None for anonymous requests. A bearer token
    that is present but invalid still fails with 401."""
    if credentials is None:
        return None
    return get_current_user(db, get_access_claims(credentials))


OptionalUser = Annotated[User | None, Depends(get_optional_user)]
