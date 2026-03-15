import { agenticHttpClient } from "./http";
import type { AgenticResearchQueryRequest, AgenticResearchQueryResponse } from "../types/api";

export async function runAgenticResearchQuery(
  payload: AgenticResearchQueryRequest
): Promise<AgenticResearchQueryResponse> {
  const response = await agenticHttpClient.post<AgenticResearchQueryResponse>("/agentic/research-query", payload);
  return response.data;
}
