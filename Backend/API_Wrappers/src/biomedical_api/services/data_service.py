from sqlalchemy.ext.asyncio import AsyncSession

from biomedical_api.db.neo4j import Neo4jClient
from biomedical_api.repositories.cypher_query_repository import CypherQueryDefinition
from biomedical_api.repositories.user_repository import UserRepository
from biomedical_api.services.cypher_query_service import CypherQueryService


class DataService:
    def __init__(self, session: AsyncSession, neo4j_client: Neo4jClient) -> None:
        self.user_repository = UserRepository(session)
        self.neo4j_client = neo4j_client
        self.cypher_query_service = CypherQueryService(neo4j_client)

    async def fetch_postgres_summary(self) -> dict[str, int]:
        return {"user_count": await self.user_repository.count_users()}

    async def fetch_neo4j_summary(self) -> dict[str, int]:
        return await self.neo4j_client.fetch_graph_summary()

    def list_cypher_queries(self) -> list[CypherQueryDefinition]:
        return self.cypher_query_service.list_queries()

    async def execute_cypher_query(self, query_id: str, parameters: dict[str, object] | None = None) -> dict[str, object]:
        return await self.cypher_query_service.execute_query(query_id, parameters)
