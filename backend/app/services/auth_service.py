from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories import gamification_repository, user_repository
from app.schemas.user import TokenResponse


def register_user(db: Session, *, email: str, password: str, display_name: str) -> User:
    if user_repository.get_by_email(db, email) is not None:
        raise ConflictError("An account with this email already exists")

    user = user_repository.create(
        db, email=email, hashed_password=hash_password(password), display_name=display_name
    )
    gamification_repository.create_profile(db, user.id)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User:
    user = user_repository.get_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")
    if not user.is_active:
        raise AuthenticationError("This account has been deactivated")
    return user


def issue_tokens(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


def refresh_access_token(db: Session, *, refresh_token: str) -> TokenResponse:
    try:
        user_id = decode_token(refresh_token, TokenType.REFRESH)
    except InvalidTokenError as exc:
        raise AuthenticationError(str(exc)) from exc

    user = user_repository.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("User no longer exists or is inactive")

    return issue_tokens(user)
