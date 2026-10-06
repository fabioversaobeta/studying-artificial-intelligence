"""Minimal in-memory sliding-window rate limiter for the auth endpoints.

State lives in the process, so with several workers/replicas each one counts
separately (the effective limit is multiplied accordingly). That is an
accepted trade-off for a single-instance deploy; see docs/DECISIONS.md.
"""

import math
import threading
import time
from collections import deque

from fastapi import Request

from app.core.config import Settings
from app.core.exceptions import RateLimitError

_MAX_TRACKED_KEYS = 10_000


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def hit(self, key: str, *, max_requests: int, window_seconds: int) -> None:
        """Record one request for `key`; raise RateLimitError when over the limit."""
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            if len(self._hits) > _MAX_TRACKED_KEYS:
                self._prune(cutoff)
            bucket = self._hits.setdefault(key, deque())
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= max_requests:
                retry_after = max(1, math.ceil(bucket[0] + window_seconds - now))
                raise RateLimitError(retry_after=retry_after)
            bucket.append(now)

    def _prune(self, cutoff: float) -> None:
        for key in [k for k, b in self._hits.items() if not b or b[-1] <= cutoff]:
            del self._hits[key]


limiter = RateLimiter()


def client_ip(request: Request, settings: Settings) -> str:
    """Best-effort client IP.

    X-Forwarded-For is only honoured when TRUST_PROXY_HEADERS is set, since
    otherwise any client could spoof it. We count from the *end*: the last
    TRUSTED_PROXY_HOPS entries were appended by our own proxies (Railway, and
    the Vercel rewrite in front of it); entries before them are client-supplied.
    With 1 hop that is the last entry; with 2 it is the second to last.
    """
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            parts = [part.strip() for part in forwarded.split(",")]
            index = -settings.trusted_proxy_hops
            if len(parts) >= settings.trusted_proxy_hops and parts[index]:
                return parts[index]
    return request.client.host if request.client else "unknown"


def rate_limit_login_email(email: str, settings: Settings) -> None:
    """Per-account limit on login attempts (case-insensitive e-mail)."""
    if not settings.rate_limit_enabled:
        return
    limiter.hit(
        f"login:email:{email.strip().lower()}",
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
