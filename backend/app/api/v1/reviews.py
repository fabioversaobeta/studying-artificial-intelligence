import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.learning import ReviewRead, ReviewRecallSubmit
from app.services import review_service

router = APIRouter(prefix="/reviews", tags=["learning"])


@router.get("/due", response_model=list[ReviewRead])
def list_due_reviews(current_user: CurrentUser, db: DbSession) -> list:
    return review_service.list_due_reviews(db, current_user.id)


@router.post("/{competency_id}/recall", response_model=ReviewRead)
def submit_recall(
    competency_id: uuid.UUID, payload: ReviewRecallSubmit, current_user: CurrentUser, db: DbSession
) -> ReviewRead:
    review = review_service.submit_recall(
        db, user_id=current_user.id, competency_id=competency_id, quality=payload.quality
    )
    return ReviewRead.model_validate(review)
