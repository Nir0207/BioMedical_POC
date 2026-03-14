from pathlib import Path

import polars as pl

from kg_framework.downloaders.base import HTTPDownloader


class CSVDownloader(HTTPDownloader):
    def download_to_frame(self, source_url: str, destination: Path, **read_kwargs) -> pl.DataFrame:
        file_path = self.download_file(source_url=source_url, destination=destination)
        return pl.read_csv(file_path, **read_kwargs)
