"""'What to study today' (roadmap I3): gathers the user's data in a constant
number of queries, derives `CompetencyFacts`, and applies the pure rules in
`app.domain.recommendations`. Read-only: it never writes, grants XP or
schedules anything.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.domain.recommendation_messages import render_reason
from app.domain.recommendations import (
    DEFAULT_LIMIT,
    Candidate,
    CompetencyFacts,
    RecommendationKind,
    candidates_for,
    path_next_step,
    select_top,
    starting_point,
    text_mentions,
)
from app.models.learning import Competency, CompetencyState, LearningGoal, LearningPath
from app.models.user import Language
from app.repositories import (
    assessment_repository,
    goal_repository,
    learning_catalog_repository,
    review_repository,
)
from app.services import learning_service


@dataclass(frozen=True)
class _GoalHit:
    days_left: int
    title: str


def _goal_hits(
    goals: list[LearningGoal],
    ordered: list[Competency],
    states: dict[uuid.UUID, dict],
    today_ordinal: int,
) -> dict[uuid.UUID, _GoalHit]:
    """Link goals to competencies by name: a goal that mentions a competency's
    name points at it; one that mentions only a subject's name points at that
    subject's focus competency (see `_focus_competency`). Goals have no
    structural link to the catalog, so this textual match is the explainable
    rule (docs/DECISIONS.md). `goals` arrive soonest-first: the nearest wins."""
    hits: dict[uuid.UUID, _GoalHit] = {}
    by_subject: dict[uuid.UUID, list[Competency]] = {}
    for competency in ordered:
        by_subject.setdefault(competency.subject_id, []).append(competency)

    for goal in goals:
        assert goal.target_date is not None
        text = f"{goal.title} {goal.description or ''}"
        days_left = goal.target_date.toordinal() - today_ordinal
        targets = [c.id for c in ordered if text_mentions(text, c.name)]
        if not targets:
            for competencies in by_subject.values():
                if text_mentions(text, competencies[0].subject.name):
                    focus = _focus_competency(competencies, states)
                    if focus is not None:
                        targets.append(focus)
        for competency_id in targets:
            hits.setdefault(competency_id, _GoalHit(days_left, goal.title))
    return hits


def _focus_competency(
    competencies: list[Competency], states: dict[uuid.UUID, dict]
) -> uuid.UUID | None:
    """Where to work inside a subject: the weakest `learning` competency, else
    the first `available` one (catalog order)."""
    learning = [c for c in competencies if states[c.id]["state"] == CompetencyState.LEARNING]
    if learning:
        return min(learning, key=lambda c: (states[c.id]["mastery_score"], str(c.id))).id
    for competency in competencies:
        if states[competency.id]["state"] == CompetencyState.AVAILABLE:
            return competency.id
    return None


def _path_targets(
    paths: list[LearningPath], states: dict[uuid.UUID, dict]
) -> dict[uuid.UUID, tuple[str, str]]:
    targets: dict[uuid.UUID, tuple[str, str]] = {}
    for path in paths:
        steps = [(item.competency_id, states[item.competency_id]["state"]) for item in path.items]
        next_id = path_next_step(steps)
        if next_id is not None:
            targets.setdefault(next_id, (path.slug, path.title))
    return targets


def _starting_point(
    paths: list[LearningPath], ordered: list[Competency], states: dict[uuid.UUID, dict]
) -> Candidate | None:
    for path in paths:
        for item in path.items:
            if states[item.competency_id]["state"] == CompetencyState.AVAILABLE:
                return starting_point(item.competency_id, (path.slug, path.title))
    for competency in ordered:
        if states[competency.id]["state"] == CompetencyState.AVAILABLE:
            return starting_point(competency.id)
    return None


def get_today(
    db: Session,
    user_id: uuid.UUID,
    language: Language,
    *,
    limit: int = DEFAULT_LIMIT,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    now = now or datetime.now(UTC)
    today_ordinal = now.date().toordinal()

    competencies = learning_catalog_repository.list_all_competencies(db)
    ordered = sorted(competencies, key=lambda c: (c.subject.sort_order, c.sort_order, str(c.id)))
    states = {
        entry["competency"].id: entry
        for entry in learning_service.competencies_with_state(db, user_id, ordered)
    }
    reviews = {r.competency_id: r for r in review_repository.list_reviews_for_user(db, user_id)}
    paths = learning_catalog_repository.list_learning_paths(db)
    goals = goal_repository.list_active_goals_with_deadline(db, user_id)
    quizzes = assessment_repository.first_quiz_by_competency(db)
    questions = assessment_repository.active_questions_by_competency(db, quizzes.keys())
    correct = assessment_repository.correct_latest_by_competency(db, user_id, quizzes.keys())

    goal_hits = _goal_hits(goals, ordered, states, today_ordinal)
    path_targets = _path_targets(paths, states)

    candidates: list[Candidate] = []
    for competency in ordered:
        cid = competency.id
        review = reviews.get(cid)
        overdue = (
            (now - review.due_at).days if review is not None and review.due_at <= now else None
        )
        total = questions.get(cid, 0)
        hit = goal_hits.get(cid)
        facts = CompetencyFacts(
            competency_id=cid,
            state=states[cid]["state"],
            mastery=states[cid]["mastery_score"],
            last_recall_quality=review.last_recall_quality if review is not None else None,
            review_overdue_days=overdue,
            goal_days_left=hit.days_left if hit else None,
            goal_title=hit.title if hit else None,
            quiz_coverage=correct.get(cid, 0) / total if cid in quizzes and total > 0 else None,
            path_next=path_targets.get(cid),
        )
        candidates.extend(candidates_for(facts))

    top = select_top(candidates, limit)
    if not top and limit > 0:
        fallback = _starting_point(paths, ordered, states)
        top = [fallback] if fallback is not None else []

    by_id = {c.id: c for c in ordered}
    return [_to_item(c, by_id[c.competency_id], quizzes, language) for c in top]


def _to_item(
    candidate: Candidate,
    competency: Competency,
    quizzes: dict[uuid.UUID, uuid.UUID],
    language: Language,
) -> dict[str, Any]:
    action: dict[str, Any]
    if candidate.kind == RecommendationKind.REVIEW_DUE:
        action = {"type": "review", "id": competency.id, "slug": None}
    elif candidate.kind == RecommendationKind.TAKE_QUIZ:
        action = {"type": "assessment", "id": quizzes[competency.id], "slug": None}
    elif candidate.kind == RecommendationKind.NEXT_IN_PATH and candidate.path_slug is not None:
        action = {"type": "path", "id": None, "slug": candidate.path_slug}
    else:
        action = {"type": "competency", "id": competency.id, "slug": None}
    return {
        "kind": candidate.kind,
        "competency": {
            "id": competency.id,
            "name": competency.name,
            "subject_id": competency.subject_id,
            "subject_name": competency.subject.name,
        },
        "reason": render_reason(candidate.reason_key, candidate.reason_params, language.value),
        "score": round(candidate.score, 2),
        "action": action,
    }
