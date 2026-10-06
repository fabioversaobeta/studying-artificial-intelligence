from fastapi import APIRouter, Depends, status

from app.api.deps import AccessClaims, CurrentUser, DbSession, SettingsDep, rate_limit_by_ip
from app.core.rate_limit import rate_limit_login_email
from app.schemas.user import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    RegistrationInfo,
    TokenResponse,
    UserRead,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


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
def register(payload: RegisterRequest, db: DbSession, settings: SettingsDep) -> TokenResponse:
    auth_service.ensure_registration_allowed(settings, payload.invite_code)
    user = auth_service.register_user(
        db, email=payload.email, password=payload.password, display_name=payload.display_name
    )
    return auth_service.issue_tokens(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit_by_ip("login"))],
)
def login(payload: LoginRequest, db: DbSession, settings: SettingsDep) -> TokenResponse:
    rate_limit_login_email(payload.email, settings)
    user = auth_service.authenticate_user(db, email=payload.email, password=payload.password)
    return auth_service.issue_tokens(user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit_by_ip("refresh"))],
)
def refresh(payload: RefreshRequest, db: DbSession) -> TokenResponse:
    return auth_service.refresh_access_token(db, refresh_token=payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest, db: DbSession, current_user: CurrentUser, claims: AccessClaims
) -> None:
    auth_service.logout(
        db, user=current_user, access_claims=claims, refresh_token=payload.refresh_token
    )


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
