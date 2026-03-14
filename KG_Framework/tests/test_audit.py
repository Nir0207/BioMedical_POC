import json
from pathlib import Path
from types import SimpleNamespace

from kg_framework.audit import RunAuditWriter
from kg_framework.downloaders.sources import SourceAsset, SourceDefinition


def test_audit_writer_persists_run_manifest(tmp_path: Path) -> None:
    settings = SimpleNamespace(
        effective_run_id="20260314T101500",
        storage_root_dir=tmp_path,
        run_root_dir=tmp_path / "snapshots" / "2026" / "03" / "14" / "20260314T101500",
        raw_data_dir=tmp_path / "snapshots" / "2026" / "03" / "14" / "20260314T101500" / "raw",
        processed_data_dir=tmp_path / "snapshots" / "2026" / "03" / "14" / "20260314T101500" / "processed",
        metadata_dir=tmp_path / "snapshots" / "2026" / "03" / "14" / "20260314T101500" / "metadata",
    )
    settings.metadata_dir.mkdir(parents=True, exist_ok=True)
    source = SourceDefinition(
        name="reactome",
        assets=[SourceAsset(name="pathways", url="https://example.org/pathways.txt", destination_name="ReactomePathways.txt")],
    )

    manifest_path = RunAuditWriter(settings).write_manifest(
        [source],
        downloaded_files=[settings.raw_data_dir / "reactome" / "ReactomePathways.txt"],
        outputs=[(
            settings.processed_data_dir / "nodes" / "reactome_nodes.csv",
            settings.processed_data_dir / "edges" / "reactome_edges.csv",
            settings.processed_data_dir / "relations" / "reactome_relations.csv",
        )],
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    latest = json.loads((tmp_path / "latest_run.json").read_text(encoding="utf-8"))

    assert payload["run_id"] == "20260314T101500"
    assert payload["sources"][0]["name"] == "reactome"
    assert latest["run_id"] == "20260314T101500"
