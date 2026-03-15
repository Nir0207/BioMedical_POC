import pytest
from httpx import AsyncClient


async def _login(client: AsyncClient, email: str) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Canvas User", "password": "strong-pass-123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strong-pass-123"},
    )
    return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_query_canvas_lists_categories_and_nodes(client: AsyncClient) -> None:
    token = await _login(client, "canvas1@example.com")

    categories_response = await client.get(
        "/api/v1/data/neo4j/query-canvas/categories",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert categories_response.status_code == 200
    assert categories_response.json()[0]["category"] == "Gene"

    nodes_response = await client.get(
        "/api/v1/data/neo4j/query-canvas/nodes",
        params={"category": "Gene", "search": "TP53"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert nodes_response.status_code == 200
    assert nodes_response.json()[0]["node_id"] == "ENSG00000141510"


@pytest.mark.asyncio
async def test_query_canvas_validates_relation_and_runs_graph_query(client: AsyncClient) -> None:
    token = await _login(client, "canvas2@example.com")

    validation_response = await client.post(
        "/api/v1/data/neo4j/query-canvas/validate",
        headers={"Authorization": f"Bearer {token}"},
        json={"source_node_id": "ENSG00000141510", "target_node_id": "MONDO_0007254"},
    )
    assert validation_response.status_code == 200
    assert validation_response.json()["exists"] is True
    assert "ASSOCIATED_WITH" in validation_response.json()["related_to_types"]
    assert "MATCH (source:Entity" in validation_response.json()["generated_cypher"]
    assert validation_response.json()["parameters"]["source_node_id"] == "ENSG00000141510"

    run_response = await client.post(
        "/api/v1/data/neo4j/query-canvas/run",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source_node_id": "ENSG00000141510",
            "target_node_id": "MONDO_0007254",
            "neighbor_limit": 6,
            "cypher": "MATCH (source:Entity {node_id: $source_node_id}) MATCH (target:Entity {node_id: $target_node_id}) RETURN source, target",
            "parameters": {"custom_limit": 12},
        },
    )
    assert run_response.status_code == 200
    assert run_response.json()["query_id"] == "query_canvas_relation"
    assert run_response.json()["record_count"] == 2
    assert run_response.json()["executed_cypher"].startswith("MATCH (source:Entity")
    assert run_response.json()["parameters"]["custom_limit"] == 12


@pytest.mark.asyncio
async def test_query_canvas_validation_reports_missing_relation(client: AsyncClient) -> None:
    token = await _login(client, "canvas3@example.com")

    validation_response = await client.post(
        "/api/v1/data/neo4j/query-canvas/validate",
        headers={"Authorization": f"Bearer {token}"},
        json={"source_node_id": "UNIPROT:P04637", "target_node_id": "MONDO_9999999"},
    )
    assert validation_response.status_code == 200
    assert validation_response.json()["exists"] is False


@pytest.mark.asyncio
async def test_query_canvas_rejects_write_cypher_override(client: AsyncClient) -> None:
    token = await _login(client, "canvas4@example.com")

    run_response = await client.post(
        "/api/v1/data/neo4j/query-canvas/run",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source_node_id": "ENSG00000141510",
            "target_node_id": "MONDO_0007254",
            "neighbor_limit": 6,
            "cypher": "MATCH (n) DELETE n",
        },
    )
    assert run_response.status_code == 422
