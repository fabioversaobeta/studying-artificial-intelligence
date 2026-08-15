from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.gamification import AchievementProgress, GamificationProfileRead, QuestProgress
from app.services import gamification_service, quest_service

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/profile", response_model=GamificationProfileRead)
def get_profile(current_user: CurrentUser, db: DbSession) -> GamificationProfileRead:
    profile = gamification_service.get_or_create_profile(db, current_user.id)
    return GamificationProfileRead.model_validate(profile)


@router.get("/achievements", response_model=list[AchievementProgress])
def list_achievements(current_user: CurrentUser, db: DbSession) -> list:
    return gamification_service.list_achievements_with_progress(db, current_user.id)


@router.get("/quests", response_model=list[QuestProgress])
def list_quests(current_user: CurrentUser, db: DbSession) -> list:
    return quest_service.list_quests_with_progress(db, current_user.id)
