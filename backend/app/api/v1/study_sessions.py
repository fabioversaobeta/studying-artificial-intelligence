from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.learning import StudySessionCreate, StudySessionRead
from app.services import learning_service

router = APIRouter(prefix="/study-sessions", tags=["learning"])


@router.post("", response_model=StudySessionRead, status_code=status.HTTP_201_CREATED)
def create_study_session(
    payload: StudySessionCreate, current_user: CurrentUser, db: DbSession
) -> StudySessionRead:
    session = learning_service.log_study_session(
        db,
        user_id=current_user.id,
        competency_id=payload.competency_id,
        subject_id=payload.subject_id,
        duration_minutes=payload.duration_minutes,
        notes=payload.notes,
        occurred_at=payload.occurred_at,
    )
    return StudySessionRead.model_validate(session)


@router.get("", response_model=list[StudySessionRead])
def list_study_sessions(current_user: CurrentUser, db: DbSession) -> list:
    return learning_service.list_study_sessions(db, current_user.id)
