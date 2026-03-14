# BioMedical POC

Biomedical platform scaffold with two implemented runtime areas:

- `KG_Framework/`: knowledge graph ingestion, normalization, audit snapshots, and Neo4j loading
- `Backend/API_Wrappers/`: FastAPI service with Postgres-backed auth, Postgres/Neo4j access, and Cypher-query-backed endpoints

## Repository Layout

- `Backend/API_Wrappers/`: backend API service
- `Backend/Agents/`: reserved for agent services
- `DB/Neo4j/CypherQueries/`: categorized reusable Cypher queries
- `DB/Postgres/PGQueries/`: categorized SQL for auth and reporting
- `DB/Sample_Data/Neo4j/`: versioned KG raw and processed snapshots
- `KG_Framework/`: KG pipeline implementation
- `Logs/KG_Logs/`: KG runtime logs

## KG Framework

The KG pipeline downloads Open Targets, Reactome, UniProt, BioGRID, and ChEMBL, writes normalized node/edge/relation CSVs, and loads Neo4j.

Main docs:
- [KG Framework README](/Users/nir_002/Dev/BioMedical_POC/KG_Framework/README.md)

Main run command:
```bash
docker compose -f KG_Framework/docker-compose.yml up --build
```

Key behavior:
- run snapshots are stored under `DB/Sample_Data/Neo4j/snapshots/YYYY/MM/DD/<run_id>/`
- same-day reruns replace that day’s snapshot by default
- Neo4j data itself persists in the Docker volume unless you remove volumes explicitly

Default local Neo4j access:
- Browser: `http://localhost:7475`
- Bolt: `bolt://localhost:7688`
- Username: `neo4j`

## Backend API

The backend is a Dockerized FastAPI service built with a layered structure:

- `core/`: config and security
- `db/`: Postgres and Neo4j clients
- `repositories/`: persistence/query access
- `services/`: business logic
- `api/routes/`: HTTP endpoints
- `schemas/`: request and response models

Implemented capabilities:
- user registration and login
- auth data stored in Postgres
- protected `/auth/me`
- protected Postgres summary endpoint
- protected Neo4j summary endpoint
- protected Cypher-query catalog and execution endpoints

Backend run command:
```bash
docker compose -f Backend/API_Wrappers/docker-compose.yml up --build
```

Backend test command:
```bash
docker compose -f Backend/API_Wrappers/docker-compose.yml --profile test run --rm backend-tests
```

Default backend local access:
- API: `http://localhost:8001`
- OpenAPI: `http://localhost:8001/docs`

## Cypher Query Endpoints

The backend exposes safe Neo4j query files from [DB/Neo4j/CypherQueries](/Users/nir_002/Dev/BioMedical_POC/DB/Neo4j/CypherQueries).

Exposed categories:
- `01_load_validation`
- `02_quality_checks`
- `03_exploration`

Not exposed through the API:
- `00_constraints`
- `04_subgraphs`
- `05_maintenance`

Endpoints:
- `GET /api/v1/data/neo4j/queries`
- `POST /api/v1/data/neo4j/queries/{query_id}`

Example:
```bash
curl -X POST http://localhost:8001/api/v1/data/neo4j/queries/03_exploration/04_disease_target_ranking \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"parameters":{"disease_node_id":"EFO:0000311"}}'
```

## Postgres SQL Library

Postgres queries are stored under [DB/Postgres/PGQueries](/Users/nir_002/Dev/BioMedical_POC/DB/Postgres/PGQueries):

- `01_schema/`: table and index creation
- `02_auth/`: user insert/select and login audit queries
- `03_reporting/`: summary/reporting queries

## Environment

Shared environment values are in [`.env`](/Users/nir_002/Dev/BioMedical_POC/.env).

The backend uses:
- `BACKEND_DATABASE_URL`
- `BACKEND_POSTGRES_*`
- `BACKEND_NEO4J_*`
- `BACKEND_JWT_*`

The KG framework uses:
- `OPEN_TARGETS_*`
- `REACTOME_*`
- `UNIPROT_*`
- `BIOGRID_*`
- `CHEMBL_*`
- `KG_*`
- `NEO4J_*`

## Validation

Verified commands:
- `docker compose -f KG_Framework/docker-compose.yml --profile test run --rm kg-tests`
- `docker compose -f Backend/API_Wrappers/docker-compose.yml --profile test run --rm backend-tests`
