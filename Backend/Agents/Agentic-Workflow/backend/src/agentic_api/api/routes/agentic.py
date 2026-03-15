from typing import Annotated

from fastapi import APIRouter, Depends

from agentic_api.api.dependencies import get_agentic_service, verify_agentic_token
from agentic_api.schemas.agentic import ResearchQueryRequest, ResearchQueryResponse
from agentic_api.services.agentic_service import AgenticService

router = APIRouter(prefix="/agentic", tags=["agentic"], dependencies=[Depends(verify_agentic_token)])


@router.post("/research-query", response_model=ResearchQueryResponse)
async def research_query(
    payload: ResearchQueryRequest,
    service: Annotated[AgenticService, Depends(get_agentic_service)],
) -> ResearchQueryResponse:
    state = await service.run_research_query(user_query=payload.user_query, top_k=payload.top_k)
    return ResearchQueryResponse(
        user_query=state.get("user_query", payload.user_query),
        normalized_query=state.get("normalized_query", payload.user_query),
        intent=state.get("intent", "unknown"),
        module=state.get("module", "disease_target_discovery"),
        resolved_entities=state.get("resolved_entities", []),
        final_answer=state.get("final_answer", "No answer generated."),
        citations=state.get("citations", []),
        graph_payload=state.get("graph_payload", {}),
        ranking_results=state.get("ranking_results", []),
        errors=state.get("errors", []),
    )
