from pathlib import Path

import pytest


@pytest.fixture
def temp_data_dirs(tmp_path: Path) -> dict[str, Path]:
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    log_dir = tmp_path / "logs"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    return {
        "raw": raw_dir,
        "processed": processed_dir,
        "logs": log_dir,
    }
