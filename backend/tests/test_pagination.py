"""limit/offset pagination + X-Total-Count on user-scoped list endpoints."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.learning import Review
from tests.factories import API, make_competency, register


def _seed_sessions(client: TestClient, headers: dict[str, str], db: Session, n: int) -> None:
    for i in range(n):
        r = client.post(
            f"{API}/study-sessions",
            headers=headers,
            json={"duration_minutes": 10 + i, "occurred_at": f"2026-01-{i + 1:02d}T10:00:00Z"},
        )
        assert r.status_code == 201


def _seed_goals(client: TestClient, headers: dict[str, str], db: Session, n: int) -> None:
    for i in range(n):
        r = client.post(f"{API}/goals", headers=headers, json={"title": f"Goal {i}"})
        assert r.status_code == 201


def _seed_reviews(client: TestClient, headers: dict[str, str], db: Session, n: int) -> None:
    for i in range(n):
        competency, _ = make_competency(db)
        client.post(
            f"{API}/study-sessions",
            headers=headers,
            json={"competency_id": str(competency.id), "duration_minutes": 10},
        )
        db.execute(
            update(Review)
            .where(Review.competency_id == competency.id)
            .values(due_at=datetime.now(UTC) - timedelta(days=n - i))
        )
    db.flush()


SEEDERS = {
    "study-sessions": _seed_sessions,
    "goals": _seed_goals,
    "reviews/due": _seed_reviews,
}


@pytest.mark.parametrize("path", list(SEEDERS))
class TestPagination:
    def test_default_returns_all_with_total_header(
        self, path: str, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        SEEDERS[path](client, auth_headers, db, 5)
        r = client.get(f"{API}/{path}", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) == 5
        assert r.headers["X-Total-Count"] == "5"

    def test_limit_and_offset_slice_without_overlap(
        self, path: str, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        SEEDERS[path](client, auth_headers, db, 5)
        full = [x["id"] for x in client.get(f"{API}/{path}", headers=auth_headers).json()]
        first = client.get(f"{API}/{path}?limit=2&offset=0", headers=auth_headers)
        second = client.get(f"{API}/{path}?limit=2&offset=2", headers=auth_headers)
        last = client.get(f"{API}/{path}?limit=2&offset=4", headers=auth_headers)
        assert [x["id"] for x in first.json()] == full[0:2]
        assert [x["id"] for x in second.json()] == full[2:4]
        assert [x["id"] for x in last.json()] == full[4:5]
        for r in (first, second, last):
            assert r.headers["X-Total-Count"] == "5"

    def test_offset_past_end_is_empty_but_total_kept(
        self, path: str, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        SEEDERS[path](client, auth_headers, db, 3)
        r = client.get(f"{API}/{path}?offset=10", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []
        assert r.headers["X-Total-Count"] == "3"

    @pytest.mark.parametrize("query", ["limit=0", "limit=201", "limit=-1", "offset=-1", "limit=x"])
    def test_invalid_params_are_422(
        self, path: str, query: str, client: TestClient, auth_headers: dict[str, str]
    ):
        assert client.get(f"{API}/{path}?{query}", headers=auth_headers).status_code == 422

    def test_max_limit_accepted(self, path: str, client: TestClient, auth_headers: dict[str, str]):
        r = client.get(f"{API}/{path}?limit=200", headers=auth_headers)
        assert r.status_code == 200
        assert r.headers["X-Total-Count"] == "0"

    def test_total_counts_only_own_rows(
        self, path: str, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        SEEDERS[path](client, auth_headers, db, 2)
        headers, _ = register(client, "other@example.com")
        r = client.get(f"{API}/{path}", headers=headers)
        assert r.json() == []
        assert r.headers["X-Total-Count"] == "0"


def test_cors_exposes_total_count_header(client: TestClient):
    r = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert "x-total-count" in r.headers.get("access-control-expose-headers", "").lower()
