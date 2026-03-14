from collections.abc import AsyncGenerator
from datetime import date, datetime
from decimal import Decimal

from neo4j import AsyncGraphDatabase
from neo4j.graph import Node, Path, Relationship

from biomedical_api.core.config import get_settings


class Neo4jClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )

    async def close(self) -> None:
        await self._driver.close()

    async def fetch_graph_summary(self) -> dict[str, int]:
        async with self._driver.session() as session:
            nodes_result = await session.run("MATCH (n) RETURN count(n) AS nodes")
            rels_result = await session.run("MATCH ()-[r]->() RETURN count(r) AS relationships")
            nodes_record = await nodes_result.single()
            rels_record = await rels_result.single()
        return {
            "nodes": int(nodes_record["nodes"]),
            "relationships": int(rels_record["relationships"]),
        }

    async def run_query(self, query: str, parameters: dict[str, object] | None = None) -> list[dict[str, object]]:
        async with self._driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
        return [self._normalize_record(record) for record in records]

    def _normalize_record(self, record: dict[str, object]) -> dict[str, object]:
        return {key: self._normalize_value(value) for key, value in record.items()}

    def _normalize_value(self, value: object) -> object:
        if isinstance(value, Node):
            return {
                "id": value.id,
                "labels": list(value.labels),
                "properties": dict(value),
            }
        if isinstance(value, Relationship):
            return {
                "id": value.id,
                "type": value.type,
                "start_node_id": value.start_node.id,
                "end_node_id": value.end_node.id,
                "properties": dict(value),
            }
        if isinstance(value, Path):
            return {
                "nodes": [self._normalize_value(node) for node in value.nodes],
                "relationships": [self._normalize_value(rel) for rel in value.relationships],
            }
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, list):
            return [self._normalize_value(item) for item in value]
        if isinstance(value, dict):
            return {key: self._normalize_value(item) for key, item in value.items()}
        return value


async def get_neo4j_client() -> AsyncGenerator[Neo4jClient, None]:
    client = Neo4jClient()
    try:
        yield client
    finally:
        await client.close()
