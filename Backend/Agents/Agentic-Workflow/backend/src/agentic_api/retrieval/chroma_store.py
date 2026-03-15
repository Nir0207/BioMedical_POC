from __future__ import annotations

from typing import Any

import chromadb
from chromadb.utils import embedding_functions


class ChromaEvidenceStore:
    def __init__(self, persist_directory: str, embedding_model: str, ollama_base_url: str) -> None:
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection_name = "agentic_evidence"
        self.embedding_function = embedding_functions.OllamaEmbeddingFunction(
            model_name=embedding_model,
            url=f"{ollama_base_url}/api/embeddings",
        )

    def _collection(self):
        return self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "Agentic workflow evidence chunks"},
        )

    def query(self, query_text: str, top_k: int = 8) -> list[dict[str, Any]]:
        try:
            result = self._collection().query(query_texts=[query_text], n_results=top_k)
        except Exception:
            return []

        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        chunks: list[dict[str, Any]] = []
        for index, chunk_id in enumerate(ids):
            chunks.append(
                {
                    "id": chunk_id,
                    "text": docs[index] if index < len(docs) else "",
                    "source": metadatas[index].get("source_name", "chroma") if index < len(metadatas) else "chroma",
                    "score": distances[index] if index < len(distances) else None,
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                }
            )
        return chunks
