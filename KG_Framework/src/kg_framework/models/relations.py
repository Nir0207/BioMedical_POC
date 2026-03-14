from kg_framework.models.base import GraphEdgeRecord, GraphRelationRecord


class GeneProteinEdge(GraphEdgeRecord):
    relationship_type: str = "ENCODES"


class ProteinPathwayEdge(GraphEdgeRecord):
    relationship_type: str = "PARTICIPATES_IN"


class CompoundTargetEdge(GraphEdgeRecord):
    relationship_type: str = "TARGETS"


class InteractionEdge(GraphEdgeRecord):
    relationship_type: str = "INTERACTS_WITH"


class TargetDiseaseEdge(GraphEdgeRecord):
    relationship_type: str = "ASSOCIATED_WITH"


class TypedRelationRecord(GraphRelationRecord):
    pass
