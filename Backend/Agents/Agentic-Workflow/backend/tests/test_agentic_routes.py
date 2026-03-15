from httpx import ASGITransport, AsyncClient
import pytest

from agentic_api.api.dependencies import get_agentic_service
from agentic_api.main import create_app


class FakeAgenticService:
    async def run_research_query(self, user_query: str, top_k: int) -> dict:
        return {
            "user_query": user_query,
            "normalized_query": user_query.lower(),
            "intent": "target_discovery",
            "module": "disease_target_discovery",
            "resolved_entities": [{"type": "Disease", "id": "MONDO_0007254", "name": "breast cancer"}],
            "final_answer": "Mocked graph-grounded answer",
            "citations": [{"id": "EV-001", "source": "Open Targets"}],
            "graph_payload": {"center_id": "MONDO_0007254", "nodes": [], "edges": []},
            "ranking_results": [{"gene_id": "ENSG00000141510", "score": 1.2}],
            "errors": [],
        }


@pytest.mark.asyncio
async def test_health_route_works():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_agentic_research_query_route():
    app = create_app()
    app.dependency_overrides[get_agentic_service] = lambda: FakeAgenticService()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agentic/research-query",
            json={"user_query": "Find targets for breast cancer", "top_k": 5},
            headers={"Authorization": "Bearer test-token"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "target_discovery"
    assert payload["resolved_entities"][0]["id"] == "MONDO_0007254"
    assert payload["citations"][0]["id"] == "EV-001"
