"""Shared helpers for service-level tests: minimal catalog rows, extra
registered users, and a controllable clock for the gamification services.

Catalog content is data in the database, so tests build the few rows they need
instead of relying on the production seeds.
"""

import uuid
from datetime import UTC, datetime
from types import ModuleType

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.gamification import (
    Achievement,
    AchievementCriterion,
    Quest,
    QuestCriterion,
    QuestPeriod,
)
from app.models.learning import Challenge, Competency, DifficultyLevel, Subject

API = "/api/v1"


def make_competency(
    db: Session, *, challenge_xp: list[int] | None = None
) -> tuple[Competency, list[Challenge]]:
    """A subject + competency with one challenge per entry of `challenge_xp`."""
    subject = Subject(name=f"Subject {uuid.uuid4()}", slug=f"subject-{uuid.uuid4()}")
    db.add(subject)
    db.flush()
    competency = Competency(
        subject_id=subject.id,
        name="Competency",
        slug=f"competency-{uuid.uuid4()}",
        difficulty=DifficultyLevel.BEGINNER,
    )
    db.add(competency)
    db.flush()
    challenges = []
    for index, xp in enumerate(challenge_xp if challenge_xp is not None else [50]):
        challenge = Challenge(
            competency_id=competency.id,
            title=f"Challenge {index}",
            description="Do the thing.",
            difficulty=DifficultyLevel.BEGINNER,
            xp_value=xp,
        )
        db.add(challenge)
        challenges.append(challenge)
    db.commit()
    return competency, challenges


def make_achievement(
    db: Session,
    code: str,
    criterion: AchievementCriterion,
    value: int | None = None,
    xp_reward: int = 0,
) -> Achievement:
    achievement = Achievement(
        code=code,
        name=code,
        description=code,
        criteria_type=criterion,
        criteria_value=value,
        xp_reward=xp_reward,
    )
    db.add(achievement)
    db.commit()
    return achievement


def make_quest(
    db: Session,
    code: str,
    criterion: QuestCriterion,
    value: int,
    xp_reward: int = 40,
    period: QuestPeriod = QuestPeriod.WEEKLY,
    is_active: bool = True,
) -> Quest:
    quest = Quest(
        code=code,
        title=code,
        description=code,
        criteria_type=criterion,
        criteria_value=value,
        period=period,
        xp_reward=xp_reward,
        is_active=is_active,
    )
    db.add(quest)
    db.commit()
    return quest


def register(client: TestClient, email: str) -> tuple[dict[str, str], uuid.UUID]:
    """Register a user; returns (auth headers, user id)."""
    response = client.post(
        f"{API}/auth/register",
        json={"email": email, "password": "supersecret123", "display_name": email.split("@")[0]},
    )
    assert response.status_code == 201
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    me = client.get(f"{API}/auth/me", headers=headers)
    return headers, uuid.UUID(me.json()["id"])


class FakeClock:
    """Mutable "now" injected in place of the `datetime` name of a service module."""

    def __init__(self, start: datetime) -> None:
        self.current = start


def freeze_time(monkeypatch: pytest.MonkeyPatch, module: ModuleType, start: datetime) -> FakeClock:
    clock = FakeClock(start)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[no-untyped-def, override]
            return clock.current

    monkeypatch.setattr(module, "datetime", FrozenDatetime)
    return clock


def utc(year: int, month: int, day: int, hour: int = 12) -> datetime:
    return datetime(year, month, day, hour, tzinfo=UTC)
