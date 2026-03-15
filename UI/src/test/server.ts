import { http, HttpResponse } from "msw";
import {
  mockAgenticResponse,
  mockCypherQueries,
  mockGraphResponse,
  mockGraphSummary,
  mockPostgresSummary,
  mockQueryCanvasCategories,
  mockQueryCanvasNodes,
  mockQueryCanvasRunResponse,
  mockQueryCanvasValidation,
  mockRankingResponse,
  mockUser
} from "./mockData";

export const handlers = [
  http.post("http://localhost:8001/api/v1/auth/register", async () => HttpResponse.json(mockUser, { status: 201 })),
  http.post("http://localhost:8001/api/v1/auth/login", async () =>
    HttpResponse.json({
      access_token: "test-token",
      token_type: "bearer"
    })
  ),
  http.get("http://localhost:8001/api/v1/auth/me", async () => HttpResponse.json(mockUser)),
  http.get("http://localhost:8001/api/v1/data/postgres/summary", async () => HttpResponse.json(mockPostgresSummary)),
  http.get("http://localhost:8001/api/v1/data/neo4j/summary", async () => HttpResponse.json(mockGraphSummary)),
  http.get("http://localhost:8001/api/v1/data/neo4j/queries", async () => HttpResponse.json(mockCypherQueries)),
  http.get("http://localhost:8001/api/v1/data/neo4j/query-canvas/categories", async () =>
    HttpResponse.json(mockQueryCanvasCategories)
  ),
  http.get("http://localhost:8001/api/v1/data/neo4j/query-canvas/nodes", async ({ request }) => {
    const url = new URL(request.url);
    const category = url.searchParams.get("category");
    const search = (url.searchParams.get("search") ?? "").toLowerCase();
    return HttpResponse.json(
      mockQueryCanvasNodes.filter(
        (node) =>
          (!category || node.category === category) &&
          (!search || node.name.toLowerCase().includes(search) || node.node_id.toLowerCase().includes(search))
      )
    );
  }),
  http.post("http://localhost:8001/api/v1/data/neo4j/query-canvas/validate", async () =>
    HttpResponse.json(mockQueryCanvasValidation)
  ),
  http.post("http://localhost:8001/api/v1/data/neo4j/query-canvas/run", async () =>
    HttpResponse.json(mockQueryCanvasRunResponse)
  ),
  http.post("http://localhost:8001/api/v1/data/neo4j/queries/03_exploration/04_disease_target_ranking", async () =>
    HttpResponse.json(mockRankingResponse)
  ),
  http.post("http://localhost:8001/api/v1/data/neo4j/queries/03_exploration/03_protein_pathway_membership", async () =>
    HttpResponse.json({
      query_id: "03_exploration/03_protein_pathway_membership",
      record_count: 1,
      records: mockGraphResponse.records
    })
  ),
  http.post("http://localhost:8001/api/v1/data/neo4j/queries/04_subgraphs/01_export_disease_neighborhood", async () =>
    HttpResponse.json(mockGraphResponse)
  ),
  http.post("http://localhost:8001/api/v1/data/neo4j/queries/04_subgraphs/02_export_compound_mechanism_subgraph", async () =>
    HttpResponse.json(mockGraphResponse)
  ),
  http.post("http://localhost:8001/api/v1/data/neo4j/queries/00_constraints/01_core_constraints", async () =>
    HttpResponse.json({
      query_id: "00_constraints/01_core_constraints",
      record_count: 0,
      records: []
    })
  ),
  http.post("http://localhost:8001/api/v1/data/neo4j/queries/01_load_validation/01_count_nodes_by_label", async () =>
    HttpResponse.json({
      query_id: "01_load_validation/01_count_nodes_by_label",
      record_count: 2,
      records: [
        { label: "Disease", count: 2400 },
        { label: "Gene", count: 18000 }
      ]
    })
  ),
  http.post("http://localhost:8011/api/v1/agentic/research-query", async () => HttpResponse.json(mockAgenticResponse))
];
