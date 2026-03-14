from pathlib import Path

from kg_framework.config import Settings, get_settings


def test_settings_read_from_environment_and_create_directories(monkeypatch, tmp_path: Path) -> None:
    storage_root_dir = tmp_path / "neo4j"
    log_dir = tmp_path / "logs"
    manifest_dir = tmp_path / "manifests"

    monkeypatch.setenv("KG_STORAGE_ROOT_DIR", str(storage_root_dir))
    monkeypatch.setenv("KG_LOG_DIR", str(log_dir))
    monkeypatch.setenv("KG_MANIFEST_DIR", str(manifest_dir))
    monkeypatch.setenv("KG_RUN_ID", "20260314T101500")
    monkeypatch.setenv("KG_RESET_SAME_DAY_SNAPSHOTS", "true")
    monkeypatch.setenv("OPEN_TARGETS_TARGET_URL", "https://example.org/open_targets/targets/")
    monkeypatch.setenv("OPEN_TARGETS_DISEASE_URL", "https://example.org/open_targets/diseases/")
    monkeypatch.setenv("OPEN_TARGETS_ASSOCIATION_URL", "https://example.org/open_targets/associations/")
    monkeypatch.setenv("REACTOME_PATHWAYS_URL", "https://example.org/reactome/pathways.txt")
    monkeypatch.setenv("REACTOME_UNIPROT_PATHWAYS_URL", "https://example.org/reactome/uniprot_pathways.txt")
    monkeypatch.setenv("UNIPROT_PROTEINS_URL", "https://example.org/uniprot/proteins.tsv.gz")
    monkeypatch.setenv("BIOGRID_TAB3_URL", "https://example.org/biogrid/biogrid.zip")
    monkeypatch.setenv("CHEMBL_SQLITE_URL", "https://example.org/chembl/chembl.tar.gz")

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.storage_root_dir == storage_root_dir
    assert settings.run_root_dir == storage_root_dir / "snapshots" / "2026" / "03" / "14" / "20260314T101500"
    assert settings.raw_data_dir == settings.run_root_dir / "raw"
    assert settings.processed_data_dir == settings.run_root_dir / "processed"
    assert settings.log_dir == log_dir
    assert settings.manifest_dir == manifest_dir
    assert settings.raw_data_dir.exists()
    assert settings.processed_data_dir.exists()
    assert settings.metadata_dir.exists()
    assert log_dir.exists()


def test_settings_can_be_constructed_directly(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_TARGETS_TARGET_URL", "https://example.org/open_targets/targets/")
    monkeypatch.setenv("OPEN_TARGETS_DISEASE_URL", "https://example.org/open_targets/diseases/")
    monkeypatch.setenv("OPEN_TARGETS_ASSOCIATION_URL", "https://example.org/open_targets/associations/")
    monkeypatch.setenv("REACTOME_PATHWAYS_URL", "https://example.org/reactome/pathways.txt")
    monkeypatch.setenv("REACTOME_UNIPROT_PATHWAYS_URL", "https://example.org/reactome/uniprot_pathways.txt")
    monkeypatch.setenv("UNIPROT_PROTEINS_URL", "https://example.org/uniprot/proteins.tsv.gz")
    monkeypatch.setenv("BIOGRID_TAB3_URL", "https://example.org/biogrid/biogrid.zip")
    monkeypatch.setenv("CHEMBL_SQLITE_URL", "https://example.org/chembl/chembl.tar.gz")
    monkeypatch.setenv("KG_MANIFEST_DIR", "/tmp/manifests")
    monkeypatch.setenv("KG_STORAGE_ROOT_DIR", "/tmp/neo4j")
    monkeypatch.setenv("KG_RESET_SAME_DAY_SNAPSHOTS", "true")
    monkeypatch.setenv("KG_BATCH_SIZE", "1000")
    monkeypatch.setenv("KG_DOWNLOAD_WORKERS", "4")

    settings = Settings()

    assert settings.neo4j_uri == "bolt://neo4j:7687"
    assert settings.batch_size == 1000
    assert settings.download_workers == 4
    assert settings.run_root_dir.as_posix().startswith("/tmp/neo4j/snapshots/")


def test_same_day_snapshots_are_replaced_for_auto_generated_runs(monkeypatch, tmp_path: Path) -> None:
    storage_root_dir = tmp_path / "neo4j"
    stale_dir = storage_root_dir / "snapshots" / "2026" / "03" / "14" / "stale_run"
    stale_dir.mkdir(parents=True, exist_ok=True)
    (stale_dir / "stale.txt").write_text("stale", encoding="utf-8")

    monkeypatch.setenv("KG_STORAGE_ROOT_DIR", str(storage_root_dir))
    monkeypatch.setenv("KG_MANIFEST_DIR", str(tmp_path / "manifests"))
    monkeypatch.setenv("KG_RESET_SAME_DAY_SNAPSHOTS", "true")
    monkeypatch.delenv("KG_RUN_ID", raising=False)
    monkeypatch.setenv("OPEN_TARGETS_TARGET_URL", "https://example.org/open_targets/targets/")
    monkeypatch.setenv("OPEN_TARGETS_DISEASE_URL", "https://example.org/open_targets/diseases/")
    monkeypatch.setenv("OPEN_TARGETS_ASSOCIATION_URL", "https://example.org/open_targets/associations/")
    monkeypatch.setenv("REACTOME_PATHWAYS_URL", "https://example.org/reactome/pathways.txt")
    monkeypatch.setenv("REACTOME_UNIPROT_PATHWAYS_URL", "https://example.org/reactome/uniprot_pathways.txt")
    monkeypatch.setenv("UNIPROT_PROTEINS_URL", "https://example.org/uniprot/proteins.tsv.gz")
    monkeypatch.setenv("BIOGRID_TAB3_URL", "https://example.org/biogrid/biogrid.zip")
    monkeypatch.setenv("CHEMBL_SQLITE_URL", "https://example.org/chembl/chembl.tar.gz")

    class FrozenDateTime:
        @staticmethod
        def now():
            from datetime import datetime
            return datetime(2026, 3, 14, 10, 15, 0)

        @staticmethod
        def strptime(value, fmt):
            from datetime import datetime
            return datetime.strptime(value, fmt)

    monkeypatch.setattr("kg_framework.config.datetime", FrozenDateTime)

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.run_root_dir.exists()
    assert not stale_dir.exists()
