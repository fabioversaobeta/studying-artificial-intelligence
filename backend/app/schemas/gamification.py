import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.gamification import AchievementCriterion, QuestCriterion, QuestPeriod


class GamificationProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_xp: int
    level: int
    current_streak_days: int
    longest_streak_days: int
    last_activity_date: date | None


class AchievementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str
    icon: str | None
    criteria_type: AchievementCriterion
    criteria_value: int | None
    xp_reward: int


class AchievementProgress(BaseModel):
    achievement: AchievementRead
    earned: bool
    earned_at: datetime | None = None


class QuestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: str
    description: str
    criteria_type: QuestCriterion
    criteria_value: int
    period: QuestPeriod
    xp_reward: int


class QuestProgress(BaseModel):
    quest: QuestRead
    progress: int
    target: int
    completed: bool
    period_key: str
