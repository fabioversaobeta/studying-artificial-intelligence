"""Assessments: the question bank and quiz attempts.

Content (questions, translations, assessments) is seeded data; attempts and
responses are per-user activity. See docs/DOMAIN.md ("Assessments") for the
model overview and docs/DECISIONS.md for the translation design and the XP rule.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.assessments import DEFAULT_COMPLETION_BONUS_XP, DEFAULT_PASS_THRESHOLD
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.user import Language

if TYPE_CHECKING:
    from app.models.learning import Competency


class QuestionType(StrEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    MULTI_SELECT = "multi_select"
    SHORT_ANSWER = "short_answer"
    CODE_READING = "code_reading"


class QuestionDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionSource(StrEnum):
    AI_GENERATED = "ai_generated"
    MANUAL = "manual"


class AssessmentKind(StrEnum):
    COMPETENCY = "competency"
    LEARNING_PATH = "learning_path"
    MIXED = "mixed"


class AttemptStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class GradingStatus(StrEnum):
    """How a response was (or will be) graded.

    GRADED: deterministic (choice questions). PENDING_REVIEW: a short answer
    still waiting for a verdict. SELF_GRADED: a short answer the learner marked
    right/wrong after seeing the model answer. A future AI judge (roadmap I5)
    would add a value here.
    """

    GRADED = "graded"
    PENDING_REVIEW = "pending_review"
    SELF_GRADED = "self_graded"


def _enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    return SAEnum(enum_cls, name=name, native_enum=False, validate_strings=True, length=32)


def _language_enum() -> SAEnum:
    return _enum(Language, "language")


class Question(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Language-independent part of a question: what to grade with and how it
    is classified. Everything a human reads lives in `QuestionTranslation`.
    """

    __tablename__ = "questions"
    __table_args__ = (Index("ix_questions_competency_active", "competency_id", "is_active"),)

    # Stable natural key used by the seeds (e.g. "python-type-hints-q01").
    code: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    competency_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("competencies.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[QuestionType] = mapped_column(_enum(QuestionType, "question_type"), nullable=False)
    difficulty: Mapped[QuestionDifficulty] = mapped_column(
        _enum(QuestionDifficulty, "question_difficulty"), nullable=False
    )
    xp_value: Mapped[int] = mapped_column(Integer, nullable=False)
    # Option ids (e.g. ["b"] or ["a", "c"]); null for short_answer. Option ids
    # are shared by every translation, so grading never depends on the language.
    correct_option_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    tags: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    source: Mapped[QuestionSource] = mapped_column(
        _enum(QuestionSource, "question_source"), default=QuestionSource.MANUAL, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )

    competency: Mapped["Competency"] = relationship()
    translations: Mapped[list["QuestionTranslation"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class QuestionTranslation(UUIDPrimaryKeyMixin, Base):
    """The text of a question in one language. `en` is mandatory (enforced by
    the seed validator and by the service fallback chain); other languages are
    optional and fall back to `en` per question."""

    __tablename__ = "question_translations"
    __table_args__ = (UniqueConstraint("question_id", "language", name="uq_question_language"),)

    question_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[Language] = mapped_column(_language_enum(), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)  # markdown
    # [{"id": "a", "text": "..."}, ...]; null for short_answer.
    options: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    # Reference answer shown for self-assessment (short_answer only).
    model_answer: Mapped[str | None] = mapped_column(Text, nullable=True)

    question: Mapped["Question"] = relationship(back_populates="translations")


class Assessment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An ordered set of questions: for a competency, a learning path, or mixed."""

    __tablename__ = "assessments"
    __table_args__ = (
        CheckConstraint(
            "pass_threshold >= 1 AND pass_threshold <= 100", name="ck_assessment_threshold_range"
        ),
        CheckConstraint("completion_bonus_xp >= 0", name="ck_assessment_bonus_non_negative"),
    )

    code: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)  # English
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # {"pt-BR": {"title": "...", "description": "..."}}; missing -> English.
    translations: Mapped[dict[str, dict[str, str]]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    kind: Mapped[AssessmentKind] = mapped_column(
        _enum(AssessmentKind, "assessment_kind"), nullable=False
    )
    competency_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("competencies.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    learning_path_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=True
    )
    pass_threshold: Mapped[int] = mapped_column(
        Integer, default=DEFAULT_PASS_THRESHOLD, server_default="70", nullable=False
    )
    completion_bonus_xp: Mapped[int] = mapped_column(
        Integer,
        default=DEFAULT_COMPLETION_BONUS_XP,
        server_default=str(DEFAULT_COMPLETION_BONUS_XP),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    competency: Mapped["Competency | None"] = relationship()
    questions: Mapped[list["AssessmentQuestion"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentQuestion.sort_order",
    )


class AssessmentQuestion(Base):
    """Membership of a question in an assessment (many-to-many, ordered)."""

    __tablename__ = "assessment_questions"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    assessment: Mapped["Assessment"] = relationship(back_populates="questions")
    question: Mapped["Question"] = relationship()


class AssessmentAttempt(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "assessment_attempts"
    __table_args__ = (
        Index("ix_attempts_user_assessment", "user_id", "assessment_id"),
        Index("ix_attempts_user_started_at", "user_id", text("started_at DESC")),
        # At most one open attempt per (user, assessment): a double-click on
        # "start" resumes instead of creating two.
        Index(
            "uq_attempt_one_open",
            "user_id",
            "assessment_id",
            unique=True,
            postgresql_where=text("status = 'IN_PROGRESS'"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[AttemptStatus] = mapped_column(
        _enum(AttemptStatus, "attempt_status"), default=AttemptStatus.IN_PROGRESS, nullable=False
    )
    # Snapshot (ordered) of the question ids served at start, so bank edits
    # during an attempt cannot change what is being answered or scored.
    question_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correct_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xp_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xp_bonus: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    assessment: Mapped["Assessment"] = relationship()
    responses: Mapped[list["QuestionResponse"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )


class QuestionResponse(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "question_responses"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_response_attempt_question"),
        Index("ix_responses_user_question", "user_id", "question_id"),
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    # Denormalised from the attempt for the per-user history/coverage queries.
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # {"option_ids": ["a"]} for choice questions, {"text": "..."} for short answers.
    answer: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    grading_status: Mapped[GradingStatus] = mapped_column(
        _enum(GradingStatus, "grading_status"), nullable=False
    )
    # null while a short answer is pending_review.
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # True when this was the first correct answer to the question in the user's
    # life (set when the attempt is finished). Informational: payment depends on
    # `xp_awarded` history, see docs/DECISIONS.md.
    is_first_correct: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    attempt: Mapped["AssessmentAttempt"] = relationship(back_populates="responses")
    question: Mapped["Question"] = relationship()
