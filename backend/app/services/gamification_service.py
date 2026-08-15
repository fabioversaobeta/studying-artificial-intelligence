"""Orchestrates XP awarding, leveling, streaks, and achievement unlocking.

This is the only place in the codebase allowed to mutate a
GamificationProfile — every other service that wants to grant XP (study
sessions, challenges, reviews, ...) must go through `award_xp`.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.domain.leveling import compute_level
from app.models.gamification import AchievementCriterion, GamificationProfile, XPSource
from app.repositories import gamification_repository


def _update_streak(profile: GamificationProfile, activity_date: date) -> None:
    last = profile.last_activity_date
    if last == activity_date:
        return  # already logged activity today; streak unchanged

    if last == activity_date - timedelta(days=1):
        profile.current_streak_days += 1
    else:
        profile.current_streak_days = 1

    profile.longest_streak_days = max(profile.longest_streak_days, profile.current_streak_days)
    profile.last_activity_date = activity_date


def award_xp(
    db: Session,
    *,
    user_id: uuid.UUID,
    amount: int,
    source: XPSource,
    reference_id: uuid.UUID | None = None,
    description: str | None = None,
    counts_for_streak: bool = True,
) -> GamificationProfile:
    if amount <= 0:
        raise ValueError("XP amount must be positive")

    gamification_repository.add_xp_award(
        db,
        user_id=user_id,
        amount=amount,
        source=source.value,
        reference_id=reference_id,
        description=description,
    )

    profile = gamification_repository.get_profile_for_update(db, user_id)
    if profile is None:
        profile = gamification_repository.create_profile(db, user_id)

    profile.total_xp += amount
    profile.level = compute_level(profile.total_xp)
    if counts_for_streak:
        _update_streak(profile, datetime.now(UTC).date())
    profile.updated_at = datetime.now(UTC)

    db.flush()
    check_and_award_achievements(db, user_id)
    db.flush()
    return profile


def check_and_award_achievements(db: Session, user_id: uuid.UUID) -> list[str]:
    """Evaluate every achievement not yet earned; award the ones whose
    criteria are now met. Returns the codes of newly earned achievements."""
    earned_codes = gamification_repository.get_earned_achievement_codes(db, user_id)
    newly_earned: list[str] = []

    for achievement in gamification_repository.list_achievements(db):
        if achievement.code in earned_codes:
            continue

        if _achievement_criteria_met(
            db, user_id, achievement.criteria_type, achievement.criteria_value
        ):
            gamification_repository.award_achievement(
                db, user_id=user_id, achievement_id=achievement.id
            )
            newly_earned.append(achievement.code)
            if achievement.xp_reward > 0:
                award_xp(
                    db,
                    user_id=user_id,
                    amount=achievement.xp_reward,
                    source=XPSource.ACHIEVEMENT,
                    reference_id=achievement.id,
                    description=f"Achievement unlocked: {achievement.name}",
                    counts_for_streak=False,
                )

    return newly_earned


def _achievement_criteria_met(
    db: Session, user_id: uuid.UUID, criterion: AchievementCriterion, value: int | None
) -> bool:
    match criterion:
        case AchievementCriterion.FIRST_STUDY_SESSION:
            return gamification_repository.count_study_sessions(db, user_id) >= 1
        case AchievementCriterion.STUDY_SESSIONS_COUNT:
            return gamification_repository.count_study_sessions(db, user_id) >= (value or 0)
        case AchievementCriterion.STREAK_DAYS:
            profile = gamification_repository.get_profile(db, user_id)
            return profile is not None and profile.longest_streak_days >= (value or 0)
        case AchievementCriterion.COMPETENCY_MASTERED_COUNT:
            return gamification_repository.count_mastered_competencies(db, user_id) >= (value or 0)
        case AchievementCriterion.CHALLENGES_PASSED_COUNT:
            return gamification_repository.count_passed_challenges(db, user_id) >= (value or 0)
        case AchievementCriterion.XP_MILESTONE:
            profile = gamification_repository.get_profile(db, user_id)
            return profile is not None and profile.total_xp >= (value or 0)
    return False


def list_achievements_with_progress(db: Session, user_id: uuid.UUID) -> list[dict]:
    earned_by_code = gamification_repository.get_earned_achievements_by_code(db, user_id)
    achievements = gamification_repository.list_achievements(db)
    return [
        {
            "achievement": a,
            "earned": a.code in earned_by_code,
            "earned_at": earned_by_code.get(a.code),
        }
        for a in achievements
    ]


def get_or_create_profile(db: Session, user_id: uuid.UUID) -> GamificationProfile:
    profile = gamification_repository.get_profile(db, user_id)
    if profile is None:
        profile = gamification_repository.create_profile(db, user_id)
        db.commit()
    return profile
