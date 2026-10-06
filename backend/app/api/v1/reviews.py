import uuid

from fastapi import APIRouter, Response

from app.api.deps import CurrentUser, DbSession
from app.api.pagination import Pagination, set_total_count
from app.schemas.learning import ReviewRead, ReviewRecallSubmit
from app.services import review_service

router = APIRouter(prefix="/reviews", tags=["learning"])


@router.get("/due", response_model=list[ReviewRead])
def list_due_reviews(
    current_user: CurrentUser, db: DbSession, page: Pagination, response: Response
) -> list:
    items, total = review_service.list_due_reviews_page(
        db, current_user.id, limit=page.limit, offset=page.offset
    )
    set_total_count(response, total)
    return items


@router.post("/{competency_id}/recall", response_model=ReviewRead)
def submit_recall(
    competency_id: uuid.UUID, payload: ReviewRecallSubmit, current_user: CurrentUser, db: DbSession
) -> ReviewRead:
    review = review_service.submit_recall(
        db, user_id=current_user.id, competency_id=competency_id, quality=payload.quality
    )
    return ReviewRead.model_validate(review)
