from __future__ import annotations

from typing import Any

from agentic_api.retrieval.hybrid_retriever import HybridRetriever
from agentic_api.services.graph_research_service import GraphResearchService


class FixedResearchTools:
    """Fixed tools used by LangGraph nodes. No free-form DB access."""

    def __init__(self, graph_service: GraphResearchService, hybrid_retriever: HybridRetriever) -> None:
        self.graph_service = graph_service
        self.hybrid_retriever = hybrid_retriever

    async def search_disease(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return await self.graph_service.search_disease(query=query, limit=limit)

    async def search_gene(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return await self.graph_service.search_gene(query=query, limit=limit)

    async def search_protein(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return await self.graph_service.search_protein(query=query, limit=limit)

    async def get_disease_target_graph(self, disease_id: str, limit: int = 100) -> dict[str, Any]:
        return await self.graph_service.get_disease_target_graph(disease_id=disease_id, limit=limit)

    async def get_protein_neighbors(self, protein_id: str, depth: int = 2) -> dict[str, Any]:
        return await self.graph_service.get_protein_neighbors(protein_id=protein_id, depth=depth)

    async def get_pathway_context(self, protein_ids: list[str], limit: int = 100) -> list[dict[str, Any]]:
        return await self.graph_service.get_pathway_context_for_proteins(protein_ids=protein_ids, limit=limit)

    async def get_compounds_for_targets(
        self,
        protein_ids: list[str],
        target_gene_ids: list[str] | None = None,
        disease_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return await self.graph_service.get_compounds_for_targets(
            protein_ids=protein_ids,
            target_gene_ids=target_gene_ids,
            disease_id=disease_id,
            limit=limit,
        )

    async def retrieve_evidence_chunks(
        self,
        query: str,
        top_k: int = 8,
        disease_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self.hybrid_retriever.retrieve_evidence_chunks(query=query, top_k=top_k, disease_id=disease_id)

    async def rank_targets(self, graph_results: dict[str, Any], evidence_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        genes = graph_results.get("associated_genes", [])
        evidence_text = " ".join((item.get("text") or "") for item in evidence_results).lower()

        ranked: list[dict[str, Any]] = []
        for gene in genes:
            gene_key = (gene.get("symbol") or gene.get("name") or gene.get("id") or "").lower()
            evidence_hits = evidence_text.count(gene_key) if gene_key else 0
            score = evidence_hits + (1 if gene.get("id") else 0)
            ranked.append(
                {
                    "gene_id": gene.get("id"),
                    "gene_symbol": gene.get("symbol"),
                    "score": score,
                    "components": {
                        "evidence_hits": evidence_hits,
                    },
                }
            )

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked

    async def build_graph_payload(self, entity_id: str, depth: int = 2) -> dict[str, Any]:
        return await self.graph_service.graph_neighborhood(entity_id=entity_id, depth=depth)
