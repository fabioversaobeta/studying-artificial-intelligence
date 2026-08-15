from fastapi import APIRouter

from app.api.v1 import (
    auth,
    challenges,
    dashboard,
    gamification,
    goals,
    learning_paths,
    reviews,
    study_sessions,
    subjects,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(subjects.router)
api_router.include_router(learning_paths.router)
api_router.include_router(study_sessions.router)
api_router.include_router(goals.router)
api_router.include_router(challenges.router)
api_router.include_router(reviews.router)
api_router.include_router(gamification.router)
api_router.include_router(dashboard.router)
