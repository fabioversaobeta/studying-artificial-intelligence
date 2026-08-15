import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.learning import LearningGoalCreate, LearningGoalRead, LearningGoalStatusUpdate
from app.services import learning_service

router = APIRouter(prefix="/goals", tags=["learning"])


@router.post("", response_model=LearningGoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: LearningGoalCreate, current_user: CurrentUser, db: DbSession
) -> LearningGoalRead:
    goal = learning_service.create_goal(
        db,
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        target_date=payload.target_date,
    )
    return LearningGoalRead.model_validate(goal)


@router.get("", response_model=list[LearningGoalRead])
def list_goals(current_user: CurrentUser, db: DbSession) -> list:
    return learning_service.list_goals(db, current_user.id)


@router.patch("/{goal_id}/status", response_model=LearningGoalRead)
def update_goal_status(
    goal_id: uuid.UUID, payload: LearningGoalStatusUpdate, current_user: CurrentUser, db: DbSession
) -> LearningGoalRead:
    goal = learning_service.update_goal_status(
        db, user_id=current_user.id, goal_id=goal_id, status=payload.status
    )
    return LearningGoalRead.model_validate(goal)
