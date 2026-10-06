"""challenge_service via the API: first-pass-only XP, failures, mastery recompute."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import API, make_competency, register


def _submit(client: TestClient, headers: dict[str, str], challenge_id, status: str):
    return client.post(
        f"{API}/challenges/{challenge_id}/submissions",
        headers=headers,
        json={"status": status},
    )


def _xp(client: TestClient, headers: dict[str, str]) -> int:
    return client.get(f"{API}/gamification/profile", headers=headers).json()["total_xp"]


def _mastery(client: TestClient, headers: dict[str, str], competency) -> float:
    detail = client.get(f"{API}/subjects/{competency.subject_id}", headers=headers).json()
    return detail["competencies"][0]["mastery_score"]


class TestChallengeXp:
    def test_failed_then_passed_awards_xp_on_the_pass(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, (challenge,) = make_competency(db, challenge_xp=[50])
        assert _submit(client, auth_headers, challenge.id, "failed").json()["xp_awarded"] == 0
        assert _xp(client, auth_headers) == 0
        assert _submit(client, auth_headers, challenge.id, "passed").json()["xp_awarded"] == 50
        assert _xp(client, auth_headers) == 50

    def test_pass_fail_pass_only_pays_once(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, (challenge,) = make_competency(db, challenge_xp=[40])
        assert _submit(client, auth_headers, challenge.id, "passed").json()["xp_awarded"] == 40
        assert _submit(client, auth_headers, challenge.id, "failed").json()["xp_awarded"] == 0
        assert _submit(client, auth_headers, challenge.id, "passed").json()["xp_awarded"] == 0
        assert _xp(client, auth_headers) == 40

    def test_each_challenge_pays_its_own_xp(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, challenges = make_competency(db, challenge_xp=[10, 20, 30])
        for challenge in challenges:
            _submit(client, auth_headers, challenge.id, "passed")
        assert _xp(client, auth_headers) == 60

    def test_xp_is_per_user(self, client: TestClient, auth_headers: dict[str, str], db: Session):
        _, (challenge,) = make_competency(db, challenge_xp=[50])
        other_headers, _ = register(client, "other@example.com")
        assert _submit(client, auth_headers, challenge.id, "passed").json()["xp_awarded"] == 50
        assert _submit(client, other_headers, challenge.id, "passed").json()["xp_awarded"] == 50

    def test_unknown_challenge_is_404(self, client: TestClient, auth_headers: dict[str, str]):
        assert _submit(client, auth_headers, uuid.uuid4(), "passed").status_code == 404

    def test_invalid_status_is_422(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, (challenge,) = make_competency(db)
        assert _submit(client, auth_headers, challenge.id, "maybe").status_code == 422

    def test_submission_notes_are_returned(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        _, (challenge,) = make_competency(db)
        response = client.post(
            f"{API}/challenges/{challenge.id}/submissions",
            headers=auth_headers,
            json={"status": "failed", "notes": "needs work"},
        )
        assert response.json()["notes"] == "needs work"
        assert response.json()["status"] == "failed"


class TestChallengeMastery:
    def test_passing_raises_practice_share_of_mastery(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, challenges = make_competency(db, challenge_xp=[10, 10])
        _submit(client, auth_headers, challenges[0].id, "passed")
        assert _mastery(client, auth_headers, competency) == pytest.approx(17.5)  # 35 * 1/2
        _submit(client, auth_headers, challenges[1].id, "passed")
        assert _mastery(client, auth_headers, competency) == pytest.approx(35.0)

    def test_failed_submission_leaves_mastery_at_zero(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, (challenge,) = make_competency(db)
        _submit(client, auth_headers, challenge.id, "failed")
        assert _mastery(client, auth_headers, competency) == 0.0

    def test_repeated_passes_do_not_inflate_mastery(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, challenges = make_competency(db, challenge_xp=[10, 10])
        for _ in range(3):
            _submit(client, auth_headers, challenges[0].id, "passed")
        assert _mastery(client, auth_headers, competency) == pytest.approx(17.5)

    def test_mastery_combines_with_study_time(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, (challenge,) = make_competency(db)
        client.post(
            f"{API}/study-sessions",
            headers=auth_headers,
            json={"competency_id": str(competency.id), "duration_minutes": 120},
        )
        _submit(client, auth_headers, challenge.id, "passed")
        assert _mastery(client, auth_headers, competency) == pytest.approx(75.0)  # 40 + 35
