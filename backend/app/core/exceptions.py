"""Domain-level exceptions, translated to HTTP responses in app.main."""


class AppError(Exception):
    """Base class for all application-raised errors."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


class ConflictError(AppError):
    status_code = 409
    error_code = "conflict"


class ValidationAppError(AppError):
    status_code = 422
    error_code = "validation_error"


class AuthenticationError(AppError):
    status_code = 401
    error_code = "authentication_error"


class AuthorizationError(AppError):
    status_code = 403
    error_code = "authorization_error"


class RateLimitError(AppError):
    status_code = 429
    error_code = "rate_limited"

    def __init__(
        self, retry_after: int, message: str = "Too many requests. Try again later."
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after
