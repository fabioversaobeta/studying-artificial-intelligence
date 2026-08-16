import uuid

from fastapi import APIRouter

from app.api.deps import DbSession
from app.models.learning import LearningResource
from app.schemas.learning import LearningResourceRead
from app.services import learning_service

router = APIRouter(tags=["learning"])


@router.get("/competencies/{competency_id}/resources", response_model=list[LearningResourceRead])
def list_resources(competency_id: uuid.UUID, db: DbSession) -> list[LearningResource]:
    return learning_service.list_competency_resources(db, competency_id)
