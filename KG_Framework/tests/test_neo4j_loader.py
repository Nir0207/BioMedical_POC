import csv
from pathlib import Path

from kg_framework.loaders.neo4j_loader import Neo4jLoader


class FakeSession:
    def __init__(self) -> None:
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def run(self, query, **params):
        self.calls.append((query, params))


class FakeDriver:
    def __init__(self) -> None:
        self.session_instance = FakeSession()
        self.closed = False

    def session(self):
        return self.session_instance

    def close(self) -> None:
        self.closed = True


def build_settings(root_dir: Path, batch_size: int = 2):
    class DummySettings:
        neo4j_uri = "bolt://neo4j:7687"
        neo4j_username = "neo4j"
        neo4j_password = "password"
        storage_root_dir = root_dir

    DummySettings.batch_size = batch_size
    return DummySettings()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_neo4j_loader_creates_constraints_and_batches_node_rows(monkeypatch, tmp_path: Path) -> None:
    fake_driver = FakeDriver()
    monkeypatch.setattr(
        "kg_framework.loaders.neo4j_loader.GraphDatabase.driver",
        lambda *args, **kwargs: fake_driver,
    )

    settings = build_settings(tmp_path, batch_size=2)
    loader = Neo4jLoader(settings)

    node_csv = write_csv(
        tmp_path / "snapshots/2026/03/14/run123/processed/nodes/test_nodes.csv",
        [
            "node_id",
            "label",
            "category",
            "name",
            "source",
            "synonyms",
            "organism",
            "external_id",
            "description",
            "properties_json",
        ],
        [
            {
                "node_id": "N1",
                "label": "Gene",
                "category": "gene",
                "name": "Gene 1",
                "source": "Test",
                "synonyms": "",
                "organism": "Homo sapiens",
                "external_id": "N1",
                "description": "",
                "properties_json": "{}",
            },
            {
                "node_id": "N2",
                "label": "Gene",
                "category": "gene",
                "name": "Gene 2",
                "source": "Test",
                "synonyms": "",
                "organism": "Homo sapiens",
                "external_id": "N2",
                "description": "",
                "properties_json": "{}",
            },
            {
                "node_id": "N3",
                "label": "Disease",
                "category": "disease",
                "name": "Disease 3",
                "source": "Test",
                "synonyms": "",
                "organism": "",
                "external_id": "N3",
                "description": "",
                "properties_json": "{}",
            },
        ],
    )

    loader.ensure_constraints()
    loader.load_nodes(node_csv)
    loader.close()

    assert fake_driver.closed is True
    assert len(fake_driver.session_instance.calls) == 5
    assert "CREATE CONSTRAINT graph_node_id" in fake_driver.session_instance.calls[0][0]
    assert "UNWIND $rows AS row" in fake_driver.session_instance.calls[3][0]
    assert "LOAD CSV WITH HEADERS" not in fake_driver.session_instance.calls[3][0]
    assert "CALL {" not in fake_driver.session_instance.calls[3][0]
    assert "RETURN count(node) AS loaded" in fake_driver.session_instance.calls[3][0]
    assert len(fake_driver.session_instance.calls[3][1]["rows"]) == 2
    assert len(fake_driver.session_instance.calls[4][1]["rows"]) == 1


def test_neo4j_loader_batches_edges_and_relations(monkeypatch, tmp_path: Path) -> None:
    fake_driver = FakeDriver()
    monkeypatch.setattr(
        "kg_framework.loaders.neo4j_loader.GraphDatabase.driver",
        lambda *args, **kwargs: fake_driver,
    )

    settings = build_settings(tmp_path, batch_size=2)
    loader = Neo4jLoader(settings)

    edge_csv = write_csv(
        tmp_path / "snapshots/2026/03/14/run123/processed/edges/test_edges.csv",
        [
            "edge_id",
            "source_node_id",
            "target_node_id",
            "relationship_type",
            "source",
            "evidence",
            "score",
            "direction",
            "properties_json",
        ],
        [
            {
                "edge_id": "E1",
                "source_node_id": "N1",
                "target_node_id": "N2",
                "relationship_type": "ASSOCIATED_WITH",
                "source": "Test",
                "evidence": "manual",
                "score": "0.9",
                "direction": "",
                "properties_json": "{}",
            },
            {
                "edge_id": "E2",
                "source_node_id": "N2",
                "target_node_id": "N3",
                "relationship_type": "ASSOCIATED_WITH",
                "source": "Test",
                "evidence": "manual",
                "score": "0.8",
                "direction": "",
                "properties_json": "{}",
            },
            {
                "edge_id": "E3",
                "source_node_id": "N3",
                "target_node_id": "N4",
                "relationship_type": "ASSOCIATED_WITH",
                "source": "Test",
                "evidence": "manual",
                "score": "",
                "direction": "",
                "properties_json": "{}",
            },
        ],
    )
    relation_csv = write_csv(
        tmp_path / "snapshots/2026/03/14/run123/processed/relations/test_relations.csv",
        [
            "relation_id",
            "relation_type",
            "source_node_id",
            "target_node_id",
            "source",
            "evidence",
            "score",
            "payload_json",
        ],
        [
            {
                "relation_id": "R1",
                "relation_type": "FACT",
                "source_node_id": "N1",
                "target_node_id": "N2",
                "source": "Test",
                "evidence": "manual",
                "score": "0.5",
                "payload_json": "{}",
            },
            {
                "relation_id": "R2",
                "relation_type": "FACT",
                "source_node_id": "N2",
                "target_node_id": "N3",
                "source": "Test",
                "evidence": "manual",
                "score": "",
                "payload_json": "{}",
            },
            {
                "relation_id": "R3",
                "relation_type": "FACT",
                "source_node_id": "N3",
                "target_node_id": "N4",
                "source": "Test",
                "evidence": "manual",
                "score": "1.0",
                "payload_json": "{}",
            },
        ],
    )

    loader.load_edges(edge_csv)
    loader.load_relations(relation_csv)

    assert len(fake_driver.session_instance.calls) == 4
    edge_query = fake_driver.session_instance.calls[0][0]
    relation_query = fake_driver.session_instance.calls[2][0]
    assert "apoc.merge.relationship" in edge_query
    assert "HAS_RELATION_FACT" in relation_query
    assert "CALL {" not in edge_query
    assert "RETURN count(rel) AS loaded" in edge_query
    assert "RETURN count(r) AS loaded" in relation_query
    assert len(fake_driver.session_instance.calls[0][1]["rows"]) == 2
    assert len(fake_driver.session_instance.calls[1][1]["rows"]) == 1
    assert len(fake_driver.session_instance.calls[2][1]["rows"]) == 2
    assert len(fake_driver.session_instance.calls[3][1]["rows"]) == 1
