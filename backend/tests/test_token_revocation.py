"""Refresh-token rotation, reuse detection, logout and the revocation denylist."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import TokenType, create_refresh_token, decode_token_claims
from app.models.user import User
from app.services import auth_service

REGISTER = {"email": "rot@example.com", "password": "supersecret123", "display_name": "Rot"}


def _register(client: TestClient) -> dict[str, str]:
    response = client.post("/api/v1/auth/register", json=REGISTER)
    assert response.status_code == 201
    return response.json()


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _refresh(client: TestClient, token: str) -> int:
    return client.post("/api/v1/auth/refresh", json={"refresh_token": token}).status_code


def _me(client: TestClient, token: str) -> int:
    return client.get("/api/v1/auth/me", headers=_bearer(token)).status_code


class TestRotation:
    def test_tokens_carry_unique_jti(self, client: TestClient):
        tokens = _register(client)
        access = decode_token_claims(tokens["access_token"], TokenType.ACCESS)
        refresh = decode_token_claims(tokens["refresh_token"], TokenType.REFRESH)
        assert access.jti != refresh.jti

    def test_refresh_returns_a_new_pair(self, client: TestClient):
        tokens = _register(client)
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert response.status_code == 200
        new = response.json()
        assert new["refresh_token"] != tokens["refresh_token"]
        assert _me(client, new["access_token"]) == 200

    def test_rotated_refresh_token_can_be_chained(self, client: TestClient):
        tokens = _register(client)
        second = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).json()
        assert _refresh(client, second["refresh_token"]) == 200

    def test_reused_refresh_token_is_rejected(self, client: TestClient):
        old = _register(client)["refresh_token"]
        assert _refresh(client, old) == 200
        assert _refresh(client, old) == 401

    def test_reuse_revokes_every_session_of_the_user(self, client: TestClient):
        tokens = _register(client)
        rotated = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).json()
        # Replay of the already-used token (attacker) ...
        assert _refresh(client, tokens["refresh_token"]) == 401
        # ... kills the legitimate, newer pair as well.
        assert _refresh(client, rotated["refresh_token"]) == 401
        assert _me(client, rotated["access_token"]) == 401

    def test_login_works_again_after_reuse_detection(self, client: TestClient, db: Session):
        old = _register(client)["refresh_token"]
        _refresh(client, old)
        _refresh(client, old)
        user = db.query(User).one()
        # Pretend the cutoff happened a few seconds ago so fresh tokens are newer.
        user.tokens_valid_after = datetime.now(UTC) - timedelta(seconds=5)
        db.flush()
        login = client.post(
            "/api/v1/auth/login",
            json={"email": REGISTER["email"], "password": REGISTER["password"]},
        )
        assert login.status_code == 200
        assert _me(client, login.json()["access_token"]) == 200

    def test_expired_refresh_token_is_rejected(self, client: TestClient, test_settings: Settings):
        claims = decode_token_claims(_register(client)["refresh_token"], TokenType.REFRESH)
        expired = jwt.encode(
            {
                "sub": str(claims.user_id),
                "type": "refresh",
                "jti": str(uuid.uuid4()),
                "iat": datetime.now(UTC) - timedelta(days=2),
                "exp": datetime.now(UTC) - timedelta(days=1),
            },
            test_settings.secret_key,
            algorithm=test_settings.jwt_algorithm,
        )
        assert _refresh(client, expired) == 401

    def test_token_without_jti_is_rejected(self, client: TestClient, test_settings: Settings):
        claims = decode_token_claims(_register(client)["refresh_token"], TokenType.REFRESH)
        legacy = jwt.encode(
            {
                "sub": str(claims.user_id),
                "type": "refresh",
                "iat": datetime.now(UTC),
                "exp": datetime.now(UTC) + timedelta(days=1),
            },
            test_settings.secret_key,
            algorithm=test_settings.jwt_algorithm,
        )
        assert _refresh(client, legacy) == 401


class TestLogout:
    def test_logout_revokes_access_and_refresh(self, client: TestClient):
        tokens = _register(client)
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers=_bearer(tokens["access_token"]),
        )
        assert response.status_code == 204
        assert _me(client, tokens["access_token"]) == 401
        assert _refresh(client, tokens["refresh_token"]) == 401

    def test_logout_without_refresh_token_still_revokes_access(self, client: TestClient):
        tokens = _register(client)
        response = client.post(
            "/api/v1/auth/logout", json={}, headers=_bearer(tokens["access_token"])
        )
        assert response.status_code == 204
        assert _me(client, tokens["access_token"]) == 401

    def test_logout_requires_authentication(self, client: TestClient):
        assert client.post("/api/v1/auth/logout", json={}).status_code == 401

    def test_logout_ignores_garbage_refresh_token(self, client: TestClient):
        tokens = _register(client)
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "garbage"},
            headers=_bearer(tokens["access_token"]),
        )
        assert response.status_code == 204

    def test_logout_does_not_revoke_another_users_refresh_token(self, client: TestClient):
        tokens = _register(client)
        other = client.post(
            "/api/v1/auth/register",
            json={"email": "other@example.com", "password": "supersecret123", "display_name": "O"},
        ).json()
        client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": other["refresh_token"]},
            headers=_bearer(tokens["access_token"]),
        )
        assert _refresh(client, other["refresh_token"]) == 200


class TestPurge:
    def test_purge_removes_only_expired_rows(self, client: TestClient, db: Session):
        tokens = _register(client)
        client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers=_bearer(tokens["access_token"]),
        )
        assert auth_service.purge_expired_revocations(db) == 0
        future = datetime.now(UTC) + timedelta(days=365)
        assert auth_service.purge_expired_revocations(db, now=future) == 2


def test_create_refresh_token_is_unique():
    user_id = uuid.uuid4()
    assert create_refresh_token(user_id) != create_refresh_token(user_id)


def test_default_access_token_lifetime_is_one_hour():
    assert Settings(_env_file=None).access_token_expire_minutes == 60
