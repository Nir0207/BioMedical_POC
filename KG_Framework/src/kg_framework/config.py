from functools import lru_cache
from datetime import datetime
from pathlib import Path
import shutil

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = "biomedical-kg-framework"
    log_level: str = Field(default="INFO", alias="KG_LOG_LEVEL")
    batch_size: int = Field(default=1000, alias="KG_BATCH_SIZE")
    download_workers: int = Field(default=4, alias="KG_DOWNLOAD_WORKERS")
    run_id: str | None = Field(default=None, alias="KG_RUN_ID")
    reset_same_day_snapshots: bool = Field(default=True, alias="KG_RESET_SAME_DAY_SNAPSHOTS")

    storage_root_dir: Path = Field(default=Path("/app/db_sample/Neo4j"), alias="KG_STORAGE_ROOT_DIR")
    notebook_dir: Path = Field(default=Path("/app/notebooks"), alias="KG_NOTEBOOK_DIR")
    log_dir: Path = Field(default=Path("/app/runtime_logs"), alias="KG_LOG_DIR")
    manifest_dir: Path = Field(default=Path("/app/manifests"), alias="KG_MANIFEST_DIR")
    neo4j_import_root: Path = Field(default=Path("/import"), alias="KG_NEO4J_IMPORT_ROOT")

    neo4j_uri: str = Field(default="bolt://neo4j:7687", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="neo4jpassword", alias="NEO4J_PASSWORD")

    human_organism_id: int = Field(default=9606, alias="KG_HUMAN_ORGANISM_ID")

    open_targets_target_url: str = Field(alias="OPEN_TARGETS_TARGET_URL")
    open_targets_disease_url: str = Field(alias="OPEN_TARGETS_DISEASE_URL")
    open_targets_association_url: str = Field(alias="OPEN_TARGETS_ASSOCIATION_URL")
    reactome_pathways_url: str = Field(alias="REACTOME_PATHWAYS_URL")
    reactome_uniprot_pathways_url: str = Field(alias="REACTOME_UNIPROT_PATHWAYS_URL")
    uniprot_proteins_url: str = Field(alias="UNIPROT_PROTEINS_URL")
    biogrid_tab3_url: str = Field(alias="BIOGRID_TAB3_URL")
    chembl_sqlite_url: str = Field(alias="CHEMBL_SQLITE_URL")

    @property
    def effective_run_id(self) -> str:
        return self.run_id or datetime.now().strftime("%Y%m%dT%H%M%S")

    @property
    def run_date_path(self) -> Path:
        run_dt = datetime.strptime(self.effective_run_id[:8], "%Y%m%d")
        return Path(str(run_dt.year)) / f"{run_dt.month:02d}" / f"{run_dt.day:02d}"

    @property
    def run_root_dir(self) -> Path:
        return self.storage_root_dir / "snapshots" / self.run_date_path / self.effective_run_id

    @property
    def raw_data_dir(self) -> Path:
        return self.run_root_dir / "raw"

    @property
    def processed_data_dir(self) -> Path:
        return self.run_root_dir / "processed"

    @property
    def metadata_dir(self) -> Path:
        return self.run_root_dir / "metadata"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    user_supplied_run_id = bool(settings.run_id)
    if not settings.run_id:
        settings.run_id = datetime.now().strftime("%Y%m%dT%H%M%S")
    if settings.reset_same_day_snapshots and not user_supplied_run_id:
        same_day_root = settings.storage_root_dir / "snapshots" / settings.run_date_path
        if same_day_root.exists():
            shutil.rmtree(same_day_root)
    settings.storage_root_dir.mkdir(parents=True, exist_ok=True)
    settings.run_root_dir.mkdir(parents=True, exist_ok=True)
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
    (settings.processed_data_dir / "nodes").mkdir(parents=True, exist_ok=True)
    (settings.processed_data_dir / "edges").mkdir(parents=True, exist_ok=True)
    (settings.processed_data_dir / "relations").mkdir(parents=True, exist_ok=True)
    settings.metadata_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    settings.manifest_dir.mkdir(parents=True, exist_ok=True)
    return settings
