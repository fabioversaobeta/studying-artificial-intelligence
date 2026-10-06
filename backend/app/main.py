import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSession
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError, RateLimitError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
    expose_headers=["X-Total-Count"],
)


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.error_code, "message": exc.message}},
    )


@app.exception_handler(RateLimitError)
def handle_rate_limit_error(request: Request, exc: RateLimitError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.error_code, "message": exc.message}},
        headers={"Retry-After": str(exc.retry_after)},
    )


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # Full details go to the log only; the client gets a generic message.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "Internal server error"}},
    )


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness probe: process is up. Does not touch the database."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["system"], response_model=None)
def readiness(db: DbSession) -> dict[str, str] | JSONResponse:
    """Readiness probe: the database connection is actually usable."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("Readiness check failed: database unavailable")
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ready"}


app.include_router(api_router)
