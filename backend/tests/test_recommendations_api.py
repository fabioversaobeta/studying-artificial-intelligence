"""GET /recommendations/today: every kind, ordering, language, new user,
isolation, read-only behaviour and a constant query count."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Base
from app.models.learning import (
    Competency,
    LearningGoal,
    LearningPath,
    LearningPathItem,
    Review,
    Subject,
)
from tests.factories import API, make_assessment, make_question, register
from tests.test_learning_state_queries import (
    _add_competency,
    _mastery,
    _prereq,
    _QueryCounter,
    _study,
    _user_id,
)

URL = f"{API}/recommendations/today"


def _subject(db: Session, name: str, order: int = 0) -> Subject:
    subject = Subject(name=name, slug=name.lower().replace(" ", "-"), sort_order=order)
    db.add(subject)
    db.flush()
    return subject


def _learning(
    db: Session, user_id: uuid.UUID, subject: Subject, name: str, order: int, mastery: float
) -> Competency:
    comp = _add_competency(db, subject, name, order)
    _mastery(db, user_id, comp, mastery)
    _study(db, user_id, comp, 20)
    db.flush()
    return comp


def _review(
    db: Session,
    user_id: uuid.UUID,
    comp: Competency,
    days_overdue: float,
    quality: int | None = None,
) -> None:
    db.add(
        Review(
            user_id=user_id,
            competency_id=comp.id,
            due_at=datetime.now(UTC) - timedelta(days=days_overdue),
            last_recall_quality=quality,
        )
    )
    db.flush()


def _get(client: TestClient, headers: dict[str, str], **params) -> list[dict]:
    response = client.get(URL, headers=headers, params=params)
    assert response.status_code == 200, response.text
    return response.json()["items"]


def test_requires_authentication(client: TestClient):
    assert client.get(URL).status_code == 401


def test_empty_catalog_gives_no_suggestions(client: TestClient, auth_headers: dict[str, str]):
    assert _get(client, auth_headers) == []


def test_new_user_gets_first_available_step_of_first_path(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    subject = _subject(db, "Python")
    first = _add_competency(db, subject, "Basics", 0)
    second = _add_competency(db, subject, "Types", 1)
    _prereq(db, second, first)
    path = LearningPath(title="Python Path", slug="python-path", sort_order=0)
    db.add(path)
    db.flush()
    for order, comp in enumerate([first, second]):
        db.add(LearningPathItem(learning_path_id=path.id, competency_id=comp.id, sort_order=order))
    db.commit()

    (item,) = _get(client, auth_headers)

    assert item["kind"] == "next_in_path"
    assert item["competency"] == {
        "id": str(first.id),
        "name": "Basics",
        "subject_id": str(subject.id),
        "subject_name": "Python",
    }
    assert item["action"] == {"type": "path", "id": None, "slug": "python-path"}
    assert "Python Path" in item["reason"]
    assert item["score"] > 0


def test_new_user_without_paths_gets_first_available_competency(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    subject = _subject(db, "Solo")
    first = _add_competency(db, subject, "Alpha", 0)
    _add_competency(db, subject, "Beta", 1)
    db.commit()

    (item,) = _get(client, auth_headers)

    assert item["competency"]["id"] == str(first.id)
    assert item["action"] == {"type": "competency", "id": str(first.id), "slug": None}


def test_review_due_most_overdue_first(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    recent = _learning(db, user_id, subject, "Recent", 0, 60.0)
    old = _learning(db, user_id, subject, "Old", 1, 60.0)
    future = _learning(db, user_id, subject, "Future", 2, 60.0)
    _review(db, user_id, recent, 1.5)
    _review(db, user_id, old, 9.5)
    _review(db, user_id, future, -3)  # not due yet
    db.commit()

    items = _get(client, auth_headers)

    assert [i["kind"] for i in items[:2]] == ["review_due", "review_due"]
    assert [i["competency"]["id"] for i in items[:2]] == [str(old.id), str(recent.id)]
    assert items[0]["action"] == {"type": "review", "id": str(old.id), "slug": None}
    assert "9 days overdue" in items[0]["reason"]
    assert items[2]["kind"] == "continue_learning"  # the not-yet-due one is just "learning"
    assert items[2]["competency"]["id"] == str(future.id)


def test_strengthen_weak_beats_continue_learning(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    ok = _learning(db, user_id, subject, "Okay", 0, 70.0)
    weak = _learning(db, user_id, subject, "Weak", 1, 12.0)
    db.commit()

    items = _get(client, auth_headers)

    assert [(i["competency"]["id"], i["kind"]) for i in items] == [
        (str(weak.id), "strengthen_weak"),
        (str(ok.id), "continue_learning"),
    ]
    assert "12%" in items[0]["reason"]
    assert items[0]["action"]["type"] == "competency"


def test_recall_lapse_marks_competency_as_weak(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    comp = _learning(db, user_id, subject, "Shaky", 0, 70.0)
    _review(db, user_id, comp, -5, quality=1)  # scheduled later, but last recall was poor
    db.commit()

    (item,) = _get(client, auth_headers)

    assert item["kind"] == "strengthen_weak"
    assert "struggled" in item["reason"]


def test_next_in_path_for_a_path_under_way(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    done = _add_competency(db, subject, "Done", 0)
    _mastery(db, user_id, done, 95.0)
    nxt = _add_competency(db, subject, "Next", 1)
    _prereq(db, nxt, done)
    later = _add_competency(db, subject, "Later", 2)
    _prereq(db, later, nxt)
    path = LearningPath(title="My Path", slug="my-path", sort_order=0)
    db.add(path)
    db.flush()
    for order, comp in enumerate([done, nxt, later]):
        db.add(LearningPathItem(learning_path_id=path.id, competency_id=comp.id, sort_order=order))
    db.commit()

    (item,) = _get(client, auth_headers)

    assert item["kind"] == "next_in_path"
    assert item["competency"]["id"] == str(nxt.id)
    assert item["action"] == {"type": "path", "id": None, "slug": "my-path"}
    assert "My Path" in item["reason"]


def test_take_quiz_when_coverage_is_low(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    comp = _learning(db, user_id, subject, "Quizzable", 0, 60.0)
    db.commit()
    assessment = make_assessment(db, comp, [make_question(db, comp), make_question(db, comp)])

    (item,) = _get(client, auth_headers)

    assert item["kind"] == "take_quiz"
    assert item["action"] == {"type": "assessment", "id": str(assessment.id), "slug": None}
    assert "0%" in item["reason"]


def test_no_quiz_suggestion_without_active_questions(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    comp = _learning(db, user_id, subject, "NoQuiz", 0, 60.0)
    db.commit()
    make_assessment(db, comp, [make_question(db, comp, is_active=False)])

    (item,) = _get(client, auth_headers)

    assert item["kind"] == "continue_learning"


def test_goal_deadline_matches_competency_name(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    target = _learning(db, user_id, subject, "Type Hints", 0, 60.0)
    _learning(db, user_id, subject, "Other", 1, 60.0)
    db.add(
        LearningGoal(
            user_id=user_id,
            title="Master type hints",
            target_date=(datetime.now(UTC) + timedelta(days=3)).date(),
        )
    )
    db.commit()

    items = _get(client, auth_headers)

    assert items[0]["kind"] == "goal_deadline"
    assert items[0]["competency"]["id"] == str(target.id)
    assert "Master type hints" in items[0]["reason"]
    assert "3 days" in items[0]["reason"]


def test_goal_deadline_matches_subject_name_and_focuses_weakest_learning(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Docker")
    _learning(db, user_id, subject, "Images", 0, 75.0)
    weakest = _learning(db, user_id, subject, "Volumes", 1, 55.0)
    db.add(
        LearningGoal(
            user_id=user_id,
            title="Learn Docker",
            target_date=(datetime.now(UTC) - timedelta(days=2)).date(),  # overdue
        )
    )
    db.commit()

    items = _get(client, auth_headers)

    assert items[0]["kind"] == "goal_deadline"
    assert items[0]["competency"]["id"] == str(weakest.id)
    assert "past its target date" in items[0]["reason"]


def test_goal_far_away_or_not_active_or_undated_is_ignored(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    _learning(db, user_id, subject, "Topic", 0, 60.0)
    today = datetime.now(UTC).date()
    db.add_all(
        [
            LearningGoal(
                user_id=user_id, title="Topic far", target_date=today + timedelta(days=90)
            ),
            LearningGoal(user_id=user_id, title="Topic undated"),
        ]
    )
    db.commit()
    client.post(
        f"{API}/goals",
        headers=auth_headers,
        json={"title": "Topic done", "target_date": today.isoformat()},
    )
    done = db.execute(select(LearningGoal).where(LearningGoal.title == "Topic done")).scalar_one()
    client.patch(f"{API}/goals/{done.id}/status", headers=auth_headers, json={"status": "achieved"})

    (item,) = _get(client, auth_headers)

    assert item["kind"] == "continue_learning"


def test_one_suggestion_per_competency_with_highest_reason(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    comp = _learning(db, user_id, subject, "Everything", 0, 10.0)
    _review(db, user_id, comp, 2.5)
    db.commit()
    make_assessment(db, comp, [make_question(db, comp)])

    items = _get(client, auth_headers)

    assert len(items) == 1
    assert items[0]["kind"] == "review_due"


def test_limit_and_deterministic_order(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    for index in range(8):
        _learning(db, user_id, subject, f"Same {index}", index, 60.0)  # identical scores
    db.commit()

    full = _get(client, auth_headers, limit=20)
    assert len(full) == 8
    assert [i["score"] for i in full] == sorted((i["score"] for i in full), reverse=True)
    assert [i["competency"]["id"] for i in full] == sorted(i["competency"]["id"] for i in full)
    assert _get(client, auth_headers, limit=3) == full[:3]
    assert len(_get(client, auth_headers)) == 5  # default limit
    assert _get(client, auth_headers) == _get(client, auth_headers)
    assert client.get(URL, headers=auth_headers, params={"limit": 0}).status_code == 422
    assert client.get(URL, headers=auth_headers, params={"limit": 21}).status_code == 422


def test_reason_follows_preferred_language(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    comp = _learning(db, user_id, subject, "Topic", 0, 60.0)
    _review(db, user_id, comp, 4.5)
    db.commit()

    assert "4 days overdue" in _get(client, auth_headers)[0]["reason"]
    client.patch(
        f"{API}/users/me", headers=auth_headers, json={"preferred_language": "pt-BR"}
    ).raise_for_status()
    assert "4 dias atrasada" in _get(client, auth_headers)[0]["reason"]


def test_users_do_not_see_each_others_data(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    comp = _learning(db, user_id, subject, "Mine", 0, 10.0)
    _review(db, user_id, comp, 3.5)
    db.add(LearningGoal(user_id=user_id, title="Mine", target_date=datetime.now(UTC).date()))
    db.commit()

    other_headers, _ = register(client, "other@example.com")
    items = _get(client, other_headers)

    # the other user has no activity: only the neutral starting point is offered
    assert [i["kind"] for i in items] == ["next_in_path"]
    assert "Mine" not in items[0]["reason"]
    assert items[0]["reason"] == "A good place to start your learning."


def test_get_has_no_side_effects(client: TestClient, auth_headers: dict[str, str], db: Session):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    comp = _learning(db, user_id, subject, "Topic", 0, 20.0)
    _review(db, user_id, comp, 2)
    db.commit()

    def snapshot() -> dict[str, int]:
        return {
            table.name: db.execute(select(func.count()).select_from(table)).scalar_one()
            for table in Base.metadata.sorted_tables
        }

    before = snapshot()
    xp_before = client.get(f"{API}/gamification/profile", headers=auth_headers).json()
    for _ in range(2):
        _get(client, auth_headers)
    assert snapshot() == before
    assert client.get(f"{API}/gamification/profile", headers=auth_headers).json() == xp_before


def test_query_count_does_not_grow_with_data(
    client: TestClient, auth_headers: dict[str, str], db: Session
):
    user_id = _user_id(client, auth_headers)
    subject = _subject(db, "Subj")
    seed = _learning(db, user_id, subject, "Seed", 0, 20.0)
    db.commit()
    # Every data source present at least once (empty id sets skip a query).
    make_assessment(db, seed, [make_question(db, seed)])
    _review(db, user_id, seed, 1)
    path = LearningPath(title="Big", slug="big", sort_order=0)
    db.add(path)
    db.flush()
    db.add(LearningPathItem(learning_path_id=path.id, competency_id=seed.id, sort_order=0))
    db.add(LearningGoal(user_id=user_id, title="Seed", target_date=datetime.now(UTC).date()))
    db.commit()
    _get(client, auth_headers)  # warm-up
    with _QueryCounter(db) as small:
        _get(client, auth_headers)

    for index in range(1, 40):
        sub = _subject(db, f"Subject {index}", index)
        comp = _learning(db, user_id, sub, f"Comp {index}", 0, float(index))
        _review(db, user_id, comp, index / 3)
        db.add(LearningPathItem(learning_path_id=path.id, competency_id=comp.id, sort_order=index))
        if index % 4 == 0:
            make_assessment(db, comp, [make_question(db, comp)])
        db.add(
            LearningGoal(
                user_id=user_id,
                title=f"Goal Comp {index}",
                target_date=datetime.now(UTC).date() + timedelta(days=index),
            )
        )
    db.commit()
    _get(client, auth_headers, limit=20)  # warm-up after the commit, as for `small`
    with _QueryCounter(db) as big:
        assert len(_get(client, auth_headers, limit=20)) == 20

    assert big.count == small.count
