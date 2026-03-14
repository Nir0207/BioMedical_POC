import json
from pathlib import Path

import polars as pl


def json_dumps(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, default=str)


def first_existing_file(root: Path, pattern: str) -> Path:
    matches = sorted(root.rglob(pattern))
    if not matches:
        raise FileNotFoundError(f"No files matching {pattern} under {root}")
    return matches[0]


def concat_parquet_directory(directory: Path) -> pl.DataFrame:
    matches = sorted(directory.glob("*.parquet"))
    if not matches:
        raise FileNotFoundError(f"No parquet files found in {directory}")
    return pl.concat([pl.read_parquet(path) for path in matches], how="diagonal_relaxed")
