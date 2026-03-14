from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from biomedical_api.core.security import decode_access_token
from biomedical_api.db.neo4j import Neo4jClient, get_neo4j_client
from biomedical_api.db.postgres import get_db_session
from biomedical_api.repositories.user_repository import LoginAuditRepository, UserRepository
from biomedical_api.services.auth_service import AuthService
from biomedical_api.services.data_service import DataService


bearer_scheme = HTTPBearer(auto_error=True)


async def get_auth_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> AuthService:
    return AuthService(
        user_repository=UserRepository(session),
        login_audit_repository=LoginAuditRepository(session),
    )


async def get_data_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    neo4j_client: Annotated[Neo4jClient, Depends(get_neo4j_client)],
) -> DataService:
    return DataService(session=session, neo4j_client=neo4j_client)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> int:
    try:
        return int(decode_access_token(credentials.credentials))
    except (JWTError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


async def get_request_ip(x_forwarded_for: Annotated[str | None, Header()] = None) -> str | None:
    return x_forwarded_for
