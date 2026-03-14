import json
from types import SimpleNamespace

from kg_framework.downloaders.sources import SourceDownloader


def test_manifest_driven_sources_are_loaded(temp_data_dirs) -> None:
    manifest_dir = temp_data_dirs["raw"].parent / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "sources.json"
    manifest_path.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "name": "reactome",
                        "assets": [
                            {
                                "name": "pathways",
                                "url_env": "REACTOME_PATHWAYS_URL",
                                "destination_name": "ReactomePathways.txt",
                                "mode": "file",
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    settings = SimpleNamespace(
        raw_data_dir=temp_data_dirs["raw"],
        manifest_dir=manifest_dir,
        reactome_pathways_url="https://example.org/reactome/pathways.txt",
    )

    sources = SourceDownloader(settings).get_sources()

    assert len(sources) == 1
    assert sources[0].name == "reactome"
    assert sources[0].assets[0].url == "https://example.org/reactome/pathways.txt"
