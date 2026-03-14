import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from biomedical_api.api.dependencies import get_data_service
from biomedical_api.core.config import get_settings
from biomedical_api.db.postgres import Base, dispose_engine, get_engine, get_session_factory
from biomedical_api.main import create_app
from biomedical_api.repositories.cypher_query_repository import CypherQueryDefinition
from biomedical_api.services.data_service import DataService


class FakeNeo4jDataService(DataService):
    async def fetch_neo4j_summary(self) -> dict[str, int]:
        return {"nodes": 10, "relationships": 20}

    def list_cypher_queries(self) -> list[CypherQueryDefinition]:
        return [
            CypherQueryDefinition(
                query_id="00_constraints/01_core_constraints",
                category="00_constraints",
                name="01_core_constraints",
                description="Core graph constraints.",
                parameters=[],
                parameter_help={},
                path=None,  # type: ignore[arg-type]
            ),
            CypherQueryDefinition(
                query_id="01_load_validation/01_count_nodes_by_label",
                category="01_load_validation",
                name="01_count_nodes_by_label",
                description="Count nodes by domain label after a load.",
                parameters=[],
                parameter_help={},
                path=None,  # type: ignore[arg-type]
            ),
            CypherQueryDefinition(
                query_id="03_exploration/04_disease_target_ranking",
                category="03_exploration",
                name="04_disease_target_ranking",
                description="Rank targets for a disease by Open Targets score.",
                parameters=["disease_node_id"],
                parameter_help={"disease_node_id": "Disease entity node_id. Example: EFO:0000311"},
                path=None,  # type: ignore[arg-type]
            ),
            CypherQueryDefinition(
                query_id="04_subgraphs/01_export_disease_neighborhood",
                category="04_subgraphs",
                name="01_export_disease_neighborhood",
                description="Export disease neighborhood subgraph.",
                parameters=["disease_node_id"],
                parameter_help={"disease_node_id": "Disease entity node_id. Example: EFO:0000311"},
                path=None,  # type: ignore[arg-type]
            ),
        ]

    async def execute_cypher_query(self, query_id: str, parameters: dict[str, object] | None = None) -> dict[str, object]:
        if query_id == "03_exploration/04_disease_target_ranking" and not (parameters or {}).get("disease_node_id"):
            raise ValueError("missing parameter")
        return {
            "query_id": query_id,
            "record_count": 1,
            "records": [{"target.node_id": "ENSG000001", "score": 0.9}],
        }


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def reset_database(monkeypatch):
    monkeypatch.setenv("BACKEND_DATABASE_URL", "sqlite+aiosqlite:///./backend_api_test.db")
    monkeypatch.setenv("BACKEND_JWT_SECRET", "test-secret")
    await dispose_engine()
    get_settings.cache_clear()
    async with get_engine().begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield
    await dispose_engine()
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def app() -> AsyncGenerator:
    application = create_app()

    async def override_data_service():
        async with get_session_factory()() as session:
            yield FakeNeo4jDataService(session=session, neo4j_client=None)  # type: ignore[arg-type]

    application.dependency_overrides[get_data_service] = override_data_service
    yield application
    application.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as async_client:
        yield async_client
