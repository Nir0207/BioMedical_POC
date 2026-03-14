from kg_framework.models.base import GraphNodeRecord


class GeneNode(GraphNodeRecord):
    label: str = "Gene"
    category: str = "gene"


class ProteinNode(GraphNodeRecord):
    label: str = "Protein"
    category: str = "protein"


class PathwayNode(GraphNodeRecord):
    label: str = "Pathway"
    category: str = "pathway"


class CompoundNode(GraphNodeRecord):
    label: str = "Compound"
    category: str = "compound"


class DiseaseNode(GraphNodeRecord):
    label: str = "Disease"
    category: str = "disease"
