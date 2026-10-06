"""The refresh token lives only in an HttpOnly cookie scoped to the auth routes."""

from fastapi import Request, Response

from app.core.config import Settings

# Browsers send the cookie only to these routes (login/register/refresh/logout),
# never to the rest of the API. Must match the public path of the API (the Vercel
# rewrite keeps /api/v1 intact).
REFRESH_COOKIE_PATH = "/api/v1/auth"


def set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        max_age=settings.refresh_token_expire_minutes * 60,
        path=REFRESH_COOKIE_PATH,
        domain=settings.cookie_domain,
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    # Attributes must match the ones used to set it or the browser keeps the cookie.
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=REFRESH_COOKIE_PATH,
        domain=settings.cookie_domain,
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )


def read_refresh_cookie(request: Request, settings: Settings) -> str | None:
    return request.cookies.get(settings.refresh_cookie_name)
