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
from app.services import quest_service


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


def _apply_xp(
    db: Session,
    *,
    user_id: uuid.UUID,
    amount: int,
    source: XPSource,
    reference_id: uuid.UUID | None,
    description: str | None,
    counts_for_streak: bool,
) -> GamificationProfile:
    """Ledger entry + profile mutation. Never evaluates rewards (no recursion)."""
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
    return profile


def record_activity(db: Session, user_id: uuid.UUID) -> GamificationProfile:
    """Count today as an active day for the streak without awarding XP.

    The streak measures consistency ("you showed up"), XP measures effort, and
    they are decoupled on purpose: a study session too short to earn XP (under
    10 minutes) must still keep the streak alive (docs/DECISIONS.md). Idempotent
    within a day. Does not evaluate rewards; call `settle_rewards` afterwards.
    """
    profile = gamification_repository.get_profile_for_update(db, user_id)
    if profile is None:
        profile = gamification_repository.create_profile(db, user_id)
    _update_streak(profile, datetime.now(UTC).date())
    profile.updated_at = datetime.now(UTC)
    db.flush()
    return profile


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
    profile = _apply_xp(
        db,
        user_id=user_id,
        amount=amount,
        source=source,
        reference_id=reference_id,
        description=description,
        counts_for_streak=counts_for_streak,
    )
    settle_rewards(db, user_id)
    return profile


def settle_rewards(db: Session, user_id: uuid.UUID) -> list[str]:
    """Event-driven reward evaluation: unlock every achievement and complete
    every quest whose criteria are now met, pay their XP rewards, and repeat
    until nothing new unlocks (a reward can itself satisfy another criterion).

    Idempotent: earned achievements / completed quests are re-read on every
    pass and the rewards are paid without re-entering this function, so there
    is no recursion and no stale snapshot. Returns the newly earned
    achievement codes. Call it after any activity that may advance progress,
    including activity that awards no XP.
    """
    newly_earned: list[str] = []

    while True:
        rewards: list[tuple[int, XPSource, uuid.UUID, str]] = []

        earned_codes = gamification_repository.get_earned_achievement_codes(db, user_id)
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
                    rewards.append(
                        (
                            achievement.xp_reward,
                            XPSource.ACHIEVEMENT,
                            achievement.id,
                            f"Achievement unlocked: {achievement.name}",
                        )
                    )

        for quest in quest_service.complete_due_quests(db, user_id):
            if quest.xp_reward > 0:
                rewards.append(
                    (
                        quest.xp_reward,
                        XPSource.QUEST,
                        quest.id,
                        f"Quest completed: {quest.title}",
                    )
                )

        for amount, source, reference_id, description in rewards:
            _apply_xp(
                db,
                user_id=user_id,
                amount=amount,
                source=source,
                reference_id=reference_id,
                description=description,
                counts_for_streak=False,
            )

        if not rewards:
            # Nothing paid XP, so no criterion can have changed after this pass
            # (a reward-less unlock was already recorded above).
            break

    db.flush()
    return newly_earned


def check_and_award_achievements(db: Session, user_id: uuid.UUID) -> list[str]:
    """Evaluate achievements (and quests); returns newly earned achievement codes."""
    return settle_rewards(db, user_id)


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
