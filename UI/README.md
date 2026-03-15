# Biomedical UI

Dockerized React frontend for the biomedical backend and knowledge graph.

## Stack

- React + TypeScript + Vite
- Tailwind CSS + Material UI
- Axios + React Query
- React Router
- `react-force-graph-2d` for graph exploration
- Vitest + Testing Library + MSW

## Screens

- Login and registration
- Protected dashboard
- Query workbench for all non-maintenance Neo4j Cypher endpoints
- Interactive graph explorer for subgraph and path queries
- Query Canvas for drag-drop node composition, relation validation, and dynamic graph results

## Run

```bash
docker compose -f UI/docker-compose.yml up --build
```

App URL:

- `http://localhost:5173`

Expected backend URL:

- `http://localhost:8001`

Override with `VITE_API_BASE_URL` in the root [`.env`](/Users/nir_002/Dev/BioMedical_POC/.env).

## Test

```bash
docker compose -f UI/docker-compose.yml --profile test run --rm ui-tests
```

## Features

- JWT auth persisted in local storage
- Endpoint catalog pulled from backend metadata
- Per-query parameter help sourced from backend `.cypher` files
- Interactive force-directed graph rendering for Neo4j path and subgraph responses
- Visual Query Canvas with:
  - category-driven Neo4j node palette
  - horizontally scrollable node cards with hover details
  - node drag and drop into a workspace
  - single-node removal from the canvas
  - relation drawing between nodes
  - persistent right-side validation panel
  - generated Cypher editor populated after validation
  - preset "Run Default" combinations for quick demos
  - validation popup for direct relation existence
  - graph results opened in a modal with a right-side control rail

Recommended first combo:

- `ENSG00000141510` -> `MONDO_0007254` (`TP53` to `breast cancer`)

## Query Canvas API

The Query Canvas screen uses backend dynamic endpoints instead of static `.cypher` files:

- `GET /api/v1/data/neo4j/query-canvas/categories`
- `GET /api/v1/data/neo4j/query-canvas/nodes`
- `POST /api/v1/data/neo4j/query-canvas/validate`
- `POST /api/v1/data/neo4j/query-canvas/run`
