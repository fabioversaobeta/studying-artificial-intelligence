"""Characterization + query-count tests for the skill-tree read endpoints.

`/subjects` and `/subjects/{id}` derive per-competency state from mastery,
study activity and prerequisites. These tests pin the exact JSON output (so
refactors cannot change the API contract) and assert that the number of SQL
queries does not grow with the number of competencies (no N+1).
"""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models.learning import (
    Competency,
    CompetencyPrerequisite,
    DifficultyLevel,
    Mastery,
    StudySession,
    Subject,
)


def _user_id(client: TestClient, headers: dict[str, str]) -> uuid.UUID:
    return uuid.UUID(client.get("/api/v1/auth/me", headers=headers).json()["id"])


def _add_competency(db: Session, subject: Subject, name: str, order: int) -> Competency:
    comp = Competency(
        subject_id=subject.id,
        name=name,
        slug=name.lower().replace(" ", "-"),
        difficulty=DifficultyLevel.BEGINNER,
        sort_order=order,
    )
    db.add(comp)
    db.flush()
    return comp


def _mastery(db: Session, user_id: uuid.UUID, comp: Competency, score: float) -> None:
    db.add(
        Mastery(user_id=user_id, competency_id=comp.id, score=score, updated_at=datetime.now(UTC))
    )


def _study(db: Session, user_id: uuid.UUID, comp: Competency, minutes: int) -> None:
    now = datetime.now(UTC)
    db.add(
        StudySession(
            user_id=user_id,
            competency_id=comp.id,
            duration_minutes=minutes,
            occurred_at=now,
            created_at=now,
        )
    )


def _prereq(db: Session, comp: Competency, prereq: Competency) -> None:
    db.add(CompetencyPrerequisite(competency_id=comp.id, prerequisite_id=prereq.id))


def _build_scenario(db: Session, user_id: uuid.UUID) -> tuple[Subject, Subject]:
    main = Subject(name="Main Subject", slug="main-subject", sort_order=1)
    other = Subject(name="Other Subject", slug="other-subject", sort_order=2)
    db.add_all([main, other])
    db.flush()

    c = [_add_competency(db, main, f"Comp {i}", i) for i in range(6)]
    o = _add_competency(db, other, "Other Comp", 0)

    _prereq(db, c[1], c[0])
    _prereq(db, c[2], c[0])
    _prereq(db, c[3], c[1])
    _prereq(db, c[4], c[0])
    _prereq(db, c[4], c[2])

    _mastery(db, user_id, c[0], 90.0)  # mastered
    _mastery(db, user_id, c[1], 40.0)  # learning (has mastery + activity)
    _study(db, user_id, c[1], 30)
    _study(db, user_id, c[1], 15)
    _study(db, user_id, c[5], 10)  # learning without mastery row
    _mastery(db, user_id, o, 50.0)
    db.commit()
    return main, other


def test_subject_detail_characterization(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    main, _ = _build_scenario(db, _user_id(client, auth_headers))

    body = client.get(f"/api/v1/subjects/{main.id}", headers=auth_headers).json()

    assert body["subject"]["name"] == "Main Subject"
    got = [(c["competency"]["name"], c["mastery_score"], c["state"]) for c in body["competencies"]]
    assert got == [
        ("Comp 0", 90.0, "mastered"),
        ("Comp 1", 40.0, "learning"),
        ("Comp 2", 0.0, "available"),  # prerequisite c0 mastered
        ("Comp 3", 0.0, "locked"),  # prerequisite c1 only 40
        ("Comp 4", 0.0, "locked"),  # c0 mastered but c2 has no mastery
        ("Comp 5", 0.0, "learning"),  # activity, no mastery row
    ]
    assert set(body["competencies"][0]["competency"]) == {
        "id",
        "subject_id",
        "name",
        "slug",
        "description",
        "difficulty",
        "sort_order",
    }


def test_list_subjects_characterization(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    _build_scenario(db, _user_id(client, auth_headers))

    body = client.get("/api/v1/subjects", headers=auth_headers).json()

    got = [(s["subject"]["name"], s["competency_count"], s["average_mastery"]) for s in body]
    assert got == [
        ("Main Subject", 6, round((90.0 + 40.0) / 6, 2)),
        ("Other Subject", 1, 50.0),
    ]


class _QueryCounter:
    def __init__(self, db: Session) -> None:
        self.bind = db.get_bind()
        self.count = 0

    def _on_execute(self, *_args: object) -> None:
        self.count += 1

    def __enter__(self) -> "_QueryCounter":
        event.listen(self.bind, "before_cursor_execute", self._on_execute)
        return self

    def __exit__(self, *_exc: object) -> None:
        event.remove(self.bind, "before_cursor_execute", self._on_execute)


def _add_chain(
    db: Session, user_id: uuid.UUID, subject: Subject, start: int, count: int, score: float
) -> None:
    prev: Competency | None = None
    for i in range(start, start + count):
        comp = _add_competency(db, subject, f"{subject.slug} C{i}", i)
        if prev is not None:
            _prereq(db, comp, prev)
        _mastery(db, user_id, comp, score)
        _study(db, user_id, comp, 10)
        prev = comp


def _add_subject(db: Session, index: int) -> Subject:
    subject = Subject(name=f"S{index}", slug=f"s{index}", sort_order=index)
    db.add(subject)
    db.flush()
    return subject


@pytest.mark.parametrize("path", ["detail", "list"])
def test_query_count_does_not_grow_with_competencies(
    client: TestClient, auth_headers: dict[str, str], db: Session, path: str
):
    user_id = _user_id(client, auth_headers)
    first = _add_subject(db, 0)
    _add_chain(db, user_id, first, 0, 3, 85.0)
    _add_chain(db, user_id, _add_subject(db, 1), 0, 3, 20.0)
    db.commit()
    url = f"/api/v1/subjects/{first.id}" if path == "detail" else "/api/v1/subjects"

    # Warm-up request: commits in the test expire identity-map objects (user,
    # subject), which would add one-off refresh queries to the measured request.
    client.get(url, headers=auth_headers)
    with _QueryCounter(db) as small:
        assert client.get(url, headers=auth_headers).status_code == 200

    # Grow the data set substantially: more subjects and many more competencies.
    _add_chain(db, user_id, first, 3, 12, 10.0)
    for s in range(2, 6):
        _add_chain(db, user_id, _add_subject(db, s), 0, 10, 85.0)
    db.commit()

    client.get(url, headers=auth_headers)
    with _QueryCounter(db) as large:
        assert client.get(url, headers=auth_headers).status_code == 200

    assert large.count == small.count, (small.count, large.count)
