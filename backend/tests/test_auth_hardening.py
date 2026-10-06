"""Rate limiting (C2) and registration policy (C4) on the auth endpoints."""

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.rate_limit import RateLimiter, client_ip
from tests.auth_cookies import refresh

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"


def payload(email: str = "p@example.com", **extra):
    return {"email": email, "password": "supersecret123", "display_name": "P", **extra}


def enable_rate_limit(settings: Settings, max_requests: int = 3) -> None:
    settings.rate_limit_enabled = True
    settings.rate_limit_max_requests = max_requests
    settings.rate_limit_window_seconds = 60


class TestRateLimit:
    def test_login_is_limited_per_ip_with_standard_error(
        self, client: TestClient, test_settings: Settings
    ):
        enable_rate_limit(test_settings)
        for i in range(3):
            r = client.post(LOGIN, json={"email": f"u{i}@example.com", "password": "wrongpass1"})
            assert r.status_code == 401
        r = client.post(LOGIN, json={"email": "u9@example.com", "password": "wrongpass1"})
        assert r.status_code == 429
        assert r.json()["error"]["code"] == "rate_limited"
        assert "message" in r.json()["error"]
        assert int(r.headers["retry-after"]) >= 1

    def test_login_is_limited_per_email_regardless_of_case(
        self, client: TestClient, test_settings: Settings
    ):
        enable_rate_limit(test_settings)
        # Different IPs (trusted proxy header), same account.
        test_settings.trust_proxy_headers = True
        codes = [
            client.post(
                LOGIN,
                json={"email": email, "password": "wrongpass1"},
                headers={"X-Forwarded-For": f"10.0.0.{i}"},
            ).status_code
            for i, email in enumerate(["a@example.com", "A@example.com"] * 2)
        ]
        assert codes == [401, 401, 401, 429]

    def test_register_and_refresh_are_limited(self, client: TestClient, test_settings: Settings):
        enable_rate_limit(test_settings, max_requests=2)
        for _ in range(2):
            assert refresh(client, "bad").status_code == 401
        assert refresh(client, "bad").status_code == 429
        # Buckets are per endpoint: register is unaffected by the refresh hits.
        assert client.post(REGISTER, json=payload("r1@example.com")).status_code == 201
        assert client.post(REGISTER, json=payload("r2@example.com")).status_code == 201
        assert client.post(REGISTER, json=payload("r3@example.com")).status_code == 429

    def test_disabled_limiter_never_blocks(self, client: TestClient, test_settings: Settings):
        test_settings.rate_limit_enabled = False
        for i in range(15):
            r = client.post(LOGIN, json={"email": "x@example.com", "password": "wrongpass1"})
            assert r.status_code == 401, i

    def test_forwarded_for_ignored_unless_trusted(
        self, client: TestClient, test_settings: Settings
    ):
        enable_rate_limit(test_settings, max_requests=1)
        body = {"email": "x@example.com", "password": "wrongpass1"}
        client.post(LOGIN, json=body, headers={"X-Forwarded-For": "1.1.1.1"})
        # Spoofed header must not give a fresh bucket (also the email bucket hits first).
        r = client.post(
            LOGIN,
            json={"email": "y@example.com", "password": "wrongpass1"},
            headers={"X-Forwarded-For": "2.2.2.2"},
        )
        assert r.status_code == 429


class TestLimiterUnit:
    def test_window_expires(self, monkeypatch):
        import app.core.rate_limit as rl

        now = [1000.0]
        monkeypatch.setattr(rl.time, "monotonic", lambda: now[0])
        lim = RateLimiter()
        lim.hit("k", max_requests=1, window_seconds=10)
        try:
            lim.hit("k", max_requests=1, window_seconds=10)
            raise AssertionError("expected RateLimitError")
        except rl.RateLimitError as exc:
            assert exc.retry_after == 10
        now[0] += 11
        lim.hit("k", max_requests=1, window_seconds=10)

    def test_client_ip_uses_last_forwarded_entry_only_when_trusted(self):
        class Req:
            headers = {"x-forwarded-for": "6.6.6.6, 9.9.9.9"}

            class client:  # noqa: N801
                host = "127.0.0.1"

        untrusted = Settings(_env_file=None, trust_proxy_headers=False)
        trusted = Settings(_env_file=None, trust_proxy_headers=True)
        assert client_ip(Req(), untrusted) == "127.0.0.1"  # type: ignore[arg-type]
        assert client_ip(Req(), trusted) == "9.9.9.9"  # type: ignore[arg-type]

    def test_client_ip_skips_trusted_proxy_hops(self):
        """Vercel rewrite in front of Railway: the real client is 2nd from the end."""

        class Req:
            headers = {"x-forwarded-for": "1.2.3.4, 6.6.6.6, 9.9.9.9"}

            class client:  # noqa: N801
                host = "127.0.0.1"

        two = Settings(_env_file=None, trust_proxy_headers=True, trusted_proxy_hops=2)
        assert client_ip(Req(), two) == "6.6.6.6"  # type: ignore[arg-type]
        too_many = Settings(_env_file=None, trust_proxy_headers=True, trusted_proxy_hops=4)
        assert client_ip(Req(), too_many) == "127.0.0.1"  # type: ignore[arg-type]


class TestRegistrationPolicy:
    def test_info_open_by_default(self, client: TestClient):
        r = client.get("/api/v1/auth/registration-info")
        assert r.status_code == 200
        assert r.json() == {"enabled": True, "invite_required": False}

    def test_disabled_returns_403_standard_format(
        self, client: TestClient, test_settings: Settings
    ):
        test_settings.registration_enabled = False
        r = client.post(REGISTER, json=payload())
        assert r.status_code == 403
        assert r.json()["error"]["code"] == "authorization_error"
        info = client.get("/api/v1/auth/registration-info").json()
        assert info["enabled"] is False

    def test_invite_code_required_when_configured(
        self, client: TestClient, test_settings: Settings
    ):
        test_settings.registration_invite_code = "s3cret-invite"
        assert client.get("/api/v1/auth/registration-info").json()["invite_required"] is True
        assert client.post(REGISTER, json=payload()).status_code == 403
        assert client.post(REGISTER, json=payload(invite_code="nope")).status_code == 403
        ok = client.post(REGISTER, json=payload(invite_code="s3cret-invite"))
        assert ok.status_code == 201

    def test_invite_code_ignored_when_not_configured(self, client: TestClient):
        assert client.post(REGISTER, json=payload(invite_code="whatever")).status_code == 201

    def test_login_still_works_when_registration_closed(
        self, client: TestClient, test_settings: Settings
    ):
        assert client.post(REGISTER, json=payload()).status_code == 201
        test_settings.registration_enabled = False
        r = client.post(LOGIN, json={"email": "p@example.com", "password": "supersecret123"})
        assert r.status_code == 200
