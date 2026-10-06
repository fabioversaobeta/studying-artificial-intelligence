from fastapi.testclient import TestClient

from tests.factories import API, register


def test_new_user_defaults_to_english(client: TestClient, auth_headers: dict[str, str]) -> None:
    me = client.get(f"{API}/auth/me", headers=auth_headers).json()
    assert me["preferred_language"] == "en"


def test_patch_updates_language_and_display_name(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.patch(
        f"{API}/users/me",
        headers=auth_headers,
        json={"preferred_language": "pt-BR", "display_name": "  Fábio  "},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["preferred_language"] == "pt-BR"
    assert body["display_name"] == "Fábio"

    again = client.get(f"{API}/auth/me", headers=auth_headers).json()
    assert again["preferred_language"] == "pt-BR"
    assert again["display_name"] == "Fábio"


def test_patch_is_partial(client: TestClient, auth_headers: dict[str, str]) -> None:
    client.patch(f"{API}/users/me", headers=auth_headers, json={"preferred_language": "pt-BR"})
    response = client.patch(f"{API}/users/me", headers=auth_headers, json={"display_name": "New"})
    assert response.status_code == 200
    assert response.json()["preferred_language"] == "pt-BR"
    assert response.json()["display_name"] == "New"


def test_patch_rejects_unsupported_language(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.patch(
        f"{API}/users/me", headers=auth_headers, json={"preferred_language": "fr"}
    )
    assert response.status_code == 422


def test_patch_rejects_blank_display_name(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.patch(f"{API}/users/me", headers=auth_headers, json={"display_name": "   "})
    assert response.status_code == 422


def test_patch_requires_authentication(client: TestClient) -> None:
    response = client.patch(f"{API}/users/me", json={"preferred_language": "pt-BR"})
    assert response.status_code == 401


def test_patch_only_touches_the_caller(client: TestClient) -> None:
    alice, _ = register(client, "alice@example.com")
    bob, _ = register(client, "bob@example.com")
    client.patch(f"{API}/users/me", headers=alice, json={"preferred_language": "pt-BR"})
    assert client.get(f"{API}/auth/me", headers=bob).json()["preferred_language"] == "en"
