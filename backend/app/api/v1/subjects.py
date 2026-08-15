import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.learning import SubjectDetail, SubjectWithProgress
from app.services import learning_service

router = APIRouter(prefix="/subjects", tags=["learning"])


@router.get("", response_model=list[SubjectWithProgress])
def list_subjects(current_user: CurrentUser, db: DbSession) -> list[dict]:
    return learning_service.list_subjects_with_progress(db, current_user.id)


@router.get("/{subject_id}", response_model=SubjectDetail)
def get_subject(subject_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    return learning_service.get_subject_detail(db, current_user.id, subject_id)
