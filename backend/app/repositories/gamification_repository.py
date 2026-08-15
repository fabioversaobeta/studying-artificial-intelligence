import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.gamification import (
    Achievement,
    GamificationProfile,
    Quest,
    QuestCompletion,
    UserAchievement,
    XPAward,
)


def get_profile(db: Session, user_id: uuid.UUID) -> GamificationProfile | None:
    stmt = select(GamificationProfile).where(GamificationProfile.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def get_profile_for_update(db: Session, user_id: uuid.UUID) -> GamificationProfile | None:
    """Row-locked read, used before mutating XP/streak to avoid lost updates
    when two requests award XP for the same user concurrently."""
    stmt = (
        select(GamificationProfile).where(GamificationProfile.user_id == user_id).with_for_update()
    )
    return db.execute(stmt).scalar_one_or_none()


def create_profile(db: Session, user_id: uuid.UUID) -> GamificationProfile:
    profile = GamificationProfile(user_id=user_id, updated_at=datetime.now(UTC))
    db.add(profile)
    db.flush()
    return profile


def add_xp_award(
    db: Session,
    *,
    user_id: uuid.UUID,
    amount: int,
    source: str,
    reference_id: uuid.UUID | None,
    description: str | None,
) -> XPAward:
    award = XPAward(
        user_id=user_id,
        amount=amount,
        source=source,
        reference_id=reference_id,
        description=description,
        created_at=datetime.now(UTC),
    )
    db.add(award)
    db.flush()
    return award


def list_achievements(db: Session) -> list[Achievement]:
    return list(db.execute(select(Achievement)).scalars().all())


def get_earned_achievement_codes(db: Session, user_id: uuid.UUID) -> set[str]:
    stmt = (
        select(Achievement.code)
        .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
        .where(UserAchievement.user_id == user_id)
    )
    return set(db.execute(stmt).scalars().all())


def get_earned_achievements_by_code(
    db: Session, user_id: uuid.UUID
) -> dict[str, datetime]:
    stmt = (
        select(Achievement.code, UserAchievement.earned_at)
        .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
        .where(UserAchievement.user_id == user_id)
    )
    return {code: earned_at for code, earned_at in db.execute(stmt).all()}


def award_achievement(db: Session, *, user_id: uuid.UUID, achievement_id: uuid.UUID) -> UserAchievement:
    record = UserAchievement(
        user_id=user_id, achievement_id=achievement_id, earned_at=datetime.now(UTC)
    )
    db.add(record)
    db.flush()
    return record


def count_study_sessions(db: Session, user_id: uuid.UUID) -> int:
    from app.models.learning import StudySession

    stmt = select(StudySession).where(StudySession.user_id == user_id)
    return len(db.execute(stmt).scalars().all())


def count_passed_challenges(db: Session, user_id: uuid.UUID) -> int:
    from app.models.learning import ChallengeSubmission, ChallengeSubmissionStatus

    stmt = select(ChallengeSubmission.challenge_id).where(
        ChallengeSubmission.user_id == user_id,
        ChallengeSubmission.status == ChallengeSubmissionStatus.PASSED,
    )
    return len(set(db.execute(stmt).scalars().all()))


def count_mastered_competencies(db: Session, user_id: uuid.UUID, threshold: float = 80.0) -> int:
    from app.models.learning import Mastery

    stmt = select(Mastery).where(Mastery.user_id == user_id, Mastery.score >= threshold)
    return len(db.execute(stmt).scalars().all())


def list_active_quests(db: Session) -> list[Quest]:
    stmt = select(Quest).where(Quest.is_active.is_(True))
    return list(db.execute(stmt).scalars().all())


def get_quest_completion(
    db: Session, *, user_id: uuid.UUID, quest_id: uuid.UUID, period_key: str
) -> QuestCompletion | None:
    stmt = select(QuestCompletion).where(
        QuestCompletion.user_id == user_id,
        QuestCompletion.quest_id == quest_id,
        QuestCompletion.period_key == period_key,
    )
    return db.execute(stmt).scalar_one_or_none()


def complete_quest(
    db: Session, *, user_id: uuid.UUID, quest_id: uuid.UUID, period_key: str
) -> QuestCompletion:
    completion = QuestCompletion(
        user_id=user_id, quest_id=quest_id, period_key=period_key, completed_at=datetime.now(UTC)
    )
    db.add(completion)
    db.flush()
    return completion
