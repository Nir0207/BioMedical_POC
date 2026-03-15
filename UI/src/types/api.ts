export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

export interface RegisterPayload {
  email: string;
  full_name: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface PostgresSummary {
  user_count: number;
}

export interface GraphSummary {
  nodes: number;
  relationships: number;
}

export interface CypherQueryDefinition {
  query_id: string;
  category: string;
  name: string;
  description: string;
  parameters: string[];
  parameter_help: Record<string, string>;
  endpoint_path: string;
}

export interface CypherQueryExecutionRequest {
  parameters: Record<string, string | number>;
}

export interface CypherQueryExecutionResponse {
  query_id: string;
  record_count: number;
  records: Array<Record<string, unknown>>;
}

export interface QueryCanvasCategory {
  category: string;
  count: number;
}

export interface QueryCanvasNode {
  node_id: string;
  name: string;
  category: string;
  labels: string[];
}

export interface QueryCanvasRelationValidationRequest {
  source_node_id: string;
  target_node_id: string;
}

export interface QueryCanvasRelationValidationResponse {
  source: QueryCanvasNode;
  target: QueryCanvasNode;
  exists: boolean;
  related_to_types: string[];
  relation_fact_types: string[];
  message: string;
  generated_cypher: string;
  parameters: Record<string, string | number>;
}

export interface QueryCanvasRunRequest {
  source_node_id: string;
  target_node_id: string;
  neighbor_limit: number;
  cypher?: string;
  parameters?: Record<string, string | number>;
}

export interface QueryCanvasRunResponse {
  query_id: string;
  record_count: number;
  records: Array<Record<string, unknown>>;
  executed_cypher: string;
  parameters: Record<string, string | number>;
}
