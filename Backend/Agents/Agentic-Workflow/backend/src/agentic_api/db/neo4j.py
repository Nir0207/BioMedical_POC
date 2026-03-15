from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from neo4j import AsyncGraphDatabase
from neo4j.graph import Node, Path, Relationship

from agentic_api.core.config import get_settings


class Neo4jClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.database = settings.neo4j_database
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )

    async def close(self) -> None:
        await self.driver.close()

    async def run_query(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, parameters or {})
            rows: list[dict[str, Any]] = []
            async for record in result:
                rows.append({key: self._normalize(record[key]) for key in record.keys()})
            return rows

    def _normalize(self, value: Any) -> Any:
        if isinstance(value, Node):
            properties = dict(value)
            return {
                "id": properties.get("id") or properties.get("node_id") or str(value.id),
                "labels": list(value.labels),
                "properties": properties,
            }
        if isinstance(value, Relationship):
            props = dict(value)
            return {
                "id": str(value.id),
                "type": value.type,
                "start_node_id": props.get("source_node_id") or str(value.start_node.id),
                "end_node_id": props.get("target_node_id") or str(value.end_node.id),
                "properties": props,
            }
        if isinstance(value, Path):
            return {
                "nodes": [self._normalize(node) for node in value.nodes],
                "relationships": [self._normalize(rel) for rel in value.relationships],
            }
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, list):
            return [self._normalize(item) for item in value]
        if isinstance(value, dict):
            return {k: self._normalize(v) for k, v in value.items()}
        return value
