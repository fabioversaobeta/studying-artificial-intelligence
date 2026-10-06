import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.learning import Competency, Review, Subject


def get_review(db: Session, user_id: uuid.UUID, competency_id: uuid.UUID) -> Review | None:
    stmt = select(Review).where(Review.user_id == user_id, Review.competency_id == competency_id)
    return db.execute(stmt).scalar_one_or_none()


def list_due_reviews(
    db: Session,
    user_id: uuid.UUID,
    *,
    as_of: datetime,
    limit: int | None = None,
    offset: int = 0,
) -> list[Review]:
    stmt = (
        select(Review)
        .where(Review.user_id == user_id, Review.due_at <= as_of)
        .order_by(Review.due_at, Review.id)
        .offset(offset)
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())


def list_due_reviews_with_context(
    db: Session, user_id: uuid.UUID, *, as_of: datetime, limit: int, offset: int
) -> list[tuple[Review, str, uuid.UUID, str]]:
    """Due reviews plus competency name and subject id/name in ONE joined query."""
    stmt = (
        select(Review, Competency.name, Subject.id, Subject.name)
        .join(Competency, Competency.id == Review.competency_id)
        .join(Subject, Subject.id == Competency.subject_id)
        .where(Review.user_id == user_id, Review.due_at <= as_of)
        .order_by(Review.due_at, Review.id)
        .offset(offset)
        .limit(limit)
    )
    return [(r, cn, sid, sn) for r, cn, sid, sn in db.execute(stmt).all()]


def count_due_reviews(db: Session, user_id: uuid.UUID, *, as_of: datetime) -> int:
    stmt = (
        select(func.count())
        .select_from(Review)
        .where(Review.user_id == user_id, Review.due_at <= as_of)
    )
    return int(db.execute(stmt).scalar_one())


def ensure_review_scheduled(
    db: Session, *, user_id: uuid.UUID, competency_id: uuid.UUID, due_at: datetime
) -> Review:
    """Create a Review row the first time a competency is studied, so it
    enters the spaced-repetition queue. Leaves an existing schedule alone."""
    review = get_review(db, user_id, competency_id)
    if review is not None:
        return review

    review = Review(user_id=user_id, competency_id=competency_id, due_at=due_at)
    db.add(review)
    db.flush()
    return review


def save_review(db: Session, review: Review) -> Review:
    db.add(review)
    db.flush()
    return review
