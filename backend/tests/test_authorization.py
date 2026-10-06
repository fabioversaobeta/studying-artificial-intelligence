"""Authentication gating and cross-user isolation.

Part 1: protected endpoints reject missing / malformed / forged / expired /
wrong-type tokens. Part 2: user B can neither read nor change user A's data.
"""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token
from app.models.learning import Review
from app.models.user import User
from tests.factories import API, make_competency, register

_ID = uuid.uuid4()

PROTECTED_ENDPOINTS = [
    ("GET", "/auth/me", None),
    ("GET", "/dashboard", None),
    ("GET", "/goals", None),
    ("POST", "/goals", {"title": "x"}),
    ("PATCH", f"/goals/{_ID}/status", {"status": "achieved"}),
    ("GET", "/study-sessions", None),
    ("POST", "/study-sessions", {"duration_minutes": 10}),
    ("GET", "/reviews/due", None),
    ("POST", f"/reviews/{_ID}/recall", {"quality": 3}),
    ("POST", f"/challenges/{_ID}/submissions", {"status": "passed"}),
    ("GET", "/gamification/profile", None),
    ("GET", "/gamification/achievements", None),
    ("GET", "/gamification/quests", None),
    ("GET", "/subjects", None),
]
ENDPOINT_IDS = [f"{m} {p}" for m, p, _ in PROTECTED_ENDPOINTS]


def _call(client: TestClient, method: str, path: str, body, headers: dict[str, str]):
    return client.request(method, f"{API}{path}", json=body, headers=headers)


def _forged_token(subject: uuid.UUID, token_type: str = "access", **overrides) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        **overrides,
    }
    return jwt.encode(payload, get_settings().secret_key, algorithm=get_settings().jwt_algorithm)


@pytest.mark.parametrize(("method", "path", "body"), PROTECTED_ENDPOINTS, ids=ENDPOINT_IDS)
class TestProtectedEndpointsRejectBadTokens:
    def test_missing_token(self, client: TestClient, method: str, path: str, body):
        assert _call(client, method, path, body, {}).status_code == 401

    def test_garbage_token(self, client: TestClient, method: str, path: str, body):
        headers = {"Authorization": "Bearer not-a-jwt"}
        assert _call(client, method, path, body, headers).status_code == 401

    def test_refresh_token_used_as_access(
        self, client: TestClient, db: Session, method: str, path: str, body
    ):
        _, user_id = register(client, "victim@example.com")
        headers = {"Authorization": f"Bearer {create_refresh_token(user_id)}"}
        assert _call(client, method, path, body, headers).status_code == 401


class TestTokenValidation:
    def test_non_bearer_scheme_is_rejected(self, client: TestClient):
        response = client.get(f"{API}/auth/me", headers={"Authorization": "Basic dXNlcjpwYXNz"})
        assert response.status_code == 401

    def test_token_signed_with_other_secret_is_rejected(self, client: TestClient):
        _, user_id = register(client, "victim@example.com")
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        }
        forged = jwt.encode(payload, "some-other-secret-key-0123456789abcdef", algorithm="HS256")
        response = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {forged}"})
        assert response.status_code == 401

    def test_unsigned_alg_none_token_is_rejected(self, client: TestClient):
        _, user_id = register(client, "victim@example.com")
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        }
        unsigned = jwt.encode(payload, key="", algorithm="none")
        response = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {unsigned}"})
        assert response.status_code == 401

    def test_expired_token_is_rejected(self, client: TestClient):
        _, user_id = register(client, "victim@example.com")
        expired = _forged_token(user_id, exp=datetime.now(UTC) - timedelta(minutes=1))
        response = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {expired}"})
        assert response.status_code == 401

    def test_token_for_unknown_user_is_rejected(self, client: TestClient):
        token = create_access_token(uuid.uuid4())
        response = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_token_with_non_uuid_subject_is_rejected(self, client: TestClient):
        token = _forged_token(uuid.uuid4(), sub="not-a-uuid")
        response = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_token_without_type_claim_is_rejected(self, client: TestClient):
        _, user_id = register(client, "victim@example.com")
        payload = {"sub": str(user_id), "exp": datetime.now(UTC) + timedelta(minutes=5)}
        token = jwt.encode(
            payload, get_settings().secret_key, algorithm=get_settings().jwt_algorithm
        )
        response = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401

    def test_deactivated_user_loses_access(self, client: TestClient, db: Session):
        headers, user_id = register(client, "leaving@example.com")
        user = db.get(User, user_id)
        assert user is not None
        user.is_active = False
        db.commit()
        assert client.get(f"{API}/auth/me", headers=headers).status_code == 401

    def test_access_token_cannot_be_used_to_refresh(self, client: TestClient):
        _, user_id = register(client, "victim@example.com")
        response = client.post(
            f"{API}/auth/refresh", json={"refresh_token": create_access_token(user_id)}
        )
        assert response.status_code == 401

    def test_valid_token_is_accepted(self, client: TestClient, auth_headers: dict[str, str]):
        assert client.get(f"{API}/auth/me", headers=auth_headers).status_code == 200


@pytest.fixture
def alice(client: TestClient, db: Session) -> dict:
    """User A with a goal, study sessions, a passed challenge, a review and XP."""
    headers, user_id = register(client, "alice@example.com")
    competency, (challenge,) = make_competency(db, challenge_xp=[50])
    goal = client.post(f"{API}/goals", headers=headers, json={"title": "Alice goal"}).json()
    session = client.post(
        f"{API}/study-sessions",
        headers=headers,
        json={"competency_id": str(competency.id), "duration_minutes": 60, "notes": "private"},
    ).json()
    submission = client.post(
        f"{API}/challenges/{challenge.id}/submissions",
        headers=headers,
        json={"status": "passed", "notes": "private"},
    ).json()
    review = db.execute(select(Review).where(Review.user_id == user_id)).scalar_one()
    review.due_at = datetime.now(UTC) - timedelta(days=1)
    db.commit()
    return {
        "headers": headers,
        "id": user_id,
        "competency": competency,
        "challenge": challenge,
        "goal": goal,
        "session": session,
        "submission": submission,
    }


@pytest.fixture
def bob(client: TestClient) -> dict[str, str]:
    headers, _ = register(client, "bob@example.com")
    return headers


class TestCrossUserIsolation:
    def test_goals_are_not_listed_to_other_users(
        self, client: TestClient, alice: dict, bob: dict[str, str]
    ):
        assert client.get(f"{API}/goals", headers=bob).json() == []
        assert len(client.get(f"{API}/goals", headers=alice["headers"]).json()) == 1

    def test_goal_status_cannot_be_changed_by_other_users(
        self, client: TestClient, alice: dict, bob: dict[str, str]
    ):
        goal_id = alice["goal"]["id"]
        response = client.patch(
            f"{API}/goals/{goal_id}/status", headers=bob, json={"status": "archived"}
        )
        assert response.status_code == 404
        goals = client.get(f"{API}/goals", headers=alice["headers"]).json()
        assert goals[0]["status"] == "active"

    def test_study_sessions_are_not_listed_to_other_users(
        self, client: TestClient, alice: dict, bob: dict[str, str]
    ):
        assert client.get(f"{API}/study-sessions", headers=bob).json() == []
        mine = client.get(f"{API}/study-sessions", headers=alice["headers"]).json()
        assert [s["id"] for s in mine] == [alice["session"]["id"]]

    def test_reviews_are_not_listed_to_other_users(
        self, client: TestClient, alice: dict, bob: dict[str, str]
    ):
        assert client.get(f"{API}/reviews/due", headers=bob).json() == []
        assert len(client.get(f"{API}/reviews/due", headers=alice["headers"]).json()) == 1

    def test_other_user_cannot_recall_someone_elses_review(
        self, client: TestClient, db: Session, alice: dict, bob: dict[str, str]
    ):
        response = client.post(
            f"{API}/reviews/{alice['competency'].id}/recall", headers=bob, json={"quality": 5}
        )
        assert response.status_code == 404
        review = db.execute(select(Review).where(Review.user_id == alice["id"])).scalar_one()
        db.refresh(review)
        assert review.repetitions == 0
        assert review.last_reviewed_at is None

    def test_gamification_data_is_per_user(
        self, client: TestClient, alice: dict, bob: dict[str, str]
    ):
        assert (
            client.get(f"{API}/gamification/profile", headers=alice["headers"]).json()["total_xp"]
            == 80
        )  # 30 study + 50 challenge
        profile = client.get(f"{API}/gamification/profile", headers=bob).json()
        assert profile["total_xp"] == 0
        assert profile["current_streak_days"] == 0
        assert all(
            not a["earned"]
            for a in client.get(f"{API}/gamification/achievements", headers=bob).json()
        )

    def test_dashboard_does_not_leak_other_users_data(
        self, client: TestClient, alice: dict, bob: dict[str, str]
    ):
        data = client.get(f"{API}/dashboard", headers=bob).json()
        assert data["total_xp"] == 0
        assert data["active_goals"] == []
        assert data["recent_study_sessions"] == []
        assert data["weakest_competencies"] == []
        assert data["due_review_count"] == 0

    def test_subject_progress_is_per_user(
        self, client: TestClient, alice: dict, bob: dict[str, str]
    ):
        subject_id = alice["competency"].subject_id
        bob_view = client.get(f"{API}/subjects/{subject_id}", headers=bob).json()
        assert bob_view["competencies"][0]["mastery_score"] == 0.0
        alice_view = client.get(f"{API}/subjects/{subject_id}", headers=alice["headers"]).json()
        assert alice_view["competencies"][0]["mastery_score"] > 0

    def test_challenge_submission_by_other_user_does_not_touch_owner(
        self, client: TestClient, alice: dict, bob: dict[str, str]
    ):
        challenge_id = alice["challenge"].id
        response = client.post(
            f"{API}/challenges/{challenge_id}/submissions",
            headers=bob,
            json={"status": "failed", "notes": "bob"},
        )
        assert response.status_code == 201
        assert response.json()["id"] != alice["submission"]["id"]
        # Alice's pass, XP and mastery are unaffected by Bob's failed attempt.
        profile = client.get(f"{API}/gamification/profile", headers=alice["headers"]).json()
        assert profile["total_xp"] == 80
        detail = client.get(
            f"{API}/subjects/{alice['competency'].subject_id}", headers=alice["headers"]
        ).json()
        assert detail["competencies"][0]["mastery_score"] == pytest.approx(20.0 + 35.0)

    def test_user_id_cannot_be_injected_through_request_bodies(
        self, client: TestClient, alice: dict, bob: dict[str, str]
    ):
        response = client.post(
            f"{API}/goals",
            headers=bob,
            json={"title": "sneaky", "user_id": str(alice["id"])},
        )
        assert response.status_code == 201
        titles = [g["title"] for g in client.get(f"{API}/goals", headers=alice["headers"]).json()]
        assert titles == ["Alice goal"]
