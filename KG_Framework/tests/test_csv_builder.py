import polars as pl

from kg_framework.models import CompoundTargetEdge, GeneNode, TypedRelationRecord
from kg_framework.transformers.csv_builder import CSVBuilder


def test_csv_builder_writes_nodes_relations_and_edges(tmp_path) -> None:
    builder = CSVBuilder()
    nodes = [
        GeneNode(
            node_id="GENE:1",
            name="TP53",
            source="UnitTest",
            properties_json='{"species":"human"}',
        )
    ]
    edges = [
        CompoundTargetEdge(
            edge_id="EDGE:1",
            source_node_id="CHEMBL:1",
            target_node_id="GENE:1",
            source="UnitTest",
            score=0.9,
            properties_json='{"score":"0.9"}',
        )
    ]
    relations = [
        TypedRelationRecord(
            relation_id="REL:1",
            relation_type="COMPOUND_TARGET_MECHANISM",
            source_node_id="CHEMBL:1",
            target_node_id="GENE:1",
            source="UnitTest",
            score=0.9,
            payload_json='{"score":"0.9"}',
        )
    ]

    node_path = builder.write_nodes(nodes, tmp_path / "nodes.csv")
    edge_path = builder.write_edges(edges, tmp_path / "edges.csv")
    relation_path = builder.write_relations(relations, tmp_path / "relations.csv")

    node_df = pl.read_csv(node_path)
    edge_df = pl.read_csv(edge_path)
    relation_df = pl.read_csv(relation_path)

    assert node_df["node_id"].to_list() == ["GENE:1"]
    assert edge_df["edge_id"].to_list() == ["EDGE:1"]
    assert relation_df["relation_id"].to_list() == ["REL:1"]
