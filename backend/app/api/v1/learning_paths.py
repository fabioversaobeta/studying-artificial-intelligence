from fastapi import APIRouter

from app.api.deps import DbSession, OptionalUser
from app.schemas.learning import LearningPathRead
from app.services import learning_service

router = APIRouter(prefix="/learning-paths", tags=["learning"])


@router.get("", response_model=list[LearningPathRead])
def list_learning_paths(db: DbSession, user: OptionalUser) -> list[dict]:
    return learning_service.list_learning_paths(db, user.id if user else None)


@router.get("/{slug}", response_model=LearningPathRead)
def get_learning_path(slug: str, db: DbSession, user: OptionalUser) -> dict:
    return learning_service.get_learning_path(db, slug, user.id if user else None)
