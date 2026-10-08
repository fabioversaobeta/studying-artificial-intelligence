import uuid
from collections.abc import Collection
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


def get_study_session(db: Session, session_id: uuid.UUID) -> StudySession | None:
    return db.get(StudySession, session_id)


def delete_study_session(db: Session, session: StudySession) -> None:
    db.delete(session)
    db.flush()


def list_study_sessions(
    db: Session, user_id: uuid.UUID, *, limit: int = 50, offset: int = 0
) -> list[StudySession]:
    stmt = (
        select(StudySession)
        .where(StudySession.user_id == user_id)
        .order_by(StudySession.occurred_at.desc(), StudySession.id)
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


def count_study_sessions(db: Session, user_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(StudySession).where(StudySession.user_id == user_id)
    return int(db.execute(stmt).scalar_one())


def total_study_minutes_for_competency(
    db: Session, user_id: uuid.UUID, competency_id: uuid.UUID
) -> int:
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
    stmt = (
        select(func.count()).select_from(Challenge).where(Challenge.competency_id == competency_id)
    )
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


def total_study_minutes_by_competency(
    db: Session, user_id: uuid.UUID, competency_ids: Collection[uuid.UUID]
) -> dict[uuid.UUID, int]:
    """Total minutes studied per competency for one user, in a single GROUP BY query.
    Competencies with no sessions are absent from the result."""
    if not competency_ids:
        return {}
    stmt = (
        select(StudySession.competency_id, func.sum(StudySession.duration_minutes))
        .where(StudySession.user_id == user_id, StudySession.competency_id.in_(competency_ids))
        .group_by(StudySession.competency_id)
    )
    return {
        competency_id: int(total)
        for competency_id, total in db.execute(stmt).all()
        if competency_id
        is not None  # sessions may have no competency; they have no per-competency total
    }
