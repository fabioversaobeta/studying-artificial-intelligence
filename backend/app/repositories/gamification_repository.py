import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.gamification import GamificationProfile


def get_profile(db: Session, user_id: uuid.UUID) -> GamificationProfile | None:
    stmt = select(GamificationProfile).where(GamificationProfile.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def create_profile(db: Session, user_id: uuid.UUID) -> GamificationProfile:
    profile = GamificationProfile(user_id=user_id, updated_at=datetime.now(UTC))
    db.add(profile)
    db.flush()
    return profile
