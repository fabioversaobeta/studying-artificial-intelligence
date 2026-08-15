import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.learning import Challenge, Competency, DifficultyLevel, Subject


@pytest.fixture
def competency(db: Session) -> Competency:
    subject = Subject(name=f"Test Subject {uuid.uuid4()}", slug=f"test-subject-{uuid.uuid4()}")
    db.add(subject)
    db.flush()

    comp = Competency(
        subject_id=subject.id,
        name="Test Competency",
        slug="test-competency",
        difficulty=DifficultyLevel.BEGINNER,
    )
    db.add(comp)
    db.flush()

    challenge = Challenge(
        competency_id=comp.id,
        title="Test Challenge",
        description="Do the thing.",
        difficulty=DifficultyLevel.BEGINNER,
        xp_value=50,
    )
    db.add(challenge)
    db.commit()
    db.refresh(comp)
    return comp


class TestStudySessions:
    def test_log_study_session_awards_xp_and_creates_mastery(
        self, client: TestClient, auth_headers: dict[str, str], competency: Competency
    ):
        response = client.post(
            "/api/v1/study-sessions",
            headers=auth_headers,
            json={
                "competency_id": str(competency.id),
                "duration_minutes": 60,
                "notes": "Focused session",
            },
        )
        assert response.status_code == 201
        assert response.json()["duration_minutes"] == 60

        profile = client.get("/api/v1/gamification/profile", headers=auth_headers).json()
        assert profile["total_xp"] == 30  # min(60, (60//10)*5) = 30

        detail = client.get(
            f"/api/v1/subjects/{competency.subject_id}", headers=auth_headers
        ).json()
        state = detail["competencies"][0]
        assert state["mastery_score"] == pytest.approx(20.0)  # 60/120 * 40 engagement points
        assert state["state"] == "learning"

    def test_study_session_requires_positive_duration(
        self, client: TestClient, auth_headers: dict[str, str], competency: Competency
    ):
        response = client.post(
            "/api/v1/study-sessions",
            headers=auth_headers,
            json={"competency_id": str(competency.id), "duration_minutes": 0},
        )
        assert response.status_code == 422

    def test_study_session_rejects_unknown_competency(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        response = client.post(
            "/api/v1/study-sessions",
            headers=auth_headers,
            json={"competency_id": str(uuid.uuid4()), "duration_minutes": 30},
        )
        assert response.status_code == 404


class TestChallengeSubmissions:
    def test_passing_a_challenge_awards_its_xp_once(
        self, client: TestClient, auth_headers: dict[str, str], competency: Competency
    ):
        challenges = client.get(
            f"/api/v1/competencies/{competency.id}/challenges", headers=auth_headers
        ).json()
        challenge_id = challenges[0]["id"]

        first = client.post(
            f"/api/v1/challenges/{challenge_id}/submissions",
            headers=auth_headers,
            json={"status": "passed", "notes": "Nailed it"},
        )
        assert first.status_code == 201
        assert first.json()["xp_awarded"] == 50

        # Resubmitting a pass for the same challenge must not double-award XP.
        second = client.post(
            f"/api/v1/challenges/{challenge_id}/submissions",
            headers=auth_headers,
            json={"status": "passed", "notes": "Again"},
        )
        assert second.status_code == 201
        assert second.json()["xp_awarded"] == 0

        profile = client.get("/api/v1/gamification/profile", headers=auth_headers).json()
        assert profile["total_xp"] == 50

    def test_failed_submission_awards_no_xp(
        self, client: TestClient, auth_headers: dict[str, str], competency: Competency
    ):
        challenges = client.get(
            f"/api/v1/competencies/{competency.id}/challenges", headers=auth_headers
        ).json()
        challenge_id = challenges[0]["id"]

        response = client.post(
            f"/api/v1/challenges/{challenge_id}/submissions",
            headers=auth_headers,
            json={"status": "failed", "notes": "Not yet"},
        )
        assert response.status_code == 201
        assert response.json()["xp_awarded"] == 0


class TestLearningGoals:
    def test_create_and_list_goals(self, client: TestClient, auth_headers: dict[str, str]):
        create = client.post(
            "/api/v1/goals",
            headers=auth_headers,
            json={"title": "Become a Staff Engineer", "description": "Focus on system design"},
        )
        assert create.status_code == 201
        goal_id = create.json()["id"]
        assert create.json()["status"] == "active"

        listing = client.get("/api/v1/goals", headers=auth_headers)
        assert len(listing.json()) == 1

        update = client.patch(
            f"/api/v1/goals/{goal_id}/status", headers=auth_headers, json={"status": "achieved"}
        )
        assert update.status_code == 200
        assert update.json()["status"] == "achieved"

    def test_cannot_update_another_users_goal(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        create = client.post(
            "/api/v1/goals", headers=auth_headers, json={"title": "My private goal"}
        )
        goal_id = create.json()["id"]

        other_register = client.post(
            "/api/v1/auth/register",
            json={
                "email": "other@example.com",
                "password": "supersecret123",
                "display_name": "Other",
            },
        )
        other_headers = {"Authorization": f"Bearer {other_register.json()['access_token']}"}

        response = client.patch(
            f"/api/v1/goals/{goal_id}/status", headers=other_headers, json={"status": "achieved"}
        )
        assert response.status_code == 404
