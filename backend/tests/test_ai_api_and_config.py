"""GET /ai/status and AI-related Settings validation."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from tests.factories import register

GOOD_SECRET = "x" * 48
KEY = "sk-ant-super-secret-value"


def make(**kwargs) -> Settings:
    return Settings(_env_file=None, **kwargs)


def test_ai_defaults_are_safe():
    s = make()
    assert s.ai_provider == "fake" and s.anthropic_api_key is None
    assert s.ai_daily_token_limit == 0 and s.ai_model == "claude-sonnet-5-5"


def test_production_claude_without_key_fails_boot():
    with pytest.raises(ValidationError, match="ANTHROPIC_API_KEY"):
        make(environment="production", secret_key=GOOD_SECRET, ai_provider="claude")
    with pytest.raises(ValidationError, match="ANTHROPIC_API_KEY"):
        make(
            environment="production",
            secret_key=GOOD_SECRET,
            ai_provider="claude",
            anthropic_api_key="   ",
        )


def test_production_claude_with_key_and_production_fake_boot():
    s = make(
        environment="production",
        secret_key=GOOD_SECRET,
        ai_provider="claude",
        anthropic_api_key=KEY,
    )
    assert s.anthropic_api_key is not None
    assert make(environment="production", secret_key=GOOD_SECRET).ai_provider == "fake"


def test_development_claude_without_key_boots():
    assert make(ai_provider="claude").ai_provider == "claude"


def test_api_key_is_not_leaked_by_repr_or_dump():
    s = make(anthropic_api_key=KEY)
    assert KEY not in repr(s) and KEY not in str(s.model_dump())


def test_status_requires_auth(client: TestClient):
    assert client.get("/api/v1/ai/status").status_code == 401


def test_status_reports_fake_provider_and_usage(client: TestClient):
    headers, _ = register(client, "status@example.com")
    body = client.get("/api/v1/ai/status", headers=headers).json()
    assert body["provider"] == "fake" and body["configured"] is True
    assert body["daily_token_limit"] is None
    assert body["usage_today"]["calls"] == 0 and body["usage_total"]["calls"] == 0


def test_status_with_claude_never_exposes_the_key(client: TestClient, test_settings: Settings):
    test_settings.ai_provider = "claude"
    test_settings.anthropic_api_key = make(anthropic_api_key=KEY).anthropic_api_key
    test_settings.ai_daily_token_limit = 1000
    headers, _ = register(client, "status2@example.com")
    response = client.get("/api/v1/ai/status", headers=headers)
    body = response.json()
    assert body["provider"] == "claude" and body["configured"] is True
    assert body["model"] == "claude-sonnet-5-5" and body["daily_token_limit"] == 1000
    assert KEY not in response.text


def test_status_claude_without_key_is_not_configured(client: TestClient, test_settings: Settings):
    test_settings.ai_provider = "claude"
    headers, _ = register(client, "status3@example.com")
    assert client.get("/api/v1/ai/status", headers=headers).json()["configured"] is False
