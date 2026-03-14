from fastapi import HTTPException, status

from biomedical_api.db.neo4j import Neo4jClient
from biomedical_api.repositories.cypher_query_repository import CypherQueryDefinition, CypherQueryRepository


class CypherQueryService:
    def __init__(self, neo4j_client: Neo4jClient, repository: CypherQueryRepository | None = None) -> None:
        self.neo4j_client = neo4j_client
        self.repository = repository or CypherQueryRepository()

    def list_queries(self) -> list[CypherQueryDefinition]:
        return self.repository.list_safe_queries()

    async def execute_query(self, query_id: str, parameters: dict[str, object] | None = None) -> dict[str, object]:
        try:
            definition = self.repository.get_query(query_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cypher query not found") from exc

        provided_parameters = parameters or {}
        missing_parameters = [name for name in definition.parameters if name not in provided_parameters]
        if missing_parameters:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing query parameters: {', '.join(missing_parameters)}",
            )

        records = await self.neo4j_client.run_query(
            self.repository.read_query_text(query_id),
            provided_parameters,
        )
        return {
            "query_id": definition.query_id,
            "record_count": len(records),
            "records": records,
        }
