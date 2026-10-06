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
from app.core.logging import configure_logging, init_sentry
from app.core.middleware import REQUEST_ID_HEADER, RequestIdMiddleware

settings = get_settings()
configure_logging(settings.log_level, settings.log_format)
init_sentry(settings.sentry_dsn, settings.environment)
logger = logging.getLogger(__name__)

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
    expose_headers=["X-Total-Count", REQUEST_ID_HEADER],
)
# Added last so it is the outermost user middleware (wraps CORS too).
app.add_middleware(RequestIdMiddleware)


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
    # This handler runs outside RequestIdMiddleware, so read the id from request.state.
    request_id = getattr(request.state, "request_id", None)
    logger.exception(
        "Unhandled error on %s %s (request_id=%s)", request.method, request.url.path, request_id
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "Internal server error",
                "request_id": request_id,
            }
        },
        headers={REQUEST_ID_HEADER: request_id} if request_id else None,
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
