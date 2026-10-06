import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.spaced_repetition import ReviewState, next_review_state
from app.models.gamification import XPSource
from app.models.learning import Review
from app.repositories import review_repository
from app.services import gamification_service, mastery_service

REVIEW_XP_REWARD = 15


def schedule_initial_review(db: Session, *, user_id: uuid.UUID, competency_id: uuid.UUID) -> Review:
    """First-touch scheduling: a competency enters the spaced-repetition
    queue the first time it's studied, due the next day."""
    return review_repository.ensure_review_scheduled(
        db,
        user_id=user_id,
        competency_id=competency_id,
        due_at=datetime.now(UTC) + timedelta(days=1),
    )


def list_due_reviews(db: Session, user_id: uuid.UUID) -> list[Review]:
    return review_repository.list_due_reviews(db, user_id, as_of=datetime.now(UTC))


def list_due_reviews_page(
    db: Session, user_id: uuid.UUID, *, limit: int, offset: int
) -> tuple[list[Review], int]:
    now = datetime.now(UTC)
    items = review_repository.list_due_reviews(db, user_id, as_of=now, limit=limit, offset=offset)
    return items, review_repository.count_due_reviews(db, user_id, as_of=now)


def submit_recall(
    db: Session, *, user_id: uuid.UUID, competency_id: uuid.UUID, quality: int
) -> Review:
    review = review_repository.get_review(db, user_id, competency_id)
    if review is None:
        raise NotFoundError("No review is scheduled for this competency yet")

    new_state = next_review_state(
        ReviewState(
            interval_days=review.interval_days,
            ease_factor=review.ease_factor,
            repetitions=review.repetitions,
        ),
        quality,
    )

    now = datetime.now(UTC)
    review.interval_days = new_state.interval_days
    review.ease_factor = new_state.ease_factor
    review.repetitions = new_state.repetitions
    review.last_recall_quality = quality
    review.last_reviewed_at = now
    review.due_at = now + timedelta(days=new_state.interval_days)
    review_repository.save_review(db, review)

    mastery_service.recompute_mastery(db, user_id=user_id, competency_id=competency_id)
    gamification_service.award_xp(
        db,
        user_id=user_id,
        amount=REVIEW_XP_REWARD,
        source=XPSource.REVIEW,
        reference_id=review.id,
        description="Spaced-repetition review completed",
    )

    db.commit()
    db.refresh(review)
    return review
