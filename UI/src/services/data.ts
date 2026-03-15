import { httpClient } from "./http";
import type {
  CypherQueryDefinition,
  CypherQueryExecutionResponse,
  GraphSummary,
  PostgresSummary,
  QueryCanvasCategory,
  QueryCanvasNode,
  QueryCanvasRelationValidationRequest,
  QueryCanvasRelationValidationResponse,
  QueryCanvasRunRequest,
  QueryCanvasRunResponse
} from "../types/api";

export async function fetchPostgresSummary(): Promise<PostgresSummary> {
  const response = await httpClient.get<PostgresSummary>("/api/v1/data/postgres/summary");
  return response.data;
}

export async function fetchNeo4jSummary(): Promise<GraphSummary> {
  const response = await httpClient.get<GraphSummary>("/api/v1/data/neo4j/summary");
  return response.data;
}

export async function fetchCypherQueries(): Promise<CypherQueryDefinition[]> {
  const response = await httpClient.get<CypherQueryDefinition[]>("/api/v1/data/neo4j/queries");
  return response.data;
}

export async function executeCypherQuery(
  endpointPath: string,
  parameters: Record<string, string | number>
): Promise<CypherQueryExecutionResponse> {
  const response = await httpClient.post<CypherQueryExecutionResponse>(endpointPath, { parameters });
  return response.data;
}

export async function fetchQueryCanvasCategories(): Promise<QueryCanvasCategory[]> {
  const response = await httpClient.get<QueryCanvasCategory[]>("/api/v1/data/neo4j/query-canvas/categories");
  return response.data;
}

export async function fetchQueryCanvasNodes(params: {
  category?: string | null;
  search?: string;
  limit?: number;
}): Promise<QueryCanvasNode[]> {
  const response = await httpClient.get<QueryCanvasNode[]>("/api/v1/data/neo4j/query-canvas/nodes", {
    params: {
      category: params.category ?? undefined,
      search: params.search ?? "",
      limit: params.limit ?? 24
    }
  });
  return response.data;
}

export async function validateQueryCanvasRelation(
  payload: QueryCanvasRelationValidationRequest
): Promise<QueryCanvasRelationValidationResponse> {
  const response = await httpClient.post<QueryCanvasRelationValidationResponse>(
    "/api/v1/data/neo4j/query-canvas/validate",
    payload
  );
  return response.data;
}

export async function runQueryCanvasRelation(payload: QueryCanvasRunRequest): Promise<QueryCanvasRunResponse> {
  const response = await httpClient.post<QueryCanvasRunResponse>("/api/v1/data/neo4j/query-canvas/run", payload);
  return response.data;
}
