from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env", "../../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="Biomedical Backend API", alias="BACKEND_APP_NAME")
    api_prefix: str = Field(default="/api/v1", alias="BACKEND_API_PREFIX")
    app_port: int = Field(default=8001, alias="BACKEND_APP_PORT")
    database_url: str = Field(
        default="postgresql+asyncpg://backend_app:backend_app_pw@backend-postgres:5432/backend_app",
        alias="BACKEND_DATABASE_URL",
    )
    neo4j_uri: str = Field(default="bolt://host.docker.internal:7688", alias="BACKEND_NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="BACKEND_NEO4J_USERNAME")
    neo4j_password: str = Field(default="KGFramework_2026!", alias="BACKEND_NEO4J_PASSWORD")
    cypher_query_root: str = Field(default="/app/db/Neo4j/CypherQueries", alias="BACKEND_CYPHER_QUERY_ROOT")
    jwt_secret: str = Field(default="change_me_in_env", alias="BACKEND_JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="BACKEND_JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="BACKEND_ACCESS_TOKEN_EXPIRE_MINUTES")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
