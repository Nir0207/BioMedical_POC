from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import json
import logging
import tarfile
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class DirectoryListingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


class HTTPDownloader:
    def __init__(self, timeout_seconds: int = 120) -> None:
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(self.__class__.__name__)

    @retry(wait=wait_exponential(min=2, max=20), stop=stop_after_attempt(3), reraise=True)
    def download_file(self, source_url: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info("Downloading source file", extra={"url": source_url, "destination": str(destination)})

        with requests.get(source_url, stream=True, timeout=self.timeout_seconds) as response:
            response.raise_for_status()
            with destination.open("wb") as file_handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file_handle.write(chunk)

        return destination

    def download_directory(
        self,
        source_url: str,
        destination: Path,
        allowed_suffixes: tuple[str, ...] = (".parquet",),
        max_workers: int = 4,
    ) -> list[Path]:
        destination.mkdir(parents=True, exist_ok=True)
        listing = requests.get(source_url, timeout=self.timeout_seconds)
        listing.raise_for_status()

        links = self._extract_links(listing.text)
        candidates: list[tuple[str, Path]] = []
        for href in links:
            if href.startswith("?") or href.startswith("/"):
                continue
            if not href.endswith(allowed_suffixes):
                continue
            file_url = urljoin(source_url, href)
            target_path = destination / Path(href).name
            candidates.append((file_url, target_path))

        if not candidates:
            return []

        worker_count = max(1, min(max_workers, len(candidates)))
        self.logger.info(
            "Downloading directory asset",
            extra={
                "url": source_url,
                "destination": str(destination),
                "file_count": len(candidates),
                "workers": worker_count,
            },
        )

        downloaded: list[Path] = []
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(self.download_file, file_url, target_path) for file_url, target_path in candidates]
            for future in as_completed(futures):
                downloaded.append(future.result())
        return sorted(downloaded)

    def extract_if_needed(self, archive_path: Path) -> list[Path]:
        if archive_path.suffix == ".zip":
            return self._extract_zip(archive_path)
        if archive_path.suffixes[-2:] == [".tar", ".gz"]:
            return self._extract_tar_gz(archive_path)
        if archive_path.suffix == ".gz" and archive_path.name.endswith((".txt.gz", ".tsv.gz", ".csv.gz")):
            return [self._extract_gzip(archive_path)]
        return [archive_path]

    def _extract_zip(self, archive_path: Path) -> list[Path]:
        extracted: list[Path] = []
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(archive_path.parent)
            extracted = [archive_path.parent / name for name in archive.namelist() if not name.endswith("/")]
        return extracted

    def _extract_tar_gz(self, archive_path: Path) -> list[Path]:
        extracted: list[Path] = []
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(archive_path.parent)
            extracted = [
                archive_path.parent / member.name
                for member in archive.getmembers()
                if member.isfile()
            ]
        return extracted

    def _extract_gzip(self, archive_path: Path) -> Path:
        target_path = archive_path.with_suffix("")
        with gzip.open(archive_path, "rb") as source_handle:
            with target_path.open("wb") as target_handle:
                target_handle.write(source_handle.read())
        return target_path

    def _extract_links(self, listing_text: str) -> list[str]:
        stripped = listing_text.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                candidates = payload.get("files") or payload.get("items") or payload.get("contents") or []
                return [item["name"] for item in candidates if isinstance(item, dict) and "name" in item]
            if isinstance(payload, list):
                return [item["name"] for item in payload if isinstance(item, dict) and "name" in item]

        parser = DirectoryListingParser()
        parser.feed(listing_text)
        return parser.links
