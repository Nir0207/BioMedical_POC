from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from agentic_api.core.config import get_settings
from agentic_api.db.neo4j import Neo4jClient
from agentic_api.retrieval.chroma_store import ChromaEvidenceStore
from agentic_api.retrieval.hybrid_retriever import HybridRetriever
from agentic_api.services.agentic_service import AgenticService
from agentic_api.services.graph_research_service import GraphResearchService
from agentic_api.tools.fixed_tools import FixedResearchTools
from agentic_api.workflows.research_workflow import AgenticResearchWorkflow

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def get_neo4j_client() -> Neo4jClient:
    return Neo4jClient()


@lru_cache(maxsize=1)
def get_graph_service() -> GraphResearchService:
    return GraphResearchService(get_neo4j_client())


@lru_cache(maxsize=1)
def get_chroma_store() -> ChromaEvidenceStore:
    settings = get_settings()
    return ChromaEvidenceStore(
        persist_directory=settings.chroma_path,
        embedding_model=settings.embedding_model,
        ollama_base_url=settings.ollama_base_url,
    )


@lru_cache(maxsize=1)
def get_hybrid_retriever() -> HybridRetriever:
    return HybridRetriever(get_graph_service(), get_chroma_store())


@lru_cache(maxsize=1)
def get_fixed_tools() -> FixedResearchTools:
    return FixedResearchTools(get_graph_service(), get_hybrid_retriever())


@lru_cache(maxsize=1)
def get_workflow() -> AgenticResearchWorkflow:
    settings = get_settings()
    return AgenticResearchWorkflow(
        tools=get_fixed_tools(),
        reasoning_model=settings.reasoning_model,
        base_url=settings.ollama_base_url,
        llm_enabled=settings.enable_llm,
    )


@lru_cache(maxsize=1)
def get_agentic_service() -> AgenticService:
    return AgenticService(get_workflow())


async def verify_agentic_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> None:
    expected_token = get_settings().api_token
    if not expected_token:
        return
    if not credentials or credentials.scheme.lower() != "bearer" or credentials.credentials != expected_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")
