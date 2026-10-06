import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.skill_tree import MASTERY_THRESHOLD, compute_competency_state
from app.models.gamification import XPSource
from app.models.learning import (
    Competency,
    CompetencyState,
    GoalStatus,
    LearningGoal,
    LearningPath,
    LearningResource,
    StudySession,
)
from app.repositories import (
    goal_repository,
    learning_catalog_repository,
    mastery_repository,
    study_repository,
)
from app.services import gamification_service, mastery_service, review_service

STUDY_XP_PER_10_MINUTES = 5
STUDY_XP_MAX_PER_SESSION = 60  # caps a single very long session at 120 minutes worth of XP


def _xp_for_study_session(duration_minutes: int) -> int:
    return min(STUDY_XP_MAX_PER_SESSION, (duration_minutes // 10) * STUDY_XP_PER_10_MINUTES)


def log_study_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    competency_id: uuid.UUID | None,
    subject_id: uuid.UUID | None,
    duration_minutes: int,
    notes: str | None,
    occurred_at: datetime | None,
) -> StudySession:
    if (
        competency_id is not None
        and learning_catalog_repository.get_competency(db, competency_id) is None
    ):
        raise NotFoundError("Competency not found")

    session = study_repository.create_study_session(
        db,
        user_id=user_id,
        competency_id=competency_id,
        subject_id=subject_id,
        duration_minutes=duration_minutes,
        notes=notes,
        occurred_at=occurred_at or datetime.now(UTC),
    )

    if competency_id is not None:
        mastery_service.recompute_mastery(db, user_id=user_id, competency_id=competency_id)
        review_service.schedule_initial_review(db, user_id=user_id, competency_id=competency_id)

    xp_amount = _xp_for_study_session(duration_minutes)
    if xp_amount > 0:
        gamification_service.award_xp(
            db,
            user_id=user_id,
            amount=xp_amount,
            source=XPSource.STUDY_SESSION,
            reference_id=session.id,
            description="Study session logged",
        )
    else:
        # No XP means award_xp never ran; progress may still have advanced.
        gamification_service.settle_rewards(db, user_id)

    db.commit()
    db.refresh(session)
    return session


def delete_study_session(db: Session, *, user_id: uuid.UUID, session_id: uuid.UUID) -> None:
    """Hard-delete one of the user's study sessions.

    XP is deliberately NOT refunded: ``xp_awards`` (the ledger), ``total_xp``,
    level, streak and already-earned achievements/quests are left untouched,
    because XP measures activity that really happened. Mastery measures
    knowledge, so it is recomputed for the affected competency.
    """
    session = study_repository.get_study_session(db, session_id)
    if session is None or session.user_id != user_id:
        raise NotFoundError("Study session not found")

    competency_id = session.competency_id
    study_repository.delete_study_session(db, session)
    if competency_id is not None:
        mastery_service.recompute_mastery(db, user_id=user_id, competency_id=competency_id)
    db.commit()


def list_study_sessions(
    db: Session, user_id: uuid.UUID, *, limit: int = 50, offset: int = 0
) -> tuple[list[StudySession], int]:
    """One page of the user's sessions plus the total count."""
    items = study_repository.list_study_sessions(db, user_id, limit=limit, offset=offset)
    return items, study_repository.count_study_sessions(db, user_id)


def list_subjects_with_progress(db: Session, user_id: uuid.UUID) -> list[dict]:
    subjects = learning_catalog_repository.list_subjects(db)
    competencies_by_subject = learning_catalog_repository.list_competencies_by_subjects(
        db, [s.id for s in subjects]
    )
    mastery_by_competency = {
        m.competency_id: m.score for m in mastery_repository.list_mastery_for_user(db, user_id)
    }

    result = []
    for subject in subjects:
        competencies = competencies_by_subject[subject.id]
        scores = [mastery_by_competency.get(c.id, 0.0) for c in competencies]
        avg_mastery = round(sum(scores) / len(scores), 2) if scores else 0.0
        result.append(
            {
                "subject": subject,
                "competency_count": len(competencies),
                "average_mastery": avg_mastery,
            }
        )
    return result


def get_subject_detail(db: Session, user_id: uuid.UUID, subject_id: uuid.UUID) -> dict:
    subject = learning_catalog_repository.get_subject(db, subject_id)
    if subject is None:
        raise NotFoundError("Subject not found")

    competencies = learning_catalog_repository.list_competencies_by_subject(db, subject_id)
    return {
        "subject": subject,
        "competencies": _competencies_with_state(db, user_id, competencies),
    }


def _competencies_with_state(
    db: Session, user_id: uuid.UUID, competencies: list[Competency]
) -> list[dict]:
    """Derive each competency's skill-tree state with a constant number of queries
    (prerequisites, mastery, study minutes), regardless of how many competencies."""
    competency_ids = [c.id for c in competencies]
    prerequisites = learning_catalog_repository.get_prerequisite_ids_by_competency(
        db, competency_ids
    )
    # Prerequisites may live in other subjects, so mastery is loaded for both sets.
    all_ids = set(competency_ids).union(*prerequisites.values())
    scores = mastery_repository.get_scores_by_competency(db, user_id, all_ids)
    minutes = study_repository.total_study_minutes_by_competency(db, user_id, competency_ids)

    result = []
    for competency in competencies:
        mastery_score = scores.get(competency.id)
        prerequisites_mastered = all(
            scores.get(prereq_id, 0.0) >= MASTERY_THRESHOLD
            for prereq_id in prerequisites[competency.id]
        )
        state = compute_competency_state(
            mastery_score=mastery_score,
            has_activity=minutes.get(competency.id, 0) > 0,
            prerequisites_mastered=prerequisites_mastered,
        )
        result.append(
            {
                "competency": competency,
                "mastery_score": mastery_score if mastery_score is not None else 0.0,
                "state": state,
            }
        )
    return result


def list_competency_resources(db: Session, competency_id: uuid.UUID) -> list[LearningResource]:
    if learning_catalog_repository.get_competency(db, competency_id) is None:
        raise NotFoundError("Competency not found")
    return learning_catalog_repository.list_resources_by_competency(db, competency_id)


def list_learning_paths(db: Session, user_id: uuid.UUID | None = None) -> list[dict]:
    paths = learning_catalog_repository.list_learning_paths(db)
    return _paths_with_progress(db, user_id, paths)


def get_learning_path(db: Session, slug: str, user_id: uuid.UUID | None = None) -> dict:
    path = learning_catalog_repository.get_learning_path_by_slug(db, slug)
    if path is None:
        raise NotFoundError("Learning path not found")
    return _paths_with_progress(db, user_id, [path])[0]


def _paths_with_progress(
    db: Session, user_id: uuid.UUID | None, paths: list[LearningPath]
) -> list[dict]:
    """Attach per-step mastery/state and an aggregate to each path.

    Reuses the skill-tree state derivation on every distinct competency of all
    given paths at once, so the query count is constant (no N+1)."""
    states: dict[uuid.UUID, dict] = {}
    if user_id is not None:
        distinct = {item.competency_id: item.competency for p in paths for item in p.items}
        states = {
            entry["competency"].id: entry
            for entry in _competencies_with_state(db, user_id, list(distinct.values()))
        }

    result = []
    for path in paths:
        items: list[dict[str, Any]] = []
        for item in path.items:
            entry = states.get(item.competency_id)
            items.append(
                {
                    "competency": item.competency,
                    "sort_order": item.sort_order,
                    "mastery_score": entry["mastery_score"] if entry else None,
                    "state": entry["state"] if entry else None,
                }
            )
        progress = None
        if user_id is not None:
            scores = [i["mastery_score"] for i in items]
            progress = {
                "total_steps": len(items),
                "mastered_steps": sum(1 for i in items if i["state"] == CompetencyState.MASTERED),
                "average_mastery": round(sum(scores) / len(scores), 2) if scores else 0.0,
            }
        result.append(
            {
                "id": path.id,
                "title": path.title,
                "slug": path.slug,
                "description": path.description,
                "items": items,
                "progress": progress,
            }
        )
    return result


def create_goal(
    db: Session,
    *,
    user_id: uuid.UUID,
    title: str,
    description: str | None,
    target_date: date | None,
) -> LearningGoal:
    goal = goal_repository.create_goal(
        db, user_id=user_id, title=title, description=description, target_date=target_date
    )
    db.commit()
    db.refresh(goal)
    return goal


def list_goals(
    db: Session, user_id: uuid.UUID, *, limit: int = 50, offset: int = 0
) -> tuple[list[LearningGoal], int]:
    """One page of the user's goals plus the total count."""
    items = goal_repository.list_goals_for_user(db, user_id, limit=limit, offset=offset)
    return items, goal_repository.count_goals_for_user(db, user_id)


def delete_goal(db: Session, *, user_id: uuid.UUID, goal_id: uuid.UUID) -> None:
    goal = goal_repository.get_goal(db, goal_id)
    if goal is None or goal.user_id != user_id:
        raise NotFoundError("Learning goal not found")
    goal_repository.delete_goal(db, goal)
    db.commit()


def update_goal_status(
    db: Session, *, user_id: uuid.UUID, goal_id: uuid.UUID, status: GoalStatus
) -> LearningGoal:
    goal = goal_repository.get_goal(db, goal_id)
    if goal is None or goal.user_id != user_id:
        raise NotFoundError("Learning goal not found")
    goal = goal_repository.update_goal_status(db, goal, status)
    db.commit()
    db.refresh(goal)
    return goal
