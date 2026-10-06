from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.gamification import XPAward
    from app.models.learning import LearningGoal, Mastery, StudySession


class Language(StrEnum):
    """Content languages. `EN` is the default and the fallback for any content
    that has no translation; adding a language is a new enum member plus
    translated content (no schema change: stored as VARCHAR)."""

    EN = "en"
    PT_BR = "pt-BR"


DEFAULT_LANGUAGE = Language.EN


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Language for *content* (questions, explanations, future AI). The UI
    # strings are not localised yet (roadmap J7).
    preferred_language: Mapped[Language] = mapped_column(
        SAEnum(Language, name="language", native_enum=False, validate_strings=True, length=32),
        default=DEFAULT_LANGUAGE,
        server_default=Language.EN.name,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Tokens issued before this instant are rejected (set on refresh-token
    # reuse detection to kill every outstanding session of the user).
    tokens_valid_after: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    learning_goals: Mapped[list["LearningGoal"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    study_sessions: Mapped[list["StudySession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    mastery_records: Mapped[list["Mastery"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    xp_awards: Mapped[list["XPAward"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"
