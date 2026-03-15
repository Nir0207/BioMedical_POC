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

    async def fetch_query_canvas_categories(self) -> list[dict[str, object]]:
        return await self.neo4j_client.fetch_query_canvas_categories()

    async def search_query_canvas_nodes(self, category: str | None, search: str, limit: int) -> list[dict[str, object]]:
        return await self.neo4j_client.search_query_canvas_nodes(category=category, search=search, limit=limit)

    async def validate_query_canvas_relation(self, source_node_id: str, target_node_id: str) -> dict[str, object]:
        payload = await self.neo4j_client.validate_query_canvas_relation(source_node_id=source_node_id, target_node_id=target_node_id)
        generated_cypher, generated_parameters = self.neo4j_client.build_query_canvas_cypher(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            neighbor_limit=8,
        )
        related_to_types = payload["related_to_types"]
        relation_fact_types = payload["relation_fact_types"]
        exists = bool(related_to_types or relation_fact_types)
        return {
            "source": {
                "node_id": payload["source_node_id"],
                "name": payload["source_name"],
                "category": payload["source_category"],
                "labels": payload["source_labels"],
            },
            "target": {
                "node_id": payload["target_node_id"],
                "name": payload["target_name"],
                "category": payload["target_category"],
                "labels": payload["target_labels"],
            },
            "exists": exists,
            "related_to_types": related_to_types,
            "relation_fact_types": relation_fact_types,
            "message": (
                "Direct relation found between the selected nodes."
                if exists
                else "No direct RELATED_TO or HAS_RELATION_FACT relation exists between the selected nodes."
            ),
            "generated_cypher": generated_cypher,
            "parameters": generated_parameters,
        }

    async def run_query_canvas_relation(
        self,
        source_node_id: str,
        target_node_id: str,
        neighbor_limit: int,
        cypher: str | None = None,
        parameters: dict[str, object] | None = None,
    ) -> dict[str, object]:
        records, executed_cypher, executed_parameters = await self.neo4j_client.run_query_canvas_relation(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            neighbor_limit=neighbor_limit,
            cypher=cypher,
            parameters=parameters,
        )
        return {
            "query_id": "query_canvas_relation",
            "record_count": len(records),
            "records": records,
            "executed_cypher": executed_cypher,
            "parameters": executed_parameters,
        }
