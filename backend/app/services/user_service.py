from sqlalchemy.orm import Session

from app.models.user import Language, User


def update_profile(
    db: Session,
    user: User,
    *,
    display_name: str | None = None,
    preferred_language: Language | None = None,
) -> User:
    """Apply the profile fields that were provided (None means "leave as is")."""
    if display_name is not None:
        user.display_name = display_name
    if preferred_language is not None:
        user.preferred_language = preferred_language
    db.commit()
    db.refresh(user)
    return user
