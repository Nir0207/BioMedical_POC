from pydantic import BaseModel, Field


class CypherQueryDefinitionResponse(BaseModel):
    query_id: str
    category: str
    name: str
    description: str
    parameters: list[str]
    parameter_help: dict[str, str]
    endpoint_path: str


class CypherQueryExecutionRequest(BaseModel):
    parameters: dict[str, object] = Field(default_factory=dict)


class CypherQueryExecutionResponse(BaseModel):
    query_id: str
    record_count: int
    records: list[dict[str, object]]
