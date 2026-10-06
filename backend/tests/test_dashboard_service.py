"""dashboard_service: the aggregate read model for the home screen."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.learning import Review
from tests.factories import API, make_competency, register


def _dashboard(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.get(f"{API}/dashboard", headers=headers)
    assert response.status_code == 200
    return response.json()


def _study(client: TestClient, headers: dict[str, str], competency, minutes: int):
    response = client.post(
        f"{API}/study-sessions",
        headers=headers,
        json={"competency_id": str(competency.id), "duration_minutes": minutes},
    )
    assert response.status_code == 201


def test_fresh_user_has_empty_dashboard(client: TestClient, auth_headers: dict[str, str]):
    data = _dashboard(client, auth_headers)
    assert data["level"] == 1
    assert data["total_xp"] == 0
    assert data["xp_to_next_level"] == 100
    assert data["current_streak_days"] == 0
    assert data["longest_streak_days"] == 0
    assert data["active_goals"] == []
    assert data["due_review_count"] == 0
    assert data["weakest_competencies"] == []
    assert data["recent_study_sessions"] == []


def test_xp_level_and_streak_reflect_activity(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    competency, _ = make_competency(db)
    _study(client, auth_headers, competency, 120)  # 60 XP
    _study(client, auth_headers, competency, 120)  # 120 XP -> level 2
    data = _dashboard(client, auth_headers)
    assert data["total_xp"] == 120
    assert data["level"] == 2
    assert data["xp_to_next_level"] == 300 - 120
    assert data["current_streak_days"] == 1


def test_only_active_goals_are_listed(client: TestClient, auth_headers: dict[str, str]):
    keep = client.post(f"{API}/goals", headers=auth_headers, json={"title": "Keep"}).json()
    done = client.post(f"{API}/goals", headers=auth_headers, json={"title": "Done"}).json()
    client.patch(
        f"{API}/goals/{done['id']}/status", headers=auth_headers, json={"status": "achieved"}
    )
    goals = _dashboard(client, auth_headers)["active_goals"]
    assert [g["id"] for g in goals] == [keep["id"]]


def test_due_review_count(client: TestClient, auth_headers: dict[str, str], db: Session):
    competency, _ = make_competency(db)
    _study(client, auth_headers, competency, 10)
    assert _dashboard(client, auth_headers)["due_review_count"] == 0
    review = db.execute(select(Review)).scalar_one()
    review.due_at = datetime.now(UTC) - timedelta(hours=1)
    db.commit()
    assert _dashboard(client, auth_headers)["due_review_count"] == 1


def test_weakest_competencies_sorted_ascending_and_capped_at_five(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    minutes_by_competency = {}
    for minutes in (120, 60, 12, 24, 36, 48, 72):
        competency, _ = make_competency(db)
        _study(client, auth_headers, competency, minutes)
        minutes_by_competency[str(competency.id)] = minutes

    weakest = _dashboard(client, auth_headers)["weakest_competencies"]
    assert len(weakest) == 5
    scores = [w["score"] for w in weakest]
    assert scores == sorted(scores)
    assert scores[0] == pytest.approx(4.0)  # 12 minutes -> 12/120 * 40
    returned_minutes = [minutes_by_competency[w["competency_id"]] for w in weakest]
    assert returned_minutes == [12, 24, 36, 48, 60]


def test_recent_sessions_are_capped_at_five_newest_first(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    competency, _ = make_competency(db)
    base = datetime.now(UTC) - timedelta(days=10)
    for index in range(7):
        client.post(
            f"{API}/study-sessions",
            headers=auth_headers,
            json={
                "competency_id": str(competency.id),
                "duration_minutes": 10 + index,
                "occurred_at": (base + timedelta(days=index)).isoformat(),
            },
        )
    sessions = _dashboard(client, auth_headers)["recent_study_sessions"]
    assert [s["duration_minutes"] for s in sessions] == [16, 15, 14, 13, 12]


def test_dashboard_is_scoped_to_the_requesting_user(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    competency, _ = make_competency(db)
    _study(client, auth_headers, competency, 60)
    client.post(f"{API}/goals", headers=auth_headers, json={"title": "Mine"})

    other_headers, _ = register(client, "other@example.com")
    data = _dashboard(client, other_headers)
    assert data["total_xp"] == 0
    assert data["active_goals"] == []
    assert data["recent_study_sessions"] == []
    assert data["weakest_competencies"] == []
