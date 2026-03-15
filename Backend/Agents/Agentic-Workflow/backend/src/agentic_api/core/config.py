from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env", "../../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="Biomedical Agentic Workflow API", alias="AGENTIC_APP_NAME")
    api_prefix: str = Field(default="/api/v1", alias="AGENTIC_API_PREFIX")
    app_port: int = Field(default=8011, alias="AGENTIC_APP_PORT")

    neo4j_uri: str = Field(default="bolt://host.docker.internal:7688", alias="AGENTIC_NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="AGENTIC_NEO4J_USERNAME")
    neo4j_password: str = Field(default="KGFramework_2026!", alias="AGENTIC_NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="AGENTIC_NEO4J_DATABASE")

    ollama_base_url: str = Field(default="http://host.docker.internal:11434", alias="AGENTIC_OLLAMA_BASE_URL")
    reasoning_model: str = Field(default="qwen2.5:7b", alias="AGENTIC_REASONING_MODEL")
    planner_model: str = Field(default="qwen2.5-coder:7b", alias="AGENTIC_PLANNER_MODEL")
    embedding_model: str = Field(default="nomic-embed-text", alias="AGENTIC_EMBEDDING_MODEL")
    enable_llm: bool = Field(default=True, alias="AGENTIC_ENABLE_LLM")
    chroma_path: str = Field(default="/app/.chroma", alias="AGENTIC_CHROMA_PATH")
    default_top_k: int = Field(default=8, alias="AGENTIC_DEFAULT_TOP_K")

    request_timeout_seconds: int = Field(default=90, alias="AGENTIC_REQUEST_TIMEOUT_SECONDS")
    log_level: str = Field(default="INFO", alias="AGENTIC_LOG_LEVEL")
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        alias="AGENTIC_CORS_ORIGINS",
    )

    api_token: str | None = Field(default=None, alias="AGENTIC_API_TOKEN")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
