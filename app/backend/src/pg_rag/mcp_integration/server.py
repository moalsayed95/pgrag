"""
MCP server exposing document retrieval as a tool.

This runs as a **separate service** (see docker-compose). The FastAPI backend's
MCP-mode chat endpoint talks to it over HTTP, demonstrating how an MCP server
can replace a hardcoded OpenAI function-calling tool definition.

Tool parity with rag.py's SEARCH_TOOL:
    - name: search_documents
    - input: {query: str, top_k: int = 5}
    - output: list of chunk dicts

Run locally:
    uv run python -m pg_rag.mcp_server
"""
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

from pg_rag.config import get_settings
from pg_rag.database import async_session
from pg_rag.rag import retrieve_chunks

settings = get_settings()

# When MCP_AUTH_TOKEN is set, require a matching bearer token on every request.
# This is essential the moment the server is exposed to the internet (e.g. via
# ngrok for the native-MCP pattern). Local-only dev can leave it unset.
_auth = None
if settings.mcp_auth_token:
    _auth = StaticTokenVerifier(
        tokens={settings.mcp_auth_token: {"sub": "pg-rag-client", "client_id": "pg-rag"}},
    )

mcp = FastMCP(
    "pg-rag-mcp",
    instructions=(
        "MCP server for the pg-rag corpus. "
        "Use search_documents to find passages relevant to a query."
    ),
    auth=_auth,
)


@mcp.tool
async def search_documents(query: str, top_k: int = 5) -> list[dict]:
    """Search the uploaded documents for information relevant to a query.

    Use this tool when the user asks about document content, specific facts,
    or anything that requires looking up stored knowledge.
    """
    async with async_session() as db:
        rows = await retrieve_chunks(db, query, top_k=top_k)
        return [
            {
                "content": row.content,
                "chunk_index": row.chunk_index,
                "filename": row.filename,
                "score": float(row.score),
            }
            for row in rows
        ]


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001)
