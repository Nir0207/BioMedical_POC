from unittest.mock import MagicMock

from kg_framework import cli


def test_cli_download_command(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["kg-cli", "download"])
    monkeypatch.setattr("kg_framework.cli.get_settings", lambda: MagicMock(log_dir=".", log_level="INFO"))
    monkeypatch.setattr("kg_framework.cli.configure_logging", lambda *args, **kwargs: None)

    orchestrator = MagicMock()
    monkeypatch.setattr("kg_framework.cli.KGOrchestrator", lambda settings: orchestrator)

    cli.main()

    orchestrator.run_downloads.assert_called_once_with()


def test_cli_transform_command(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["kg-cli", "transform"])
    monkeypatch.setattr("kg_framework.cli.get_settings", lambda: MagicMock(log_dir=".", log_level="INFO"))
    monkeypatch.setattr("kg_framework.cli.configure_logging", lambda *args, **kwargs: None)

    orchestrator = MagicMock()
    monkeypatch.setattr("kg_framework.cli.KGOrchestrator", lambda settings: orchestrator)

    cli.main()

    orchestrator.run_pipelines.assert_called_once_with()


def test_cli_load_command_runs_transform_then_load(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["kg-cli", "load"])
    monkeypatch.setattr("kg_framework.cli.get_settings", lambda: MagicMock(log_dir=".", log_level="INFO"))
    monkeypatch.setattr("kg_framework.cli.configure_logging", lambda *args, **kwargs: None)

    orchestrator = MagicMock()
    orchestrator.run_pipelines.return_value = [("nodes.csv", "edges.csv", "relations.csv")]
    monkeypatch.setattr("kg_framework.cli.KGOrchestrator", lambda settings: orchestrator)

    cli.main()

    orchestrator.run_pipelines.assert_called_once_with()
    orchestrator.load_graph.assert_called_once_with([("nodes.csv", "edges.csv", "relations.csv")])


def test_cli_run_all_command_executes_full_flow(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["kg-cli", "run-all"])
    monkeypatch.setattr("kg_framework.cli.get_settings", lambda: MagicMock(log_dir=".", log_level="INFO"))
    monkeypatch.setattr("kg_framework.cli.configure_logging", lambda *args, **kwargs: None)

    orchestrator = MagicMock()
    orchestrator.run_pipelines.return_value = [("nodes.csv", "edges.csv", "relations.csv")]
    monkeypatch.setattr("kg_framework.cli.KGOrchestrator", lambda settings: orchestrator)

    cli.main()

    orchestrator.run_downloads.assert_called_once_with()
    orchestrator.run_pipelines.assert_called_once_with()
    orchestrator.load_graph.assert_called_once_with([("nodes.csv", "edges.csv", "relations.csv")])
