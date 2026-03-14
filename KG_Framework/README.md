# KG Framework

Production-oriented biomedical knowledge graph pipeline built around `polars`, typed graph schemas, and Neo4j bulk loading.

## Layout

- `src/kg_framework/config.py`: environment-backed settings
- `manifests/sources.json`: manifest-driven source discovery
- `src/kg_framework/schemas.py`: explicit output schemas for nodes, edges, and relation facts
- `src/kg_framework/models/`: validated graph records
- `src/kg_framework/downloaders/`: multi-asset HTTP download and archive extraction
- `src/kg_framework/pipelines/`: real source-specific transforms for Open Targets, Reactome, UniProt, BioGRID, and ChEMBL
- `src/kg_framework/loaders/neo4j_loader.py`: APOC-backed Neo4j import interface with typed node labels and constrained edge imports
- `src/kg_framework/audit.py`: run manifest generation for audit/version tracking
- `notebooks/data_massage.ipynb`: notebook for QA, schema checks, and CSV inspection
- `DB/Sample_Data/Neo4j/snapshots/YYYY/MM/DD/<run_id>/raw/<source>/`: source-native downloads separated by provider
- `DB/Sample_Data/Neo4j/snapshots/YYYY/MM/DD/<run_id>/processed/{nodes,edges,relations}/`: normalized graph-ready CSV outputs
- `DB/Sample_Data/Neo4j/snapshots/YYYY/MM/DD/<run_id>/metadata/run_manifest.json`: audit manifest for each run

## Run

1. Copy `KG_Framework/.env.example` values into the parent [`.env`](/Users/nir_002/Dev/BioMedical_POC/.env) and adjust release URLs if needed.
   Default local Neo4j credentials are `neo4j / KGFramework_2026!` and the exposed ports are controlled by `KG_NEO4J_HTTP_PORT=7475` and `KG_NEO4J_BOLT_PORT=7688`.
   Set `KG_RUN_ID` only if you want to force a specific version label; otherwise each run creates a timestamped snapshot automatically.
   By default, rerunning on the same day clears that day’s existing Neo4j snapshots first via `KG_RESET_SAME_DAY_SNAPSHOTS=true`.
2. Start services:

```bash
docker compose -f KG_Framework/docker-compose.yml up --build
```

3. Run notebook server if needed:

```bash
docker compose -f KG_Framework/docker-compose.yml run --service-ports kg-pipeline jupyter lab --ip 0.0.0.0 --allow-root --no-browser
```

4. Run the containerized test suite:

```bash
docker compose -f KG_Framework/docker-compose.yml --profile test run --rm kg-tests
```

## Production Notes

- Source acquisition is driven by [manifests/sources.json](/Users/nir_002/Dev/BioMedical_POC/KG_Framework/manifests/sources.json), not hardcoded downloader definitions.
- Neo4j imports use transactional chunking to avoid single-transaction `LOAD CSV` bottlenecks on large files.
- Containerized tests are the primary validation path because the project dependencies are installed in the image.
- Every pipeline run is versioned under `DB/Sample_Data/Neo4j/snapshots/YYYY/MM/DD/<run_id>` and the latest pointer is written to `DB/Sample_Data/Neo4j/latest_run.json`.
- If you rerun without setting `KG_RUN_ID`, the pipeline deletes that day’s existing snapshot folder before recreating a fresh one to avoid same-day duplicate runs.

## Source coverage

- Open Targets: target, disease, and target-disease association parquet downloads
- Reactome: pathway catalog and UniProt-to-pathway mappings
- UniProt: reviewed human proteins via TSV stream
- BioGRID: Tab3 physical/genetic interaction archive
- ChEMBL: SQLite release archive for compound-target mechanism extraction
