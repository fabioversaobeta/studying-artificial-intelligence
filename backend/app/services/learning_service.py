import uuid
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.domain.skill_tree import compute_competency_state
from app.models.gamification import XPSource
from app.models.learning import Competency, GoalStatus, LearningGoal, StudySession
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
    if competency_id is not None and learning_catalog_repository.get_competency(db, competency_id) is None:
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

    db.commit()
    db.refresh(session)
    return session


def list_study_sessions(db: Session, user_id: uuid.UUID) -> list[StudySession]:
    return study_repository.list_study_sessions(db, user_id)


def list_subjects_with_progress(db: Session, user_id: uuid.UUID) -> list[dict]:
    subjects = learning_catalog_repository.list_subjects(db)
    mastery_by_competency = {
        m.competency_id: m.score for m in mastery_repository.list_mastery_for_user(db, user_id)
    }

    result = []
    for subject in subjects:
        competencies = learning_catalog_repository.list_competencies_by_subject(db, subject.id)
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
        "competencies": [_competency_with_state(db, user_id, c) for c in competencies],
    }


def _competency_with_state(db: Session, user_id: uuid.UUID, competency: Competency) -> dict:
    mastery = mastery_repository.get_mastery(db, user_id, competency.id)
    total_minutes = study_repository.total_study_minutes_for_competency(db, user_id, competency.id)
    prerequisite_ids = learning_catalog_repository.get_prerequisite_ids(db, competency.id)

    prerequisites_mastered = True
    for prereq_id in prerequisite_ids:
        prereq_mastery = mastery_repository.get_mastery(db, user_id, prereq_id)
        if prereq_mastery is None or prereq_mastery.score < 80.0:
            prerequisites_mastered = False
            break

    state = compute_competency_state(
        mastery_score=mastery.score if mastery else None,
        has_activity=total_minutes > 0,
        prerequisites_mastered=prerequisites_mastered,
    )

    return {
        "competency": competency,
        "mastery_score": mastery.score if mastery else 0.0,
        "state": state,
    }


def list_learning_paths(db: Session) -> list:
    return learning_catalog_repository.list_learning_paths(db)


def get_learning_path(db: Session, slug: str):
    path = learning_catalog_repository.get_learning_path_by_slug(db, slug)
    if path is None:
        raise NotFoundError("Learning path not found")
    return path


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


def list_goals(db: Session, user_id: uuid.UUID) -> list[LearningGoal]:
    return goal_repository.list_goals_for_user(db, user_id)


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
