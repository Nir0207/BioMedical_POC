from pydantic import BaseModel, Field


class ResearchQueryRequest(BaseModel):
    user_query: str = Field(..., min_length=3)
    top_k: int = Field(default=8, ge=3, le=25)


class ResearchQueryResponse(BaseModel):
    user_query: str
    normalized_query: str
    intent: str
    module: str
    resolved_entities: list[dict]
    final_answer: str
    citations: list[dict]
    graph_payload: dict
    ranking_results: list[dict]
    errors: list[str] = Field(default_factory=list)
