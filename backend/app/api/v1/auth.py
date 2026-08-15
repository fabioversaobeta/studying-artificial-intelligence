from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.user import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> TokenResponse:
    user = auth_service.register_user(
        db, email=payload.email, password=payload.password, display_name=payload.display_name
    )
    return auth_service.issue_tokens(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = auth_service.authenticate_user(db, email=payload.email, password=payload.password)
    return auth_service.issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: DbSession) -> TokenResponse:
    return auth_service.refresh_access_token(db, refresh_token=payload.refresh_token)


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
