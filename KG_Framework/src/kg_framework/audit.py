import json
from datetime import datetime, timezone
from pathlib import Path

from kg_framework.config import Settings
from kg_framework.downloaders.sources import SourceDefinition


class RunAuditWriter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def write_manifest(
        self,
        sources: list[SourceDefinition],
        downloaded_files: list[Path] | None = None,
        outputs: list[tuple[Path, Path, Path]] | None = None,
        status: str = "success",
        failed_stage: str | None = None,
        error_message: str | None = None,
    ) -> Path:
        payload = {
            "run_id": self.settings.effective_run_id,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "failed_stage": failed_stage,
            "error_message": error_message,
            "storage_root_dir": str(self.settings.storage_root_dir),
            "run_root_dir": str(self.settings.run_root_dir),
            "raw_data_dir": str(self.settings.raw_data_dir),
            "processed_data_dir": str(self.settings.processed_data_dir),
            "sources": [
                {
                    "name": source.name,
                    "assets": [
                        {
                            "name": asset.name,
                            "url": asset.url,
                            "destination_name": asset.destination_name,
                            "mode": asset.mode,
                        }
                        for asset in source.assets
                    ],
                }
                for source in sources
            ],
            "downloaded_files": [str(path) for path in downloaded_files or []],
            "outputs": [
                {
                    "nodes": str(node_path),
                    "edges": str(edge_path),
                    "relations": str(relation_path),
                }
                for node_path, edge_path, relation_path in (outputs or [])
            ],
        }
        manifest_path = self.settings.metadata_dir / "run_manifest.json"
        manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        latest_path = self.settings.storage_root_dir / "latest_run.json"
        latest_path.write_text(
            json.dumps(
                {
                    "run_id": self.settings.effective_run_id,
                    "run_root_dir": str(self.settings.run_root_dir),
                    "manifest_path": str(manifest_path),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return manifest_path

    def write_failure_manifest(
        self,
        sources: list[SourceDefinition],
        failed_stage: str,
        error_message: str,
    ) -> Path:
        return self.write_manifest(
            sources=sources,
            status="failed",
            failed_stage=failed_stage,
            error_message=error_message,
        )
