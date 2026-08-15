import uuid

from sqlalchemy.orm import Session

from app.domain.mastery import MasteryInputs, compute_mastery_score
from app.models.learning import Mastery
from app.repositories import mastery_repository, review_repository, study_repository


def recompute_mastery(db: Session, *, user_id: uuid.UUID, competency_id: uuid.UUID) -> Mastery:
    """Recompute and persist the mastery score for one (user, competency)
    pair from current activity data. Call this after any event that could
    move the needle: a study session, a challenge submission, a review."""
    total_minutes = study_repository.total_study_minutes_for_competency(db, user_id, competency_id)
    challenges_total = study_repository.count_challenges_for_competency(db, competency_id)
    challenges_passed = study_repository.count_challenges_passed_for_competency(
        db, user_id, competency_id
    )
    review = review_repository.get_review(db, user_id, competency_id)

    score = compute_mastery_score(
        MasteryInputs(
            total_study_minutes=total_minutes,
            challenges_total=challenges_total,
            challenges_passed=challenges_passed,
            last_recall_quality=review.last_recall_quality if review else None,
        )
    )

    return mastery_repository.upsert_mastery(
        db, user_id=user_id, competency_id=competency_id, score=score
    )
