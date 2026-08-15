import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.infrastructure.database.session import SessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.error_code, "message": exc.message}},
    )


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness probe: process is up. Does not touch the database."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["system"])
def readiness() -> dict[str, str]:
    """Readiness probe: the database connection is actually usable."""
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ready"}


app.include_router(api_router)
