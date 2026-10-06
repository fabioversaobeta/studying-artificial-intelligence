"""Gamification domain: XP ledger, levels, streaks, achievements, quests.

XP measures *activity*. Mastery (see app.models.learning.Mastery) measures
*knowledge*. They are computed independently and must never be conflated
(see docs/DECISIONS.md).
"""

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


def _enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    return SAEnum(enum_cls, name=name, native_enum=False, validate_strings=True, length=32)


class XPSource(StrEnum):
    STUDY_SESSION = "study_session"
    CHALLENGE = "challenge"
    ASSESSMENT = "assessment"
    REVIEW = "review"
    PROJECT = "project"
    TEACHING = "teaching"
    ACHIEVEMENT = "achievement"
    QUEST = "quest"


class AchievementCriterion(StrEnum):
    FIRST_STUDY_SESSION = "first_study_session"
    STUDY_SESSIONS_COUNT = "study_sessions_count"
    STREAK_DAYS = "streak_days"
    COMPETENCY_MASTERED_COUNT = "competency_mastered_count"
    CHALLENGES_PASSED_COUNT = "challenges_passed_count"
    XP_MILESTONE = "xp_milestone"


class QuestCriterion(StrEnum):
    STUDY_SESSIONS_COUNT = "study_sessions_count"
    CHALLENGES_PASSED_COUNT = "challenges_passed_count"
    REVIEWS_COMPLETED_COUNT = "reviews_completed_count"
    XP_EARNED = "xp_earned"


class QuestPeriod(StrEnum):
    ONE_TIME = "one_time"
    WEEKLY = "weekly"


class GamificationProfile(UUIDPrimaryKeyMixin, Base):
    """One row per user; a cached read-model kept in sync by the gamification
    service whenever XP is awarded (see app.services.gamification_service).
    """

    __tablename__ = "gamification_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship()


class XPAward(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "xp_awards"
    # "XP earned since X" sums and newest-first ledger reads per user.
    __table_args__ = (Index("ix_xp_awards_user_created_at", "user_id", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[XPSource] = mapped_column(_enum(XPSource, "xp_source"), nullable=False)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="xp_awards")


class Achievement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "achievements"

    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    criteria_type: Mapped[AchievementCriterion] = mapped_column(
        _enum(AchievementCriterion, "achievement_criterion"), nullable=False
    )
    criteria_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    xp_reward: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user_achievements: Mapped[list["UserAchievement"]] = relationship(
        back_populates="achievement", cascade="all, delete-orphan"
    )


class UserAchievement(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    achievement_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False
    )
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship()
    achievement: Mapped["Achievement"] = relationship(back_populates="user_achievements")


class Quest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "quests"

    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    criteria_type: Mapped[QuestCriterion] = mapped_column(
        _enum(QuestCriterion, "quest_criterion"), nullable=False
    )
    criteria_value: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[QuestPeriod] = mapped_column(_enum(QuestPeriod, "quest_period"), nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    completions: Mapped[list["QuestCompletion"]] = relationship(
        back_populates="quest", cascade="all, delete-orphan"
    )


class QuestCompletion(UUIDPrimaryKeyMixin, Base):
    """Records that a user completed a quest for a given period.

    `period_key` is ``"one_time"`` for ``ONE_TIME`` quests, or an ISO week
    string (e.g. ``"2026-W33"``) for ``WEEKLY`` quests, which lets the same
    quest be completed again each week without extra bookkeeping tables.
    """

    __tablename__ = "quest_completions"
    __table_args__ = (
        UniqueConstraint("user_id", "quest_id", "period_key", name="uq_quest_completion_period"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quest_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("quests.id", ondelete="CASCADE"), nullable=False
    )
    period_key: Mapped[str] = mapped_column(String(20), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship()
    quest: Mapped["Quest"] = relationship(back_populates="completions")
