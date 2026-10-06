"""Logging setup: request_id context, text/JSON formatters and optional Sentry.

Stdlib only. The request id lives in a ``ContextVar`` set by the request-id
middleware; a ``logging.Filter`` copies it onto every record so formatters can
print it.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

TEXT_FORMAT = "%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s"


class RequestIdFilter(logging.Filter):
    """Attach the current request id (or "-") to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True


class JsonFormatter(logging.Formatter):
    """One JSON object per line: timestamp, level, logger, message, request_id."""

    def format(self, record: logging.LogRecord) -> str:
        request_id = getattr(record, "request_id", None) or request_id_var.get()
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": None if request_id == "-" else request_id,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


class _AppHandler(logging.StreamHandler):  # type: ignore[type-arg]
    """Marker subclass so reconfiguration removes only our own handler."""


def configure_logging(level: str = "INFO", log_format: str = "text") -> None:
    """(Re)configure the root logger; safe to call more than once."""
    handler = _AppHandler(sys.stderr)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        JsonFormatter() if log_format == "json" else logging.Formatter(TEXT_FORMAT)
    )
    root = logging.getLogger()
    for existing in list(root.handlers):
        if isinstance(existing, _AppHandler):
            root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level.upper())


def init_sentry(dsn: str | None, environment: str) -> bool:
    """Initialise Sentry if a DSN is set and ``sentry-sdk`` is installed.

    Returns True when initialised. Never raises on a missing package: the app
    must run without the optional extra and without a DSN.
    """
    if not dsn:
        return False
    try:
        import sentry_sdk
    except ImportError:
        logging.getLogger(__name__).warning(
            "SENTRY_DSN is set but sentry-sdk is not installed "
            "(pip install '.[observability]'); error reporting disabled"
        )
        return False
    sentry_sdk.init(dsn=dsn, environment=environment, send_default_pii=False)
    return True
