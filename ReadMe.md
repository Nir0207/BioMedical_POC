# BioMedical POC

Biomedical platform scaffold with three implemented runtime areas:

- `KG_Framework/`: knowledge graph ingestion, normalization, audit snapshots, and Neo4j loading
- `Backend/API_Wrappers/`: FastAPI service with Postgres-backed auth, Postgres/Neo4j access, and Cypher-query-backed endpoints
- `UI/`: React control surface for auth, analytics, graph exploration, and visual query composition

Biology/domain onboarding:
- [Bio_ReadMe.md](/Users/nir_002/Dev/BioMedical_POC/Bio_ReadMe.md)

## Repository Layout

- `Backend/API_Wrappers/`: backend API service
- `Backend/Agents/`: reserved for agent services
- `Bio_ReadMe.md`: biology/domain primer for this POC
- `DB/Neo4j/CypherQueries/`: categorized reusable Cypher queries
- `DB/Postgres/PGQueries/`: categorized SQL for auth and reporting
- `DB/Sample_Data/Neo4j/`: versioned KG raw and processed snapshots
- `KG_Framework/`: KG pipeline implementation
- `Logs/KG_Logs/`: KG runtime logs
- `UI/`: frontend app for login, dashboard, graph exploration, and query canvas

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
- protected per-file Cypher-query endpoints
- protected dynamic Query Canvas endpoints for node search, relation validation, and graph execution

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

## Neo4j Endpoint Surface

The backend exposes safe Neo4j query files from [DB/Neo4j/CypherQueries](/Users/nir_002/Dev/BioMedical_POC/DB/Neo4j/CypherQueries) and also provides dynamic endpoints for the visual Query Canvas.

Exposed categories:
- `00_constraints`
- `01_load_validation`
- `02_quality_checks`
- `03_exploration`
- `04_subgraphs`

Not exposed through the API:
- `05_maintenance`

Endpoints:
- `GET /api/v1/data/neo4j/queries`
- `POST /api/v1/data/neo4j/queries/{query_id}`
- `GET /api/v1/data/neo4j/query-canvas/categories`
- `GET /api/v1/data/neo4j/query-canvas/nodes`
- `POST /api/v1/data/neo4j/query-canvas/validate`
- `POST /api/v1/data/neo4j/query-canvas/run`

Example:
```bash
curl -X POST http://localhost:8001/api/v1/data/neo4j/queries/03_exploration/04_disease_target_ranking \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"parameters":{"disease_node_id":"MONDO_0007254"}}'
```

Query Canvas flow:
- fetch top node categories and searchable node suggestions from Neo4j
- add nodes from Neo4j suggestions or preset combinations
- validate whether a direct `RELATED_TO` or `HAS_RELATION_FACT` link exists
- review and edit the generated read-only Cypher in the right-side inspector
- run a dynamic graph query to open the result in a modal with graph controls on the right
- use `Run Default` to preload a known-valid example such as `ENSG00000141510 -> MONDO_0007254`

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

The UI uses:
- `VITE_API_BASE_URL`

## Frontend Notes

The graph UI currently uses:
- `react-force-graph-3d`
- `three`
- `three-spritetext`

Current graph behavior:
- Query Canvas graph results open only in a modal
- graph controls stay on the right side
- labels are rendered on the graph
- HTML export captures the rendered graph canvas and embeds the graph data payload

Recommended first graph run:
- source: `ENSG00000141510`
- target: `MONDO_0007254`

## Validation

Verified commands:
- `docker compose -f KG_Framework/docker-compose.yml --profile test run --rm kg-tests`
- `docker compose -f Backend/API_Wrappers/docker-compose.yml --profile test run --rm backend-tests`
- `docker compose -f UI/docker-compose.yml --profile test run --rm ui-tests`
- `docker compose -f UI/docker-compose.yml run --rm ui npm run build`
