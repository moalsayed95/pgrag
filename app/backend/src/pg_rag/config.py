from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pgrag"
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"
    chunk_size: int = 500
    chunk_overlap: int = 100
    mcp_server_url: str = "http://localhost:8001/mcp"
    # Public URL of the MCP server (e.g. an ngrok tunnel). Required for the
    # native MCP pattern — OpenAI itself connects to this URL.
    mcp_public_url: str = ""
    # Shared secret guarding the MCP server. When set, the server rejects
    # requests without matching bearer token. Leave unset for local-only dev.
    mcp_auth_token: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
