from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.domain.recommendations import DEFAULT_LIMIT, MAX_LIMIT
from app.schemas.recommendation import TodayRecommendationsRead
from app.services import recommendation_service

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations/today", response_model=TodayRecommendationsRead)
def get_today_recommendations(
    current_user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
) -> dict:
    items = recommendation_service.get_today(
        db, current_user.id, current_user.preferred_language, limit=limit
    )
    return {"items": items}
