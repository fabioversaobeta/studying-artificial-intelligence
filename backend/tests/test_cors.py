from fastapi.testclient import TestClient

ORIGIN = "http://localhost:5173"


def test_preflight_allows_listed_origin_and_headers(client: TestClient):
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN


def test_preflight_rejects_unlisted_origin(client: TestClient):
    response = client.options(
        "/api/v1/auth/login",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_preflight_rejects_unlisted_header(client: TestClient):
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-custom-evil",
        },
    )
    assert response.status_code == 400
