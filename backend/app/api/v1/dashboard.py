from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.dashboard import DashboardRead
from app.services import dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardRead)
def get_dashboard(current_user: CurrentUser, db: DbSession) -> dict:
    return dashboard_service.get_dashboard(db, current_user.id)
