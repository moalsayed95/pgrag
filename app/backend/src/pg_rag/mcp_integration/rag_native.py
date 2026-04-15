"""
Native MCP pattern — OpenAI itself is the MCP client.

Contrast with rag_mcp.py:

    rag_mcp.py        → our app speaks MCP (list_tools / call_tool ourselves)
    rag_mcp_native.py → OpenAI speaks MCP for us (single API call)

The trade-off: OpenAI's servers need to reach the MCP server, so the URL
must be publicly accessible (ngrok / deployed). See learn_mcp/06_exposing_with_ngrok.md
for the security-hardening guide that belongs with this pattern.
"""
import json
from collections.abc import AsyncGenerator
from types import SimpleNamespace
from typing import Any

from openai import AsyncOpenAI

from pg_rag.config import get_settings

settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)

INSTRUCTIONS = (
    "You are a helpful assistant. "
    "If the user's question requires information from uploaded documents, "
    "use the search_documents tool. "
    "For casual conversation or general knowledge questions, answer directly without searching."
)


def _build_mcp_tool() -> dict:
    """Build the Responses-API MCP tool descriptor.

    This is the entire MCP glue in the native pattern — a few fields that
    tell OpenAI where the MCP server lives and (if protected) how to
    authenticate to it.
    """
    tool: dict[str, Any] = {
        "type": "mcp",
        "server_label": "pg_rag",
        "server_description": "Retrieves passages from the pg-rag corpus.",
        "server_url": settings.mcp_public_url,
        "require_approval": "never",
    }
    if settings.mcp_auth_token:
        tool["headers"] = {"Authorization": f"Bearer {settings.mcp_auth_token}"}
    return tool


def _extract_sources(output_items) -> list[SimpleNamespace]:
    """Best-effort extraction of retrieval results from OpenAI's mcp_call items.

    OpenAI returns each MCP tool invocation as an output item of type 'mcp_call'
    with the tool's JSON output attached. We parse it back into the same
    shape rag_mcp.py returns so the frontend renders identical source cards.
    """
    sources: list[SimpleNamespace] = []
    for item in output_items or []:
        if getattr(item, "type", None) != "mcp_call":
            continue
        raw = getattr(item, "output", None)
        if not raw:
            continue
        try:
            payload = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            continue
        # FastMCP structured-output shape: {"content": [...], "structuredContent": {"result": [...]}}
        rows: Any = payload
        if isinstance(payload, dict):
            rows = (
                payload.get("structuredContent", {}).get("result")
                or payload.get("result")
                or payload.get("content")
                or []
            )
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and "content" in row:
                    sources.append(SimpleNamespace(**row))
    return sources


async def stream_rag_response_mcp_native(
    question: str,
) -> AsyncGenerator[tuple[str, Any], None]:
    """
    Native MCP counterpart of stream_rag_response.

    One API call. OpenAI handles: tool discovery, tool dispatch, and streaming
    the grounded answer. We only forward text deltas and extract source cards
    from the completed response for the UI.
    """
    if not settings.mcp_public_url:
        raise RuntimeError(
            "MCP_PUBLIC_URL is not set. The native MCP pattern needs a public "
            "URL for the MCP server (see learn_mcp/06_exposing_with_ngrok.md)."
        )

    stream = await client.responses.create(
        model=settings.openai_chat_model,
        instructions=INSTRUCTIONS,
        input=question,
        tools=[_build_mcp_tool()],
        temperature=0.2,
        stream=True,
    )

    final_output_items = None
    async for event in stream:
        if event.type == "response.output_text.delta":
            yield ("delta", event.delta)
        elif event.type == "response.completed":
            final_output_items = event.response.output

    yield ("sources", _extract_sources(final_output_items))
