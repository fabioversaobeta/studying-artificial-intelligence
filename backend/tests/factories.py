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

from app.domain.assessments import XP_BY_DIFFICULTY
from app.models.assessment import (
    Assessment,
    AssessmentKind,
    AssessmentQuestion,
    Question,
    QuestionDifficulty,
    QuestionSource,
    QuestionTranslation,
    QuestionType,
)
from app.models.gamification import (
    Achievement,
    AchievementCriterion,
    Quest,
    QuestCriterion,
    QuestPeriod,
)
from app.models.learning import Challenge, Competency, DifficultyLevel, Subject
from app.models.user import Language

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


def make_question(
    db: Session,
    competency: Competency,
    *,
    type: QuestionType = QuestionType.MULTIPLE_CHOICE,
    difficulty: QuestionDifficulty = QuestionDifficulty.EASY,
    correct: list[str] | None = None,
    option_ids: tuple[str, ...] = ("a", "b", "c"),
    pt_br: bool = False,
    is_active: bool = True,
) -> Question:
    """A question whose correct answer is option "b" (single) unless stated.

    English text is "EN <code> option X"; the optional pt-BR translation is
    "PT <code> opcao X". Short answers get no options and a model answer.
    """
    code = f"q-{uuid.uuid4().hex[:10]}"
    is_open = type == QuestionType.SHORT_ANSWER
    if correct is None:
        correct = ["b", "c"] if type == QuestionType.MULTI_SELECT else ["b"]
    question = Question(
        code=code,
        competency_id=competency.id,
        type=type,
        difficulty=difficulty,
        xp_value=XP_BY_DIFFICULTY[difficulty.value],
        correct_option_ids=None if is_open else correct,
        tags=["test"],
        source=QuestionSource.MANUAL,
        is_active=is_active,
    )
    db.add(question)
    db.flush()

    def translation(language: Language, prefix: str, word: str) -> QuestionTranslation:
        return QuestionTranslation(
            question_id=question.id,
            language=language,
            prompt=f"{prefix} prompt {code}",
            options=None
            if is_open
            else [{"id": o, "text": f"{prefix} {code} {word} {o.upper()}"} for o in option_ids],
            explanation=f"{prefix} explanation {code}",
            model_answer=f"{prefix} model answer {code}" if is_open else None,
        )

    db.add(translation(Language.EN, "EN", "option"))
    if pt_br:
        db.add(translation(Language.PT_BR, "PT", "opcao"))
    db.commit()
    return question


def make_assessment(
    db: Session,
    competency: Competency | None,
    questions: list[Question],
    *,
    threshold: int = 70,
    bonus: int = 25,
    kind: AssessmentKind = AssessmentKind.COMPETENCY,
    is_active: bool = True,
    translations: dict[str, dict[str, str]] | None = None,
) -> Assessment:
    assessment = Assessment(
        code=f"a-{uuid.uuid4().hex[:10]}",
        title="Quiz",
        description="A quiz",
        translations=translations or {},
        kind=kind,
        competency_id=competency.id if competency else None,
        pass_threshold=threshold,
        completion_bonus_xp=bonus,
        is_active=is_active,
    )
    db.add(assessment)
    db.flush()
    for order, question in enumerate(questions):
        db.add(
            AssessmentQuestion(
                assessment_id=assessment.id, question_id=question.id, sort_order=order
            )
        )
    db.commit()
    return assessment


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
