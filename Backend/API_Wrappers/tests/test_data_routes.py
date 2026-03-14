import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_summary_endpoints_require_auth_and_return_data(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "summary@example.com", "full_name": "Summary User", "password": "strong-pass-123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "summary@example.com", "password": "strong-pass-123"},
    )
    token = login_response.json()["access_token"]

    postgres_response = await client.get(
        "/api/v1/data/postgres/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert postgres_response.status_code == 200
    assert postgres_response.json()["user_count"] == 1

    neo4j_response = await client.get(
        "/api/v1/data/neo4j/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert neo4j_response.status_code == 200
    assert neo4j_response.json() == {"nodes": 10, "relationships": 20}
