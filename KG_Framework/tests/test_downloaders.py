from pathlib import Path
from unittest.mock import MagicMock

from kg_framework.downloaders.base import HTTPDownloader
from kg_framework.downloaders.sources import SourceDownloader


class DummyResponse:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self) -> None:
        return None

    def iter_content(self, chunk_size: int):
        del chunk_size
        return iter(self._chunks)


def test_file_downloader_writes_bytes(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "raw" / "payload.dat"

    monkeypatch.setattr(
        "kg_framework.downloaders.base.requests.get",
        lambda *args, **kwargs: DummyResponse([b"abc", b"123"]),
    )

    downloader = HTTPDownloader()
    output = downloader.download_file("https://example.org/file", target)

    assert output == target
    assert target.read_bytes() == b"abc123"


def test_source_downloader_builds_expected_destinations(temp_data_dirs) -> None:
    manifest_dir = temp_data_dirs["raw"].parent / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "sources.json").write_text(
        """
        {
          "sources": [
            {
              "name": "open_targets",
              "assets": [
                {
                  "name": "targets",
                  "url_env": "OPEN_TARGETS_TARGET_URL",
                  "destination_name": "targets",
                  "mode": "directory",
                  "allowed_suffixes": [".parquet"]
                }
              ]
            }
          ]
        }
        """.strip(),
        encoding="utf-8",
    )
    settings = MagicMock()
    settings.raw_data_dir = temp_data_dirs["raw"]
    settings.manifest_dir = manifest_dir
    settings.open_targets_target_url = "https://example.org/open_targets/targets/"

    downloader = SourceDownloader(settings)
    sources = downloader.get_sources()

    assert [source.name for source in sources] == ["open_targets"]
    assert sources[0].assets[0].destination_path(sources[0].root_dir(settings.raw_data_dir)) == temp_data_dirs["raw"] / "open_targets" / "targets"
