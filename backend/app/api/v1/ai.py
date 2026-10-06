from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, SettingsDep
from app.schemas.ai import AIStatusRead
from app.services.ai import get_ai_service
from app.services.ai.status import get_status

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status", response_model=AIStatusRead)
def ai_status(current_user: CurrentUser, db: DbSession, settings: SettingsDep) -> dict:
    """Internal probe: which provider/model is configured and the caller's usage.

    Exposes whether a key is configured, never the key itself. There are no
    AI feature endpoints yet (roadmap I1 is the foundation only).
    """
    return get_status(db, get_ai_service(settings), current_user.id)
