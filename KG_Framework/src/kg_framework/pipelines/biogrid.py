import polars as pl

from kg_framework.config import Settings
from kg_framework.models import InteractionEdge, ProteinNode, TypedRelationRecord
from kg_framework.pipelines.base import BasePipeline
from kg_framework.utils import first_existing_file, json_dumps


class BioGRIDPipeline(BasePipeline):
    source_name = "biogrid"

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    def run(self) -> tuple:
        self.logger.info("Running BioGRID pipeline")

        biogrid_path = first_existing_file(self.raw_dir, "*.tab3.txt")
        interactions = (
            pl.scan_csv(
                biogrid_path,
                separator="\t",
                null_values=["-", ""],
                schema_overrides={
                    "Entrez Gene Interactor A": pl.Utf8,
                    "Entrez Gene Interactor B": pl.Utf8,
                    "Organism ID Interactor A": pl.Int64,
                    "Organism ID Interactor B": pl.Int64,
                },
                infer_schema_length=10000,
            )
            .filter(
                (pl.col("Organism ID Interactor A") == self.settings.human_organism_id)
                & (pl.col("Organism ID Interactor B") == self.settings.human_organism_id)
            )
            .collect(streaming=True)
        )

        protein_nodes = {}
        edges = []
        relations = []

        for row in interactions.iter_rows(named=True):
            accession_a = _clean_accession(row.get("Swiss-Prot Accessions Interactor A"))
            accession_b = _clean_accession(row.get("Swiss-Prot Accessions Interactor B"))
            if not accession_a or not accession_b:
                continue

            node_a = ProteinNode(
                node_id=f"UNIPROT:{accession_a}",
                name=row.get("Official Symbol Interactor A") or accession_a,
                source="BioGRID",
                synonyms=row.get("Systematic Name Interactor A") or "",
                organism="Homo sapiens",
                external_id=accession_a,
                properties_json=json_dumps({"entrez_id": row.get("Entrez Gene Interactor A")}),
            )
            node_b = ProteinNode(
                node_id=f"UNIPROT:{accession_b}",
                name=row.get("Official Symbol Interactor B") or accession_b,
                source="BioGRID",
                synonyms=row.get("Systematic Name Interactor B") or "",
                organism="Homo sapiens",
                external_id=accession_b,
                properties_json=json_dumps({"entrez_id": row.get("Entrez Gene Interactor B")}),
            )
            protein_nodes[node_a.node_id] = node_a
            protein_nodes[node_b.node_id] = node_b

            edge_id = f"BIOGRID::{row['#BioGRID Interaction ID']}"
            payload = {
                "experimental_system": row.get("Experimental System"),
                "publication": row.get("Publication Source"),
            }
            edges.append(
                InteractionEdge(
                    edge_id=edge_id,
                    source_node_id=node_a.node_id,
                    target_node_id=node_b.node_id,
                    source="BioGRID",
                    evidence=row.get("Experimental System Type"),
                    properties_json=json_dumps(payload),
                )
            )
            relations.append(
                TypedRelationRecord(
                    relation_id=edge_id,
                    relation_type="PROTEIN_PROTEIN_INTERACTION",
                    source_node_id=node_a.node_id,
                    target_node_id=node_b.node_id,
                    source="BioGRID",
                    evidence=row.get("Experimental System Type"),
                    payload_json=json_dumps(payload),
                )
            )

        node_path = self.csv_builder.write_nodes(list(protein_nodes.values()), self.node_output)
        edge_path = self.csv_builder.write_edges(edges, self.edge_output)
        relation_path = self.csv_builder.write_relations(relations, self.relation_output)
        return node_path, edge_path, relation_path


def _clean_accession(value: str | None) -> str | None:
    if not value:
        return None
    return value.split("|")[0].strip()
