import logging
from abc import ABC, abstractmethod
from pathlib import Path

from kg_framework.config import Settings
from kg_framework.transformers.csv_builder import CSVBuilder


class BasePipeline(ABC):
    source_name: str

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        self.csv_builder = CSVBuilder()

    @property
    def raw_dir(self) -> Path:
        return self.settings.raw_data_dir / self.source_name

    @property
    def node_output(self) -> Path:
        return self.settings.processed_data_dir / "nodes" / f"{self.source_name}_nodes.csv"

    @property
    def relation_output(self) -> Path:
        return self.settings.processed_data_dir / "relations" / f"{self.source_name}_relations.csv"

    @property
    def edge_output(self) -> Path:
        return self.settings.processed_data_dir / "edges" / f"{self.source_name}_edges.csv"

    @abstractmethod
    def run(self) -> tuple[Path, Path, Path]:
        raise NotImplementedError
