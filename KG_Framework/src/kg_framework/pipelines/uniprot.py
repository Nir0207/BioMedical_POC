import polars as pl

from kg_framework.config import Settings
from kg_framework.models import GeneNode, GeneProteinEdge, ProteinNode, TypedRelationRecord
from kg_framework.pipelines.base import BasePipeline
from kg_framework.utils import first_existing_file, json_dumps


class UniProtPipeline(BasePipeline):
    source_name = "uniprot"

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    def run(self) -> tuple:
        self.logger.info("Running UniProt pipeline")

        tsv_path = first_existing_file(self.raw_dir, "uniprot_human.tsv")
        proteins = pl.read_csv(tsv_path, separator="\t")

        protein_nodes = []
        gene_nodes = []
        edges = []
        relations = []

        for row in proteins.iter_rows(named=True):
            accession = row["Entry"]
            gene_names = row.get("Gene Names", "") or ""
            gene_symbol = gene_names.split()[0] if gene_names else None

            protein_nodes.append(
                ProteinNode(
                    node_id=f"UNIPROT:{accession}",
                    name=row["Protein names"],
                    source="UniProt",
                    synonyms=gene_names,
                    organism=row.get("Organism"),
                    external_id=accession,
                    description=row["Entry Name"],
                    properties_json=json_dumps({"length": row.get("Length")}),
                )
            )

            if gene_symbol:
                gene_nodes.append(
                    GeneNode(
                        node_id=f"GENE_SYMBOL:{gene_symbol}",
                        name=gene_symbol,
                        source="UniProt",
                        synonyms=gene_names,
                        organism=row.get("Organism"),
                        external_id=gene_symbol,
                        description=row["Protein names"],
                        properties_json=json_dumps({"accession": accession}),
                    )
                )
                edge_id = f"UNIPROT::{gene_symbol}::{accession}"
                payload = {"entry_name": row["Entry Name"]}
                edges.append(
                    GeneProteinEdge(
                        edge_id=edge_id,
                        source_node_id=f"GENE_SYMBOL:{gene_symbol}",
                        target_node_id=f"UNIPROT:{accession}",
                        source="UniProt",
                        evidence="reviewed",
                        properties_json=json_dumps(payload),
                    )
                )
                relations.append(
                    TypedRelationRecord(
                        relation_id=edge_id,
                        relation_type="GENE_PROTEIN_ENCODING",
                        source_node_id=f"GENE_SYMBOL:{gene_symbol}",
                        target_node_id=f"UNIPROT:{accession}",
                        source="UniProt",
                        evidence="reviewed",
                        payload_json=json_dumps(payload),
                    )
                )

        node_path = self.csv_builder.write_nodes(
            _deduplicate_nodes(gene_nodes + protein_nodes),
            self.node_output,
        )
        edge_path = self.csv_builder.write_edges(edges, self.edge_output)
        relation_path = self.csv_builder.write_relations(relations, self.relation_output)
        return node_path, edge_path, relation_path


def _deduplicate_nodes(nodes):
    unique = {}
    for node in nodes:
        unique[node.node_id] = node
    return list(unique.values())
