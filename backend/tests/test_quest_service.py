"""quest_service: progress is computed on read and completion pays XP once per period."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.gamification import QuestCriterion, QuestPeriod
from tests.factories import API, make_competency, make_quest


def _quests(client: TestClient, headers: dict[str, str]) -> dict[str, dict]:
    response = client.get(f"{API}/gamification/quests", headers=headers)
    assert response.status_code == 200
    return {q["quest"]["code"]: q for q in response.json()}


def _xp(client: TestClient, headers: dict[str, str]) -> int:
    return client.get(f"{API}/gamification/profile", headers=headers).json()["total_xp"]


def _study(client: TestClient, headers: dict[str, str], competency=None, minutes: int = 5):
    body: dict = {"duration_minutes": minutes}
    if competency is not None:
        body["competency_id"] = str(competency.id)
    assert client.post(f"{API}/study-sessions", headers=headers, json=body).status_code == 201


class TestQuestProgress:
    def test_no_quests_returns_empty_list(self, client: TestClient, auth_headers: dict[str, str]):
        assert client.get(f"{API}/gamification/quests", headers=auth_headers).json() == []

    def test_progress_below_target_is_not_completed(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        make_quest(db, "study_3", QuestCriterion.STUDY_SESSIONS_COUNT, 3)
        _study(client, auth_headers)
        quest = _quests(client, auth_headers)["study_3"]
        assert (quest["progress"], quest["target"], quest["completed"]) == (1, 3, False)
        assert _xp(client, auth_headers) == 0

    def test_inactive_quests_are_hidden(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        make_quest(db, "off", QuestCriterion.STUDY_SESSIONS_COUNT, 1, is_active=False)
        make_quest(db, "on", QuestCriterion.STUDY_SESSIONS_COUNT, 1)
        assert set(_quests(client, auth_headers)) == {"on"}

    def test_period_key_formats(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        make_quest(db, "weekly", QuestCriterion.STUDY_SESSIONS_COUNT, 1)
        make_quest(db, "once", QuestCriterion.STUDY_SESSIONS_COUNT, 1, period=QuestPeriod.ONE_TIME)
        quests = _quests(client, auth_headers)
        iso = datetime.now(UTC).isocalendar()
        assert quests["weekly"]["period_key"] == f"{iso.year}-W{iso.week:02d}"
        assert quests["once"]["period_key"] == "one_time"

    def test_progress_is_per_user(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        from tests.factories import register

        make_quest(db, "study_1", QuestCriterion.STUDY_SESSIONS_COUNT, 1)
        other_headers, _ = register(client, "other@example.com")
        _study(client, auth_headers)
        assert _quests(client, other_headers)["study_1"]["progress"] == 0
        assert _quests(client, auth_headers)["study_1"]["completed"] is True


class TestQuestCompletion:
    def test_completion_pays_xp_exactly_once(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        make_quest(db, "study_2", QuestCriterion.STUDY_SESSIONS_COUNT, 2, xp_reward=40)
        _study(client, auth_headers, minutes=5)  # study XP 0 (under 10 minutes)
        _study(client, auth_headers, minutes=5)
        assert _xp(client, auth_headers) == 0

        first = _quests(client, auth_headers)["study_2"]
        assert first["completed"] is True
        assert _xp(client, auth_headers) == 40

        for _ in range(3):
            assert _quests(client, auth_headers)["study_2"]["completed"] is True
        assert _xp(client, auth_headers) == 40

    def test_progress_is_capped_at_target(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        make_quest(db, "study_1", QuestCriterion.STUDY_SESSIONS_COUNT, 1)
        for _ in range(3):
            _study(client, auth_headers)
        assert _quests(client, auth_headers)["study_1"]["progress"] == 1

    def test_one_time_quest_completes_once(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        make_quest(
            db,
            "once",
            QuestCriterion.STUDY_SESSIONS_COUNT,
            1,
            xp_reward=25,
            period=QuestPeriod.ONE_TIME,
        )
        _study(client, auth_headers)
        _quests(client, auth_headers)
        _quests(client, auth_headers)
        assert _xp(client, auth_headers) == 25

    def test_challenge_quest_counts_only_passed_submissions(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        make_quest(db, "pass_1", QuestCriterion.CHALLENGES_PASSED_COUNT, 1, xp_reward=30)
        _, (challenge,) = make_competency(db, challenge_xp=[10])
        url = f"{API}/challenges/{challenge.id}/submissions"
        client.post(url, headers=auth_headers, json={"status": "failed"})
        assert _quests(client, auth_headers)["pass_1"]["progress"] == 0
        client.post(url, headers=auth_headers, json={"status": "passed"})
        assert _quests(client, auth_headers)["pass_1"]["completed"] is True
        assert _xp(client, auth_headers) == 10 + 30

    def test_review_quest_counts_completed_recalls(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        make_quest(db, "review_1", QuestCriterion.REVIEWS_COMPLETED_COUNT, 1, xp_reward=20)
        competency, _ = make_competency(db)
        _study(client, auth_headers, competency)
        assert _quests(client, auth_headers)["review_1"]["progress"] == 0
        client.post(
            f"{API}/reviews/{competency.id}/recall", headers=auth_headers, json={"quality": 4}
        )
        assert _quests(client, auth_headers)["review_1"]["completed"] is True
        assert _xp(client, auth_headers) == 15 + 20

    def test_xp_earned_quest_uses_xp_ledger(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        make_quest(db, "xp_50", QuestCriterion.XP_EARNED, 50, xp_reward=10)
        _study(client, auth_headers, minutes=60)  # 30 XP
        assert _quests(client, auth_headers)["xp_50"]["progress"] == 30
        _study(client, auth_headers, minutes=60)  # 60 XP total
        quest = _quests(client, auth_headers)["xp_50"]
        assert quest["completed"] is True
        assert _xp(client, auth_headers) == 60 + 10

    @pytest.mark.parametrize("target", [1, 2])
    def test_quest_reward_is_not_counted_as_streak_activity(
        self, client: TestClient, auth_headers: dict[str, str], db: Session, target: int
    ):
        make_quest(db, "q", QuestCriterion.STUDY_SESSIONS_COUNT, target)
        for _ in range(target):
            _study(client, auth_headers, minutes=10)  # 5 XP, so it counts for the streak
        _quests(client, auth_headers)
        profile = client.get(f"{API}/gamification/profile", headers=auth_headers).json()
        assert profile["current_streak_days"] == 1
