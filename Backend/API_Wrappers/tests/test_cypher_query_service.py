from pathlib import Path

import pytest
from fastapi import HTTPException

from biomedical_api.repositories.cypher_query_repository import CypherQueryRepository
from biomedical_api.services.cypher_query_service import CypherQueryService

QUERY_ROOT = Path("/app/db/Neo4j/CypherQueries")


class FakeNeo4jClient:
    def __init__(self) -> None:
        self.calls = []

    async def run_query(self, query: str, parameters: dict[str, object] | None = None) -> list[dict[str, object]]:
        self.calls.append((query, parameters))
        return [{"node_count": 10}]


def test_cypher_query_repository_lists_only_safe_queries() -> None:
    repository = CypherQueryRepository(QUERY_ROOT)
    queries = repository.list_safe_queries()

    query_ids = {query.query_id for query in queries}
    assert "00_constraints/01_core_constraints" in query_ids
    assert "01_load_validation/01_count_nodes_by_label" in query_ids
    assert "03_exploration/04_disease_target_ranking" in query_ids
    assert "04_subgraphs/01_export_disease_neighborhood" in query_ids
    assert "05_maintenance/01_delete_all_graph_data" not in query_ids
    disease_ranking_query = next(query for query in queries if query.query_id == "03_exploration/04_disease_target_ranking")
    assert "disease_node_id" in disease_ranking_query.parameter_help
    assert "Disease entity node_id" in disease_ranking_query.parameter_help["disease_node_id"]


@pytest.mark.asyncio
async def test_cypher_query_service_executes_query_with_parameters() -> None:
    repository = CypherQueryRepository(QUERY_ROOT)
    client = FakeNeo4jClient()
    service = CypherQueryService(client, repository)

    response = await service.execute_query(
        "03_exploration/04_disease_target_ranking",
        {"disease_node_id": "EFO:0000311"},
    )

    assert response["record_count"] == 1
    assert client.calls
    assert client.calls[0][1] == {"disease_node_id": "EFO:0000311"}


@pytest.mark.asyncio
async def test_cypher_query_service_rejects_missing_parameters() -> None:
    repository = CypherQueryRepository(QUERY_ROOT)
    client = FakeNeo4jClient()
    service = CypherQueryService(client, repository)

    with pytest.raises(HTTPException) as exc:
        await service.execute_query("03_exploration/04_disease_target_ranking", {})

    assert exc.value.status_code == 422
