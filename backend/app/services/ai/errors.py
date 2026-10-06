"""Domain exceptions of the AI layer.

They subclass ``AppError`` so the global handler in ``app.main`` turns them
into the standard error JSON. Provider-specific SDK errors never escape the
``app.services.ai`` package: providers map them to these.
"""

from app.core.exceptions import AppError


class AIError(AppError):
    """Base class for every error raised by the AI layer."""

    status_code = 502
    error_code = "ai_error"


class AIProviderError(AIError):
    """The provider rejected or failed the call (bad request, auth, 5xx...)."""

    status_code = 502
    error_code = "ai_provider_error"


class AIRateLimited(AIError):
    """The provider answered 429 (rate limit); safe to retry later."""

    status_code = 429
    error_code = "ai_rate_limited"


class AIUnavailable(AIError):
    """Provider unreachable, timed out, overloaded, or not configured."""

    status_code = 503
    error_code = "ai_unavailable"


class AIInvalidOutput(AIError):
    """The model output did not match the requested schema, even after repair."""

    status_code = 502
    error_code = "ai_invalid_output"


class AIUsageLimitExceeded(AIError):
    """The optional daily token ceiling (AI_DAILY_TOKEN_LIMIT) was reached.

    Callers are expected to catch this (or any ``AIError``) and degrade the
    feature to "AI feedback unavailable" instead of failing the whole flow.
    """

    status_code = 429
    error_code = "ai_usage_limit_exceeded"
