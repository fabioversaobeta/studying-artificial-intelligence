"""How finishing an assessment feeds the rest of the platform: mastery
(Practice signal), spaced repetition, streak, achievements and quests."""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.gamification import AchievementCriterion, QuestCriterion, XPAward, XPSource
from app.models.learning import Review
from app.repositories import mastery_repository, review_repository
from app.services import gamification_service
from tests.factories import (
    API,
    freeze_time,
    make_achievement,
    make_assessment,
    make_competency,
    make_quest,
    make_question,
    register,
    utc,
)


def _play(client: TestClient, headers: dict[str, str], assessment, n_correct: int) -> dict:
    attempt = client.post(f"{API}/assessments/{assessment.id}/attempts", headers=headers).json()
    for index, item in enumerate(attempt["questions"]):
        client.put(
            f"{API}/attempts/{attempt['id']}/responses/{item['id']}",
            headers=headers,
            json={"option_ids": ["b"] if index < n_correct else ["a"]},
        )
    finished = client.post(f"{API}/attempts/{attempt['id']}/finish", headers=headers)
    assert finished.status_code == 200
    return finished.json()


@pytest.fixture
def user(client: TestClient) -> tuple[dict[str, str], uuid.UUID]:
    return register(client, "learner@example.com")


def _mastery(db: Session, user_id: uuid.UUID, competency) -> float:
    record = mastery_repository.get_mastery(db, user_id, competency.id)
    return record.score if record else 0.0


class TestMasteryPractice:
    def test_finishing_sets_practice_from_quiz_coverage(
        self, client: TestClient, db: Session, user
    ):
        headers, user_id = user
        competency, _ = make_competency(db, challenge_xp=[])
        questions = [make_question(db, competency) for _ in range(4)]
        assessment = make_assessment(db, competency, questions)

        _play(client, headers, assessment, 2)
        assert _mastery(db, user_id, competency) == 17.5  # 35 * 2/4
        _play(client, headers, assessment, 4)
        assert _mastery(db, user_id, competency) == 35.0

    def test_latest_answer_decides_so_later_misses_take_credit_back(
        self, client: TestClient, db: Session, user
    ):
        headers, user_id = user
        competency, _ = make_competency(db, challenge_xp=[])
        assessment = make_assessment(
            db, competency, [make_question(db, competency) for _ in range(4)]
        )
        _play(client, headers, assessment, 4)
        assert _mastery(db, user_id, competency) == 35.0
        _play(client, headers, assessment, 0)
        assert _mastery(db, user_id, competency) == 0.0

    def test_repeating_the_same_answers_cannot_inflate_practice(
        self, client: TestClient, db: Session, user
    ):
        headers, user_id = user
        competency, _ = make_competency(db, challenge_xp=[])
        assessment = make_assessment(
            db, competency, [make_question(db, competency) for _ in range(4)]
        )
        for _ in range(5):
            _play(client, headers, assessment, 1)
        # Five attempts, still the same single question covered: 1/4, not 5/4.
        assert _mastery(db, user_id, competency) == 8.75

    def test_answers_in_an_open_attempt_do_not_count_until_finished(
        self, client: TestClient, db: Session, user
    ):
        headers, user_id = user
        competency, _ = make_competency(db, challenge_xp=[])
        questions = [make_question(db, competency) for _ in range(2)]
        assessment = make_assessment(db, competency, questions)
        attempt = client.post(f"{API}/assessments/{assessment.id}/attempts", headers=headers).json()
        client.put(
            f"{API}/attempts/{attempt['id']}/responses/{questions[0].id}",
            headers=headers,
            json={"option_ids": ["b"]},
        )
        assert _mastery(db, user_id, competency) == 0.0

    def test_challenges_and_quizzes_are_averaged_with_equal_weight(
        self, client: TestClient, db: Session, user
    ):
        headers, user_id = user
        competency, (challenge,) = make_competency(db, challenge_xp=[50])
        assessment = make_assessment(
            db, competency, [make_question(db, competency) for _ in range(4)]
        )
        client.post(
            f"{API}/challenges/{challenge.id}/submissions",
            headers=headers,
            json={"status": "passed"},
        )
        # Challenge share 1/1, no quiz yet: (1.0 + 0.0) / 2 of 35 points.
        assert _mastery(db, user_id, competency) == 17.5
        _play(client, headers, assessment, 2)
        # (1.0 + 0.5) / 2 = 0.75 -> 26.25
        assert _mastery(db, user_id, competency) == 26.25

    def test_a_mixed_assessment_updates_every_touched_competency(
        self, client: TestClient, db: Session, user
    ):
        from app.models.assessment import AssessmentKind

        headers, user_id = user
        first, _ = make_competency(db, challenge_xp=[])
        second, _ = make_competency(db, challenge_xp=[])
        q1, q2 = make_question(db, first), make_question(db, second)
        mixed = make_assessment(db, None, [q1, q2], kind=AssessmentKind.MIXED)
        _play(client, headers, mixed, 2)
        assert _mastery(db, user_id, first) == 35.0
        assert _mastery(db, user_id, second) == 35.0

    def test_deactivated_questions_leave_the_denominator(
        self, client: TestClient, db: Session, user
    ):
        headers, user_id = user
        competency, _ = make_competency(db, challenge_xp=[])
        questions = [make_question(db, competency) for _ in range(2)]
        assessment = make_assessment(db, competency, questions)
        _play(client, headers, assessment, 1)
        assert _mastery(db, user_id, competency) == 17.5
        questions[1].is_active = False
        db.commit()
        _play(client, headers, assessment, 1)
        assert _mastery(db, user_id, competency) == 35.0


class TestSpacedRepetition:
    def test_a_wrong_answer_creates_a_due_review(self, client: TestClient, db: Session, user):
        headers, user_id = user
        competency, _ = make_competency(db, challenge_xp=[])
        assessment = make_assessment(
            db, competency, [make_question(db, competency) for _ in range(2)]
        )
        _play(client, headers, assessment, 1)
        review = review_repository.get_review(db, user_id, competency.id)
        assert review is not None
        due = client.get(f"{API}/reviews/due", headers=headers).json()
        assert [r["competency_id"] for r in due] == [str(competency.id)]

    def test_a_perfect_attempt_does_not_create_a_review(
        self, client: TestClient, db: Session, user
    ):
        headers, user_id = user
        competency, _ = make_competency(db, challenge_xp=[])
        assessment = make_assessment(
            db, competency, [make_question(db, competency) for _ in range(2)]
        )
        _play(client, headers, assessment, 2)
        assert review_repository.get_review(db, user_id, competency.id) is None

    def test_unanswered_questions_are_not_evidence_of_a_gap(
        self, client: TestClient, db: Session, user
    ):
        headers, user_id = user
        competency, _ = make_competency(db, challenge_xp=[])
        assessment = make_assessment(db, competency, [make_question(db, competency)])
        attempt = client.post(f"{API}/assessments/{assessment.id}/attempts", headers=headers).json()
        client.post(f"{API}/attempts/{attempt['id']}/finish", headers=headers)
        assert review_repository.get_review(db, user_id, competency.id) is None

    def test_a_later_review_is_pulled_forward_without_touching_the_sm2_state(
        self, client: TestClient, db: Session, user
    ):
        headers, user_id = user
        competency, _ = make_competency(db, challenge_xp=[])
        assessment = make_assessment(db, competency, [make_question(db, competency)])
        client.post(
            f"{API}/study-sessions",
            headers=headers,
            json={"competency_id": str(competency.id), "duration_minutes": 10},
        )
        review = review_repository.get_review(db, user_id, competency.id)
        review.interval_days, review.ease_factor, review.repetitions = 6, 2.1, 3
        db.commit()
        assert review.due_at > datetime.now(UTC)

        _play(client, headers, assessment, 0)
        db.expire_all()
        review = db.query(Review).filter(Review.competency_id == competency.id).one()
        assert (review.interval_days, review.ease_factor, review.repetitions) == (6, 2.1, 3)
        assert len(client.get(f"{API}/reviews/due", headers=headers).json()) == 1


class TestGamificationHooks:
    def test_finishing_without_xp_still_extends_the_streak(
        self, client: TestClient, db: Session, user, monkeypatch: pytest.MonkeyPatch
    ):
        headers, user_id = user
        competency, _ = make_competency(db, challenge_xp=[])
        assessment = make_assessment(
            db, competency, [make_question(db, competency) for _ in range(2)]
        )
        clock = freeze_time(monkeypatch, gamification_service, utc(2026, 3, 1))
        assert _play(client, headers, assessment, 2)["xp_awarded"] > 0

        clock.current = utc(2026, 3, 2)
        repeat = _play(client, headers, assessment, 2)
        assert repeat["xp_awarded"] == 0
        profile = client.get(f"{API}/gamification/profile", headers=headers).json()
        assert profile["current_streak_days"] == 2

    def test_a_failed_attempt_counts_as_activity(self, client: TestClient, db: Session, user):
        headers, _ = user
        competency, _ = make_competency(db, challenge_xp=[])
        assessment = make_assessment(db, competency, [make_question(db, competency)])
        _play(client, headers, assessment, 0)
        profile = client.get(f"{API}/gamification/profile", headers=headers).json()
        assert (profile["total_xp"], profile["current_streak_days"]) == (0, 1)

    def test_assessments_passed_achievement(self, client: TestClient, db: Session, user):
        headers, user_id = user
        make_achievement(
            db, "quiz_taker", AchievementCriterion.ASSESSMENTS_PASSED_COUNT, 2, xp_reward=100
        )
        competency, _ = make_competency(db, challenge_xp=[])
        first = make_assessment(db, competency, [make_question(db, competency)], bonus=0)
        second = make_assessment(db, competency, [make_question(db, competency)], bonus=0)

        _play(client, headers, first, 0)  # failed: does not count
        _play(client, headers, first, 1)
        _play(client, headers, first, 1)  # same assessment again: still one distinct
        earned = lambda: {  # noqa: E731
            a["achievement"]["code"]: a["earned"]
            for a in client.get(f"{API}/gamification/achievements", headers=headers).json()
        }
        assert earned()["quiz_taker"] is False
        _play(client, headers, second, 1)
        assert earned()["quiz_taker"] is True
        reward = db.query(XPAward).filter(XPAward.source == XPSource.ACHIEVEMENT).one()
        assert reward.amount == 100

    def test_assessments_passed_quest(self, client: TestClient, db: Session, user):
        headers, _ = user
        make_quest(db, "weekly_quiz", QuestCriterion.ASSESSMENTS_PASSED_COUNT, 1, xp_reward=40)
        competency, _ = make_competency(db, challenge_xp=[])
        assessment = make_assessment(db, competency, [make_question(db, competency)], bonus=0)

        _play(client, headers, assessment, 0)
        quests = client.get(f"{API}/gamification/quests", headers=headers).json()
        assert quests[0]["completed"] is False
        _play(client, headers, assessment, 1)
        quests = client.get(f"{API}/gamification/quests", headers=headers).json()
        assert quests[0]["completed"] is True
        # 10 for the question + 40 for the quest (quest XP paid by the existing mechanism).
        assert client.get(f"{API}/gamification/profile", headers=headers).json()["total_xp"] == 50


def test_started_attempt_survives_bank_changes(client: TestClient, db: Session, user):
    """The question list is snapshotted at start: retiring a question mid-attempt
    does not change what is served or how the attempt is scored."""
    headers, _ = user
    competency, _ = make_competency(db, challenge_xp=[])
    questions = [make_question(db, competency) for _ in range(2)]
    assessment = make_assessment(db, competency, questions)
    attempt = client.post(f"{API}/assessments/{assessment.id}/attempts", headers=headers).json()
    questions[0].is_active = False
    db.commit()
    again = client.get(f"{API}/attempts/{attempt['id']}", headers=headers).json()
    assert again["total_questions"] == 2
    assert len(again["questions"]) == 2
