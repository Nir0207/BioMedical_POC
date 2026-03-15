# Agentic-Workflow

Local-first bounded agentic workflow service for biomedical disease target discovery.

This module is intentionally scoped to the **agent layer only** and plugs into the existing graph/data stack without replacing `Backend/API_Wrappers`.

## Scope and intent
- Owns agent orchestration only (LangGraph state machine + fixed tools)
- Reads from Neo4j and Chroma evidence store
- Synthesizes a bounded answer using local Ollama models
- Does not own KG ingestion/ETL or generic graph API wrappers

## What this service provides
- FastAPI service at `/api/v1/agentic/research-query`
- Explicit LangGraph workflow state with conditional routing
- Fixed tool contracts only (no free-form DB tool execution)
- Hybrid retrieval:
  - graph retrieval from Neo4j
  - evidence retrieval from ChromaDB (`nomic-embed-text`)
- Optional token protection via `AGENTIC_API_TOKEN`

## Agentic UI behavior (current)
In the `UI` Agentic tab, the response surface is intentionally ordered as:
1. Research Query Composer + Execution Snapshot
2. Answer and Top Ranked Targets (immediately below query area)
3. Workflow Stage Monitor as a single-line breadcrumb/chip strip
4. Resolved Entities + Evidence Citations (side-by-side)
5. Graph Payload summary

Stage monitor states:
- `Idle`, `Running`, `Done`, `Partial`, `Failed`, `Skipped`

## Current workflow graph
1. Query intake
2. Intent/module router
3. Entity resolution (natural-language disease extraction + matching)
4. Graph query planning
5. Graph retrieval
6. Evidence retrieval
7. Optional ranking
8. Answer synthesis
9. Response formatting

Bounded paths:
- no entities found -> clarification-style failure response
- insufficient evidence -> graph-only guidance with explicit limitation
- ranking skipped when not needed

## Fixed tool contracts
- `search_disease`
- `search_gene`
- `search_protein`
- `get_disease_target_graph`
- `get_protein_neighbors`
- `get_pathway_context`
- `get_compounds_for_targets`
- `retrieve_evidence_chunks`
- `rank_targets`
- `build_graph_payload`

## Models (Ollama)
```bash
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
```

## Run locally with Docker
From `Backend/Agents/Agentic-Workflow`:
```bash
docker compose up --build agentic-api
```

Service URLs:
- `http://localhost:8011/api/v1/health`
- `http://localhost:8011/api/v1/agentic/research-query`

## Example request
```bash
curl -X POST "http://localhost:8011/api/v1/agentic/research-query" \
  -H "Content-Type: application/json" \
  -d '{"user_query":"For breast cancer, identify top target genes and summarize evidence","top_k":8}'
```

If `AGENTIC_API_TOKEN` is set, include:
```bash
-H "Authorization: Bearer <token>"
```

## Query guidance for better results
Best-performing prompt style right now:
- disease-focused research intent in one sentence
- include target/evidence objective

Examples:
- `For Parkinson disease, identify key targets and summarize evidence`
- `For breast carcinoma, list candidate target genes and rank by available evidence`
- `For rheumatoid arthritis, summarize target genes and pathway context`

## Recent hardening updates (Mar 2026)
- Disease resolver now uses alias/synonym-aware candidate expansion with confidence-gap handling.
- Graph retrieval moved from broad wildcard hops to schema-bounded relationship traversal (`RELATED_TO`, `HAS_RELATION_FACT`) for this graph shape.
- Compound intent queries now use known-drug fallback signals (ChEMBL/Open Targets relation facts) when explicit compound links are sparse.
- Evidence retrieval is disease-scoped first, with vector retrieval bounded by timeout so API responses stay responsive.

## Known limitations (current data shape)
- Evidence chunk retrieval quality still depends on Chroma indexing coverage.
- Some broad disease prompts may still resolve to a subtype; disambiguation notes are returned when confidence is close.
- Compound/protein/pathway outputs depend on explicit graph connectivity in the loaded snapshot.

## Recommended next hardening steps
- Add explicit UI-level disease disambiguation chip selection when multiple close matches are found.
- Materialize direct gene->protein canonical links for sources where only disease associations are currently loaded.
- Expand evidence ingestion so citations include richer source metadata (record IDs, confidence normalization).

## Run tests
Local:
```bash
cd backend
pytest -q
```

Docker:
```bash
docker compose --profile test up --build agentic-tests
```

## Notes
- Neo4j and Ollama must be available on host.
- On Docker Desktop (Windows), `host.docker.internal` resolves host services by default.
- If your graph label/property conventions differ, adjust:
  - `backend/src/agentic_api/services/graph_research_service.py`
  - `backend/src/agentic_api/workflows/research_workflow.py`
