import uuid
from collections.abc import Collection
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


def get_scores_by_competency(
    db: Session, user_id: uuid.UUID, competency_ids: Collection[uuid.UUID]
) -> dict[uuid.UUID, float]:
    """Mastery score per competency for one user, in a single query. Competencies
    without a mastery record are absent from the result."""
    if not competency_ids:
        return {}
    stmt = select(Mastery.competency_id, Mastery.score).where(
        Mastery.user_id == user_id, Mastery.competency_id.in_(competency_ids)
    )
    return {competency_id: score for competency_id, score in db.execute(stmt).all()}
