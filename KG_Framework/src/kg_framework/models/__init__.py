from kg_framework.models.base import GraphEdgeRecord, GraphNodeRecord, GraphRelationRecord
from kg_framework.models.entities import (
    CompoundNode,
    DiseaseNode,
    GeneNode,
    PathwayNode,
    ProteinNode,
)
from kg_framework.models.relations import (
    CompoundTargetEdge,
    GeneProteinEdge,
    InteractionEdge,
    ProteinPathwayEdge,
    TargetDiseaseEdge,
    TypedRelationRecord,
)

__all__ = [
    "CompoundNode",
    "CompoundTargetEdge",
    "DiseaseNode",
    "GeneNode",
    "GeneProteinEdge",
    "GraphEdgeRecord",
    "GraphNodeRecord",
    "GraphRelationRecord",
    "InteractionEdge",
    "PathwayNode",
    "ProteinNode",
    "ProteinPathwayEdge",
    "TargetDiseaseEdge",
    "TypedRelationRecord",
]
