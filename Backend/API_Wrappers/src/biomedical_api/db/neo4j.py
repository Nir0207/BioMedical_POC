from collections.abc import AsyncGenerator
from datetime import date, datetime
from decimal import Decimal
import re

from fastapi import HTTPException, status
from neo4j import AsyncGraphDatabase
from neo4j.graph import Node, Path, Relationship

from biomedical_api.core.config import get_settings


class Neo4jClient:
    _READ_ONLY_BLOCKLIST = re.compile(
        r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV|FOREACH|CALL\s+dbms|CALL\s+apoc\.periodic|CALL\s+apoc\.load|CALL\s+apoc\.import)\b",
        re.IGNORECASE,
    )

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
            records: list[dict[str, object]] = []
            async for record in result:
                records.append({key: self._normalize_value(record[key]) for key in record.keys()})
        return records

    def build_query_canvas_cypher(
        self,
        source_node_id: str,
        target_node_id: str,
        neighbor_limit: int,
    ) -> tuple[str, dict[str, object]]:
        query = """
        MATCH (source:Entity {node_id: $source_node_id})
        MATCH (target:Entity {node_id: $target_node_id})
        CALL (source, target) {
          OPTIONAL MATCH direct_path = (source)-[:RELATED_TO]-(target)
          WITH direct_path
          WHERE direct_path IS NOT NULL
          RETURN collect(direct_path) AS direct_paths
        }
        CALL (source, target) {
          OPTIONAL MATCH fact_path = (source)-[:HAS_RELATION_FACT]-(target)
          WITH fact_path
          WHERE fact_path IS NOT NULL
          RETURN collect(fact_path) AS fact_paths
        }
        CALL (source) {
          MATCH source_path = (source)-[:RELATED_TO]-(source_neighbor:Entity)
          WITH source_path
          LIMIT $neighbor_limit
          RETURN collect(source_path) AS source_paths
        }
        CALL (target) {
          MATCH target_path = (target)-[:RELATED_TO]-(target_neighbor:Entity)
          WITH target_path
          LIMIT $neighbor_limit
          RETURN collect(target_path) AS target_paths
        }
        WITH coalesce(direct_paths, []) + coalesce(fact_paths, []) + coalesce(source_paths, []) + coalesce(target_paths, []) AS candidate_paths
        UNWIND candidate_paths AS path
        RETURN DISTINCT path
        LIMIT 100
        """.strip()
        return query, {
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "neighbor_limit": neighbor_limit,
        }

    def ensure_read_only_query(self, query: str) -> None:
        normalized_query = query.strip()
        if not normalized_query:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cypher query cannot be empty")
        if self._READ_ONLY_BLOCKLIST.search(normalized_query):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only read-only Cypher queries are allowed from Query Canvas",
            )

    async def fetch_query_canvas_categories(self, limit: int = 8) -> list[dict[str, object]]:
        query = """
        MATCH (n:Entity)
        UNWIND [label IN labels(n) WHERE label <> 'Entity'] AS category
        RETURN category, count(*) AS count
        ORDER BY count DESC, category ASC
        LIMIT toInteger($limit)
        """
        return await self.run_query(query, {"limit": limit})

    async def search_query_canvas_nodes(
        self,
        category: str | None = None,
        search: str = "",
        limit: int = 24,
    ) -> list[dict[str, object]]:
        query = """
        MATCH (n:Entity)
        WHERE ($category = '' OR $category IN labels(n))
          AND (
            $search = ''
            OR toLower(coalesce(n.name, '')) CONTAINS toLower($search)
            OR toLower(n.node_id) CONTAINS toLower($search)
          )
        WITH n,
             coalesce(
               head([label IN labels(n) WHERE label <> 'Entity' AND ($category = '' OR label = $category)]),
               head([label IN labels(n) WHERE label <> 'Entity'])
             ) AS category
        RETURN
          n.node_id AS node_id,
          coalesce(n.name, n.node_id) AS name,
          category AS category,
          labels(n) AS labels
        ORDER BY
          CASE WHEN $search <> '' AND toLower(coalesce(n.name, '')) STARTS WITH toLower($search) THEN 0 ELSE 1 END,
          coalesce(n.name, n.node_id) ASC
        LIMIT toInteger($limit)
        """
        return await self.run_query(
            query,
            {
                "category": category or "",
                "search": search.strip(),
                "limit": limit,
            },
        )

    async def validate_query_canvas_relation(self, source_node_id: str, target_node_id: str) -> dict[str, object]:
        query = """
        MATCH (source:Entity {node_id: $source_node_id})
        MATCH (target:Entity {node_id: $target_node_id})
        OPTIONAL MATCH (source)-[related:RELATED_TO]-(target)
        WITH source, target,
             collect(DISTINCT related.relationship_type) AS related_to_types
        OPTIONAL MATCH (source)-[fact:HAS_RELATION_FACT]-(target)
        RETURN
          source.node_id AS source_node_id,
          coalesce(source.name, source.node_id) AS source_name,
          head([label IN labels(source) WHERE label <> 'Entity']) AS source_category,
          labels(source) AS source_labels,
          target.node_id AS target_node_id,
          coalesce(target.name, target.node_id) AS target_name,
          head([label IN labels(target) WHERE label <> 'Entity']) AS target_category,
          labels(target) AS target_labels,
          [item IN related_to_types WHERE item IS NOT NULL] AS related_to_types,
          [item IN collect(DISTINCT fact.relation_type) WHERE item IS NOT NULL] AS relation_fact_types
        """
        records = await self.run_query(query, {"source_node_id": source_node_id, "target_node_id": target_node_id})
        if not records:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both query canvas nodes were not found")
        return records[0]

    async def run_query_canvas_relation(
        self,
        source_node_id: str,
        target_node_id: str,
        neighbor_limit: int,
        cypher: str | None = None,
        parameters: dict[str, object] | None = None,
    ) -> tuple[list[dict[str, object]], str, dict[str, object]]:
        seed_records = await self.run_query(
            """
            MATCH (source:Entity {node_id: $source_node_id})
            MATCH (target:Entity {node_id: $target_node_id})
            RETURN source AS source_node, target AS target_node
            """,
            {"source_node_id": source_node_id, "target_node_id": target_node_id},
        )
        if not seed_records:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both query canvas nodes were not found")

        effective_cypher: str
        effective_parameters: dict[str, object]
        if cypher is None:
            effective_cypher, effective_parameters = self.build_query_canvas_cypher(
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                neighbor_limit=neighbor_limit,
            )
        else:
            self.ensure_read_only_query(cypher)
            effective_cypher = cypher.strip()
            effective_parameters = {
                "source_node_id": source_node_id,
                "target_node_id": target_node_id,
                "neighbor_limit": neighbor_limit,
                **(parameters or {}),
            }

        graph_paths = await self.run_query(effective_cypher, effective_parameters)
        return seed_records + graph_paths, effective_cypher, effective_parameters

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
            start_node_properties = dict(value.start_node)
            end_node_properties = dict(value.end_node)
            return {
                "id": value.id,
                "type": value.type,
                "start_node_id": value.start_node.id,
                "end_node_id": value.end_node.id,
                "properties": {
                    **dict(value),
                    "source_node_id": start_node_properties.get("node_id", value.start_node.id),
                    "target_node_id": end_node_properties.get("node_id", value.end_node.id),
                },
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
