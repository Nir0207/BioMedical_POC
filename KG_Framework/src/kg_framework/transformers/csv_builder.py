import logging
from pathlib import Path

import polars as pl

from kg_framework.models import GraphEdgeRecord, GraphNodeRecord, GraphRelationRecord
from kg_framework.schemas import EDGE_SCHEMA, NODE_SCHEMA, RELATION_SCHEMA


class CSVBuilder:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def write_nodes(self, nodes: list[GraphNodeRecord], output_path: Path) -> Path:
        frame = pl.DataFrame([node.model_dump() for node in nodes], schema=NODE_SCHEMA)
        self._write(frame, output_path)
        return output_path

    def write_edges(self, edges: list[GraphEdgeRecord], output_path: Path) -> Path:
        frame = pl.DataFrame([edge.model_dump() for edge in edges], schema=EDGE_SCHEMA)
        self._write(frame, output_path)
        return output_path

    def write_relations(self, relations: list[GraphRelationRecord], output_path: Path) -> Path:
        frame = pl.DataFrame([relation.model_dump() for relation in relations], schema=RELATION_SCHEMA)
        self._write(frame, output_path)
        return output_path

    def _write(self, frame: pl.DataFrame, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        frame.write_csv(output_path)
        self.logger.info("Wrote csv", extra={"output_path": str(output_path), "rows": frame.height})
