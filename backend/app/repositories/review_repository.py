import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.learning import Review


def get_review(db: Session, user_id: uuid.UUID, competency_id: uuid.UUID) -> Review | None:
    stmt = select(Review).where(Review.user_id == user_id, Review.competency_id == competency_id)
    return db.execute(stmt).scalar_one_or_none()


def list_due_reviews(db: Session, user_id: uuid.UUID, *, as_of: datetime) -> list[Review]:
    stmt = (
        select(Review)
        .where(Review.user_id == user_id, Review.due_at <= as_of)
        .order_by(Review.due_at)
    )
    return list(db.execute(stmt).scalars().all())


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
