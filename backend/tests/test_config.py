"""Settings validation. Instantiates Settings directly (not the cached
get_settings()) and ignores any local .env file."""

import pytest
from pydantic import ValidationError

from app.core.config import INSECURE_DEFAULT_SECRET_KEY, Settings

GOOD_SECRET = "x" * 48


def make(**kwargs) -> Settings:
    return Settings(_env_file=None, **kwargs)


def test_debug_defaults_to_false():
    assert make().debug is False


def test_development_allows_default_secret_and_debug():
    s = make(environment="development", debug=True, secret_key=INSECURE_DEFAULT_SECRET_KEY)
    assert not s.is_production


def test_production_with_strong_secret_boots():
    s = make(environment="production", secret_key=GOOD_SECRET, debug=False)
    assert s.is_production


def test_production_rejects_default_secret():
    with pytest.raises(ValidationError, match="insecure development default"):
        make(environment="production", secret_key=INSECURE_DEFAULT_SECRET_KEY)


def test_production_rejects_short_secret():
    with pytest.raises(ValidationError, match="shorter than 32"):
        make(environment="production", secret_key="short")


def test_production_rejects_debug():
    with pytest.raises(ValidationError, match="DEBUG must be false"):
        make(environment="production", secret_key=GOOD_SECRET, debug=True)


def test_production_rejects_missing_secret_env(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        make(environment="production")


def test_reads_from_environment(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", GOOD_SECRET)
    monkeypatch.setenv("DEBUG", "true")
    with pytest.raises(ValidationError):
        make()
