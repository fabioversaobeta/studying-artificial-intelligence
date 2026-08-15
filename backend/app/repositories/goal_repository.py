import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.learning import GoalStatus, LearningGoal


def list_goals_for_user(db: Session, user_id: uuid.UUID) -> list[LearningGoal]:
    stmt = (
        select(LearningGoal)
        .where(LearningGoal.user_id == user_id)
        .order_by(LearningGoal.created_at.desc())
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


def update_goal_status(db: Session, goal: LearningGoal, status: GoalStatus) -> LearningGoal:
    goal.status = status
    db.flush()
    return goal
