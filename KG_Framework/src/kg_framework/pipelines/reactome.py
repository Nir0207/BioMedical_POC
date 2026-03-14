import polars as pl

from kg_framework.config import Settings
from kg_framework.models import PathwayNode, ProteinPathwayEdge, ProteinNode, TypedRelationRecord
from kg_framework.pipelines.base import BasePipeline
from kg_framework.utils import json_dumps


class ReactomePipeline(BasePipeline):
    source_name = "reactome"

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    def run(self) -> tuple:
        self.logger.info("Running Reactome pipeline")

        pathways = pl.read_csv(
            self.raw_dir / "ReactomePathways.txt",
            separator="\t",
            has_header=False,
            new_columns=["pathway_id", "pathway_name", "species"],
        ).filter(pl.col("species") == "Homo sapiens")

        mapping = pl.read_csv(
            self.raw_dir / "UniProt2Reactome_All_Levels.txt",
            separator="\t",
            has_header=False,
            new_columns=[
                "uniprot_accession",
                "pathway_id",
                "url",
                "pathway_name",
                "evidence_code",
                "species",
            ],
        ).filter(pl.col("species") == "Homo sapiens")

        pathway_nodes = [
            PathwayNode(
                node_id=row["pathway_id"],
                name=row["pathway_name"],
                source="Reactome",
                external_id=row["pathway_id"],
                organism=row["species"],
                properties_json=json_dumps({"reactome_url": None}),
            )
            for row in pathways.iter_rows(named=True)
        ]

        protein_nodes = [
            ProteinNode(
                node_id=f"UNIPROT:{row['uniprot_accession']}",
                name=row["uniprot_accession"],
                source="Reactome",
                external_id=row["uniprot_accession"],
                organism=row["species"],
                properties_json=json_dumps({"pathway_context": row["pathway_id"]}),
            )
            for row in mapping.select("uniprot_accession", "pathway_id", "species").unique().iter_rows(named=True)
        ]

        edges = []
        relations = []
        for row in mapping.iter_rows(named=True):
            edge_id = f"REACT::{row['uniprot_accession']}::{row['pathway_id']}"
            payload = {"reactome_url": row["url"], "evidence_code": row["evidence_code"]}
            edges.append(
                ProteinPathwayEdge(
                    edge_id=edge_id,
                    source_node_id=f"UNIPROT:{row['uniprot_accession']}",
                    target_node_id=row["pathway_id"],
                    source="Reactome",
                    evidence=row["evidence_code"],
                    properties_json=json_dumps(payload),
                )
            )
            relations.append(
                TypedRelationRecord(
                    relation_id=edge_id,
                    relation_type="PROTEIN_PATHWAY_MEMBERSHIP",
                    source_node_id=f"UNIPROT:{row['uniprot_accession']}",
                    target_node_id=row["pathway_id"],
                    source="Reactome",
                    evidence=row["evidence_code"],
                    payload_json=json_dumps(payload),
                )
            )

        node_path = self.csv_builder.write_nodes(pathway_nodes + protein_nodes, self.node_output)
        edge_path = self.csv_builder.write_edges(edges, self.edge_output)
        relation_path = self.csv_builder.write_relations(relations, self.relation_output)
        return node_path, edge_path, relation_path
