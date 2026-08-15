import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.learning import (
    Challenge,
    ChallengeSubmission,
    ChallengeSubmissionStatus,
    StudySession,
)


def create_study_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    competency_id: uuid.UUID | None,
    subject_id: uuid.UUID | None,
    duration_minutes: int,
    notes: str | None,
    occurred_at: datetime,
) -> StudySession:
    session = StudySession(
        user_id=user_id,
        competency_id=competency_id,
        subject_id=subject_id,
        duration_minutes=duration_minutes,
        notes=notes,
        occurred_at=occurred_at,
        created_at=datetime.now(UTC),
    )
    db.add(session)
    db.flush()
    return session


def list_study_sessions(
    db: Session, user_id: uuid.UUID, *, limit: int = 50
) -> list[StudySession]:
    stmt = (
        select(StudySession)
        .where(StudySession.user_id == user_id)
        .order_by(StudySession.occurred_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def total_study_minutes_for_competency(db: Session, user_id: uuid.UUID, competency_id: uuid.UUID) -> int:
    stmt = select(func.coalesce(func.sum(StudySession.duration_minutes), 0)).where(
        StudySession.user_id == user_id, StudySession.competency_id == competency_id
    )
    return int(db.execute(stmt).scalar_one())


def get_challenge(db: Session, challenge_id: uuid.UUID) -> Challenge | None:
    return db.get(Challenge, challenge_id)


def list_challenges_by_competency(db: Session, competency_id: uuid.UUID) -> list[Challenge]:
    stmt = select(Challenge).where(Challenge.competency_id == competency_id)
    return list(db.execute(stmt).scalars().all())


def create_challenge_submission(
    db: Session,
    *,
    user_id: uuid.UUID,
    challenge_id: uuid.UUID,
    status: ChallengeSubmissionStatus,
    notes: str | None,
    xp_awarded: int,
) -> ChallengeSubmission:
    submission = ChallengeSubmission(
        user_id=user_id,
        challenge_id=challenge_id,
        status=status,
        notes=notes,
        submitted_at=datetime.now(UTC),
        xp_awarded=xp_awarded,
    )
    db.add(submission)
    db.flush()
    return submission


def has_passed_challenge_before(db: Session, user_id: uuid.UUID, challenge_id: uuid.UUID) -> bool:
    stmt = select(ChallengeSubmission).where(
        ChallengeSubmission.user_id == user_id,
        ChallengeSubmission.challenge_id == challenge_id,
        ChallengeSubmission.status == ChallengeSubmissionStatus.PASSED,
    )
    return db.execute(stmt).first() is not None


def count_challenges_for_competency(db: Session, competency_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(Challenge).where(Challenge.competency_id == competency_id)
    return int(db.execute(stmt).scalar_one())


def count_challenges_passed_for_competency(
    db: Session, user_id: uuid.UUID, competency_id: uuid.UUID
) -> int:
    stmt = (
        select(func.count(func.distinct(ChallengeSubmission.challenge_id)))
        .select_from(ChallengeSubmission)
        .join(Challenge, Challenge.id == ChallengeSubmission.challenge_id)
        .where(
            ChallengeSubmission.user_id == user_id,
            Challenge.competency_id == competency_id,
            ChallengeSubmission.status == ChallengeSubmissionStatus.PASSED,
        )
    )
    return int(db.execute(stmt).scalar_one())
