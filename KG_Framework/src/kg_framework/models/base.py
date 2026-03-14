from pydantic import BaseModel, ConfigDict, Field


class GraphNodeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    node_id: str
    label: str
    category: str
    name: str
    source: str
    synonyms: str = ""
    organism: str | None = None
    external_id: str | None = None
    description: str | None = None
    properties_json: str = Field(default="{}")


class GraphEdgeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    edge_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    source: str
    evidence: str | None = None
    score: float | None = None
    direction: str | None = None
    properties_json: str = Field(default="{}")


class GraphRelationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    relation_id: str
    relation_type: str
    source_node_id: str
    target_node_id: str
    source: str
    evidence: str | None = None
    score: float | None = None
    payload_json: str = Field(default="{}")
