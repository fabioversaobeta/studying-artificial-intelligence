"""Per-step mastery/state and aggregate progress on learning paths."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.learning import LearningPath, LearningPathItem, Subject
from tests.test_learning_state_queries import (
    _add_competency,
    _mastery,
    _prereq,
    _QueryCounter,
    _study,
    _user_id,
)


def _build_path(db: Session, user_id: uuid.UUID, slug: str = "p", steps: int = 4) -> LearningPath:
    subject = Subject(name=f"Subj {slug}", slug=f"subj-{slug}")
    db.add(subject)
    db.flush()
    comps = [_add_competency(db, subject, f"{slug} step {i}", i) for i in range(steps)]
    if steps >= 4:
        _prereq(db, comps[1], comps[0])
        _prereq(db, comps[3], comps[2])
        _mastery(db, user_id, comps[0], 90.0)  # mastered
        _mastery(db, user_id, comps[1], 40.0)  # learning
        _study(db, user_id, comps[1], 20)
        # comps[2]: no prereq, no activity -> available; comps[3]: prereq unmet -> locked
    path = LearningPath(title=f"Path {slug}", slug=slug, sort_order=0)
    db.add(path)
    db.flush()
    for i, comp in enumerate(comps):
        db.add(LearningPathItem(learning_path_id=path.id, competency_id=comp.id, sort_order=i))
    db.commit()
    return path


def test_detail_exposes_step_progress_and_summary(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    _build_path(db, _user_id(client, auth_headers))

    body = client.get("/api/v1/learning-paths/p", headers=auth_headers).json()

    assert [(i["mastery_score"], i["state"]) for i in body["items"]] == [
        (90.0, "mastered"),
        (40.0, "learning"),
        (0.0, "available"),
        (0.0, "locked"),
    ]
    assert body["progress"] == {
        "total_steps": 4,
        "mastered_steps": 1,
        "average_mastery": 32.5,
    }
    # existing fields untouched
    assert body["items"][0]["competency"]["name"] == "p step 0"
    assert body["items"][0]["sort_order"] == 0
    assert body["slug"] == "p"


def test_list_includes_aggregate_progress(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    _build_path(db, _user_id(client, auth_headers))

    (path,) = client.get("/api/v1/learning-paths", headers=auth_headers).json()

    assert path["progress"]["mastered_steps"] == 1
    assert path["progress"]["total_steps"] == 4


def test_anonymous_request_still_works_without_progress(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    _build_path(db, _user_id(client, auth_headers))

    body = client.get("/api/v1/learning-paths/p").json()

    assert body["progress"] is None
    assert body["items"][0]["state"] is None
    assert body["items"][0]["mastery_score"] is None
    assert client.get("/api/v1/learning-paths").status_code == 200


def test_invalid_token_is_rejected(client: TestClient):
    response = client.get("/api/v1/learning-paths", headers={"Authorization": "Bearer nope"})
    assert response.status_code == 401


def test_unknown_path_is_404(client: TestClient, auth_headers: dict[str, str]):
    assert client.get("/api/v1/learning-paths/nope", headers=auth_headers).status_code == 404


def test_query_count_does_not_grow_with_steps(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    _build_path(db, user_id, slug="small", steps=2)
    with _QueryCounter(db) as small:
        assert client.get("/api/v1/learning-paths/small", headers=auth_headers).status_code == 200

    _build_path(db, user_id, slug="big", steps=12)
    with _QueryCounter(db) as big:
        assert client.get("/api/v1/learning-paths/big", headers=auth_headers).status_code == 200
    assert big.count == small.count
