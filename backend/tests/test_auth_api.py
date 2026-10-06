from fastapi.testclient import TestClient

from tests.auth_cookies import CSRF, refresh


class TestRegister:
    def test_register_returns_tokens(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "supersecret123",
                "display_name": "New User",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert "access_token" in body
        # The refresh token never appears in the body; it is an HttpOnly cookie.
        assert "refresh_token" not in body
        assert "refresh_token" in client.cookies
        assert body["token_type"] == "bearer"

    def test_duplicate_email_is_rejected(self, client: TestClient):
        payload = {"email": "dup@example.com", "password": "supersecret123", "display_name": "Dup"}
        first = client.post("/api/v1/auth/register", json=payload)
        second = client.post("/api/v1/auth/register", json=payload)
        assert first.status_code == 201
        assert second.status_code == 409

    def test_short_password_is_rejected(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "short@example.com", "password": "short", "display_name": "Short"},
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_with_correct_credentials(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "supersecret123",
                "display_name": "Login",
            },
        )
        response = client.post(
            "/api/v1/auth/login", json={"email": "login@example.com", "password": "supersecret123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_with_wrong_password_is_rejected(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpw@example.com",
                "password": "supersecret123",
                "display_name": "X",
            },
        )
        response = client.post(
            "/api/v1/auth/login", json={"email": "wrongpw@example.com", "password": "incorrect"}
        )
        assert response.status_code == 401

    def test_login_with_unknown_email_is_rejected(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/login", json={"email": "ghost@example.com", "password": "supersecret123"}
        )
        assert response.status_code == 401


class TestMe:
    def test_me_requires_authentication(self, client: TestClient):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_returns_current_user(self, client: TestClient, auth_headers: dict[str, str]):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["email"] == "tester@example.com"

    def test_me_rejects_garbage_token(self, client: TestClient):
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"})
        assert response.status_code == 401


class TestRefresh:
    def test_refresh_issues_new_access_token(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "supersecret123",
                "display_name": "R",
            },
        )
        response = client.post("/api/v1/auth/refresh", headers=CSRF)
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" not in response.json()

    def test_refresh_without_cookie_is_rejected(self, client: TestClient):
        assert client.post("/api/v1/auth/refresh", headers=CSRF).status_code == 401

    def test_refresh_ignores_a_token_in_the_body(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={"email": "b@example.com", "password": "supersecret123", "display_name": "B"},
        )
        token = client.cookies.get("refresh_token")
        client.cookies.clear()
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": token}, headers=CSRF)
        assert response.status_code == 401

    def test_refresh_rejects_an_access_token(
        self, client: TestClient, auth_headers: dict[str, str]
    ):
        access_token = auth_headers["Authorization"].split(" ")[1]
        assert refresh(client, access_token).status_code == 401
