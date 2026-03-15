from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query

from biomedical_api.api.dependencies import get_current_user_id, get_data_service
from biomedical_api.repositories.cypher_query_repository import CypherQueryDefinition, CypherQueryRepository
from biomedical_api.schemas.cypher import (
    CypherQueryDefinitionResponse,
    CypherQueryExecutionRequest,
    CypherQueryExecutionResponse,
)
from biomedical_api.schemas.query_canvas import (
    QueryCanvasCategoryResponse,
    QueryCanvasNodeResponse,
    QueryCanvasRelationValidationRequest,
    QueryCanvasRelationValidationResponse,
    QueryCanvasRunRequest,
    QueryCanvasRunResponse,
)
from biomedical_api.schemas.user import GraphSummaryResponse, PostgresSummaryResponse
from biomedical_api.services.data_service import DataService

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/postgres/summary", response_model=PostgresSummaryResponse)
async def postgres_summary(
    _: Annotated[int, Depends(get_current_user_id)],
    data_service: Annotated[DataService, Depends(get_data_service)],
) -> PostgresSummaryResponse:
    return PostgresSummaryResponse(**(await data_service.fetch_postgres_summary()))


@router.get("/neo4j/summary", response_model=GraphSummaryResponse)
async def neo4j_summary(
    _: Annotated[int, Depends(get_current_user_id)],
    data_service: Annotated[DataService, Depends(get_data_service)],
) -> GraphSummaryResponse:
    return GraphSummaryResponse(**(await data_service.fetch_neo4j_summary()))


@router.get("/neo4j/queries", response_model=list[CypherQueryDefinitionResponse])
async def list_neo4j_queries(
    _: Annotated[int, Depends(get_current_user_id)],
    data_service: Annotated[DataService, Depends(get_data_service)],
) -> list[CypherQueryDefinitionResponse]:
    return [
        CypherQueryDefinitionResponse(
            query_id=query.query_id,
            category=query.category,
            name=query.name,
            description=query.description,
            parameters=query.parameters,
            parameter_help=query.parameter_help,
            endpoint_path=query.endpoint_path,
        )
        for query in data_service.list_cypher_queries()
    ]


@router.get("/neo4j/query-canvas/categories", response_model=list[QueryCanvasCategoryResponse])
async def list_query_canvas_categories(
    _: Annotated[int, Depends(get_current_user_id)],
    data_service: Annotated[DataService, Depends(get_data_service)],
) -> list[QueryCanvasCategoryResponse]:
    return [QueryCanvasCategoryResponse(**row) for row in await data_service.fetch_query_canvas_categories()]


@router.get("/neo4j/query-canvas/nodes", response_model=list[QueryCanvasNodeResponse])
async def search_query_canvas_nodes(
    _: Annotated[int, Depends(get_current_user_id)],
    data_service: Annotated[DataService, Depends(get_data_service)],
    category: str | None = Query(default=None),
    search: str = Query(default=""),
    limit: int = Query(default=24, ge=1, le=50),
) -> list[QueryCanvasNodeResponse]:
    records = await data_service.search_query_canvas_nodes(category=category, search=search, limit=limit)
    return [QueryCanvasNodeResponse(**record) for record in records]


@router.post("/neo4j/query-canvas/validate", response_model=QueryCanvasRelationValidationResponse)
async def validate_query_canvas_relation(
    payload: QueryCanvasRelationValidationRequest,
    _: Annotated[int, Depends(get_current_user_id)],
    data_service: Annotated[DataService, Depends(get_data_service)],
) -> QueryCanvasRelationValidationResponse:
    return QueryCanvasRelationValidationResponse(
        **(
            await data_service.validate_query_canvas_relation(
                source_node_id=payload.source_node_id,
                target_node_id=payload.target_node_id,
            )
        )
    )


@router.post("/neo4j/query-canvas/run", response_model=QueryCanvasRunResponse)
async def run_query_canvas_relation(
    payload: QueryCanvasRunRequest,
    _: Annotated[int, Depends(get_current_user_id)],
    data_service: Annotated[DataService, Depends(get_data_service)],
) -> QueryCanvasRunResponse:
    return QueryCanvasRunResponse(
        **(
            await data_service.run_query_canvas_relation(
                source_node_id=payload.source_node_id,
                target_node_id=payload.target_node_id,
                neighbor_limit=payload.neighbor_limit,
                cypher=payload.cypher,
                parameters=payload.parameters,
            )
        )
    )


def _build_query_description(query: CypherQueryDefinition) -> str:
    description_parts = [query.description or "Cypher query loaded from the repository."]
    if query.parameters:
        parameter_lines = ["Required JSON body shape: `{\"parameters\": {...}}`", "", "Required parameters:"]
        for parameter_name in query.parameters:
            parameter_lines.append(f"- `{parameter_name}`: {query.parameter_help[parameter_name]}")
        description_parts.append("\n".join(parameter_lines))
    else:
        description_parts.append("No parameters are required. You can call this endpoint with an empty body.")
    description_parts.append(f"Source query file: `{query.path.name}`")
    return "\n\n".join(description_parts)


def _build_query_endpoint(query: CypherQueryDefinition):
    async def execute_neo4j_query(
        _: Annotated[int, Depends(get_current_user_id)],
        data_service: Annotated[DataService, Depends(get_data_service)],
        payload: CypherQueryExecutionRequest | None = Body(
            default=None,
            description="Query parameters sourced from the underlying .cypher file.",
        ),
    ) -> CypherQueryExecutionResponse:
        parameters = payload.parameters if payload else {}
        return CypherQueryExecutionResponse(
            **(await data_service.execute_cypher_query(query_id=query.query_id, parameters=parameters))
        )

    execute_neo4j_query.__name__ = f"execute_{query.query_id.replace('/', '_')}"
    return execute_neo4j_query


for query_definition in CypherQueryRepository().list_safe_queries():
    router.add_api_route(
        path=f"/neo4j/queries/{query_definition.query_id}",
        endpoint=_build_query_endpoint(query_definition),
        methods=["POST"],
        response_model=CypherQueryExecutionResponse,
        summary=f"Execute {query_definition.query_id}",
        description=_build_query_description(query_definition),
        operation_id=f"execute_{query_definition.query_id.replace('/', '_')}",
    )
