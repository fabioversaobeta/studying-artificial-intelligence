"""Refresh-token cookie flags, CSRF protection on the cookie endpoints, and API headers."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from tests.auth_cookies import CSRF, LOGOUT_URL, REFRESH_URL, get_refresh_cookie

ORIGIN = "http://localhost:5173"
REGISTER = {"email": "ck@example.com", "password": "supersecret123", "display_name": "Ck"}


def _set_cookie_headers(response) -> list[str]:
    return response.headers.get_list("set-cookie")


def _register(client: TestClient):
    response = client.post("/api/v1/auth/register", json=REGISTER)
    assert response.status_code == 201
    return response


class TestCookieFlags:
    def test_login_sets_an_httponly_scoped_cookie(self, client: TestClient):
        _register(client)
        client.cookies.clear()
        response = client.post(
            "/api/v1/auth/login",
            json={"email": REGISTER["email"], "password": REGISTER["password"]},
        )
        (cookie,) = _set_cookie_headers(response)
        lowered = cookie.lower()
        assert cookie.startswith("refresh_token=")
        assert "httponly" in lowered
        assert "path=/api/v1/auth" in lowered
        assert "samesite=strict" in lowered
        assert "max-age=2592000" in lowered  # 30 days
        assert "secure" not in lowered  # dev default: plain http://localhost
        assert "domain=" not in lowered  # host-only
        assert "refresh_token" not in response.json()

    def test_register_and_refresh_also_set_the_cookie(self, client: TestClient):
        assert len(_set_cookie_headers(_register(client))) == 1
        assert len(_set_cookie_headers(client.post(REFRESH_URL, headers=CSRF))) == 1

    def test_secure_config_adds_secure_flag_and_prefix(
        self, client: TestClient, test_settings: Settings
    ):
        test_settings.cookie_secure = True
        test_settings.cookie_samesite = "lax"
        test_settings.cookie_domain = "example.com"
        (cookie,) = _set_cookie_headers(_register(client))
        lowered = cookie.lower()
        assert cookie.startswith("__Secure-refresh_token=")
        assert "secure" in lowered
        assert "samesite=lax" in lowered
        assert "domain=example.com" in lowered
        assert "httponly" in lowered

    def test_logout_expires_the_cookie_with_matching_attributes(self, client: TestClient):
        _register(client)
        response = client.post(LOGOUT_URL, headers=CSRF)
        (cookie,) = _set_cookie_headers(response)
        lowered = cookie.lower()
        assert cookie.startswith("refresh_token=")
        assert "max-age=0" in lowered
        assert "path=/api/v1/auth" in lowered
        assert "httponly" in lowered
        assert "refresh_token" not in client.cookies

    def test_failed_refresh_clears_the_dead_cookie(self, client: TestClient):
        _register(client)
        old = get_refresh_cookie(client)
        assert client.post(REFRESH_URL, headers=CSRF).status_code == 200
        client.cookies.clear()
        client.cookies.set("refresh_token", old, domain="testserver.local", path="/api/v1/auth")
        response = client.post(REFRESH_URL, headers=CSRF)
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "authentication_error"
        (cookie,) = _set_cookie_headers(response)
        assert "max-age=0" in cookie.lower()

    def test_cookie_is_not_sent_outside_the_auth_path(self, client: TestClient):
        _register(client)
        response = client.get("/api/v1/subjects")
        assert "refresh_token" not in response.request.headers.get("cookie", "")


class TestCsrf:
    @pytest.mark.parametrize("url", [REFRESH_URL, LOGOUT_URL])
    def test_missing_header_is_rejected(self, client: TestClient, url: str):
        _register(client)
        response = client.post(url)
        assert response.status_code == 403
        assert "refresh_token" in client.cookies  # nothing happened

    @pytest.mark.parametrize("url", [REFRESH_URL, LOGOUT_URL])
    def test_wrong_header_value_is_rejected(self, client: TestClient, url: str):
        _register(client)
        assert client.post(url, headers={"X-CSRF-Protection": "0"}).status_code == 403

    @pytest.mark.parametrize("url", [REFRESH_URL, LOGOUT_URL])
    def test_foreign_origin_is_rejected(self, client: TestClient, url: str):
        _register(client)
        headers = {**CSRF, "Origin": "https://evil.example"}
        assert client.post(url, headers=headers).status_code == 403

    def test_null_origin_is_rejected(self, client: TestClient):
        _register(client)
        assert client.post(REFRESH_URL, headers={**CSRF, "Origin": "null"}).status_code == 403

    def test_foreign_referer_without_origin_is_rejected(self, client: TestClient):
        _register(client)
        headers = {**CSRF, "Referer": "https://evil.example/page?x=1"}
        assert client.post(REFRESH_URL, headers=headers).status_code == 403

    def test_allowed_origin_and_referer_pass(self, client: TestClient):
        _register(client)
        assert client.post(REFRESH_URL, headers={**CSRF, "Origin": ORIGIN}).status_code == 200
        referer = {**CSRF, "Referer": f"{ORIGIN}/dashboard"}
        assert client.post(REFRESH_URL, headers=referer).status_code == 200

    def test_csrf_failure_does_not_burn_the_refresh_token(self, client: TestClient):
        _register(client)
        before = get_refresh_cookie(client)
        client.post(REFRESH_URL, headers={"Origin": "https://evil.example"})
        assert get_refresh_cookie(client) == before
        assert client.post(REFRESH_URL, headers=CSRF).status_code == 200

    def test_login_and_register_do_not_need_the_header(self, client: TestClient):
        # They authenticate with credentials in the body, not with the cookie.
        _register(client)

    def test_preflight_allows_the_csrf_header_for_listed_origins(self, client: TestClient):
        response = client.options(
            REFRESH_URL,
            headers={
                "Origin": ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "x-csrf-protection",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-credentials"] == "true"


class TestApiSecurityHeaders:
    def test_json_responses_carry_defensive_headers(self, client: TestClient):
        response = client.get("/health")
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert "default-src 'none'" in response.headers["content-security-policy"]
        assert "strict-transport-security" not in response.headers  # off outside production

    def test_auth_responses_are_not_cacheable(self, client: TestClient):
        assert _register(client).headers["cache-control"] == "no-store"
        assert client.post(REFRESH_URL, headers=CSRF).headers["cache-control"] == "no-store"

    def test_docs_do_not_get_the_api_csp(self, client: TestClient):
        response = client.get("/docs")
        assert "content-security-policy" not in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"


class TestCookieSettings:
    def test_production_forces_secure_cookie(self):
        settings = Settings(
            _env_file=None,
            environment="production",
            secret_key="x" * 40,
            cookie_secure=False,
        )
        assert settings.cookie_secure is True
        assert settings.refresh_cookie_name == "__Secure-refresh_token"

    def test_development_default_is_insecure_http_friendly(self):
        settings = Settings(_env_file=None)
        assert settings.cookie_secure is False
        assert settings.cookie_samesite == "strict"
        assert settings.refresh_cookie_name == "refresh_token"

    def test_samesite_none_requires_secure(self):
        with pytest.raises(ValueError, match="COOKIE_SAMESITE=none"):
            Settings(_env_file=None, cookie_samesite="none", cookie_secure=False)
        Settings(_env_file=None, cookie_samesite="none", cookie_secure=True)
