import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_login_and_fetch_current_user(client: AsyncClient) -> None:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "full_name": "API User", "password": "strong-pass-123"},
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "user@example.com"

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "strong-pass-123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["full_name"] == "API User"


@pytest.mark.asyncio
async def test_login_rejects_invalid_credentials(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user2@example.com", "full_name": "API User 2", "password": "strong-pass-123"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user2@example.com", "password": "wrong-pass-123"},
    )
    assert response.status_code == 401
