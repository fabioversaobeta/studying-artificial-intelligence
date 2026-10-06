import uuid

from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, DbSession
from app.api.pagination import Pagination, set_total_count
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
def list_study_sessions(
    current_user: CurrentUser, db: DbSession, page: Pagination, response: Response
) -> list:
    items, total = learning_service.list_study_sessions(
        db, current_user.id, limit=page.limit, offset=page.offset
    )
    set_total_count(response, total)
    return items


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_study_session(
    session_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> Response:
    learning_service.delete_study_session(db, user_id=current_user.id, session_id=session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
