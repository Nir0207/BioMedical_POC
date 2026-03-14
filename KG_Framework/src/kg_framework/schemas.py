import polars as pl


NODE_SCHEMA = {
    "node_id": pl.Utf8,
    "label": pl.Utf8,
    "category": pl.Utf8,
    "name": pl.Utf8,
    "source": pl.Utf8,
    "synonyms": pl.Utf8,
    "organism": pl.Utf8,
    "external_id": pl.Utf8,
    "description": pl.Utf8,
    "properties_json": pl.Utf8,
}

EDGE_SCHEMA = {
    "edge_id": pl.Utf8,
    "source_node_id": pl.Utf8,
    "target_node_id": pl.Utf8,
    "relationship_type": pl.Utf8,
    "source": pl.Utf8,
    "evidence": pl.Utf8,
    "score": pl.Float64,
    "direction": pl.Utf8,
    "properties_json": pl.Utf8,
}

RELATION_SCHEMA = {
    "relation_id": pl.Utf8,
    "relation_type": pl.Utf8,
    "source_node_id": pl.Utf8,
    "target_node_id": pl.Utf8,
    "source": pl.Utf8,
    "evidence": pl.Utf8,
    "score": pl.Float64,
    "payload_json": pl.Utf8,
}
