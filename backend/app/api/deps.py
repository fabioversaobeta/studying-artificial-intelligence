from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError
from app.core.rate_limit import client_ip, limiter
from app.core.security import InvalidTokenError, TokenType, decode_token
from app.infrastructure.database.session import get_db
from app.models.user import User
from app.repositories import user_repository

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


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> User:
    if credentials is None:
        raise AuthenticationError("Missing authentication credentials")

    try:
        user_id = decode_token(credentials.credentials, TokenType.ACCESS)
    except InvalidTokenError as exc:
        raise AuthenticationError(str(exc)) from exc

    user = user_repository.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("User no longer exists or is inactive")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
