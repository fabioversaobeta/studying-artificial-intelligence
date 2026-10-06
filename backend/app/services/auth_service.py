import secrets
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, AuthorizationError, ConflictError
from app.core.security import (
    InvalidTokenError,
    TokenClaims,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token_claims,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories import gamification_repository, revoked_token_repository, user_repository
from app.schemas.user import TokenResponse


def ensure_registration_allowed(settings: Settings, invite_code: str | None) -> None:
    """Enforce the signup policy (REGISTRATION_ENABLED / REGISTRATION_INVITE_CODE)."""
    if not settings.registration_enabled:
        raise AuthorizationError("Registration is currently closed")
    expected = settings.registration_invite_code
    # Constant-time comparison; same message for missing and wrong codes.
    if expected and (
        invite_code is None or not secrets.compare_digest(invite_code.encode(), expected.encode())
    ):
        raise AuthorizationError("A valid invite code is required to register")


def register_user(db: Session, *, email: str, password: str, display_name: str) -> User:
    if user_repository.get_by_email(db, email) is not None:
        raise ConflictError("An account with this email already exists")

    try:
        user = user_repository.create(
            db, email=email, hashed_password=hash_password(password), display_name=display_name
        )
        gamification_repository.create_profile(db, user.id)
        db.commit()
    except IntegrityError as exc:
        # Lost a race with a concurrent registration of the same email: the
        # unique constraint is the real guard, the get_by_email check above
        # is only a fast path.
        db.rollback()
        raise ConflictError("An account with this email already exists") from exc
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


def ensure_not_revoked(db: Session, claims: TokenClaims, user: User) -> None:
    """Reject a token that was revoked individually or predates a revoke-all."""
    if revoked_token_repository.is_revoked(db, claims.jti):
        raise AuthenticationError("Token has been revoked")
    cutoff = user.tokens_valid_after
    if cutoff is not None and claims.issued_at <= cutoff:
        raise AuthenticationError("Token has been revoked")


def refresh_access_token(db: Session, *, refresh_token: str) -> TokenResponse:
    """Rotate a refresh token: burn the presented one and issue a new pair.

    Presenting an already-used refresh token is treated as theft: every
    token of the user issued so far is invalidated, forcing a fresh login.
    """
    try:
        claims = decode_token_claims(refresh_token, TokenType.REFRESH)
    except InvalidTokenError as exc:
        raise AuthenticationError(str(exc)) from exc

    user = user_repository.get_by_id(db, claims.user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("User no longer exists or is inactive")

    cutoff = user.tokens_valid_after
    if cutoff is not None and claims.issued_at <= cutoff:
        raise AuthenticationError("Token has been revoked")

    newly_revoked = revoked_token_repository.revoke(
        db,
        jti=claims.jti,
        user_id=user.id,
        token_type=TokenType.REFRESH.value,
        expires_at=claims.expires_at,
    )
    if not newly_revoked:
        # Reuse detected: kill every session. Floored to the second (and compared with <=) because
        # JWT `iat` has second resolution.
        user.tokens_valid_after = datetime.now(UTC).replace(microsecond=0)
        db.commit()
        raise AuthenticationError("Refresh token reuse detected; please sign in again")

    tokens = issue_tokens(user)
    db.commit()
    return tokens


def logout(
    db: Session, *, user: User, access_claims: TokenClaims, refresh_token: str | None
) -> None:
    """Revoke the current access token and (if valid and the user's) the refresh token."""
    revoked_token_repository.revoke(
        db,
        jti=access_claims.jti,
        user_id=user.id,
        token_type=TokenType.ACCESS.value,
        expires_at=access_claims.expires_at,
    )
    if refresh_token:
        try:
            refresh_claims = decode_token_claims(refresh_token, TokenType.REFRESH)
        except InvalidTokenError:
            refresh_claims = None
        if refresh_claims is not None and refresh_claims.user_id == user.id:
            revoked_token_repository.revoke(
                db,
                jti=refresh_claims.jti,
                user_id=user.id,
                token_type=TokenType.REFRESH.value,
                expires_at=refresh_claims.expires_at,
            )
    db.commit()


def purge_expired_revocations(db: Session, now: datetime | None = None) -> int:
    """Delete denylist rows whose tokens have expired anyway. Returns rows removed."""
    removed = revoked_token_repository.delete_expired(db, now or datetime.now(UTC))
    db.commit()
    return removed
