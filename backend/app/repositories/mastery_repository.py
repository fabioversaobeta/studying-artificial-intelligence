import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.learning import Mastery


def get_mastery(db: Session, user_id: uuid.UUID, competency_id: uuid.UUID) -> Mastery | None:
    stmt = select(Mastery).where(Mastery.user_id == user_id, Mastery.competency_id == competency_id)
    return db.execute(stmt).scalar_one_or_none()


def list_mastery_for_user(db: Session, user_id: uuid.UUID) -> list[Mastery]:
    stmt = select(Mastery).where(Mastery.user_id == user_id)
    return list(db.execute(stmt).scalars().all())


def upsert_mastery(
    db: Session, *, user_id: uuid.UUID, competency_id: uuid.UUID, score: float
) -> Mastery:
    record = get_mastery(db, user_id, competency_id)
    if record is None:
        record = Mastery(
            user_id=user_id,
            competency_id=competency_id,
            score=score,
            updated_at=datetime.now(UTC),
        )
        db.add(record)
    else:
        record.score = score
        record.updated_at = datetime.now(UTC)
    db.flush()
    return record
