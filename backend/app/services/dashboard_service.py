import uuid

from sqlalchemy.orm import Session

from app.domain.leveling import xp_to_next_level
from app.models.learning import GoalStatus
from app.repositories import goal_repository, mastery_repository, study_repository
from app.services import gamification_service, review_service


def get_dashboard(db: Session, user_id: uuid.UUID) -> dict:
    profile = gamification_service.get_or_create_profile(db, user_id)
    active_goals = [
        g for g in goal_repository.list_goals_for_user(db, user_id) if g.status == GoalStatus.ACTIVE
    ]
    due_reviews = review_service.list_due_reviews(db, user_id)
    mastery_records = mastery_repository.list_mastery_for_user(db, user_id)
    weakest = sorted(mastery_records, key=lambda m: m.score)[:5]
    recent_sessions = study_repository.list_study_sessions(db, user_id)[:5]

    return {
        "level": profile.level,
        "total_xp": profile.total_xp,
        "xp_to_next_level": xp_to_next_level(profile.total_xp),
        "current_streak_days": profile.current_streak_days,
        "longest_streak_days": profile.longest_streak_days,
        "active_goals": active_goals,
        "due_review_count": len(due_reviews),
        "weakest_competencies": weakest,
        "recent_study_sessions": recent_sessions,
    }
