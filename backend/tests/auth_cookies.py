"""Helpers for tests that drive the refresh-token cookie flow."""

from fastapi.testclient import TestClient

REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
COOKIE_NAME = "refresh_token"  # not Secure in tests, so no __Secure- prefix
# What the frontend sends on the cookie-authenticated endpoints.
CSRF = {"X-CSRF-Protection": "1"}


def set_refresh_cookie(client: TestClient, token: str) -> None:
    """Replace whatever refresh cookie the client holds with `token`."""
    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, token, domain="testserver.local", path="/api/v1/auth")


def get_refresh_cookie(client: TestClient) -> str:
    token = client.cookies.get(COOKIE_NAME)
    assert token, "client has no refresh cookie"
    return token


def refresh(client: TestClient, token: str | None = None):
    """POST /auth/refresh (optionally presenting `token` as the cookie)."""
    if token is not None:
        set_refresh_cookie(client, token)
    return client.post(REFRESH_URL, headers=CSRF)
