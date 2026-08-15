"""Quests are evaluated and auto-completed on read: whenever a user's quest
list is requested, progress is computed fresh from their activity and any
quest that has newly crossed its target is completed and its XP awarded in
the same call. This avoids a separate "claim" endpoint/UI affordance for v1
while still being real, persisted completion (not a cosmetic progress bar).
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.gamification import Quest, QuestCriterion, QuestPeriod, XPSource
from app.repositories import gamification_repository, quest_repository
from app.services import gamification_service


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
        case QuestCriterion.REVIEWS_COMPLETED_COUNT:
            return quest_repository.count_reviews_completed_since(db, user_id, since)
        case QuestCriterion.XP_EARNED:
            return quest_repository.sum_xp_earned_since(db, user_id, since)
    return 0


def list_quests_with_progress(db: Session, user_id: uuid.UUID) -> list[dict]:
    now = datetime.now(UTC)
    results = []

    for quest in gamification_repository.list_active_quests(db):
        period_key = _period_key(quest, now)
        already_completed = (
            gamification_repository.get_quest_completion(
                db, user_id=user_id, quest_id=quest.id, period_key=period_key
            )
            is not None
        )

        progress = _current_progress(db, user_id, quest, _period_start(quest, now))
        target_met = progress >= quest.criteria_value

        if target_met and not already_completed:
            gamification_repository.complete_quest(
                db, user_id=user_id, quest_id=quest.id, period_key=period_key
            )
            gamification_service.award_xp(
                db,
                user_id=user_id,
                amount=quest.xp_reward,
                source=XPSource.QUEST,
                reference_id=quest.id,
                description=f"Quest completed: {quest.title}",
                counts_for_streak=False,
            )
            already_completed = True

        results.append(
            {
                "quest": quest,
                "progress": min(progress, quest.criteria_value),
                "target": quest.criteria_value,
                "completed": already_completed,
                "period_key": period_key,
            }
        )

    db.commit()
    return results
