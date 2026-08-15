"""Core learning domain: goals, subjects, competencies, paths, study activity,
mastery, and spaced-repetition review state.

See docs/DOMAIN.md for the conceptual model and docs/DECISIONS.md for why
mastery/XP are kept as separate concepts.
"""

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
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


class GoalStatus(StrEnum):
    ACTIVE = "active"
    ACHIEVED = "achieved"
    ARCHIVED = "archived"


class DifficultyLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ResourceType(StrEnum):
    ARTICLE = "article"
    BOOK = "book"
    VIDEO = "video"
    DOCUMENTATION = "documentation"
    COURSE = "course"
    NOTES = "notes"


class ChallengeSubmissionStatus(StrEnum):
    SUBMITTED = "submitted"
    PASSED = "passed"
    FAILED = "failed"


class CompetencyState(StrEnum):
    """Computed (not persisted) per-user state of a competency in the skill tree."""

    LOCKED = "locked"
    AVAILABLE = "available"
    LEARNING = "learning"
    MASTERED = "mastered"


def _enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    """Store Python str-enums as portable VARCHAR + CHECK constraint (not a
    native Postgres enum type), so adding new values later is a simple
    Alembic column-level change instead of an `ALTER TYPE`."""
    return SAEnum(enum_cls, name=name, native_enum=False, validate_strings=True, length=32)


class LearningGoal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "learning_goals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[GoalStatus] = mapped_column(
        _enum(GoalStatus, "goal_status"), default=GoalStatus.ACTIVE, nullable=False
    )
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    user: Mapped["User"] = relationship(back_populates="learning_goals")


class Subject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    competencies: Mapped[list["Competency"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan", order_by="Competency.sort_order"
    )


class Competency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "competencies"
    __table_args__ = (UniqueConstraint("subject_id", "slug", name="uq_competency_subject_slug"),)

    subject_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        _enum(DifficultyLevel, "difficulty_level"), default=DifficultyLevel.BEGINNER, nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subject: Mapped["Subject"] = relationship(back_populates="competencies")
    resources: Mapped[list["LearningResource"]] = relationship(
        back_populates="competency", cascade="all, delete-orphan"
    )
    challenges: Mapped[list["Challenge"]] = relationship(
        back_populates="competency", cascade="all, delete-orphan"
    )

    prerequisites: Mapped[list["Competency"]] = relationship(
        secondary="competency_prerequisites",
        primaryjoin="Competency.id == CompetencyPrerequisite.competency_id",
        secondaryjoin="Competency.id == CompetencyPrerequisite.prerequisite_id",
        viewonly=True,
    )


class CompetencyPrerequisite(Base):
    """Directed edge in the skill tree: `competency_id` requires `prerequisite_id`."""

    __tablename__ = "competency_prerequisites"
    __table_args__ = (
        CheckConstraint("competency_id != prerequisite_id", name="ck_prerequisite_not_self"),
    )

    competency_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True
    )
    prerequisite_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), primary_key=True
    )


class LearningPath(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "learning_paths"

    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    items: Mapped[list["LearningPathItem"]] = relationship(
        back_populates="learning_path",
        cascade="all, delete-orphan",
        order_by="LearningPathItem.sort_order",
    )


class LearningPathItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learning_path_items"
    __table_args__ = (
        UniqueConstraint("learning_path_id", "competency_id", name="uq_path_competency"),
    )

    learning_path_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    learning_path: Mapped["LearningPath"] = relationship(back_populates="items")
    competency: Mapped["Competency"] = relationship()


class LearningResource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "learning_resources"

    competency_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[ResourceType] = mapped_column(_enum(ResourceType, "resource_type"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    competency: Mapped["Competency"] = relationship(back_populates="resources")


class StudySession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "study_sessions"
    __table_args__ = (CheckConstraint("duration_minutes > 0", name="ck_duration_positive"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    competency_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id", ondelete="SET NULL"), nullable=True
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="study_sessions")
    competency: Mapped["Competency | None"] = relationship()


class Challenge(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "challenges"

    competency_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        _enum(DifficultyLevel, "difficulty_level"), default=DifficultyLevel.BEGINNER, nullable=False
    )
    xp_value: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    competency: Mapped["Competency"] = relationship(back_populates="challenges")
    submissions: Mapped[list["ChallengeSubmission"]] = relationship(
        back_populates="challenge", cascade="all, delete-orphan"
    )


class ChallengeSubmission(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "challenge_submissions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("challenges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[ChallengeSubmissionStatus] = mapped_column(
        _enum(ChallengeSubmissionStatus, "challenge_submission_status"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship()
    challenge: Mapped["Challenge"] = relationship(back_populates="submissions")


class Mastery(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "mastery_records"
    __table_args__ = (
        UniqueConstraint("user_id", "competency_id", name="uq_mastery_user_competency"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    algorithm_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="mastery_records")
    competency: Mapped["Competency"] = relationship()


class Review(UUIDPrimaryKeyMixin, Base):
    """Spaced-repetition state per (user, competency), SM-2-lite algorithm.

    See docs/DECISIONS.md for the simplified SM-2 formula used.
    """

    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "competency_id", name="uq_review_user_competency"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interval_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    repetitions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_recall_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship()
    competency: Mapped["Competency"] = relationship()
