from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse

from app.api.csrf import require_csrf_protection
from app.api.deps import (
    CurrentUser,
    DbSession,
    OptionalAccessClaims,
    SettingsDep,
    rate_limit_by_ip,
)
from app.api.refresh_cookie import clear_refresh_cookie, read_refresh_cookie, set_refresh_cookie
from app.core.config import Settings
from app.core.exceptions import AuthenticationError
from app.core.rate_limit import rate_limit_login_email
from app.schemas.user import (
    LoginRequest,
    RegisterRequest,
    RegistrationInfo,
    TokenResponse,
    UserRead,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _start_session(
    response: Response, tokens: auth_service.IssuedTokens, settings: Settings
) -> TokenResponse:
    """Put the refresh token in its HttpOnly cookie; only the access token goes in the body."""
    set_refresh_cookie(response, tokens.refresh_token, settings)
    return TokenResponse(access_token=tokens.access_token)


@router.get("/registration-info", response_model=RegistrationInfo)
def registration_info(settings: SettingsDep) -> RegistrationInfo:
    """Public: lets the UI know whether signups are open and need an invite code."""
    return RegistrationInfo(
        enabled=settings.registration_enabled,
        invite_required=bool(settings.registration_invite_code),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_by_ip("register"))],
)
def register(
    payload: RegisterRequest, db: DbSession, settings: SettingsDep, response: Response
) -> TokenResponse:
    auth_service.ensure_registration_allowed(settings, payload.invite_code)
    user = auth_service.register_user(
        db, email=payload.email, password=payload.password, display_name=payload.display_name
    )
    return _start_session(response, auth_service.issue_tokens(user), settings)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit_by_ip("login"))],
)
def login(
    payload: LoginRequest, db: DbSession, settings: SettingsDep, response: Response
) -> TokenResponse:
    rate_limit_login_email(payload.email, settings)
    user = auth_service.authenticate_user(db, email=payload.email, password=payload.password)
    return _start_session(response, auth_service.issue_tokens(user), settings)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={401: {"description": "Missing, invalid, expired or reused refresh cookie"}},
    dependencies=[Depends(require_csrf_protection), Depends(rate_limit_by_ip("refresh"))],
)
def refresh(
    request: Request, db: DbSession, settings: SettingsDep, response: Response
) -> TokenResponse | JSONResponse:
    """Rotate the refresh cookie and return a new access token."""
    refresh_token = read_refresh_cookie(request, settings)
    if not refresh_token:
        raise AuthenticationError("Missing refresh token")
    try:
        tokens = auth_service.refresh_access_token(db, refresh_token=refresh_token)
    except AuthenticationError as exc:
        # Drop a cookie that can no longer work (expired, revoked, reuse detected).
        # Built by hand because cookies set on `response` are lost when an exception
        # handler produces the error response.
        failure = JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.error_code, "message": exc.message}},
        )
        clear_refresh_cookie(failure, settings)
        return failure
    return _start_session(response, tokens, settings)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf_protection)],
)
def logout(
    request: Request,
    db: DbSession,
    settings: SettingsDep,
    claims: OptionalAccessClaims,
) -> Response:
    """Revoke the refresh cookie (and the bearer access token, if sent) and clear the cookie."""
    auth_service.logout(
        db, access_claims=claims, refresh_token=read_refresh_cookie(request, settings)
    )
    out = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_refresh_cookie(out, settings)
    return out


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
