import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentAttempt, AttemptStatus
from app.models.gamification import XPAward
from app.models.learning import ChallengeSubmission, ChallengeSubmissionStatus, Review, StudySession


def count_study_sessions_since(db: Session, user_id: uuid.UUID, since: datetime) -> int:
    stmt = (
        select(func.count())
        .select_from(StudySession)
        .where(StudySession.user_id == user_id, StudySession.occurred_at >= since)
    )
    return int(db.execute(stmt).scalar_one())


def count_challenges_passed_since(db: Session, user_id: uuid.UUID, since: datetime) -> int:
    stmt = (
        select(func.count())
        .select_from(ChallengeSubmission)
        .where(
            ChallengeSubmission.user_id == user_id,
            ChallengeSubmission.status == ChallengeSubmissionStatus.PASSED,
            ChallengeSubmission.submitted_at >= since,
        )
    )
    return int(db.execute(stmt).scalar_one())


def count_assessments_passed_since(db: Session, user_id: uuid.UUID, since: datetime) -> int:
    """Passed attempts finished since `since` (repeating a quiz does not make
    the quest easier to farm: the quest completes once per period regardless)."""
    stmt = (
        select(func.count())
        .select_from(AssessmentAttempt)
        .where(
            AssessmentAttempt.user_id == user_id,
            AssessmentAttempt.status == AttemptStatus.COMPLETED,
            AssessmentAttempt.passed.is_(True),
            AssessmentAttempt.completed_at >= since,
        )
    )
    return int(db.execute(stmt).scalar_one())


def count_reviews_completed_since(db: Session, user_id: uuid.UUID, since: datetime) -> int:
    stmt = (
        select(func.count())
        .select_from(Review)
        .where(
            Review.user_id == user_id,
            Review.last_reviewed_at.isnot(None),
            Review.last_reviewed_at >= since,
        )
    )
    return int(db.execute(stmt).scalar_one())


def sum_xp_earned_since(db: Session, user_id: uuid.UUID, since: datetime) -> int:
    stmt = select(func.coalesce(func.sum(XPAward.amount), 0)).where(
        XPAward.user_id == user_id, XPAward.created_at >= since
    )
    return int(db.execute(stmt).scalar_one())
