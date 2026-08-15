from pydantic import BaseModel, ConfigDict

from app.schemas.learning import LearningGoalRead, MasteryRead, StudySessionRead


class DashboardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    level: int
    total_xp: int
    xp_to_next_level: int
    current_streak_days: int
    longest_streak_days: int
    active_goals: list[LearningGoalRead]
    due_review_count: int
    weakest_competencies: list[MasteryRead]
    recent_study_sessions: list[StudySessionRead]
