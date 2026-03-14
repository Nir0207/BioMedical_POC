import gzip
import sqlite3
from pathlib import Path

import polars as pl
import pytest

from kg_framework.pipelines import (
    BioGRIDPipeline,
    ChEMBLPipeline,
    OpenTargetsPipeline,
    ReactomePipeline,
    UniProtPipeline,
)


@pytest.fixture
def pipeline_settings(temp_data_dirs):
    class DummySettings:
        raw_data_dir = temp_data_dirs["raw"]
        processed_data_dir = temp_data_dirs["processed"]
        human_organism_id = 9606
        batch_size = 1000

    return DummySettings()


def test_open_targets_pipeline_generates_graph_files(pipeline_settings) -> None:
    raw_dir = pipeline_settings.raw_data_dir / "open_targets"
    (raw_dir / "targets").mkdir(parents=True, exist_ok=True)
    (raw_dir / "diseases").mkdir(parents=True, exist_ok=True)
    (raw_dir / "associations").mkdir(parents=True, exist_ok=True)

    pl.DataFrame(
        [{"id": "ENSG000001", "approvedSymbol": "TP53", "approvedName": "tumor protein p53", "biotype": "protein_coding"}]
    ).write_parquet(raw_dir / "targets" / "part-000.parquet")
    pl.DataFrame(
        [{"id": "EFO:0000311", "name": "cancer", "description": "Cancer disease", "therapeuticAreas": ["MONDO:0004992"]}]
    ).write_parquet(raw_dir / "diseases" / "part-000.parquet")
    pl.DataFrame(
        [{"targetId": "ENSG000001", "diseaseId": "EFO:0000311", "datasourceId": "ot_genetics_portal", "score": 0.83, "datatypeId": "genetic_association"}]
    ).write_parquet(raw_dir / "associations" / "part-000.parquet")

    node_path, edge_path, relation_path = OpenTargetsPipeline(pipeline_settings).run()

    assert pl.read_csv(node_path).height == 2
    assert pl.read_csv(edge_path)["relationship_type"].to_list() == ["ASSOCIATED_WITH"]
    assert pl.read_csv(relation_path)["relation_type"].to_list() == ["TARGET_DISEASE_ASSOCIATION"]


def test_reactome_pipeline_generates_graph_files(pipeline_settings) -> None:
    raw_dir = pipeline_settings.raw_data_dir / "reactome"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "ReactomePathways.txt").write_text("R-HSA-1\tPathway A\tHomo sapiens\n", encoding="utf-8")
    (
        raw_dir / "UniProt2Reactome_All_Levels.txt"
    ).write_text(
        "P04637\tR-HSA-1\thttps://reactome.org/PathwayBrowser/#/R-HSA-1\tPathway A\tTAS\tHomo sapiens\n",
        encoding="utf-8",
    )

    node_path, edge_path, relation_path = ReactomePipeline(pipeline_settings).run()

    assert pl.read_csv(node_path).height == 2
    assert pl.read_csv(edge_path)["relationship_type"].to_list() == ["PARTICIPATES_IN"]
    assert pl.read_csv(relation_path)["relation_type"].to_list() == ["PROTEIN_PATHWAY_MEMBERSHIP"]


def test_uniprot_pipeline_generates_graph_files(pipeline_settings) -> None:
    raw_dir = pipeline_settings.raw_data_dir / "uniprot"
    raw_dir.mkdir(parents=True, exist_ok=True)
    uniprot_text = (
        "Entry\tEntry Name\tProtein names\tGene Names\tOrganism\tLength\n"
        "P04637\tP53_HUMAN\tCellular tumor antigen p53\tTP53\tHomo sapiens\t393\n"
    )
    with gzip.open(raw_dir / "uniprot_human.tsv.gz", "wb") as handle:
        handle.write(uniprot_text.encode("utf-8"))
    with gzip.open(raw_dir / "uniprot_human.tsv.gz", "rb") as source:
        (raw_dir / "uniprot_human.tsv").write_bytes(source.read())

    node_path, edge_path, relation_path = UniProtPipeline(pipeline_settings).run()

    assert pl.read_csv(node_path).height == 2
    assert "GENE_SYMBOL:TP53" in pl.read_csv(node_path)["node_id"].to_list()
    assert pl.read_csv(edge_path)["relationship_type"].to_list() == ["ENCODES"]
    assert pl.read_csv(relation_path)["relation_type"].to_list() == ["GENE_PROTEIN_ENCODING"]


def test_biogrid_pipeline_generates_graph_files(pipeline_settings) -> None:
    raw_dir = pipeline_settings.raw_data_dir / "biogrid"
    raw_dir.mkdir(parents=True, exist_ok=True)
    content = (
        "#BioGRID Interaction ID\tEntrez Gene Interactor A\tEntrez Gene Interactor B\tBioGRID ID Interactor A\tBioGRID ID Interactor B\tSystematic Name Interactor A\tSystematic Name Interactor B\tOfficial Symbol Interactor A\tOfficial Symbol Interactor B\tSynonyms Interactor A\tSynonyms Interactor B\tExperimental System\tExperimental System Type\tAuthor\tPublication Source\tOrganism ID Interactor A\tOrganism ID Interactor B\tThroughput\tScore\tModification\tPhenotypes\tQualifications\tTags\tSource Database\tSwiss-Prot Accessions Interactor A\tSwiss-Prot Accessions Interactor B\n"
        "1\t7157\t5290\t1\t2\tSYSA\tSYSB\tTP53\tPIK3CA\t\t\tAffinity Capture-MS\tphysical\tDoe\tPMID:1\t9606\t9606\tHigh Throughput\t\t\t\t\t\tBioGRID\tP04637\tP42336\n"
    )
    (raw_dir / "BIOGRID-ALL-LATEST.tab3.txt").write_text(content, encoding="utf-8")

    node_path, edge_path, relation_path = BioGRIDPipeline(pipeline_settings).run()

    assert pl.read_csv(node_path).height == 2
    assert pl.read_csv(edge_path)["relationship_type"].to_list() == ["INTERACTS_WITH"]
    assert pl.read_csv(relation_path)["relation_type"].to_list() == ["PROTEIN_PROTEIN_INTERACTION"]


def test_chembl_pipeline_generates_graph_files(pipeline_settings) -> None:
    raw_dir = pipeline_settings.raw_data_dir / "chembl"
    raw_dir.mkdir(parents=True, exist_ok=True)
    db_path = raw_dir / "chembl.db"

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.executescript(
            """
            CREATE TABLE molecule_dictionary (molregno INTEGER PRIMARY KEY, chembl_id TEXT, pref_name TEXT, max_phase INTEGER);
            CREATE TABLE drug_mechanism (molregno INTEGER, tid INTEGER, mechanism_of_action TEXT, action_type TEXT);
            CREATE TABLE target_dictionary (tid INTEGER PRIMARY KEY, chembl_id TEXT);
            CREATE TABLE target_components (tid INTEGER, component_id INTEGER);
            CREATE TABLE component_sequences (component_id INTEGER PRIMARY KEY, accession TEXT);
            INSERT INTO molecule_dictionary VALUES (1, 'CHEMBL25', 'Aspirin', 4);
            INSERT INTO drug_mechanism VALUES (1, 10, 'Cyclooxygenase inhibition', 'INHIBITOR');
            INSERT INTO drug_mechanism VALUES (1, 10, 'Platelet aggregation reduction', 'MODULATOR');
            INSERT INTO target_dictionary VALUES (10, 'CHEMBLTARGET1');
            INSERT INTO target_components VALUES (10, 100);
            INSERT INTO component_sequences VALUES (100, 'P35354');
            """
        )
        connection.commit()

    node_path, edge_path, relation_path = ChEMBLPipeline(pipeline_settings).run()

    edge_df = pl.read_csv(edge_path)
    relation_df = pl.read_csv(relation_path)

    assert pl.read_csv(node_path).height == 2
    assert edge_df["relationship_type"].to_list() == ["TARGETS", "TARGETS"]
    assert edge_df["edge_id"].n_unique() == 2
    assert relation_df["relation_type"].to_list() == ["COMPOUND_TARGET_MECHANISM", "COMPOUND_TARGET_MECHANISM"]
