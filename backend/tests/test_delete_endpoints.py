"""DELETE /goals/{id} and DELETE /study-sessions/{id}.

Owner decision: deleting never refunds XP. The XP ledger, total XP, level,
streak and earned achievements stay as they were; mastery (knowledge, not
activity) is recomputed for the affected competency.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.gamification import AchievementCriterion, XPAward
from app.models.learning import Competency, StudySession
from tests.factories import API, make_achievement, make_competency, register


@pytest.fixture
def competency(db: Session) -> Competency:
    comp, _ = make_competency(db)
    return comp


def _log_session(
    client: TestClient, headers: dict[str, str], competency: Competency, minutes: int = 60
) -> str:
    response = client.post(
        f"{API}/study-sessions",
        headers=headers,
        json={"competency_id": str(competency.id), "duration_minutes": minutes},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _mastery_score(client: TestClient, headers: dict[str, str], competency: Competency) -> float:
    detail = client.get(f"{API}/subjects/{competency.subject_id}", headers=headers).json()
    return detail["competencies"][0]["mastery_score"]


class TestDeleteStudySession:
    def test_delete_returns_204_and_removes_the_session(
        self, client: TestClient, auth_headers: dict[str, str], competency: Competency
    ):
        session_id = _log_session(client, auth_headers, competency)

        response = client.delete(f"{API}/study-sessions/{session_id}", headers=auth_headers)

        assert response.status_code == 204
        assert response.content == b""
        listing = client.get(f"{API}/study-sessions", headers=auth_headers).json()
        assert listing == []

    def test_unknown_session_is_404(self, client: TestClient, auth_headers: dict[str, str]):
        response = client.delete(f"{API}/study-sessions/{uuid.uuid4()}", headers=auth_headers)
        assert response.status_code == 404

    def test_other_users_session_is_404_and_untouched(
        self, client: TestClient, auth_headers: dict[str, str], competency: Competency
    ):
        session_id = _log_session(client, auth_headers, competency)
        other_headers, _ = register(client, "intruder@example.com")

        response = client.delete(f"{API}/study-sessions/{session_id}", headers=other_headers)

        assert response.status_code == 404
        assert len(client.get(f"{API}/study-sessions", headers=auth_headers).json()) == 1

    def test_requires_authentication(self, client: TestClient):
        assert client.delete(f"{API}/study-sessions/{uuid.uuid4()}").status_code in (401, 403)

    def test_xp_level_streak_and_achievements_are_not_refunded(
        self, client: TestClient, db: Session, competency: Competency
    ):
        make_achievement(db, "first_session", AchievementCriterion.FIRST_STUDY_SESSION)
        headers, user_id = register(client, "keeper@example.com")
        session_id = _log_session(client, headers, competency)
        profile_before = client.get(f"{API}/gamification/profile", headers=headers).json()
        achievements_before = [
            a["achievement"]["code"]
            for a in client.get(f"{API}/gamification/achievements", headers=headers).json()
            if a["earned"]
        ]
        assert profile_before["total_xp"] == 30
        assert achievements_before == ["first_session"]
        awards_before = db.scalar(
            select(func.count()).select_from(XPAward).where(XPAward.user_id == user_id)
        )

        response = client.delete(f"{API}/study-sessions/{session_id}", headers=headers)
        assert response.status_code == 204

        profile_after = client.get(f"{API}/gamification/profile", headers=headers).json()
        assert profile_after == profile_before  # total_xp, level, streaks, last activity
        achievements_after = [
            a["achievement"]["code"]
            for a in client.get(f"{API}/gamification/achievements", headers=headers).json()
            if a["earned"]
        ]
        assert achievements_after == achievements_before
        # The ledger keeps the award even though its reference_id no longer exists.
        awards = list(db.scalars(select(XPAward).where(XPAward.user_id == user_id)))
        assert len(awards) == awards_before
        assert any(a.reference_id == uuid.UUID(session_id) for a in awards)
        assert db.get(StudySession, uuid.UUID(session_id)) is None

    def test_mastery_is_recomputed_for_the_competency(
        self, client: TestClient, auth_headers: dict[str, str], competency: Competency
    ):
        first = _log_session(client, auth_headers, competency, minutes=60)
        _log_session(client, auth_headers, competency, minutes=60)
        assert _mastery_score(client, auth_headers, competency) == pytest.approx(40.0)

        client.delete(f"{API}/study-sessions/{first}", headers=auth_headers)

        assert _mastery_score(client, auth_headers, competency) == pytest.approx(20.0)

    def test_mastery_returns_to_zero_when_last_session_is_deleted(
        self, client: TestClient, auth_headers: dict[str, str], competency: Competency
    ):
        session_id = _log_session(client, auth_headers, competency)
        assert _mastery_score(client, auth_headers, competency) > 0

        client.delete(f"{API}/study-sessions/{session_id}", headers=auth_headers)

        assert _mastery_score(client, auth_headers, competency) == 0.0


class TestDeleteGoal:
    def test_delete_returns_204_and_removes_the_goal(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        goal_id = client.post(
            f"{API}/goals", headers=auth_headers, json={"title": "Temporary goal"}
        ).json()["id"]

        response = client.delete(f"{API}/goals/{goal_id}", headers=auth_headers)

        assert response.status_code == 204
        assert client.get(f"{API}/goals", headers=auth_headers).json() == []

    def test_unknown_goal_is_404(self, client: TestClient, auth_headers: dict[str, str]):
        assert client.delete(f"{API}/goals/{uuid.uuid4()}", headers=auth_headers).status_code == 404

    def test_other_users_goal_is_404_and_untouched(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        goal_id = client.post(
            f"{API}/goals", headers=auth_headers, json={"title": "Private goal"}
        ).json()["id"]
        other_headers, _ = register(client, "intruder@example.com")

        response = client.delete(f"{API}/goals/{goal_id}", headers=other_headers)

        assert response.status_code == 404
        assert len(client.get(f"{API}/goals", headers=auth_headers).json()) == 1

    def test_deleting_a_goal_does_not_touch_xp(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        goal_id = client.post(f"{API}/goals", headers=auth_headers, json={"title": "G"}).json()[
            "id"
        ]
        before = client.get(f"{API}/gamification/profile", headers=auth_headers).json()

        client.delete(f"{API}/goals/{goal_id}", headers=auth_headers)

        assert client.get(f"{API}/gamification/profile", headers=auth_headers).json() == before
