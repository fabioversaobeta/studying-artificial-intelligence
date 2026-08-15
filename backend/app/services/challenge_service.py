"""Challenge submissions are self-assessed in v1: the learner marks their own
attempt as passed or failed, optionally with notes. Automated grading (e.g.
an AI-assisted reviewer) is a natural extension point — see docs/PENDING.md —
but self-assessment is an honest, working v1 rather than a fake "AI grading"
placeholder.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.gamification import XPSource
from app.models.learning import Challenge, ChallengeSubmission, ChallengeSubmissionStatus
from app.repositories import study_repository
from app.services import gamification_service, mastery_service


def list_challenges_for_competency(db: Session, competency_id: uuid.UUID) -> list[Challenge]:
    return study_repository.list_challenges_by_competency(db, competency_id)


def submit_challenge(
    db: Session,
    *,
    user_id: uuid.UUID,
    challenge_id: uuid.UUID,
    status: ChallengeSubmissionStatus,
    notes: str | None,
) -> ChallengeSubmission:
    challenge = study_repository.get_challenge(db, challenge_id)
    if challenge is None:
        raise NotFoundError("Challenge not found")

    xp_awarded = 0
    if (
        status == ChallengeSubmissionStatus.PASSED
        and not study_repository.has_passed_challenge_before(db, user_id, challenge_id)
    ):
        xp_awarded = challenge.xp_value

    submission = study_repository.create_challenge_submission(
        db,
        user_id=user_id,
        challenge_id=challenge_id,
        status=status,
        notes=notes,
        xp_awarded=xp_awarded,
    )

    mastery_service.recompute_mastery(db, user_id=user_id, competency_id=challenge.competency_id)

    if xp_awarded > 0:
        gamification_service.award_xp(
            db,
            user_id=user_id,
            amount=xp_awarded,
            source=XPSource.CHALLENGE,
            reference_id=submission.id,
            description=f"Challenge passed: {challenge.title}",
        )

    db.commit()
    db.refresh(submission)
    return submission
