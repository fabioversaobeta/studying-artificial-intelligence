import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.learning import GoalStatus, LearningGoal


def list_goals_for_user(
    db: Session, user_id: uuid.UUID, *, limit: int | None = None, offset: int = 0
) -> list[LearningGoal]:
    stmt = (
        select(LearningGoal)
        .where(LearningGoal.user_id == user_id)
        .order_by(LearningGoal.created_at.desc(), LearningGoal.id)
        .offset(offset)
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())


def count_goals_for_user(db: Session, user_id: uuid.UUID) -> int:
    stmt = select(func.count()).select_from(LearningGoal).where(LearningGoal.user_id == user_id)
    return int(db.execute(stmt).scalar_one())


def list_active_goals_with_deadline(db: Session, user_id: uuid.UUID) -> list[LearningGoal]:
    """Active goals that have a target date, soonest first (ties by id)."""
    stmt = (
        select(LearningGoal)
        .where(
            LearningGoal.user_id == user_id,
            LearningGoal.status == GoalStatus.ACTIVE,
            LearningGoal.target_date.is_not(None),
        )
        .order_by(LearningGoal.target_date, LearningGoal.id)
    )
    return list(db.execute(stmt).scalars().all())


def get_goal(db: Session, goal_id: uuid.UUID) -> LearningGoal | None:
    return db.get(LearningGoal, goal_id)


def create_goal(
    db: Session,
    *,
    user_id: uuid.UUID,
    title: str,
    description: str | None,
    target_date: date | None,
) -> LearningGoal:
    goal = LearningGoal(
        user_id=user_id, title=title, description=description, target_date=target_date
    )
    db.add(goal)
    db.flush()
    return goal


def delete_goal(db: Session, goal: LearningGoal) -> None:
    db.delete(goal)
    db.flush()


def update_goal_status(db: Session, goal: LearningGoal, status: GoalStatus) -> LearningGoal:
    goal.status = status
    db.flush()
    return goal
