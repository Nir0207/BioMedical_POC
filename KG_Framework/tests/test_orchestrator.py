from pathlib import Path
from unittest.mock import MagicMock

from kg_framework.orchestrator import KGOrchestrator


def test_orchestrator_runs_downloads(monkeypatch) -> None:
    settings = MagicMock()
    orchestrator = KGOrchestrator(settings)
    expected = [Path("/tmp/a"), Path("/tmp/b")]
    orchestrator.source_downloader = MagicMock()
    orchestrator.source_downloader.download_all.return_value = expected
    orchestrator.source_downloader.get_sources.return_value = []
    orchestrator.audit_writer = MagicMock()

    result = orchestrator.run_downloads()

    assert result == expected
    orchestrator.source_downloader.download_all.assert_called_once_with()
    orchestrator.audit_writer.write_manifest.assert_called_once()


def test_orchestrator_runs_all_pipelines(monkeypatch) -> None:
    settings = MagicMock()
    orchestrator = KGOrchestrator(settings)
    pipeline_a = MagicMock()
    pipeline_b = MagicMock()
    pipeline_a.run.return_value = ("nodes_a.csv", "edges_a.csv", "relations_a.csv")
    pipeline_b.run.return_value = ("nodes_b.csv", "edges_b.csv", "relations_b.csv")
    orchestrator.pipelines = [pipeline_a, pipeline_b]
    orchestrator.source_downloader = MagicMock()
    orchestrator.source_downloader.get_sources.return_value = []
    orchestrator.audit_writer = MagicMock()

    result = orchestrator.run_pipelines()

    assert result == [
        ("nodes_a.csv", "edges_a.csv", "relations_a.csv"),
        ("nodes_b.csv", "edges_b.csv", "relations_b.csv"),
    ]
    orchestrator.audit_writer.write_manifest.assert_called_once()


def test_orchestrator_loads_graph_outputs(monkeypatch) -> None:
    settings = MagicMock()
    loader = MagicMock()
    monkeypatch.setattr("kg_framework.orchestrator.Neo4jLoader", lambda current_settings: loader)

    orchestrator = KGOrchestrator(settings)
    outputs = [
        (Path("/tmp/nodes.csv"), Path("/tmp/edges.csv"), Path("/tmp/relations.csv")),
    ]

    orchestrator.load_graph(outputs)

    loader.ensure_constraints.assert_called_once_with()
    loader.load_nodes.assert_called_once_with(Path("/tmp/nodes.csv"))
    loader.load_edges.assert_called_once_with(Path("/tmp/edges.csv"))
    loader.load_relations.assert_called_once_with(Path("/tmp/relations.csv"))
    loader.close.assert_called_once_with()
