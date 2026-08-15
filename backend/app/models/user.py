from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    learning_goals: Mapped[list["LearningGoal"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    study_sessions: Mapped[list["StudySession"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    mastery_records: Mapped[list["Mastery"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    xp_awards: Mapped[list["XPAward"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"
