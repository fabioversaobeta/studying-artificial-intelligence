from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.user import UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserRead)
def update_me(payload: UserUpdate, current_user: CurrentUser, db: DbSession) -> UserRead:
    """Change your display name and/or preferred content language."""
    user = user_service.update_profile(
        db,
        current_user,
        display_name=payload.display_name,
        preferred_language=payload.preferred_language,
    )
    return UserRead.model_validate(user)
