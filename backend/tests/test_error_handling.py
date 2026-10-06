from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.infrastructure.database.session import get_db
from app.main import app
from app.repositories import user_repository

REGISTER_URL = "/api/v1/auth/register"


class TestRegisterRace:
    def test_race_on_duplicate_email_returns_409(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ):
        payload = {"email": "race@example.com", "password": "supersecret123", "display_name": "R"}
        assert client.post(REGISTER_URL, json=payload).status_code == 201

        # Simulate the concurrent request that passed the pre-check before the
        # other one committed: the unique constraint is what stops it.
        monkeypatch.setattr(user_repository, "get_by_email", lambda db, email: None)
        response = client.post(REGISTER_URL, json=payload)

        assert response.status_code == 409
        assert response.json() == {
            "error": {"code": "conflict", "message": "An account with this email already exists"}
        }


class TestUnhandledError:
    def test_unexpected_exception_returns_standard_500(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ):
        def boom(db: Session, email: str):
            raise RuntimeError("secret internal detail")

        monkeypatch.setattr(user_repository, "get_by_email", boom)
        with TestClient(app, raise_server_exceptions=False) as c:
            response = c.post(
                REGISTER_URL,
                json={"email": "x@example.com", "password": "supersecret123", "display_name": "X"},
            )

        assert response.status_code == 500
        assert response.json() == {
            "error": {"code": "internal_error", "message": "Internal server error"}
        }
        assert "secret" not in response.text


class TestReadiness:
    def test_ready_when_database_is_up(self, client: TestClient):
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}

    def test_returns_503_without_details_when_database_fails(self):
        class BrokenSession:
            def execute(self, *args, **kwargs):
                raise OperationalError("SELECT 1", {}, Exception("connection refused host=db"))

        def broken_get_db() -> Generator[BrokenSession, None, None]:
            yield BrokenSession()

        app.dependency_overrides[get_db] = broken_get_db
        try:
            with TestClient(app, raise_server_exceptions=False) as c:
                response = c.get("/health/ready")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 503
        assert response.json() == {"status": "unavailable"}
