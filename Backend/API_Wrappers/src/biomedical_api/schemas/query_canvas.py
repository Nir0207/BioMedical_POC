from pydantic import BaseModel, Field


class QueryCanvasCategoryResponse(BaseModel):
    category: str
    count: int


class QueryCanvasNodeResponse(BaseModel):
    node_id: str
    name: str
    category: str
    labels: list[str]


class QueryCanvasRelationValidationRequest(BaseModel):
    source_node_id: str = Field(min_length=1)
    target_node_id: str = Field(min_length=1)


class QueryCanvasRelationValidationResponse(BaseModel):
    source: QueryCanvasNodeResponse
    target: QueryCanvasNodeResponse
    exists: bool
    related_to_types: list[str]
    relation_fact_types: list[str]
    message: str
    generated_cypher: str
    parameters: dict[str, object]


class QueryCanvasRunRequest(BaseModel):
    source_node_id: str = Field(min_length=1)
    target_node_id: str = Field(min_length=1)
    neighbor_limit: int = Field(default=8, ge=1, le=25)
    cypher: str | None = None
    parameters: dict[str, object] | None = None


class QueryCanvasRunResponse(BaseModel):
    query_id: str
    record_count: int
    records: list[dict[str, object]]
    executed_cypher: str
    parameters: dict[str, object]
