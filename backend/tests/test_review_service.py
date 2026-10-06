"""review_service (SM-2) via the API: due list, recall, intervals, XP, mastery."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.learning import Competency, Review
from tests.factories import API, make_competency


@pytest.fixture
def studied(client: TestClient, auth_headers: dict[str, str], db: Session) -> Competency:
    """A competency the user has studied once, so a Review row exists."""
    competency, _ = make_competency(db)
    response = client.post(
        f"{API}/study-sessions",
        headers=auth_headers,
        json={"competency_id": str(competency.id), "duration_minutes": 60},
    )
    assert response.status_code == 201
    return competency


def _recall(client: TestClient, headers: dict[str, str], competency: Competency, quality: int):
    return client.post(
        f"{API}/reviews/{competency.id}/recall", headers=headers, json={"quality": quality}
    )


def _make_due(db: Session, competency: Competency, days_ago: int = 1) -> Review:
    review = db.execute(select(Review).where(Review.competency_id == competency.id)).scalar_one()
    review.due_at = datetime.now(UTC) - timedelta(days=days_ago)
    db.commit()
    return review


class TestDueList:
    def test_empty_before_any_study(self, client: TestClient, auth_headers: dict[str, str]):
        assert client.get(f"{API}/reviews/due", headers=auth_headers).json() == []

    def test_first_study_schedules_review_for_tomorrow_so_not_due_yet(
        self, client: TestClient, auth_headers: dict[str, str], db: Session, studied: Competency
    ):
        assert client.get(f"{API}/reviews/due", headers=auth_headers).json() == []
        review = db.execute(select(Review)).scalar_one()
        delta = review.due_at - datetime.now(UTC)
        assert timedelta(hours=23) < delta <= timedelta(days=1)

    def test_overdue_review_is_listed(
        self, client: TestClient, auth_headers: dict[str, str], db: Session, studied: Competency
    ):
        _make_due(db, studied)
        due = client.get(f"{API}/reviews/due", headers=auth_headers).json()
        assert [d["competency_id"] for d in due] == [str(studied.id)]

    def test_due_review_includes_competency_and_subject_context(
        self, client: TestClient, auth_headers: dict[str, str], db: Session, studied: Competency
    ):
        _make_due(db, studied)
        (item,) = client.get(f"{API}/reviews/due", headers=auth_headers).json()
        assert item["competency_name"] == studied.name
        assert item["subject_id"] == str(studied.subject_id)
        assert item["subject_name"] == studied.subject.name
        # existing fields are untouched (additive contract)
        assert item["competency_id"] == str(studied.id)
        assert "interval_days" in item and "due_at" in item

    def test_due_list_query_count_does_not_grow_with_reviews(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        from sqlalchemy import event

        def run() -> int:
            count = 0

            def _count(*_args) -> None:
                nonlocal count
                count += 1

            bind = db.get_bind()
            event.listen(bind, "before_cursor_execute", _count)
            try:
                assert client.get(f"{API}/reviews/due", headers=auth_headers).status_code == 200
            finally:
                event.remove(bind, "before_cursor_execute", _count)
            return count

        def add(n: int) -> None:
            for _ in range(n):
                comp, _ = make_competency(db)
                client.post(
                    f"{API}/study-sessions",
                    headers=auth_headers,
                    json={"competency_id": str(comp.id), "duration_minutes": 5},
                )
                _make_due(db, comp)

        add(1)
        few = run()
        add(5)
        assert run() == few

    def test_due_reviews_are_ordered_oldest_first(
        self, client: TestClient, auth_headers: dict[str, str], db: Session, studied: Competency
    ):
        second, _ = make_competency(db)
        client.post(
            f"{API}/study-sessions",
            headers=auth_headers,
            json={"competency_id": str(second.id), "duration_minutes": 10},
        )
        _make_due(db, studied, days_ago=1)
        _make_due(db, second, days_ago=5)
        due = client.get(f"{API}/reviews/due", headers=auth_headers).json()
        assert [d["competency_id"] for d in due] == [str(second.id), str(studied.id)]

    def test_studying_again_does_not_reset_schedule(
        self, client: TestClient, auth_headers: dict[str, str], db: Session, studied: Competency
    ):
        _make_due(db, studied)
        client.post(
            f"{API}/study-sessions",
            headers=auth_headers,
            json={"competency_id": str(studied.id), "duration_minutes": 10},
        )
        assert len(client.get(f"{API}/reviews/due", headers=auth_headers).json()) == 1

    def test_study_without_competency_schedules_nothing(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        client.post(f"{API}/study-sessions", headers=auth_headers, json={"duration_minutes": 30})
        assert db.execute(select(Review)).first() is None


class TestRecall:
    def test_successive_perfect_recalls_grow_the_interval(
        self, client: TestClient, auth_headers: dict[str, str], studied: Competency
    ):
        first = _recall(client, auth_headers, studied, 5).json()
        assert (first["interval_days"], first["repetitions"]) == (1, 1)
        assert first["ease_factor"] == pytest.approx(2.6)

        second = _recall(client, auth_headers, studied, 5).json()
        assert (second["interval_days"], second["repetitions"]) == (6, 2)
        assert second["ease_factor"] == pytest.approx(2.7)

        third = _recall(client, auth_headers, studied, 5).json()
        assert third["interval_days"] == 16  # round(6 * 2.7)
        assert third["repetitions"] == 3

    @pytest.mark.parametrize("quality", [0, 1, 2])
    def test_failed_recall_resets_progress(
        self, client: TestClient, auth_headers: dict[str, str], studied: Competency, quality: int
    ):
        _recall(client, auth_headers, studied, 5)
        _recall(client, auth_headers, studied, 5)
        failed = _recall(client, auth_headers, studied, quality).json()
        assert failed["interval_days"] == 1
        assert failed["repetitions"] == 0
        assert failed["ease_factor"] == pytest.approx(2.7)  # ease is left untouched
        assert failed["last_recall_quality"] == quality

    def test_quality_four_keeps_ease_and_three_lowers_it(
        self, client: TestClient, auth_headers: dict[str, str], studied: Competency
    ):
        assert _recall(client, auth_headers, studied, 4).json()["ease_factor"] == pytest.approx(2.5)
        # 2.5 + (0.1 - 2 * (0.08 + 2 * 0.02)) = 2.36
        assert _recall(client, auth_headers, studied, 3).json()["ease_factor"] == pytest.approx(
            2.36
        )

    def test_ease_factor_never_drops_below_floor(
        self, client: TestClient, auth_headers: dict[str, str], studied: Competency
    ):
        for _ in range(15):
            review = _recall(client, auth_headers, studied, 3).json()
        assert review["ease_factor"] == pytest.approx(1.3)

    def test_recall_reschedules_due_date_from_now(
        self, client: TestClient, auth_headers: dict[str, str], db: Session, studied: Competency
    ):
        _make_due(db, studied)
        _recall(client, auth_headers, studied, 5)
        _recall(client, auth_headers, studied, 5)  # interval is now 6 days
        review = db.execute(select(Review)).scalar_one()
        delta = review.due_at - datetime.now(UTC)
        assert timedelta(days=5, hours=23) < delta <= timedelta(days=6)
        assert review.last_reviewed_at is not None
        assert client.get(f"{API}/reviews/due", headers={**auth_headers}).json() == []

    def test_recall_awards_review_xp_every_time(
        self, client: TestClient, auth_headers: dict[str, str], studied: Competency
    ):
        before = client.get(f"{API}/gamification/profile", headers=auth_headers).json()["total_xp"]
        _recall(client, auth_headers, studied, 4)
        _recall(client, auth_headers, studied, 0)
        after = client.get(f"{API}/gamification/profile", headers=auth_headers).json()["total_xp"]
        assert after - before == 30

    def test_recall_updates_mastery_retention_component(
        self, client: TestClient, auth_headers: dict[str, str], studied: Competency
    ):
        def mastery() -> float:
            detail = client.get(f"{API}/subjects/{studied.subject_id}", headers=auth_headers).json()
            return detail["competencies"][0]["mastery_score"]

        assert mastery() == pytest.approx(20.0)  # engagement only
        _recall(client, auth_headers, studied, 5)
        assert mastery() == pytest.approx(45.0)  # + 25 retention
        _recall(client, auth_headers, studied, 0)
        assert mastery() == pytest.approx(20.0)

    def test_recall_without_scheduled_review_is_404(
        self, client: TestClient, auth_headers: dict[str, str], db: Session
    ):
        competency, _ = make_competency(db)
        assert _recall(client, auth_headers, competency, 5).status_code == 404

    def test_recall_for_unknown_competency_is_404(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        response = client.post(
            f"{API}/reviews/{uuid.uuid4()}/recall", headers=auth_headers, json={"quality": 3}
        )
        assert response.status_code == 404

    @pytest.mark.parametrize("quality", [-1, 6, 100])
    def test_quality_out_of_range_is_422(
        self, client: TestClient, auth_headers: dict[str, str], studied: Competency, quality: int
    ):
        assert _recall(client, auth_headers, studied, quality).status_code == 422
