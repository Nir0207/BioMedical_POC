import csv
import logging
from pathlib import Path
from typing import Iterator

from neo4j import GraphDatabase

from kg_framework.config import Settings


class Neo4jLoader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        self.driver = GraphDatabase.driver(
            self.settings.neo4j_uri,
            auth=(self.settings.neo4j_username, self.settings.neo4j_password),
        )

    def close(self) -> None:
        self.driver.close()

    def ensure_constraints(self) -> None:
        statements = [
            "CREATE CONSTRAINT graph_node_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.node_id IS UNIQUE",
            "CREATE CONSTRAINT graph_edge_id IF NOT EXISTS FOR ()-[r:RELATED_TO]-() REQUIRE r.edge_id IS UNIQUE",
            "CREATE CONSTRAINT graph_relation_id IF NOT EXISTS FOR ()-[r:HAS_RELATION_FACT]-() REQUIRE r.relation_id IS UNIQUE",
        ]
        with self.driver.session() as session:
            for statement in statements:
                session.run(statement)

    def load_nodes(self, csv_path: Path) -> None:
        query = """
        UNWIND $rows AS row
        CALL apoc.merge.node(
            ['Entity', row.label],
            {node_id: row.node_id},
            {
                category: row.category,
                name: row.name,
                source: row.source,
                synonyms: row.synonyms,
                organism: row.organism,
                external_id: row.external_id,
                description: row.description,
                properties_json: row.properties_json
            }
        ) YIELD node
        RETURN count(node) AS loaded
        """
        self._run_batched_query(csv_path, query)

    def load_edges(self, csv_path: Path) -> None:
        query = """
        UNWIND $rows AS row
        MATCH (source:Entity {node_id: row.source_node_id})
        MATCH (target:Entity {node_id: row.target_node_id})
        CALL apoc.merge.relationship(
            source,
            'RELATED_TO',
            {edge_id: row.edge_id},
            {
                relationship_type: row.relationship_type,
                source: row.source,
                evidence: row.evidence,
                score: CASE WHEN row.score = '' THEN null ELSE toFloat(row.score) END,
                direction: row.direction,
                properties_json: row.properties_json
            },
            target
        ) YIELD rel
        RETURN count(rel) AS loaded
        """
        self._run_batched_query(csv_path, query)

    def load_relations(self, csv_path: Path) -> None:
        query = """
        UNWIND $rows AS row
        MATCH (source:Entity {node_id: row.source_node_id})
        MATCH (target:Entity {node_id: row.target_node_id})
        MERGE (source)-[r:HAS_RELATION_FACT {relation_id: row.relation_id, relation_type: row.relation_type}]->(target)
        SET r.source = row.source,
            r.evidence = row.evidence,
            r.score = CASE WHEN row.score = '' THEN null ELSE toFloat(row.score) END,
            r.payload_json = row.payload_json
        RETURN count(r) AS loaded
        """
        self._run_batched_query(csv_path, query)

    def _run_batched_query(self, csv_path: Path, query: str) -> None:
        self.logger.info("Loading csv into Neo4j", extra={"csv_path": str(csv_path), "batch_size": self.settings.batch_size})
        with self.driver.session() as session:
            for rows in self._iter_csv_batches(csv_path):
                session.run(query, rows=rows)

    def _iter_csv_batches(self, csv_path: Path) -> Iterator[list[dict[str, str]]]:
        batch: list[dict[str, str]] = []
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                batch.append(dict(row))
                if len(batch) >= self.settings.batch_size:
                    yield batch
                    batch = []
        if batch:
            yield batch
