from __future__ import annotations

import asyncio
from collections import OrderedDict
from typing import Any

from agentic_api.retrieval.chroma_store import ChromaEvidenceStore
from agentic_api.services.graph_research_service import GraphResearchService


class HybridRetriever:
    def __init__(self, graph_service: GraphResearchService, chroma_store: ChromaEvidenceStore) -> None:
        self.graph_service = graph_service
        self.chroma_store = chroma_store

    async def retrieve_evidence_chunks(
        self,
        query: str,
        top_k: int = 8,
        disease_id: str | None = None,
    ) -> list[dict[str, Any]]:
        graph_rows = await self.graph_service.search_evidence(query_text=query, limit=top_k, disease_id=disease_id)
        try:
            vector_rows = await asyncio.wait_for(
                asyncio.to_thread(self.chroma_store.query, query_text=query, top_k=top_k),
                timeout=5,
            )
        except Exception:
            vector_rows = []

        merged: OrderedDict[str, dict[str, Any]] = OrderedDict()
        for row in graph_rows:
            row_id = row.get("id")
            if row_id and row_id not in merged:
                merged[row_id] = {
                    "id": row_id,
                    "text": row.get("text"),
                    "source": row.get("source", "graph"),
                    "score": row.get("confidence_score"),
                    "metadata": row,
                }
        for row in vector_rows:
            row_id = row.get("id")
            if row_id and row_id not in merged:
                merged[row_id] = row

        return list(merged.values())[:top_k]
