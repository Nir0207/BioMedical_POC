import logging
from pathlib import Path

from pythonjsonlogger.jsonlogger import JsonFormatter


def configure_logging(log_dir: Path, level: str = "INFO") -> None:
    log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())
    root_logger.handlers.clear()

    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(filename)s %(lineno)d"
    )

    info_handler = logging.FileHandler(log_dir / "kg_info.log")
    info_handler.setLevel(level.upper())
    info_handler.setFormatter(formatter)

    error_handler = logging.FileHandler(log_dir / "kg_error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level.upper())
    stream_handler.setFormatter(formatter)

    root_logger.addHandler(info_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(stream_handler)
