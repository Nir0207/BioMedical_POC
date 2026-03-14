import argparse
import logging
import sys

from kg_framework.audit import RunAuditWriter
from kg_framework.config import get_settings
from kg_framework.logging_config import configure_logging
from kg_framework.orchestrator import KGOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Biomedical KG framework CLI")
    parser.add_argument(
        "command",
        choices=["download", "transform", "load", "run-all"],
        help="Pipeline stage to execute",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()
    configure_logging(settings.log_dir, settings.log_level)

    logger = logging.getLogger("kg_framework.cli")
    orchestrator = KGOrchestrator(settings)
    audit_writer = RunAuditWriter(settings)

    try:
        if args.command == "download":
            orchestrator.run_downloads()
            return

        if args.command == "transform":
            orchestrator.run_pipelines()
            return

        if args.command == "load":
            outputs = orchestrator.run_pipelines()
            orchestrator.load_graph(outputs)
            return

        logger.info("Running end-to-end KG pipeline")
        orchestrator.run_downloads()
        outputs = orchestrator.run_pipelines()
        orchestrator.load_graph(outputs)
    except Exception as exc:
        logger.exception("KG pipeline execution failed", extra={"command": args.command})
        audit_writer.write_failure_manifest(
            sources=orchestrator.source_downloader.get_sources(),
            failed_stage=args.command,
            error_message=str(exc),
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
