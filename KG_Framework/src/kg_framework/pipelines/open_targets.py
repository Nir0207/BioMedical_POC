import csv
from pathlib import Path

import pyarrow.dataset as ds

from kg_framework.config import Settings
from kg_framework.pipelines.base import BasePipeline
from kg_framework.schemas import EDGE_SCHEMA, NODE_SCHEMA, RELATION_SCHEMA
from kg_framework.utils import json_dumps


class OpenTargetsPipeline(BasePipeline):
    source_name = "open_targets"

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    def run(self) -> tuple[Path, Path, Path]:
        self.logger.info("Running Open Targets pipeline")

        target_dataset = ds.dataset(self.raw_dir / "targets", format="parquet")
        disease_dataset = ds.dataset(self.raw_dir / "diseases", format="parquet")
        association_dataset = ds.dataset(self.raw_dir / "associations", format="parquet")

        target_columns = set(target_dataset.schema.names)
        disease_columns = set(disease_dataset.schema.names)
        association_columns = set(association_dataset.schema.names)

        target_id_col = "id" if "id" in target_columns else "targetId"
        target_name_col = "approvedSymbol" if "approvedSymbol" in target_columns else "name"
        target_desc_col = "approvedName" if "approvedName" in target_columns else "description"

        disease_id_col = "id" if "id" in disease_columns else "diseaseId"
        disease_name_col = "name"
        disease_desc_col = "description" if "description" in disease_columns else None

        assoc_target_col = "targetId"
        assoc_disease_col = "diseaseId"
        assoc_source_col = "datasourceId" if "datasourceId" in association_columns else "sourceId"
        assoc_score_col = "score"

        scan_batch_size = max(100, min(self.settings.batch_size, 1000))

        self.logger.info("Writing Open Targets gene nodes", extra={"batch_size": scan_batch_size})

        self._write_target_nodes(
            dataset=target_dataset,
            target_id_col=target_id_col,
            target_name_col=target_name_col,
            target_desc_col=target_desc_col,
            include_biotype="biotype" in target_columns,
            output_path=self.node_output,
            scan_batch_size=scan_batch_size,
        )
        self.logger.info("Appending Open Targets disease nodes", extra={"batch_size": scan_batch_size})
        self._append_disease_nodes(
            dataset=disease_dataset,
            disease_id_col=disease_id_col,
            disease_name_col=disease_name_col,
            disease_desc_col=disease_desc_col,
            include_therapeutic_areas="therapeuticAreas" in disease_columns,
            output_path=self.node_output,
            scan_batch_size=scan_batch_size,
        )
        self.logger.info("Writing Open Targets association edges", extra={"batch_size": scan_batch_size})
        self._write_association_outputs(
            dataset=association_dataset,
            assoc_target_col=assoc_target_col,
            assoc_disease_col=assoc_disease_col,
            assoc_source_col=assoc_source_col,
            assoc_score_col=assoc_score_col,
            include_datatype="datatypeId" in association_columns,
            edge_output_path=self.edge_output,
            relation_output_path=self.relation_output,
            scan_batch_size=scan_batch_size,
        )

        return self.node_output, self.edge_output, self.relation_output

    def _write_target_nodes(
        self,
        dataset: ds.Dataset,
        target_id_col: str,
        target_name_col: str,
        target_desc_col: str | None,
        include_biotype: bool,
        output_path: Path,
        scan_batch_size: int,
    ) -> None:
        columns = [target_id_col, target_name_col]
        if target_desc_col:
            columns.append(target_desc_col)
        if include_biotype:
            columns.append("biotype")

        rows = (
            {
                "node_id": row.get(target_id_col, ""),
                "label": "Gene",
                "category": "gene",
                "name": row.get(target_name_col) or row.get(target_id_col, ""),
                "source": "OpenTargets",
                "synonyms": "",
                "organism": "Homo sapiens",
                "external_id": row.get(target_id_col),
                "description": row.get(target_desc_col) if target_desc_col else None,
                "properties_json": json_dumps(
                    {
                        "biotype": row.get("biotype"),
                        "approved_name": row.get(target_desc_col) if target_desc_col else None,
                    }
                ),
            }
            for batch in dataset.scanner(
                columns=columns,
                batch_size=scan_batch_size,
                batch_readahead=1,
                fragment_readahead=1,
                use_threads=False,
            ).to_batches()
            for row in batch.to_pylist()
        )
        self._write_csv_rows(output_path, NODE_SCHEMA.keys(), rows)

    def _append_disease_nodes(
        self,
        dataset: ds.Dataset,
        disease_id_col: str,
        disease_name_col: str,
        disease_desc_col: str | None,
        include_therapeutic_areas: bool,
        output_path: Path,
        scan_batch_size: int,
    ) -> None:
        columns = [disease_id_col, disease_name_col]
        if disease_desc_col:
            columns.append(disease_desc_col)
        if include_therapeutic_areas:
            columns.append("therapeuticAreas")

        rows = (
            {
                "node_id": row.get(disease_id_col, ""),
                "label": "Disease",
                "category": "disease",
                "name": row.get(disease_name_col, ""),
                "source": "OpenTargets",
                "synonyms": "",
                "organism": None,
                "external_id": row.get(disease_id_col),
                "description": row.get(disease_desc_col) if disease_desc_col else None,
                "properties_json": json_dumps(
                    {
                        "therapeutic_areas": row.get("therapeuticAreas"),
                    }
                ),
            }
            for batch in dataset.scanner(
                columns=columns,
                batch_size=scan_batch_size,
                batch_readahead=1,
                fragment_readahead=1,
                use_threads=False,
            ).to_batches()
            for row in batch.to_pylist()
        )
        self._write_csv_rows(output_path, NODE_SCHEMA.keys(), rows, append=True)

    def _write_association_outputs(
        self,
        dataset: ds.Dataset,
        assoc_target_col: str,
        assoc_disease_col: str,
        assoc_source_col: str,
        assoc_score_col: str,
        include_datatype: bool,
        edge_output_path: Path,
        relation_output_path: Path,
        scan_batch_size: int,
    ) -> None:
        columns = [assoc_target_col, assoc_disease_col, assoc_source_col, assoc_score_col]
        if include_datatype:
            columns.append("datatypeId")

        edge_rows = []
        relation_rows = []

        def iter_batches():
            for batch in dataset.scanner(
                columns=columns,
                batch_size=scan_batch_size,
                batch_readahead=1,
                fragment_readahead=1,
                use_threads=False,
            ).to_batches():
                for row in batch.to_pylist():
                    yield row

        for row in iter_batches():
            edge_id = f"OT::{row.get(assoc_target_col)}::{row.get(assoc_disease_col)}::{row.get(assoc_source_col)}"
            payload = {
                "datasource_id": row.get(assoc_source_col),
                "datatype_id": row.get("datatypeId"),
            }
            edge_rows.append(
                {
                    "edge_id": edge_id,
                    "source_node_id": row.get(assoc_target_col),
                    "target_node_id": row.get(assoc_disease_col),
                    "relationship_type": "ASSOCIATED_WITH",
                    "source": "OpenTargets",
                    "evidence": row.get(assoc_source_col),
                    "score": row.get(assoc_score_col),
                    "direction": None,
                    "properties_json": json_dumps(payload),
                }
            )
            relation_rows.append(
                {
                    "relation_id": edge_id,
                    "relation_type": "TARGET_DISEASE_ASSOCIATION",
                    "source_node_id": row.get(assoc_target_col),
                    "target_node_id": row.get(assoc_disease_col),
                    "source": "OpenTargets",
                    "evidence": row.get(assoc_source_col),
                    "score": row.get(assoc_score_col),
                    "payload_json": json_dumps(payload),
                }
            )

            if len(edge_rows) >= scan_batch_size:
                self._write_csv_rows(edge_output_path, EDGE_SCHEMA.keys(), edge_rows, append=edge_output_path.exists())
                self._write_csv_rows(
                    relation_output_path,
                    RELATION_SCHEMA.keys(),
                    relation_rows,
                    append=relation_output_path.exists(),
                )
                edge_rows.clear()
                relation_rows.clear()

        if edge_rows:
            self._write_csv_rows(edge_output_path, EDGE_SCHEMA.keys(), edge_rows, append=edge_output_path.exists())
            self._write_csv_rows(
                relation_output_path,
                RELATION_SCHEMA.keys(),
                relation_rows,
                append=relation_output_path.exists(),
            )

    def _write_csv_rows(
        self,
        output_path: Path,
        fieldnames,
        rows,
        append: bool = False,
    ) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with output_path.open(mode, newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
            if not append:
                writer.writeheader()
            for row in rows:
                writer.writerow(row)
