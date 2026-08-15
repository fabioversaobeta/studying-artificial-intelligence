import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.learning import ChallengeRead, ChallengeSubmissionCreate, ChallengeSubmissionRead
from app.services import challenge_service

router = APIRouter(tags=["learning"])


@router.get("/competencies/{competency_id}/challenges", response_model=list[ChallengeRead])
def list_challenges(competency_id: uuid.UUID, db: DbSession) -> list:
    return challenge_service.list_challenges_for_competency(db, competency_id)


@router.post(
    "/challenges/{challenge_id}/submissions",
    response_model=ChallengeSubmissionRead,
    status_code=status.HTTP_201_CREATED,
)
def submit_challenge(
    challenge_id: uuid.UUID,
    payload: ChallengeSubmissionCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> ChallengeSubmissionRead:
    submission = challenge_service.submit_challenge(
        db,
        user_id=current_user.id,
        challenge_id=challenge_id,
        status=payload.status,
        notes=payload.notes,
    )
    return ChallengeSubmissionRead.model_validate(submission)
