"""Quests: progress is computed fresh from the user's activity, and completion
is recorded on events, not on reads. `gamification_service.settle_rewards`
calls `complete_due_quests` whenever activity is registered (XP awarded, study
session logged); `list_quests_with_progress` (GET) is strictly read-only.
This module never awards XP itself — the caller pays the reward.
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.gamification import Quest, QuestCriterion, QuestPeriod
from app.repositories import gamification_repository, quest_repository


def _period_key(quest: Quest, now: datetime) -> str:
    if quest.period == QuestPeriod.ONE_TIME:
        return "one_time"
    iso = now.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _period_start(quest: Quest, now: datetime) -> datetime:
    if quest.period == QuestPeriod.ONE_TIME:
        return datetime.min.replace(tzinfo=UTC)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_of_day - timedelta(days=start_of_day.isoweekday() - 1)


def _current_progress(db: Session, user_id: uuid.UUID, quest: Quest, since: datetime) -> int:
    match quest.criteria_type:
        case QuestCriterion.STUDY_SESSIONS_COUNT:
            return quest_repository.count_study_sessions_since(db, user_id, since)
        case QuestCriterion.CHALLENGES_PASSED_COUNT:
            return quest_repository.count_challenges_passed_since(db, user_id, since)
        case QuestCriterion.ASSESSMENTS_PASSED_COUNT:
            return quest_repository.count_assessments_passed_since(db, user_id, since)
        case QuestCriterion.REVIEWS_COMPLETED_COUNT:
            return quest_repository.count_reviews_completed_since(db, user_id, since)
        case QuestCriterion.XP_EARNED:
            return quest_repository.sum_xp_earned_since(db, user_id, since)
    return 0


def complete_due_quests(db: Session, user_id: uuid.UUID) -> list[Quest]:
    """Persist a completion for every active quest whose target is newly met in
    its current period. Returns those quests so the caller can pay the XP."""
    now = datetime.now(UTC)
    completed: list[Quest] = []
    for quest in gamification_repository.list_active_quests(db):
        period_key = _period_key(quest, now)
        if (
            gamification_repository.get_quest_completion(
                db, user_id=user_id, quest_id=quest.id, period_key=period_key
            )
            is not None
        ):
            continue
        progress = _current_progress(db, user_id, quest, _period_start(quest, now))
        if progress >= quest.criteria_value:
            gamification_repository.complete_quest(
                db, user_id=user_id, quest_id=quest.id, period_key=period_key
            )
            completed.append(quest)
    return completed


def list_quests_with_progress(db: Session, user_id: uuid.UUID) -> list[dict]:
    """Read-only: reports progress and completion, never mutates."""
    now = datetime.now(UTC)
    results = []

    for quest in gamification_repository.list_active_quests(db):
        period_key = _period_key(quest, now)
        completed = (
            gamification_repository.get_quest_completion(
                db, user_id=user_id, quest_id=quest.id, period_key=period_key
            )
            is not None
        )
        progress = _current_progress(db, user_id, quest, _period_start(quest, now))
        results.append(
            {
                "quest": quest,
                "progress": min(progress, quest.criteria_value),
                "target": quest.criteria_value,
                "completed": completed,
                "period_key": period_key,
            }
        )

    return results
