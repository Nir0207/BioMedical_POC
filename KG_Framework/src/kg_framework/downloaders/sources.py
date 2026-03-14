from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import json
from pathlib import Path

from kg_framework.config import Settings
from kg_framework.downloaders.base import HTTPDownloader


@dataclass(slots=True)
class SourceAsset:
    name: str
    url: str
    destination_name: str
    mode: str = "file"
    allowed_suffixes: tuple[str, ...] = (".parquet",)

    def destination_path(self, source_root: Path) -> Path:
        return source_root / self.destination_name


@dataclass(slots=True)
class SourceDefinition:
    name: str
    assets: list[SourceAsset]

    def root_dir(self, raw_data_dir: Path) -> Path:
        return raw_data_dir / self.name


class SourceDownloader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.downloader = HTTPDownloader()

    def get_sources(self) -> list[SourceDefinition]:
        manifest_path = self.settings.manifest_dir / "sources.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        sources: list[SourceDefinition] = []
        for source_payload in manifest["sources"]:
            assets = [
                SourceAsset(
                    name=asset_payload["name"],
                    url=getattr(self.settings, _env_name_to_field(asset_payload["url_env"])),
                    destination_name=asset_payload["destination_name"],
                    mode=asset_payload.get("mode", "file"),
                    allowed_suffixes=tuple(asset_payload.get("allowed_suffixes", [".parquet"])),
                )
                for asset_payload in source_payload["assets"]
            ]
            sources.append(SourceDefinition(name=source_payload["name"], assets=assets))
        return sources

    def get_source_map(self) -> dict[str, SourceDefinition]:
        return {source.name: source for source in self.get_sources()}

    def download_all(self) -> list[Path]:
        tasks = [(source, asset) for source in self.get_sources() for asset in source.assets]
        if not tasks:
            return []

        downloaded: list[Path] = []
        worker_count = max(1, min(self.settings.download_workers, len(tasks)))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(self._download_asset, source, asset) for source, asset in tasks]
            for future in as_completed(futures):
                downloaded.extend(future.result())
        return sorted(downloaded)

    def _download_asset(self, source: SourceDefinition, asset: SourceAsset) -> list[Path]:
        source_root = source.root_dir(self.settings.raw_data_dir)
        destination = asset.destination_path(source_root)
        if asset.mode == "directory":
            return self.downloader.download_directory(
                asset.url,
                destination,
                allowed_suffixes=asset.allowed_suffixes,
                max_workers=self.settings.download_workers,
            )

        archive_path = self.downloader.download_file(asset.url, destination)
        return self.downloader.extract_if_needed(archive_path)


def _env_name_to_field(env_name: str) -> str:
    return env_name.lower()
