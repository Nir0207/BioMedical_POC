import sqlite3

from kg_framework.config import Settings
from kg_framework.models import CompoundNode, CompoundTargetEdge, ProteinNode, TypedRelationRecord
from kg_framework.pipelines.base import BasePipeline
from kg_framework.utils import first_existing_file, json_dumps


class ChEMBLPipeline(BasePipeline):
    source_name = "chembl"

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    def run(self) -> tuple:
        self.logger.info("Running ChEMBL pipeline")

        sqlite_path = first_existing_file(self.raw_dir, "*.db")
        query = """
        SELECT
            md.chembl_id AS molecule_chembl_id,
            md.pref_name AS molecule_name,
            md.max_phase AS max_phase,
            dm.mechanism_of_action AS mechanism_of_action,
            dm.action_type AS action_type,
            td.chembl_id AS target_chembl_id,
            cs.accession AS accession
        FROM drug_mechanism dm
        JOIN molecule_dictionary md ON md.molregno = dm.molregno
        JOIN target_dictionary td ON td.tid = dm.tid
        LEFT JOIN target_components tc ON tc.tid = td.tid
        LEFT JOIN component_sequences cs ON cs.component_id = tc.component_id
        WHERE md.chembl_id IS NOT NULL
          AND td.chembl_id IS NOT NULL
          AND cs.accession IS NOT NULL
        """

        with sqlite3.connect(sqlite_path) as connection:
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        compound_nodes = {}
        protein_nodes = {}
        edges = []
        relations = []

        for (
            molecule_chembl_id,
            molecule_name,
            max_phase,
            mechanism_of_action,
            action_type,
            target_chembl_id,
            accession,
        ) in rows:
            compound_nodes[molecule_chembl_id] = CompoundNode(
                node_id=f"CHEMBL:{molecule_chembl_id}",
                name=molecule_name or molecule_chembl_id,
                source="ChEMBL",
                external_id=molecule_chembl_id,
                properties_json=json_dumps({"max_phase": max_phase}),
            )
            protein_nodes[accession] = ProteinNode(
                node_id=f"UNIPROT:{accession}",
                name=accession,
                source="ChEMBL",
                external_id=accession,
                properties_json=json_dumps({"target_chembl_id": target_chembl_id}),
            )

            mechanism_key = mechanism_of_action or "unknown_mechanism"
            action_key = action_type or "unknown_action"
            edge_id = f"CHEMBL::{molecule_chembl_id}::{target_chembl_id}::{accession}::{action_key}::{mechanism_key}"
            payload = {
                "mechanism_of_action": mechanism_of_action,
                "action_type": action_type,
                "target_chembl_id": target_chembl_id,
            }
            edges.append(
                CompoundTargetEdge(
                    edge_id=edge_id,
                    source_node_id=f"CHEMBL:{molecule_chembl_id}",
                    target_node_id=f"UNIPROT:{accession}",
                    source="ChEMBL",
                    evidence=action_type,
                    properties_json=json_dumps(payload),
                )
            )
            relations.append(
                TypedRelationRecord(
                    relation_id=edge_id,
                    relation_type="COMPOUND_TARGET_MECHANISM",
                    source_node_id=f"CHEMBL:{molecule_chembl_id}",
                    target_node_id=f"UNIPROT:{accession}",
                    source="ChEMBL",
                    evidence=action_type,
                    payload_json=json_dumps(payload),
                )
            )

        node_path = self.csv_builder.write_nodes(
            list(compound_nodes.values()) + list(protein_nodes.values()),
            self.node_output,
        )
        edge_path = self.csv_builder.write_edges(edges, self.edge_output)
        relation_path = self.csv_builder.write_relations(relations, self.relation_output)
        return node_path, edge_path, relation_path
