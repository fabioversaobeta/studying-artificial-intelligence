"""CSRF protection for the endpoints authenticated by the refresh cookie.

Only /auth/refresh and /auth/logout rely on the ambient cookie; every other
endpoint needs an `Authorization: Bearer` header, which a cross-site form or
request cannot attach. Defence in depth, no server-side state:

1. SameSite cookie attribute (Strict by default) -- the browser withholds the
   cookie from cross-site requests.
2. A required custom header. Cross-origin requests with a non-simple header are
   preflighted, and CORS only approves the origins in CORS_ALLOW_ORIGINS, so a
   foreign page cannot send it.
3. If the browser sent `Origin` (always on POST) or `Referer`, its origin must
   be one of CORS_ALLOW_ORIGINS; `Origin: null` is rejected.
"""

from urllib.parse import urlsplit

from fastapi import Request

from app.api.deps import SettingsDep
from app.core.exceptions import AuthorizationError

CSRF_HEADER = "X-CSRF-Protection"


def _origin_of(url: str) -> str | None:
    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        return None
    return f"{parts.scheme}://{parts.netloc}"


def require_csrf_protection(request: Request, settings: SettingsDep) -> None:
    if request.headers.get(CSRF_HEADER) != "1":
        raise AuthorizationError("Missing CSRF protection header")

    origin = request.headers.get("origin")
    if origin is None and (referer := request.headers.get("referer")):
        origin = _origin_of(referer) or referer
    if origin is not None and origin not in settings.cors_allow_origins:
        raise AuthorizationError("Cross-origin request not allowed")
