import pytest
from httpx import AsyncClient


async def _login(client: AsyncClient, email: str) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Cypher User", "password": "strong-pass-123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strong-pass-123"},
    )
    return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_list_cypher_queries_includes_endpoint_help(client: AsyncClient) -> None:
    token = await _login(client, "cypher@example.com")

    response = await client.get(
        "/api/v1/data/neo4j/queries",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 4
    assert payload[0]["query_id"] == "00_constraints/01_core_constraints"
    assert payload[0]["endpoint_path"] == "/api/v1/data/neo4j/queries/00_constraints/01_core_constraints"
    disease_query = next(item for item in payload if item["query_id"] == "03_exploration/04_disease_target_ranking")
    assert disease_query["parameter_help"]["disease_node_id"].startswith("Disease entity node_id")


@pytest.mark.asyncio
async def test_openapi_contains_one_route_per_cypher_file_except_maintenance(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/data/neo4j/queries/00_constraints/01_core_constraints" in paths
    assert "/api/v1/data/neo4j/queries/04_subgraphs/01_export_disease_neighborhood" in paths
    assert "/api/v1/data/neo4j/queries/05_maintenance/01_delete_all_graph_data" not in paths

    disease_ranking_operation = paths["/api/v1/data/neo4j/queries/03_exploration/04_disease_target_ranking"]["post"]
    assert "disease_node_id" in disease_ranking_operation["description"]
    assert "Disease entity node_id" in disease_ranking_operation["description"]


@pytest.mark.asyncio
async def test_execute_generated_cypher_route(client: AsyncClient) -> None:
    token = await _login(client, "cypher2@example.com")

    response = await client.post(
        "/api/v1/data/neo4j/queries/03_exploration/04_disease_target_ranking",
        headers={"Authorization": f"Bearer {token}"},
        json={"parameters": {"disease_node_id": "EFO:0000311"}},
    )

    assert response.status_code == 200
    assert response.json()["record_count"] == 1


@pytest.mark.asyncio
async def test_maintenance_query_route_is_not_exposed(client: AsyncClient) -> None:
    token = await _login(client, "cypher3@example.com")

    response = await client.post(
        "/api/v1/data/neo4j/queries/05_maintenance/01_delete_all_graph_data",
        headers={"Authorization": f"Bearer {token}"},
        json={"parameters": {}},
    )

    assert response.status_code == 404
