import logging
from pathlib import Path

from kg_framework.audit import RunAuditWriter
from kg_framework.config import Settings
from kg_framework.downloaders.sources import SourceDownloader
from kg_framework.loaders.neo4j_loader import Neo4jLoader
from kg_framework.pipelines import (
    BioGRIDPipeline,
    ChEMBLPipeline,
    OpenTargetsPipeline,
    ReactomePipeline,
    UniProtPipeline,
)


class KGOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        self.source_downloader = SourceDownloader(settings)
        self.audit_writer = RunAuditWriter(settings)
        self.pipelines = [
            OpenTargetsPipeline(settings),
            ReactomePipeline(settings),
            UniProtPipeline(settings),
            BioGRIDPipeline(settings),
            ChEMBLPipeline(settings),
        ]

    def run_downloads(self) -> list[Path]:
        self.logger.info("Starting source downloads")
        downloaded = self.source_downloader.download_all()
        self.audit_writer.write_manifest(self.source_downloader.get_sources(), downloaded_files=downloaded)
        return downloaded

    def run_pipelines(self) -> list[tuple[Path, Path, Path]]:
        self.logger.info("Starting pipeline execution")
        outputs = [pipeline.run() for pipeline in self.pipelines]
        self.audit_writer.write_manifest(self.source_downloader.get_sources(), outputs=outputs)
        return outputs

    def load_graph(self, outputs: list[tuple[Path, Path, Path]]) -> None:
        self.logger.info("Starting Neo4j graph load")
        loader = Neo4jLoader(self.settings)
        try:
            loader.ensure_constraints()
            for node_csv, edge_csv, relation_csv in outputs:
                loader.load_nodes(node_csv)
                loader.load_edges(edge_csv)
                loader.load_relations(relation_csv)
        finally:
            loader.close()
