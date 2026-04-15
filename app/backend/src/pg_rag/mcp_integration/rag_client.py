"""
MCP-backed RAG flow — side-by-side counterpart to rag.py.

Keep this module structurally identical to rag.py so a diff shows exactly
what changes when you swap a hardcoded function-calling tool for an MCP
server:

    rag.py  → hardcoded SEARCH_TOOL dict + direct retrieve_chunks() call
    rag_mcp.py → tool schema fetched via Client.list_tools()
                 + dispatched via Client.call_tool()

Everything else (two-pass flow, streaming, previous_response_id) is the same.
"""
import json
from collections.abc import AsyncGenerator
from types import SimpleNamespace
from typing import Any

from fastmcp import Client
from openai import AsyncOpenAI

from pg_rag.config import get_settings

settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)

# Same instructions as rag.py — only the tool *source* changes.
GENERAL_INSTRUCTIONS = (
    "You are a helpful assistant. "
    "If the user's question requires information from uploaded documents, "
    "use the search_documents tool. "
    "For casual conversation or general knowledge questions, answer directly without searching."
)

GROUNDED_INSTRUCTIONS = (
    "You are a helpful assistant. Answer the user's question using the document "
    "context returned by the search_documents tool. "
    "If the context does not contain enough information, say so clearly. "
    "Be concise and accurate."
)


def _mcp_tool_to_openai(tool) -> dict:
    """Convert an MCP tool descriptor into an OpenAI Responses API tool schema.

    This is the teaching moment: the LLM still sees a plain "function", but
    the schema is *discovered at runtime* from the MCP server instead of
    being hardcoded in the app.
    """
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description or "",
        "parameters": tool.inputSchema,
    }


def build_context(chunks) -> str:
    return "\n\n---\n\n".join(
        f"[Source: {row.filename}, chunk {row.chunk_index}]\n{row.content}"
        for row in chunks
    )


async def stream_rag_response_mcp(
    question: str,
) -> AsyncGenerator[tuple[str, Any], None]:
    """
    MCP-backed counterpart of stream_rag_response.

    Yields:
        ("delta",   str)                    — one text chunk of the answer
        ("sources", list[SimpleNamespace])  — chunk rows used (empty for direct)
    """
    # If the MCP server is protected with a bearer token, fastmcp's Client
    # will forward it as an Authorization header automatically.
    mcp_auth = settings.mcp_auth_token or None
    async with Client(settings.mcp_server_url, auth=mcp_auth) as mcp:
        # Discover tools from the MCP server (replaces hardcoded SEARCH_TOOL).
        mcp_tools = await mcp.list_tools()
        openai_tools = [_mcp_tool_to_openai(t) for t in mcp_tools]

        # Step 1: let the LLM decide whether retrieval is needed.
        first_response = await client.responses.create(
            model=settings.openai_chat_model,
            instructions=GENERAL_INSTRUCTIONS,
            input=question,
            tools=openai_tools,
            temperature=0.2,
        )

        tool_call = next(
            (item for item in first_response.output if item.type == "function_call"),
            None,
        )

        if tool_call is None:
            yield ("delta", first_response.output_text or "")
            yield ("sources", [])
            return

        # Step 2: dispatch the tool call to the MCP server (replaces direct
        # retrieve_chunks call).
        args = json.loads(tool_call.arguments)
        result = await mcp.call_tool(tool_call.name, args)

        # fastmcp returns structured JSON in .data when the tool is typed.
        raw = result.data if result.data is not None else []
        chunks = [SimpleNamespace(**row) for row in raw]
        context = build_context(chunks) if chunks else "No relevant documents found."

        # Step 3: stream the grounded answer.
        stream = await client.responses.create(
            model=settings.openai_chat_model,
            instructions=GROUNDED_INSTRUCTIONS,
            input=[{
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": context,
            }],
            previous_response_id=first_response.id,
            temperature=0.2,
            stream=True,
        )
        async for event in stream:
            if event.type == "response.output_text.delta":
                yield ("delta", event.delta)

        yield ("sources", chunks)
